"""Advanced intelligent data processor with flexible field detection"""

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


class FlexibleColumnMatcher:
    """Flexible column matcher that finds any field that could be a name"""
    
    def __init__(self):
        self.column_map = {}
        self.all_columns = []
        self.name_columns = []  # Columns that look like names
    
    def match_columns(self, dataframe):
        """Match columns and find name fields"""
        
        self.all_columns = list(dataframe.columns)
        df_columns_lower = [str(col).lower().strip() for col in self.all_columns]
        
        print(f"\n[ColumnMatcher] Available columns: {self.all_columns}")
        
        # Find columns that look like names
        name_keywords = ['name', 'label', 'registerlabel', 'register_label', 'description', 'id']
        self.name_columns = []
        
        for i, col_lower in enumerate(df_columns_lower):
            for keyword in name_keywords:
                if keyword in col_lower or col_lower in keyword:
                    self.name_columns.append(self.all_columns[i])
                    break
        
        print(f"[ColumnMatcher] Name columns found: {self.name_columns}")
        
        # Map standard fields
        field_patterns = {
            'address': ['address', 'modbusaddr', 'modbus_addr', 'addr'],
            'data_type': ['datatype', 'data_type', 'format', 'dtype'],
            'access': ['access', 'requesttype', 'request_type'],
            'register_count': ['registercount', 'register_count', 'count'],
            'scale_factor': ['scalefactor', 'scale_factor', 'scale', 'mask'],
            'unit': ['unit', 'units'],
            'polling_ms': ['polling', 'polling_ms'],
            'enabled': ['enabled', 'active'],
        }
        
        self.column_map = {}
        
        for field, patterns in field_patterns.items():
            for i, col_lower in enumerate(df_columns_lower):
                for pattern in patterns:
                    if pattern in col_lower or col_lower in pattern:
                        self.column_map[field] = self.all_columns[i]
                        break
                if field in self.column_map:
                    break
        
        print(f"[ColumnMatcher] Mapped fields: {self.column_map}")
        
        return self.column_map
    
    def get_name_from_record(self, record):
        """Get name from record using any name column"""
        
        # Try each name column
        for name_col in self.name_columns:
            value = record.get(name_col)
            if value is not None:
                val_str = str(value).strip()
                if val_str and val_str.lower() not in ['nan', 'none', '']:
                    return val_str
        
        return None
    
    def get_value(self, record, field):
        """Get value from record"""
        
        if field not in self.column_map:
            return None
        
        column = self.column_map[field]
        value = record.get(column)
        
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        
        return value


class SmartAddressParser:
    """Parse Modbus addresses"""
    
    FUNCTION_CODE_RANGES = {
        1: (0, 9999),
        2: (10000, 19999),
        3: (30000, 39999),
        4: (40000, 49999),
    }
    
    def parse_address(self, address_value):
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
        self.column_matcher = FlexibleColumnMatcher()
        self.address_parser = SmartAddressParser()
        self.skipped_rows = 0
        self.processed_rows = 0
    
    def process(self, raw_data):
        """Process raw data"""
        
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
        
        print(f"\n[DataProcessor] Starting processing...")
        print(f"[DataProcessor] Total records to process: {len(raw_data_clean)}")
        
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
        
        print(f"\n[DataProcessor] Processing completed:")
        print(f"  Processed: {self.processed_rows}")
        print(f"  Skipped: {self.skipped_rows}")
        print(f"  Total: {len(raw_data_clean)}\n")
        
        return processed_data
    
    def _normalize_record(self, record, idx):
        """Normalize a single record"""
        
        # Get name using flexible matcher
        register_name = self.column_matcher.get_name_from_record(record)
        
        if not register_name:
            return None
        
        register_name = str(register_name).strip()
        if not register_name or register_name.lower() in ['nan', '', 'none']:
            return None
        
        display_name = self._clean_display_name(register_name)
        
        # Get address
        raw_address = self.column_matcher.get_value(record, 'address')
        extracted_fc, extracted_addr = self.address_parser.parse_address(raw_address)
        
        # Get function code
        function_code = extracted_fc if extracted_fc else 4
        
        # Get register type
        register_type = self._get_register_type_from_function_code(function_code)
        
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
        
        return validation_results


DataProcessor = AdvancedDataProcessor
