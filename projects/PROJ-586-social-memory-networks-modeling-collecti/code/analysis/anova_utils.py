"""
Utility functions for ANOVA analysis to avoid circular imports.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from pathlib import Path
import sys

# Ensure parent is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

def safe_import_statsmodels():
    """Safely import statsmodels, handling potential missing dependencies."""
    try:
        import statsmodels.formula.api as smf
        import statsmodels.stats.anova as anova
        return smf, anova
    except ImportError as e:
        raise ImportError(
            "statsmodels is required for ANOVA analysis. "
            "Install with: pip install statsmodels"
        ) from e

def compute_effect_size_etasquared(ss_effect: float, ss_total: float) -> float:
    """
    Compute eta-squared effect size.
    
    eta² = SS_effect / SS_total
    """
    if ss_total == 0:
        return 0.0
    return ss_effect / ss_total