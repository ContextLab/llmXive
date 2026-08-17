"""
Analysis module for cross-modal comparison of neural prediction error signals.

This module contains functions for computing metrics, source localization,
and statistical comparisons.
"""

from .metrics import (
    compute_difference_wave_auditory,
    compute_difference_wave_visual,
    extract_peak_latency,
    extract_mean_amplitude,
    generate_metrics_summary,
    main as metrics_main
)

from .source import (
    SourceLocalizationError,
    setup_icbm152_head_model,
    setup_source_space,
    compute_lead_fields,
    load_lead_fields,
    compute_inverse_operator,
    apply_inverse_source_estimation,
    run_sensitivity_analysis,
    main as source_main
)

from .stats import (
    StatsError,
    mixed_effects_permutation_test,
    independent_samples_ttest,
    tost_equivalence_test,
    benjamini_hochberg_correction,
    main as stats_main
)

__all__ = [
    'compute_difference_wave_auditory',
    'compute_difference_wave_visual',
    'extract_peak_latency',
    'extract_mean_amplitude',
    'generate_metrics_summary',
    'metrics_main',
    'SourceLocalizationError',
    'setup_icbm152_head_model',
    'setup_source_space',
    'compute_lead_fields',
    'load_lead_fields',
    'compute_inverse_operator',
    'apply_inverse_source_estimation',
    'run_sensitivity_analysis',
    'source_main',
    'StatsError',
    'mixed_effects_permutation_test',
    'independent_samples_ttest',
    'tost_equivalence_test',
    'benjamini_hochberg_correction',
    'stats_main'
]
