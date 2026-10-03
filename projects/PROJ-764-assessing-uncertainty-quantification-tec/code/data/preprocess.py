import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pickle
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path='code/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_data():
    """Load the raw OQMD dataset from parquet file."""
    raw_path = 'data/raw/oqmd.parquet'
    if not os.path.exists(raw_path):
        raise FileNotFoundError(
            f"Data file not found: {raw_path}. Please run T005 (download.py) to materialize the dataset first."
        )
    logger.info(f"Loading data from {raw_path}...")
    df = pd.read_parquet(raw_path)
    logger.info(f"Loaded {len(df)} records. Columns: {list(df.columns)}")
    return df

def apply_quantile_binning(df, target_col, n_bins=10):
    """Apply quantile binning to the target variable."""
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    
    # Create bins based on quantiles
    df['target_bin'] = pd.qcut(df[target_col], q=n_bins, labels=False, duplicates='drop')
    logger.info(f"Applied quantile binning with {len(df['target_bin'].unique())} bins.")
    return df

def stratified_split(df, config):
    """Perform stratified split based on target_bin."""
    train_ratio, val_ratio, test_ratio = config['split_ratio']
    seed = config['seed']
    
    # First split: train vs (val + test)
    train_df, temp_df = train_test_split(
        df, 
        train_size=train_ratio, 
        stratify=df['target_bin'], 
        random_state=seed
    )
    
    # Second split: val vs test (adjust ratios)
    val_test_ratio = val_ratio / (val_ratio + test_ratio)
    val_df, test_df = train_test_split(
        temp_df, 
        train_size=val_test_ratio, 
        stratify=temp_df['target_bin'], 
        random_state=seed
    )
    
    logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    return train_df, val_df, test_df

def save_split_data(train_df, val_df, test_df, processed_dir='data/processed'):
    """Save split data to CSV files."""
    os.makedirs(processed_dir, exist_ok=True)
    
    train_path = os.path.join(processed_dir, 'raw_train.csv')
    val_path = os.path.join(processed_dir, 'raw_val.csv')
    test_path = os.path.join(processed_dir, 'raw_test.csv')
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Saved raw splits to {train_path}, {val_path}, {test_path}")

