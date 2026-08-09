"""
Analysis module for metrics calculation, statistical testing, and validation.
"""

from .metrics import (
    calculate_aucc,
    calculate_final_accuracy,
    calculate_average_prompt_length,
    calculate_metrics_from_log,
    save_metrics_to_csv,
    ensure_directory,
    calculate_baseline_metrics,
    calculate_cap_metrics
)

from .stats import (
    calculate_paired_ttest,
    calculate_effect_size,
    bootstrap_confidence_interval,
    check_catastrophic_forgetting
)

from .report import (
    load_metrics_from_csv,
    calculate_summary_statistics,
    generate_comparative_report,
    main as report_main
)

from .validate_metrics import (
    load_schema,
    load_metrics_data,
    validate_metrics_against_schema,
    validate_aggregated_metrics_file,
    main as validate_main
)

__all__ = [
    # Metrics
    "calculate_aucc",
    "calculate_final_accuracy",
    "calculate_average_prompt_length",
    "calculate_metrics_from_log",
    "save_metrics_to_csv",
    "ensure_directory",
    "calculate_baseline_metrics",
    "calculate_cap_metrics",

    # Stats
    "calculate_paired_ttest",
    "calculate_effect_size",
    "bootstrap_confidence_interval",
    "check_catastrophic_forgetting",

    # Report
    "load_metrics_from_csv",
    "calculate_summary_statistics",
    "generate_comparative_report",
    "report_main",

    # Validation
    "load_schema",
    "load_metrics_data",
    "validate_metrics_against_schema",
    "validate_aggregated_metrics_file",
    "validate_main"
]
