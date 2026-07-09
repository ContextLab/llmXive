"""
llmXive Research Pipeline - Code Package

This package contains the core implementation modules for the
investigation into the relationship between brain network reconfiguration
and recovery from mild traumatic brain injury.
"""

from .config import (
    get_config,
    is_synthetic,
    is_methodology_validation_mode,
    set_synthetic_mode,
    check_data_availability,
    initialize_methodology_validation_mode,
    get_memory_limit_gb,
    get_runtime_limit_hours,
    get_warning_runtime_hours,
    PROJECT_ROOT,
    CODE_DIR,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_RESULTS_DIR,
    SPECS_DIR,
)

from .logging_config import get_logger, initialize_logging, set_log_level

from .memory_monitor import (
    get_current_ram_gb,
    is_limit_exceeded,
    check_and_warn,
    enforce_limit,
)

from .entities import Subject, ConnectivityMatrix, GraphMetrics

__all__ = [
    # Config
    "get_config",
    "is_synthetic",
    "is_methodology_validation_mode",
    "set_synthetic_mode",
    "check_data_availability",
    "initialize_methodology_validation_mode",
    "get_memory_limit_gb",
    "get_runtime_limit_hours",
    "get_warning_runtime_hours",
    "PROJECT_ROOT",
    "CODE_DIR",
    "DATA_RAW_DIR",
    "DATA_PROCESSED_DIR",
    "DATA_RESULTS_DIR",
    "SPECS_DIR",
    # Logging
    "get_logger",
    "initialize_logging",
    "set_log_level",
    # Memory
    "get_current_ram_gb",
    "is_limit_exceeded",
    "check_and_warn",
    "enforce_limit",
    # Entities
    "Subject",
    "ConnectivityMatrix",
    "GraphMetrics",
]
