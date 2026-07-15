import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SPLITS_DIR = DATA_DIR / "splits"
CURATED_DATA_PATH = DATA_DIR / "curated_builds.csv"

# Ensure splits directory exists
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

def calculate_energy_density(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate volumetric energy density: E_v = P / (v * h * t)
    Units: P (W), v (mm/s), h (mm), t (mm) -> E_v (J/mm^3)
    
    Args:
        df: DataFrame with columns 'laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness'
    
    Returns:
        DataFrame with added 'energy_density' column
    """
    df = df.copy()
    
    # Ensure numeric types
    numeric_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate energy density
    # Avoid division by zero
    denominator = df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness']
    denominator = denominator.replace(0, np.nan)
    
    df['energy_density'] = df['laser_power'] / denominator
    
    logger.info(f"Calculated energy density for {len(df)} rows")
    return df

def verify_column_integrity(df: pd.DataFrame) -> bool:
    """
    Verify that all required columns exist and are numeric where appropriate.
    
    Args:
        df: Input DataFrame
    
    Returns:
        True if integrity check passes, False otherwise
    """
    required_cols = [
        'laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness',
        'ductility', 'alloy_family'
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    
    numeric_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'ductility']
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"Column {col} is not numeric")
    
    logger.info("Column integrity verified")
    return True

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for given features.
    
    Args:
        df: DataFrame containing features
        features: List of feature column names
    
    Returns:
        DataFrame with columns 'feature' and 'vif'
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Create a matrix with features
    X = df[features].copy()
    
    # Handle constant features (VIF undefined)
    vif_data = []
    for i, feature in enumerate(features):
        if X[feature].std() == 0:
            vif = np.inf
        else:
            try:
                vif = variance_inflation_factor(X.values, i)
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {feature}: {e}")
                vif = np.inf
        
        vif_data.append({'feature': feature, 'vif': vif})
    
    return pd.DataFrame(vif_data)

def perform_vif_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform VIF analysis and apply FR-005 logic:
    If Energy Density VIF > 5, drop individual constituents (Power, Speed, Hatch, Thickness)
    and retain only Energy Density.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with reduced feature set if VIF threshold exceeded
    """
    # Features for VIF calculation
    potential_features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
    
    # Check which features exist
    available_features = [f for f in potential_features if f in df.columns]
    
    if not available_features:
        logger.warning("No features available for VIF analysis")
        return df
    
    # Calculate initial VIF
    vif_df = calculate_vif(df, available_features)
    logger.info(f"Initial VIF analysis:\n{vif_df}")
    
    # Check Energy Density VIF
    ed_vif_row = vif_df[vif_df['feature'] == 'energy_density']
    
    if len(ed_vif_row) > 0:
        ed_vif = ed_vif_row['vif'].values[0]
        
        if ed_vif > 5:
            logger.info(f"Energy Density VIF ({ed_vif:.2f}) > 5. Applying FR-005 logic.")
            logger.info("Dropping individual constituents: laser_power, scan_speed, hatch_spacing, layer_thickness")
            
            # Drop constituent features
            constituents = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
            df_reduced = df.drop(columns=[c for c in constituents if c in df.columns])
            
            # Re-calculate VIF to verify
            remaining_features = [f for f in available_features if f in df_reduced.columns and f != 'energy_density']
            if 'energy_density' in df_reduced.columns:
                remaining_features.insert(0, 'energy_density')
            
            if len(remaining_features) > 1:
                vif_reduced = calculate_vif(df_reduced, remaining_features)
                max_vif = vif_reduced['vif'].max()
                logger.info(f"Re-calculated max VIF: {max_vif:.2f}")
            
            return df_reduced
        else:
            logger.info(f"Energy Density VIF ({ed_vif:.2f}) <= 5. Keeping all features.")
    else:
        logger.warning("Energy density column not found for VIF analysis")
    
    return df

def perform_loafo_split(df: pd.DataFrame, target_col: str = 'ductility') -> Dict[str, pd.DataFrame]:
    """
    Perform Leave-One-Alloy-Family-Out (LOAFO) cross-validation split.
    
    For N < 100, each alloy family is left out once as the test set.
    Returns a list of dictionaries, each containing 'train', 'val', 'test' splits.
    
    Args:
        df: Input DataFrame
        target_col: Target column name
    
    Returns:
        List of dictionaries with train/val/test DataFrames
    """
    alloy_families = df['alloy_family'].unique()
    n_families = len(alloy_families)
    
    logger.info(f"Performing LOAFO split with {n_families} alloy families")
    
    splits = []
    
    for i, test_family in enumerate(alloy_families):
        # Test set: all rows with this alloy family
        test_mask = df['alloy_family'] == test_family
        test_df = df[test_mask].copy()
        
        # Train+Val set: all other rows
        train_val_df = df[~test_mask].copy()
        
        if len(train_val_df) == 0:
            logger.warning(f"No training data available when leaving out {test_family}")
            continue
        
        # Split train/val from the remaining data (80/20)
        if len(train_val_df) > 1:
            # Stratified split by alloy_family within train_val
            train_family_families = train_val_df['alloy_family'].unique()
            
            # Simple split: 80% train, 20% val
            val_size = max(1, int(len(train_val_df) * 0.2))
            val_df = train_val_df.sample(n=val_size, random_state=42)
            train_df = train_val_df.drop(val_df.index)
        else:
            train_df = train_val_df.copy()
            val_df = pd.DataFrame(columns=df.columns)
        
        splits.append({
            'train': train_df,
            'val': val_df,
            'test': test_df,
            'fold': i,
            'test_family': test_family
        })
        
        logger.info(f"Fold {i}: Test family={test_family}, Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    return splits

def perform_stratified_split(df: pd.DataFrame, target_col: str = 'ductility') -> Dict[str, pd.DataFrame]:
    """
    Perform standard stratified train/val/test split by alloy_family.
    
    For N >= 100, use 70/15/15 split stratified by alloy_family.
    
    Args:
        df: Input DataFrame
        target_col: Target column name
    
    Returns:
        Dictionary with 'train', 'val', 'test' DataFrames
    """
    from sklearn.model_selection import train_test_split
    
    logger.info(f"Performing stratified split (N={len(df)})")
    
    # First split: 70% train, 30% temp (val+test)
    train_df, temp_df = train_test_split(
        df, 
        test_size=0.30, 
        stratify=df['alloy_family'],
        random_state=42
    )
    
    # Second split: 50% of temp for val, 50% for test (15% each of original)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        stratify=temp_df['alloy_family'],
        random_state=42
    )
    
    logger.info(f"Split sizes: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    return {
        'train': train_df,
        'val': val_df,
        'test': test_df
    }

def split_data(df: pd.DataFrame, target_col: str = 'ductility') -> Dict[str, any]:
    """
    Main entry point for data splitting.
    
    Logic:
    - If N < 100: Use LOAFO (returns list of splits)
    - If N >= 100: Use stratified split (returns single split dict)
    
    Args:
        df: Input DataFrame
        target_col: Target column name
    
    Returns:
        Dictionary with 'splits' (list or dict), 'strategy', 'n_rows'
    """
    n_rows = len(df)
    
    if n_rows < 100:
        logger.info(f"Dataset size ({n_rows}) < 100. Using LOAFO strategy.")
        splits = perform_loafo_split(df, target_col)
        strategy = 'loafo'
    else:
        logger.info(f"Dataset size ({n_rows}) >= 100. Using stratified split strategy.")
        splits = perform_stratified_split(df, target_col)
        strategy = 'stratified'
    
    return {
        'splits': splits,
        'strategy': strategy,
        'n_rows': n_rows
    }

def save_split_artifacts(split_result: Dict[str, any]) -> None:
    """
    Save split artifacts to data/splits directory.
    
    For LOAFO: Saves each fold as separate files.
    For Stratified: Saves train, val, test files.
    
    Args:
        split_result: Result from split_data()
    """
    strategy = split_result['strategy']
    splits = split_result['splits']
    metadata = {
        'strategy': strategy,
        'n_rows': split_result['n_rows'],
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    if strategy == 'loafo':
        # Save each fold
        for i, fold_data in enumerate(splits):
            fold_dir = SPLITS_DIR / f"fold_{i}"
            fold_dir.mkdir(parents=True, exist_ok=True)
            
            fold_data['train'].to_csv(fold_dir / 'train.csv', index=False)
            fold_data['val'].to_csv(fold_dir / 'val.csv', index=False)
            fold_data['test'].to_csv(fold_dir / 'test.csv', index=False)
            
            # Save fold metadata
            fold_meta = {
                'fold': fold_data['fold'],
                'test_family': fold_data['test_family'],
                'train_size': len(fold_data['train']),
                'val_size': len(fold_data['val']),
                'test_size': len(fold_data['test'])
            }
            with open(fold_dir / 'metadata.json', 'w') as f:
                json.dump(fold_meta, f, indent=2)
        
        logger.info(f"Saved {len(splits)} LOAFO folds to {SPLITS_DIR}")
        
        # Save overall metadata
        with open(SPLITS_DIR / 'loafo_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
            
    else:  # stratified
        splits['train'].to_csv(SPLITS_DIR / 'train.csv', index=False)
        splits['val'].to_csv(SPLITS_DIR / 'val.csv', index=False)
        splits['test'].to_csv(SPLITS_DIR / 'test.csv', index=False)
        
        # Save metadata
        with open(SPLITS_DIR / 'stratified_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved stratified splits to {SPLITS_DIR}")

def main():
    """
    Main execution function for data splitting.
    
    Reads curated_builds.csv, performs splitting based on dataset size,
    and saves artifacts to data/splits/.
    """
    logger.info("Starting data splitting process")
    
    # Load curated data
    if not CURATED_DATA_PATH.exists():
        logger.error(f"Curated data not found at {CURATED_DATA_PATH}")
        sys.exit(1)
    
    df = pd.read_csv(CURATED_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from {CURATED_DATA_PATH}")
    
    # Verify required columns
    if not verify_column_integrity(df):
        logger.error("Column integrity check failed")
        sys.exit(1)
    
    # Perform splitting
    split_result = split_data(df)
    
    # Save artifacts
    save_split_artifacts(split_result)
    
    logger.info("Data splitting completed successfully")
    return split_result

if __name__ == "__main__":
    main()