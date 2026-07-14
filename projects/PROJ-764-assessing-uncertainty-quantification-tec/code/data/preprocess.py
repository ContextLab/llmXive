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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def load_data(data_path="data/raw/oqmd.parquet"):
    """Load the raw dataset from Parquet file."""
    logger.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def exclude_missing_data(df, target_column="formation_energy_per_atom"):
    """
    Exclude rows with missing values in critical features or target.
    Returns cleaned dataframe and exclusion metadata.
    """
    logger.info("Checking for missing data...")
    
    # Identify critical columns (all feature columns + target)
    # Assuming the target is 'formation_energy_per_atom' and rest are features
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset")
    
    # Determine feature columns (everything except target and non-numeric)
    feature_cols = [col for col in df.columns if col != target_column and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    critical_cols = feature_cols + [target_column]
    
    # Check for missing values in critical columns
    missing_mask = df[critical_cols].isnull().any(axis=1)
    excluded_count = missing_mask.sum()
    excluded_indices = df[missing_mask].index
    
    # Identify which columns had missing values
    missing_columns = []
    for col in critical_cols:
        if df[col].isnull().any():
            missing_columns.append(col)
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} rows with missing critical data")
        logger.warning(f"Missing in columns: {missing_columns}")
    
    # Clean dataframe
    df_clean = df.dropna(subset=critical_cols).reset_index(drop=True)
    
    exclusion_log = {
        "excluded_count": int(excluded_count),
        "missing_columns": missing_columns
    }
    
    return df_clean, exclusion_log

def stratified_split(df, target_column="formation_energy_per_atom", 
                     split_ratio=None, seed=42):
    """
    Perform stratified random split based on target variable.
    Bins the continuous target for stratification.
    """
    if split_ratio is None:
        split_ratio = [0.8, 0.1, 0.1]
    
    logger.info(f"Performing stratified split with ratio {split_ratio} and seed {seed}")
    
    # Create bins for stratification (quantile-based)
    n_bins = 10
    df = df.copy()
    df['_strata'] = pd.qcut(df[target_column], q=n_bins, labels=False, duplicates='drop')
    
    # If we can't make enough bins, fall back to simple split
    if len(df['_strata'].unique()) < 2:
        logger.warning("Not enough unique values for stratification, falling back to random split")
        train_df, temp_df = train_test_split(
            df, test_size=split_ratio[1] + split_ratio[2], random_state=seed
        )
        val_df, test_df = train_test_split(
            temp_df, test_size=split_ratio[2] / (split_ratio[1] + split_ratio[2]), 
            random_state=seed
        )
    else:
        # Train vs (Val + Test)
        train_df, temp_df = train_test_split(
            df, test_size=split_ratio[1] + split_ratio[2], 
            stratify=df['_strata'], random_state=seed
        )
        # Val vs Test
        val_ratio = split_ratio[2] / (split_ratio[1] + split_ratio[2])
        val_df, test_df = train_test_split(
            temp_df, test_size=val_ratio, 
            stratify=temp_df['_strata'], random_state=seed
        )
    
    # Drop the temporary strata column
    train_df = train_df.drop(columns=['_strata'])
    val_df = val_df.drop(columns=['_strata'])
    test_df = test_df.drop(columns=['_strata'])
    
    logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    return train_df, val_df, test_df

def apply_pca(df, target_column="formation_energy_per_atom", n_components=20):
    """
    Apply PCA to reduce features to exactly n_components.
    Returns dataframe with PCA-transformed features and target.
    """
    logger.info(f"Applying PCA to reduce features to {n_components} components")
    
    # Separate features and target
    feature_cols = [col for col in df.columns if col != target_column]
    X = df[feature_cols].values
    y = df[target_column].values
    
    # Standardize features before PCA
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std == 0] = 1  # Avoid division by zero
    X_scaled = (X - mean) / std
    
    # Apply PCA
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)
    
    # Check if we got the requested number of components
    actual_components = X_pca.shape[1]
    if actual_components < n_components:
        logger.warning(f"PCA only produced {actual_components} components, requested {n_components}")
        n_components = actual_components
    
    # Create dataframe with PCA features
    pca_col_names = [f"pca_{i}" for i in range(n_components)]
    pca_df = pd.DataFrame(X_pca[:, :n_components], columns=pca_col_names)
    pca_df[target_column] = y
    
    logger.info(f"PCA output shape: {pca_df.shape}")
    logger.info(f"Explained variance ratio: {pca.explained_variance_ratio_}")
    logger.info(f"Total explained variance: {np.sum(pca.explained_variance_ratio_):.4f}")
    
    return pca_df

