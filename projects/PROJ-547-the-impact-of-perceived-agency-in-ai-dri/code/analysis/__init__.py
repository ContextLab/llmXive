"""
Analysis Module.

This module contains the regression analysis pipeline, including data merging,
model selection, regression execution, and result generation.
"""

from .check_agency_variance import check_variance, main as variance_main
from .compute_posthoc_power import compute_posthoc_power, main as power_main
from .generate_results import main as results_main
from .merge_datasets import merge_datasets, main as merge_main
from .run_regression import run_regression, MemoryProfiler, main as regression_main
from .select_regression import select_regression, main as select_main

__all__ = [
    "check_variance",
    "compute_posthoc_power",
    "generate_results",
    "merge_datasets",
    "run_regression",
    "select_regression",
    "MemoryProfiler",
    "variance_main",
    "power_main",
    "results_main",
    "merge_main",
    "regression_main",
    "select_main",
]
