import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, LeaveOneGroupOut, StratifiedKFold
from sklearn.preprocessing import StandardScaler
import json
import pickle

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
    Calculate volumetric energy density: E_v = P / (v * h * t).
    
    Parameters:
        df: DataFrame with columns laser_power (W), scan_speed (mm/s), 
            hatch_spacing (mm), layer_thickness (mm).
            
    Returns:
        DataFrame with added 'energy_density' column (J/mm^3).
    """
    if not all(col in df.columns for col in ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']):
        missing = [c for c in ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness'] if c not in df.columns]
        raise ValueError(f"Missing required columns for energy density calculation: {missing}")
    
    # Prevent division by zero
    df = df.copy()
    df['scan_speed'] = df['scan_speed'].replace(0, np.nan)
    df['hatch_spacing'] = df['hatch_spacing'].replace(0, np.nan)
    df['layer_thickness'] = df['layer_thickness'].replace(0, np.nan)
    
    df['energy_density'] = df['laser_power'] / (df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness'])
    
    logger.info(f"Calculated energy density for {len(df)} records.")
    return df

def verify_column_integrity(df: pd.DataFrame) -> bool:
    """
    Verify that essential columns exist and have no critical missing values.
    """
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'ductility', 'alloy_family']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    if df['ductility'].isnull().any():
        logger.warning("Found missing ductility values.")
        return False
        
    logger.info("Column integrity verified.")
    return True

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for a list of features.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    X = df[features].dropna()
    if X.empty:
        return pd.Series(dtype=float)
        
    # Add constant for intercept
    X_const = sm.add_constant(X)
    vif_data = pd.Series([variance_inflation_factor(X_const.values, i) 
                          for i in range(X_const.shape[1])], 
                         index=X_const.columns)
    return vif_data

def perform_vif_analysis(df: pd.DataFrame, predictors: list) -> dict:
    """
    Perform VIF analysis and apply FR-005 logic:
    If Energy Density VIF > 5, drop individual constituents (Power, Speed, Hatch, Thickness)
    and retain only Energy Density.
    """
    import statsmodels.api as sm
    
    # Ensure we have the necessary columns
    required = predictors + ['energy_density']
    available = [c for c in required if c in df.columns]
    
    if 'energy_density' not in available:
        logger.warning("Energy density not in available predictors, skipping VIF logic.")
        return {"final_predictors": predictors, "dropped": [], "vif_report": {}}

    # Calculate initial VIFs
    try:
        vif_report = calculate_vif(df, available)
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        return {"final_predictors": predictors, "dropped": [], "vif_report": {}}

    ed_vif = vif_report.get('energy_density', 0)
    
    dropped = []
    final_predictors = predictors.copy()
    
    # FR-005 Logic
    if ed_vif > 5.0:
        constituents = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        to_drop = [c for c in constituents if c in final_predictors]
        if to_drop:
            final_predictors = [c for c in final_predictors if c not in to_drop]
            dropped = to_drop
            logger.info(f"FR-005 triggered: Energy Density VIF ({ed_vif:.2f}) > 5.0. "
                        f"Dropping constituents: {dropped}. Retaining Energy Density.")
    else:
        logger.info(f"Energy Density VIF ({ed_vif:.2f}) <= 5.0. Keeping all predictors.")

    return {
        "final_predictors": final_predictors,
        "dropped": dropped,
        "vif_report": vif_report.to_dict()
    }

def perform_loafo_split(df: pd.DataFrame, target_col: str, group_col: str = 'alloy_family'):
    """
    Perform Leave-One-Alloy-Family-Out (LOAFO) split.
    Yields (train_df, test_df) for each fold where the test set is a unique alloy family.
    """
    groups = df[group_col].unique()
    logger.info(f"Performing LOAFO split with {len(groups)} alloy families.")
    
    for group in groups:
        test_mask = df[group_col] == group
        train_mask = ~test_mask
        
        yield df[train_mask].reset_index(drop=True), df[test_mask].reset_index(drop=True)

def perform_stratified_split(df: pd.DataFrame, target_col: str, group_col: str = 'alloy_family', 
                             test_size: float = 0.2, val_size: float = 0.15):
    """
    Perform standard stratified train/val/test split by alloy_family.
    """
    # First split: Train+Val vs Test
    # We stratify by alloy_family to ensure representation
    train_val_df, test_df = train_test_split(
        df, 
        test_size=test_size, 
        stratify=df[group_col],
        random_state=42
    )
    
    # Second split: Train vs Val from the remaining
    # Adjust ratio for the second split to achieve overall val_size
    # If total N=100, test=20, left=80. val_size=0.15 -> 15 total. 15/80 = 0.1875
    if len(train_val_df) > 0:
        val_ratio = val_size / (1 - test_size)
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=val_ratio,
            stratify=train_val_df[group_col],
            random_state=42
        )
    else:
        train_df, val_df = pd.DataFrame(), pd.DataFrame()

    return train_df, val_df, test_df

def split_data(df: pd.DataFrame, target_col: str = 'ductility', group_col: str = 'alloy_family'):
    """
    Main entry point for data splitting logic.
    Logic:
      If N < 100: Use LOAFO (yields multiple train/test pairs).
      If N >= 100: Use standard stratified split (train, val, test).
      
    Returns:
      If N < 100: List of tuples [(train_df, test_df), ...]
      If N >= 100: Tuple (train_df, val_df, test_df)
    """
    n = len(df)
    logger.info(f"Starting data split. N={n}, Threshold=100.")
    
    if n < 100:
        logger.info("Dataset size < 100. Switching to LOAFO strategy.")
        return list(perform_loafo_split(df, target_col, group_col))
    else:
        logger.info("Dataset size >= 100. Using standard stratified split.")
        return perform_stratified_split(df, target_col, group_col)

def save_split_artifacts(splits: list, output_dir: str = "data"):
    """
    Save split data artifacts to disk.
    For LOAFO: Saves multiple files like data/loafo_fold_0_train.csv, data/loafo_fold_0_test.csv, etc.
    For Stratified: Saves data/train.csv, data/val.csv, data/test.csv.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if isinstance(splits, list):
        # LOAFO case
        logger.info(f"Saving {len(splits)} LOAFO folds.")
        for i, (train_df, test_df) in enumerate(splits):
            train_path = output_path / f"loafo_fold_{i}_train.csv"
            test_path = output_path / f"loafo_fold_{i}_test.csv"
            train_df.to_csv(train_path, index=False)
            test_df.to_csv(test_path, index=False)
            logger.info(f"Saved fold {i}: {train_path}, {test_path}")
    else:
        # Stratified case
        train_df, val_df, test_df = splits
        train_path = output_path / "train.csv"
        val_path = output_path / "val.csv"
        test_path = output_path / "test.csv"
        
        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)
        logger.info(f"Saved stratified splits: {train_path}, {val_path}, {test_path}")

def main():
    """
    Main execution function for preprocessing and splitting.
    Reads data/curated_builds.csv, performs VIF analysis, splits data, and saves artifacts.
    """
    input_file = Path("data/curated_builds.csv")
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Ensure required columns exist (assuming cleaning/preprocessing steps before this)
    if 'energy_density' not in df.columns:
        logger.info("Calculating energy density...")
        df = calculate_energy_density(df)
    
    # Define predictors for VIF analysis
    predictors = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
    # Filter to only those present in df
    predictors = [p for p in predictors if p in df.columns]
    
    logger.info("Performing VIF analysis...")
    vif_results = perform_vif_analysis(df, predictors)
    logger.info(f"Final predictors for modeling: {vif_results['final_predictors']}")
    
    # Save VIF results for reference
    vif_log = Path("data/vif_analysis.json")
    with open(vif_log, 'w') as f:
        json.dump(vif_results, f, indent=2, default=str)
    
    # Perform splitting
    logger.info("Splitting data...")
    splits = split_data(df)
    
    # Save artifacts
    save_split_artifacts(splits)
    
    logger.info("Preprocessing and splitting complete.")

if __name__ == "__main__":
    main()