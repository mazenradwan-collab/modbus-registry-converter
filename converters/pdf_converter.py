"""PDF file converter"""

import pandas as pd
import pdfplumber
from pathlib import Path
from converters.base_converter import BaseConverter


class PDFConverter(BaseConverter):
    """Converter for PDF files containing tables"""
    
    def read(self, file_path):
        """Read data from PDF file"""
        try:
            all_data = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract tables from the page
                    tables = page.extract_tables()
                    
                    if tables:
                        for table in tables:
                            # Convert table to DataFrame
                            if table:
                                # First row is typically headers
                                if len(table) > 1:
                                    df = pd.DataFrame(table[1:], columns=table[0])
                                    all_data.append(df)
            
            if not all_data:
                raise ValueError("No tables found in PDF")
            
            # Combine all data from all pages
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Remove empty columns
            combined_df = combined_df.dropna(axis=1, how='all')
            
            self.data = combined_df.to_dict('records')
            return self.data
        
        except Exception as e:
            raise Exception(f"Error reading PDF file: {str(e)}")
