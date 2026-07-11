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
    Calculate elemental ratios (e.g., C/Mn, Cr/Ni) for steel composition analysis.
    
    Args:
        df: DataFrame containing composition columns (e.g., 'C', 'Mn', 'Cr', 'Ni')
        
    Returns:
        DataFrame with added ratio columns
    """
    df = df.copy()
    composition_cols = ['C', 'Mn', 'Cr', 'Ni', 'Mo', 'V', 'Cu', 'Si', 'P', 'S']
    
    # Calculate C/Mn ratio if both exist
    if 'C' in df.columns and 'Mn' in df.columns:
        # Avoid division by zero
        mask = df['Mn'] > 0
        df.loc[mask, 'C_Mn_ratio'] = df.loc[mask, 'C'] / df.loc[mask, 'Mn']
        # Handle zero Mn cases
        df.loc[~mask, 'C_Mn_ratio'] = np.nan
    
    # Calculate Cr/Ni ratio if both exist
    if 'Cr' in df.columns and 'Ni' in df.columns:
        mask = df['Ni'] > 0
        df.loc[mask, 'Cr_Ni_ratio'] = df.loc[mask, 'Cr'] / df.loc[mask, 'Ni']
        df.loc[~mask, 'Cr_Ni_ratio'] = np.nan
        
    logger.info(f"Calculated elemental ratios. Shape: {df.shape}")
    return df

def calculate_pairwise_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate pairwise interactions, specifically:
    - cooling_rate × holding_time
    - C × cooling_rate
    
    Args:
        df: DataFrame with thermal parameters and composition
        
    Returns:
        DataFrame with added interaction columns
    """
    df = df.copy()
    
    # Cooling rate × holding time interaction
    if 'cooling_rate' in df.columns and 'holding_time' in df.columns:
        df['cooling_rate_holding_time'] = df['cooling_rate'] * df['holding_time']
        logger.info("Created cooling_rate × holding_time interaction")
        
    # C × Cooling Rate interaction
    if 'C' in df.columns and 'cooling_rate' in df.columns:
        df['C_cooling_rate'] = df['C'] * df['cooling_rate']
        logger.info("Created C × cooling_rate interaction")
        
    return df

def orthogonalize_spline(
    interaction_col: pd.Series, 
    main_effects: List[pd.Series], 
    degree: int = 3, 
    knots: int = 5
) -> pd.Series:
    """
    Orthogonalize an interaction term against its constituent main effects 
    using non-linear orthogonalization with natural spline basis.
    
    Args:
        interaction_col: The interaction term to orthogonalize
        main_effects: List of main effect series to regress against
        degree: Degree of the spline basis (default 3)
        knots: Number of knots in the spline (default 5)
        
    Returns:
        Orthogonalized interaction term (residuals)
    """
    if len(main_effects) == 0:
        return interaction_col
        
    # Combine main effects into a design matrix
    X = pd.concat(main_effects, axis=1).values
    
    # Handle edge case where main effects are constant
    if X.shape[1] == 0 or np.all(X == X[0, 0]):
        return interaction_col - interaction_col.mean()
    
    # Create spline basis for each main effect
    basis_matrix = []
    for i, col in enumerate(main_effects):
        x = col.values
        # Skip constant columns
        if np.std(x) < 1e-10:
            continue
            
        # Create natural spline basis
        # Using UnivariateSpline for flexibility
        try:
            # Normalize x for better spline fitting
            x_norm = (x - x.min()) / (x.max() - x.min() + 1e-10)
            spline = UnivariateSpline(x_norm, x_norm, k=degree, s=None)
            
            # Evaluate spline basis at each point
            # We create a basis of 'degree' terms
            for j in range(degree):
                basis_col = spline(x_norm) * (x_norm ** j)
                basis_matrix.append(basis_col)
        except Exception as e:
            logger.warning(f"Failed to create spline basis for column {i}: {e}")
            # Fallback to polynomial terms
            for j in range(degree):
                basis_matrix.append(x ** (j + 1))
    
    if len(basis_matrix) == 0:
        return interaction_col - interaction_col.mean()
        
    # Stack basis matrix
    X_basis = np.column_stack(basis_matrix)
    
    # Add constant term
    X_basis = np.column_stack([np.ones(len(interaction_col)), X_basis])
    
    # Perform least squares regression: interaction = X_basis * beta + residuals
    try:
        # Use scipy's lstsq for numerical stability
        coeffs, residuals, rank, s = np.linalg.lstsq(X_basis, interaction_col.values, rcond=None)
        
        # Calculate fitted values
        fitted = X_basis @ coeffs
        
        # Return residuals (orthogonalized term)
        orthogonalized = interaction_col.values - fitted
        
        logger.debug(f"Orthogonalization residuals stats: mean={np.mean(orthogonalized):.6f}, std={np.std(orthogonalized):.6f}")
        return orthogonalized
        
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in orthogonalization, returning centered interaction")
        return interaction_col - interaction_col.mean()

