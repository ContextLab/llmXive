# llmXive Project: PROJ-340-investigating-the-correlation-between-gu
# Core package initialization
# This package contains the analysis pipeline for gut microbiome and sleep architecture correlation.

from .ingest import (
    RealDataFetchError,
    setup_paths,
    load_schema,
    load_required_variables,
    validate_variables,
    fetch_real_data,
    load_data,
    detect_outliers_iqr,
    save_outlier_report,
    filter_outliers,
    save_filtered_data,
    calculate_checksum,
    record_checksum,
    main as ingest_main
)
from .analysis import (
    set_analysis_seed,
    check_distribution,
    select_correlation_method,
    run_correlation_analysis,
    benjamini_hochberg_fdr,
    main as analysis_main
)
from .transform import (
    apply_compositional_correction,
    main as transform_main
)
from .diagnostics import (
    set_diagnostics_seed,
    detect_perfect_multicollinearity,
    calculate_vif,
    run_sensitivity_analysis,
    calculate_power,
    main as diagnostics_main
)
from .report import (
    load_json_file,
    generate_report,
    main as report_main
)
from .synthetic_data import (
    set_seeds,
    load_required_variables as load_req_vars_synthetic,
    generate_metagenomic_counts,
    generate_sleep_metrics,
    generate_synthetic_dataset,
    generate_synthetic_manifest,
    main as synthetic_main
)
from .reference_validator import (
    VerificationStatus,
    CitationSchema,
    VerificationResult,
    ReferenceValidator,
    create_sample_schema,
    main as validator_main
)
from .main import (
    setup_paths as main_setup_paths,
    estimate_ram_usage,
    determine_compute_strategy,
    save_compute_strategy,
    check_validation_mode,
    run_ingestion_and_validation,
    run_analysis,
    run_diagnostics,
    main as pipeline_main
)

__version__ = "0.1.0"
__all__ = [
    # Ingest
    "RealDataFetchError",
    "setup_paths",
    "load_schema",
    "load_required_variables",
    "validate_variables",
    "fetch_real_data",
    "load_data",
    "detect_outliers_iqr",
    "save_outlier_report",
    "filter_outliers",
    "save_filtered_data",
    "calculate_checksum",
    "record_checksum",
    "ingest_main",
    # Analysis
    "set_analysis_seed",
    "check_distribution",
    "select_correlation_method",
    "run_correlation_analysis",
    "benjamini_hochberg_fdr",
    "analysis_main",
    # Transform
    "apply_compositional_correction",
    "transform_main",
    # Diagnostics
    "set_diagnostics_seed",
    "detect_perfect_multicollinearity",
    "calculate_vif",
    "run_sensitivity_analysis",
    "calculate_power",
    "diagnostics_main",
    # Report
    "load_json_file",
    "generate_report",
    "report_main",
    # Synthetic
    "set_seeds",
    "load_req_vars_synthetic",
    "generate_metagenomic_counts",
    "generate_sleep_metrics",
    "generate_synthetic_dataset",
    "generate_synthetic_manifest",
    "synthetic_main",
    # Reference Validator
    "VerificationStatus",
    "CitationSchema",
    "VerificationResult",
    "ReferenceValidator",
    "create_sample_schema",
    "validator_main",
    # Main Pipeline
    "main_setup_paths",
    "estimate_ram_usage",
    "determine_compute_strategy",
    "save_compute_strategy",
    "check_validation_mode",
    "run_ingestion_and_validation",
    "run_analysis",
    "run_diagnostics",
    "pipeline_main",
]