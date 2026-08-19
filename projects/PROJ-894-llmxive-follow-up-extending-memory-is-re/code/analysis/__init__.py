"""
Analysis module for llmXive.
"""
from .correlation_analysis import main as correlation_main
from .stats import main as stats_main
from .threshold_analysis import main as threshold_main
from .sensitivity_analysis import main as sensitivity_main
from .noisy_stats import main as noisy_stats_main

__all__ = [
    'correlation_main',
    'stats_main',
    'threshold_main',
    'sensitivity_main',
    'noisy_stats_main'
]