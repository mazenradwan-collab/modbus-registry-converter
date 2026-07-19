"""Advanced CSV file converter with intelligent header detection"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from converters.base_converter import BaseConverter


class SmartCSVReader:
    """Intelligently reads CSV files with complex structures"""
    
    def __init__(self):
        self.detected_header_row = None
        self.detected_data_start_row = None
        self.skipped_rows_info = []
    
    def detect_header_row(self, file_path: Path) -> int:
        """
        Detect which row contains the actual headers
        """
        
        try:
            # Read all rows without header
            df_raw = pd.read_csv(file_path, header=None)
            
            # Look for row that contains common field names
            common_fields = [
                'registername', 'name', 'label', 'address', 'addr',
                'functioncode', 'registertype', 'datatype', 'access',
                'modbusaddr', 'registerlabel', 'format', 'requesttype',
                'unit', 'polling', 'enabled', 'managerlabel', 'modulelabel'
            ]
            
            for idx, row in df_raw.iterrows():
                # Convert row to lowercase strings
                row_values = [str(val).lower().strip() for val in row if pd.notna(val)]
                
                # Count how many common fields are in this row
                matching_fields = sum(1 for val in row_values if any(field in val for field in common_fields))
                
                # If we find a row with multiple matching fields, it's likely the header
                if matching_fields >= 3:
                    self.detected_header_row = idx
                    return idx
            
            # If no header detected, assume first non-empty row
            for idx, row in df_raw.iterrows():
                if row.notna().sum() > 2:  # At least 3 non-empty cells
                    self.detected_header_row = idx
                    return idx
            
            self.detected_header_row = 0
            return 0
            
        except Exception as e:
            print(f"Error detecting header: {e}")
            self.detected_header_row = 0
            return 0
    
    def read_csv_smart(self, file_path: Path, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        Intelligently read CSV file with complex structure
        """
        
        header_row = self.detect_header_row(file_path)
        
        try:
            # Read CSV with detected header row
            df = pd.read_csv(
                file_path, 
                header=header_row, 
                skiprows=range(0, header_row),
                encoding=encoding
            )
            
            # Clean column names - remove extra spaces and empty names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Remove completely empty columns
            df = df.dropna(axis=1, how='all')
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Remove rows where all meaningful columns are empty
            meaningful_cols = [col for col in df.columns if col and not str(col).isspace()]
            if meaningful_cols:
                df = df.dropna(subset=meaningful_cols, how='all')
            
            # Convert to list of dicts
            records = df.to_dict('records')
            
            # Clean records - remove empty entries and standardize
            cleaned_records = []
            for record in records:
                # Remove None and NaN values, keep empty strings as None
                cleaned_record = {}
                has_data = False
                
                for key, value in record.items():
                    if pd.isna(value) or value is None:
                        cleaned_record[key] = None
                    elif isinstance(value, str) and not value.strip():
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                        has_data = True
                
                # Only add record if it has at least one non-empty field
                if has_data:
                    cleaned_records.append(cleaned_record)
            
            print(f"[CSV Smart Reader] Detected header at row: {self.detected_header_row}")
            print(f"[CSV Smart Reader] Read {len(cleaned_records)} records")
            print(f"[CSV Smart Reader] Columns: {list(df.columns)}")
            
            return cleaned_records
            
        except Exception as e:
            print(f"Error reading CSV with smart reader: {e}")
            raise


class CSVConverter(BaseConverter):
    """Advanced converter for CSV files with intelligent parsing"""
    
    def __init__(self):
        super().__init__()
        self.smart_reader = SmartCSVReader()
    
    def read(self, file_path):
        """
        Read data from CSV file using intelligent header detection
        
        Tries multiple encodings and uses smart header row detection
        """
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        last_error = None
        for encoding in encodings:
            try:
                self.data = self.smart_reader.read_csv_smart(file_path, encoding=encoding)
                print(f"[CSV Converter] Successfully read with encoding: {encoding}")
                return self.data
            except Exception as e:
                last_error = e
                print(f"[CSV Converter] Failed with encoding {encoding}: {e}")
                continue
        
        # If all encodings failed, raise the last error
        raise ValueError(f"Could not read CSV file. Last error: {str(last_error)}")
    
    def save_csv(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Save data to CSV file"""
        
        if not data:
            raise ValueError("No data to save")
        
        output_path = Path(output_path)
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"[CSV Converter] Saved {len(data)} records to {output_path}")
    
    def get_reader_report(self) -> str:
        """Get report of how CSV was read"""
        
        report = "CSV Reader Report:\n"
        report += "-" * 60 + "\n"
        report += f"Header row detected at: Row {self.smart_reader.detected_header_row}\n"
        report += f"Records read: {self.data.__len__() if self.data else 0}\n"
        
        return report
