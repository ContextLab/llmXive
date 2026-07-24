import os
import logging
from typing import Dict, List, Optional, Union, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from scipy.interpolate import LSQUnivariateSpline

logger = logging.getLogger(__name__)

def calculate_elemental_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate elemental ratios (C/Mn, Cr/Ni) and add them to the DataFrame.
    Assumes columns exist: 'C', 'Mn', 'Cr', 'Ni'.
    """
    df = df.copy()
    ratio_cols = []

    # C/Mn ratio
    if 'C' in df.columns and 'Mn' in df.columns:
        # Avoid division by zero
        df['C_Mn_ratio'] = df['C'] / df['Mn'].replace(0, np.nan)
        ratio_cols.append('C_Mn_ratio')

    # Cr/Ni ratio
    if 'Cr' in df.columns and 'Ni' in df.columns:
        df['Cr_Ni_ratio'] = df['Cr'] / df['Ni'].replace(0, np.nan)
        ratio_cols.append('Cr_Ni_ratio')

    logger.info(f"Calculated elemental ratios: {ratio_cols}")
    return df

def calculate_pairwise_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate specific pairwise interactions:
    1. cooling rate × holding time
    2. C × Cooling Rate
    """
    df = df.copy()
    interaction_cols = []

    # cooling rate × holding time
    # Assume normalized columns exist from T012: 'cooling_rate_norm', 'holding_time_norm'
    if 'cooling_rate_norm' in df.columns and 'holding_time_norm' in df.columns:
        df['cooling_rate_x_holding_time'] = df['cooling_rate_norm'] * df['holding_time_norm']
        interaction_cols.append('cooling_rate_x_holding_time')

    # C × Cooling Rate
    if 'C' in df.columns and 'cooling_rate_norm' in df.columns:
        df['C_x_cooling_rate'] = df['C'] * df['cooling_rate_norm']
        interaction_cols.append('C_x_cooling_rate')

    logger.info(f"Calculated pairwise interactions: {interaction_cols}")
    return df

def orthogonalize_spline(x: np.ndarray, y: np.ndarray, degree: int = 3, n_knots: int = 5) -> np.ndarray:
    """
    Perform non-linear orthogonalization of y against x using a natural spline basis.
    Regress y against a spline basis of x, return the residuals.

    Parameters:
    -----------
    x : np.ndarray
        The predictor variable (main effect).
    y : np.ndarray
        The variable to orthogonalize (interaction term).
    degree : int
        Degree of the spline (default 3).
    n_knots : int
        Number of interior knots (default 5).

    Returns:
    --------
    np.ndarray
        Residuals of y after regressing against the spline basis of x.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")

    # Create knot sequence for LSQUnivariateSpline
    # We need to place knots appropriately within the range of x
    x_sorted = np.sort(x)
    if len(x_sorted) < n_knots + 2:
        # Fallback if not enough data points
        logger.warning(f"Not enough data points ({len(x)}) for {n_knots} knots. Reducing knots.")
        n_knots = max(1, len(x_sorted) - 2)

    # Generate interior knots
    # LSQUnivariateSpline expects interior knots
    t_min, t_max = x_sorted[0], x_sorted[-1]
    knots = np.linspace(t_min, t_max, n_knots + 2)[1:-1]

    try:
        spline = LSQUnivariateSpline(x, y, knots)
        y_pred = spline(x)
        residuals = y - y_pred
    except Exception as e:
        logger.warning(f"Spline fitting failed: {e}. Falling back to linear regression.")
        # Fallback to linear regression if spline fails
        slope, intercept, _, _, _ = stats.linregress(x, y)
        y_pred = slope * x + intercept
        residuals = y - y_pred

    return residuals

def orthogonalize_interactions(df: pd.DataFrame, interaction_cols: List[str], main_effect_cols: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Orthogonalize interaction features against their constituent main effects.

    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame.
    interaction_cols : List[str]
        List of interaction column names to orthogonalize.
    main_effect_cols : Dict[str, List[str]]
        Mapping from interaction column name to list of main effect column names.

    Returns:
    --------
    pd.DataFrame
        DataFrame with orthogonalized interaction columns.
    """
    df = df.copy()

    for interaction in interaction_cols:
        if interaction not in df.columns:
            logger.warning(f"Interaction column {interaction} not found in DataFrame.")
            continue

        if interaction not in main_effect_cols:
            logger.warning(f"No main effects defined for interaction {interaction}. Skipping.")
            continue

        main_effects = main_effect_cols[interaction]
        missing_effects = [col for col in main_effects if col not in df.columns]
        if missing_effects:
            logger.warning(f"Missing main effects for {interaction}: {missing_effects}. Skipping.")
            continue

        # Extract the interaction series
        y = df[interaction].values

        # Orthogonalize against each main effect sequentially or combined?
        # Standard approach: Regress against all main effects (linear or spline) and take residuals.
        # Here we apply spline orthogonalization against each main effect sequentially to be conservative,
        # or combine them. The spec says "regressing interactions against a natural spline basis".
        # We will regress against the combined set of main effects using a linear model first,
        # then apply spline residuals if needed, or simply apply spline against each.
        # Given the specific instruction "regressing interactions against a natural spline basis, degree=3, knots=5",
        # we interpret this as applying the spline orthogonalization for each main effect.

        orthogonalized_y = y.copy()
        for main_col in main_effects:
            x = df[main_col].values
            orthogonalized_y = orthogonalize_spline(x, orthogonalized_y, degree=3, n_knots=5)

        df[f'{interaction}_orthogonalized'] = orthogonalized_y
        logger.info(f"Orthogonalized {interaction} against {main_effects}.")

    return df

