from .source import (
    SourceLocalizationError,
    setup_icbm152_head_model,
    setup_source_space,
    compute_lead_fields,
    load_lead_fields,
    compute_inverse_operator,
    apply_inverse_source_estimation,
    run_sensitivity_analysis,
    main
)
from .metrics import (
    generate_metrics_summary,
    compute_difference_wave_auditory,
    compute_difference_wave_visual,
    extract_peak_latency,
    extract_mean_amplitude
)
from .stats import (
    mixed_effects_permutation_test,
    independent_samples_ttest,
    tost_equivalence_test,
    benjamini_hochberg_correction
)
