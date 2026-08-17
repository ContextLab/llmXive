"""
Utils package for llmXive project.

This package contains utility modules for configuration, metrics,
statistics, and other helper functions.
"""
from .config import Config, get_config, get_path, get_hyperparameter, get_seed
from .metrics import ImageDataset, calculate_clip_score, calculate_fid
from .statistics import (
    TimeoutError,
    timeout_handler,
    calculate_effect_size,
    bootstrap_power_analysis,
    run_bootstrap_test,
    run_ttest,
    save_partial_results,
    save_statistical_tests,
)
from .check_weights import (
    calculate_sha256,
    get_file_size,
    load_manifest,
    verify_file,
    verify_ground_truth,
    initialize_manifest,
)
from .memory_profiler import get_memory_usage_mb, profile_function, save_memory_profile
from .batch_processor import BatchResult, run_parallel_batch_processing, estimate_runtime
from .vulture_runner import main as vulture_main
from .cleanup_unused_imports import (
    ImportUsageVisitor,
    get_imports_and_usage,
    remove_unused_imports,
    scan_code_directory,
)
from .import_check import check_module_imports, run_import_check

__all__ = [
    # config
    "Config",
    "get_config",
    "get_path",
    "get_hyperparameter",
    "get_seed",
    # metrics
    "ImageDataset",
    "calculate_clip_score",
    "calculate_fid",
    # statistics
    "TimeoutError",
    "timeout_handler",
    "calculate_effect_size",
    "bootstrap_power_analysis",
    "run_bootstrap_test",
    "run_ttest",
    "save_partial_results",
    "save_statistical_tests",
    # check_weights
    "calculate_sha256",
    "get_file_size",
    "load_manifest",
    "verify_file",
    "verify_ground_truth",
    "initialize_manifest",
    # memory_profiler
    "get_memory_usage_mb",
    "profile_function",
    "save_memory_profile",
    # batch_processor
    "BatchResult",
    "run_parallel_batch_processing",
    "estimate_runtime",
    # vulture_runner
    "vulture_main",
    # cleanup_unused_imports
    "ImportUsageVisitor",
    "get_imports_and_usage",
    "remove_unused_imports",
    "scan_code_directory",
    # import_check
    "check_module_imports",
    "run_import_check",
]
