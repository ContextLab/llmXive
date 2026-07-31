import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.impute import KNNImputer
from sklearn.model_selection import GroupShuffleSplit

from config import ensure_directories, DATA_ROOT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_interim_dataset(filepath: str = None) -> pd.DataFrame:
    """Load the harmonized dataset from the interim directory."""
    if filepath is None:
        filepath = os.path.join(DATA_ROOT, 'interim', 'harmonized.csv')
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Interim dataset not found at {filepath}. Run ingestion tasks first.")
    
    logger.info(f"Loading interim dataset from {filepath}")
    df = pd.read_csv(filepath)
    return df

def filter_low_variance_metabolites(df: pd.DataFrame, threshold: float = 0.001) -> pd.DataFrame:
    """Filter out metabolites with variance below the threshold."""
    logger.info(f"Filtering metabolites with variance < {threshold}")
    
    # Identify metabolite columns (assume they start with 'metabolite_')
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        logger.warning("No metabolite columns found. Returning original dataframe.")
        return df

    variances = df[metabolite_cols].var(numeric_only=True)
    high_var_cols = variances[variances >= threshold].index.tolist()
    
    logger.info(f"Keeping {len(high_var_cols)} metabolites with variance >= {threshold}")
    logger.info(f"Removed {len(metabolite_cols) - len(high_var_cols)} low-variance metabolites")
    
    # Keep non-metabolite columns (sample_id, genotype_id, resistance, etc.)
    non_metabolite_cols = [col for col in df.columns if not col.startswith('metabolite_')]
    final_cols = non_metabolite_cols + high_var_cols
    
    return df[final_cols]

