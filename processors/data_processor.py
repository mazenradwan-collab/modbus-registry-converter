"""Advanced intelligent data processor with smart address parsing - Enhanced version"""

import pandas as pd
import re
from difflib import SequenceMatcher
from config import (
    OUTPUT_COLUMNS,
    FUNCTION_CODE_MAP,
    REGISTER_TYPE_MAP,
    DATA_TYPE_MAP,
    ACCESS_TYPE_MAP,
    DEFAULT_POLLING_MS,
    DEFAULT_SCALE_FACTOR,
    DEFAULT_REGISTER_COUNT,
    DEFAULT_ENABLED
)


class AdvancedColumnMatcher:
    """Advanced intelligent column name matcher with fuzzy matching and smart field extraction"""
    
    FIELD_PATTERNS = {
        'register_name': ['registername', 'register_name', 'name', 'id', 'description', 'desc', 'registerlabel', 'register_label', 'label', 'registerlabel'],
        'display_name': ['displayname', 'display_name', 'label', 'description', 'desc', 'display', 'registerlabel', 'name'],
        'function_code': ['functioncode', 'function_code', 'function', 'code', 'fc', 'func', 'modbusfunction', 'requesttype'],
        'register_type': ['registertype', 'register_type', 'type', 'regtype', 'reg_type', 'modbustype'],
        'address': ['address', 'addr', 'offset', 'register', 'reg_addr', 'modbus_address', 'modbusaddr', 'modbus_addr'],
        'data_type': ['datatype', 'data_type', 'dtype', 'format', 'value_type', 'valuetype'],
        'register_count': ['registercount', 'register_count', 'count', 'size', 'length', 'qty', 'quantity', 'numberofregisters'],
        'scale_factor': ['scalefactor', 'scale_factor', 'scale', 'multiplier', 'factor', 'scaling', 'mask'],
        'unit': ['unit', 'units', 'uom', 'measurement', 'measure'],
        'access': ['access', 'permission', 'permissions', 'accesstype', 'access_type', 'mode', 'accessmode', 'requesttype'],
        'polling_ms': ['polling_ms', 'polling', 'pollinterval', 'poll_interval', 'interval', 'frequency'],
        'enabled': ['enabled', 'active', 'status', 'disabled', 'enable']
    }
    
    def __init__(self):
        self.column_map = {}
        self.confidence_scores = {}
    
    def match_columns(self, dataframe):
        """Intelligently match DataFrame columns to standard fields"""
        
        # Remove completely empty columns
        df_clean = dataframe.dropna(axis=1, how='all')
        
        df_columns = [str(col).lower().strip() for col in df_clean.columns]
        self.column_map = {}
        self.confidence_scores = {}
        
        for field, patterns in self.FIELD_PATTERNS.items():
            best_match = None
            best_score = 0
            
            for df_col in df_columns:
                if not df_col or df_col.isspace():  # Skip empty column names
                    continue
                    
                if df_col in patterns:
                    best_match = df_col
                    best_score = 1.0
                    break
                
                for pattern in patterns:
                    score = self._similarity_score(df_col, pattern)
                    if score > best_score:
                        best_score = score
                        best_match = df_col
            
            if best_match and best_score > 0.6:
                original_col = next(
                    (col for col in df_clean.columns if str(col).lower() == best_match),
                    best_match
                )
                self.column_map[field] = original_col
                self.confidence_scores[field] = best_score
        
        return self.column_map, self.confidence_scores
    
    def _similarity_score(self, str1, str2):
        """Calculate similarity score between two strings"""
        str1_clean = str1.replace('_', '').replace(' ', '')
        str2_clean = str2.replace('_', '').replace(' ', '')
        
        return SequenceMatcher(None, str1_clean, str2_clean).ratio()
    
    def get_value(self, record, field):
        """Get value from record using mapped column name"""
        if field not in self.column_map:
            return None
        
        column = self.column_map[field]
        value = record.get(column)
        
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        
        return value


