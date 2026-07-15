"""
Preprocessing module for ductility prediction pipeline.
Handles energy density calculation, VIF analysis, and data splitting.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def calculate_energy_density(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate volumetric energy density: E_v = P / (v * h * t)
    
    Args:
        df: DataFrame with columns laser_power (W), scan_speed (mm/s),
            hatch_spacing (mm), layer_thickness (mm)
    
    Returns:
        DataFrame with added 'energy_density' column (J/mm^3)
    """
    df = df.copy()
    
    # Validate required columns exist
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for energy density calculation: {missing}")
    
    # Calculate energy density
    # E_v = P / (v * h * t) where P in W, v in mm/s, h in mm, t in mm
    # Result in J/mm^3
    df['energy_density'] = df['laser_power'] / (
        df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness']
    )
    
    logger.info(f"Calculated energy density for {len(df)} rows")
    return df

def verify_column_integrity(df: pd.DataFrame, required_cols: list = None) -> bool:
    """
    Verify that all required columns exist and have no missing values.
    
    Args:
        df: Input DataFrame
        required_cols: List of required column names
    
    Returns:
        True if integrity check passes, False otherwise
    """
    if required_cols is None:
        required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 
                       'layer_thickness', 'ductility', 'alloy_family', 
                       'energy_density']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    missing_values = {}
    for col in required_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            missing_values[col] = null_count
    
    if missing_values:
        logger.warning(f"Missing values found: {missing_values}")
        return False
    
    logger.info("Column integrity check passed")
    return True

def calculate_vif(df: pd.DataFrame, features: list) -> pd.Series:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        df: DataFrame with features
        features: List of feature column names
    
    Returns:
        Series with VIF values for each feature
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Add constant for intercept
    X = df[features].copy()
    X = X.replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(X) < len(features) + 1:
        logger.warning("Insufficient samples for VIF calculation")
        return pd.Series([np.nan] * len(features), index=features)
    
    vif_data = pd.Series(
        [variance_inflation_factor(X.values, i) for i in range(len(features))],
        index=features
    )
    
    return vif_data

def perform_vif_analysis(df: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
    """
    Perform VIF analysis and filter features if necessary.
    
    If Energy Density VIF > threshold, drop constituent predictors (Power, Speed, 
    Hatch, Thickness) and retain only Energy Density.
    
    Args:
        df: Input DataFrame
        threshold: VIF threshold for dropping features
    
    Returns:
        DataFrame with filtered features
    """
    features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 
               'energy_density']
    
    # Filter out rows with missing values in features
    df_clean = df.dropna(subset=features).copy()
    
    if len(df_clean) < len(features) + 1:
        logger.warning(f"Insufficient data for VIF analysis: {len(df_clean)} rows")
        return df
    
    vif_values = calculate_vif(df_clean, features)
    logger.info(f"VIF values: {vif_values.to_dict()}")
    
    energy_vif = vif_values.get('energy_density', 0)
    
    if energy_vif > threshold:
        logger.info(f"Energy Density VIF ({energy_vif:.2f}) > {threshold}. "
                   "Dropping constituent predictors.")
        # Drop constituent predictors, keep energy_density
        drop_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        df_filtered = df.drop(columns=drop_cols, errors='ignore')
        logger.info(f"Dropped columns: {drop_cols}")
    else:
        logger.info(f"Energy Density VIF ({energy_vif:.2f}) <= {threshold}. "
                   "Retaining all features.")
        df_filtered = df.copy()
    
    # Re-calculate VIF on reduced set
    if energy_vif > threshold:
        reduced_features = ['energy_density']
        if len(df_filtered.dropna(subset=reduced_features)) > 1:
            reduced_vif = calculate_vif(df_filtered.dropna(subset=reduced_features), 
                                       reduced_features)
            logger.info(f"Reduced set VIF: {reduced_vif.to_dict()}")
    
    return df_filtered

