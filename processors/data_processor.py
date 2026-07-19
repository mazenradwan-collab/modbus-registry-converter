"""Advanced intelligent data processor with smart address parsing - Fixed version"""

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
    """Advanced intelligent column name matcher"""
    
    FIELD_PATTERNS = {
        'register_name': ['registername', 'register_name', 'registerlabel', 'name', 'id', 'description', 'desc', 'label'],
        'display_name': ['displayname', 'display_name', 'name', 'label', 'description', 'registerlabel'],
        'function_code': ['functioncode', 'function_code', 'requesttype', 'request_type', 'function', 'code', 'fc'],
        'register_type': ['registertype', 'register_type', 'type', 'regtype'],
        'address': ['address', 'modbusaddr', 'modbus_addr', 'addr', 'offset', 'register'],
        'data_type': ['datatype', 'data_type', 'format', 'dtype'],
        'register_count': ['registercount', 'register_count', 'count', 'numberofregisters', 'size'],
        'scale_factor': ['scalefactor', 'scale_factor', 'scale', 'mask', 'multiplier'],
        'unit': ['unit', 'units', 'uom'],
        'access': ['access', 'requesttype', 'request_type', 'permission', 'mode'],
        'polling_ms': ['polling_ms', 'polling', 'interval'],
        'enabled': ['enabled', 'active', 'status']
    }
    
    def __init__(self):
        self.column_map = {}
        self.confidence_scores = {}
        self.all_columns = []
    
    def match_columns(self, dataframe):
        """Match DataFrame columns to standard fields"""
        
        self.all_columns = list(dataframe.columns)
        df_columns = [str(col).lower().strip() for col in self.all_columns]
        self.column_map = {}
        self.confidence_scores = {}
        
        for field, patterns in self.FIELD_PATTERNS.items():
            best_match = None
            best_score = 0
            
            for i, df_col in enumerate(df_columns):
                if not df_col or df_col.isspace():
                    continue
                    
                if df_col in patterns:
                    best_match = self.all_columns[i]
                    best_score = 1.0
                    break
                
                for pattern in patterns:
                    score = self._similarity_score(df_col, pattern)
                    if score > best_score:
                        best_score = score
                        best_match = self.all_columns[i]
            
            if best_match and best_score > 0.5:
                self.column_map[field] = best_match
                self.confidence_scores[field] = best_score
        
        return self.column_map, self.confidence_scores
    
    def _similarity_score(self, str1, str2):
        """Calculate similarity between strings"""
        str1_clean = str1.replace('_', '').replace(' ', '')
        str2_clean = str2.replace('_', '').replace(' ', '')
        return SequenceMatcher(None, str1_clean, str2_clean).ratio()
    
    def get_value(self, record, field):
        """Get value from record using mapped column"""
        if field not in self.column_map:
            return None
        
        column = self.column_map[field]
        value = record.get(column)
        
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        
        return value


class SmartAddressParser:
    """Parse Modbus addresses with function code extraction"""
    
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
        """Parse address and extract function code if embedded"""
        
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
        
        # Check if first digit is function code
        addr_str_num = str(addr_int)
        
        if len(addr_str_num) >= 5:
            first_digit = int(addr_str_num[0])
            
            if first_digit in [1, 2, 3, 4]:
                potential_addr = addr_int - (first_digit * 10000)
                
                if 0 <= potential_addr <= 65535:
                    extracted_fc = first_digit
                    extracted_addr = potential_addr
        
        if extracted_addr is None:
            extracted_addr = addr_int
            extracted_fc = self._determine_function_code_by_address(addr_int)
        
        return extracted_fc, extracted_addr
    
    def _determine_function_code_by_address(self, address):
        """Determine function code from address range"""
        for fc, (min_addr, max_addr) in self.FUNCTION_CODE_RANGES.items():
            if min_addr <= address <= max_addr:
                return fc
        return 4


