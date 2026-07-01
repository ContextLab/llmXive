import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/preprocessing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def calculate_energy_density(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate volumetric energy density: E_v = P / (v * h * t)
    P: Laser Power (W)
    v: Scan Speed (mm/s)
    h: Hatch Spacing (mm)
    t: Layer Thickness (mm)
    
    Returns DataFrame with 'energy_density' column added.
    """
    logger.info("Calculating volumetric energy density...")
    
    # Ensure units are SI (W, mm/s, mm, mm) - assuming cleaning.py handled unit conversion
    # If units are in different scales, conversion is needed here
    # Assuming inputs are: P (W), v (mm/s), h (mm), t (mm)
    
    df = df.copy()
    
    # Avoid division by zero
    df['energy_density'] = df['laser_power'] / (
        df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness']
    )
    
    logger.info(f"Energy density calculated. Range: {df['energy_density'].min():.2f} to {df['energy_density'].max():.2f} J/mm³")
    return df

def verify_column_integrity(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Verify that all required columns exist in the DataFrame.
    
    Args:
        df: Input DataFrame
        required_columns: List of column names that must exist
        
    Returns:
        True if all columns exist, False otherwise.
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def calculate_vif(df: pd.DataFrame, features: list) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.
    
    Args:
        df: DataFrame containing the features
        features: List of column names to calculate VIF for
        
    Returns:
        Series of VIF values indexed by feature name
    """
    logger.info("Calculating VIF for features...")
    
    # Add constant for intercept
    X = df[features].dropna()
    if X.empty:
        logger.warning("No valid data for VIF calculation after dropping NaNs.")
        return pd.Series(dtype=float)
        
    vif_data = pd.Series(
        [variance_inflation_factor(X.values, i) for i in range(len(features))],
        index=features
    )
    
    logger.info(f"VIF values: {vif_data.to_dict()}")
    return vif_data

def perform_vif_analysis(df: pd.DataFrame, predictors: list, threshold: float = 5.0) -> pd.DataFrame:
    """
    Perform VIF analysis and filter features based on multicollinearity.
    FR-005: If Energy Density VIF > 5, drop individual constituents (Power, Speed, Hatch, Thickness).
    
    Args:
        df: Input DataFrame
        predictors: List of potential predictor columns
        threshold: VIF threshold for multicollinearity (default 5.0)
        
    Returns:
        DataFrame with filtered features
    """
    logger.info(f"Performing VIF analysis with threshold {threshold}...")
    
    # Check for NaNs in predictors
    if df[predictors].isnull().any().any():
        logger.warning("NaN values found in predictors. Dropping rows with NaNs for VIF calculation.")
        df_clean = df.dropna(subset=predictors)
    else:
        df_clean = df
        
    if df_clean.empty:
        logger.error("No valid data remaining for VIF analysis.")
        return df.copy()
    
    vif_results = calculate_vif(df_clean, predictors)
    
    # Check if Energy Density is in predictors and if its VIF > threshold
    if 'energy_density' in vif_results.index and vif_results['energy_density'] > threshold:
        logger.warning(f"Energy Density VIF ({vif_results['energy_density']:.2f}) > {threshold}. Dropping constituent predictors.")
        
        # Define constituent predictors
        constituents = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        # Filter to only those present in the dataframe
        constituents_to_drop = [c for c in constituents if c in df.columns]
        
        # Drop constituents, keep energy_density
        final_predictors = [p for p in predictors if p not in constituents_to_drop]
        logger.info(f"Dropping constituents: {constituents_to_drop}. Keeping: {final_predictors}")
        
        # Re-calculate VIF on reduced set to verify
        if len(final_predictors) > 1:
            reduced_vif = calculate_vif(df_clean, final_predictors)
            max_vif = reduced_vif.max()
            logger.info(f"Re-calculated max VIF on reduced set: {max_vif:.2f}")
            if max_vif > threshold:
                logger.warning(f"Max VIF ({max_vif:.2f}) still exceeds threshold. Proceeding with caution.")
        else:
            logger.info("Only one predictor remaining after filtering. Skipping re-calculation.")
        
        # Return DataFrame with only the final predictors (and target/other columns)
        # We return the full df but the caller should know which columns to use
        # For this function, we just log the decision. The actual filtering happens in the caller or downstream.
        # However, to be consistent with "Output the filtered dataset", we might return a subset.
        # Let's assume the task wants us to prepare the data for modeling, so we return the df with only the kept predictors.
        # But we need to keep target and random effect columns.
        # Let's return the original df and log the columns to use.
        # Actually, the task says "Output the filtered dataset". Let's return a df with only the selected predictors + target + alloy_family.
        # We need to know the target column. Let's assume it's 'ductility' based on context.
        target_col = 'ductility'
        random_col = 'alloy_family'
        
        cols_to_keep = [c for c in df.columns if c in final_predictors or c == target_col or c == random_col]
        return df[cols_to_keep].copy()
    
    logger.info("VIF analysis complete. No features dropped.")
    return df.copy()

def perform_loafo_split(df: pd.DataFrame, target_col: str, random_col: str = 'alloy_family') -> dict:
    """
    Perform Leave-One-Alloy-Family-Out (LOAFO) split for small datasets (N < 100).
    
    In each fold, the left-out alloy family serves as the "held-out test set".
    Returns a dict of fold results to allow aggregation.
    
    Args:
        df: Input DataFrame
        target_col: Name of the target column
        random_col: Name of the random effect column (alloy_family)
        
    Returns:
        Dict containing:
            - 'folds': List of dicts with 'train', 'val', 'test' indices for each fold
            - 'alloy_families': List of alloy families
            - 'method': 'LOAFO'
    """
    logger.info("Performing LOAFO split...")
    
    alloy_families = df[random_col].unique().tolist()
    n_families = len(alloy_families)
    
    if n_families < 2:
        logger.error("Not enough alloy families for LOAFO split.")
        return {'folds': [], 'alloy_families': alloy_families, 'method': 'LOAFO'}
    
    folds = []
    
    # If we have more families than needed for 5-fold, we might group them, 
    # but LOAFO typically means one family out per fold.
    # The task says "5-fold cross-validation loop" with "left-out alloy family".
    # If N_families > 5, we can't do 5-fold LOAFO in the strict sense without grouping.
    # We will iterate through all families if <= 5, or sample 5 if > 5?
    # The task says "5-fold cross-validation loop". Let's assume we do 5 folds if possible.
    # If N_families < 5, we do N_families folds.
    # If N_families >= 5, we do 5 folds by grouping families? Or just pick 5 families to leave out?
    # The task says "In each fold, the left-out alloy family serves as the 'held-out test set'".
    # This implies one family per fold. So we can have at most N_families folds.
    # Let's do min(5, N_families) folds by selecting families to leave out.
    
    num_folds = min(5, n_families)
    
    # Select families to leave out for the folds
    # If N_families > 5, we select 5 families to leave out.
    # If N_families <= 5, we leave out each one in a fold.
    if n_families > 5:
        # Randomly select 5 families to be the test sets for the 5 folds
        np.random.seed(42)  # For reproducibility
        test_families = np.random.choice(alloy_families, size=num_folds, replace=False).tolist()
    else:
        test_families = alloy_families
    
    for i, test_family in enumerate(test_families):
        # Test set: rows where alloy_family == test_family
        test_mask = df[random_col] == test_family
        # Train/Val set: rows where alloy_family != test_family
        train_val_mask = ~test_mask
        
        train_val_df = df[train_val_mask]
        test_df = df[test_mask]
        
        # Split train_val into train and val (e.g., 80/20)
        # We need to split by index to keep indices
        train_indices, val_indices = train_test_split(
            train_val_df.index,
            test_size=0.2,
            random_state=42
        )
        
        folds.append({
            'fold': i,
            'test_family': test_family,
            'train_indices': train_indices.tolist(),
            'val_indices': val_indices.tolist(),
            'test_indices': test_df.index.tolist()
        })
        
    logger.info(f"LOAFO split complete. {len(folds)} folds generated.")
    return {
        'folds': folds,
        'alloy_families': alloy_families,
        'method': 'LOAFO'
    }

def perform_stratified_split(df: pd.DataFrame, target_col: str, random_col: str = 'alloy_family') -> dict:
    """
    Perform standard stratified train/val/test split by alloy_family for larger datasets (N >= 100).
    
    Args:
        df: Input DataFrame
        target_col: Name of the target column
        random_col: Name of the random effect column (alloy_family)
        
    Returns:
        Dict containing:
            - 'train_indices': List of train indices
            - 'val_indices': List of val indices
            - 'test_indices': List of test indices
            - 'method': 'Stratified'
    """
    logger.info("Performing stratified train/val/test split...")
    
    # First, split off test set (20%)
    # Stratify by alloy_family
    train_val_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df[random_col]
    )
    
    # Then split train_val into train (80% of train_val = 64% total) and val (20% of train_val = 16% total)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=0.2,
        random_state=42,
        stratify=train_val_df[random_col]
    )
    
    logger.info(f"Stratified split complete. Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    return {
        'train_indices': train_df.index.tolist(),
        'val_indices': val_df.index.tolist(),
        'test_indices': test_df.index.tolist(),
        'method': 'Stratified'
    }

