import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CURATED_DATA_PATH = Path("data/curated_builds.csv")
SPLIT_OUTPUT_DIR = Path("data/splits")
LOAFO_OUTPUT_FILE = SPLIT_OUTPUT_DIR / "loafo_splits.json"

def calculate_energy_density(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate volumetric energy density: E_v = P / (v * h * t)
    Assumes columns: laser_power (W), scan_speed (mm/s), 
    hatch_spacing (mm), layer_thickness (mm).
    """
    if not all(col in df.columns for col in ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']):
        raise ValueError("Missing required columns for energy density calculation.")
    
    # Avoid division by zero
    denominator = df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness']
    denominator = denominator.replace(0, np.nan)
    
    df['energy_density'] = df['laser_power'] / denominator
    return df

def verify_column_integrity(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """Verify that all required columns exist in the DataFrame."""
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    Returns a dictionary mapping feature names to VIF values.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    if not features:
        return {}
    
    # Add constant for intercept
    X = df[features].copy()
    X['const'] = 1.0
    
    vif_data = {}
    for i, feature in enumerate(features):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[feature] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_data[feature] = float('inf')
    
    return vif_data

def perform_vif_analysis(df: pd.DataFrame, 
                         features: List[str], 
                         threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Perform VIF analysis and filter features.
    Logic: If Energy Density VIF > threshold, drop individual constituents.
    Returns the filtered DataFrame and the list of final features.
    """
    logger.info("Starting VIF analysis...")
    
    # Initial VIF calculation
    vif_initial = calculate_vif(df, features)
    logger.info(f"Initial VIF values: {vif_initial}")
    
    # Check for Energy Density collinearity
    constituents = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    energy_density_col = 'energy_density'
    
    final_features = features.copy()
    
    if energy_density_col in vif_initial and vif_initial[energy_density_col] > threshold:
        logger.warning(f"Energy Density VIF ({vif_initial[energy_density_col]:.2f}) > {threshold}. "
                     f"Dropping constituent predictors: {constituents}")
        
        # Drop constituents
        for const in constituents:
            if const in final_features:
                final_features.remove(const)
        
        # Re-calculate VIF on reduced set
        vif_reduced = calculate_vif(df, final_features)
        logger.info(f"Reduced VIF values: {vif_reduced}")
        
        # Robustness check (T042): If any remaining feature has VIF > threshold, halt
        for feat, val in vif_reduced.items():
            if val > threshold:
                logger.critical(f"CRITICAL: Irreducible collinearity detected. "
                              f"Feature '{feat}' has VIF {val:.2f} > {threshold}. "
                              f"Model cannot be fitted safely. Halting execution.")
                raise RuntimeError(f"Irreducible collinearity: {feat} VIF={val:.2f}")
    else:
        logger.info("Energy Density VIF is acceptable or not present. Keeping all features.")
    
    # Filter dataframe to final features
    # Note: We assume the caller handles dropping the original constituents from the 
    # main dataframe if they are no longer needed, but here we return the feature list
    # for model training.
    return df, final_features

def perform_loafo_split(df: pd.DataFrame, 
                        target_col: str, 
                        group_col: str = 'alloy_family') -> List[Dict[str, pd.DataFrame]]:
    """
    Perform Leave-One-Alloy-Family-Out (LOAFO) cross-validation split.
    
    Validates split integrity by ensuring the left-out group is strictly absent
    from the training set for each fold.
    
    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        group_col: Name of the column defining groups (alloy families).
    
    Returns:
        List of dictionaries with 'train' and 'test' DataFrames for each fold.
    """
    logger.info(f"Performing LOAFO split on column '{group_col}'.")
    
    if group_col not in df.columns:
        raise ValueError(f"Group column '{group_col}' not found in DataFrame.")
    
    unique_groups = df[group_col].unique()
    logger.info(f"Found {len(unique_groups)} unique alloy families: {unique_groups}")
    
    splits = []
    
    for i, left_out_group in enumerate(unique_groups):
        logger.info(f"Fold {i+1}/{len(unique_groups)}: Left-out group = '{left_out_group}'")
        
        # Create test set
        test_mask = df[group_col] == left_out_group
        test_set = df[test_mask].copy()
        
        # Create train set
        train_mask = df[group_col] != left_out_group
        train_set = df[train_mask].copy()
        
        # VALIDATION CHECK: Ensure strict absence
        train_groups = set(train_set[group_col].unique())
        test_groups = set(test_set[group_col].unique())
        
        if left_out_group in train_groups:
            logger.critical(f"FATAL DATA LEAKAGE: Group '{left_out_group}' found in training set!")
            raise ValueError(f"Data leakage detected: '{left_out_group}' is in the training set.")
        
        if not test_groups.issubset({left_out_group}):
            logger.warning(f"Test set contains unexpected groups: {test_groups - {left_out_group}}")
        
        logger.info(f"  Train size: {len(train_set)}, Test size: {len(test_set)}")
        logger.info(f"  Train groups: {sorted(train_groups)}")
        logger.info(f"  Test groups: {sorted(test_groups)}")
        
        splits.append({
            'train': train_set,
            'test': test_set,
            'left_out_group': left_out_group
        })
    
    return splits

def perform_stratified_split(df: pd.DataFrame, 
                             target_col: str, 
                             group_col: str = 'alloy_family',
                             test_size: float = 0.2,
                             val_size: float = 0.1) -> Dict[str, pd.DataFrame]:
    """
    Perform standard stratified train/val/test split by alloy_family.
    Only used if N >= 100.
    """
    from sklearn.model_selection import train_test_split
    
    logger.info(f"Performing stratified split by '{group_col}'.")
    
    # First split: Train+Val vs Test
    temp_train_val, test = train_test_split(
        df, 
        test_size=test_size, 
        stratify=df[group_col], 
        random_state=42
    )
    
    # Second split: Train vs Val
    # Adjust val_size relative to the remaining data
    val_ratio = val_size / (1 - test_size)
    
    train, val = train_test_split(
        temp_train_val,
        test_size=val_ratio,
        stratify=temp_train_val[group_col],
        random_state=42
    )
    
    logger.info(f"Split sizes - Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
    
    return {
        'train': train,
        'val': val,
        'test': test
    }

def split_data(df: pd.DataFrame, 
               target_col: str, 
               group_col: str = 'alloy_family',
               min_samples: int = 100) -> Dict[str, any]:
    """
    Orchestrates the data splitting strategy based on dataset size.
    
    If N < min_samples: Uses LOAFO.
    If N >= min_samples: Uses Stratified Split.
    """
    n_samples = len(df)
    logger.info(f"Dataset size: {n_samples}. Threshold: {min_samples}.")
    
    if n_samples < min_samples:
        logger.info("Using LOAFO strategy (N < 100).")
        splits = perform_loafo_split(df, target_col, group_col)
        return {
            'strategy': 'LOAFO',
            'splits': splits,
            'min_samples': min_samples
        }
    else:
        logger.info("Using Stratified Split strategy (N >= 100).")
        splits = perform_stratified_split(df, target_col, group_col)
        return {
            'strategy': 'Stratified',
            'splits': splits,
            'min_samples': min_samples
        }

def save_split_artifacts(split_result: Dict[str, any], output_dir: Path = SPLIT_OUTPUT_DIR) -> None:
    """
    Saves the split artifacts to disk.
    For LOAFO, saves a JSON summary of the fold structure and the actual splits as CSVs.
    For Stratified, saves train/val/test CSVs.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    strategy = split_result['strategy']
    splits = split_result['splits']
    
    logger.info(f"Saving {strategy} split artifacts to {output_dir}")
    
    if strategy == 'LOAFO':
        summary = {
            'strategy': 'LOAFO',
            'total_folds': len(splits),
            'folds': []
        }
        
        for i, fold in enumerate(splits):
            fold_id = f"fold_{i}"
            train_path = output_dir / f"{fold_id}_train.csv"
            test_path = output_dir / f"{fold_id}_test.csv"
            
            fold['train'].to_csv(train_path, index=False)
            fold['test'].to_csv(test_path, index=False)
            
            summary['folds'].append({
                'fold_id': fold_id,
                'left_out_group': fold['left_out_group'],
                'train_path': str(train_path),
                'test_path': str(test_path),
                'train_size': len(fold['train']),
                'test_size': len(fold['test'])
            })
        
        import json
        summary_path = output_dir / "loafo_splits.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved LOAFO summary to {summary_path}")
        
    elif strategy == 'Stratified':
        for key, data in splits.items():
            path = output_dir / f"{key}.csv"
            data.to_csv(path, index=False)
            logger.info(f"Saved {key} set to {path} (n={len(data)})")

def main():
    """
    Main entry point for preprocessing tasks including VIF analysis and data splitting.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load Data
    if not CURATED_DATA_PATH.exists():
        logger.error(f"Curated data not found at {CURATED_DATA_PATH}.")
        sys.exit(1)
    
    df = pd.read_csv(CURATED_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from {CURATED_DATA_PATH}")
    
    # 2. Verify Integrity
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'ductility', 'alloy_family']
    if not verify_column_integrity(df, required_cols):
        logger.error("Column integrity check failed.")
        sys.exit(1)
    
    # 3. Calculate Energy Density
    df = calculate_energy_density(df)
    logger.info("Calculated energy density.")
    
    # 4. VIF Analysis
    features_for_vif = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
    # Filter to only existing columns if needed, though we just verified
    features_for_vif = [c for c in features_for_vif if c in df.columns]
    
    try:
        df, final_features = perform_vif_analysis(df, features_for_vif, threshold=5.0)
        logger.info(f"Final features after VIF analysis: {final_features}")
    except RuntimeError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # 5. Data Splitting (T043: LOAFO Validation)
    # Target is 'ductility'
    split_result = split_data(df, target_col='ductility', group_col='alloy_family', min_samples=100)
    
    # 6. Save Artifacts
    save_split_artifacts(split_result)
    
    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()