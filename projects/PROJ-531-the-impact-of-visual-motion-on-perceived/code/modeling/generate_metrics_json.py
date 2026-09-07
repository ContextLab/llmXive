"""
T026 Implementation: Generate model_metrics.json
Aggregates OLS coefficients, corrected p-values, Random Forest feature importance,
and Cross-Validation metrics into a single JSON artifact.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add parent directory to path to resolve imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger
from preprocessing.output_cleaned_data import run_cleaning_pipeline

logger = get_logger(__name__)

def load_cleaned_data(data_path: str) -> pd.DataFrame:
    """Loads the cleaned dataset produced by T017."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. "
                                "Ensure T017 has run successfully.")
    logger.info(f"Loading cleaned data from {data_path}")
    return pd.read_csv(path)

def load_model_results(base_path: str) -> Dict[str, Any]:
    """
    Loads intermediate model results.
    In a full pipeline, these would be saved by T021 (OLS), T021b (Ridge), T022b (RF).
    For this task, we assume T021, T021b, and T022b have populated a temporary
    results directory or we reconstruct them if the pipeline is run sequentially.
    
    However, to satisfy the 'one task' constraint and ensure this script is
    self-contained for the final aggregation, we will attempt to load
    pre-computed results from a standard location. If they don't exist, 
    we raise an error indicating the prerequisite tasks (T021, T021b, T022b)
    must run first.
    """
    results_dir = Path(base_path) / "data" / "results" / "intermediate"
    if not results_dir.exists():
        raise FileNotFoundError(
            f"Intermediate results directory not found at {results_dir}. "
            "Prerequisite tasks (T021, T021b, T022b) must be executed first."
        )
    
    results = {}
    
    # Load OLS results (T021)
    ols_path = results_dir / "ols_results.json"
    if ols_path.exists():
        with open(ols_path, 'r') as f:
            results['ols'] = json.load(f)
    else:
        raise FileNotFoundError(f"OLS results missing at {ols_path}. Run T021.")
        
    # Load RF results (T022b)
    rf_path = results_dir / "rf_results.json"
    if rf_path.exists():
        with open(rf_path, 'r') as f:
            results['random_forest'] = json.load(f)
    else:
        raise FileNotFoundError(f"RF results missing at {rf_path}. Run T022b.")

    # Load Ridge results (T021b) if available
    ridge_path = results_dir / "ridge_results.json"
    if ridge_path.exists():
        with open(ridge_path, 'r') as f:
            results['ridge'] = json.load(f)
    
    return results

def run_metric_aggregation(cleaned_data_path: str, base_dir: str) -> Dict[str, Any]:
    """
    Aggregates all metrics into the final model_metrics.json structure.
    """
    logger.info("Starting metric aggregation for T026")
    
    # 1. Load Data
    df = load_cleaned_data(cleaned_data_path)
    n_samples = len(df)
    
    # 2. Load Intermediate Results
    results = load_model_results(base_dir)
    
    # 3. Construct Final Output
    output = {
        "metadata": {
            "n_samples": n_samples,
            "generated_at": pd.Timestamp.now().isoformat(),
            "pipeline_version": "1.0.0",
            "task_id": "T026"
        },
        "ols_model": {
            "coefficients": results['ols'].get('coefficients', {}),
            "p_values_raw": results['ols'].get('p_values_raw', {}),
            "p_values_corrected": results['ols'].get('p_values_corrected', {}),
            "r_squared": results['ols'].get('r_squared', 0.0),
            "adj_r_squared": results['ols'].get('adj_r_squared', 0.0),
            "f_statistic": results['ols'].get('f_statistic', 0.0),
            "f_p_value": results['ols'].get('f_p_value', 0.0)
        },
        "random_forest_model": {
            "feature_importance": results['random_forest'].get('feature_importance', {}),
            "cv_r_squared_mean": results['random_forest'].get('cv_r_squared_mean', 0.0),
            "cv_r_squared_std": results['random_forest'].get('cv_r_squared_std', 0.0),
            "cv_rmse_mean": results['random_forest'].get('cv_rmse_mean', 0.0),
            "cv_rmse_std": results['random_forest'].get('cv_rmse_std', 0.0),
            "n_estimators": results['random_forest'].get('n_estimators', 100)
        }
    }
    
    # Optional: Add Ridge if available
    if 'ridge' in results:
        output["ridge_model"] = {
            "coefficients": results['ridge'].get('coefficients', {}),
            "alpha": results['ridge'].get('alpha', 1.0),
            "cv_r_squared_mean": results['ridge'].get('cv_r_squared_mean', 0.0),
            "cv_rmse_mean": results['ridge'].get('cv_rmse_mean', 0.0)
        }
        
    # 4. Ensure Correlational Framing (FR-008)
    output["metadata"]["interpretation_note"] = (
        "Results are correlational. No causal claims are made. "
        "Synthetic data stress-test only."
    )
    
    logger.info("Metric aggregation complete.")
    return output

def main():
    """
    Entry point for T026.
    Reads cleaned data and intermediate model results, aggregates them,
    and writes data/results/model_metrics.json.
    """
    base_dir = Path(__file__).parent.parent.parent
    cleaned_data_path = base_dir / "data" / "processed" / "cleaned_data.csv"
    output_path = base_dir / "data" / "results" / "model_metrics.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        metrics = run_metric_aggregation(str(cleaned_data_path), str(base_dir))
        
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
            
        logger.info(f"Successfully wrote model metrics to {output_path}")
        print(f"SUCCESS: {output_path} generated.")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()