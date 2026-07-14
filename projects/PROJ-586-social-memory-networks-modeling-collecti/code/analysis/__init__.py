"""Analysis package for social memory networks."""
from __future__ import annotations

# Import public API from submodules
from .anova import (
    ANOVAOutput,
    load_experiment_results,
    prepare_data_for_anova,
    compute_two_way_anova,
    compute_manual_anova,
    apply_bonferroni_correction,
    run_anova_analysis,
    main as anova_main,
)
from .power import (
    PowerAnalysisResult,
    load_experiment_results as load_power_results,
    compute_effect_size_cohens_d,
    compute_effect_size_etasquared,
    compute_power_ttest,
    compute_power_anova,
    compute_detectable_effect_size,
    run_power_analysis,
    main as power_main,
)
from .scaling import (
    PowerLawFitResult,
    ScalingAnalysisResult,
    power_law,
    fit_power_law,
    load_scaling_data,
    run_scaling_analysis,
    generate_scaling_plot,
    build_parser as scaling_build_parser,
    main as scaling_main,
)
from .sensitivity import (
    SensitivityResult,
    truncate_context_to_token_limit,
    run_sensitivity_analysis,
    write_results_csv,
    build_parser as sensitivity_build_parser,
    main as sensitivity_main,
)

__all__ = [
    # ANOVA
    "ANOVAOutput",
    "load_experiment_results",
    "prepare_data_for_anova",
    "compute_two_way_anova",
    "compute_manual_anova",
    "apply_bonferroni_correction",
    "run_anova_analysis",
    "anova_main",
    # Power
    "PowerAnalysisResult",
    "load_power_results",
    "compute_effect_size_cohens_d",
    "compute_effect_size_etasquared",
    "compute_power_ttest",
    "compute_power_anova",
    "compute_detectable_effect_size",
    "run_power_analysis",
    "power_main",
    # Scaling
    "PowerLawFitResult",
    "ScalingAnalysisResult",
    "power_law",
    "fit_power_law",
    "load_scaling_data",
    "run_scaling_analysis",
    "generate_scaling_plot",
    "scaling_build_parser",
    "scaling_main",
    # Sensitivity
    "SensitivityResult",
    "truncate_context_to_token_limit",
    "run_sensitivity_analysis",
    "write_results_csv",
    "sensitivity_build_parser",
    "sensitivity_main",
]
