"""
Data Preprocessing Module.
Calculates energy density, performs VIF analysis, and splits data.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_energy_density(df):
    """Calculate volumetric energy density: Ev = P / (v * h * t)."""
    logger.info("Calculating energy density...")
    # Ensure columns are float
    df['laser_power'] = pd.to_numeric(df['laser_power'], errors='coerce')
    df['scan_speed'] = pd.to_numeric(df['scan_speed'], errors='coerce')
    df['hatch_spacing'] = pd.to_numeric(df['hatch_spacing'], errors='coerce')
    df['layer_thickness'] = pd.to_numeric(df['layer_thickness'], errors='coerce')
    
    # Avoid division by zero
    df['energy_density'] = df.apply(
        lambda row: row['laser_power'] / (row['scan_speed'] * row['hatch_spacing'] * row['layer_thickness'])
        if row['scan_speed'] * row['hatch_spacing'] * row['layer_thickness'] > 0 else np.nan,
        axis=1
    )
    return df

def verify_column_integrity(df):
    """Verify column integrity."""
    logger.info("Verifying column integrity...")
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density', 'ductility']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.warning(f"Missing columns: {missing}")
    return df

def calculate_vif(df, features):
    """Calculate VIF for given features."""
    logger.info("Calculating VIF...")
    X = df[features].dropna()
    if X.empty:
        return {}
    vif_data = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
    return vif_data

def perform_vif_analysis(df):
    """Perform VIF analysis and feature filtering."""
    logger.info("Performing VIF analysis...")
    features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
    # Filter out rows with NaN in features
    df_clean = df[features].dropna()
    if df_clean.empty:
        logger.warning("No valid data for VIF analysis.")
        return df, features
    
    vif_data = calculate_vif(df_clean, features)
    logger.info(f"VIF Data: {vif_data}")
    
    # Logic: If Energy Density VIF > 5, drop components
    if vif_data.get('energy_density', 0) > 5:
        logger.warning("Energy Density VIF > 5. Dropping constituent predictors.")
        final_features = ['energy_density']
    else:
        final_features = features
    
    # Re-calculate VIF on reduced set
    if len(final_features) > 1:
        df_sub = df[final_features].dropna()
        if not df_sub.empty:
            vif_reduced = calculate_vif(df_sub, final_features)
            if any(v > 5 for v in vif_reduced.values()):
                logger.critical("Irreducible collinearity remains. Halting.")
                sys.exit(1)
    
    logger.info(f"Final features for modeling: {final_features}")
    return df, final_features

def perform_loafo_split(df, target_col='ductility', group_col='alloy_family'):
    """Perform Leave-One-Alloy-Family-Out split."""
    logger.info("Performing LOAFO split...")
    groups = df[group_col].unique()
    splits = []
    for group in groups:
        test_mask = df[group_col] == group
        train_mask = ~test_mask
        splits.append({
            'train': df[train_mask],
            'test': df[test_mask]
        })
    return splits

def perform_stratified_split(df, test_size=0.2):
    """Perform standard stratified split."""
    logger.info("Performing stratified split...")
    from sklearn.model_selection import train_test_split
    train, test = train_test_split(df, test_size=test_size, stratify=df['alloy_family'])
    return train, test

def split_data(df):
    """Split data based on dataset size."""
    logger.info("Splitting data...")
    if len(df) < 100:
        return perform_loafo_split(df)
    else:
        return perform_stratified_split(df)

def save_split_artifacts(splits, output_dir):
    """Save split artifacts."""
    logger.info("Saving split artifacts...")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, split in enumerate(splits):
        if isinstance(split, dict):
            split['train'].to_csv(output_dir / f"train_fold_{i}.csv", index=False)
            split['test'].to_csv(output_dir / f"test_fold_{i}.csv", index=False)
        else:
            split[0].to_csv(output_dir / f"train.csv", index=False)
            split[1].to_csv(output_dir / f"test.csv", index=False)

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting Preprocessing...")
    
    input_path = Path(__file__).parent.parent.parent / "data" / "curated_builds.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    
    df = calculate_energy_density(df)
    df = verify_column_integrity(df)
    df, final_features = perform_vif_analysis(df)
    
    # Save processed data
    output_path = Path(__file__).parent.parent.parent / "data" / "processed_data.csv"
    df.to_csv(output_path, index=False)
    
    logger.info("Preprocessing stage completed.")
    return df, final_features

if __name__ == "__main__":
    main()
