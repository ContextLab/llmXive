"""
Validation Module.

This module handles the validation of agency scores against external scales
and generates validation reports.
"""

from .check_thresholds import main as thresholds_main
from .compute_convergent import compute_convergent_correlation, parse_args, main as convergent_main
from .compute_reliability import compute_split_half_reliability, parse_args, main as reliability_main
from .generate_report import (
    ValidationResult,
    load_validation_subset,
    generate_yaml_summary,
    generate_pdf_report,
    parse_args,
    main as report_main,
)
from .select_subset import (
    find_external_scale_file,
    load_data,
    stratified_sample,
    write_subset,
    parse_args,
    main as subset_main,
)

__all__ = [
    "compute_convergent_correlation",
    "compute_split_half_reliability",
    "ValidationResult",
    "load_validation_subset",
    "generate_yaml_summary",
    "generate_pdf_report",
    "find_external_scale_file",
    "load_data",
    "stratified_sample",
    "write_subset",
    "thresholds_main",
    "convergent_main",
    "reliability_main",
    "report_main",
    "subset_main",
    "parse_args",
]
