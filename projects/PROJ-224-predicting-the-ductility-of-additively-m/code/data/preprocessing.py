"""
Preprocessing module for ductility prediction pipeline.

Handles energy density calculation, VIF analysis, feature filtering,
and dataset splitting strategies (LOAFO vs Stratified).
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from sklearn.model_selection import train_test_split, GroupKFold, cross_val_score
from sklearn.linear_model import LinearRegression
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
PREPROCESSED_DIR = DATA_DIR / "preprocessed"
PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CURATED_FILE = DATA_DIR / "curated_builds.csv"
ENERGY_DENSITY_FILE = PREPROCESSED_DIR / "curated_builds_with_energy.csv"
VIF_FILTERED_FILE = PREPROCESSED_DIR / "vif_filtered_builds.csv"
SPLIT_TRAIN_FILE = PREPROCESSED_DIR / "train_set.csv"
SPLIT_TEST_FILE = PREPROCESSED_DIR / "test_set.csv"
SPLIT_VAL_FILE = PREPROCESSED_DIR / "val_set.csv"

def calculate_energy_density(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate volumetric energy density: E_v = P / (v * h * t)
    
    Args:
        df: DataFrame with columns laser_power (W), scan_speed (mm/s), 
            hatch_spacing (µm), layer_thickness (µm)
    
    Returns:
        DataFrame with added 'energy_density' column (J/mm^3)
    """
    logger.info("Calculating volumetric energy density...")
    
    # Ensure columns exist
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Convert units to consistent SI for calculation:
    # P: W (already SI)
    # v: mm/s (already SI for this context)
    # h: µm -> mm (divide by 1000)
    # t: µm -> mm (divide by 1000)
    # E_v = P / (v * (h/1000) * (t/1000)) = P / (v * h * t / 1e6) = (P * 1e6) / (v * h * t)
    
    df = df.copy()
    df['energy_density'] = (df['laser_power'] * 1e6) / (
        df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness']
    )
    
    logger.info(f"Energy density calculated. Range: [{df['energy_density'].min():.2f}, {df['energy_density'].max():.2f}] J/mm^3")
    return df

def verify_column_integrity(df: pd.DataFrame, required_cols: List[str]) -> Tuple[bool, List[str]]:
    """
    Verify that all required columns exist and have no NaN values in key predictors.
    
    Args:
        df: Input DataFrame
        required_cols: List of column names to check
    
    Returns:
        Tuple of (is_valid, list_of_missing_or_nan_columns)
    """
    missing = []
    for col in required_cols:
        if col not in df.columns:
            missing.append(col)
        elif df[col].isna().any():
            missing.append(f"{col} (has NaN)")
    
    return len(missing) == 0, missing

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        df: DataFrame containing features
        feature_cols: List of feature column names
    
    Returns:
        DataFrame with VIF values
    """
    logger.info("Calculating VIF for features...")
    
    # Handle constant columns
    X = df[feature_cols].dropna()
    if X.shape[0] < 2:
        logger.warning("Not enough samples to calculate VIF")
        return pd.DataFrame(index=feature_cols, columns=['VIF'], data=np.nan)
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_data = []
    for col in feature_cols:
        if col in X_with_const.columns:
            try:
                vif = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
                vif_data.append({'feature': col, 'VIF': vif})
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {col}: {e}")
                vif_data.append({'feature': col, 'VIF': np.nan})
    
    return pd.DataFrame(vif_data)

def apply_vif_filtering(df: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
    """
    Apply VIF-based feature filtering per FR-005.
    
    Logic:
    - Calculate VIF for Energy Density and its components (Power, Speed, Hatch, Thickness).
    - If Energy Density VIF > threshold, drop components and keep only Energy Density.
    - Otherwise, keep all.
    
    Args:
        df: Input DataFrame
        threshold: VIF threshold (default 5.0)
    
    Returns:
        Filtered DataFrame
    """
    logger.info("Applying VIF filtering...")
    
    # Define candidate features
    component_features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    energy_feature = 'energy_density'
    
    # Check if all required columns exist
    all_features = [f for f in component_features + [energy_feature] if f in df.columns]
    if len(all_features) < len(component_features) + 1:
        logger.warning("Missing required features for VIF analysis. Skipping filtering.")
        return df
    
    # Calculate VIF
    vif_df = calculate_vif(df, all_features)
    logger.info("VIF Results:\n%s", vif_df.to_string(index=False))
    
    # Check Energy Density VIF
    ed_vif = vif_df[vif_df['feature'] == energy_feature]['VIF'].values
    if len(ed_vif) == 0 or np.isnan(ed_vif[0]):
        logger.warning("Could not determine Energy Density VIF. Keeping all features.")
        return df
    
    ed_vif_val = ed_vif[0]
    logger.info(f"Energy Density VIF: {ed_vif_val:.2f}")
    
    if ed_vif_val > threshold:
        logger.info(f"Energy Density VIF ({ed_vif_val:.2f}) > {threshold}. Dropping component features.")
        # Drop component features
        filtered_df = df.drop(columns=component_features)
        # Verify Energy Density is still there
        if energy_feature not in filtered_df.columns:
            raise RuntimeError("Energy density was accidentally dropped.")
        return filtered_df
    else:
        logger.info(f"Energy Density VIF ({ed_vif_val:.2f}) <= {threshold}. Keeping all features.")
        return df

def split_dataset_loafo(df: pd.DataFrame, test_fraction: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Implement Leave-One-Alloy-Family-Out (LOAFO) split for small datasets (N < 100).
    
    Strategy:
    - Iterate through unique alloy families.
    - In each iteration, hold out one family as test, rest as train.
    - Aggregate metrics or return the split that best represents the distribution.
    - For this implementation, we perform a 5-fold LOAFO-like split where we
      select 5 distinct families to serve as test sets in a cross-validation loop,
      but for the single "final" split artifact, we choose the family that
      represents the median size or the first unique family if < 5 families exist.
    
    To satisfy the requirement of producing a single train/test/val split artifact:
    - We will identify the unique alloy families.
    - If N_families >= 5, we will reserve 1 family for test, split the rest into 80% train / 20% val.
    - If N_families < 5, we use the smallest family as test, split rest into train/val.
    
    Args:
        df: Input DataFrame
        test_fraction: Fraction of data to hold out (used for logic selection)
    
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    logger.info("Performing LOAFO-style split...")
    
    if 'alloy_family' not in df.columns:
        raise ValueError("Column 'alloy_family' not found for LOAFO split.")
    
    families = df['alloy_family'].unique()
    n_families = len(families)
    n_rows = len(df)
    
    logger.info(f"Dataset size: {n_rows}, Unique families: {n_families}")
    
    if n_families == 1:
        logger.warning("Only one alloy family found. Cannot perform LOAFO. Using random split.")
        return _random_split(df)
    
    # Strategy: Select one family for Test.
    # Prefer a family with median size to avoid extreme test sets, or the first if few.
    family_sizes = df.groupby('alloy_family').size()
    if n_families >= 3:
        # Pick a family that is not the largest or smallest to be representative
        sorted_families = family_sizes.sort_values()
        mid_idx = len(sorted_families) // 2
        test_family = sorted_families.index[mid_idx]
    else:
        # Just pick the first one if very few families
        test_family = families[0]
    
    logger.info(f"Selected test family for LOAFO: {test_family}")
    
    test_df = df[df['alloy_family'] == test_family]
    train_val_df = df[df['alloy_family'] != test_family]
    
    # Split train_val into train and val (80/20)
    if len(train_val_df) > 0:
        train_df, val_df = train_test_split(
            train_val_df, 
            test_size=0.2, 
            random_state=42,
            shuffle=True
        )
    else:
        train_df = pd.DataFrame()
        val_df = pd.DataFrame()
    
    logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    return train_df, val_df, test_df

def _random_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fallback random split if LOAFO is not feasible."""
    logger.warning("Falling back to random split.")
    train, temp = train_test_split(df, test_size=0.4, random_state=42, shuffle=True)
    val, test = train_test_split(temp, test_size=0.5, random_state=42, shuffle=True)
    return train, val, test

