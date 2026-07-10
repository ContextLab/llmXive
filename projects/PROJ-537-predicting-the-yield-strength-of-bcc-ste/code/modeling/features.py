import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from typing import Tuple, List, Dict, Any, Optional
import logging
from scipy import stats

logger = logging.getLogger(__name__)

def parse_element_column(df: pd.DataFrame, element_col: str) -> pd.DataFrame:
    """
    Parse a column containing element compositions (e.g., 'Fe 95.0, Cr 5.0')
    into separate columns for each element with their atomic fractions.
    """
    element_data = {}
    for _, row in df.iterrows():
        if pd.isna(row[element_col]):
            continue
        parts = str(row[element_col]).split(',')
        for part in parts:
            parts = part.strip().split()
            if len(parts) == 2:
                element, fraction = parts
                if element not in element_data:
                    element_data[element] = []
                element_data[element].append(float(fraction))
    
    # Create a new dataframe with element columns
    new_df = df.copy()
    for element, values in element_data.items():
        # Pad with NaN if necessary
        if len(values) < len(df):
            values.extend([np.nan] * (len(df) - len(values)))
        new_df[element] = values
    
    return new_df

def encode_composition(df: pd.DataFrame, element_cols: List[str]) -> pd.DataFrame:
    """
    Encode composition data into a feature matrix using one-hot encoding
    and atomic fractions.
    """
    # Normalize atomic fractions to sum to 1.0 for each row
    for col in element_cols:
        if col in df.columns:
            row_sums = df[col].sum(axis=1, skipna=True)
            # Avoid division by zero
            row_sums = row_sums.replace(0, 1)
            df[col] = df[col] / row_sums
    
    return df

