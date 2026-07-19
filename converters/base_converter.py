"""Base converter class"""

from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
from config import OUTPUT_DIR


class BaseConverter(ABC):
    """Abstract base class for all converters"""
    
    def __init__(self):
        self.data = None
    
    @abstractmethod
    def read(self, file_path):
        """Read data from file"""
        pass
    
    def save_csv(self, data, output_path):
        """Save data as CSV"""
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    def save_excel(self, data, output_path):
        """Save data as Excel file with formatting"""
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Registry')
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Registry']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Format header row
            from openpyxl.styles import Font, PatternFill, Alignment
            header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            header_font = Font(color='FFFFFF', bold=True)
            header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
