"""Advanced CSV file converter - DIRECT POSITION-BASED READING"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from converters.base_converter import BaseConverter


class SmartCSVReader:
    """Reads CSV files by analyzing structure directly"""
    
    def __init__(self):
        self.detected_separator = None
        self.records_read = 0
    
    def read_csv_smart(self, file_path: Path, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """Read CSV intelligently - skip format issues"""
        
        file_path = Path(file_path)
        
        # Read raw file to inspect structure
        print(f"[CSV Reader] Reading file: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
                print(f"[CSV Reader] Total lines: {len(lines)}")
                
                # Print first 3 lines for inspection
                print(f"[CSV Reader] First 3 lines:")
                for i, line in enumerate(lines[:3]):
                    print(f"  Line {i}: {line[:100]}...")
        except Exception as e:
            print(f"[CSV Reader] Error reading raw file: {e}")
        
        # Try reading with TAB separator first
        try:
            print(f"\n[CSV Reader] Attempting to read with TAB separator...")
            df = pd.read_csv(
                file_path,
                sep='\t',
                encoding=encoding,
                dtype=str,
                header=None,  # No header - we'll handle it manually
                skip_blank_lines=True
            )
            
            print(f"[CSV Reader] Success! Read {len(df)} rows x {len(df.columns)} columns")
            
            # Find header row (first row with meaningful data)
            header_row = 0
            header_names = list(df.iloc[header_row])
            print(f"[CSV Reader] Header row: {header_names}")
            
            # Skip header and convert to list of dicts using column positions
            data_rows = df.iloc[1:].reset_index(drop=True)
            
            records = []
            for idx, row in data_rows.iterrows():
                record = {}
                for col_idx, col_name in enumerate(header_names):
                    value = row.iloc[col_idx] if col_idx < len(row) else ''
                    if value and str(value).strip() and str(value).lower() != 'nan':
                        record[col_name] = str(value).strip()
                
                if record:  # Only keep non-empty records
                    records.append(record)
            
            self.records_read = len(records)
            print(f"[CSV Reader] Total records with data: {self.records_read}\n")
            
            return records
            
        except Exception as e:
            print(f"[CSV Reader] TAB separator failed: {e}")
        
        # Fallback: Try comma separator
        try:
            print(f"[CSV Reader] Fallback: Attempting COMMA separator...")
            df = pd.read_csv(
                file_path,
                sep=',',
                encoding=encoding,
                dtype=str,
                header=None,
                skip_blank_lines=True
            )
            
            header_row = 0
            header_names = list(df.iloc[header_row])
            data_rows = df.iloc[1:].reset_index(drop=True)
            
            records = []
            for idx, row in data_rows.iterrows():
                record = {}
                for col_idx, col_name in enumerate(header_names):
                    value = row.iloc[col_idx] if col_idx < len(row) else ''
                    if value and str(value).strip() and str(value).lower() != 'nan':
                        record[col_name] = str(value).strip()
                
                if record:
                    records.append(record)
            
            self.records_read = len(records)
            print(f"[CSV Reader] COMMA Success! Total records: {self.records_read}\n")
            return records
            
        except Exception as e:
            print(f"[CSV Reader] COMMA separator failed: {e}")
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
        
        for encoding in encodings:
            try:
                print(f"[CSV Converter] Trying encoding: {encoding}\n")
                self.data = self.smart_reader.read_csv_smart(file_path, encoding=encoding)
                print(f"[CSV Converter] Successfully read with encoding: {encoding}")
                print(f"[CSV Converter] Total records: {len(self.data)}\n")
                return self.data
            except Exception as e:
                print(f"[CSV Converter] Failed with {encoding}: {e}\n")
                continue
        
        raise ValueError("Could not read CSV file with any encoding")
    
    def save_csv(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Save data to CSV file"""
        
        if not data:
            raise ValueError("No data to save")
        
        output_path = Path(output_path)
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"[CSV Converter] Saved {len(data)} records to {output_path}")
