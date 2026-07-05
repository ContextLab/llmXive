import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List

from src.utils.logging import get_logger

logger = get_logger(__name__)


def load_climate_data(filepath: str) -> pd.DataFrame:
    """
    Load climate predictor data from a CSV file.
    
    Args:
        filepath: Path to the climate data CSV file.
        
    Returns:
        DataFrame with climate variables.
    """
    logger.info(f"Loading climate data from {filepath}")
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        return df
    except FileNotFoundError:
        logger.error(f"Climate data file not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error loading climate data: {e}")
        raise


def load_trait_data(filepath: str) -> pd.DataFrame:
    """
    Load functional trait data from a CSV file.
    
    Args:
        filepath: Path to the trait data CSV file.
        
    Returns:
        DataFrame with trait variables.
    """
    logger.info(f"Loading trait data from {filepath}")
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        return df
    except FileNotFoundError:
        logger.error(f"Trait data file not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error loading trait data: {e}")
        raise


def merge_predictors(climate_df: pd.DataFrame, trait_df: pd.DataFrame, key: str = "species") -> pd.DataFrame:
    """
    Merge climate and trait data on the specified key.
    
    Args:
        climate_df: DataFrame with climate variables.
        trait_df: DataFrame with trait variables.
        key: Column name to merge on (default: "species").
        
    Returns:
        Merged DataFrame with both climate and trait predictors.
    """
    logger.info(f"Merging predictors on key '{key}'")
    merged = pd.merge(climate_df, trait_df, on=key, how="inner")
    
    if len(merged) == 0:
        logger.warning("Merge resulted in an empty DataFrame. Check key alignment.")
    
    logger.info(f"Merged dataset has {len(merged)} records and {len(merged.columns)} columns")
    return merged


