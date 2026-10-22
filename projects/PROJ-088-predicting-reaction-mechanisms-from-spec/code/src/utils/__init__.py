"""
Utility package initializer.

Exposes key utilities at the package level for convenient imports.
"""

# Re‑export commonly used utilities so callers can do:
#   from src.utils import set_seed, get_default_seed, configure_random_seed
from .seed import (
    set_seed,
    get_default_seed,
    configure_random_seed,
    verify_seed_consistency,
    generate_experiment_id,
    get_environment_seeds,
)

# The logging utilities are also frequently needed; expose them here.
from .logging import (
    get_logger,
    setup_logger,
    log_info,
    log_warning,
    log_error,
    log_critical,
    flag_edge_case,
    get_edge_cases,
    clear_edge_cases,
    log_data_quality_issue,
    get_data_quality_issues,
    clear_data_quality_issues,
    log_provenance_mismatch,
    get_provenance_mismatches,
    clear_provenance_mismatches,
    log_label_validation_issue,
    get_label_validation_issues,
    clear_label_validation_issues,
    generate_edge_case_report,
)

__all__ = [
    # Seed utilities
    "set_seed",
    "get_default_seed",
    "configure_random_seed",
    "verify_seed_consistency",
    "generate_experiment_id",
    "get_environment_seeds",
    # Logging utilities
    "get_logger",
    "setup_logger",
    "log_info",
    "log_warning",
    "log_error",
    "log_critical",
    "flag_edge_case",
    "get_edge_cases",
    "clear_edge_cases",
    "log_data_quality_issue",
    "get_data_quality_issues",
    "clear_data_quality_issues",
    "log_provenance_mismatch",
    "get_provenance_mismatches",
    "clear_provenance_mismatches",
    "log_label_validation_issue",
    "get_label_validation_issues",
    "clear_label_validation_issues",
    "generate_edge_case_report",
]