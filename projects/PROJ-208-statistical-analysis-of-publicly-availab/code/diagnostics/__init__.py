"""
Diagnostics module for statistical analysis.

Contains modules for:
- Collinearity diagnostics (VIF calculation)
- Sensitivity analysis
"""

from .collinearity import (
    load_cleaned_data,
    prepare_design_matrix,
    calculate_vif,
    flag_collinearity,
    analyze_collinearity,
    save_results,
    main
)

__all__ = [
    'load_cleaned_data',
    'prepare_design_matrix',
    'calculate_vif',
    'flag_collinearity',
    'analyze_collinearity',
    'save_results',
    'main'
]
