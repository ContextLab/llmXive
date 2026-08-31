"""
Eval module initialization.
Exposes the report verifier for T036.
"""
from .report_verifier import verify_report, verify_report_structure, verify_sensitivity_table_structure, verify_numeric_values, verify_report_file_exists, REQUIRED_KEYS

__all__ = [
    'verify_report',
    'verify_report_structure',
    'verify_sensitivity_table_structure',
    'verify_numeric_values',
    'verify_report_file_exists',
    'REQUIRED_KEYS'
]