class SmartAddressParser:
    """Smart parser for extracting function code and address from combined address values"""
    
    # Function code ranges for Modbus
    FUNCTION_CODE_RANGES = {
        1: (0, 9999),           # Coil
        2: (10000, 19999),      # Discrete Input
        3: (30000, 39999),      # Input Register
        4: (40000, 49999),      # Holding Register
    }
    
    def __init__(self):
        self.extracted_function_codes = {}
        self.extracted_addresses = {}
    
    def parse_address(self, address_value, register_name=""):
        """
        Smart parse address that may contain encoded function code
        Examples:
        - 414201 -> function_code=4, address=14201
        - 314500 -> function_code=3, address=14500
        - 100 -> function_code=3 (default), address=100
        - 420010 -> function_code=4, address=20010
        """
        
        if address_value is None:
            return None, None
        
        try:
            addr_str = str(address_value).strip()
            addr_int = int(float(addr_str))
        except:
            return None, None
        
        if addr_int < 0:
            return None, None
        
        extracted_fc = None
        extracted_addr = None
        
        # Check if first digit is a valid function code (1, 2, 3, or 4)
        addr_str_num = str(addr_int)
        
        if len(addr_str_num) >= 5:  # Address like 414201, 320000, etc.
            first_digit = int(addr_str_num[0])
            
            if first_digit in [1, 2, 3, 4]:
                potential_addr = addr_int - (first_digit * 10000)
                
                # Verify if this makes sense (address should be 0-9999 or up to 65535)
                if 0 <= potential_addr <= 65535:
                    extracted_fc = first_digit
                    extracted_addr = potential_addr
        
        # If no extraction, use whole address
        if extracted_addr is None:
            extracted_addr = addr_int
            extracted_fc = self._determine_function_code_by_address(addr_int)
        
        return extracted_fc, extracted_addr
    
    def _determine_function_code_by_address(self, address):
        """Determine function code based on address range"""
        
        for fc, (min_addr, max_addr) in self.FUNCTION_CODE_RANGES.items():
            if min_addr <= address <= max_addr:
                return fc
        
        return 4  # Default to Holding Register


