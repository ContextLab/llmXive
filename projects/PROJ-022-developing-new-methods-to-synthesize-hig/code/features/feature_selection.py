"""
Feature Selection Module for Membrane Synthesis Pipeline.

Implements Recursive Feature Elimination (RFE) if feature count > 15,
otherwise performs Principal Component Analysis (PCA) as per FR-011.
"""
import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any, Optional

from sklearn.feature_selection import RFE
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Import local utilities
from utils.logging_config import get_logger
from utils.errors import DataInsufficientError

# Configure logger
logger = get_logger(__name__)

# Constants
FEATURE_THRESHOLD = 15
RANDOM_STATE = 42
OUTPUT_PATH = "data/processed/feature_selection_report.json"
SELECTED_FEATURES_PATH = "data/processed/selected_features.txt"

def perform_rfe(X: np.ndarray, y: np.ndarray, n_features_to_select: int) -> Tuple[np.ndarray, List[str]]:
    """
    Perform Recursive Feature Elimination using a Random Forest estimator.

    Args:
        X: Feature matrix (numpy array)
        y: Target variable (numpy array)
        n_features_to_select: Number of features to select

    Returns:
        Tuple of (selected feature matrix, list of selected feature names)
    """
    logger.info(f"Performing RFE to select top {n_features_to_select} features from {X.shape[1]} available.")

    # Use a simple Random Forest as the estimator for RFE
    estimator = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    rfe = RFE(
        estimator=estimator,
        n_features_to_select=n_features_to_select,
        step=1
    )

    rfe.fit(X, y)

    # Get the boolean mask of selected features
    selected_mask = rfe.support_

    return selected_mask

def perform_pca(X: np.ndarray, y: np.ndarray, n_components: float = 0.95) -> Tuple[np.ndarray, List[str]]:
    """
    Perform Principal Component Analysis to reduce dimensionality.
    Retains enough components to explain 95% of the variance.

    Args:
        X: Feature matrix (numpy array)
        y: Target variable (numpy array) - used for scaling context, though PCA is unsupervised
        n_components: Variance threshold (default 0.95)

    Returns:
        Tuple of (transformed feature matrix, list of component names)
    """
    logger.info(f"Performing PCA to retain {n_components*100}% variance.")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=n_components, random_state=RANDOM_STATE)
    X_pca = pca.fit_transform(X_scaled)

    logger.info(f"PCA reduced features from {X.shape[1]} to {X_pca.shape[1]} components.")
    logger.info(f"Explained variance ratio: {pca.explained_variance_ratio_}")

    # Return component names as 'PC1', 'PC2', etc.
    component_names = [f"PC{i+1}" for i in range(X_pca.shape[1])]

    return X_pca, component_names

