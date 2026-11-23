"""
llmXive Research Pipeline - Main Code Package

This package contains all core implementation modules for the
brain network reconfiguration and mTBI recovery study.
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
    get_warning_runtime_hours
)
from .memory_monitor import (
    get_current_ram_gb,
    is_limit_exceeded,
    check_and_warn,
    enforce_limit
)
from .logging_config import (
    get_logger,
    initialize_logging,
    set_log_level,
    log_memory_warning
)
from .entities import (
    Subject,
    ConnectivityMatrix,
    GraphMetrics
)
from .synthetic_data import (
    generate_connectivity_matrix,
    generate_graph_metrics,
    generate_cognitive_score,
    generate_subject_data,
    generate_dataset,
    run_generator,
    main as synthetic_main
)
from .data_ingestion import (
    check_memory_and_log,
    get_dataset_metadata,
    download_dataset_files,
    parse_subject_info,
    generate_manifest,
    main as ingestion_main
)
from .preprocessing import (
    download_atlas_if_needed,
    load_confounds_from_bids,
    preprocess_fmri,
    compute_connectivity_matrix,
    save_connectivity_matrix,
    check_time_point_completeness,
    process_subject,
    run_preprocessing_pipeline,
    main as preprocessing_main
)
from .graph_metrics import (
    calculate_global_efficiency,
    calculate_local_efficiency,
    calculate_modularity,
    apply_spatial_threshold,
    compute_metrics_from_matrix,
    process_connectivity_matrices,
    main as graph_metrics_main
)
from .statistical_model import (
    load_preprocessed_data,
    check_multicollinearity,
    fit_linear_mixed_effects_model,
    run_statistical_analysis,
    main as statistical_main
)
from .collinearity import (
    calculate_vif,
    run_pca_on_metrics,
    generate_descriptive_vif_report,
    check_and_handle_collinearity,
    main as collinearity_main
)
from .robustness import (
    load_statistical_results,
    calculate_observed_correlation,
    perform_permutation_test,
    run_robustness_analysis,
    save_results,
    main as robustness_main
)
from .sensitivity_analysis import (
    load_data_for_sensitivity,
    generate_synthetic_sensitivity_data,
    calculate_correlation_metric,
    run_sensitivity_sweep,
    save_results,
    main as sensitivity_main
)
from .analysis_report import (
    load_json_safely,
    parse_log_for_memory,
    parse_log_for_runtime,
    aggregate_metrics,
    generate_report,
    main as report_main
)
from .validation import (
    load_manifest,
    find_target_column,
    calculate_correlation_with_metric,
    run_validation_pipeline,
    main as validation_main
)
from .validation_search import (
    query_openneuro_dataset_metadata,
    scan_participants_file_for_targets,
    search_multiple_datasets,
    generate_search_report,
    main as validation_search_main
)
from .time_monitor import (
    initialize_runtime_monitor,
    check_runtime_status,
    get_elapsed_time_hours,
    ensure_runtime_limit,
    main as time_monitor_main
)
from .cleanup import (
    optimize_dataframe_dtypes,
    load_csv_memory_efficient,
    clean_large_objects,
    downcast_numpy_array,
    ensure_memory_fits,
    run_cleanup_pipeline,
    main as cleanup_main
)

__version__ = "1.0.0"
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
    # Memory
    "get_current_ram_gb",
    "is_limit_exceeded",
    "check_and_warn",
    "enforce_limit",
    # Logging
    "get_logger",
    "initialize_logging",
    "set_log_level",
    "log_memory_warning",
    # Entities
    "Subject",
    "ConnectivityMatrix",
    "GraphMetrics",
    # Synthetic Data
    "generate_connectivity_matrix",
    "generate_graph_metrics",
    "generate_cognitive_score",
    "generate_subject_data",
    "generate_dataset",
    "run_generator",
    "synthetic_main",
    # Data Ingestion
    "check_memory_and_log",
    "get_dataset_metadata",
    "download_dataset_files",
    "parse_subject_info",
    "generate_manifest",
    "ingestion_main",
    # Preprocessing
    "download_atlas_if_needed",
    "load_confounds_from_bids",
    "preprocess_fmri",
    "compute_connectivity_matrix",
    "save_connectivity_matrix",
    "check_time_point_completeness",
    "process_subject",
    "run_preprocessing_pipeline",
    "preprocessing_main",
    # Graph Metrics
    "calculate_global_efficiency",
    "calculate_local_efficiency",
    "calculate_modularity",
    "apply_spatial_threshold",
    "compute_metrics_from_matrix",
    "process_connectivity_matrices",
    "graph_metrics_main",
    # Statistical Model
    "load_preprocessed_data",
    "check_multicollinearity",
    "fit_linear_mixed_effects_model",
    "run_statistical_analysis",
    "statistical_main",
    # Collinearity
    "calculate_vif",
    "run_pca_on_metrics",
    "generate_descriptive_vif_report",
    "check_and_handle_collinearity",
    "collinearity_main",
    # Robustness
    "load_statistical_results",
    "calculate_observed_correlation",
    "perform_permutation_test",
    "run_robustness_analysis",
    "save_results",
    "robustness_main",
    # Sensitivity
    "load_data_for_sensitivity",
    "generate_synthetic_sensitivity_data",
    "calculate_correlation_metric",
    "run_sensitivity_sweep",
    "sensitivity_main",
    # Analysis Report
    "load_json_safely",
    "parse_log_for_memory",
    "parse_log_for_runtime",
    "aggregate_metrics",
    "generate_report",
    "report_main",
    # Validation
    "load_manifest",
    "find_target_column",
    "calculate_correlation_with_metric",
    "run_validation_pipeline",
    "validation_main",
    # Validation Search
    "query_openneuro_dataset_metadata",
    "scan_participants_file_for_targets",
    "search_multiple_datasets",
    "generate_search_report",
    "validation_search_main",
    # Time Monitor
    "initialize_runtime_monitor",
    "check_runtime_status",
    "get_elapsed_time_hours",
    "ensure_runtime_limit",
    "time_monitor_main",
    # Cleanup (T033)
    "optimize_dataframe_dtypes",
    "load_csv_memory_efficient",
    "clean_large_objects",
    "downcast_numpy_array",
    "ensure_memory_fits",
    "run_cleanup_pipeline",
    "cleanup_main",
]
