#!/usr/bin/env python3
"""GUI for Modbus Registry Converter using tkinter with advanced filtering"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
from datetime import datetime

from converters.csv_converter import CSVConverter
from converters.excel_converter import ExcelConverter
from converters.pdf_converter import PDFConverter
from processors.data_processor import DataProcessor
from processors.registry_filter import RegistryFilter, get_filter_presets
from config import OUTPUT_DIR


class ModbusConverterGUI:
    """GUI Application for Modbus Registry Converter with Filter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Modbus Registry Converter - Advanced Filter")
        self.root.geometry("1000x900")
        self.root.resizable(True, True)
        
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.output_format = tk.StringVar(value="csv")
        self.validate_var = tk.BooleanVar(value=False)
        self.use_filter = tk.BooleanVar(value=False)
        self.filter_mode = tk.StringVar(value="include")
        self.conversion_running = False
        
        self.registry_filter = RegistryFilter()
        self.selected_filter_categories = set()
        self.excluded_keywords = set()
        self.included_keywords = set()
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface"""
        
        # Create main canvas with scrollbar
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Title
        title_label = ttk.Label(
            scrollable_frame,
            text="Modbus Registry Converter - Advanced Filter",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # File Selection Sections
        self._create_file_section(scrollable_frame, "Input File", self.input_file, "Select Input File", 
                                  [("CSV Files", "*.csv"), ("Excel Files", "*.xlsx;*.xls"), ("PDF Files", "*.pdf"), ("All Files", "*.*")])
        
        self._create_file_section(scrollable_frame, "Output Directory", self.output_file, "Select Output Directory",
                                  is_save=True)
        
        # Output Format Section
        format_frame = ttk.LabelFrame(scrollable_frame, text="Output Format", padding="10")
        format_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Radiobutton(format_frame, text="CSV", variable=self.output_format, 
                       value="csv").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="Excel", variable=self.output_format, 
                       value="excel").pack(side=tk.LEFT, padx=10)
        
        # Filter Section
        self._create_filter_section(scrollable_frame)
        
        # Options Section
        options_frame = ttk.LabelFrame(scrollable_frame, text="Options", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Checkbutton(options_frame, text="Validate Data", 
                       variable=self.validate_var).pack(side=tk.LEFT, padx=10)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(scrollable_frame, text="Conversion Status", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready", foreground="green")
        self.status_label.pack(pady=5)
        
        # Buttons Section
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(pady=20)
        
        convert_btn = ttk.Button(buttons_frame, text="Convert", command=self._on_convert, width=15)
        convert_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = ttk.Button(buttons_frame, text="Reset", command=self._on_reset, width=15)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = ttk.Button(buttons_frame, text="Exit", command=self.root.quit, width=15)
        exit_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_file_section(self, parent, title, var, dialog_title, file_types=None, is_save=False):
        """Create a file selection section"""
        
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)
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
    
    def _create_filter_section(self, parent):
        """Create filter configuration section"""
        
        filter_frame = ttk.LabelFrame(parent, text="Advanced Filter (Optional)", padding="10")
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        filter_frame.columnconfigure(0, weight=1)
        
        # Enable filter checkbox
        ttk.Checkbutton(filter_frame, text="Enable Filtering", 
                       variable=self.use_filter, command=self._on_filter_toggle).pack(anchor=tk.W, pady=5)
        
        # Filter mode selection
        mode_frame = ttk.Frame(filter_frame)
        mode_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Include", variable=self.filter_mode, 
                       value="include").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Exclude", variable=self.filter_mode, 
                       value="exclude").pack(side=tk.LEFT, padx=5)
        
        # Categories section
        cat_label = ttk.Label(filter_frame, text="Register Categories:")
        cat_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.category_vars = {}
        categories = self.registry_filter.get_available_categories()
        
        # Create category checkboxes in a grid for better layout
        cat_grid_frame = ttk.Frame(filter_frame)
        cat_grid_frame.pack(fill=tk.X, padx=10, pady=5)
        
        col = 0
        for idx, (category, info) in enumerate(categories.items()):
            var = tk.BooleanVar()
            self.category_vars[category] = var
            
            ttk.Checkbutton(
                cat_grid_frame,
                text=f"{category.capitalize()}",
                variable=var,
                command=self._update_selected_categories
            ).grid(row=idx//2, column=idx%2, sticky=tk.W, padx=10, pady=2)
        
        # Presets section
        preset_frame = ttk.LabelFrame(filter_frame, text="Filter Presets", padding="10")
        preset_frame.pack(fill=tk.X, pady=10)
        
        presets = get_filter_presets()
        
        preset_buttons_frame = ttk.Frame(preset_frame)
        preset_buttons_frame.pack(fill=tk.X)
        
        for idx, (preset_name, preset_config) in enumerate(presets.items()):
            ttk.Button(
                preset_buttons_frame,
                text=f"{preset_name.replace('_', ' ').title()}",
                command=lambda name=preset_name, config=preset_config: self._apply_preset(name, config),
                width=20
            ).grid(row=idx//3, column=idx%3, padx=5, pady=5)
        
        # Keywords section
        keywords_frame = ttk.LabelFrame(filter_frame, text="Custom Keywords", padding="10")
        keywords_frame.pack(fill=tk.X, pady=10)
        keywords_frame.columnconfigure(1, weight=1)
        
        ttk.Label(keywords_frame, text="Include (comma-separated):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.include_keywords_entry = ttk.Entry(keywords_frame)
        self.include_keywords_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(keywords_frame, text="Exclude (comma-separated):").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.exclude_keywords_entry = ttk.Entry(keywords_frame)
        self.exclude_keywords_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Disable initially
        self._on_filter_toggle()
    
    def _on_filter_toggle(self):
        """Enable/disable filter controls"""
        state = tk.NORMAL if self.use_filter.get() else tk.DISABLED
        
        self.include_keywords_entry.config(state=state)
        self.exclude_keywords_entry.config(state=state)
    
    def _update_selected_categories(self):
        """Update selected filter categories"""
        self.selected_filter_categories = {
            cat for cat, var in self.category_vars.items() if var.get()
        }
    
    def _apply_preset(self, preset_name, preset_config):
        """Apply a filter preset"""
        
        # Reset all categories
        for var in self.category_vars.values():
            var.set(False)
        
        # Apply categories from preset
        for category in preset_config.get('categories', []):
            if category in self.category_vars:
                self.category_vars[category].set(True)
        
        # Apply excluded keywords
        excluded = preset_config.get('excluded_keywords', [])
        self.exclude_keywords_entry.delete(0, tk.END)
        if excluded:
            self.exclude_keywords_entry.insert(0, ', '.join(excluded))
        
        # Apply included keywords
        included = preset_config.get('included_keywords', [])
        self.include_keywords_entry.delete(0, tk.END)
        if included:
            self.include_keywords_entry.insert(0, ', '.join(included))
        
        self._update_selected_categories()
        messagebox.showinfo("Preset Applied", f"Preset '{preset_name}' applied successfully!")
    
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
        """Perform the actual conversion with optional filtering"""
        
        try:
            self.conversion_running = True
            self.progress_bar.start()
            self.status_label.config(text="Converting...", foreground="orange")
            self.root.update()
            
            input_path = Path(self.input_file.get())
            output_dir = Path(self.output_file.get())
            output_format = self.output_format.get()
            validate = self.validate_var.get()
            use_filter = self.use_filter.get()
            
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
            
            # Apply filter if enabled
            filter_report = None
            if use_filter and self.selected_filter_categories:
                registry_filter = RegistryFilter()
                
                registry_filter.select_categories(list(self.selected_filter_categories))
                
                # Parse keywords
                include_keywords_str = self.include_keywords_entry.get()
                if include_keywords_str.strip():
                    keywords = [kw.strip() for kw in include_keywords_str.split(',')]
                    registry_filter.add_included_keywords(keywords)
                
                exclude_keywords_str = self.exclude_keywords_entry.get()
                if exclude_keywords_str.strip():
                    keywords = [kw.strip() for kw in exclude_keywords_str.split(',')]
                    registry_filter.add_excluded_keywords(keywords)
                
                processed_data, filter_report = registry_filter.filter_records(
                    processed_data,
                    category_mode=self.filter_mode.get()
                )
            
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
            message += f"Records processed: {len(processed_data)}\n"
            message += f"Output: {output_path}\n"
            
            if filter_report:
                message += f"\nFilter Report:\n"
                message += f"Total input records: {filter_report['total_records']}\n"
                message += f"Filtered records: {filter_report['filtered_records']}\n"
                message += f"Excluded records: {filter_report['excluded_records']}\n"
            
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
        self.use_filter.set(False)
        self.filter_mode.set("include")
        
        for var in self.category_vars.values():
            var.set(False)
        
        self.include_keywords_entry.delete(0, tk.END)
        self.exclude_keywords_entry.delete(0, tk.END)
        
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
