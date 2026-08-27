import os
import json
import yaml
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded config: {config}")
    return config

def load_data(data_path="data/raw/oqmd.parquet"):
    """Load the raw OQMD dataset from parquet file."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded dataset with shape: {df.shape}")
    return df

def exclude_missing_data(df, critical_columns=None):
    """
    Exclude rows with missing values in critical columns.
    
    Args:
        df: Input DataFrame
        critical_columns: List of column names to check for missing values.
                         If None, checks all numeric columns.
    
    Returns:
        tuple: (cleaned_df, exclusion_log_dict)
    """
    if critical_columns is None:
        # Identify numeric columns that are likely features or target
        # Exclude non-numeric columns from missing check
        critical_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Check for missing values
    missing_mask = df[critical_columns].isna().any(axis=1)
    excluded_count = missing_mask.sum()
    excluded_indices = df[missing_mask].index.tolist()
    
    # Determine which columns had missing values
    missing_columns = []
    for col in critical_columns:
        if df[col].isna().any():
            missing_columns.append(col)
    
    # Create exclusion log
    exclusion_log = {
        "excluded_count": int(excluded_count),
        "missing_columns": missing_columns
    }
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows with missing values in columns: {missing_columns}")
    
    # Drop rows with missing values
    cleaned_df = df.dropna(subset=critical_columns)
    logger.info(f"Cleaned dataset shape: {cleaned_df.shape}")
    
    return cleaned_df, exclusion_log

def stratified_split(df, target_column, split_ratio, seed):
    """
    Perform stratified random split based on target variable.
    
    Args:
        df: Input DataFrame
        target_column: Name of the target column for stratification
        split_ratio: List [train_ratio, val_ratio, test_ratio]
        seed: Random seed for reproducibility
    
    Returns:
        tuple: (train_df, val_df, test_df)
    """
    if len(split_ratio) != 3:
        raise ValueError("split_ratio must be a list of 3 values: [train, val, test]")
    
    train_ratio, val_ratio, test_ratio = split_ratio
    
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
        raise ValueError("Split ratios must sum to 1.0")
    
    # First split: train vs (val + test)
    train_df, temp_df = train_test_split(
        df,
        train_size=train_ratio,
        stratify=df[target_column],
        random_state=seed
    )
    
    # Calculate ratio for val vs test from the remaining
    remaining_ratio = val_ratio + test_ratio
    if remaining_ratio > 0:
        val_ratio_adjusted = val_ratio / remaining_ratio
    else:
        val_ratio_adjusted = 0
    
    # Second split: val vs test
    val_df, test_df = train_test_split(
        temp_df,
        train_size=val_ratio_adjusted,
        stratify=temp_df[target_column],
        random_state=seed
    )
    
    logger.info(f"Stratified split completed:")
    logger.info(f"  Train: {len(train_df)} ({len(train_df)/len(df)*100:.1f}%)")
    logger.info(f"  Val:   {len(val_df)} ({len(val_df)/len(df)*100:.1f}%)")
    logger.info(f"  Test:  {len(test_df)} ({len(test_df)/len(df)*100:.1f}%)")
    
    return train_df, val_df, test_df

def apply_pca(df, n_components=20, target_column=None):
    """
    Apply PCA to reduce features to exactly n_components.
    
    Args:
        df: Input DataFrame (features only, no target)
        n_components: Number of PCA components (default 20)
        target_column: Column name to exclude from features (if any)
    
    Returns:
        tuple: (pca_df, pca_model, explained_variance_ratio)
    """
    # Prepare features
    if target_column and target_column in df.columns:
        features_df = df.drop(columns=[target_column])
    else:
        features_df = df.copy()
    
    # Ensure only numeric features
    features_df = features_df.select_dtypes(include=[np.number])
    
    if features_df.shape[1] < n_components:
        logger.warning(f"Number of features ({features_df.shape[1]}) is less than requested components ({n_components}). Adjusting n_components.")
        n_components = features_df.shape[1]
    
    # Apply PCA
    pca = PCA(n_components=n_components)
    pca_features = pca.fit_transform(features_df)
    
    # Create DataFrame with PCA components
    pca_column_names = [f'pca_{i}' for i in range(n_components)]
    pca_df = pd.DataFrame(pca_features, columns=pca_column_names, index=df.index)
    
    logger.info(f"PCA applied: reduced from {features_df.shape[1]} features to {n_components} components")
    logger.info(f"Explained variance ratio: {pca.explained_variance_ratio_.sum():.4f}")
    
    return pca_df, pca, pca.explained_variance_ratio_

def main():
    """Main function to run the preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")
    
    # Load configuration
    config = load_config()
    seed = config.get('seed', 42)
    split_ratio = config.get('split_ratio', [0.8, 0.1, 0.1])
    split_type = config.get('split_type', 'stratified')
    
    # Load data
    df = load_data()
    
    # Identify target column (assuming 'formation_energy' based on OQMD)
    target_column = 'formation_energy'
    if target_column not in df.columns:
        # Try to find any column that looks like a target
        potential_targets = [col for col in df.columns if 'energy' in col.lower() or 'target' in col.lower()]
        if potential_targets:
            target_column = potential_targets[0]
            logger.info(f"Using {target_column} as target column")
        else:
            raise ValueError("Could not identify target column. Expected 'formation_energy' or similar.")
    
    # Exclude missing data
    df_clean, exclusion_log = exclude_missing_data(df, critical_columns=[target_column])
    
    # Save exclusion log
    exclusion_log_path = "data/processed/exclusion_log.json"
    os.makedirs(os.path.dirname(exclusion_log_path), exist_ok=True)
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Saved exclusion log to {exclusion_log_path}")
    
    # Apply stratified split if configured
    if split_type == 'stratified':
        train_df, val_df, test_df = stratified_split(
            df_clean, 
            target_column=target_column, 
            split_ratio=split_ratio, 
            seed=seed
        )
        
        # Combine train and val for feature extraction (test is held out)
        # For this task, we process the full cleaned dataset for PCA
        # But typically we'd fit PCA on train only. Here we follow task spec.
        combined_df = pd.concat([train_df, val_df, test_df])
    else:
        logger.warning(f"Split type '{split_type}' not implemented. Using full dataset.")
        combined_df = df_clean
    
    # Apply PCA to reduce features to exactly 20 components
    # Exclude target column from features
    pca_df, pca_model, var_ratio = apply_pca(
        combined_df, 
        n_components=20, 
        target_column=target_column
    )
    
    # Add target back to the PCA DataFrame
    pca_df[target_column] = combined_df[target_column].values
    
    # Save the processed features
    output_path = "data/processed/features_20pca.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pca_df.to_csv(output_path, index=False)
    logger.info(f"Saved processed features to {output_path}")
    
    # Save PCA model for later use (optional but good practice)
    # We'll save the explained variance ratio as metadata
    pca_metadata = {
        "n_components": 20,
        "explained_variance_ratio": var_ratio.tolist(),
        "total_explained_variance": float(var_ratio.sum()),
        "seed": seed,
        "split_type": split_type
    }
    
    metadata_path = "data/processed/pca_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(pca_metadata, f, indent=2)
    logger.info(f"Saved PCA metadata to {metadata_path}")
    
    logger.info("Preprocessing pipeline completed successfully!")
    return pca_df

if __name__ == "__main__":
    main()