def orthogonalize_interactions(df: pd.DataFrame, interaction_cols: List[str]) -> pd.DataFrame:
    """
    Orthogonalize multiple interaction terms against their constituent main effects.
    
    Args:
        df: DataFrame with interaction and main effect columns
        interaction_cols: List of interaction column names to orthogonalize
        
    Returns:
        DataFrame with orthogonalized interaction columns (prefixed with 'ortho_')
    """
    df = df.copy()
    
    for interaction_col in interaction_cols:
        if interaction_col not in df.columns:
            logger.warning(f"Interaction column {interaction_col} not found, skipping")
            continue
            
        # Infer main effects from column name (e.g., "cooling_rate_holding_time" -> ["cooling_rate", "holding_time"])
        parts = interaction_col.split('_')
        main_effects = []
        
        for part in parts:
            # Check if this part corresponds to a column in the dataframe
            if part in df.columns:
                main_effects.append(df[part])
            else:
                # Try to find a column that contains this part
                found = False
                for col in df.columns:
                    if part in col:
                        main_effects.append(df[col])
                        found = True
                        break
                if not found:
                    logger.warning(f"Could not find main effect for '{part}' in column '{interaction_col}'")
        
        if len(main_effects) > 0:
            orthogonalized = orthogonalize_spline(df[interaction_col], main_effects)
            df[f'ortho_{interaction_col}'] = orthogonalized
            logger.info(f"Orthogonalized {interaction_col} against {len(main_effects)} main effects")
        else:
            logger.warning(f"No main effects found for {interaction_col}, skipping orthogonalization")
            
    return df

def detect_zero_variance_columns(df: pd.DataFrame, threshold: float = 1e-10) -> List[str]:
    """
    Detect and return columns with zero or near-zero variance (collinear/constant features).
    
    Args:
        df: DataFrame to analyze
        threshold: Variance threshold below which a column is considered zero-variance
        
    Returns:
        List of column names with zero or near-zero variance
    """
    zero_var_cols = []
    
    for col in df.columns:
        if df[col].dtype in ['object', 'category']:
            # For categorical columns, check if only one unique value exists
            if df[col].nunique() <= 1:
                zero_var_cols.append(col)
        else:
            # For numeric columns, check variance
            var = df[col].var()
            if pd.isna(var) or var < threshold:
                zero_var_cols.append(col)
                
    if zero_var_cols:
        logger.warning(f"Detected {len(zero_var_cols)} zero/near-zero variance columns: {zero_var_cols}")
    else:
        logger.debug("No zero/near-zero variance columns detected")
        
    return zero_var_cols

def exclude_collinear_thermal_features(
    df: pd.DataFrame, 
    thermal_cols: Optional[List[str]] = None,
    threshold: float = 1e-10
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Detect and exclude collinear thermal features (zero-variance detection).
    
    This function identifies thermal parameters that have zero or near-zero variance
    (indicating they are constant across the dataset) and removes them from the DataFrame.
    
    Args:
        df: DataFrame containing thermal parameters
        thermal_cols: List of thermal column names to check. If None, tries to infer.
        threshold: Variance threshold for zero-variance detection
        
    Returns:
        Tuple of (cleaned DataFrame, list of removed column names)
    """
    df = df.copy()
    
    # Infer thermal columns if not provided
    if thermal_cols is None:
        potential_thermal = ['temperature', 'cooling_rate', 'holding_time', 'quench_rate', 
                           'anneal_temp', 'temper_temp', 'solution_temp']
        thermal_cols = [col for col in potential_thermal if col in df.columns]
        
        # Also check for any column with 'temp' or 'rate' or 'time' in the name
        if not thermal_cols:
            thermal_cols = [col for col in df.columns 
                           if any(keyword in col.lower() for keyword in ['temp', 'rate', 'time', 'cooling', 'holding'])]
    
    if not thermal_cols:
        logger.info("No thermal columns found to check for zero variance")
        return df, []
    
    # Detect zero-variance columns among thermal features
    zero_var_thermal = []
    for col in thermal_cols:
        if col not in df.columns:
            continue
            
        var = df[col].var()
        if pd.isna(var) or var < threshold:
            zero_var_thermal.append(col)
    
    # Remove zero-variance thermal columns
    if zero_var_thermal:
        logger.info(f"Removing {len(zero_var_thermal)} zero-variance thermal columns: {zero_var_thermal}")
        df = df.drop(columns=zero_var_thermal)
    else:
        logger.debug("No zero-variance thermal columns detected")
        
    return df, zero_var_thermal

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main feature engineering pipeline:
    1. Calculate elemental ratios
    2. Calculate pairwise interactions
    3. Orthogonalize interactions
    4. Detect and exclude zero-variance thermal features
    
    Args:
        df: Raw or preprocessed DataFrame
        
    Returns:
        DataFrame with all engineered features
    """
    logger.info(f"Starting feature engineering on dataset with shape: {df.shape}")
    
    # Step 1: Calculate elemental ratios
    df = calculate_elemental_ratios(df)
    
    # Step 2: Calculate pairwise interactions
    df = calculate_pairwise_interactions(df)
    
    # Step 3: Orthogonalize interactions
    # Identify interaction columns created in step 2
    interaction_cols = []
    for col in ['cooling_rate_holding_time', 'C_cooling_rate']:
        if col in df.columns:
            interaction_cols.append(col)
    
    if interaction_cols:
        df = orthogonalize_interactions(df, interaction_cols)
    
    # Step 4: Detect and exclude zero-variance thermal features
    df, removed_cols = exclude_collinear_thermal_features(df)
    
    logger.info(f"Feature engineering complete. Final shape: {df.shape}, Removed columns: {removed_cols}")
    return df

# Export public names
__all__ = [
    'calculate_elemental_ratios',
    'calculate_pairwise_interactions', 
    'orthogonalize_spline',
    'orthogonalize_interactions',
    'engineer_features',
    'detect_zero_variance_columns',
    'exclude_collinear_thermal_features'
]