def select_features(df: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main entry point for feature selection.
    Implements FR-011: RFE if features > 15, else PCA.

    Args:
        df: Input dataframe containing features and target
        target_column: Name of the target column (e.g., 'permeability_barrer')

    Returns:
        Tuple of (processed dataframe with selected features, selection metadata)
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataframe.")

    # Separate features and target
    # Filter for numeric columns only for feature selection
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_column in numeric_cols:
        numeric_cols.remove(target_column)

    if len(numeric_cols) == 0:
        raise DataInsufficientError("No numeric feature columns found for selection.")

    X = df[numeric_cols].values
    y = df[target_column].values
    feature_names = numeric_cols

    # Remove rows with NaN in features or target before selection
    valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    if not np.all(valid_mask):
        logger.warning(f"Removing {np.sum(~valid_mask)} rows with NaN values before feature selection.")
        X = X[valid_mask]
        y = y[valid_mask]
        # Re-align feature names list isn't needed as we use indices, but we need to know which rows were kept
        # However, we need to return a dataframe, so we must handle the original index
        original_index = df.index[valid_mask]
        df_clean = df.loc[original_index].copy()
    else:
        df_clean = df.copy()

    X = df_clean[numeric_cols].values
    y = df_clean[target_column].values
    feature_names = numeric_cols

    num_features = len(feature_names)
    metadata = {
        "original_feature_count": num_features,
        "method": "",
        "final_feature_count": 0,
        "selected_features": [],
        "variance_explained": None
    }

    if num_features > FEATURE_THRESHOLD:
        logger.info(f"Feature count ({num_features}) > {FEATURE_THRESHOLD}. Using RFE.")
        metadata["method"] = "RFE"
        
        # Select top half or a fixed number, but at least 1
        n_select = max(1, int(num_features * 0.5))
        # Ensure we don't try to select more than available
        n_select = min(n_select, num_features)

        selected_mask = perform_rfe(X, y, n_select)
        selected_indices = [i for i, m in enumerate(selected_mask) if m]
        selected_features = [feature_names[i] for i in selected_indices]

        result_df = df_clean[selected_features].copy()
        
        metadata["selected_features"] = selected_features
        metadata["final_feature_count"] = len(selected_features)

    else:
        logger.info(f"Feature count ({num_features}) <= {FEATURE_THRESHOLD}. Using PCA.")
        metadata["method"] = "PCA"

        # Perform PCA
        X_pca, component_names = perform_pca(X, y, n_components=0.95)
        
        # Create a new dataframe with PCA components
        pca_df = pd.DataFrame(X_pca, columns=component_names, index=df_clean.index)
        
        # Merge back with non-numeric columns if any (though usually we just want the features)
        # For simplicity in this pipeline, we return the PCA components as the feature set
        result_df = pca_df

        metadata["selected_features"] = component_names
        metadata["final_feature_count"] = len(component_names)
        # Estimate variance explained from the PCA logic (we'd need to capture the PCA object to get exact ratio here, 
        # but for the report we can note the method used)
        metadata["variance_explained"] = "0.95 (threshold)"

    return result_df, metadata

def save_metadata(metadata: Dict[str, Any], output_path: str):
    """Saves the feature selection metadata to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Feature selection metadata saved to {output_path}")

def save_selected_features_list(feature_list: List[str], output_path: str):
    """Saves the list of selected feature names to a text file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        for feature in feature_list:
            f.write(f"{feature}\n")
    logger.info(f"Selected features list saved to {output_path}")

def main():
    """
    Main execution function.
    Expects data/processed/standardized_polymers.csv to exist (from T016).
    Produces data/processed/feature_selection_report.json and updates the feature matrix.
    """
    input_path = "data/processed/standardized_polymers.csv"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. Please run ingestion pipeline first.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # Identify the target variable. Based on T014/T016 context, it's likely 'permeability_barrer' or similar.
    # We look for a column that represents performance.
    target_candidates = ['permeability_barrer', 'permeability', 'performance_score']
    target_col = None
    for candidate in target_candidates:
        if candidate in df.columns:
            target_col = candidate
            break
    
    if not target_col:
        # Fallback: try to find any column with 'permeability' in name
        cols = [c for c in df.columns if 'permeability' in c.lower()]
        if cols:
            target_col = cols[0]
        else:
            logger.error("Could not identify target variable (permeability) in dataset.")
            sys.exit(1)

    logger.info(f"Using '{target_col}' as target variable for feature selection.")

    result_df, metadata = select_features(df, target_col)

    # Save metadata
    save_metadata(metadata, OUTPUT_PATH)
    
    # Save list of selected features
    if metadata["selected_features"]:
        save_selected_features_list(metadata["selected_features"], SELECTED_FEATURES_PATH)

    # Save the processed feature matrix (overwriting or creating a new one)
    # The task asks to "Implement feature selection", usually implying the output is the selected features.
    # We save this as the new feature matrix for modeling.
    output_matrix_path = "data/processed/feature_matrix_selected.csv"
    result_df.to_csv(output_matrix_path, index=False)
    logger.info(f"Selected feature matrix saved to {output_matrix_path}")

    return result_df, metadata

if __name__ == "__main__":
    main()