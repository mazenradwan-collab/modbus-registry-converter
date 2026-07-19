"""Advanced CSV file converter with intelligent header detection for tab-separated files"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from converters.base_converter import BaseConverter


class SmartCSVReader:
    """Intelligently reads CSV files with complex structures, including tab-separated"""
    
    def __init__(self):
        self.detected_header_row = 0
        self.detected_data_start_row = 1
        self.separator = ','
        self.records_read = 0
        self.records_skipped = 0
    
    def detect_separator(self, file_path: Path) -> str:
        """Detect if file is comma or tab separated"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                
                # Count separators
                comma_count = first_line.count(',')
                tab_count = first_line.count('\t')
                
                if tab_count > comma_count:
                    return '\t'
                return ','
        except:
            return ','
    
    def read_csv_smart(self, file_path: Path, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        Intelligently read CSV/TSV file with complex structure
        """
        
        separator = self.detect_separator(file_path)
        
        try:
            # Read with detected separator
            df = pd.read_csv(
                file_path,
                sep=separator,
                encoding=encoding,
                dtype=str  # Read everything as string first
            )
            
            # Clean column names - remove extra spaces
            df.columns = [str(col).strip() for col in df.columns]
            
            print(f"[CSV Smart Reader] Detected separator: {'TAB' if separator == '\t' else 'COMMA'}")
            print(f"[CSV Smart Reader] Original columns: {list(df.columns)}")
            print(f"[CSV Smart Reader] Original rows: {len(df)}")
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Remove rows where ALL columns are empty/whitespace
            df_clean = df.copy()
            for col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna('').astype(str).str.strip()
            
            # Keep only rows that have at least some data
            df = df[df_clean.replace('', pd.NA).notna().any(axis=1)]
            
            print(f"[CSV Smart Reader] Rows after cleaning empty: {len(df)}")
            
            # Remove completely empty columns (all NaN or all empty strings)
            df = df.dropna(axis=1, how='all')
            
            # Also remove columns that are completely empty strings
            for col in df.columns:
                if df[col].astype(str).str.strip().eq('').all():
                    df = df.drop(columns=[col])
            
            print(f"[CSV Smart Reader] Columns after cleaning empty: {list(df.columns)}")
            print(f"[CSV Smart Reader] Final rows: {len(df)}")
            
            # Convert to list of dicts
            records = df.to_dict('records')
            
            # Clean records - remove empty entries and standardize
            cleaned_records = []
            skipped = 0
            
            for record in records:
                cleaned_record = {}
                has_data = False
                
                for key, value in record.items():
                    if pd.isna(value) or value is None:
                        cleaned_record[key] = None
                    elif isinstance(value, str):
                        cleaned_val = value.strip()
                        if cleaned_val:
                            cleaned_record[key] = cleaned_val
                            has_data = True
                        else:
                            cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                        has_data = True
                
                # Only add record if it has at least one non-empty field
                if has_data:
                    cleaned_records.append(cleaned_record)
                else:
                    skipped += 1
            
            self.records_read = len(cleaned_records)
            self.records_skipped = skipped
            
            print(f"[CSV Smart Reader] Records with data: {self.records_read}")
            print(f"[CSV Smart Reader] Empty records skipped: {self.records_skipped}")
            
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
        
        Supports both comma and tab-separated files
        Automatically detects and skips empty rows/columns
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
                print(f"[CSV Converter] Total records loaded: {len(self.data)}")
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
        report += f"Records read: {self.smart_reader.records_read}\n"
        report += f"Empty records skipped: {self.smart_reader.records_skipped}\n"
        
        return report
