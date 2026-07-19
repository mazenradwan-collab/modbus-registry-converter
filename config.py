"""Configuration settings for Modbus Registry Converter"""

import os
from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).parent.resolve()

# Input/Output directories
INPUT_DIR = ROOT_DIR / "input_files"
OUTPUT_DIR = ROOT_DIR / "output_files"
TEMPLATE_DIR = ROOT_DIR / "templates"

# Create directories if they don't exist
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMPLATE_DIR.mkdir(exist_ok=True)

# Output template columns
OUTPUT_COLUMNS = [
    'RegisterName',
    'DisplayName',
    'FunctionCode',
    'RegisterType',
    'Address',
    'DataType',
    'RegisterCount',
    'ScaleFactor',
    'Unit',
    'Access',
    'Polling_ms',
    'Enabled'
]

# Modbus Function Code Mapping
FUNCTION_CODE_MAP = {
    'coil': 1,
    'discrete_input': 2,
    'input_register': 3,
    'holding_register': 4,
    'write_single_coil': 5,
    'write_single_register': 6,
    'write_multiple_registers': 16,
    'read_write_multiple_registers': 23
}

# Register Type Mapping
REGISTER_TYPE_MAP = {
    'coil': 'Coil',
    'discrete': 'Discrete Input',
    'input': 'Input Register',
    'holding': 'Holding Register'
}

# Data Type Mapping
DATA_TYPE_MAP = {
    'int16': 'INT16',
    'int32': 'INT32',
    'uint16': 'UINT16',
    'uint32': 'UINT32',
    'float': 'FLOAT32',
    'float32': 'FLOAT32',
    'double': 'FLOAT64',
    'float64': 'FLOAT64',
    'string': 'STRING',
    'bool': 'BOOL'
}

# Access Type Mapping
ACCESS_TYPE_MAP = {
    'read': 'Read',
    'write': 'Write',
    'read_write': 'Read/Write',
    'rw': 'Read/Write'
}

# Default values
DEFAULT_POLLING_MS = 1000
DEFAULT_SCALE_FACTOR = 1.0
DEFAULT_REGISTER_COUNT = 1
DEFAULT_ENABLED = True
