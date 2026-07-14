"""
Analysis module for the llmXive research pipeline.
Provides functions for statistical modeling, bootstrap confidence intervals,
FDR correction, sensitivity analysis, and results reporting.
"""

from .bootstrap_ci import (
    load_seed_config,
    compute_bca_bootstrap_ci,
    run_bootstrap_analysis,
    main as bootstrap_main
)
from .fdr_correction import (
    load_regression_results,
    apply_benjamini_hochberg,
    add_fdr_correction_to_results,
    main as fdr_main
)
from .models import (
    load_synthetic_cohort,
    create_interaction_term,
    fit_ols_model,
    extract_model_results,
    run_all_models,
    main as models_main
)
from .results import (
    load_synthetic_cohort as load_cohort_for_results,
    load_regression_results as load_reg_for_results,
    generate_summary_stats,
    format_coefficient,
    generate_markdown_report,
    save_report,
    main as results_main
)
from .scales import (
    load_scale_config,
    score_cesd,
    score_gad7,
    score_pcl5
)
from .sensitivity import (
    load_synthetic_cohort as load_cohort_for_sens,
    load_baseline_results,
    fit_ols_model_continuous,
    stratify_by_platform,
    run_sensitivity_analysis,
    save_results as save_sens_results,
    main as sensitivity_main
)
from .sensitivity_compare import (
    load_baseline_results as load_baseline_for_compare,
    load_sensitivity_results,
    extract_interaction_coefficients,
    compare_coefficients,
    save_comparison_table,
    main as compare_main
)
from .validation import (
    calculate_smd,
    check_balance,
    check_harassment_variance,
    check_vif,
    validate_synthetic_cohort,
    main as validation_main
)

__all__ = [
    # Bootstrap
    'load_seed_config', 'compute_bca_bootstrap_ci', 'run_bootstrap_analysis', 'bootstrap_main',
    # FDR
    'load_regression_results', 'apply_benjamini_hochberg', 'add_fdr_correction_to_results', 'fdr_main',
    # Models
    'load_synthetic_cohort', 'create_interaction_term', 'fit_ols_model', 'extract_model_results', 'run_all_models', 'models_main',
    # Results
    'load_cohort_for_results', 'load_reg_for_results', 'generate_summary_stats', 'format_coefficient', 'generate_markdown_report', 'save_report', 'results_main',
    # Scales
    'load_scale_config', 'score_cesd', 'score_gad7', 'score_pcl5',
    # Sensitivity
    'load_cohort_for_sens', 'load_baseline_results', 'fit_ols_model_continuous', 'stratify_by_platform', 'run_sensitivity_analysis', 'save_sens_results', 'sensitivity_main',
    # Sensitivity Compare
    'load_baseline_for_compare', 'load_sensitivity_results', 'extract_interaction_coefficients', 'compare_coefficients', 'save_comparison_table', 'compare_main',
    # Validation
    'calculate_smd', 'check_balance', 'check_harassment_variance', 'check_vif', 'validate_synthetic_cohort', 'validation_main'
]