def perform_pca_and_exclusion():
    """
    T006b Task: PCA & Exclusion.
    1. Read raw_train.csv.
    2. Identify critical features (exclude non-numeric, ID columns).
    3. Exclude rows with missing critical features.
    4. Fit PCA on training set only (20 components).
    5. Transform train/val/test.
    6. Save outputs and validation report.
    """
    processed_dir = 'data/processed'
    
    # Load raw splits
    train_path = os.path.join(processed_dir, 'raw_train.csv')
    val_path = os.path.join(processed_dir, 'raw_val.csv')
    test_path = os.path.join(processed_dir, 'raw_test.csv')
    
    if not all(os.path.exists(p) for p in [train_path, val_path, test_path]):
        raise FileNotFoundError(
            f"Raw split files missing. Ensure T006a (preprocess.py split) has completed. "
            f"Expected: {train_path}, {val_path}, {test_path}"
        )
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    logger.info(f"Loaded raw splits: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    # Identify feature columns
    # Exclude: sample_id (if exists), target_bin, and any non-numeric columns
    exclude_cols = ['sample_id', 'target_bin', 'name', 'formula', 'split']
    feature_cols = [c for c in train_df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(train_df[c])]
    
    logger.info(f"Identified {len(feature_cols)} feature columns for PCA: {feature_cols[:5]}...")
    
    if len(feature_cols) == 0:
        raise ValueError("No numeric feature columns found for PCA.")
    
    # Check for missing values in feature columns
    missing_mask = train_df[feature_cols].isnull().any(axis=1)
    excluded_count = missing_mask.sum()
    excluded_indices = train_df[missing_mask].index.tolist()
    
    # Identify which columns have missing values
    missing_columns = list(train_df[feature_cols].columns[train_df[feature_cols].isnull().any()])
    
    logger.info(f"Exclusion: {excluded_count} rows have missing values in features: {missing_columns}")
    
    # Filter training data
    clean_train_df = train_df[~missing_mask].reset_index(drop=True)
    clean_val_df = val_df[~val_df[feature_cols].isnull().any(axis=1)].reset_index(drop=True)
    clean_test_df = test_df[~test_df[feature_cols].isnull().any(axis=1)].reset_index(drop=True)
    
    logger.info(f"After exclusion: Train={len(clean_train_df)}, Val={len(clean_val_df)}, Test={len(clean_test_df)}")
    
    # Prepare data for PCA
    X_train = clean_train_df[feature_cols].values
    X_val = clean_val_df[feature_cols].values
    X_test = clean_test_df[feature_cols].values
    
    # Standardize before PCA
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Fit PCA on training set only
    n_components = 20
    pca = PCA(n_components=n_components)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_val_pca = pca.transform(X_val_scaled)
    X_test_pca = pca.transform(X_test_scaled)
    
    logger.info(f"PCA fitted. Explained variance ratio (sum): {np.sum(pca.explained_variance_ratio_):.4f}")
    
    # Create output dataframes
    # Keep target_bin and sample_id if they exist, add PCA components
    pca_col_names = [f'pca_{i}' for i in range(n_components)]
    
    output_train = clean_train_df[['target_bin']].copy()
    if 'sample_id' in clean_train_df.columns:
        output_train['sample_id'] = clean_train_df['sample_id']
    output_train[pca_col_names] = X_train_pca
    
    output_val = clean_val_df[['target_bin']].copy()
    if 'sample_id' in clean_val_df.columns:
        output_val['sample_id'] = clean_val_df['sample_id']
    output_val[pca_col_names] = X_val_pca
    
    output_test = clean_test_df[['target_bin']].copy()
    if 'sample_id' in clean_test_df.columns:
        output_test['sample_id'] = clean_test_df['sample_id']
    output_test[pca_col_names] = X_test_pca
    
    # Save outputs
    features_train_path = os.path.join(processed_dir, 'features_train_20pca.csv')
    features_val_path = os.path.join(processed_dir, 'features_val_20pca.csv')
    features_test_path = os.path.join(processed_dir, 'features_test_20pca.csv')
    
    output_train.to_csv(features_train_path, index=False)
    output_val.to_csv(features_val_path, index=False)
    output_test.to_csv(features_test_path, index=False)
    
    logger.info(f"Saved PCA features to {features_train_path}, {features_val_path}, {features_test_path}")
    
    # Save PCA transformer and scaler
    transformer_path = os.path.join(processed_dir, 'pca_transformer.pkl')
    with open(transformer_path, 'wb') as f:
        pickle.dump({'pca': pca, 'scaler': scaler, 'feature_cols': feature_cols}, f)
    logger.info(f"Saved PCA transformer to {transformer_path}")
    
    # Write validation report
    validation_report = {
        "excluded_count": int(excluded_count),
        "missing_columns": missing_columns,
        "structural_features_available": False, # Placeholder, updated from download if needed
        "pca_components": n_components,
        "explained_variance_ratio": float(np.sum(pca.explained_variance_ratio_)),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    report_path = os.path.join('data', 'validation_report.json')
    with open(report_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    logger.info(f"Saved validation report to {report_path}")
    
    return True

def main():
    """Main entry point for T006a (Split) and T006b (PCA)."""
    logger.info("Starting Preprocessing Pipeline (T006a + T006b)...")
    
    try:
        # Step 1: Load Config
        config = load_config()
        logger.info(f"Loaded config: split_ratio={config['split_ratio']}, seed={config['seed']}")
        
        # Step 2: Load Raw Data
        df = load_data()
        
        # Step 3: Apply Quantile Binning (T006a)
        target_col = 'formation_energy' # Or 'formation_energy_per_atom' depending on schema
        if target_col not in df.columns:
            # Fallback if column name differs
            target_col = 'energy_per_atom'
            if target_col not in df.columns:
                raise KeyError("Target column 'formation_energy' or 'energy_per_atom' not found.")
        
        df = apply_quantile_binning(df, target_col, n_bins=10)
        
        # Step 4: Stratified Split (T006a)
        train_df, val_df, test_df = stratified_split(df, config)
        
        # Step 5: Save Raw Splits (T006a)
        save_split_data(train_df, val_df, test_df)
        
        # Step 6: PCA & Exclusion (T006b)
        perform_pca_and_exclusion()
        
        logger.info("Preprocessing Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()