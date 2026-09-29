import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Union, Iterator, Dict, Any
import pandas as pd
import numpy as np

# Attempt to import optional dependencies
try:
    import miceforest
    MICEFOREST_AVAILABLE = True
except ImportError:
    MICEFOREST_AVAILABLE = False
    logging.warning("miceforest not found. Falling back to sklearn.impute.IterativeImputer.")

try:
    from sklearn.impute import IterativeImputer
    SKLEARN_IMPUTE_AVAILABLE = True
except ImportError:
    SKLEARN_IMPUTE_AVAILABLE = False
    logging.error("Neither miceforest nor sklearn.impute.IterativeImputer available. Cannot impute.")

from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config

logger = get_logger(__name__)

def get_available_ram_gb() -> float:
    """Estimate available RAM in GB."""
    try:
        import psutil
        available = psutil.virtual_memory().available
        return available / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not installed. Cannot estimate RAM. Defaulting to 4GB assumption.")
        return 4.0

def estimate_dataframe_memory(df: pd.DataFrame) -> float:
    """Estimate memory usage of a DataFrame in GB."""
    # Rough estimate: bytes / (1024^3)
    return df.memory_usage(deep=True).sum() / (1024 ** 3)

def load_data_streaming(path: Union[str, Path], batch_size: int = 1000) -> Iterator[pd.DataFrame]:
    """Load data in chunks if the file is large."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    # Check file size roughly
    size_gb = path.stat().st_size / (1024 ** 3)
    if size_gb > 0.5: # Arbitrary threshold for streaming
        logger.info(f"Loading {path} in streaming mode (size > 0.5GB)")
        for chunk in pd.read_csv(path, chunksize=batch_size):
            yield chunk
    else:
        logger.info(f"Loading {path} into memory (size <= 0.5GB)")
        yield pd.read_csv(path)

def calculate_missing_ratio(df: pd.DataFrame, subset: Optional[list] = None) -> pd.Series:
    """Calculate missing ratio per row."""
    if subset:
        return df[subset].isna().mean(axis=1)
    return df.isna().mean(axis=1)

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic preprocessing:
    1. Ensure numeric types for key variables.
    2. Normalize avatar_condition to 0/1 if binary.
    3. Log descriptive stats (but do not use change scores as outcome).
    """
    df = df.copy()
    key_vars = ['pre_self_esteem', 'post_self_esteem', 'comparison_tendency', 'avatar_condition']
    
    # Ensure numeric
    for col in key_vars:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Normalize avatar_condition
    if 'avatar_condition' in df.columns:
        # If it has values like 0, 1, 2... but we expect binary 0/1
        # If it's already 0/1, no change. If it's 1/2, map to 0/1? 
        # Spec says: "avatar_condition to 0/1 if binary"
        unique_vals = df['avatar_condition'].dropna().unique()
        if len(unique_vals) == 2 and set(unique_vals) == {0, 1}:
            logger.info("avatar_condition is already binary (0, 1).")
        elif len(unique_vals) == 2:
            # Map to 0, 1 preserving order
            sorted_vals = sorted(unique_vals)
            mapping = {sorted_vals[0]: 0, sorted_vals[1]: 1}
            df['avatar_condition'] = df['avatar_condition'].map(mapping)
            logger.info(f"Normalized avatar_condition from {sorted_vals} to [0, 1].")
        else:
            logger.warning(f"avatar_condition has {len(unique_vals)} unique values: {unique_vals}. Cannot normalize to binary.")

    # Log change scores for diagnostics ONLY (FR-017)
    if 'pre_self_esteem' in df.columns and 'post_self_esteem' in df.columns:
        change = df['post_self_esteem'] - df['pre_self_esteem']
        logger.info(f"Change score stats (diagnostic only): mean={change.mean():.4f}, std={change.std():.4f}")
        logger.warning("Change scores are for descriptive use only. Do NOT use as outcome in ANCOVA.")

    return df

