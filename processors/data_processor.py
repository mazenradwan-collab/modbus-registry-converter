"""Advanced intelligent data processor with smart address parsing"""

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
        'register_name': ['registername', 'register_name', 'name', 'id', 'description', 'desc', 'registerlabel', 'register_label', 'label'],
        'display_name': ['displayname', 'display_name', 'label', 'description', 'desc', 'display', 'registerlabel'],
        'function_code': ['functioncode', 'function_code', 'function', 'code', 'fc', 'func', 'modbusfunction'],
        'register_type': ['registertype', 'register_type', 'type', 'regtype', 'reg_type', 'modbustype'],
        'address': ['address', 'addr', 'offset', 'register', 'reg_addr', 'modbus_address', 'modbusaddr', 'modbus_addr'],
        'data_type': ['datatype', 'data_type', 'dtype', 'format', 'value_type', 'valuetype'],
        'register_count': ['registercount', 'register_count', 'count', 'size', 'length', 'qty', 'quantity'],
        'scale_factor': ['scalefactor', 'scale_factor', 'scale', 'multiplier', 'factor', 'scaling'],
        'unit': ['unit', 'units', 'uom', 'measurement', 'measure'],
        'access': ['access', 'permission', 'permissions', 'accesstype', 'access_type', 'mode', 'accessmode'],
        'polling_ms': ['polling_ms', 'polling', 'pollinterval', 'poll_interval', 'interval', 'frequency'],
        'enabled': ['enabled', 'active', 'status', 'disabled', 'enable']
    }
    
    def __init__(self):
        self.column_map = {}
        self.confidence_scores = {}
    
    def match_columns(self, dataframe):
        """Intelligently match DataFrame columns to standard fields"""
        
        df_columns = [str(col).lower().strip() for col in dataframe.columns]
        self.column_map = {}
        self.confidence_scores = {}
        
        for field, patterns in self.FIELD_PATTERNS.items():
            best_match = None
            best_score = 0
            
            for df_col in df_columns:
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
                    (col for col in dataframe.columns if str(col).lower() == best_match),
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
    
    # Function code ranges
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
        """
        
        if not address_value:
            return None, None
        
        try:
            addr_str = str(address_value).strip()
            addr_int = int(float(addr_str))
        except:
            return None, None
        
        extracted_fc = None
        extracted_addr = None
        
        # Check if first digit is a function code
        addr_str_padded = str(addr_int).zfill(6)
        first_digit = int(addr_str_padded[0])
        
        if first_digit in self.FUNCTION_CODE_RANGES:
            potential_addr = addr_int - (first_digit * 10000)
            
            # Verify if this makes sense (address should be 0-9999 typically)
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
        
        return 3  # Default to Input Register
    
    def get_parsing_report(self):
        """Get report of parsed addresses"""
        return {
            'extracted_function_codes': self.extracted_function_codes,
            'extracted_addresses': self.extracted_addresses
        }


class AdvancedDataProcessor:
    """Advanced process and normalize registry data with smart extraction"""
    
    def __init__(self):
        self.warnings = []
        self.column_matcher = AdvancedColumnMatcher()
        self.address_parser = SmartAddressParser()
    
    def process(self, raw_data):
        """Process raw data to unified format with smart extraction"""
        
        if not raw_data:
            return []
        
        self.warnings = []
        
        df = pd.DataFrame(raw_data)
        
        self.column_matcher.match_columns(df)
        
        processed_data = []
        
        for idx, record in enumerate(raw_data):
            try:
                processed_record = self._normalize_record(record, idx)
                if processed_record:
                    processed_data.append(processed_record)
            except Exception as e:
                self.warnings.append(f"Row {idx + 1}: {str(e)}")
        
        return processed_data
    
    def _normalize_record(self, record, idx):
        """Normalize a single record to unified format with smart parsing"""
        
        # Get register name (try multiple sources)
        register_name = self.column_matcher.get_value(record, 'register_name')
        
        # If register_name not found, try to extract from display_name
        if not register_name:
            register_name = self.column_matcher.get_value(record, 'display_name')
        
        if not register_name:
            return None
        
        # Get display name
        display_name = self.column_matcher.get_value(record, 'display_name')
        if not display_name:
            # Use register_name as display_name, or extract cleaner version
            display_name = self._clean_display_name(register_name)
        
        # Get address and extract function code if embedded
        raw_address = self.column_matcher.get_value(record, 'address')
        extracted_fc, extracted_addr = self.address_parser.parse_address(raw_address, register_name)
        
        # Get function code (prefer extracted, then from data, then use extracted or default)
        function_code = self.column_matcher.get_value(record, 'function_code')
        if function_code:
            function_code = self._normalize_function_code(function_code)
        elif extracted_fc:
            function_code = extracted_fc
        else:
            function_code = 3
        
        # Get register type based on function code
        register_type = self.column_matcher.get_value(record, 'register_type')
        if not register_type:
            register_type = self._get_register_type_from_function_code(function_code)
        else:
            register_type = self._normalize_register_type(register_type)
        
        # Use extracted address or default to 0
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
            'Unit': str(unit).strip(),
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
        name = ' '.join(word.capitalize() for word in name.split())
        return name
    
    def _get_register_type_from_function_code(self, function_code):
        """Get register type based on Modbus function code"""
        fc_to_type = {
            1: 'Coil',
            2: 'Discrete Input',
            3: 'Input Register',
            4: 'Holding Register',
        }
        return fc_to_type.get(function_code, 'Holding Register')
    
    def _normalize_function_code(self, value):
        """Normalize function code to standard value"""
        
        if not value:
            return 3
        
        value_str = str(value).lower().strip()
        
        for key, code in FUNCTION_CODE_MAP.items():
            if key in value_str or value_str in key:
                return code
        
        try:
            code = int(value)
            if code in [1, 2, 3, 4, 16, 23]:
                return code
        except:
            pass
        
        return 3
    
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
        
        for key, data_type in DATA_TYPE_MAP.items():
            if key in value_str or value_str in key:
                return data_type
        
        return 'INT16'
    
    def _normalize_access_type(self, value):
        """Normalize access type to standard format"""
        
        if not value:
            return 'Read'
        
        value_str = str(value).lower().strip()
        
        for key, access in ACCESS_TYPE_MAP.items():
            if key in value_str or value_str in key:
                return access
        
        return 'Read'
    
    def _normalize_boolean(self, value, default=True):
        """Convert value to boolean"""
        
        if value is None:
            return default
        
        value_str = str(value).lower().strip()
        return value_str in ['true', 'yes', '1', 'enabled', 'active', 'on']
    
    def validate(self, data):
        """Validate processed data"""
        
        validation_results = {
            'is_valid': True,
            'warnings': self.warnings,
            'errors': []
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
        report += "-" * 50 + "\n"
        
        for field, column in self.column_matcher.column_map.items():
            confidence = self.column_matcher.confidence_scores.get(field, 0)
            confidence_pct = int(confidence * 100)
            report += f"{field:20s} -> {column:20s} ({confidence_pct}%)\n"
        
        unmapped = [field for field in self.column_matcher.FIELD_PATTERNS.keys() 
                   if field not in self.column_matcher.column_map]
        
        if unmapped:
            report += "\nUnmapped fields:\n"
            for field in unmapped:
                report += f"  - {field}\n"
        
        return report


# Keep backward compatibility
DataProcessor = AdvancedDataProcessor
