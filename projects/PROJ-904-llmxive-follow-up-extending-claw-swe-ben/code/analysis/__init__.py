"""
Data analysis and aggregation module.

Contains tools for merging results, failure classification, and GLM analysis.
"""
from analysis.merge_results import (
    MergedResultRow,
    validate_input_schema,
    validate_strategy_consistency,
    validate_model_sizes,
    define_aggregation_schema,
    define_merge_logic,
    execute_merge
)
from analysis.failure_classifier import (
    FailureCategory,
    classify_failure,
    process_results
)
from analysis.glm_analyzer import (
    GLMConvergenceError,
    load_results_data,
    prepare_features,
    fit_firth_glm,
    fit_glm_with_interaction,
    perform_post_hoc_analysis,
    run_glm_analysis
)

__all__ = [
    'MergedResultRow',
    'validate_input_schema',
    'validate_strategy_consistency',
    'validate_model_sizes',
    'define_aggregation_schema',
    'define_merge_logic',
    'execute_merge',
    'FailureCategory',
    'classify_failure',
    'process_results',
    'GLMConvergenceError',
    'load_results_data',
    'prepare_features',
    'fit_firth_glm',
    'fit_glm_with_interaction',
    'perform_post_hoc_analysis',
    'run_glm_analysis'
]
