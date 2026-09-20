"""
Transform module for compositional data handling in gut microbiome analysis.
Implements Centered Log-Ratio (CLR) transformation as a fallback for compositional bias correction.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_compositionality_flag(metadata_path: str = "data/metadata/compositionality_flag.json") -> bool:
    """
    Ensure the compositionality flag exists. If not, assume True (compositional data).
    
    Args:
        metadata_path: Path to the compositionality flag JSON file.
        
    Returns:
        bool: True if data is compositional, False otherwise.
    """
    path = Path(metadata_path)
    if not path.exists():
        logger.warning(f"Compositionality flag not found at {metadata_path}. Assuming compositional data (True).")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump({"is_compositional": True, "source": "default_assumption"}, f)
        return True
    
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get("is_compositional", True)

def detect_compositionality(df: pd.DataFrame, predictor_cols: Optional[list] = None, tolerance: float = 1e-6) -> bool:
    """
    Detect if the data is compositional by checking if row sums are approximately 1.
    
    Args:
        df: DataFrame containing the data.
        predictor_cols: List of columns to check. If None, all numeric columns are checked.
        tolerance: Tolerance for floating point comparison.
        
    Returns:
        bool: True if data appears compositional, False otherwise.
    """
    if predictor_cols is None:
        predictor_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only numeric columns that exist
    cols_to_check = [c for c in predictor_cols if c in df.columns]
    if not cols_to_check:
        logger.warning("No numeric predictor columns found to check for compositionality.")
        return False
    
    row_sums = df[cols_to_check].sum(axis=1)
    # Check if sums are close to 1 (or 0 if counts, but we expect relative abundance)
    # For relative abundance, sums should be ~1. For counts, we might need to normalize first.
    # Assuming relative abundance for this check.
    is_compositional = np.allclose(row_sums, 1.0, atol=tolerance)
    
    logger.info(f"Compositionality check: {'PASS' if is_compositional else 'FAIL'} (sums ~ 1.0)")
    return is_compositional

def apply_clr_transformation(df: pd.DataFrame, predictor_cols: Optional[list] = None, pseudo_count: float = 1e-6) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to the data.
    
    CLR(x) = log(x / geometric_mean(x))
    where geometric_mean(x) = (prod(x_i))^(1/n)
    
    Args:
        df: DataFrame containing the data.
        predictor_cols: List of columns to transform. If None, all numeric columns are transformed.
        pseudo_count: Small constant added to avoid log(0).
        
    Returns:
        pd.DataFrame: DataFrame with CLR-transformed values.
    """
    if predictor_cols is None:
        predictor_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    cols_to_transform = [c for c in predictor_cols if c in df.columns]
    if not cols_to_transform:
        logger.warning("No columns found to transform.")
        return df.copy()
    
    # Create a copy to avoid modifying the original
    transformed_df = df.copy()
    
    # Add pseudo-count to avoid log(0)
    data_subset = transformed_df[cols_to_transform].copy()
    data_subset = data_subset + pseudo_count
    
    # Calculate geometric mean for each row
    # log(geometric_mean) = mean(log(x))
    log_data = np.log(data_subset)
    log_geom_mean = log_data.mean(axis=1)
    
    # Apply CLR: log(x) - mean(log(x))
    clr_data = log_data.sub(log_geom_mean, axis=0)
    
    # Replace the original columns with transformed values
    transformed_df[cols_to_transform] = clr_data
    
    logger.info(f"CLR transformation applied to {len(cols_to_transform)} columns.")
    return transformed_df

def manual_clr(values: np.ndarray, pseudo_count: float = 1e-6) -> np.ndarray:
    """
    Manual CLR transformation for a 1D array (single row or sample).
    
    Args:
        values: 1D numpy array of values.
        pseudo_count: Small constant added to avoid log(0).
        
    Returns:
        np.ndarray: CLR-transformed values.
    """
    # Add pseudo-count
    values = values + pseudo_count
    
    # Calculate log
    log_values = np.log(values)
    
    # Calculate mean of log values
    log_mean = np.mean(log_values)
    
    # Subtract mean
    clr_values = log_values - log_mean
    
    return clr_values

def transform_data(
    input_path: str,
    output_path: str,
    metadata_path: str = "data/metadata/compositionality_flag.json",
    method_selection_log_path: str = "data/metadata/method_selection_log.json",
    predictor_cols: Optional[list] = None,
    pseudo_count: float = 1e-6
) -> None:
    """
    Main function to load data, check compositionality, apply CLR transformation,
    and save the result.
    
    Args:
        input_path: Path to the input data file (CSV or Parquet).
        output_path: Path to save the transformed data (Parquet).
        metadata_path: Path to the compositionality flag JSON file.
        method_selection_log_path: Path to save the method selection log.
        predictor_cols: List of predictor columns to transform.
        pseudo_count: Pseudo-count for CLR transformation.
    """
    logger.info(f"Starting data transformation from {input_path} to {output_path}")
    
    # Load data
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if input_file.suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_file.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_file.suffix}")
    
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    
    # Check compositionality
    is_compositional = ensure_compositionality_flag(metadata_path)
    
    if is_compositional:
        logger.info("Data is compositional. Applying CLR transformation.")
        transformed_df = apply_clr_transformation(df, predictor_cols, pseudo_count)
        
        # Log method selection
        method_log = {
            "transformation_method": "CLR",
            "reason": "Compositional data detected",
            "pseudo_count": pseudo_count,
            "timestamp": str(pd.Timestamp.now())
        }
    else:
        logger.info("Data is not compositional. No transformation applied.")
        transformed_df = df.copy()
        
        method_log = {
            "transformation_method": "None",
            "reason": "Non-compositional data",
            "timestamp": str(pd.Timestamp.now())
        }
    
    # Save method selection log
    log_file = Path(method_selection_log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing log if it exists, otherwise create new
    if log_file.exists():
        with open(log_file, 'r') as f:
            existing_log = json.load(f)
        # Append or update
        if "transformation_log" not in existing_log:
            existing_log["transformation_log"] = []
        existing_log["transformation_log"].append(method_log)
        final_log = existing_log
    else:
        final_log = {"transformation_log": [method_log]}
    
    with open(log_file, 'w') as f:
        json.dump(final_log, f, indent=2)
    
    logger.info(f"Method selection log saved to {method_selection_log_path}")
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save transformed data
    transformed_df.to_parquet(output_path, index=False)
    logger.info(f"Transformed data saved to {output_path}")

def main():
    """
    CLI entry point for the transform module.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply CLR transformation to compositional data.")
    parser.add_argument("--input", type=str, required=True, help="Input data file (CSV or Parquet)")
    parser.add_argument("--output", type=str, required=True, help="Output data file (Parquet)")
    parser.add_argument("--metadata", type=str, default="data/metadata/compositionality_flag.json",
                        help="Path to compositionality flag file")
    parser.add_argument("--log", type=str, default="data/metadata/method_selection_log.json",
                        help="Path to method selection log file")
    parser.add_argument("--pseudo-count", type=float, default=1e-6, help="Pseudo-count for CLR")
    
    args = parser.parse_args()
    
    try:
        transform_data(
            input_path=args.input,
            output_path=args.output,
            metadata_path=args.metadata,
            method_selection_log_path=args.log,
            pseudo_count=args.pseudo_count
        )
        logger.info("Transformation completed successfully.")
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise

if __name__ == "__main__":
    main()
