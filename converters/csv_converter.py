"""CSV file converter"""

import pandas as pd
from pathlib import Path
from converters.base_converter import BaseConverter


class CSVConverter(BaseConverter):
    """Converter for CSV files"""
    
    def read(self, file_path):
        """Read data from CSV file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    self.data = df.to_dict('records')
                    return self.data
                except UnicodeDecodeError:
                    continue
            
            raise ValueError(f"Could not read CSV file with any supported encoding")
        
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")
