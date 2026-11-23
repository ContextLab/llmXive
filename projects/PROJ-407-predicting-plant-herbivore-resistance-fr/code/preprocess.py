import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import GroupShuffleSplit
from config import DATA_ROOT, RANDOM_SEED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_interim_dataset(filepath=None):
    """Load the harmonized dataset from the interim directory."""
    if filepath is None:
        filepath = os.path.join(DATA_ROOT, 'interim', 'harmonized.csv')
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Interim dataset not found at {filepath}")
    
    logger.info(f"Loading interim dataset from {filepath}")
    return pd.read_csv(filepath)

def filter_low_variance_metabolites(df, threshold=0.001):
    """Filter out metabolites with variance below a threshold."""
    # Assume metabolite columns start with 'metabolite_'
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        logger.warning("No metabolite columns found starting with 'metabolite_'")
        return df, []
    
    variances = df[metabolite_cols].var()
    low_var_cols = variances[variances < threshold].index.tolist()
    filtered_df = df.drop(columns=low_var_cols)
    
    logger.info(f"Filtered {len(low_var_cols)} low variance metabolites")
    return filtered_df, low_var_cols

def apply_knn_imputation(df, k=5):
    """Apply k-NN imputation for missing values."""
    from sklearn.impute import KNNImputer
    
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        logger.warning("No metabolite columns found for imputation")
        return df, False
    
    X = df[metabolite_cols].values
    imputer = KNNImputer(n_neighbors=k)
    X_imputed = imputer.fit_transform(X)
    
    df_imputed = df.copy()
    df_imputed[metabolite_cols] = X_imputed
    
    # Set imputation flag if any missing values were present
    imputation_flag = df[metabolite_cols].isnull().any().any()
    
    logger.info(f"Applied k-NN imputation (k={k})")
    return df_imputed, imputation_flag

def apply_pca_if_needed(df, variance_threshold=0.95):
    """Apply PCA if features > samples, otherwise skip."""
    from sklearn.decomposition import PCA
    
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    n_samples = len(df)
    n_features = len(metabolite_cols)
    
    if n_features <= n_samples:
        logger.info("PCA skipped: features <= samples")
        return df, False, []
    
    logger.info(f"Applying PCA: {n_features} features > {n_samples} samples")
    
    X = df[metabolite_cols].values
    # Retain components explaining variance_threshold of variance or n_samples - 1 components
    n_components = min(n_samples - 1, n_features)
    
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X)
    
    # Create PCA column names
    pca_cols = [f"PC{i+1}" for i in range(X_pca.shape[1])]
    
    df_pca = df.copy()
    # Drop original metabolite columns and add PCA components
    df_pca = df_pca.drop(columns=metabolite_cols)
    for i, col in enumerate(pca_cols):
        df_pca[col] = X_pca[:, i]
    
    logger.info(f"PCA reduced to {len(pca_cols)} components")
    return df_pca, True, pca_cols

def save_pca_reduced_data(df, pca_cols, filepath=None):
    """Save PCA reduced data to a CSV file."""
    if filepath is None:
        filepath = os.path.join(DATA_ROOT, 'processed', 'pca_reduced.csv')
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved PCA reduced data to {filepath}")

def genotype_stratified_split(df, test_size=0.2):
    """
    Perform genotype-stratified train/test split ensuring no genotype leakage.
    Uses GroupShuffleSplit with groups=genotype_id.
    """
    if 'genotype_id' not in df.columns:
        raise ValueError("Column 'genotype_id' not found in dataset")
    
    logger.info("Performing genotype-stratified train/test split")
    
    # Use GroupShuffleSplit to ensure entire genotypes are held out
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=RANDOM_SEED)
    
    # Get indices for train and test sets
    for train_idx, test_idx in gss.split(df, groups=df['genotype_id']):
        train_indices = train_idx.tolist()
        test_indices = test_idx.tolist()
    
    logger.info(f"Split complete: {len(train_indices)} train samples, {len(test_indices)} test samples")
    
    return train_indices, test_indices

def save_split_indices(train_indices, test_indices, filepath=None):
    """Save split indices to a JSON file."""
    if filepath is None:
        filepath = os.path.join(DATA_ROOT, 'interim', 'split_indices.json')
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    data = {
        "train_indices": train_indices,
        "test_indices": test_indices
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved split indices to {filepath}")

def save_split_log(train_indices, test_indices, filepath=None):
    """Log the train/test split ratio and sample counts to a text file."""
    if filepath is None:
        filepath = os.path.join(DATA_ROOT, 'interim', 'split_log.txt')
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    total_samples = len(train_indices) + len(test_indices)
    train_ratio = len(train_indices) / total_samples
    test_ratio = len(test_indices) / total_samples
    
    log_content = (
        f"Genotype-Stratified Split Log\n"
        f"==============================\n"
        f"Total samples: {total_samples}\n"
        f"Train samples: {len(train_indices)}\n"
        f"Test samples: {len(test_indices)}\n"
        f"Train ratio: {train_ratio:.4f}\n"
        f"Test ratio: {test_ratio:.4f}\n"
    )
    
    with open(filepath, 'w') as f:
        f.write(log_content)
    
    logger.info(f"Saved split log to {filepath}")

def main():
    """Main function to run the genotype split pipeline."""
    # Load the harmonized dataset
    df = load_interim_dataset()
    
    # Perform genotype-stratified split
    train_indices, test_indices = genotype_stratified_split(df)
    
    # Save split indices and log
    save_split_indices(train_indices, test_indices)
    save_split_log(train_indices, test_indices)
    
    logger.info("Genotype split pipeline completed successfully")

if __name__ == "__main__":
    main()
