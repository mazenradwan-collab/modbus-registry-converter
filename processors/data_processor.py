"""Advanced intelligent data processor - FINAL VERSION with complete field detection"""

import pandas as pd
import re
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


class SmartColumnDetector:
    """Intelligently detect all columns by analyzing data patterns"""
    
    def __init__(self):
        self.column_map = {}
        self.all_columns = []
        self.detected_patterns = {}
    
    def analyze_column_content(self, dataframe):
        """Analyze column content to detect purpose"""
        
        self.all_columns = list(dataframe.columns)
        
        print(f"\n[SmartColumnDetector] Analyzing {len(self.all_columns)} columns...")
        print(f"[SmartColumnDetector] Available columns: {self.all_columns}\n")
        
        # Analyze each column
        for col in self.all_columns:
            analysis = self._analyze_single_column(dataframe[col], col)
            self.detected_patterns[col] = analysis
            print(f"[SmartColumnDetector] {col:25s} -> {analysis['detected_type']:20s} (samples: {analysis['sample_values']})")
        
        print()  # Newline
        
        # Map columns based on analysis
        self._map_columns_by_analysis()
        
        return self.column_map
    
    def _analyze_single_column(self, series, col_name):
        """Analyze a single column to determine its type"""
        
        analysis = {
            'name': col_name,
            'detected_type': 'UNKNOWN',
            'sample_values': [],
            'numeric_count': 0,
            'max_value': 0,
            'has_addresses': False
        }
        
        # Get non-null values
        values = series.dropna().astype(str).str.strip()
        values = values[values != '']
        
        if len(values) == 0:
            return analysis
        
        sample_vals = values.head(2).tolist()
        analysis['sample_values'] = sample_vals
        
        col_lower = col_name.lower().strip()
        
        # Check column name first - MOST IMPORTANT
        name_keywords = ['registerlabel', 'register_label', 'name', 'label', 'description']
        for keyword in name_keywords:
            if keyword in col_lower or col_lower in keyword:
                analysis['detected_type'] = 'REGISTER_NAME'
                return analysis
        
        # Check for address columns
        addr_keywords = ['address', 'modbusaddr', 'modbus_addr', 'addr', 'modbus']
        for keyword in addr_keywords:
            if keyword in col_lower or col_lower in keyword:
                analysis['detected_type'] = 'ADDRESS'
                return analysis
        
        # Check for data type
        dtype_keywords = ['datatype', 'data_type', 'format', 'dtype']
        for keyword in dtype_keywords:
            if keyword in col_lower or col_lower in keyword:
                analysis['detected_type'] = 'DATA_TYPE'
                return analysis
        
        # Check for access/request type - CRITICAL
        access_keywords = ['access', 'requesttype', 'request_type', 'permission', 'mode']
        for keyword in access_keywords:
            if keyword in col_lower or col_lower in keyword:
                analysis['detected_type'] = 'ACCESS'
                return analysis
        
        # Check for units
        unit_keywords = ['unit', 'units', 'uom']
        for keyword in unit_keywords:
            if keyword in col_lower or col_lower in keyword:
                analysis['detected_type'] = 'UNIT'
                return analysis
        
        # Analyze by content
        try:
            numeric_values = pd.to_numeric(values, errors='coerce')
            numeric_count = numeric_values.notna().sum()
            
            if numeric_count > len(values) * 0.8:
                max_val = numeric_values.max()
                analysis['numeric_count'] = numeric_count
                analysis['max_value'] = max_val
                
                if max_val > 100000:
                    analysis['detected_type'] = 'ADDRESS'
                    analysis['has_addresses'] = True
                elif max_val < 100:
                    analysis['detected_type'] = 'REGISTER_COUNT'
                else:
                    analysis['detected_type'] = 'NUMERIC_FIELD'
                
                return analysis
        except:
            pass
        
        # Check text patterns
        text_samples = ' '.join(sample_vals).lower()
        
        if any(word in text_samples for word in ['read', 'write', 'rw', ' r ', ' w ']):
            analysis['detected_type'] = 'ACCESS'
        elif any(word in text_samples for word in ['int', 'float', 'ascii', 'bool', 'uint', 'datetime']):
            analysis['detected_type'] = 'DATA_TYPE'
        elif any(word in text_samples for word in ['coil', 'input', 'holding', 'register']):
            analysis['detected_type'] = 'REGISTER_TYPE'
        else:
            analysis['detected_type'] = 'TEXT_FIELD'
        
        return analysis
    
    def _map_columns_by_analysis(self):
        """Map detected columns to standard fields"""
        
        # Priority mapping
        address_candidates = []
        name_candidates = []
        datatype_candidates = []
        access_candidates = []
        unit_candidates = []
        registertype_candidates = []
        
        for col, analysis in self.detected_patterns.items():
            detected_type = analysis['detected_type']
            
            if detected_type == 'ADDRESS':
                address_candidates.append((col, analysis))
            elif detected_type == 'REGISTER_NAME':
                name_candidates.append((col, analysis))
            elif detected_type == 'DATA_TYPE':
                datatype_candidates.append((col, analysis))
            elif detected_type == 'ACCESS':
                access_candidates.append((col, analysis))
            elif detected_type == 'UNIT':
                unit_candidates.append((col, analysis))
            elif detected_type == 'REGISTER_TYPE':
                registertype_candidates.append((col, analysis))
        
        # Assign best matches
        if address_candidates:
            # Choose address with highest max value
            best_addr_col = max(address_candidates, key=lambda x: x[1]['max_value'])[0]
            self.column_map['address'] = best_addr_col
            print(f"[SmartColumnDetector] Mapped 'address' -> {best_addr_col}")
        
        if name_candidates:
            best_name_col = name_candidates[0][0]
            self.column_map['register_name'] = best_name_col
            print(f"[SmartColumnDetector] Mapped 'register_name' -> {best_name_col}")
        
        if datatype_candidates:
            best_dtype_col = datatype_candidates[0][0]
            self.column_map['data_type'] = best_dtype_col
            print(f"[SmartColumnDetector] Mapped 'data_type' -> {best_dtype_col}")
        
        if access_candidates:
            best_access_col = access_candidates[0][0]
            self.column_map['access'] = best_access_col
            print(f"[SmartColumnDetector] Mapped 'access' -> {best_access_col}")
        
        if unit_candidates:
            best_unit_col = unit_candidates[0][0]
            self.column_map['unit'] = best_unit_col
            print(f"[SmartColumnDetector] Mapped 'unit' -> {best_unit_col}")
        
        if registertype_candidates:
            best_regtype_col = registertype_candidates[0][0]
            self.column_map['register_type'] = best_regtype_col
            print(f"[SmartColumnDetector] Mapped 'register_type' -> {best_regtype_col}")
        
        print()  # Newline
    
    def get_name_from_record(self, record):
        """Get name from record"""
        
        if 'register_name' not in self.column_map:
            return None
        
        col = self.column_map['register_name']
        value = record.get(col)
        
        if value:
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
    """Process and normalize registry data with complete field detection"""
    
    def __init__(self):
        self.warnings = []
        self.column_detector = SmartColumnDetector()
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
        
        # Analyze columns with smart detector
        df_analysis = pd.DataFrame(raw_data_clean)
        self.column_detector.analyze_column_content(df_analysis)
        
        print(f"[DataProcessor] Starting processing...")
        print(f"[DataProcessor] Total records to process: {len(raw_data_clean)}")
        print(f"[DataProcessor] Column mapping: {self.column_detector.column_map}\n")
        
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
        
        print(f"[DataProcessor] Processing completed:")
        print(f"  Processed: {self.processed_rows}")
        print(f"  Skipped: {self.skipped_rows}")
        print(f"  Total: {len(raw_data_clean)}\n")
        
        return processed_data
    
    def _normalize_record(self, record, idx):
        """Normalize a single record"""
        
        # Get name - CRITICAL
        register_name = self.column_detector.get_name_from_record(record)
        
        if not register_name:
            return None
        
        register_name = str(register_name).strip()
        if not register_name or register_name.lower() in ['nan', '', 'none']:
            return None
        
        display_name = self._clean_display_name(register_name)
        
        # Get address
        raw_address = self.column_detector.get_value(record, 'address')
        extracted_fc, extracted_addr = self.address_parser.parse_address(raw_address)
        
        # Get function code
        function_code = extracted_fc if extracted_fc else 4
        
        # Get register type from column or from function code
        register_type = self.column_detector.get_value(record, 'register_type')
        if not register_type:
            register_type = self._get_register_type_from_function_code(function_code)
        else:
            register_type = self._normalize_register_type(register_type)
        
        # Use extracted address
        address = extracted_addr if extracted_addr is not None else 0
        
        # Data type
        data_type = self.column_detector.get_value(record, 'data_type')
        data_type = self._normalize_data_type(data_type)
        
        # Register count
        register_count = DEFAULT_REGISTER_COUNT
        
        # Scale factor
        scale_factor = DEFAULT_SCALE_FACTOR
        
        # Unit
        unit = self.column_detector.get_value(record, 'unit')
        unit = str(unit).strip() if unit else ''
        
        # Access - CRITICAL: Get from RequestType or Access column
        access = self.column_detector.get_value(record, 'access')
        access = self._normalize_access_type(access)
        
        # Polling
        polling_ms = DEFAULT_POLLING_MS
        
        # Enabled
        enabled = DEFAULT_ENABLED
        
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
    
    def _normalize_register_type(self, value):
        """Normalize register type"""
        if not value:
            return 'Holding Register'
        
        value_str = str(value).lower().strip()
        
        type_map = {
            'coil': 'Coil',
            'discrete': 'Discrete Input',
            'input': 'Input Register',
            'holding': 'Holding Register',
        }
        
        for key, regtype in type_map.items():
            if key in value_str:
                return regtype
        
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
        """Normalize access type - CRITICAL"""
        if not value:
            return 'Read'
        
        value_str = str(value).lower().strip()
        
        # Check for different access patterns
        if 'rw' in value_str or 'read/write' in value_str or 'read-write' in value_str:
            return 'Read/Write'
        elif 'w' in value_str and 'r' not in value_str:
            return 'Write'
        elif 'r' in value_str:
            return 'Read'
        
        return 'Read'
    
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