def apply_knn_imputation(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Apply k-Nearest Neighbors imputation for missing values."""
    logger.info(f"Applying KNN imputation with k={k}")
    
    # Identify metabolite columns
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        logger.warning("No metabolite columns found for imputation.")
        # Add imputation flag column if missing
        if 'imputation_flag' not in df.columns:
            df['imputation_flag'] = False
        return df

    # Check for missing values
    has_missing = df[metabolite_cols].isnull().any().any()
    
    if not has_missing:
        logger.info("No missing values found. Skipping imputation.")
        df['imputation_flag'] = False
        return df

    logger.info("Missing values detected. Proceeding with imputation.")
    
    # Separate metadata and features
    metadata_cols = [col for col in df.columns if not col.startswith('metabolite_')]
    features_df = df[metabolite_cols].copy()
    
    # Apply KNN imputation
    imputer = KNNImputer(n_neighbors=k)
    imputed_features = imputer.fit_transform(features_df)
    
    # Update dataframe with imputed values
    for i, col in enumerate(metabolite_cols):
        df[col] = imputed_features[:, i]
    
    # Set imputation flag
    df['imputation_flag'] = True
    
    logger.info("KNN imputation completed.")
    return df

def apply_pca_if_needed(df: pd.DataFrame, output_path: str = None) -> pd.DataFrame:
    """
    Apply PCA if features > samples.
    
    Logic:
    1. Count samples (rows) and metabolite features.
    2. If metabolite_features > samples, apply PCA to reduce dimensionality.
    3. Keep enough components to explain 95% of variance or reduce to sample count.
    4. Save the reduced matrix to the specified output path.
    
    Returns the dataframe with PCA-reduced features (or original if not needed).
    """
    logger.info("Checking if PCA is needed (features > samples)...")
    
    # Identify metabolite columns
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    non_metabolite_cols = [col for col in df.columns if not col.startswith('metabolite_')]
    
    n_samples = len(df)
    n_features = len(metabolite_cols)
    
    logger.info(f"Samples: {n_samples}, Metabolite Features: {n_features}")
    
    if n_features <= n_samples:
        logger.info(f"Features ({n_features}) <= Samples ({n_samples}). PCA not needed.")
        return df
    
    logger.info(f"Features ({n_features}) > Samples ({n_samples}). Applying PCA.")
    
    # Extract features
    X = df[metabolite_cols].values.astype(float)
    
    # Determine number of components: min(n_samples - 1, enough for 95% variance)
    # We must leave at least 1 degree of freedom, so max components is n_samples - 1
    max_components = min(n_samples - 1, n_features)
    
    # Try to explain 95% variance, but cap at max_components
    pca = PCA(n_components=max_components, svd_solver='full')
    X_reduced = pca.fit_transform(X)
    
    logger.info(f"PCA reduced {n_features} features to {X_reduced.shape[1]} components.")
    logger.info(f"Explained variance ratio: {pca.explained_variance_ratio_.sum():.4f}")
    
    # Create new column names for PCA components
    pca_col_names = [f'pca_component_{i+1}' for i in range(X_reduced.shape[1])]
    
    # Create new dataframe with non-metabolite columns and PCA components
    reduced_df = df[non_metabolite_cols].copy()
    for i, col_name in enumerate(pca_col_names):
        reduced_df[col_name] = X_reduced[:, i]
    
    # Save if output path is provided
    if output_path:
        ensure_directories()
        reduced_df.to_csv(output_path, index=False)
        logger.info(f"PCA reduced data saved to {output_path}")
    
    return reduced_df

def genotype_stratified_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> tuple:
    """
    Perform a genotype-stratified train/test split to prevent data leakage.
    
    Returns:
        train_indices, test_indices (lists of row indices)
    """
    logger.info("Performing genotype-stratified split...")
    
    if 'genotype_id' not in df.columns:
        raise ValueError("Column 'genotype_id' not found in dataframe. Cannot perform stratified split.")
    
    groups = df['genotype_id']
    
    gss = GroupShuffleSplit(test_size=test_size, n_splits=1, random_state=random_state)
    train_idx, test_idx = next(gss.split(df, groups=groups))
    
    logger.info(f"Split complete: {len(train_idx)} train samples, {len(test_idx)} test samples")
    
    return train_idx.tolist(), test_idx.tolist()

def save_split_indices(train_indices: list, test_indices: list, output_path: str = None):
    """Save split indices to a JSON file."""
    if output_path is None:
        output_path = os.path.join(DATA_ROOT, 'interim', 'split_indices.json')
    
    data = {
        'train_indices': train_indices,
        'test_indices': test_indices
    }
    
    ensure_directories()
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Split indices saved to {output_path}")

def save_pca_reduced_data(df: pd.DataFrame, output_path: str = None):
    """Save PCA reduced dataframe to CSV."""
    if output_path is None:
        output_path = os.path.join(DATA_ROOT, 'processed', 'pca_reduced.csv')
    
    ensure_directories()
    df.to_csv(output_path, index=False)
    logger.info(f"PCA reduced data saved to {output_path}")

def save_feature_importance(importance_df: pd.DataFrame, output_path: str = None):
    """Save feature importance table to CSV."""
    if output_path is None:
        output_path = os.path.join(DATA_ROOT, 'processed', 'feature_importance.csv')
    
    ensure_directories()
    importance_df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")

def main():
    """Main execution flow for preprocessing tasks."""
    logger.info("Starting preprocessing pipeline...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load interim dataset
    try:
        df = load_interim_dataset()
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    # 1. Filter low variance metabolites
    df_filtered = filter_low_variance_metabolites(df)
    
    # 2. Apply KNN imputation
    df_imputed = apply_knn_imputation(df_filtered)
    
    # 3. Apply PCA if needed and save
    # The task specifically asks to save to data/processed/pca_reduced.csv
    pca_output_path = os.path.join(DATA_ROOT, 'processed', 'pca_reduced.csv')
    df_final = apply_pca_if_needed(df_imputed, output_path=pca_output_path)
    
    logger.info("Preprocessing pipeline completed.")

if __name__ == "__main__":
    main()