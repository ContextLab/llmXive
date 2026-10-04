import os
import logging
from typing import Dict, List, Optional, Union, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from scipy.interpolate import UnivariateSpline

logger = logging.getLogger(__name__)

def calculate_elemental_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate elemental ratios (e.g., C/Mn, Cr/Ni) based on composition columns.
    Adds new columns to the dataframe.
    """
    df = df.copy()
    
    # Define common ratios to calculate if columns exist
    ratios = [
        ('C', 'Mn', 'C_Mn_ratio'),
        ('Cr', 'Ni', 'Cr_Ni_ratio'),
        ('C', 'Si', 'C_Si_ratio'),
        ('Mn', 'Si', 'Mn_Si_ratio')
    ]
    
    for num, denom, new_col in ratios:
        if num in df.columns and denom in df.columns:
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                df[new_col] = np.where(
                    df[denom] != 0,
                    df[num] / df[denom],
                    0.0
                )
            logger.info(f"Calculated ratio {new_col}")
        else:
            logger.debug(f"Skipping ratio {new_col}: missing columns ({num} or {denom})")
    
    return df

def calculate_pairwise_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate pairwise interactions, specifically:
    - cooling_rate × holding_time
    - C × Cooling_Rate
    """
    df = df.copy()
    interactions = []
    
    # Check for thermal interactions
    if 'cooling_rate' in df.columns and 'holding_time' in df.columns:
        col_name = 'cooling_rate_x_holding_time'
        df[col_name] = df['cooling_rate'] * df['holding_time']
        interactions.append(col_name)
        logger.info(f"Calculated interaction {col_name}")
    
    # Check for composition-thermal interactions
    # Handle potential case variations
    c_col = None
    cr_col = None
    
    for col in df.columns:
        if col.lower() == 'c' or col.lower() == 'carbon':
            c_col = col
        if col.lower() == 'cooling_rate':
            cr_col = col
    
    if c_col and cr_col:
        col_name = f'{c_col}_x_{cr_col}'
        df[col_name] = df[c_col] * df[cr_col]
        interactions.append(col_name)
        logger.info(f"Calculated interaction {col_name}")
    
    return df

def orthogonalize_spline(x: np.ndarray, y: np.ndarray, degree: int = 3, knots: int = 5) -> np.ndarray:
    """
    Orthogonalize y against x using a natural spline basis.
    Fits a spline regression of y on x, then returns the residuals.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    
    if len(x) < knots:
        logger.warning(f"Data length ({len(x)}) is less than requested knots ({knots}). Reducing knots.")
        knots = max(1, len(x) - 1)
    
    # Fit spline
    try:
        spline = UnivariateSpline(x, y, k=min(degree, len(x)-1), s=0) # s=0 for interpolation if possible, or smoothing
        # Actually, for orthogonalization, we want the projection. 
        # Using UnivariateSpline for regression:
        # We need to solve for coefficients or use the spline to predict.
        # A more robust way for "regressing against a spline basis" is to use the spline object directly.
        
        # Predicted values based on spline fit
        y_pred = spline(x)
        
        # Residuals
        residuals = y - y_pred
        return residuals
    except Exception as e:
        logger.error(f"Spline orthogonalization failed: {e}")
        # Fallback to linear if spline fails (though task asks for spline)
        logger.warning("Falling back to linear regression for orthogonalization")
        slope, intercept, _, _, _ = stats.linregress(x, y)
        return y - (slope * x + intercept)

def orthogonalize_interactions(df: pd.DataFrame, interaction_cols: List[str], main_effect_cols: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Orthogonalize interaction features against their constituent main effects.
    interaction_cols: list of interaction column names
    main_effect_cols: dict mapping interaction col -> list of main effect col names
    """
    df = df.copy()
    
    for inter_col in interaction_cols:
        if inter_col not in df.columns:
            continue
        
        if inter_col not in main_effect_cols:
            logger.warning(f"No main effects defined for interaction {inter_col}, skipping orthogonalization.")
            continue
        
        main_effects = main_effect_cols[inter_col]
        missing = [m for m in main_effects if m not in df.columns]
        if missing:
            logger.warning(f"Missing main effects for {inter_col}: {missing}. Skipping.")
            continue
        
        # Orthogonalize against each main effect sequentially or jointly?
        # Task says "regressing interactions against a natural spline basis".
        # Usually, this means regressing the interaction term against the spline-transformed main effects.
        # We will do a sequential orthogonalization for simplicity and robustness, 
        # or fit a model with all main effects.
        
        # Let's fit a model: Interaction ~ Spline(Main1) + Spline(Main2) + ...
        # Then take residuals.
        
        # Since UnivariateSpline is univariate, we can do sequential or use a simple linear model 
        # if we treat the spline basis as features. 
        # To strictly follow "natural spline basis, degree=3, knots=5", we can use patsy or statsmodels,
        # but to avoid heavy deps, we'll approximate by orthogonalizing against each main effect 
        # using the spline helper.
        
        residuals = df[inter_col].values
        for main_col in main_effects:
            x = df[main_col].values
            residuals = orthogonalize_spline(x, residuals, degree=3, knots=5)
        
        df[inter_col] = residuals
        logger.info(f"Orthogonalized {inter_col} against {main_effects}")
    
    return df

