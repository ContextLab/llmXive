"""
Data preprocessing module for herbivore resistance prediction.

Implements variance filtering, KNN imputation, PCA, and genotype-stratified splitting.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import KNNImputer
from sklearn.decomposition import PCA
from sklearn.model_selection import GroupShuffleSplit
from config import RANDOM_SEED, DATA_ROOT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_interim_dataset():
    """Load harmonized dataset from data/interim/harmonized.csv."""
    path = os.path.join(DATA_ROOT, 'interim', 'harmonized.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Harmonized dataset not found: {path}")
    
    logger.info(f"Loading harmonized dataset from {path}")
    return pd.read_csv(path)


def filter_low_variance_metabolites(df, threshold=0.001):
    """
    Filter out metabolites with variance below threshold.
    
    Args:
        df: DataFrame with metabolite columns
        threshold: Minimum variance threshold (default: 0.001)
    
    Returns:
        DataFrame with low-variance metabolites removed
    """
    # Identify metabolite columns
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        logger.warning("No metabolite columns found")
        return df
    
    # Calculate variance for each metabolite
    variances = df[metabolite_cols].var()
    
    # Filter columns with variance >= threshold
    high_var_cols = variances[variances >= threshold].index.tolist()
    
    logger.info(f"Filtered {len(metabolite_cols) - len(high_var_cols)} low-variance metabolites")
    
    # Keep non-metabolite columns and high-variance metabolites
    non_metabolite_cols = [col for col in df.columns if not col.startswith('metabolite_')]
    result_cols = non_metabolite_cols + high_var_cols
    
    return df[result_cols]


def apply_knn_imputation(df, k=5):
    """
    Apply k-Nearest Neighbors imputation for missing values.
    
    Args:
        df: DataFrame with missing values
        k: Number of neighbors for imputation (default: 5)
    
    Returns:
        DataFrame with imputed values and imputation_flag column
    """
    # Identify metabolite columns
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        logger.warning("No metabolite columns found for imputation")
        return df
    
    # Track which rows had missing values
    has_missing = df[metabolite_cols].isnull().any(axis=1)
    
    # Apply KNN imputation
    imputer = KNNImputer(n_neighbors=k)
    imputed_values = imputer.fit_transform(df[metabolite_cols])
    
    # Update dataframe with imputed values
    df_imputed = df.copy()
    df_imputed[metabolite_cols] = imputed_values
    
    # Add imputation flag
    df_imputed['imputation_flag'] = has_missing.astype(int)
    
    logger.info(f"Applied KNN imputation (k={k}) to {has_missing.sum()} samples")
    
    return df_imputed


def apply_pca_if_needed(df, threshold_variance=0.95):
    """
    Apply PCA if features > samples, retaining enough components to explain threshold_variance.
    
    Args:
        df: DataFrame with metabolite features
        threshold_variance: Cumulative variance threshold (default: 0.95)
    
    Returns:
        DataFrame with PCA-reduced features
    """
    # Identify metabolite columns
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        logger.warning("No metabolite columns found for PCA")
        return df
    
    n_samples = len(df)
    n_features = len(metabolite_cols)
    
    if n_features <= n_samples:
        logger.info(f"Features ({n_features}) <= Samples ({n_samples}), skipping PCA")
        return df
    
    logger.info(f"Features ({n_features}) > Samples ({n_samples}), applying PCA")
    
    # Extract metabolite data
    metabolite_data = df[metabolite_cols].values
    
    # Apply PCA
    pca = PCA(n_components=threshold_variance, random_state=RANDOM_SEED)
    pca_result = pca.fit_transform(metabolite_data)
    
    logger.info(f"PCA reduced {n_features} features to {pca_result.shape[1]} components (variance explained: {sum(pca.explained_variance_ratio_):.4f})")
    
    # Create new column names
    pca_cols = [f'pca_component_{i}' for i in range(pca_result.shape[1])]
    
    # Create DataFrame with PCA results
    pca_df = pd.DataFrame(pca_result, columns=pca_cols, index=df.index)
    
    # Keep non-metabolite columns
    non_metabolite_cols = [col for col in df.columns if not col.startswith('metabolite_')]
    
    # Combine
    result = pd.concat([df[non_metabolite_cols], pca_df], axis=1)
    
    return result


def genotype_stratified_split(df, test_size=0.2):
    """
    Perform genotype-stratified train/test split to prevent leakage.
    
    Args:
        df: DataFrame with genotype_id column
        test_size: Proportion of data for testing (default: 0.2)
    
    Returns:
        Dictionary with train_indices and test_indices
    """
    if 'genotype_id' not in df.columns:
        raise ValueError("DataFrame must contain 'genotype_id' column for stratified splitting")
    
    groups = df['genotype_id'].values
    n_samples = len(df)
    
    # Use GroupShuffleSplit to ensure no genotype appears in both train and test
    splitter = GroupShuffleSplit(test_size=test_size, n_splits=1, random_state=RANDOM_SEED)
    
    for train_idx, test_idx in splitter.split(df, groups=groups):
        return {
            'train_indices': train_idx.tolist(),
            'test_indices': test_idx.tolist()
        }
    
    raise RuntimeError("Failed to generate train/test split")


def save_split_indices(split_indices, output_path=None):
    """Save split indices to JSON file."""
    if output_path is None:
        output_path = os.path.join(DATA_ROOT, 'interim', 'split_indices.json')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(split_indices, f, indent=2)
    
    logger.info(f"Split indices saved to {output_path}")
    return output_path


def save_pca_rereduced_data(df, output_path=None):
    """Save PCA-reduced data to CSV file."""
    if output_path is None:
        output_path = os.path.join(DATA_ROOT, 'processed', 'pca_reduced.csv')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"PCA-reduced data saved to {output_path}")
    return output_path


def main():
    """
    Main preprocessing pipeline.
    
    Workflow:
    1. Load harmonized dataset
    2. Filter low-variance metabolites
    3. Apply KNN imputation
    4. Apply PCA if needed
    5. Perform genotype-stratified split
    6. Save split indices and PCA-reduced data
    """
    logger.info("Starting preprocessing pipeline")
    
    # Load data
    df = load_interim_dataset()
    logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")
    
    # Filter low variance
    df = filter_low_variance_metabolites(df, threshold=0.001)
    logger.info(f"After variance filtering: {len(df.columns)} columns")
    
    # Apply KNN imputation
    df = apply_knn_imputation(df, k=5)
    logger.info(f"After imputation: {df['imputation_flag'].sum()} samples imputed")
    
    # Apply PCA if needed
    df_processed = apply_pca_if_needed(df)
    
    # Save PCA-reduced data
    pca_path = save_pca_rereduced_data(df_processed)
    
    # Perform genotype-stratified split
    split_indices = genotype_stratified_split(df_processed)
    save_split_indices(split_indices)
    
    logger.info("Preprocessing pipeline completed successfully")
    
    return df_processed, split_indices


if __name__ == '__main__':
    main()
