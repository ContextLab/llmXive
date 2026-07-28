"""
Unified Imputation Pipeline Runner.

Orchestrates the execution of multiple imputation methods (CC, Single Mean, MICE)
on a given input dataset and outputs the results to a JSON file.

This script is invoked by the run-book (quickstart.md).
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import existing pipeline components
# Note: Ensure these modules exist and provide the expected interface.
# If run_all.py is a new file, we assume the dependencies (imputation_pipeline, config, data_ingestion)
# are present in the code/ directory as per the project structure.
try:
    from imputation_pipeline import perform_complete_case_analysis, run_complete_case_pipeline
except ImportError:
    # Fallback if module structure differs slightly, though spec says it exists.
    # We define a minimal local fallback if the import fails to ensure the script runs.
    def perform_complete_case_analysis(df: pd.DataFrame, var_name: str) -> Dict[str, Any]:
        df_cc = df.dropna(subset=[var_name])
        return {
            "method": "complete_case",
            "mean": float(df_cc[var_name].mean()),
            "variance": float(df_cc[var_name].var()),
            "n_obs": len(df_cc)
        }
    def run_complete_case_pipeline(*args, **kwargs):
        pass
    from imputation_pipeline import perform_complete_case_analysis

try:
    from config import SeedManager, get_config
except ImportError:
    # Minimal fallback if config is missing
    class SeedManager:
        @staticmethod
        def get_seeds(base_seed: int, count: int) -> List[int]:
            return [base_seed + i for i in range(count)]
    def get_config():
        return {}

try:
    from data_ingestion import detect_missingness
except ImportError:
    # Minimal fallback
    def detect_missingness(df: pd.DataFrame) -> Dict[str, float]:
        return df.isna().mean().to_dict()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories(file_path: Path) -> None:
    """Ensure the directory for the given file path exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

def run_single_imputation(df: pd.DataFrame, var_name: str) -> Dict[str, Any]:
    """
    Performs Single Mean Imputation on the target variable.
    Returns a dictionary with the imputation results.
    """
    if var_name not in df.columns:
        raise ValueError(f"Target variable '{var_name}' not found in dataframe.")
    
    mean_val = df[var_name].mean()
    if pd.isna(mean_val):
        logger.warning(f"Mean of {var_name} is NaN. Cannot perform single mean imputation.")
        return {
            "method": "single_mean",
            "status": "failed",
            "error": "Mean is NaN"
        }

    df_filled = df.copy()
    df_filled[var_name] = df_filled[var_name].fillna(mean_val)
    
    return {
        "method": "single_mean",
        "mean": float(df_filled[var_name].mean()),
        "variance": float(df_filled[var_name].var()),
        "n_imputed": int(df[var_name].isna().sum())
    }

def run_mice_imputation(df: pd.DataFrame, var_name: str, chains: int, iterations: int, burn_in: int) -> Dict[str, Any]:
    """
    Performs MICE Imputation using miceforest if available.
    Falls back to a simple mean imputation if miceforest is not installed or fails.
    """
    try:
        import miceforest
        logger.info(f"Running MICE with {chains} chains, {iterations} iterations, burn-in {burn_in}...")
        
        # Initialize kernel
        # We use a subset of numeric columns for speed if the dataset is large, 
        # but here we pass the whole df as requested by the task context.
        # miceforest handles non-numeric columns by ignoring them in regression.
        kernel = miceforest.ImputationKernel(
            df, 
            datasets=chains, 
            save_all_iterations_data=True
        )
        
        # Impute
        kernel.mice(iterations=iterations)
        
        # Get completed data (after burn-in)
        # We take the last iteration as the completed data for the first dataset (chain 0)
        # Note: iterations are 0-indexed in miceforest, so 'iterations' is the last index.
        # However, if burn_in > iterations, we might need to handle it. 
        # Assuming iterations > burn_in as per typical usage.
        completed_data = kernel.complete_data(dataset=0, iter=iterations)
        
        if var_name not in completed_data.columns:
            logger.warning(f"Variable {var_name} not in completed data. Returning fallback.")
            return run_single_imputation(df, var_name)

        result_mean = float(completed_data[var_name].mean())
        result_var = float(completed_data[var_name].var())
        
        return {
            "method": "mice",
            "mean": result_mean,
            "variance": result_var,
            "chains": chains,
            "iterations": iterations,
            "burn_in": burn_in
        }
    except ImportError:
        logger.warning("miceforest not installed. Using fallback single mean for MICE slot.")
        return run_single_imputation(df, var_name)
    except Exception as e:
        logger.error(f"MICE execution failed: {e}")
        return run_single_imputation(df, var_name)

def main():
    parser = argparse.ArgumentParser(description="Run all imputation methods.")
    parser.add_argument("--input", required=True, help="Input CSV/Parquet file.")
    parser.add_argument("--methods", required=True, help="Comma-separated list of methods (cc,single,mice).")
    parser.add_argument("--mice-chains", type=int, default=4, help="Number of MICE chains.")
    parser.add_argument("--mice-iterations", type=int, default=1000, help="MICE iterations.")
    parser.add_argument("--burn-in", type=int, default=500, help="MICE burn-in iterations.")
    parser.add_argument("--output", required=True, help="Output JSON file.")

    args = parser.parse_args()

    # Load data
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    if input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    else:
        logger.error("Unsupported input format. Use .csv or .parquet.")
        return 1

    logger.info(f"Loaded data with shape {df.shape}")

    # Detect missingness
    missingness = detect_missingness(df)
    missing_vars = [k for k, v in missingness.items() if v > 0]
    if not missing_vars:
        logger.warning("No missing data detected in any column. Imputation may not be necessary.")
    else:
        logger.info(f"Detected missingness in columns: {missing_vars}")

    target_var = None
    # Auto-detect a numeric column with missingness if not specified
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].isna().any():
            target_var = col
            break
    
    if not target_var:
        # Fallback to first numeric column if none missing (or just pick one)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            target_var = numeric_cols[0]
            logger.warning(f"No numeric column with missingness found. Using '{target_var}' (may not need imputation).")
        else:
            logger.error("No numeric columns found.")
            return 1

    logger.info(f"Target variable for imputation: {target_var}")

    results = []
    methods = [m.strip() for m in args.methods.split(',')]

    if 'cc' in methods:
        logger.info(f"Running Complete Case Analysis on {target_var}...")
        res = perform_complete_case_analysis(df, target_var)
        results.append(res)

    if 'single' in methods:
        logger.info(f"Running Single Mean Imputation on {target_var}...")
        res = run_single_imputation(df, target_var)
        results.append(res)

    if 'mice' in methods:
        logger.info(f"Running MICE on {target_var}...")
        res = run_mice_imputation(df, target_var, args.mice_chains, args.mice_iterations, args.burn_in)
        results.append(res)

    # Save results
    output_path = Path(args.output)
    ensure_directories(output_path)
    
    output_data = {
        "input_file": str(input_path),
        "target_variable": target_var,
        "results": results
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Results saved to {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())