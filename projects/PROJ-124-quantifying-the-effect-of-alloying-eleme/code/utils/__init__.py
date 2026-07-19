"""
Shared utilities for the llmXive automated science pipeline.
"""
from .logger import (
    get_logger,
    PipelineError,
    DataDownloadError,
    DataIngestionError,
    FeatureEngineeringError,
    ModelTrainingError,
    ScreeningError,
    ConfigurationError,
    log_pipeline_start,
    log_pipeline_end,
    handle_pipeline_error
)
from .novelty import (
    load_known_alloys,
    normalize_composition,
    compositions_match,
    check_novelty,
    batch_check_novelty
)
from .shap_utils import (
    ensure_shap_available,
    compute_global_shap_values,
    get_feature_importance_from_shap,
    save_shap_results,
    generate_shap_summary_plot
)
from .state_manager import (
    compute_sha256,
    update_artifact_hash,
    verify_artifact_integrity
)
from .schema_validator import (
    load_schema,
    validate_csv_schema,
    validate_processed_features
)
from .setup_data_dirs import create_data_directories

__all__ = [
    # Logger
    'get_logger',
    'PipelineError',
    'DataDownloadError',
    'DataIngestionError',
    'FeatureEngineeringError',
    'ModelTrainingError',
    'ScreeningError',
    'ConfigurationError',
    'log_pipeline_start',
    'log_pipeline_end',
    'handle_pipeline_error',
    # Novelty
    'load_known_alloys',
    'normalize_composition',
    'compositions_match',
    'check_novelty',
    'batch_check_novelty',
    # SHAP
    'ensure_shap_available',
    'compute_global_shap_values',
    'get_feature_importance_from_shap',
    'save_shap_results',
    'generate_shap_summary_plot',
    # State
    'compute_sha256',
    'update_artifact_hash',
    'verify_artifact_integrity',
    # Schema
    'load_schema',
    'validate_csv_schema',
    'validate_processed_features',
    # Setup
    'create_data_directories'
]