class AdvancedDataProcessor:
    """Process and normalize registry data"""
    
    def __init__(self):
        self.warnings = []
        self.column_matcher = AdvancedColumnMatcher()
        self.address_parser = SmartAddressParser()
        self.skipped_rows = 0
        self.processed_rows = 0
    
    def process(self, raw_data):
        """Process raw data to unified format"""
        
        if not raw_data:
            return []
        
        self.warnings = []
        self.skipped_rows = 0
        self.processed_rows = 0
        
        try:
            df = pd.DataFrame(raw_data)
            df = df.dropna(how='all')
            raw_data_clean = df.to_dict('records')
        except:
            raw_data_clean = raw_data
        
        self.column_matcher.match_columns(pd.DataFrame(raw_data_clean))
        
        print(f"\n[DataProcessor] Column Mapping:")
        for field, col in self.column_matcher.column_map.items():
            score = self.column_matcher.confidence_scores.get(field, 0)
            print(f"  {field:20s} <- {col:20s} ({int(score*100)}%)")
        
        processed_data = []
        
        for idx, record in enumerate(raw_data_clean):
            try:
                processed_record = self._normalize_record(record, idx)
                if processed_record:
                    processed_data.append(processed_record)
                    self.processed_rows += 1
                else:
                    self.skipped_rows += 1
            except Exception as e:
                self.warnings.append(f"Row {idx + 1}: {str(e)}")
                self.skipped_rows += 1
        
        print(f"\n[DataProcessor] Processing Summary:")
        print(f"  Total rows: {len(raw_data_clean)}")
        print(f"  Processed: {self.processed_rows}")
        print(f"  Skipped: {self.skipped_rows}")
        
        return processed_data
    
    def _normalize_record(self, record, idx):
        """Normalize a single record"""
        
        # Get register name - CRITICAL: accept ANY non-empty value
        register_name = self.column_matcher.get_value(record, 'register_name')
        
        if not register_name:
            return None
        
        register_name = str(register_name).strip()
        if not register_name or register_name.lower() in ['nan', '', 'none']:
            return None
        
        # Get display name
        display_name = self.column_matcher.get_value(record, 'display_name')
        if not display_name:
            display_name = self._clean_display_name(register_name)
        
        # Get address
        raw_address = self.column_matcher.get_value(record, 'address')
        extracted_fc, extracted_addr = self.address_parser.parse_address(raw_address, register_name)
        
        # Get function code
        function_code = self.column_matcher.get_value(record, 'function_code')
        if function_code:
            function_code = self._normalize_function_code(function_code)
        elif extracted_fc:
            function_code = extracted_fc
        else:
            function_code = 4
        
        # Get register type
        register_type = self.column_matcher.get_value(record, 'register_type')
        if not register_type:
            register_type = self._get_register_type_from_function_code(function_code)
        else:
            register_type = self._normalize_register_type(register_type)
        
        # Use extracted address
        address = extracted_addr if extracted_addr is not None else 0
        
        # Data type
        data_type = self.column_matcher.get_value(record, 'data_type')
        data_type = self._normalize_data_type(data_type)
        
        # Register count
        register_count = self.column_matcher.get_value(record, 'register_count')
        try:
            register_count = int(register_count) if register_count else DEFAULT_REGISTER_COUNT
        except:
            register_count = DEFAULT_REGISTER_COUNT
        
        # Scale factor
        scale_factor = self.column_matcher.get_value(record, 'scale_factor')
        try:
            scale_factor = float(scale_factor) if scale_factor else DEFAULT_SCALE_FACTOR
        except:
            scale_factor = DEFAULT_SCALE_FACTOR
        
        # Unit
        unit = self.column_matcher.get_value(record, 'unit')
        unit = str(unit).strip() if unit else ''
        
        # Access
        access = self.column_matcher.get_value(record, 'access')
        access = self._normalize_access_type(access)
        
        # Polling
        polling_ms = self.column_matcher.get_value(record, 'polling_ms')
        try:
            polling_ms = int(polling_ms) if polling_ms else DEFAULT_POLLING_MS
        except:
            polling_ms = DEFAULT_POLLING_MS
        
        # Enabled
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
            'Unit': unit,
            'Access': access,
            'Polling_ms': polling_ms,
            'Enabled': enabled
        }
    
    def _clean_display_name(self, register_name):
        """Clean register name for display"""
        name = str(register_name).strip()
        name = name.replace('_', ' ')
        name = ' '.join(word.capitalize() for word in name.split() if word)
        return name
    
    def _get_register_type_from_function_code(self, function_code):
        """Get register type from function code"""
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
        """Normalize function code"""
        if not value:
            return 4
        
        value_str = str(value).lower().strip()
        
        if 'rw' in value_str or 'read-write' in value_str:
            return 4
        elif 'r' in value_str:
            return 3
        elif 'w' in value_str:
            return 16
        
        try:
            code = int(value)
            if code in [1, 2, 3, 4, 16, 23]:
                return code
        except:
            pass
        
        return 4
    
    def _normalize_register_type(self, value):
        """Normalize register type"""
        if not value:
            return 'Holding Register'
        
        value_str = str(value).lower().strip()
        
        for key, reg_type in REGISTER_TYPE_MAP.items():
            if key in value_str:
                return reg_type
        
        return 'Holding Register'
    
    def _normalize_data_type(self, value):
        """Normalize data type"""
        if not value:
            return 'INT16'
        
        value_str = str(value).lower().strip()
        
        type_map = {
            'uint32': 'UINT32',
            'int32': 'INT32',
            'float': 'FLOAT32',
            'f32': 'FLOAT32',
            'ascii': 'ASCII',
            'datetime': 'DATETIME',
            'maskedbool': 'BOOL',
            'uint': 'UINT16',
            'int': 'INT16',
            'bool': 'BOOL',
        }
        
        for key, dtype in type_map.items():
            if key in value_str:
                return dtype
        
        return 'INT16'
    
    def _normalize_access_type(self, value):
        """Normalize access type"""
        if not value:
            return 'Read'
        
        value_str = str(value).lower().strip()
        
        if 'rw' in value_str:
            return 'Read/Write'
        elif 'w' in value_str:
            return 'Write'
        
        return 'Read'
    
    def _normalize_boolean(self, value, default=True):
        """Convert to boolean"""
        if value is None:
            return default
        
        value_str = str(value).lower().strip()
        return value_str in ['true', 'yes', '1', 'enabled', 'active', 'on']
    
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
        
        return validation_results
    
    def get_column_mapping_report(self):
        """Get column mapping report"""
        
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
        
        report += f"\nProcessing Summary:\n"
        report += f"  Total rows processed: {self.processed_rows}\n"
        report += f"  Total rows skipped: {self.skipped_rows}\n"
        
        return report


DataProcessor = AdvancedDataProcessor