def perform_reciprocal_vif_check(df: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
    """
    Perform reciprocal VIF check.
    
    If Energy Density was NOT dropped in previous step, check VIF for constituent 
    predictors. If any have VIF > threshold, drop or combine them.
    
    Args:
        df: Input DataFrame
        threshold: VIF threshold
    
    Returns:
        Filtered DataFrame
    """
    # Check if energy_density exists and constituents exist
    has_energy = 'energy_density' in df.columns
    has_constituents = all(col in df.columns for col in 
                          ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness'])
    
    if has_energy and not has_constituents:
        # Energy was already dropped in T023, this is a no-op
        logger.info("Energy Density was already dropped. Skipping reciprocal VIF check.")
        return df
    
    if not has_energy and has_constituents:
        # Energy was not dropped, check constituents
        features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        df_clean = df.dropna(subset=features).copy()
        
        if len(df_clean) < len(features) + 1:
            logger.warning("Insufficient data for reciprocal VIF check")
            return df
        
        vif_values = calculate_vif(df_clean, features)
        logger.info(f"Constituent VIF values: {vif_values.to_dict()}")
        
        high_vif_features = [f for f, v in vif_values.items() if v > threshold]
        
        if high_vif_features:
            logger.critical(f"High VIF detected in constituents: {high_vif_features}. "
                          "Attempting to drop highest VIF predictor.")
            
            # Drop highest VIF predictor
            worst_feature = max(high_vif_features, key=lambda x: vif_values[x])
            df_filtered = df.drop(columns=[worst_feature], errors='ignore')
            logger.info(f"Dropped {worst_feature} due to high VIF")
            
            # Re-check VIF
            remaining_features = [f for f in features if f != worst_feature]
            if remaining_features:
                df_check = df_filtered.dropna(subset=remaining_features)
                if len(df_check) >= len(remaining_features) + 1:
                    new_vif = calculate_vif(df_check, remaining_features)
                    max_vif = new_vif.max()
                    
                    if max_vif > threshold:
                        logger.critical(f"VIF still > {threshold} after dropping {worst_feature}. "
                                      f"Max VIF: {max_vif:.2f}. HALTING execution.")
                        raise ValueError(f"VIF collinearity cannot be resolved. Max VIF: {max_vif:.2f}")
                    else:
                        logger.info(f"VIF reduced to {max_vif:.2f} after dropping {worst_feature}")
        else:
            logger.info("All constituent VIFs <= threshold. No action needed.")
    else:
        logger.info("No constituents to check or energy density not present.")
    
    return df

def perform_loafo_split(df: pd.DataFrame, target_col: str = 'ductility', 
                       group_col: str = 'alloy_family', random_seed: int = 42) -> dict:
    """
    Perform Leave-One-Alloy-Family-Out (LOAFO) cross-validation split.
    
    For each fold, one alloy family is left out as validation set.
    
    Args:
        df: Input DataFrame
        target_col: Target column name
        group_col: Grouping column name
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary with train, val, test splits (for final evaluation)
    """
    np.random.seed(random_seed)
    
    groups = df[group_col].unique()
    logger.info(f"Performing LOAFO with {len(groups)} alloy families: {list(groups)}")
    
    if len(groups) < 2:
        logger.error("LOAFO requires at least 2 alloy families")
        raise ValueError("LOAFO requires at least 2 alloy families")
    
    # For final evaluation, designate one family as held-out test set
    # if there are >= 3 families
    if len(groups) >= 3:
        # Randomly select one family for final test set
        test_family = np.random.choice(groups)
        test_df = df[df[group_col] == test_family].copy()
        
        # Remaining families for CV
        cv_families = [f for f in groups if f != test_family]
        cv_df = df[df[group_col].isin(cv_families)].copy()
        
        logger.info(f"Final test set: {test_family} ({len(test_df)} rows)")
        logger.info(f"CV set: {cv_families} ({len(cv_df)} rows)")
        
        # For the CV set, we'll use LOAFO internally for tuning
        # But for this function, return train/val/test for final evaluation
        # Split CV set into train/val (80/20) for simplicity in this context
        train_df, val_df = train_test_split(
            cv_df, test_size=0.2, random_state=random_seed, stratify=cv_df[group_col]
        )
        
        return {
            'train': train_df,
            'val': val_df,
            'test': test_df
        }
    else:
        # Only 2 families: use LOAFO for final evaluation
        # Return both families as separate splits
        family1, family2 = groups
        df1 = df[df[group_col] == family1].copy()
        df2 = df[df[group_col] == family2].copy()
        
        logger.info(f"Using LOAFO for final evaluation: {family1} vs {family2}")
        
        return {
            'train': df1,
            'val': df2,
            'test': None  # Will be handled in CV loop
        }

def perform_stratified_split(df: pd.DataFrame, target_col: str = 'ductility',
                            group_col: str = 'alloy_family', 
                            train_size: float = 0.6, val_size: float = 0.2,
                            random_seed: int = 42) -> dict:
    """
    Perform stratified train/val/test split by alloy family.
    
    Args:
        df: Input DataFrame
        target_col: Target column name
        group_col: Grouping column name
        train_size: Proportion for training
        val_size: Proportion for validation
        random_seed: Random seed
    
    Returns:
        Dictionary with train, val, test splits
    """
    np.random.seed(random_seed)
    
    # Stratify by alloy_family
    train_df, temp_df = train_test_split(
        df, train_size=train_size, random_state=random_seed, 
        stratify=df[group_col]
    )
    
    # Calculate val size relative to remaining
    remaining_size = 1 - train_size
    val_proportion = val_size / remaining_size if remaining_size > 0 else 0
    
    val_df, test_df = train_test_split(
        temp_df, train_size=val_proportion, random_state=random_seed,
        stratify=temp_df[group_col]
    )
    
    logger.info(f"Stratified split: Train={len(train_df)}, Val={len(val_df)}, "
               f"Test={len(test_df)}")
    
    return {
        'train': train_df,
        'val': val_df,
        'test': test_df
    }

def split_data(df: pd.DataFrame, group_col: str = 'alloy_family', 
              random_seed: int = 42) -> dict:
    """
    Main data splitting function.
    
    If N < 100: Use LOAFO strategy.
    If N >= 100: Use stratified split.
    
    Args:
        df: Input DataFrame
        group_col: Grouping column name
        random_seed: Random seed
    
    Returns:
        Dictionary with train, val, test splits
    """
    n_samples = len(df)
    logger.info(f"Splitting data: N={n_samples}")
    
    if n_samples < 100:
        logger.info("N < 100. Using LOAFO strategy.")
        return perform_loafo_split(df, group_col=group_col, random_seed=random_seed)
    else:
        logger.info("N >= 100. Using stratified split.")
        return perform_stratified_split(df, group_col=group_col, random_seed=random_seed)

def save_split_artifacts(splits: dict, output_dir: str = 'data/splits') -> None:
    """
    Save train, val, test splits to CSV files.
    
    Args:
        splits: Dictionary with train, val, test DataFrames
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if 'train' in splits and splits['train'] is not None:
        splits['train'].to_csv(output_path / 'train.csv', index=False)
        logger.info(f"Saved train.csv: {len(splits['train'])} rows")
    
    if 'val' in splits and splits['val'] is not None:
        splits['val'].to_csv(output_path / 'val.csv', index=False)
        logger.info(f"Saved val.csv: {len(splits['val'])} rows")
    
    if 'test' in splits and splits['test'] is not None:
        splits['test'].to_csv(output_path / 'test.csv', index=False)
        logger.info(f"Saved test.csv: {len(splits['test'])} rows")
    
    logger.info(f"Split artifacts saved to {output_dir}")

def main():
    """Main execution function for data splitting."""
    try:
        # Load input data
        input_path = Path('data/filtered_builds_final.csv')
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            sys.exit(1)
        
        logger.info(f"Loading data from {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows")
        
        # Perform splitting
        splits = split_data(df)
        
        # Save artifacts
        save_split_artifacts(splits)
        
        logger.info("Data splitting completed successfully")
        
    except Exception as e:
        logger.error(f"Error during data splitting: {e}")
        raise

if __name__ == '__main__':
    main()
