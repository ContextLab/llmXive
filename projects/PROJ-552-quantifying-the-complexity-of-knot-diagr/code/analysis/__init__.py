"""
Analysis module for knot complexity research.

This module contains analysis scripts for:
- Data quality assessment
- Dataset statistics
- Exploratory visualization
- Hyperbolic volume validation
- OEIS validation
- Precision validation
- Complexity visualization
"""

from .data_quality import (
    NullStatistics,
    DataQualityReport,
    calculate_null_percentages,
    generate_data_quality_report,
    write_data_quality_report_md,
    main as data_quality_main
)

from .dataset_counts import (
    load_cleaned_knots as dataset_counts_load_cleaned_knots,
    count_knots_per_crossing_number,
    generate_dataset_counts_report,
    main as dataset_counts_main
)

from .exploratory import (
    load_cleaned_knots as exploratory_load_cleaned_knots,
    create_stratified_scatter_plot,
    generate_exploratory_plots,
    main as exploratory_main
)

from .hyperbolic_volume_validation import (
    ValidationEntry,
    ValidationResult,
    HyperbolicVolumeValidator,
    main as hyperbolic_volume_main
)

from .oeis_validation import (
    ValidationEntry as OeisValidationEntry,
    ValidationResult as OeisValidationResult,
    OeisValidator,
    load_cleaned_knots as oeis_load_cleaned_knots,
    count_knots_per_crossing_number as oeis_count_knots_per_crossing_number,
    validate_oeis_a002863,
    main as oeis_main
)

from .precision import (
    PrecisionValidationEntry,
    PrecisionValidationResult,
    load_cleaned_knots as precision_load_cleaned_knots,
    validate_crossing_number_precision,
    validate_braid_index_precision,
    validate_alternating_classification,
    calculate_precision_score,
    validate_knot_precision,
    validate_precision,
    generate_precision_report,
    save_precision_report,
    main as precision_main
)

from .complexity_visualization import (
    VisualizationSpec,
    load_cleaned_knots as viz_load_cleaned_knots,
    create_complexity_heatmap,
    create_crossing_braid_scatter,
    create_complexity_distribution,
    create_braid_index_by_crossing,
    create_complexity_feature_examples,
    generate_complexity_visualization_examples,
    main as viz_main
)

__all__ = [
    # Data quality
    'NullStatistics',
    'DataQualityReport',
    'calculate_null_percentages',
    'generate_data_quality_report',
    'write_data_quality_report_md',
    'data_quality_main',

    # Dataset counts
    'dataset_counts_load_cleaned_knots',
    'count_knots_per_crossing_number',
    'generate_dataset_counts_report',
    'dataset_counts_main',

    # Exploratory analysis
    'exploratory_load_cleaned_knots',
    'create_stratified_scatter_plot',
    'generate_exploratory_plots',
    'exploratory_main',

    # Hyperbolic volume validation
    'ValidationEntry',
    'ValidationResult',
    'HyperbolicVolumeValidator',
    'hyperbolic_volume_main',

    # OEIS validation
    'OeisValidationEntry',
    'OeisValidationResult',
    'OeisValidator',
    'oeis_load_cleaned_knots',
    'oeis_count_knots_per_crossing_number',
    'validate_oeis_a002863',
    'oeis_main',

    # Precision validation
    'PrecisionValidationEntry',
    'PrecisionValidationResult',
    'precision_load_cleaned_knots',
    'validate_crossing_number_precision',
    'validate_braid_index_precision',
    'validate_alternating_classification',
    'calculate_precision_score',
    'validate_knot_precision',
    'validate_precision',
    'generate_precision_report',
    'save_precision_report',
    'precision_main',

    # Complexity visualization
    'VisualizationSpec',
    'viz_load_cleaned_knots',
    'create_complexity_heatmap',
    'create_crossing_braid_scatter',
    'create_complexity_distribution',
    'create_braid_index_by_crossing',
    'create_complexity_feature_examples',
    'generate_complexity_visualization_examples',
    'viz_main',
]