def split_dataset_stratified(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Standard stratified train/val/test split by alloy_family for N >= 100.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    logger.info("Performing stratified split...")
    
    if 'alloy_family' not in df.columns:
        raise ValueError("Column 'alloy_family' not found for stratified split.")
    
    # Split 60% train, 20% val, 20% test
    train_df, temp_df = train_test_split(
        df, 
        test_size=0.4, 
        random_state=42, 
        shuffle=True,
        stratify=df['alloy_family']
    )
    
    val_df, test_df = train_test_split(
        temp_df, 
        test_size=0.5, 
        random_state=42, 
        shuffle=True,
        stratify=temp_df['alloy_family']
    )
    
    logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    return train_df, val_df, test_df

def preprocess_and_save(df: pd.DataFrame, strategy: str = 'auto') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Main entry point for preprocessing: Energy Density -> VIF -> Split.
    
    Args:
        df: Input DataFrame
        strategy: 'auto', 'loafo', or 'stratified'
    
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Energy Density
    df = calculate_energy_density(df)
    df.to_csv(ENERGY_DENSITY_FILE, index=False)
    logger.info(f"Saved energy density file: {ENERGY_DENSITY_FILE}")
    
    # 2. VIF Filtering
    df = apply_vif_filtering(df)
    df.to_csv(VIF_FILTERED_FILE, index=False)
    logger.info(f"Saved VIF filtered file: {VIF_FILTERED_FILE}")
    
    # 3. Splitting
    n_rows = len(df)
    if strategy == 'auto':
        if n_rows < 100:
            logger.info(f"Dataset size {n_rows} < 100. Using LOAFO strategy.")
            train, val, test = split_dataset_loafo(df)
        else:
            logger.info(f"Dataset size {n_rows} >= 100. Using Stratified strategy.")
            train, val, test = split_dataset_stratified(df)
    elif strategy == 'loafo':
        train, val, test = split_dataset_loafo(df)
    elif strategy == 'stratified':
        train, val, test = split_dataset_stratified(df)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    # Save splits
    train.to_csv(SPLIT_TRAIN_FILE, index=False)
    val.to_csv(SPLIT_VAL_FILE, index=False)
    test.to_csv(SPLIT_TEST_FILE, index=False)
    
    logger.info(f"Saved splits to: {SPLIT_TRAIN_FILE}, {SPLIT_VAL_FILE}, {SPLIT_TEST_FILE}")
    return train, val, test

def main():
    """Main execution function."""
    logger.info("Running preprocessing main...")
    
    if not CURATED_FILE.exists():
        logger.error(f"Curated file not found: {CURATED_FILE}")
        logger.error("Please run acquisition and cleaning first.")
        return
    
    df = pd.read_csv(CURATED_FILE)
    logger.info(f"Loaded {len(df)} rows from {CURATED_FILE}")
    
    try:
        train, val, test = preprocess_and_save(df)
        logger.info("Preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()