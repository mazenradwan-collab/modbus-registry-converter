"""Excel file converter"""

import pandas as pd
from pathlib import Path
from converters.base_converter import BaseConverter


class ExcelConverter(BaseConverter):
    """Converter for Excel files (.xlsx, .xls)"""
    
    def read(self, file_path):
        """Read data from Excel file"""
        try:
            # Try to read with openpyxl engine first (for .xlsx)
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
            except:
                # Fall back to xlrd engine for older .xls files
                df = pd.read_excel(file_path, engine='xlrd')
            
            # Handle multiple sheets - use first sheet with data
            if isinstance(df, dict):
                # Multiple sheets returned
                for sheet_name, sheet_df in df.items():
                    if len(sheet_df) > 0:
                        df = sheet_df
                        break
            
            # Remove empty columns
            df = df.dropna(axis=1, how='all')
            
            self.data = df.to_dict('records')
            return self.data
        
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")
