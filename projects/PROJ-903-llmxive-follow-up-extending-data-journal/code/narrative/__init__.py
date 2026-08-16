"""Narrative generation modules."""
from .baseline import run_baseline_analysis, main as baseline_main
from .flag_propagator import propagate_low_power_flag, write_propagated_report, main as flag_main

__all__ = [
    'run_baseline_analysis',
    'baseline_main',
    'propagate_low_power_flag',
    'write_propagated_report',
    'flag_main'
]