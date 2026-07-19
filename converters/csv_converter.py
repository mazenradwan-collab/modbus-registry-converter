"""Advanced CSV file converter - DEBUG VERSION with explicit handling"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from converters.base_converter import BaseConverter


class SmartCSVReader:
    """Intelligently reads CSV files with proper header detection"""
    
    def __init__(self):
        self.detected_header_row = 0
        self.detected_separator = None
        self.records_read = 0
        self.records_skipped = 0
    
    def detect_separator_and_read(self, file_path: Path, encoding: str = 'utf-8'):
        """Try multiple separators and return best result"""
        
        separators_to_try = ['\t', ',', ';', '|']
        best_result = None
        best_columns = 0
        best_separator = None
        
        for sep in separators_to_try:
            try:
                # Read first 10 lines to test separator
                df_test = pd.read_csv(
                    file_path, 
                    sep=sep, 
                    encoding=encoding, 
                    nrows=10,
                    header=0
                )
                num_cols = len(df_test.columns)
                
                print(f"[CSV Reader] Testing separator {repr(sep)}: {num_cols} columns")
                print(f"[CSV Reader]   Column names: {list(df_test.columns)[:5]}...")
                
                if num_cols > best_columns:
                    best_columns = num_cols
                    best_separator = sep
                
            except Exception as e:
                print(f"[CSV Reader] Separator {repr(sep)} failed: {type(e).__name__}")
                continue
        
        if best_separator is None:
            raise ValueError("Could not determine file separator")
        
        self.detected_separator = best_separator
        print(f"\n[CSV Reader] SELECTED separator: {repr(best_separator)} ({best_columns} columns)\n")
        
        return best_separator
    
    def read_csv_smart(self, file_path: Path, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """Intelligently read CSV file with proper header detection"""
        
        # Detect best separator
        separator = self.detect_separator_and_read(file_path, encoding)
        
        try:
            # Read with detected separator and first row as header
            df = pd.read_csv(
                file_path,
                sep=separator,
                encoding=encoding,
                dtype=str,
                header=0  # CRITICAL: First row is header
            )
            
            print(f"[CSV Reader] Successfully read with header=0:")
            print(f"  Total rows: {len(df)}")
            print(f"  Total columns: {len(df.columns)}")
            print(f"  Actual column names: {list(df.columns)}\n")
            
            # Verify columns are real (not Unnamed)
            unnamed_count = sum(1 for col in df.columns if 'Unnamed' in str(col))
            if unnamed_count > 0:
                print(f"[CSV Reader] WARNING: Found {unnamed_count} 'Unnamed' columns!")
                print(f"[CSV Reader] This means the separator might be wrong or header parsing failed\n")
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Clean whitespace in all cells
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('').astype(str).str.strip()
            
            # Remove rows where ALL columns are empty
            df_mask = (df.replace('', pd.NA).notna().any(axis=1))
            df = df[df_mask]
            
            print(f"[CSV Reader] After removing empty rows: {len(df)} rows")
            
            # Remove completely empty columns
            df = df.dropna(axis=1, how='all')
            
            # Remove columns that are all empty strings
            cols_to_keep = []
            for col in df.columns:
                if not (df[col].astype(str).str.strip() == '').all():
                    cols_to_keep.append(col)
            
            df = df[cols_to_keep]
            
            print(f"[CSV Reader] After removing empty columns: {len(df.columns)} columns")
            print(f"[CSV Reader] Final column names: {list(df.columns)}\n")
            
            # Convert to list of dicts
            records = df.to_dict('records')
            
            # Clean records
            cleaned_records = []
            
            for record in records:
                cleaned_record = {}
                has_data = False
                
                for key, value in record.items():
                    if pd.isna(value) or value is None or value == '':
                        continue
                    
                    if isinstance(value, str):
                        cleaned_val = value.strip()
                        if cleaned_val:
                            cleaned_record[key] = cleaned_val
                            has_data = True
                    else:
                        cleaned_record[key] = value
                        has_data = True
                
                if has_data:
                    cleaned_records.append(cleaned_record)
            
            self.records_read = len(cleaned_records)
            self.records_skipped = len(records) - len(cleaned_records)
            
            print(f"[CSV Reader] Final result:")
            print(f"  Records with data: {self.records_read}")
            print(f"  Empty records removed: {self.records_skipped}\n")
            
            return cleaned_records
            
        except Exception as e:
            print(f"[CSV Reader] ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise


class CSVConverter(BaseConverter):
    """Advanced converter for CSV files"""
    
    def __init__(self):
        super().__init__()
        self.smart_reader = SmartCSVReader()
    
    def read(self, file_path):
        """Read data from CSV file"""
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        last_error = None
        for encoding in encodings:
            try:
                print(f"[CSV Converter] Trying encoding: {encoding}")
                self.data = self.smart_reader.read_csv_smart(file_path, encoding=encoding)
                print(f"[CSV Converter] Successfully read with encoding: {encoding}")
                print(f"[CSV Converter] Total records: {len(self.data)}\n")
                return self.data
            except Exception as e:
                last_error = e
                print(f"[CSV Converter] Failed with {encoding}\n")
                continue
        
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
        report += f"Separator detected: {repr(self.smart_reader.detected_separator)}\n"
        report += f"Records read: {self.smart_reader.records_read}\n"
        report += f"Records skipped: {self.smart_reader.records_skipped}\n"
        
        return report
