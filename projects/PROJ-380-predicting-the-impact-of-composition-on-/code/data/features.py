import os
import sys
import logging
import math
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from sibling modules as per API surface
from utils.logging_config import get_logger
from utils.provenance import record_artifact

# Third-party imports
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.decomposition import PCA

logger = get_logger(__name__)

VIF_THRESHOLD = 5.0
PCA_THRESHOLD_COUNT = 2  # If more than this many features exceed VIF threshold, apply PCA

def calculate_vif(X: np.ndarray, feature_names: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        feature_names: List of feature names corresponding to columns in X
        
    Returns:
        DataFrame with feature names and their VIF scores
    """
    if X.shape[1] == 0:
        return pd.DataFrame(columns=['feature', 'vif'])
        
    vif_data = []
    
    for i in range(X.shape[1]):
        # Create a temporary DataFrame for the regression
        y = X[:, i]
        X_temp = np.delete(X, i, axis=1)
        
        # Handle case where only one feature remains
        if X_temp.shape[1] == 0:
            vif = float('inf')
        else:
            # Add intercept
            X_with_intercept = np.column_stack([np.ones(X_temp.shape[0]), X_temp])
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X_with_intercept, y)
            
            # Calculate R-squared
            r_squared = model.score(X_with_intercept, y)
            
            # Calculate VIF
            if r_squared == 1.0:
                vif = float('inf')
            else:
                vif = 1 / (1 - r_squared)
        
        vif_data.append({
            'feature': feature_names[i],
            'vif': vif
        })
        
    return pd.DataFrame(vif_data)

def iterative_vif_selection(X: np.ndarray, y: np.ndarray, feature_names: List[str], 
                            threshold: float = VIF_THRESHOLD) -> Tuple[np.ndarray, List[str], List[str]]:
    """
    Iteratively remove features with highest VIF until all VIFs are below threshold.
    
    Args:
        X: Feature matrix
        y: Target variable
        feature_names: List of feature names
        threshold: VIF threshold for removal
        
    Returns:
        Tuple of (reduced X, reduced feature names, removed feature names)
    """
    X_current = X.copy()
    names_current = feature_names.copy()
    removed_names = []
    
    iteration = 0
    max_iterations = len(feature_names)
    
    while iteration < max_iterations:
        vif_df = calculate_vif(X_current, names_current)
        
        # Check if any VIF exceeds threshold
        high_vif = vif_df[vif_df['vif'] > threshold]
        
        if high_vif.empty:
            logger.info(f"VIF selection complete. All features below threshold {threshold}.")
            break
        
        # Find feature with highest VIF
        max_vif_idx = high_vif['vif'].idxmax()
        feature_to_remove = vif_df.loc[max_vif_idx, 'feature']
        remove_idx = names_current.index(feature_to_remove)
        
        logger.warning(f"Iteration {iteration}: Removing '{feature_to_remove}' with VIF={vif_df.loc[max_vif_idx, 'vif']:.2f}")
        
        # Remove feature
        X_current = np.delete(X_current, remove_idx, axis=1)
        names_current.pop(remove_idx)
        removed_names.append(feature_to_remove)
        
        iteration += 1
        
        # Safety check
        if len(names_current) == 1:
            logger.warning("Only one feature remaining, stopping VIF selection.")
            break
    
    return X_current, names_current, removed_names

def apply_pca(X: np.ndarray, feature_names: List[str], target_variance: float = 0.95) -> Tuple[np.ndarray, List[str], PCA]:
    """
    Apply PCA to reduce dimensionality while preserving variance.
    
    Args:
        X: Feature matrix
        feature_names: Original feature names
        target_variance: Cumulative variance to preserve
        
    Returns:
        Tuple of (reduced X, new feature names, PCA model)
    """
    pca = PCA()
    pca.fit(X)
    
    # Find number of components to reach target variance
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    n_components = np.argmax(cumulative_variance >= target_variance) + 1
    
    # If target variance is not reachable with any components, use all
    if n_components >= X.shape[1]:
        n_components = X.shape[1]
        
    logger.info(f"PCA: Reducing {X.shape[1]} features to {n_components} components (target variance: {target_variance})")
    
    # Transform data
    X_pca = pca.transform(X)
    
    # Create new feature names
    new_names = [f"PC{i+1}" for i in range(n_components)]
    
    return X_pca[:, :n_components], new_names, pca

def handle_collinearity(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, List[str], str]:
    """
    Handle multicollinearity by iterative VIF removal or PCA.
    
    Logic:
    1. Iteratively remove features with highest VIF until all < threshold
    2. If >2 features exceed threshold initially, apply PCA instead
    
    Args:
        X: Feature matrix
        y: Target variable
        feature_names: List of feature names
        
    Returns:
        Tuple of (processed X, processed feature names, method_used)
    """
    initial_vif_df = calculate_vif(X, feature_names)
    high_vif_count = (initial_vif_df['vif'] > VIF_THRESHOLD).sum()
    
    logger.info(f"Initial VIF analysis: {high_vif_count} features exceed threshold {VIF_THRESHOLD}")
    
    if high_vif_count > PCA_THRESHOLD_COUNT:
        logger.info(f"More than {PCA_THRESHOLD_COUNT} features exceed VIF threshold. Applying PCA.")
        X_processed, names_processed, _ = apply_pca(X, feature_names)
        return X_processed, names_processed, "pca"
    else:
        logger.info(f"Applying iterative VIF removal (<= {PCA_THRESHOLD_COUNT} features exceed threshold).")
        X_processed, names_processed, removed = iterative_vif_selection(X, y, feature_names)
        if removed:
            return X_processed, names_processed, "iterative_vif"
        else:
            return X_processed, names_processed, "none"

def add_descriptors_to_dataframe(df: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
    """
    Ensure all feature columns exist in the dataframe and add descriptor columns if needed.
    
    Args:
        df: Input dataframe
        feature_names: List of expected feature names
        
    Returns:
        Updated dataframe with all feature columns
    """
    # Ensure all feature columns exist
    for name in feature_names:
        if name not in df.columns:
            logger.warning(f"Feature column '{name}' not found in dataframe. Adding with NaN.")
            df[name] = np.nan
    
    return df

def process_features(input_path: str, output_path: str) -> None:
    """
    Main function to process features and handle collinearity.
    
    Args:
        input_path: Path to input CSV with descriptors
        output_path: Path to output CSV with processed features
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Identify feature columns (exclude target and metadata)
    exclude_cols = ['shear_modulus_GPa', 'material_id', 'formula', 'alloy_family', 'source']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        logger.error("No feature columns found in input data.")
        raise ValueError("No feature columns found")
    
    logger.info(f"Found {len(feature_cols)} feature columns: {feature_cols}")
    
    # Convert to numpy arrays
    X = df[feature_cols].values
    y = df['shear_modulus_GPa'].values if 'shear_modulus_GPa' in df.columns else None
    
    # Handle missing values in features
    if np.any(np.isnan(X)):
        logger.warning("Missing values detected in features. Dropping rows with NaN.")
        valid_mask = ~np.any(np.isnan(X), axis=1)
        if y is not None:
            valid_mask &= ~np.isnan(y)
        X = X[valid_mask]
        if y is not None:
            y = y[valid_mask]
        df = df[valid_mask]
        feature_cols = [col for col in feature_cols if col in df.columns]
    
    # Handle collinearity
    X_processed, processed_names, method = handle_collinearity(X, y, feature_cols)
    
    logger.info(f"Collinearity handling method: {method}")
    logger.info(f"Feature count: {len(feature_cols)} -> {len(processed_names)}")
    
    # Update dataframe with processed features
    if method == "pca":
        # For PCA, we create new columns
        for i, name in enumerate(processed_names):
            df[name] = X_processed[:, i]
        # Remove original feature columns
        df = df.drop(columns=feature_cols)
    else:
        # For iterative VIF, keep only selected features
        df = df[processed_names + [col for col in df.columns if col not in feature_cols]]
    
    # Save output
    logger.info(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Record provenance
    record_artifact(output_path, "processed_features", "VIF collinearity handling")
    
    logger.info("Feature processing complete.")

def main():
    """Main entry point for feature processing script."""
    # Default paths
    input_path = "data/processed/bmg_descriptors.csv"
    output_path = "data/processed/bmg_features_processed.csv"
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    # Ensure directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    process_features(input_path, output_path)

if __name__ == "__main__":
    main()