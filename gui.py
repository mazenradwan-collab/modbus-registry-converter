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
        
        # Set icon if available
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.output_format = tk.StringVar(value="csv")
        self.validate_var = tk.BooleanVar(value=False)
        self.conversion_running = False
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="🔄 محول Modbus Registry",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Input File Section
        self._create_file_section(main_frame, "📥 ملف الإدخال", 1, self.input_file, "ملفات Modbus Registry", 
                                  [("CSV Files", "*.csv"), ("Excel Files", "*.xlsx;*.xls"), ("PDF Files", "*.pdf"), ("All Files", "*.*")])
        
        # Output File Section
        self._create_file_section(main_frame, "📤 ملف الإخراج", 4, self.output_file, "اختر مجلد الحفظ",
                                  is_save=True)
        
        # Output Format Section
        format_frame = ttk.LabelFrame(main_frame, text="🔧 صيغة الإخراج", padding="10")
        format_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        format_frame.columnconfigure(0, weight=1)
        
        ttk.Radiobutton(format_frame, text="CSV", variable=self.output_format, 
                       value="csv").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="Excel", variable=self.output_format, 
                       value="excel").pack(side=tk.LEFT, padx=10)
        
        # Options Section
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ الخيارات", padding="10")
        options_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(0, weight=1)
        
        ttk.Checkbutton(options_frame, text="التحقق من صحة البيانات", 
                       variable=self.validate_var).pack(side=tk.LEFT, padx=10)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 حالة التحويل", padding="10")
        progress_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="جاهز", foreground="green")
        self.status_label.pack(pady=5)
        
        # Buttons Section
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=10, column=0, columnspan=3, pady=20)
        
        ttk.Button(buttons_frame, text="▶️ تحويل", command=self._on_convert).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🔄 إعادة تعيين", command=self._on_reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="❌ إغلاق", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # Info Section
        info_frame = ttk.LabelFrame(main_frame, text="ℹ️ معلومات", padding="10")
        info_frame.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        info_frame.columnconfigure(0, weight=1)
        
        info_text = "يدعم تحويل ملفات CSV و Excel و PDF إلى صيغة موحدة\n"
        info_text += "• اختر ملف الإدخال\n"
        info_text += "• حدد مجلد الحفظ\n"
        info_text += "• اختر صيغة الإخراج\n"
        info_text += "• اضغط تحويل"
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
    
    def _create_file_section(self, parent, title, row, var, dialog_title, file_types=None, is_save=False):
        """Create a file selection section"""
        
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        frame.columnconfigure(1, weight=1)
        
        # File path label
        path_label = ttk.Label(frame, text="المسار:", width=10)
        path_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # Path entry
        path_entry = ttk.Entry(frame, textvariable=var, state='readonly')
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Browse button
        if is_save:
            browse_btn = ttk.Button(
                frame,
                text="📁 استعراض",
                command=lambda: self._select_output_directory(var)
            )
        else:
            browse_btn = ttk.Button(
                frame,
                text="📁 استعراض",
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
            title="اختر مجلد الحفظ",
            initialdir=str(OUTPUT_DIR)
        )
        
        if directory:
            var.set(directory)
    
    def _on_convert(self):
        """Handle conversion button click"""
        
        # Validate inputs
        if not self.input_file.get():
            messagebox.showerror("خطأ", "الرجاء اختيار ملف الإدخال")
            return
        
        if not self.output_file.get():
            messagebox.showerror("خطأ", "الرجاء اختيار مجلد الحفظ")
            return
        
        # Run conversion in separate thread to prevent UI freezing
        thread = threading.Thread(target=self._perform_conversion)
        thread.daemon = True
        thread.start()
    
    def _perform_conversion(self):
        """Perform the actual conversion"""
        
        try:
            self.conversion_running = True
            self.progress_bar.start()
            self.status_label.config(text="جاري التحويل...", foreground="orange")
            self.root.update()
            
            input_path = Path(self.input_file.get())
            output_dir = Path(self.output_file.get())
            output_format = self.output_format.get()
            validate = self.validate_var.get()
            
            # Get appropriate converter
            file_ext = input_path.suffix.lower()
            
            if file_ext == '.csv':
                converter = CSVConverter()
            elif file_ext in ['.xlsx', '.xls']:
                converter = ExcelConverter()
            elif file_ext == '.pdf':
                converter = PDFConverter()
            else:
                raise ValueError(f"صيغة ملف غير مدعومة: {file_ext}")
            
            # Read data
            data = converter.read(input_path)
            
            # Process data
            processor = DataProcessor()
            processed_data = processor.process(data)
            
            # Validate if requested
            validation_results = None
            if validate:
                validation_results = processor.validate(processed_data)
                if not validation_results['is_valid']:
                    errors = "\n".join(validation_results['errors'][:5])
                    raise ValueError(f"خطأ في التحقق من البيانات:\n{errors}")
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"converted_registry_{timestamp}.{output_format}"
            output_path = output_dir / output_name
            
            # Save output
            if output_format == 'csv':
                converter.save_csv(processed_data, output_path)
            elif output_format == 'excel':
                converter.save_excel(processed_data, output_path)
            
            # Show success message
            message = f"✅ تم التحويل بنجاح!\n\n"
            message += f"📊 عدد السجلات: {len(processed_data)}\n"
            message += f"📁 مسار الملف: {output_path}\n"
            
            if validation_results and validation_results['warnings']:
                message += f"\n⚠️ تنبيهات: {len(validation_results['warnings'])}"
            
            self.status_label.config(text="تم بنجاح ✅", foreground="green")
            messagebox.showinfo("نجاح", message)
            
        except Exception as e:
            error_message = f"❌ حدث خطأ:\n{str(e)}"
            self.status_label.config(text="خطأ ❌", foreground="red")
            messagebox.showerror("خطأ", error_message)
        
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
        self.status_label.config(text="جاهز", foreground="green")
        self.progress_bar.stop()


def main():
    """Main entry point"""
    
    root = tk.Tk()
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Create GUI
    app = ModbusConverterGUI(root)
    
    # Run application
    root.mainloop()


if __name__ == '__main__':
    main()
