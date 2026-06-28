"""
Analysis module for Social Memory Networks.

Contains statistical analysis functions including ANOVA, sensitivity analysis,
power analysis, and scaling analysis.
"""

from .anova import (
    ANOVAOutput,
    load_experiment_results,
    prepare_data_for_anova,
    compute_two_way_anova,
    run_anova_analysis,
    main
)

__all__ = [
    'ANOVAOutput',
    'load_experiment_results',
    'prepare_data_for_anova',
    'compute_two_way_anova',
    'run_anova_analysis',
    'main'
]
