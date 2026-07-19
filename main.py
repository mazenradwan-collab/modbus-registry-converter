#!/usr/bin/env python3
"""Main entry point for Modbus Registry Converter"""

import sys
import click
from pathlib import Path

from converters.csv_converter import CSVConverter
from converters.excel_converter import ExcelConverter
from converters.pdf_converter import PDFConverter
from processors.data_processor import DataProcessor
from config import OUTPUT_DIR


class ConverterFactory:
    """Factory for creating appropriate converter based on file type"""
    
    @staticmethod
    def get_converter(file_path):
        """Get the appropriate converter for the file type"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            return CSVConverter()
        elif file_ext in ['.xlsx', '.xls']:
            return ExcelConverter()
        elif file_ext == '.pdf':
            return PDFConverter()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")


@click.command()
@click.option(
    '--input', '-i',
    type=click.Path(exists=True),
    required=True,
    help='Input file path (CSV, Excel, or PDF)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    required=False,
    help='Output file path (default: output_files/converted_registry.csv)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['csv', 'excel']),
    default='csv',
    help='Output format (csv or excel)'
)
@click.option(
    '--validate',
    is_flag=True,
    help='Validate output data after conversion'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
def convert(input, output, format, validate, verbose):
    """Convert Modbus Registry Map files to unified format"""
    
    try:
        input_path = Path(input)
        
        if not input_path.exists():
            click.echo(f"❌ Error: Input file not found: {input}", err=True)
            sys.exit(1)
        
        # Set default output path if not provided
        if not output:
            output = str(OUTPUT_DIR / f"converted_registry.{format}")
        
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            click.echo(f"📂 Input: {input_path}")
            click.echo(f"📂 Output: {output_path}")
            click.echo(f"🔧 Format: {format}")
        
        # Get appropriate converter
        converter = ConverterFactory.get_converter(input_path)
        
        if verbose:
            click.echo(f"🔄 Reading {input_path.suffix} file...")
        
        # Read and convert data
        data = converter.read(input_path)
        
        if verbose:
            click.echo(f"✓ Successfully read {len(data)} registers")
            click.echo(f"🔄 Processing data...")
        
        # Process data
        processor = DataProcessor()
        processed_data = processor.process(data)
        
        if verbose:
            click.echo(f"✓ Successfully processed data")
        
        # Validate if requested
        if validate:
            if verbose:
                click.echo(f"🔍 Validating data...")
            validation_results = processor.validate(processed_data)
            if validation_results['is_valid']:
                if verbose:
                    click.echo(f"✓ Data validation passed")
            else:
                click.echo(f"⚠️  Validation warnings:", err=True)
                for warning in validation_results['warnings']:
                    click.echo(f"  - {warning}", err=True)
        
        # Save output
        if verbose:
            click.echo(f"💾 Saving to {format} format...")
        
        if format == 'csv':
            converter.save_csv(processed_data, output_path)
        elif format == 'excel':
            converter.save_excel(processed_data, output_path)
        
        if verbose:
            click.echo(f"✓ Successfully saved to {output_path}")
        
        click.echo(f"✅ Conversion completed successfully!")
        click.echo(f"📄 Output file: {output_path}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    convert()