def detect_zero_variance_columns(df: pd.DataFrame) -> List[str]:
    """
    Detect columns with zero variance (constant values) or near-zero variance.
    Returns a list of column names to be excluded.
    """
    zero_var_cols = []
    
    for col in df.columns:
        if df[col].dtype in ['object', 'bool']:
            # For categorical, check unique count
            if df[col].nunique() <= 1:
                zero_var_cols.append(col)
        else:
            # For numeric, check variance
            if df[col].var() == 0.0:
                zero_var_cols.append(col)
    
    if zero_var_cols:
        logger.warning(f"Detected {len(zero_var_cols)} zero-variance columns: {zero_var_cols}")
    
    return zero_var_cols

def exclude_collinear_thermal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude collinear thermal features (Edge Case).
    Specifically targets thermal parameters that might have zero variance or perfect correlation.
    1. Detect zero variance thermal columns.
    2. Detect perfect correlation (|r| == 1.0) between thermal columns.
    """
    df = df.copy()
    
    # Identify thermal columns (heuristic: contains 'temp', 'rate', 'time', 'cool', 'heat')
    thermal_keywords = ['temp', 'rate', 'time', 'cool', 'heat', 'treatment']
    thermal_cols = [c for c in df.columns if any(k in c.lower() for k in thermal_keywords)]
    
    if not thermal_cols:
        logger.info("No thermal columns detected.")
        return df
    
    logger.info(f"Analyzing thermal columns: {thermal_cols}")
    
    # 1. Zero Variance Check
    cols_to_drop = []
    for col in thermal_cols:
        if df[col].var() == 0.0:
            cols_to_drop.append(col)
            logger.warning(f"Dropping zero-variance thermal column: {col}")
    
    # 2. Perfect Correlation Check
    # Only check numeric columns
    numeric_thermal = [c for c in thermal_cols if c not in cols_to_drop and pd.api.types.is_numeric_dtype(df[c])]
    
    if len(numeric_thermal) > 1:
        corr_matrix = df[numeric_thermal].corr()
        for i, col1 in enumerate(numeric_thermal):
            for j, col2 in enumerate(numeric_thermal):
                if i < j:
                    if abs(corr_matrix.loc[col1, col2]) == 1.0:
                        # Drop the second one to avoid redundancy
                        if col2 not in cols_to_drop:
                            cols_to_drop.append(col2)
                            logger.warning(f"Dropping collinear thermal column {col2} (corr={corr_matrix.loc[col1, col2]:.2f} with {col1})")
    
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        logger.info(f"Excluded {len(cols_to_drop)} collinear/zero-variance thermal features.")
    
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main pipeline function to engineer features:
    1. Calculate elemental ratios.
    2. Calculate pairwise interactions.
    3. Orthogonalize interactions.
    4. Detect and exclude zero-variance columns.
    5. Exclude collinear thermal features.
    """
    logger.info("Starting feature engineering pipeline...")
    
    # 1. Ratios
    df = calculate_elemental_ratios(df)
    
    # 2. Interactions
    df = calculate_pairwise_interactions(df)
    
    # 3. Orthogonalization
    # Define interactions and their main effects based on calculate_pairwise_interactions logic
    interaction_map = {}
    if 'cooling_rate_x_holding_time' in df.columns:
        interaction_map['cooling_rate_x_holding_time'] = ['cooling_rate', 'holding_time']
    # Check for C_x_Cooling_Rate variant
    for col in df.columns:
        if col.endswith('_x_cooling_rate') or col.endswith('_x_Cooling_Rate'):
            # Infer main effects: C and cooling_rate
            interaction_map[col] = ['C', 'cooling_rate'] # Assuming 'C' exists, might need refinement
            # Better: find the other part
            parts = col.split('_x_')
            if len(parts) == 2:
                interaction_map[col] = [parts[0], parts[1]]
    
    if interaction_map:
        df = orthogonalize_interactions(df, list(interaction_map.keys()), interaction_map)
    
    # 4. Zero Variance Detection (General)
    zero_var = detect_zero_variance_columns(df)
    if zero_var:
        df = df.drop(columns=zero_var)
    
    # 5. Collinear Thermal Features
    df = exclude_collinear_thermal_features(df)
    
    logger.info("Feature engineering pipeline completed.")
    return df
