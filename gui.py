#!/usr/bin/env python3
"""GUI for Modbus Registry Converter using tkinter"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
from datetime import datetime

from converters.csv_converter import CSVConverter
from converters.excel_converter import ExcelConverter
from converters.pdf_converter import PDFConverter
from processors.data_processor import DataProcessor
from config import OUTPUT_DIR


class ModbusConverterGUI:
    """GUI Application for Modbus Registry Converter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Modbus Registry Converter")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.output_format = tk.StringVar(value="csv")
        self.validate_var = tk.BooleanVar(value=False)
        self.conversion_running = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface"""
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(
            main_frame,
            text="Modbus Registry Converter",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        self._create_file_section(main_frame, "Input File", 1, self.input_file, "Select Input File", 
                                  [("CSV Files", "*.csv"), ("Excel Files", "*.xlsx;*.xls"), ("PDF Files", "*.pdf"), ("All Files", "*.*")])
        
        self._create_file_section(main_frame, "Output Directory", 4, self.output_file, "Select Output Directory",
                                  is_save=True)
        
        format_frame = ttk.LabelFrame(main_frame, text="Output Format", padding="10")
        format_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        format_frame.columnconfigure(0, weight=1)
        
        ttk.Radiobutton(format_frame, text="CSV", variable=self.output_format, 
                       value="csv").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="Excel", variable=self.output_format, 
                       value="excel").pack(side=tk.LEFT, padx=10)
        
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(0, weight=1)
        
        ttk.Checkbutton(options_frame, text="Validate Data", 
                       variable=self.validate_var).pack(side=tk.LEFT, padx=10)
        
        progress_frame = ttk.LabelFrame(main_frame, text="Conversion Status", padding="10")
        progress_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready", foreground="green")
        self.status_label.pack(pady=5)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=10, column=0, columnspan=3, pady=20)
        
        ttk.Button(buttons_frame, text="Convert", command=self._on_convert).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Reset", command=self._on_reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="10")
        info_frame.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        info_frame.columnconfigure(0, weight=1)
        
        info_text = "Convert CSV, Excel, and PDF files to unified format\n"
        info_text += "- Select input file\n"
        info_text += "- Choose output directory\n"
        info_text += "- Select output format\n"
        info_text += "- Click Convert"
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
    
    def _create_file_section(self, parent, title, row, var, dialog_title, file_types=None, is_save=False):
        """Create a file selection section"""
        
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        frame.columnconfigure(1, weight=1)
        
        path_label = ttk.Label(frame, text="Path:", width=10)
        path_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        path_entry = ttk.Entry(frame, textvariable=var, state='readonly')
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        if is_save:
            browse_btn = ttk.Button(
                frame,
                text="Browse",
                command=lambda: self._select_output_directory(var)
            )
        else:
            browse_btn = ttk.Button(
                frame,
                text="Browse",
                command=lambda: self._select_input_file(var, dialog_title, file_types)
            )
        browse_btn.grid(row=0, column=2, padx=5)
    
    def _select_input_file(self, var, dialog_title, file_types):
        """Open file dialog to select input file"""
        
        file_path = filedialog.askopenfilename(
            title=dialog_title,
            filetypes=file_types if file_types else [("All Files", "*.*")],
            initialdir=str(Path.home())
        )
        
        if file_path:
            var.set(file_path)
    
    def _select_output_directory(self, var):
        """Open directory dialog to select output location"""
        
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=str(OUTPUT_DIR)
        )
        
        if directory:
            var.set(directory)
    
    def _on_convert(self):
        """Handle conversion button click"""
        
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not self.output_file.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        thread = threading.Thread(target=self._perform_conversion)
        thread.daemon = True
        thread.start()
    
    def _perform_conversion(self):
        """Perform the actual conversion"""
        
        try:
            self.conversion_running = True
            self.progress_bar.start()
            self.status_label.config(text="Converting...", foreground="orange")
            self.root.update()
            
            input_path = Path(self.input_file.get())
            output_dir = Path(self.output_file.get())
            output_format = self.output_format.get()
            validate = self.validate_var.get()
            
            file_ext = input_path.suffix.lower()
            
            if file_ext == '.csv':
                converter = CSVConverter()
            elif file_ext in ['.xlsx', '.xls']:
                converter = ExcelConverter()
            elif file_ext == '.pdf':
                converter = PDFConverter()
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            data = converter.read(input_path)
            
            processor = DataProcessor()
            processed_data = processor.process(data)
            
            validation_results = None
            if validate:
                validation_results = processor.validate(processed_data)
                if not validation_results['is_valid']:
                    errors = "\n".join(validation_results['errors'][:5])
                    raise ValueError(f"Data validation failed:\n{errors}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"converted_registry_{timestamp}.{output_format}"
            output_path = output_dir / output_name
            
            if output_format == 'csv':
                converter.save_csv(processed_data, output_path)
            elif output_format == 'excel':
                converter.save_excel(processed_data, output_path)
            
            message = f"Conversion completed successfully!\n\n"
            message += f"Records: {len(processed_data)}\n"
            message += f"Output: {output_path}\n"
            
            if validation_results and validation_results['warnings']:
                message += f"\nWarnings: {len(validation_results['warnings'])}"
            
            self.status_label.config(text="Success", foreground="green")
            messagebox.showinfo("Success", message)
            
        except Exception as e:
            error_message = f"Error occurred:\n{str(e)}"
            self.status_label.config(text="Error", foreground="red")
            messagebox.showerror("Error", error_message)
        
        finally:
            self.progress_bar.stop()
            self.conversion_running = False
            self.root.update()
    
    def _on_reset(self):
        """Reset all fields"""
        
        self.input_file.set("")
        self.output_file.set(str(OUTPUT_DIR))
        self.output_format.set("csv")
        self.validate_var.set(False)
        self.status_label.config(text="Ready", foreground="green")
        self.progress_bar.stop()


def main():
    """Main entry point"""
    
    root = tk.Tk()
    
    style = ttk.Style()
    style.theme_use('clam')
    
    app = ModbusConverterGUI(root)
    
    root.mainloop()


if __name__ == '__main__':
    main()
