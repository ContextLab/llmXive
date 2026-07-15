"""
Utilities package for the llmXive research pipeline.

This package contains helper modules for logging, environment configuration,
data setup, and refactoring utilities.
"""
from .logger import (
    ResearchError,
    DataLoadError,
    SimulationError,
    AnalysisError,
    ConfigError,
    StructuredErrorFilter,
    setup_logger,
    get_logger,
    get_traceback_info,
    log_exception,
    log_pipeline_start,
    log_pipeline_end,
    handle_exceptions,
    safe_execute
)

from .env_config import (
    load_environment,
    get_env_variable,
    get_data_root,
    get_simulation_seed,
    get_log_level,
    setup_env_config,
    get_config
)

from .data_setup import (
    compute_file_checksum,
    load_checksums,
    save_checksums,
    update_checksum_for_file,
    verify_file_integrity,
    setup_data_environment
)

from .refactor_utils import (
    get_module_functions,
    validate_module_exports,
    organize_imports,
    extract_constants,
    check_circular_dependencies,
    generate_module_documentation,
    run_refactoring_checks,
    main
)

__all__ = [
    # Logger
    'ResearchError',
    'DataLoadError',
    'SimulationError',
    'AnalysisError',
    'ConfigError',
    'StructuredErrorFilter',
    'setup_logger',
    'get_logger',
    'get_traceback_info',
    'log_exception',
    'log_pipeline_start',
    'log_pipeline_end',
    'handle_exceptions',
    'safe_execute',
    
    # Environment Configuration
    'load_environment',
    'get_env_variable',
    'get_data_root',
    'get_simulation_seed',
    'get_log_level',
    'setup_env_config',
    'get_config',
    
    # Data Setup
    'compute_file_checksum',
    'load_checksums',
    'save_checksums',
    'update_checksum_for_file',
    'verify_file_integrity',
    'setup_data_environment',
    
    # Refactoring Utilities
    'get_module_functions',
    'validate_module_exports',
    'organize_imports',
    'extract_constants',
    'check_circular_dependencies',
    'generate_module_documentation',
    'run_refactoring_checks',
    'main'
]