def main():
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    
    # 1. Load config
    config = load_config("code/config.yaml")
    seed = config.get("seed", 42)
    split_type = config.get("split_type", "stratified")
    split_ratio = config.get("split_ratio", [0.8, 0.1, 0.1])
    
    # 2. Load data
    df = load_data("data/raw/oqmd.parquet")
    
    # 3. Exclude missing data
    df_clean, exclusion_log = exclude_missing_data(df)
    
    # 4. Save exclusion log
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exclusion_log_path = output_dir / "exclusion_log.json"
    with open(exclusion_log_path, "w") as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Saved exclusion log to {exclusion_log_path}")
    
    # 5. Split data
    if split_type == "stratified":
        train_df, val_df, test_df = stratified_split(
            df_clean, split_ratio=split_ratio, seed=seed
        )
    else:
        logger.warning(f"Unknown split_type '{split_type}', using random split")
        train_df, temp_df = train_test_split(
            df_clean, test_size=split_ratio[1] + split_ratio[2], random_state=seed
        )
        val_df, test_df = train_test_split(
            temp_df, test_size=split_ratio[2] / (split_ratio[1] + split_ratio[2]), 
            random_state=seed
        )
    
    # 6. Apply PCA to each split
    # Note: We fit PCA on training data and transform all sets
    # But for simplicity in this task, we apply PCA independently to each split
    # as per task description which says "Apply PCA" without specifying fit/transform separation
    # For a more rigorous approach, we would fit on train and transform all.
    
    # Fit PCA on training data
    feature_cols = [col for col in train_df.columns if col != "formation_energy_per_atom"]
    X_train = train_df[feature_cols].values
    y_train = train_df["formation_energy_per_atom"].values
    
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0)
    std[std == 0] = 1
    X_train_scaled = (X_train - mean) / std
    
    X_val = val_df[feature_cols].values
    y_val = val_df["formation_energy_per_atom"].values
    X_val_scaled = (X_val - mean) / std
    
    X_test = test_df[feature_cols].values
    y_test = test_df["formation_energy_per_atom"].values
    X_test_scaled = (X_test - mean) / std
    
    # Apply PCA
    pca = PCA(n_components=20)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_val_pca = pca.transform(X_val_scaled)
    X_test_pca = pca.transform(X_test_scaled)
    
    # Create combined dataframe with all splits
    # For the output file, we'll combine all splits with a split indicator
    train_pca_df = pd.DataFrame(X_train_pca, columns=[f"pca_{i}" for i in range(X_train_pca.shape[1])])
    train_pca_df["formation_energy_per_atom"] = y_train
    train_pca_df["split"] = "train"
    
    val_pca_df = pd.DataFrame(X_val_pca, columns=[f"pca_{i}" for i in range(X_val_pca.shape[1])])
    val_pca_df["formation_energy_per_atom"] = y_val
    val_pca_df["split"] = "val"
    
    test_pca_df = pd.DataFrame(X_test_pca, columns=[f"pca_{i}" for i in range(X_test_pca.shape[1])])
    test_pca_df["formation_energy_per_atom"] = y_test
    test_pca_df["split"] = "test"
    
    combined_df = pd.concat([train_pca_df, val_pca_df, test_pca_df], ignore_index=True)
    
    # 7. Save processed features
    output_path = output_dir / "features_20pca.csv"
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Saved processed features to {output_path}")
    logger.info(f"Total rows in processed data: {len(combined_df)}")
    
    logger.info("Preprocessing pipeline completed successfully")
    return combined_df

if __name__ == "__main__":
    main()