def impute_data(df: pd.DataFrame, subset: Optional[list] = None) -> Tuple[pd.DataFrame, str]:
    """
    Perform MICE imputation.
    Priority: miceforest > sklearn.impute.IterativeImputer.
    Excludes rows with > 20% missingness.
    
    Returns:
        Tuple[imputed_df, method_used]
    """
    if subset is None:
        subset = ['pre_self_esteem', 'post_self_esteem', 'comparison_tendency', 'avatar_condition']
    
    # Filter to only relevant columns for imputation logic, but keep index
    # We need to track which rows are excluded
    missing_ratio = calculate_missing_ratio(df, subset)
    excluded_mask = missing_ratio > 0.20
    excluded_count = excluded_mask.sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} rows with > 20% missingness.")
        df_clean = df[~excluded_mask].copy()
    else:
        df_clean = df.copy()

    if df_clean.empty:
        raise ValueError("No rows remaining after excluding high-missingness rows.")

    # Check for any remaining missingness
    if df_clean[subset].isna().sum().sum() == 0:
        logger.info("No missing values remaining in key variables.")
        return df_clean, "none_needed"

    method_used = ""

    if MICEFOREST_AVAILABLE:
        logger.info("Using miceforest for MICE imputation.")
        try:
            kernel = miceforest.ImputationKernel(df_clean[subset], datasets=1, save_all_iterations=False)
            # Impute all missing values
            imputed_ds = kernel.complete_data()
            method_used = "miceforest"
            logger.info("miceforest imputation completed successfully.")
        except Exception as e:
            logger.error(f"miceforest failed: {e}")
            # Fallback logic handled below if we catch it, but let's try sklearn next
            if not SKLEARN_IMPUTE_AVAILABLE:
                raise
            MICEFOREST_AVAILABLE = False # Force fallback

    if not MICEFOREST_AVAILABLE and SKLEARN_IMPUTE_AVAILABLE:
        logger.info("Falling back to sklearn.impute.IterativeImputer.")
        logger.warning("miceforest is unavailable or failed. Using sklearn.impute.IterativeImputer as fallback.")
        logger.warning("This is a fallback mechanism. Ensure results are interpreted with caution if miceforest was expected.")
        
        imp = IterativeImputer(random_state=42, max_iter=10, tol=1e-3)
        try:
            imputed_array = imp.fit_transform(df_clean[subset])
            imputed_df = df_clean.copy()
            imputed_df[subset] = imputed_array
            method_used = "sklearn_iterative"
            logger.info("sklearn.impute.IterativeImputer completed successfully.")
        except Exception as e:
            logger.error(f"sklearn.impute.IterativeImputer failed: {e}")
            raise

    if not MICEFOREST_AVAILABLE and not SKLEARN_IMPUTE_AVAILABLE:
        raise RuntimeError("No imputation library available (miceforest or sklearn).")

    return imputed_df, method_used

def run_preprocess(input_path: Union[str, Path], output_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Main entry point for preprocessing.
    1. Load data.
    2. Preprocess (types, normalization).
    3. Impute (MICE).
    4. Save results.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    log_execution_start(logger, "preprocess", input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load data (handle streaming if needed, though for imputation we usually need full df)
    # For simplicity in this runner, we load full if < 1GB, else warn
    if input_path.stat().st_size > 1 * 1024 * 1024 * 1024:
        logger.warning("File is large (>1GB). Attempting to load into memory. If OOM, streaming imputation is required.")
    
    df = pd.read_csv(input_path)
    
    # Preprocess
    df = preprocess_data(df)
    
    # Impute
    df_imputed, method = impute_data(df)
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_imputed.to_csv(output_path, index=False)
    
    logger.info(f"Imputed data saved to {output_path} using {method}.")
    
    log_execution_end(logger, "preprocess", output_path)
    
    return {
        "status": "success",
        "rows_in": len(df),
        "rows_out": len(df_imputed),
        "imputation_method": method,
        "output_path": str(output_path)
    }

def main():
    """CLI entry point."""
    config = get_config()
    input_path = config.get("raw_data_path", "data/raw/synthetic_data.csv") # Default fallback
    output_path = config.get("imputed_data_path", "data/processed/imputed_data.csv")
    
    # Override with args if provided (simplified)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="Input CSV path")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()
    
    if args.input: input_path = args.input
    if args.output: output_path = args.output
    
    result = run_preprocess(input_path, output_path)
    print(result)

if __name__ == "__main__":
    main()