"""Data processor for normalizing and validating registry data"""

import pandas as pd
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


class DataProcessor:
    """Process and normalize registry data"""
    
    def __init__(self):
        self.warnings = []
    
    def process(self, raw_data):
        """Process raw data to unified format"""
        self.warnings = []
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
        
        # Extract and clean values
        register_name = self._get_field(record, ['RegisterName', 'Name', 'Register'])
        if not register_name:
            return None  # Skip if no name
        
        display_name = self._get_field(record, ['DisplayName', 'Description', 'Label'])
        if not display_name:
            display_name = register_name
        
        function_code = self._get_field(record, ['FunctionCode', 'Function', 'Code'])
        function_code = self._normalize_function_code(function_code)
        
        register_type = self._get_field(record, ['RegisterType', 'Type'])
        register_type = self._normalize_register_type(register_type)
        
        address = self._get_field(record, ['Address', 'Addr', 'Offset'])
        try:
            address = int(address) if address else 0
        except:
            address = 0
        
        data_type = self._get_field(record, ['DataType', 'Type', 'Format'])
        data_type = self._normalize_data_type(data_type)
        
        register_count = self._get_field(record, ['RegisterCount', 'Count', 'Size'])
        try:
            register_count = int(register_count) if register_count else DEFAULT_REGISTER_COUNT
        except:
            register_count = DEFAULT_REGISTER_COUNT
        
        scale_factor = self._get_field(record, ['ScaleFactor', 'Scale'])
        try:
            scale_factor = float(scale_factor) if scale_factor else DEFAULT_SCALE_FACTOR
        except:
            scale_factor = DEFAULT_SCALE_FACTOR
        
        unit = self._get_field(record, ['Unit', 'Units'])
        if not unit:
            unit = ''
        
        access = self._get_field(record, ['Access', 'Permission'])
        access = self._normalize_access_type(access)
        
        polling_ms = self._get_field(record, ['Polling_ms', 'Polling', 'PollInterval'])
        try:
            polling_ms = int(polling_ms) if polling_ms else DEFAULT_POLLING_MS
        except:
            polling_ms = DEFAULT_POLLING_MS
        
        enabled = self._get_field(record, ['Enabled', 'Active', 'Status'])
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
    
    def _get_field(self, record, field_names):
        """Get field value from record using multiple possible field names"""
        for field_name in field_names:
            for key in record.keys():
                if key.lower() == field_name.lower():
                    value = record[key]
                    if value is None or (isinstance(value, float) and pd.isna(value)):
                        return None
                    return value
        return None
    
    def _normalize_function_code(self, value):
        """Normalize function code to standard value"""
        if not value:
            return 3  # Default to Input Register
        
        value_str = str(value).lower().strip()
        
        # Try to match with map
        for key, code in FUNCTION_CODE_MAP.items():
            if key in value_str or value_str in key:
                return code
        
        # Try to parse as number
        try:
            code = int(value)
            if code in FUNCTION_CODE_MAP.values():
                return code
        except:
            pass
        
        return 3  # Default
    
    def _normalize_register_type(self, value):
        """Normalize register type to standard format"""
        if not value:
            return 'Holding Register'
        
        value_str = str(value).lower().strip()
        
        # Try to match with map
        for key, reg_type in REGISTER_TYPE_MAP.items():
            if key in value_str or value_str in key:
                return reg_type
        
        return 'Holding Register'  # Default
    
    def _normalize_data_type(self, value):
        """Normalize data type to standard format"""
        if not value:
            return 'INT16'
        
        value_str = str(value).lower().strip()
        
        # Try to match with map
        for key, data_type in DATA_TYPE_MAP.items():
            if key in value_str or value_str in key:
                return data_type
        
        return 'INT16'  # Default
    
    def _normalize_access_type(self, value):
        """Normalize access type to standard format"""
        if not value:
            return 'Read'
        
        value_str = str(value).lower().strip()
        
        # Try to match with map
        for key, access in ACCESS_TYPE_MAP.items():
            if key in value_str or value_str in key:
                return access
        
        return 'Read'  # Default
    
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
            # Check for required fields
            if not record.get('RegisterName'):
                validation_results['errors'].append(f"Row {idx + 1}: Missing RegisterName")
                validation_results['is_valid'] = False
            
            # Check address is valid
            if not isinstance(record.get('Address'), int) or record.get('Address') < 0:
                validation_results['warnings'].append(f"Row {idx + 1}: Invalid Address")
            
            # Check Polling_ms is positive
            if record.get('Polling_ms', 0) <= 0:
                validation_results['warnings'].append(f"Row {idx + 1}: Polling_ms should be positive")
        
        return validation_results