def create_full_predictor_matrix(merged_df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Create a numeric predictor matrix from the merged DataFrame, excluding non-numeric columns.
    
    Args:
        merged_df: Merged DataFrame with climate and trait data.
        exclude_cols: List of column names to exclude (e.g., species names, IDs).
        
    Returns:
        DataFrame containing only numeric predictor columns.
    """
    if exclude_cols is None:
        exclude_cols = []
        
    logger.info(f"Creating predictor matrix, excluding: {exclude_cols}")
    
    # Select only numeric columns, excluding specified ones
    numeric_cols = merged_df.select_dtypes(include=[np.number]).columns.tolist()
    predictor_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    if len(predictor_cols) == 0:
        raise ValueError("No numeric predictor columns found after filtering.")
        
    X = merged_df[predictor_cols]
    logger.info(f"Created predictor matrix with shape {X.shape}")
    return X


def get_predictor_columns(X: pd.DataFrame) -> List[str]:
    """
    Get the list of predictor column names.
    
    Args:
        X: Predictor DataFrame.
        
    Returns:
        List of column names.
    """
    return X.columns.tolist()


def validate_predictor_matrix(X: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the predictor matrix for VIF calculation.
    
    Args:
        X: Predictor DataFrame.
        
    Returns:
        Dictionary with validation results (n_samples, n_features, missing_values, etc.).
    """
    validation = {
        "n_samples": X.shape[0],
        "n_features": X.shape[1],
        "missing_values": int(X.isnull().sum().sum()),
        "infinite_values": int(np.isinf(X.values).sum()),
        "constant_features": 0
    }
    
    # Check for constant features (zero variance)
    for col in X.columns:
        if X[col].std() == 0:
            validation["constant_features"] += 1
            
    logger.info(f"Validation results: {validation}")
    
    if validation["missing_values"] > 0:
        logger.warning(f"Found {validation['missing_values']} missing values in predictor matrix.")
    if validation["infinite_values"] > 0:
        logger.warning(f"Found {validation['infinite_values']} infinite values in predictor matrix.")
    if validation["constant_features"] > 0:
        logger.warning(f"Found {validation['constant_features']} constant features (zero variance).")
        
    return validation


def compute_vif(X: pd.DataFrame, threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Compute Variance Inflation Factor (VIF) for each predictor in the matrix.
    
    VIF measures how much the variance of an estimated regression coefficient 
    increases if your predictors are correlated. A VIF > 5 indicates high 
    multicollinearity.
    
    Args:
        X: Predictor DataFrame (numeric columns only).
        threshold: VIF threshold for flagging high collinearity (default: 5.0).
        
    Returns:
        Tuple of (VIF DataFrame, List of flagged column names).
        
    Raises:
        ValueError: If X contains non-numeric data or insufficient samples.
    """
    logger.info(f"Computing VIF with threshold {threshold}")
    
    # Validate input
    if not all(np.issubdtype(dtype, np.number) for dtype in X.dtypes):
        raise ValueError("All columns in X must be numeric for VIF calculation.")
        
    if X.shape[0] <= X.shape[1]:
        raise ValueError(f"Insufficient samples ({X.shape[0]}) for {X.shape[1]} features. "
                       "Need more samples than features.")
        
    # Handle missing values by dropping rows
    X_clean = X.dropna()
    if X_clean.shape[0] != X.shape[0]:
        logger.warning(f"Dropped {X.shape[0] - X_clean.shape[0]} rows with missing values.")
        
    if X_clean.shape[0] <= X_clean.shape[1]:
        raise ValueError(f"After dropping missing values, insufficient samples ({X_clean.shape[0]}) "
                       f"for {X_clean.shape[1]} features.")
    
    vif_data = []
    
    logger.info("Calculating VIF for each predictor...")
    for i, col in enumerate(X_clean.columns):
        # Fit OLS regression of this column against all others
        y = X_clean[col]
        X_other = X_clean.drop(columns=[col])
        
        # Add constant for intercept
        X_other_with_const = X_other.copy()
        X_other_with_const['const'] = 1.0
        
        try:
            # Simple OLS: y = b0 + b1*x1 + ... + bn*xn
            # VIF = 1 / (1 - R^2)
            beta = np.linalg.lstsq(X_other_with_const.values, y.values, rcond=None)[0]
            y_pred = X_other_with_const.values @ beta
            
            # Calculate R-squared
            ss_res = np.sum((y.values - y_pred) ** 2)
            ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
            
            if ss_tot == 0:
                r_squared = 0.0
            else:
                r_squared = 1.0 - (ss_res / ss_tot)
            
            # Avoid division by zero or negative values due to numerical issues
            if r_squared >= 1.0:
                vif = np.inf
            elif r_squared < 0:
                vif = 1.0  # Should not happen, but handle gracefully
            else:
                vif = 1.0 / (1.0 - r_squared)
                
        except np.linalg.LinAlgError as e:
            logger.warning(f"Singular matrix for column {col}: {e}. Setting VIF to infinity.")
            vif = np.inf
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif = np.nan
        
        vif_data.append({
            "feature": col,
            "vif": vif
        })
        
        if (i + 1) % 10 == 0:
            logger.debug(f"Processed {i + 1}/{len(X_clean.columns)} features")
    
    vif_df = pd.DataFrame(vif_data)
    vif_df = vif_df.sort_values(by="vif", ascending=False)
    
    # Flag high collinearity
    flagged_features = vif_df[vif_df["vif"] > threshold]["feature"].tolist()
    
    logger.info(f"VIF calculation complete. Found {len(flagged_features)} features with VIF > {threshold}")
    if len(flagged_features) > 0:
        logger.warning(f"High collinearity detected in: {', '.join(flagged_features)}")
    
    return vif_df, flagged_features


def run_collinearity_analysis(
    climate_filepath: str,
    trait_filepath: str,
    output_filepath: Optional[str] = None,
    threshold: float = 5.0,
    merge_key: str = "species"
) -> Dict[str, Any]:
    """
    Run the full collinearity analysis pipeline.
    
    1. Load climate and trait data
    2. Merge predictors
    3. Create numeric predictor matrix
    4. Validate matrix
    5. Compute VIF
    6. Flag high collinearity
    7. Optionally save results
    
    Args:
        climate_filepath: Path to climate data CSV.
        trait_filepath: Path to trait data CSV.
        output_filepath: Optional path to save VIF results as CSV.
        threshold: VIF threshold for flagging (default: 5.0).
        merge_key: Key column for merging (default: "species").
        
    Returns:
        Dictionary containing:
            - vif_df: DataFrame with VIF values
            - flagged_features: List of features with VIF > threshold
            - validation: Validation results
            - summary: Summary statistics
    """
    logger.info("Starting collinearity analysis")
    
    # Load data
    climate_df = load_climate_data(climate_filepath)
    trait_df = load_trait_data(trait_filepath)
    
    # Merge
    merged_df = merge_predictors(climate_df, trait_df, key=merge_key)
    
    # Create predictor matrix
    exclude_cols = [merge_key]  # Exclude the merge key from predictors
    X = create_full_predictor_matrix(merged_df, exclude_cols=exclude_cols)
    
    # Validate
    validation = validate_predictor_matrix(X)
    
    # Compute VIF
    vif_df, flagged_features = compute_vif(X, threshold=threshold)
    
    # Prepare summary
    summary = {
        "total_predictors": len(X.columns),
        "flagged_count": len(flagged_features),
        "threshold_used": threshold,
        "high_collinearity_features": flagged_features,
        "max_vif": float(vif_df["vif"].max()) if not vif_df.empty else None,
        "mean_vif": float(vif_df["vif"].mean()) if not vif_df.empty else None
    }
    
    # Save results if output path provided
    if output_filepath:
        logger.info(f"Saving VIF results to {output_filepath}")
        vif_df.to_csv(output_filepath, index=False)
        
    result = {
        "vif_df": vif_df,
        "flagged_features": flagged_features,
        "validation": validation,
        "summary": summary
    }
    
    logger.info("Collinearity analysis complete")
    return result