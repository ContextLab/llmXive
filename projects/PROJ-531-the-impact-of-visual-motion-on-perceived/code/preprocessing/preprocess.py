import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Tuple, List, Optional, Dict, Any

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_source_data(input_path: str) -> pd.DataFrame:
    """
    Loads the raw or intermediate dataset from the specified path.
    Expected to be called after T012 (download) or T013 (synthetic generation).
    """
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Source data file not found: {path}")
        raise FileNotFoundError(f"Source data file not found: {path}")

    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.parquet':
        df = pd.read_parquet(path)
    else:
        logger.error(f"Unsupported file format: {path.suffix}")
        raise ValueError(f"Unsupported file format: {path.suffix}")

    logger.info(f"Loaded source data with shape: {df.shape}")
    return df

def extract_motion_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts motion features (latency, smoothness, lead_time) from the raw data.
    If columns are missing, attempts to derive them or raises a warning.
    """
    # Define expected feature columns based on schema
    required_features = ['latency', 'smoothness', 'lead_time']
    available_features = [col for col in required_features if col in df.columns]

    if not available_features:
        logger.warning("No motion features found in raw data. Returning df as-is.")
        return df

    # Ensure numeric types
    for col in available_features:
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"Converting {col} to numeric.")
            df[col] = pd.to_numeric(df[col], errors='coerce')

    logger.info(f"Extracted motion features: {available_features}")
    return df

def aggregate_agency_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates agency scores if multiple rating columns exist.
    If 'agency_score' exists, it is kept. If not, attempts to average rating columns.
    """
    if 'agency_score' in df.columns:
        logger.info("Agency score column already exists.")
        return df

    # Fallback: look for generic rating columns
    rating_cols = [col for col in df.columns if 'rating' in col.lower() or 'score' in col.lower()]
    if len(rating_cols) >= 2:
        logger.info(f"Aggregating agency score from columns: {rating_cols}")
        df['agency_score'] = df[rating_cols].mean(axis=1)
    elif len(rating_cols) == 1:
        logger.info(f"Renaming {rating_cols[0]} to agency_score")
        df.rename(columns={rating_cols[0]: 'agency_score'}, inplace=True)
    else:
        logger.warning("Could not find or aggregate agency_score column.")

    return df

def calculate_vif(df: pd.DataFrame, feature_columns: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Calculates Variance Inflation Factor (VIF) for specified feature columns.
    Flags and excludes features with VIF >= 5.
    
    Args:
        df: DataFrame containing the features.
        feature_columns: List of column names to check for collinearity.
    
    Returns:
        A tuple containing:
        - A DataFrame with the VIF values.
        - A list of column names that are excluded due to high collinearity (VIF >= 5).
    """
    if not feature_columns:
        logger.warning("No feature columns provided for VIF calculation.")
        return pd.DataFrame(), []

    # Filter to available columns
    valid_features = [col for col in feature_columns if col in df.columns]
    if not valid_features:
        logger.warning("None of the provided feature columns exist in the DataFrame.")
        return pd.DataFrame(), []

    # Prepare data for VIF calculation (drop NaNs)
    vif_df = df[valid_features].dropna()
    
    if vif_df.empty:
        logger.warning("No valid data remaining after dropping NaNs for VIF calculation.")
        return pd.DataFrame(), valid_features # Exclude all if no data

    # Add constant for intercept (required for statsmodels VIF)
    vif_df_with_const = sm.add_constant(vif_df)
    
    vif_results = []
    excluded_cols = []
    
    logger.info("Calculating VIF for features...")
    
    for col in valid_features:
        # statsmodels VIF requires the constant column, but we only report on features
        try:
            vif_val = variance_inflation_factor(vif_df_with_const.values, 
                                                list(vif_df_with_const.columns).index(col))
            vif_results.append({'feature': col, 'vif': vif_val})
            
            if vif_val >= 5.0:
                excluded_cols.append(col)
                logger.warning(f"High collinearity detected: {col} has VIF = {vif_val:.2f} (>= 5.0). Flagging for exclusion.")
            else:
                logger.debug(f"Feature {col} has VIF = {vif_val:.2f}")
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            excluded_cols.append(col) # Exclude on error to be safe

    vif_df_output = pd.DataFrame(vif_results)
    
    if excluded_cols:
        logger.info(f"Excluding {len(excluded_cols)} features due to high VIF: {excluded_cols}")
    else:
        logger.info("No features excluded based on VIF threshold (5.0).")
        
    return vif_df_output, excluded_cols

def run_preprocessing(input_path: str, output_path: str, feature_columns: List[str]) -> Dict[str, Any]:
    """
    Main preprocessing pipeline:
    1. Load data
    2. Extract motion features
    3. Aggregate agency scores
    4. Calculate VIF and exclude high-collinearity features
    5. Handle missing values
    6. Save cleaned data
    
    Args:
        input_path: Path to raw/intermediate data.
        output_path: Path to save cleaned data.
        feature_columns: List of candidate feature columns for VIF check.
    
    Returns:
        A dictionary with processing metadata (rows_in, rows_out, excluded_features, etc.)
    """
    logger.info(f"Starting preprocessing pipeline. Input: {input_path}, Output: {output_path}")
    
    # 1. Load
    df = load_source_data(input_path)
    rows_in = len(df)
    
    # 2. Extract Features
    df = extract_motion_features(df)
    
    # 3. Aggregate Scores
    df = aggregate_agency_scores(df)
    
    # 4. VIF Check
    vif_results, excluded_features = calculate_vif(df, feature_columns)
    
    # 5. Exclude features
    cols_to_drop = [col for col in excluded_features if col in df.columns]
    if cols_to_drop:
        df.drop(columns=cols_to_drop, inplace=True)
    
    # 6. Handle Missing Values (Simple imputation for numeric columns)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        logger.info(f"Filled missing values in numeric columns using median.")
    
    rows_out = len(df)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")
    
    metadata = {
        "input_path": input_path,
        "output_path": output_path,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "features_excluded": excluded_features,
        "vif_results": vif_results.to_dict(orient='records') if not vif_results.empty else []
    }
    
    return metadata

def main():
    """
    Entry point for the preprocessing script.
    Reads configuration from environment or defaults.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "raw" / "synthetic_interactions.csv"
    output_path = project_root / "data" / "processed" / "cleaned_data.csv"
    
    # Features to check for collinearity
    feature_columns = ['latency', 'smoothness', 'lead_time']
    
    # Allow override via environment variables
    if os.getenv('RAW_DATA_PATH'):
        input_path = Path(os.getenv('RAW_DATA_PATH'))
    if os.getenv('CLEANED_DATA_PATH'):
        output_path = Path(os.getenv('CLEANED_DATA_PATH'))
        
    try:
        metadata = run_preprocessing(str(input_path), str(output_path), feature_columns)
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()