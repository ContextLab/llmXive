"""
Data preprocessing module for the ductility prediction pipeline.
Handles energy density calculation, VIF analysis, and data splitting.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def calculate_energy_density(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate volumetric energy density: E_v = P / (v * h * t)."""
    logger.info("Calculating energy density")
    
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    if not all(col in df.columns for col in required_cols):
        logger.error("Missing required columns for energy density calculation")
        return df
    
    # E_v = P / (v * h * t)
    # Units: W / (mm/s * mm * mm) = J/mm^3
    df['energy_density'] = df['laser_power'] / (df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness'])
    
    logger.info(f"Calculated energy density for {len(df)} records")
    return df

def verify_column_integrity(df: pd.DataFrame) -> bool:
    """Verify that all required columns are present."""
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 
                    'ductility', 'alloy_family', 'energy_density']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing columns: {missing}")
        return False
    return True

def calculate_vif(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """Calculate VIF for a list of features."""
    vif_data = pd.DataFrame()
    vif_data["feature"] = features
    vif_data["VIF"] = [variance_inflation_factor(df[features].values, i) 
                      for i in range(len(features))]
    return vif_data

def perform_vif_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Perform VIF analysis and filter features."""
    logger.info("Performing VIF analysis")
    
    features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
    
    # Calculate initial VIF
    vif_df = calculate_vif(df, features)
    logger.info(f"Initial VIF:\n{vif_df}")
    
    # Check if energy density VIF > 5
    ev_vif = vif_df[vif_df['feature'] == 'energy_density']['VIF'].values[0]
    
    if ev_vif > 5:
        logger.info(f"Energy Density VIF ({ev_vif:.2f}) > 5. Dropping constituent predictors.")
        # Drop constituents, keep only energy density
        drop_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        df_filtered = df.drop(columns=drop_cols, errors='ignore')
        final_features = ['energy_density']
    else:
        logger.info(f"Energy Density VIF ({ev_vif:.2f}) <= 5. Keeping all features.")
        df_filtered = df
        final_features = features
    
    # Re-calculate VIF on reduced set
    if len(final_features) > 1:
        vif_df_final = calculate_vif(df_filtered, final_features)
        logger.info(f"Final VIF:\n{vif_df_final}")
        
        if vif_df_final['VIF'].max() > 5:
            logger.warning(f"Final VIF max ({vif_df_final['VIF'].max():.2f}) > 5. Proceeding with caution.")
    
    logger.info(f"Final predictors: {final_features}")
    return df_filtered

def perform_reciprocal_vif_check(df: pd.DataFrame) -> pd.DataFrame:
    """Perform reciprocal VIF check as per T023b."""
    logger.info("Performing reciprocal VIF check")
    
    # If energy density was kept (constituents dropped in T023), check constituents
    features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    present_features = [f for f in features if f in df.columns]
    
    if len(present_features) > 1:
        vif_df = calculate_vif(df, present_features)
        max_vif = vif_df['VIF'].max()
        
        if max_vif > 5:
            logger.critical(f"Reciprocal VIF check failed: max VIF = {max_vif:.2f}")
            logger.critical("Halt execution as per T023b requirements.")
            raise ValueError(f"Reciprocal VIF check failed: max VIF = {max_vif:.2f}")
    
    return df

def perform_loafo_split(df: pd.DataFrame, target_col: str = 'ductility'):
    """Perform Leave-One-Alloy-Family-Out split."""
    logger.info("Performing LOAFO split")
    
    alloy_families = df['alloy_family'].unique()
    if len(alloy_families) < 2:
        logger.error("Not enough alloy families for LOAFO")
        return None, None, None
    
    folds = []
    for family in alloy_families:
        test_mask = df['alloy_family'] == family
        train_mask = ~test_mask
        
        train_df = df[train_mask].copy()
        test_df = df[test_mask].copy()
        
        # Verify no leakage
        assert family not in train_df['alloy_family'].values, "Data leakage detected!"
        
        folds.append({
            'train': train_df,
            'test': test_df,
            'left_out': family
        })
        logger.info(f"LOAFO fold: left out {family}, train size={len(train_df)}, test size={len(test_df)}")
    
    return folds

def perform_stratified_split(df: pd.DataFrame, target_col: str = 'ductility'):
    """Perform stratified train/val/test split by alloy family."""
    logger.info("Performing stratified split")
    
    from sklearn.model_selection import train_test_split
    
    # First split: train+val vs test
    train_val, test = train_test_split(
        df, test_size=0.2, stratify=df['alloy_family'], random_state=42
    )
    
    # Second split: train vs val
    train, val = train_test_split(
        train_val, test_size=0.25, stratify=train_val['alloy_family'], random_state=42
    )
    
    logger.info(f"Split sizes: train={len(train)}, val={len(val)}, test={len(test)}")
    return train, val, test

def split_data(df: pd.DataFrame) -> tuple:
    """Split data based on dataset size."""
    n = len(df)
    
    if n < 100:
        logger.info(f"Dataset size ({n}) < 100. Using LOAFO.")
        # For evaluation, use the last fold's test set as held-out
        folds = perform_loafo_split(df)
        if folds:
            # Return the last fold as test, rest as train
            test_df = folds[-1]['test']
            train_df = pd.concat([f['train'] for f in folds[:-1]], ignore_index=True)
            val_df = pd.concat([f['train'] for f in folds[-2:-1]], ignore_index=True) if len(folds) > 1 else train_df.iloc[:10]
            return train_df, val_df, test_df
        else:
            return df, pd.DataFrame(), pd.DataFrame()
    else:
        logger.info(f"Dataset size ({n}) >= 100. Using stratified split.")
        return perform_stratified_split(df)

def save_split_artifacts(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame):
    """Save split data artifacts."""
    splits_dir = DATA_DIR / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    
    train_df.to_csv(splits_dir / "train.csv", index=False)
    val_df.to_csv(splits_dir / "val.csv", index=False)
    test_df.to_csv(splits_dir / "test.csv", index=False)
    
    logger.info(f"Saved split artifacts to {splits_dir}")

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting preprocessing")
    
    # Load input data
    input_path = DATA_DIR / "curated_builds.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # Calculate energy density
    df = calculate_energy_density(df)
    
    # Verify column integrity
    if not verify_column_integrity(df):
        logger.error("Column integrity check failed")
        sys.exit(1)
    
    # Save intermediate artifact
    intermediate_path = DATA_DIR / "curated_builds_features.csv"
    df.to_csv(intermediate_path, index=False)
    logger.info(f"Saved features to {intermediate_path}")
    
    # Perform VIF analysis
    df_filtered = perform_vif_analysis(df)
    
    # Perform reciprocal VIF check
    df_filtered = perform_reciprocal_vif_check(df_filtered)
    
    # Save filtered dataset
    filtered_path = DATA_DIR / "filtered_builds_final.csv"
    df_filtered.to_csv(filtered_path, index=False)
    logger.info(f"Saved filtered data to {filtered_path}")
    
    # Split data
    train_df, val_df, test_df = split_data(df_filtered)
    
    # Save split artifacts
    save_split_artifacts(train_df, val_df, test_df)
    
    return df_filtered

if __name__ == "__main__":
    main()