def normalize_dft_descriptors(df: pd.DataFrame, descriptor_cols: List[str]) -> Tuple[pd.DataFrame, StandardScaler]:
    """
    Normalize DFT descriptors using StandardScaler.
    Returns the normalized dataframe and the fitted scaler.
    """
    scaler = StandardScaler()
    df_normalized = df.copy()
    
    # Only normalize columns that exist in the dataframe
    cols_to_normalize = [col for col in descriptor_cols if col in df.columns]
    if cols_to_normalize:
        df_normalized[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])
    
    return df_normalized, scaler

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors (VIF) for a set of features.
    VIF > 10 indicates high multicollinearity.
    
    Args:
        df: DataFrame containing the features
        feature_cols: List of column names to calculate VIF for
        
    Returns:
        Dictionary mapping feature names to their VIF values
    """
    # Filter to only include features that exist in the dataframe
    valid_features = [col for col in feature_cols if col in df.columns]
    
    if len(valid_features) < 2:
        logger.warning("Need at least 2 features to calculate VIF. Skipping VIF calculation.")
        return {col: np.nan for col in valid_features}
    
    # Remove rows with any NaN values in the features
    clean_df = df[valid_features].dropna()
    
    if len(clean_df) < len(valid_features) + 1:
        logger.warning("Not enough samples to calculate VIF reliably. Skipping VIF calculation.")
        return {col: np.nan for col in valid_features}
    
    vif_data = {}
    
    for i, feature in enumerate(valid_features):
        # Create a dataframe with the target feature and all other features
        other_features = [f for f in valid_features if f != feature]
        X = clean_df[other_features]
        y = clean_df[feature]
        
        # Check if there's enough variance in y
        if y.std() == 0:
            vif_data[feature] = np.inf
            continue
        
        # Fit a linear regression model
        try:
            # Add constant for intercept
            X_with_const = pd.concat([pd.Series(np.ones(len(X)), name='const'), X], axis=1)
            
            # Calculate R-squared
            # Using the formula: R^2 = 1 - (SS_res / SS_tot)
            # where SS_res = sum((y - y_pred)^2) and SS_tot = sum((y - y_mean)^2)
            
            # Simple OLS calculation
            X_matrix = X_with_const.values
            y_vector = y.values
            
            # (X'X)^-1 X'y
            try:
                beta = np.linalg.solve(X_matrix.T @ X_matrix, X_matrix.T @ y_vector)
                y_pred = X_matrix @ beta
                ss_res = np.sum((y_vector - y_pred) ** 2)
                ss_tot = np.sum((y_vector - y_vector.mean()) ** 2)
                
                if ss_tot == 0:
                    r_squared = 0
                else:
                    r_squared = 1 - (ss_res / ss_tot)
                
                # VIF = 1 / (1 - R^2)
                if r_squared >= 1.0:
                    vif_data[feature] = np.inf
                else:
                    vif_data[feature] = 1.0 / (1.0 - r_squared)
                    
            except np.linalg.LinAlgError:
                logger.warning(f"Singular matrix when calculating VIF for {feature}. Setting VIF to infinity.")
                vif_data[feature] = np.inf
                
        except Exception as e:
            logger.error(f"Error calculating VIF for {feature}: {e}")
            vif_data[feature] = np.nan
    
    return vif_data

def prepare_modeling_features(df: pd.DataFrame, 
                             element_cols: List[str], 
                             dft_cols: List[str],
                             target_col: str,
                             vif_threshold: float = 10.0) -> Tuple[pd.DataFrame, pd.Series, Dict[str, float]]:
    """
    Prepare features for modeling by encoding composition, normalizing DFT descriptors,
    and calculating VIF to detect multicollinearity.
    
    Args:
        df: Input dataframe
        element_cols: List of element composition column names
        dft_cols: List of DFT descriptor column names
        target_col: Name of the target variable column
        vif_threshold: Threshold above which features are considered multicollinear
        
    Returns:
        Tuple of (feature_matrix, target_series, vif_report)
    """
    # Parse element columns if they contain strings
    if element_cols and element_cols[0] in df.columns:
        # Check if the column contains strings that need parsing
        sample_val = df[element_cols[0]].iloc[0] if len(df) > 0 else None
        if isinstance(sample_val, str) and ',' in sample_val:
            df = parse_element_column(df, element_cols[0])
            # Update element_cols to include the new individual element columns
            new_element_cols = [col for col in df.columns if col not in df.columns[:df.columns.get_loc(element_cols[0]) + 1]]
            # Keep only the element columns that were parsed
            element_cols = [col for col in df.columns if col in df.columns and col != target_col and col not in dft_cols]
            # Filter to only numeric columns
            element_cols = [col for col in element_cols if pd.api.types.is_numeric_dtype(df[col])]
    
    # Encode composition
    df_encoded = encode_composition(df, element_cols)
    
    # Normalize DFT descriptors
    df_normalized, _ = normalize_dft_descriptors(df_encoded, dft_cols)
    
    # Select all feature columns (element + DFT)
    all_feature_cols = [col for col in df_normalized.columns 
                       if col not in [target_col] and col not in element_cols[:1] and col not in dft_cols[:1]]
    # Ensure we only have numeric columns
    all_feature_cols = [col for col in all_feature_cols if pd.api.types.is_numeric_dtype(df_normalized[col])]
    
    # Calculate VIF
    vif_report = calculate_vif(df_normalized, all_feature_cols)
    
    # Log multicollinearity warnings
    high_vif_features = {k: v for k, v in vif_report.items() if v > vif_threshold}
    if high_vif_features:
        logger.warning(f"High multicollinearity detected (VIF > {vif_threshold}): {high_vif_features}")
        for feature, vif_val in high_vif_features.items():
            logger.warning(f"Feature '{feature}' has VIF = {vif_val:.2f}")
    else:
        logger.info("No significant multicollinearity detected (all VIF < 10).")
    
    # Prepare final feature matrix
    feature_matrix = df_normalized[all_feature_cols].copy()
    target_series = df_normalized[target_col].copy()
    
    return feature_matrix, target_series, vif_report

def get_feature_matrix(df: pd.DataFrame, 
                      element_cols: List[str], 
                      dft_cols: List[str],
                      target_col: str) -> Tuple[pd.DataFrame, pd.Series, Dict[str, float]]:
    """
    Wrapper function to prepare features for modeling.
    Includes VIF calculation and multicollinearity reporting.
    """
    return prepare_modeling_features(df, element_cols, dft_cols, target_col)

def main():
    """
    Main function to demonstrate VIF calculation on the merged dataset.
    """
    import sys
    from pathlib import Path
    from config import CONFIG
    
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Load the merged dataset
    merged_path = CONFIG.INTERMEDIATE_DIR / "merged.csv"
    if not merged_path.exists():
        logger.error(f"Merged dataset not found at {merged_path}. Run ingestion pipeline first.")
        return
    
    df = pd.read_csv(merged_path)
    logger.info(f"Loaded {len(df)} rows from {merged_path}")
    
    # Define feature columns based on the dataset structure
    # Assuming element composition is in a column named 'composition' or similar
    # and DFT descriptors are in columns like 'shear_modulus', 'bulk_modulus', etc.
    
    # Try to identify element columns
    element_cols = []
    for col in df.columns:
        if col.lower() in ['fe', 'cr', 'ni', 'mn', 'mo', 'w', 'v', 'ti', 'al', 'c', 'n']:
            element_cols.append(col)
    
    # If no element columns found, try to parse from a composition column
    if not element_cols and 'composition' in df.columns:
        element_cols = ['composition']
    
    # DFT descriptor columns
    dft_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in 
                ['modulus', 'elastic', 'dft', 'shear', 'bulk', 'young'])]
    
    target_col = 'yield_strength_MPa'
    
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in dataset.")
        logger.info(f"Available columns: {list(df.columns)}")
        return
    
    if not element_cols and not dft_cols:
        logger.error("No feature columns found. Please check the dataset structure.")
        logger.info(f"Available columns: {list(df.columns)}")
        return
    
    logger.info(f"Element columns: {element_cols}")
    logger.info(f"DFT columns: {dft_cols}")
    
    # Prepare features and calculate VIF
    feature_matrix, target_series, vif_report = prepare_modeling_features(
        df, element_cols, dft_cols, target_col
    )
    
    # Print VIF report
    logger.info("Variance Inflation Factor (VIF) Report:")
    logger.info("-" * 50)
    for feature, vif_val in sorted(vif_report.items(), key=lambda x: x[1], reverse=True):
        status = "HIGH" if vif_val > 10 else "OK"
        logger.info(f"{feature:30s}: {vif_val:10.4f} [{status}]")
    
    # Save VIF report to a file
    vif_report_path = CONFIG.RESULTS_DIR / "vif_report.json"
    import json
    with open(vif_report_path, 'w') as f:
        json.dump({k: float(v) if not np.isinf(v) else "inf" for k, v in vif_report.items()}, f, indent=2)
    
    logger.info(f"VIF report saved to {vif_report_path}")
    
    # Return the feature matrix and VIF report for use in other tasks
    return feature_matrix, target_series, vif_report

if __name__ == "__main__":
    main()