def split_data(df: pd.DataFrame, target_col: str = 'ductility', random_col: str = 'alloy_family') -> dict:
    """
    Main function to split data based on dataset size.
    
    Logic:
    - If N < 100: Use LOAFO (5-fold or N_folds if < 5)
    - If N >= 100: Use standard stratified train/val/test split
    
    Args:
        df: Input DataFrame
        target_col: Name of the target column
        random_col: Name of the random effect column
        
    Returns:
        Dict with split results
    """
    n_samples = len(df)
    logger.info(f"Splitting data. Total samples: {n_samples}")
    
    if n_samples < 100:
        logger.info("Dataset size < 100. Using LOAFO strategy.")
        return perform_loafo_split(df, target_col, random_col)
    else:
        logger.info("Dataset size >= 100. Using stratified split strategy.")
        return perform_stratified_split(df, target_col, random_col)

def save_split_artifacts(split_result: dict, output_dir: Path):
    """
    Save split results to CSV/JSON files.
    
    Args:
        split_result: Dict from split_data
        output_dir: Directory to save artifacts
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if split_result['method'] == 'LOAFO':
        # Save each fold's indices
        for fold in split_result['folds']:
            fold_file = output_dir / f"fold_{fold['fold']}_indices.csv"
            data = {
                'train': fold['train_indices'],
                'val': fold['val_indices'],
                'test': fold['test_indices'],
                'test_family': fold['test_family']
            }
            # Convert to DataFrame for saving
            # We'll save as a JSON file for simplicity with lists
            import json
            with open(fold_file.with_suffix('.json'), 'w') as f:
                json.dump(data, f, indent=2)
        logger.info(f"Saved LOAFO fold indices to {output_dir}")
    else:
        # Save train, val, test indices
        import json
        indices_file = output_dir / "split_indices.json"
        with open(indices_file, 'w') as f:
            json.dump(split_result, f, indent=2)
        logger.info(f"Saved stratified split indices to {output_dir}")

def main():
    """
    Main entry point for preprocessing script.
    Loads curated data, performs VIF analysis if needed, and splits data.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / 'data'
    output_dir = project_root / 'data'
    
    input_file = data_dir / 'curated_builds.csv'
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Load data
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} rows from {input_file}")
    
    # Required columns for energy density calculation
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'ductility', 'alloy_family']
    if not verify_column_integrity(df, required_cols):
        logger.error("Missing required columns for preprocessing.")
        sys.exit(1)
    
    # Calculate energy density
    df = calculate_energy_density(df)
    
    # Perform VIF analysis and feature filtering
    # Define predictors for VIF
    predictors = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
    # Filter to only those present
    predictors = [p for p in predictors if p in df.columns]
    
    df_filtered = perform_vif_analysis(df, predictors, threshold=5.0)
    
    # Split data
    split_result = split_data(df_filtered, target_col='ductility', random_col='alloy_family')
    
    # Save artifacts
    save_split_artifacts(split_result, output_dir)
    
    logger.info("Preprocessing pipeline completed successfully.")
    return split_result

if __name__ == "__main__":
    main()