def detect_zero_variance_columns(df: pd.DataFrame) -> List[str]:
    """
    Detect columns with zero variance (constant values) or near-zero variance.
    These are collinear features that provide no predictive power.

    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame.

    Returns:
    --------
    List[str]
        List of column names with zero or near-zero variance.
    """
    zero_var_cols = []
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            # Check variance
            var = df[col].var()
            if var == 0 or np.isnan(var):
                zero_var_cols.append(col)
            # Also check for near-zero variance (e.g., variance < 1e-10)
            elif var < 1e-10:
                zero_var_cols.append(col)
        else:
            # For categorical/object columns, check unique values
            if df[col].nunique() <= 1:
                zero_var_cols.append(col)

    if zero_var_cols:
        logger.info(f"Detected zero/near-zero variance columns: {zero_var_cols}")
    else:
        logger.info("No zero/near-zero variance columns detected.")

    return zero_var_cols

def exclude_collinear_thermal_features(df: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
    """
    Exclude collinear thermal features based on correlation or zero variance.
    This implements the "zero-variance detection" and "collinear thermal features" exclusion.

    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame.
    threshold : float
        Correlation threshold for considering features collinear (not used in this specific
        implementation which focuses on zero-variance as per task description, but kept for extensibility).

    Returns:
    --------
    pd.DataFrame
        DataFrame with collinear/zero-variance thermal features removed.
    """
    df = df.copy()

    # Step 1: Detect zero-variance columns
    zero_var_cols = detect_zero_variance_columns(df)

    # Step 2: Specifically look for thermal features that might be collinear
    # Define thermal feature names that might be present
    thermal_feature_keywords = ['temp', 'cooling', 'heating', 'time', 'rate', 'holding', 'anneal', 'quench']
    thermal_cols = [col for col in df.columns if any(kw in col.lower() for kw in thermal_feature_keywords)]

    # Check for high correlation among thermal features (optional, as per "collinear" requirement)
    # If variance is zero, they are perfectly collinear with a constant.
    # If variance is non-zero but correlation is 1.0, they are collinear.
    collinear_thermal_cols = set(zero_var_cols) # Start with zero variance

    if len(thermal_cols) > 1:
        thermal_df = df[thermal_cols]
        # Calculate correlation matrix
        corr_matrix = thermal_df.corr().abs()

        # Select upper triangle of correlation matrix
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

        # Find features with correlation above threshold
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]

        collinear_thermal_cols.update(to_drop)

    # Remove identified columns
    cols_to_drop = list(collinear_thermal_cols)
    if cols_to_drop:
        logger.info(f"Dropping collinear/zero-variance thermal features: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)
    else:
        logger.info("No collinear thermal features to drop.")

    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main entry point for feature engineering.
    1. Calculate elemental ratios.
    2. Calculate pairwise interactions.
    3. Orthogonalize interactions.
    4. Detect and exclude zero-variance/collinear thermal features.

    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame with raw and normalized features.

    Returns:
    --------
    pd.DataFrame
        DataFrame with engineered features.
    """
    logger.info("Starting feature engineering pipeline.")

    # 1. Elemental Ratios
    df = calculate_elemental_ratios(df)

    # 2. Pairwise Interactions
    df = calculate_pairwise_interactions(df)

    # 3. Orthogonalize Interactions
    # Define which interactions to orthogonalize and their main effects
    interaction_map = {
        'cooling_rate_x_holding_time': ['cooling_rate_norm', 'holding_time_norm'],
        'C_x_cooling_rate': ['C', 'cooling_rate_norm']
    }
    interaction_cols = list(interaction_map.keys())
    # Filter to only those present in df
    present_interactions = [col for col in interaction_cols if col in df.columns]

    if present_interactions:
        df = orthogonalize_interactions(df, present_interactions, interaction_map)

    # 4. Exclude Collinear Thermal Features (Zero Variance)
    df = exclude_collinear_thermal_features(df)

    logger.info("Feature engineering pipeline completed.")
    return df