class AdvancedDataProcessor:
    """Advanced process and normalize registry data with smart extraction"""
    
    def __init__(self):
        self.warnings = []
        self.column_matcher = AdvancedColumnMatcher()
        self.address_parser = SmartAddressParser()
        self.skipped_rows = 0
    
    def process(self, raw_data):
        """Process raw data to unified format with smart extraction"""
        
        if not raw_data:
            return []
        
        self.warnings = []
        self.skipped_rows = 0
        
        # Convert to DataFrame for column matching
        try:
            df = pd.DataFrame(raw_data)
            # Remove rows that are completely empty
            df = df.dropna(how='all')
            # Convert back to list of dicts
            raw_data_clean = df.to_dict('records')
        except:
            raw_data_clean = raw_data
        
        self.column_matcher.match_columns(pd.DataFrame(raw_data_clean))
        
        processed_data = []
        
        for idx, record in enumerate(raw_data_clean):
            try:
                processed_record = self._normalize_record(record, idx)
                if processed_record:
                    processed_data.append(processed_record)
                else:
                    self.skipped_rows += 1
            except Exception as e:
                self.warnings.append(f"Row {idx + 1}: {str(e)}")
                self.skipped_rows += 1
        
        return processed_data
    
    def _normalize_record(self, record, idx):
        """Normalize a single record to unified format with smart parsing"""
        
        # Get register name (try multiple sources)
        register_name = self.column_matcher.get_value(record, 'register_name')
        
        # If register_name not found, try display_name
        if not register_name:
            register_name = self.column_matcher.get_value(record, 'display_name')
        
        if not register_name:
            return None
        
        register_name = str(register_name).strip()
        if not register_name or register_name.lower() in ['nan', '']:
            return None
        
        # Get display name
        display_name = self.column_matcher.get_value(record, 'display_name')
        if not display_name:
            display_name = self._clean_display_name(register_name)
        
        # Get address and extract function code if embedded
        raw_address = self.column_matcher.get_value(record, 'address')
        extracted_fc, extracted_addr = self.address_parser.parse_address(raw_address, register_name)
        
        # Get function code from data or use extracted
        function_code = self.column_matcher.get_value(record, 'function_code')
        if function_code:
            function_code = self._normalize_function_code(function_code)
        elif extracted_fc:
            function_code = extracted_fc
        else:
            function_code = 4  # Default
        
        # Get register type based on function code
        register_type = self.column_matcher.get_value(record, 'register_type')
        if not register_type:
            register_type = self._get_register_type_from_function_code(function_code)
        else:
            register_type = self._normalize_register_type(register_type)
        
        # Use extracted address or default
        address = extracted_addr if extracted_addr is not None else 0
        
        data_type = self.column_matcher.get_value(record, 'data_type')
        data_type = self._normalize_data_type(data_type)
        
        register_count = self.column_matcher.get_value(record, 'register_count')
        try:
            register_count = int(register_count) if register_count else DEFAULT_REGISTER_COUNT
        except:
            register_count = DEFAULT_REGISTER_COUNT
        
        scale_factor = self.column_matcher.get_value(record, 'scale_factor')
        try:
            scale_factor = float(scale_factor) if scale_factor else DEFAULT_SCALE_FACTOR
        except:
            scale_factor = DEFAULT_SCALE_FACTOR
        
        unit = self.column_matcher.get_value(record, 'unit')
        if not unit:
            unit = ''
        
        access = self.column_matcher.get_value(record, 'access')
        access = self._normalize_access_type(access)
        
        polling_ms = self.column_matcher.get_value(record, 'polling_ms')
        try:
            polling_ms = int(polling_ms) if polling_ms else DEFAULT_POLLING_MS
        except:
            polling_ms = DEFAULT_POLLING_MS
        
        enabled = self.column_matcher.get_value(record, 'enabled')
        enabled = self._normalize_boolean(enabled, DEFAULT_ENABLED)
        
        return {
            'RegisterName': str(register_name).strip(),
            'DisplayName': str(display_name).strip(),
            'FunctionCode': function_code,
            'RegisterType': register_type,
            'Address': address,
            'DataType': data_type,
            'RegisterCount': register_count,
            'ScaleFactor': scale_factor,
            'Unit': str(unit).strip() if unit else '',
            'Access': access,
            'Polling_ms': polling_ms,
            'Enabled': enabled
        }
    
    def _clean_display_name(self, register_name):
        """Clean and format register name for display"""
        name = str(register_name).strip()
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        # Capitalize first letter of each word
        name = ' '.join(word.capitalize() for word in name.split() if word)
        return name
    
    def _get_register_type_from_function_code(self, function_code):
        """Get register type based on Modbus function code"""
        fc_to_type = {
            1: 'Coil',
            2: 'Discrete Input',
            3: 'Input Register',
            4: 'Holding Register',
            16: 'Holding Register',
            23: 'Holding Register',
        }
        return fc_to_type.get(function_code, 'Holding Register')
    
    def _normalize_function_code(self, value):
        """Normalize function code to standard value"""
        
        if not value:
            return 4
        
        value_str = str(value).lower().strip()
        
        # Map common text to function codes
        fc_map = {
            'coil': 1,
            'discrete': 2,
            'input': 3,
            'holding': 4,
            'write': 16,
            'r': 3,  # Read
            'rw': 4,  # Read-Write
            'w': 16,  # Write
        }
        
        for key, code in fc_map.items():
            if key in value_str:
                return code
        
        for key, code in FUNCTION_CODE_MAP.items():
            if key in value_str or value_str in key:
                return code
        
        try:
            code = int(value)
            if code in [1, 2, 3, 4, 16, 23]:
                return code
        except:
            pass
        
        return 4
    
    def _normalize_register_type(self, value):
        """Normalize register type to standard format"""
        
        if not value:
            return 'Holding Register'
        
        value_str = str(value).lower().strip()
        
        for key, reg_type in REGISTER_TYPE_MAP.items():
            if key in value_str or value_str in key:
                return reg_type
        
        return 'Holding Register'
    
    def _normalize_data_type(self, value):
        """Normalize data type to standard format"""
        
        if not value:
            return 'INT16'
        
        value_str = str(value).lower().strip()
        
        # Common data types mapping
        type_map = {
            'int': 'INT16',
            'uint': 'UINT16',
            'int32': 'INT32',
            'uint32': 'UINT32',
            'float': 'FLOAT32',
            'f32': 'FLOAT32',
            'ascii': 'ASCII',
            'datetime': 'DATETIME',
            'bool': 'BOOL',
            'maskedbool': 'BOOL',
        }
        
        for key, dtype in type_map.items():
            if key in value_str:
                return dtype
        
        for key, data_type in DATA_TYPE_MAP.items():
            if key in value_str or value_str in key:
                return data_type
        
        return 'INT16'
    
    def _normalize_access_type(self, value):
        """Normalize access type to standard format"""
        
        if not value:
            return 'Read'
        
        value_str = str(value).lower().strip()
        
        if 'rw' in value_str or 'read-write' in value_str or 'read/write' in value_str:
            return 'Read/Write'
        elif 'w' in value_str and 'rw' not in value_str:
            return 'Write'
        elif 'r' in value_str:
            return 'Read'
        
        for key, access in ACCESS_TYPE_MAP.items():
            if key in value_str or value_str in key:
                return access
        
        return 'Read'
    
    def _normalize_boolean(self, value, default=True):
        """Convert value to boolean"""
        
        if value is None:
            return default
        
        value_str = str(value).lower().strip()
        return value_str in ['true', 'yes', '1', 'enabled', 'active', 'on', 'r', 'rw']
    
    def validate(self, data):
        """Validate processed data"""
        
        validation_results = {
            'is_valid': True,
            'warnings': self.warnings,
            'errors': [],
            'skipped_rows': self.skipped_rows
        }
        
        for idx, record in enumerate(data):
            if not record.get('RegisterName'):
                validation_results['errors'].append(f"Row {idx + 1}: Missing RegisterName")
                validation_results['is_valid'] = False
            
            if not isinstance(record.get('Address'), int) or record.get('Address') < 0:
                validation_results['warnings'].append(f"Row {idx + 1}: Invalid Address")
            
            if record.get('Polling_ms', 0) <= 0:
                validation_results['warnings'].append(f"Row {idx + 1}: Polling_ms should be positive")
            
            # Validate function code
            fc = record.get('FunctionCode')
            if fc not in [1, 2, 3, 4, 16, 23]:
                validation_results['warnings'].append(f"Row {idx + 1}: Invalid Function Code {fc}")
        
        return validation_results
    
    def get_column_mapping_report(self):
        """Get a report of how columns were mapped"""
        
        report = "Column Mapping Report:\n"
        report += "-" * 60 + "\n"
        
        for field, column in self.column_matcher.column_map.items():
            confidence = self.column_matcher.confidence_scores.get(field, 0)
            confidence_pct = int(confidence * 100)
            report += f"{field:20s} -> {column:30s} ({confidence_pct}%)\n"
        
        unmapped = [field for field in self.column_matcher.FIELD_PATTERNS.keys() 
                   if field not in self.column_matcher.column_map]
        
        if unmapped:
            report += "\nUnmapped fields (using defaults):\n"
            for field in unmapped:
                report += f"  - {field}\n"
        
        report += f"\nRows skipped (empty/invalid): {self.skipped_rows}\n"
        
        return report


# Keep backward compatibility
DataProcessor = AdvancedDataProcessor
