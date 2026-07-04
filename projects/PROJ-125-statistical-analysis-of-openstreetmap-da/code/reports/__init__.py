"""
Reports package initialization.
"""
from .eda_report_generator import load_correlation_matrix, load_spatial_stats, check_socioeconomic_proxies, generate_report_content, main

__all__ = [
    'load_correlation_matrix',
    'load_spatial_stats',
    'check_socioeconomic_proxies',
    'generate_report_content',
    'main'
]