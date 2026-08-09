"""
Analysis module for statistical analysis and metadata management.

This module contains:
- Statistical analysis functions (stats.py)
- Statistical analysis runner (run_statistical_analysis.py)
- Statistical results generator (generate_statistical_results.py)
- Sensitivity analysis (sensitivity.py)
- Metadata utilities (metadata_utils.py)
- Output metadata updater (update_output_metadata.py)
"""
from .stats import (
    apply_bonferroni_correction,
    kruskal_wallis_test,
    mann_whitney_u_test,
    ks_test,
    nearest_neighbor_matching,
    linear_regression_with_mass_control
)

from .run_statistical_analysis import (
    load_halo_data,
    load_galaxy_properties,
    merge_halo_galaxy_data,
    run_statistical_tests,
    run_tests_for_property,
    run_tests_for_metric,
    apply_bonferroni_correction,
    main
)

from .generate_statistical_results import (
    load_metadata,
    save_metadata,
    add_associational_only_flag,
    main
)

from .metadata_utils import (
    load_metadata as load_metadata_utils,
    save_metadata as save_metadata_utils,
    add_associational_only_flag_to_dataset,
    add_associational_only_flag_to_csv,
    flag_all_output_datasets
)

__all__ = [
    # Stats
    'apply_bonferroni_correction',
    'kruskal_wallis_test',
    'mann_whitney_u_test',
    'ks_test',
    'nearest_neighbor_matching',
    'linear_regression_with_mass_control',
    
    # Run statistical analysis
    'load_halo_data',
    'load_galaxy_properties',
    'merge_halo_galaxy_data',
    'run_statistical_tests',
    'run_tests_for_property',
    'run_tests_for_metric',
    'main as run_analysis_main',
    
    # Generate statistical results
    'load_metadata',
    'save_metadata',
    'add_associational_only_flag',
    
    # Metadata utilities
    'load_metadata_utils',
    'save_metadata_utils',
    'add_associational_only_flag_to_dataset',
    'add_associational_only_flag_to_csv',
    'flag_all_output_datasets'
]