import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
import yaml
from pathlib import Path

from utils.logging_config import get_logger
from config import get_data_processed_dir, get_vif_threshold

logger = get_logger(__name__)

def calculate_vif(features_df: pd.DataFrame, exclude_intercept: bool = True) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature in the DataFrame.

    Args:
        features_df: DataFrame containing feature columns (numeric).
        exclude_intercept: If True, excludes the intercept column (if present) from calculation.

    Returns:
        Dictionary mapping feature names to their VIF scores.
    """
    logger.info("Starting VIF calculation...")
    
    # Ensure we are working with numeric data
    numeric_df = features_df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        logger.error("No numeric columns found in the feature DataFrame.")
        return {}

    # Drop any columns with constant variance (VIF is undefined)
    # But for the calculation loop, we handle it via the regression
    
    vif_data = {}
    
    # Create a copy to avoid modifying original
    X = numeric_df.copy()
    
    # Remove columns with zero variance (constant features) to prevent division by zero
    # These technically have infinite VIF, but we'll flag them separately if needed
    # For now, we drop them to allow the rest to calculate
    constant_cols = X.columns[X.var() == 0]
    if len(constant_cols) > 0:
        logger.warning(f"Dropping constant columns (VIF undefined): {list(constant_cols)}")
        X = X.drop(columns=constant_cols)

    if X.empty:
        logger.warning("All columns were constant or non-numeric. VIF calculation skipped.")
        return {}

    from sklearn.linear_model import LinearRegression

    for col in X.columns:
        y = X[col]
        # Features for regression: all other columns
        X_other = X.drop(columns=[col])
        
        # If only one feature left, VIF is 0 (or undefined depending on definition, usually 0 for single predictor)
        if X_other.shape[1] == 0:
            vif_data[col] = 0.0
            continue

        try:
            model = LinearRegression()
            model.fit(X_other, y)
            r_squared = model.score(X_other, y)
            
            # VIF = 1 / (1 - R^2)
            if r_squared >= 1.0:
                # Perfect multicollinearity
                vif_data[col] = float('inf')
            else:
                vif_data[col] = 1.0 / (1.0 - r_squared)
        except Exception as e:
            logger.error(f"Error calculating VIF for column {col}: {e}")
            vif_data[col] = float('nan')

    logger.info(f"VIF calculation complete. Processed {len(vif_data)} features.")
    return vif_data

def get_collinear_features(vif_scores: Dict[str, float], threshold: Optional[float] = None) -> List[str]:
    """
    Identify features with VIF scores above a given threshold.

    Args:
        vif_scores: Dictionary of feature names to VIF scores.
        threshold: The VIF threshold for collinearity (default from config).

    Returns:
        List of feature names considered collinear.
    """
    if threshold is None:
        threshold = get_vif_threshold()
    
    collinear = [
        feat for feat, score in vif_scores.items()
        if not np.isnan(score) and score >= threshold
    ]
    
    if collinear:
        logger.warning(f"Found {len(collinear)} collinear features (VIF >= {threshold}): {collinear}")
    else:
        logger.info(f"No collinear features found (threshold: {threshold}).")
        
    return collinear

def remove_collinear_features(
    features_df: pd.DataFrame, 
    vif_scores: Dict[str, float], 
    threshold: Optional[float] = None
) -> pd.DataFrame:
    """
    Remove features with VIF scores above the threshold from the DataFrame.

    Args:
        features_df: Original DataFrame.
        vif_scores: Dictionary of VIF scores.
        threshold: VIF threshold.

    Returns:
        DataFrame with collinear features removed.
    """
    collinear = get_collinear_features(vif_scores, threshold)
    if not collinear:
        return features_df.copy()
    
    logger.info(f"Removing collinear features: {collinear}")
    # We need to be careful not to drop columns that don't exist in the original df
    # (though they should)
    cols_to_drop = [c for c in collinear if c in features_df.columns]
    return features_df.drop(columns=cols_to_drop)

def save_vif_report(
    vif_scores: Dict[str, float], 
    output_path: Optional[Path] = None, 
    threshold: Optional[float] = None
) -> Path:
    """
    Generate and save a detailed VIF report to a YAML file.

    Args:
        vif_scores: Dictionary of feature names to VIF scores.
        output_path: Path to save the report. If None, uses default processed dir.
        threshold: VIF threshold for the 'is_collinear' flag.

    Returns:
        Path to the saved report file.
    """
    if threshold is None:
        threshold = get_vif_threshold()
    
    if output_path is None:
        processed_dir = get_data_processed_dir()
        output_path = processed_dir / "vif_report.yaml"
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "metadata": {
            "threshold": threshold,
            "total_features": len(vif_scores),
            "report_type": "VIF Collinearity Analysis"
        },
        "features": []
    }

    # Sort by VIF score descending
    sorted_features = sorted(vif_scores.items(), key=lambda x: x[1], reverse=True)

    collinear_count = 0
    for feat_name, score in sorted_features:
        is_collinear = False
        if not np.isnan(score):
            is_collinear = score >= threshold
            if is_collinear:
                collinear_count += 1
        
        feature_entry = {
            "feature_name": feat_name,
            "vif_score": score if not np.isnan(score) else None,
            "is_collinear": is_collinear
        }
        report_data["features"].append(feature_entry)

    report_data["metadata"]["collinear_feature_count"] = collinear_count

    try:
        with open(output_path, 'w') as f:
            yaml.dump(report_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"VIF report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save VIF report: {e}")
        raise

    return output_path

def main():
    """
    Main entry point for VIF analysis and report generation.
    Reads the cleaned dataset, calculates VIF, and saves the report.
    """
    logger.info("Starting VIF analysis main process...")
    
    # Load cleaned data
    processed_dir = get_data_processed_dir()
    cleaned_file = processed_dir / "solder_hardness_cleaned.csv"
    
    if not cleaned_file.exists():
        logger.error(f"Cleaned data file not found: {cleaned_file}")
        logger.error("Please ensure T013 (cleaner) has been executed first.")
        return

    try:
        df = pd.read_csv(cleaned_file)
        logger.info(f"Loaded {len(df)} records from {cleaned_file}")
    except Exception as e:
        logger.error(f"Failed to load cleaned data: {e}")
        return

    # Identify feature columns (exclude target and metadata)
    # Assuming the cleaned file has 'hardness_hv' as target and composition columns
    # We need to select only the numeric feature columns (e.g., CLR transformed or descriptors)
    # For now, we assume the user has a specific feature set. 
    # If the dataframe contains non-numeric columns (like alloy_family), we drop them.
    
    # Heuristic: Select all numeric columns except 'hardness_hv'
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'hardness_hv' in numeric_cols:
        numeric_cols.remove('hardness_hv')
    
    if not numeric_cols:
        logger.error("No numeric feature columns found in the cleaned dataset.")
        return

    logger.info(f"Calculating VIF for {len(numeric_cols)} features: {numeric_cols}")
    
    feature_df = df[numeric_cols].copy()
    
    # Calculate VIF
    vif_scores = calculate_vif(feature_df)
    
    if not vif_scores:
        logger.warning("No VIF scores calculated.")
        return

    # Save report
    try:
        report_path = save_vif_report(vif_scores)
        logger.info(f"VIF report successfully generated at: {report_path}")
    except Exception as e:
        logger.error(f"Failed to generate VIF report: {e}")
        raise

if __name__ == "__main__":
    main()