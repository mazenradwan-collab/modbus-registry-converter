"""Intelligent data processor for normalizing and validating registry data"""

import pandas as pd
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


class ColumnMatcher:
    """Intelligent column name matcher using fuzzy matching"""
    
    FIELD_PATTERNS = {
        'register_name': ['registername', 'register_name', 'name', 'id', 'description', 'desc'],
        'display_name': ['displayname', 'display_name', 'label', 'description', 'desc', 'display'],
        'function_code': ['functioncode', 'function_code', 'function', 'code', 'fc', 'func'],
        'register_type': ['registertype', 'register_type', 'type', 'regtype', 'reg_type'],
        'address': ['address', 'addr', 'offset', 'register', 'reg_addr', 'modbus_address'],
        'data_type': ['datatype', 'data_type', 'dtype', 'format', 'value_type'],
        'register_count': ['registercount', 'register_count', 'count', 'size', 'length', 'qty'],
        'scale_factor': ['scalefactor', 'scale_factor', 'scale', 'multiplier', 'factor'],
        'unit': ['unit', 'units', 'uom', 'measurement'],
        'access': ['access', 'permission', 'permissions', 'accesstype', 'access_type', 'mode'],
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


class DataProcessor:
    """Process and normalize registry data"""
    
    def __init__(self):
        self.warnings = []
        self.column_matcher = ColumnMatcher()
    
    def process(self, raw_data):
        """Process raw data to unified format"""
        
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
        """Normalize a single record to unified format"""
        
        register_name = self.column_matcher.get_value(record, 'register_name')
        if not register_name:
            return None
        
        display_name = self.column_matcher.get_value(record, 'display_name')
        if not display_name:
            display_name = register_name
        
        function_code = self.column_matcher.get_value(record, 'function_code')
        function_code = self._normalize_function_code(function_code)
        
        register_type = self.column_matcher.get_value(record, 'register_type')
        register_type = self._normalize_register_type(register_type)
        
        address = self.column_matcher.get_value(record, 'address')
        try:
            address = int(address) if address else 0
        except:
            address = 0
        
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
            if code in FUNCTION_CODE_MAP.values():
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
