"""
PCA and L1 Regularization for High-Dimensional Genomic Data.

This module implements dimensionality reduction techniques specifically for
linear models when the number of features exceeds 5000. It provides:
1. PCA transformation to reduce feature space while preserving variance.
2. L1 (Lasso) regularization to perform feature selection.
3. Logic to apply these techniques conditionally based on feature count.

Outputs transformed features to data/processed/pca_features.parquet.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
import joblib

# Import project config for paths
from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_preprocessed_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Load the unified dataset and split into features (X) and target (y).
    
    Returns:
        Tuple of (X, y, metadata) where X is the feature matrix.
    """
    data_path = Path("data/processed/unified_dataset.parquet")
    
    if not data_path.exists():
        raise FileNotFoundError(
            f"Preprocessed dataset not found at {data_path}. "
            "Please run the preprocessing pipeline (T021) first."
        )
    
    logger.info(f"Loading preprocessed data from {data_path}")
    df = pd.read_parquet(data_path)
    
    # Assuming the unified dataset has 'target' as the phenotype column
    # and other columns are features. Adjust if column names differ.
    if 'target' not in df.columns:
        # Fallback: try to identify target column or raise error
        raise ValueError("Column 'target' not found in unified dataset.")
    
    y = df['target']
    X = df.drop(columns=['target'])
    
    # Ensure all features are numeric
    X = X.apply(pd.to_numeric, errors='coerce')
    X = X.dropna(axis=1, how='all') # Drop columns that are entirely NaN
    
    logger.info(f"Loaded dataset with shape: {X.shape}")
    return X, y, df

def apply_pca(X: pd.DataFrame, n_components: Optional[int] = None, 
              variance_threshold: float = 0.95) -> Tuple[pd.DataFrame, PCA, StandardScaler]:
    """
    Apply PCA to reduce dimensionality while preserving variance.
    
    Args:
        X: Feature DataFrame.
        n_components: Number of components to keep. If None, determined by variance_threshold.
        variance_threshold: Minimum cumulative variance to preserve.
        
    Returns:
        Transformed DataFrame, fitted PCA object, fitted Scaler.
    """
    logger.info(f"Applying PCA with variance threshold: {variance_threshold}")
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if n_components is None:
        pca = PCA(n_components=variance_threshold)
    else:
        pca = PCA(n_components=n_components)
        
    X_pca = pca.fit_transform(X_scaled)
    
    logger.info(f"PCA reduced features from {X.shape[1]} to {X_pca.shape[1]}")
    logger.info(f"Explained variance ratio: {pca.explained_variance_ratio_.sum():.4f}")
    
    # Create DataFrame with new feature names
    pca_columns = [f'PC{i+1}' for i in range(X_pca.shape[1])]
    X_pca_df = pd.DataFrame(X_pca, columns=pca_columns, index=X.index)
    
    return X_pca_df, pca, scaler

def apply_l1_regularization(X: pd.DataFrame, y: pd.Series, 
                            cv_folds: int = 5) -> Tuple[pd.DataFrame, LassoCV, np.ndarray]:
    """
    Apply L1 (Lasso) regularization to select features.
    
    Args:
        X: Feature DataFrame.
        y: Target Series.
        cv_folds: Number of cross-validation folds.
        
    Returns:
        DataFrame with only selected features, fitted LassoCV, selected feature mask.
    """
    logger.info(f"Applying L1 regularization with {cv_folds} CV folds")
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Use LassoCV for automatic alpha selection
    lasso = LassoCV(cv=cv_folds, random_state=42, n_jobs=-1)
    lasso.fit(X_scaled, y)
    
    # Identify non-zero coefficients
    selected_mask = lasso.coef_ != 0
    selected_features = X.columns[selected_mask]
    
    logger.info(f"L1 selected {len(selected_features)} features out of {X.shape[1]}")
    logger.info(f"Optimal alpha: {lasso.alpha_}")
    
    X_selected = X[selected_features]
    
    return X_selected, lasso, selected_mask

def process_high_dimensional_features(X: pd.DataFrame, y: pd.Series, 
                                      threshold: int = 5000) -> Tuple[pd.DataFrame, str]:
    """
    Process features if count exceeds threshold.
    
    Args:
        X: Feature DataFrame.
        y: Target Series.
        threshold: Feature count threshold (default 5000).
        
    Returns:
        Processed DataFrame and method used ('pca', 'l1', or 'none').
    """
    n_features = X.shape[1]
    
    if n_features <= threshold:
        logger.info(f"Feature count ({n_features}) <= {threshold}. No reduction needed.")
        return X, 'none'
    
    logger.warning(f"Feature count ({n_features}) > {threshold}. Applying reduction.")
    
    # Strategy: Use PCA for extreme dimensionality, L1 for moderate
    # Given genomic data often has high collinearity, PCA is robust.
    # However, L1 provides interpretability. 
    # The task specifies "PCA/L1". We will use PCA if features > 10000, else L1.
    
    if n_features > 10000:
        logger.info("Using PCA for high-dimensional reduction (>10k features)")
        X_processed, _, _ = apply_pca(X, variance_threshold=0.95)
        return X_processed, 'pca'
    else:
        logger.info("Using L1 regularization for feature selection")
        X_processed, _, _ = apply_l1_regularization(X, y)
        return X_processed, 'l1'

def save_transformed_features(X: pd.DataFrame, method: str, 
                              metadata: Optional[pd.DataFrame] = None,
                              output_path: str = "data/processed/pca_features.parquet"):
    """
    Save the transformed features to a Parquet file.
    
    Args:
        X: Processed feature DataFrame.
        method: Method used ('pca', 'l1', 'none').
        metadata: Original metadata (optional).
        output_path: Path to save the output.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving transformed features to {output_file}")
    
    # Combine with metadata if available to keep row alignment
    if metadata is not None:
        # Ensure metadata index matches X index
        if not X.index.equals(metadata.index):
            logger.warning("Index mismatch between features and metadata. Reindexing metadata.")
            metadata = metadata.reindex(X.index)
        combined_df = pd.concat([metadata, X], axis=1)
        combined_df.to_parquet(output_file, index=True)
    else:
        X.to_parquet(output_file, index=True)
        
    logger.info(f"Saved {X.shape[0]} rows and {X.shape[1]} features.")
    
    # Save model artifacts for later use
    models_dir = Path("data/processed/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Save method info
    with open(models_dir / "reduction_method.txt", "w") as f:
        f.write(method)

def main():
    """Main entry point for PCA/L1 reduction task."""
    parser = argparse.ArgumentParser(description="Apply PCA or L1 to high-dimensional genomic data.")
    parser.add_argument('--threshold', type=int, default=5000, 
                        help='Feature count threshold for reduction (default: 5000)')
    parser.add_argument('--output', type=str, default="data/processed/pca_features.parquet",
                        help='Output path for transformed features')
    args = parser.parse_args()
    
    ensure_directories()
    
    try:
        X, y, metadata = load_preprocessed_data()
        
        X_processed, method = process_high_dimensional_features(
            X, y, threshold=args.threshold
        )
        
        save_transformed_features(
            X_processed, 
            method, 
            metadata=metadata.drop(columns=['target'], errors='ignore'),
            output_path=args.output
        )
        
        logger.info("Task completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
