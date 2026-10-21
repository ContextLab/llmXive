"""
Wrapper module that re‑exports the actual QC implementation located in
``code/qc.py``.  All public symbols (functions and the ``main`` entry point)
are imported so that test modules can use ``from src.qc import …`` while the
implementation lives in the dedicated ``code`` directory.
"""
from code.qc import (
    calculate_framewise_displacement,
    calculate_subject_motion_metrics,
    calculate_subject_motion_metrics_with_conditions,
    check_subject_count,
    filter_by_motion_threshold,
    load_motion_parameters,
    main,
    verify_conditions,
)

__all__ = [
    "calculate_framewise_displacement",
    "calculate_subject_motion_metrics",
    "calculate_subject_motion_metrics_with_conditions",
    "check_subject_count",
    "filter_by_motion_threshold",
    "load_motion_parameters",
    "verify_conditions",
    "main",
]
