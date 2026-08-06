import os
import json
import yaml
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from pathlib import Path

def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_data(data_path: str = "data/raw/oqmd.parquet") -> pd.DataFrame:
    """Load the raw dataset from Parquet file."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_parquet(data_path)

def exclude_missing_data(df: pd.DataFrame, critical_columns: list = None) -> tuple[pd.DataFrame, dict]:
    """
    Exclude rows with missing values in critical columns.
    Returns cleaned dataframe and exclusion log details.
    """
    if critical_columns is None:
        # Define critical columns based on typical material property datasets
        # Assuming 'formation_energy' is the target and feature columns start with 'element_'
        # We'll check for any column that is critical for the model
        critical_columns = [col for col in df.columns if col not in ['material_id', 'formula']]
    
    missing_columns = []
    for col in critical_columns:
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        # If expected columns are missing entirely, we can't proceed with those
        # But we continue with what we have, noting the missing ones
        pass
    
    # Check for rows with NaN in any of the critical columns that exist
    existing_critical = [col for col in critical_columns if col in df.columns]
    if not existing_critical:
        return df, {"excluded_count": 0, "missing_columns": []}
    
    mask = df[existing_critical].isna().any(axis=1)
    excluded_count = mask.sum()
    
    cleaned_df = df[~mask].reset_index(drop=True)
    
    exclusion_log = {
        "excluded_count": int(excluded_count),
        "missing_columns": [col for col in existing_critical if df[col].isna().any()]
    }
    
    return cleaned_df, exclusion_log

def stratified_split(df: pd.DataFrame, target_col: str = "formation_energy", 
                     split_ratio: list = [0.8, 0.1, 0.1], seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified train/validation/test split.
    Since continuous targets can't be directly stratified, we bin them.
    """
    # Create bins for stratification
    df = df.copy()
    n_bins = 10
    df['_target_bin'] = pd.qcut(df[target_col], q=n_bins, duplicates='drop')
    
    # First split: train vs (val+test)
    train_df, temp_df = train_test_split(
        df, 
        test_size=(split_ratio[1] + split_ratio[2]), 
        stratify=df['_target_bin'], 
        random_state=seed
    )
    
    # Calculate ratio for val vs test from the remaining
    val_test_ratio = split_ratio[1] / (split_ratio[1] + split_ratio[2])
    
    # Second split: val vs test
    val_df, test_df = train_test_split(
        temp_df,
        test_size=1 - val_test_ratio,
        stratify=temp_df['_target_bin'],
        random_state=seed
    )
    
    # Drop the temporary bin column
    train_df = train_df.drop(columns=['_target_bin'])
    val_df = val_df.drop(columns=['_target_bin'])
    test_df = test_df.drop(columns=['_target_bin'])
    
    return train_df, val_df, test_df

def apply_pca(df: pd.DataFrame, n_components: int = 20, target_col: str = "formation_energy", seed: int = 42) -> tuple[pd.DataFrame, PCA]:
    """
    Apply PCA to reduce features to exactly n_components.
    Separates features from target, applies PCA, and returns combined dataframe.
    """
    df = df.copy()
    
    # Identify feature columns (exclude target and identifiers)
    feature_cols = [col for col in df.columns if col not in [target_col, 'material_id', 'formula']]
    
    if len(feature_cols) < n_components:
        raise ValueError(f"Number of feature columns ({len(feature_cols)}) is less than requested PCA components ({n_components})")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Standardize features before PCA
    X_mean = np.mean(X, axis=0)
    X_std = np.std(X, axis=0)
    X_std[X_std == 0] = 1  # Avoid division by zero
    X_scaled = (X - X_mean) / X_std
    
    # Apply PCA
    pca = PCA(n_components=n_components, random_state=seed)
    X_pca = pca.fit_transform(X_scaled)
    
    # Create new dataframe with PCA components
    pca_cols = [f'pca_{i}' for i in range(n_components)]
    pca_df = pd.DataFrame(X_pca, columns=pca_cols)
    pca_df[target_col] = y
    
    # Add material_id and formula if they exist
    if 'material_id' in df.columns:
        pca_df['material_id'] = df['material_id'].values
    if 'formula' in df.columns:
        pca_df['formula'] = df['formula'].values
    
    return pca_df, pca

def main():
    """Main function to execute the preprocessing pipeline."""
    print("Starting preprocessing pipeline...")
    
    # Load configuration
    config = load_config()
    seed = config['seed']
    split_type = config['split_type']
    split_ratio = config['split_ratio']
    
    # Load raw data
    print("Loading raw data...")
    df = load_data()
    print(f"Loaded {len(df)} rows")
    
    # Exclude missing data
    print("Excluding rows with missing critical features...")
    df_clean, exclusion_log = exclude_missing_data(df)
    print(f"Excluded {exclusion_log['excluded_count']} rows. Remaining: {len(df_clean)}")
    
    # Save exclusion log
    exclusion_log_path = "data/processed/exclusion_log.json"
    os.makedirs(os.path.dirname(exclusion_log_path), exist_ok=True)
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    print(f"Exclusion log saved to {exclusion_log_path}")
    
    # Apply stratified split if configured
    train_df, val_df, test_df = None, None, None
    if split_type == "stratified":
        print("Applying stratified split...")
        train_df, val_df, test_df = stratified_split(
            df_clean, 
            target_col="formation_energy", 
            split_ratio=split_ratio, 
            seed=seed
        )
        print(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    else:
        print("Using random split (stratification not configured)")
        train_df, val_df, test_df = train_test_split(
            df_clean, 
            test_size=0.2, 
            random_state=seed
        )
    
    # Apply PCA to training data to determine components
    print("Applying PCA to reduce features to 20 components...")
    train_pca, pca_model = apply_pca(train_df, n_components=20, seed=seed)
    
    # Apply the same PCA transformation to validation and test sets
    # Reuse the mean and std from training, and the PCA components
    def apply_pca_transform(df, pca_model, train_mean, train_std, n_components=20):
        df = df.copy()
        feature_cols = [col for col in df.columns if col not in ['formation_energy', 'material_id', 'formula']]
        
        X = df[feature_cols].values
        y = df['formation_energy'].values
        
        X_scaled = (X - train_mean) / train_std
        X_pca = pca_model.transform(X_scaled)[:, :n_components]
        
        pca_cols = [f'pca_{i}' for i in range(n_components)]
        pca_df = pd.DataFrame(X_pca, columns=pca_cols)
        pca_df['formation_energy'] = y
        
        if 'material_id' in df.columns:
            pca_df['material_id'] = df['material_id'].values
        if 'formula' in df.columns:
            pca_df['formula'] = df['formula'].values
        
        return pca_df
    
    # Recalculate mean and std from training set for transformation
    train_features = train_df[[col for col in train_df.columns if col not in ['formation_energy', 'material_id', 'formula']]].values
    train_mean = np.mean(train_features, axis=0)
    train_std = np.std(train_features, axis=0)
    train_std[train_std == 0] = 1
    
    val_pca = apply_pca_transform(val_df, pca_model, train_mean, train_std, n_components=20)
    test_pca = apply_pca_transform(test_df, pca_model, train_mean, train_std, n_components=20)
    
    # Combine all splits for final output
    combined_df = pd.concat([train_pca, val_pca, test_pca], ignore_index=True)
    
    # Save final processed features
    output_path = "data/processed/features_20pca.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined_df.to_csv(output_path, index=False)
    print(f"Processed features saved to {output_path}")
    print(f"Final dataset shape: {combined_df.shape}")
    
    print("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()
