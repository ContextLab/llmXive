"""
Package initializer for the `code.data` module.

This file provides convenient re-exports of the most commonly used
functions from the submodules within `code.data`. It deliberately
avoids importing names that do not exist (e.g., a previously
referenced `preprocess_dataset` function that was never implemented),
thereby preventing ImportError failures during module import.

The public API includes:
  - fetch_dataset: Retrieve the raw GitHub PR dataset.
  - Functions for audit accuracy pipeline.
  - Functions for audit sample generation.
"""

# Re-export dataset fetching utilities
from .fetch import fetch_dataset  # noqa: F401

# Re-export audit accuracy pipeline utilities
from .preprocess import (  # noqa: F401
    load_human_labeled_sample,
    calculate_audit_accuracy,
    write_audit_accuracy_report,
    run_audit_accuracy_pipeline,
    main as preprocess_main,
)

# Re-export audit sample generation utilities
from .generate_audit_sample import (  # noqa: F401
    load_classified_data,
    create_classified_parquet,
    select_audit_sample,
    write_audit_csv,
    main as generate_audit_main,
)

__all__ = [
    "fetch_dataset",
    "load_human_labeled_sample",
    "calculate_audit_accuracy",
    "write_audit_accuracy_report",
    "run_audit_accuracy_pipeline",
    "preprocess_main",
    "load_classified_data",
    "create_classified_parquet",
    "select_audit_sample",
    "write_audit_csv",
    "generate_audit_main",
]
