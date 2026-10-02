"""
llmXive Scripts Package.

This package contains all pipeline execution scripts for the llmXive automated science
project. Each module implements a specific stage of the research pipeline:
- Ingestion: Download and parse datasets
- Ground Truth: Execute baseline tests and generate labels
- Feature Extraction: Calculate structural metrics and build graphs
- Modeling: Train models and determine decision boundaries
- Analysis: Generate reports and validate artifacts
"""

# Explicitly expose all public functions for cleaner imports
from .ingest import load_swe_bench, load_agent_bench, parse_swe_bench, parse_agent_bench, merge_datasets, write_to_csv, main as ingest_main
from .baseline_runner import ExecutionResult, run_with_timeout, run_baseline_task, main as baseline_main
from .generate_ground_truth import load_baseline_results, load_ingested_tasks, process_unparseable_tasks, generate_ground_truth, main as ground_truth_main
from .extract_features import load_ground_truth, filter_unparseable, get_lines_of_code, get_cyclomatic_complexity, get_dependency_depth, calculate_semantic_complexity_score, extract_graph_and_metrics, serialize_graph, load_graph_metrics, main as extract_main
from .generate_features import load_graph_metrics, merge_ground_truth_with_metrics, write_features_csv, main as features_main
from .validate_features import load_features_csv, validate_columns_present, validate_no_missing_metrics, main as validate_main
from .train_model import load_features, prepare_train_val_split, train_logistic_regression, train_random_forest, evaluate_model, calculate_correlation_coefficient, run_training_pipeline, main as train_main
from .sensitivity_analysis import load_model_and_features, calculate_fnr, run_sensitivity_analysis, main as sensitivity_main
from .identify_threshold import load_threshold_sweep, identify_optimal_threshold, save_decision_boundary, main as threshold_main
from .calculate_correlations import encode_target, calculate_correlations, main as correlations_main
from .generate_model_report import load_threshold_sweep_safe, load_decision_boundary, generate_model_report, main as report_main
from .update_state import ensure_state_dirs, load_state, save_state, update_task_status, add_artifact, main as state_main

__all__ = [
    # Ingest
    'load_swe_bench', 'load_agent_bench', 'parse_swe_bench', 'parse_agent_bench', 
    'merge_datasets', 'write_to_csv', 'ingest_main',
    # Baseline Runner
    'ExecutionResult', 'run_with_timeout', 'run_baseline_task', 'baseline_main',
    # Ground Truth
    'load_baseline_results', 'load_ingested_tasks', 'process_unparseable_tasks', 
    'generate_ground_truth', 'ground_truth_main',
    # Feature Extraction
    'load_ground_truth', 'filter_unparseable', 'get_lines_of_code', 
    'get_cyclomatic_complexity', 'get_dependency_depth', 
    'calculate_semantic_complexity_score', 'extract_graph_and_metrics', 
    'serialize_graph', 'load_graph_metrics', 'extract_main',
    # Feature Generation
    'merge_ground_truth_with_metrics', 'write_features_csv', 'features_main',
    # Validation
    'validate_columns_present', 'validate_no_missing_metrics', 'validate_main',
    # Modeling
    'load_features', 'prepare_train_val_split', 'train_logistic_regression', 
    'train_random_forest', 'evaluate_model', 'calculate_correlation_coefficient', 
    'run_training_pipeline', 'train_main',
    # Sensitivity Analysis
    'load_model_and_features', 'calculate_fnr', 'run_sensitivity_analysis', 'sensitivity_main',
    # Threshold Identification
    'load_threshold_sweep', 'identify_optimal_threshold', 'save_decision_boundary', 'threshold_main',
    # Correlations
    'encode_target', 'calculate_correlations', 'correlations_main',
    # Model Report
    'load_threshold_sweep_safe', 'load_decision_boundary', 'generate_model_report', 'report_main',
    # State Management
    'ensure_state_dirs', 'load_state', 'save_state', 'update_task_status', 
    'add_artifact', 'state_main',
]

__version__ = '0.1.0'

# Utility functions for package-level access
def get_available_scripts():
    """Return a list of available script modules in this package."""
    return [
        'ingest',
        'baseline_runner',
        'generate_ground_truth',
        'extract_features',
        'generate_features',
        'validate_features',
        'train_model',
        'sensitivity_analysis',
        'identify_threshold',
        'calculate_correlations',
        'generate_model_report',
        'update_state'
    ]
