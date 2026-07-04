"""
GLM Analysis Module for PROJ-710.

This module fits Generalized Linear Models (GLM) with binomial link
to test the effects of epsilon and noise type on coverage probability.
"""
import statsmodels.api as sm
from statsmodels.formula.api import glm as smf_glm
from typing import Tuple, Optional
import pandas as pd


def fit_coverage_glm(
    df: pd.DataFrame,
    formula: str = "covered ~ epsilon * noise_type"
) -> Tuple[sm.GLM, sm.GLMResultsWrapper]:
    """
    Fit a GLM with binomial family to coverage data.

    Args:
        df: DataFrame containing 'covered', 'epsilon', 'noise_type', and optionally 'dataset', 'statistic'.
        formula: R-style formula for the GLM.

    Returns:
        Tuple of (model, results)
    """
    # Ensure 'covered' is numeric and binary
    if df['covered'].dtype not in [np.float64, np.float32, np.int64, np.int32]:
        df = df.copy()
        df['covered'] = pd.to_numeric(df['covered'], errors='coerce')

    # Drop NaNs in key variables
    df_clean = df.dropna(subset=['covered', 'epsilon'])

    if len(df_clean) == 0:
        raise ValueError("DataFrame is empty after dropping NaNs.")

    # Fit the model
    model = smf_glm(formula=formula, data=df_clean, family=sm.families.Binomial())
    result = model.fit()

    return model, result
