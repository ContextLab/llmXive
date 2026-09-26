"""
PCA dimensionality check for complexity metrics.

Validates the construct validity of the three complexity metrics (edge_density, 
entropy, fractal_dim) by performing Principal Component Analysis.

This task implements T051: Verify that the metrics collectively explain a 
sufficient amount of variance (>= 0.8) to avoid cherry-picking a single metric.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from config import get_data_path
from utils.logging import get_logger
from sklearn.decomposition import PCA

def run_pca_check(metrics_path: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run PCA check on complexity metrics.
    
    Args:
        metrics_path: Path to complexity_metrics_raw.csv
        output_path: Path to output JSON (pca_variance.json)
        
    Returns:
        Result dictionary containing status, message, and cumulative_variance
    """
    logger = get_logger(__name__)
    
    # Default paths based on project structure
    if metrics_path is None:
        metrics_path = str(get_data_path("processed/complexity_metrics_raw.csv"))
    if output_path is None:
        output_path = str(get_data_path("results/pca_variance.json"))
        
    try:
        # Check if input file exists
        if not os.path.exists(metrics_path):
            logger.warning(f"Metrics file not found: {metrics_path}. Writing error status.")
            result = {"status": "error", "message": "File not found", "cumulative_variance": 0.0}
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            return result
        
        # Load the data
        df = pd.read_csv(metrics_path)
        required_cols = ['edge_density', 'entropy', 'fractal_dim']
        
        # Validate columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing required columns: {missing_cols}. Writing error status.")
            result = {"status": "error", "message": f"Missing columns: {missing_cols}", "cumulative_variance": 0.0}
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            return result
        
        # Prepare data for PCA (drop rows with NaN in required columns)
        X = df[required_cols].dropna()
        
        # Check for sufficient data points
        if X.shape[0] < 2:
            logger.warning(f"Insufficient data for PCA (n={X.shape[0]}). Writing warning status.")
            result = {"status": "warning", "message": "Insufficient data", "cumulative_variance": 0.0}
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            return result
        
        # Perform PCA
        n_components = len(required_cols)
        pca = PCA(n_components=n_components)
        pca.fit(X)
        
        # Calculate cumulative variance explained
        cumulative_variance = float(pca.explained_variance_ratio_.cumsum()[-1])
        
        # Determine status based on threshold (0.8)
        if cumulative_variance < 0.8:
            logger.warning(f"Low cumulative variance: {cumulative_variance:.4f} (< 0.8). Metrics may not form a unified construct.")
            result = {
                "status": "warning", 
                "message": "Low variance", 
                "cumulative_variance": cumulative_variance,
                "individual_variances": pca.explained_variance_ratio_.tolist()
            }
        else:
            logger.info(f"PCA check complete. Cumulative variance: {cumulative_variance:.4f} (>= 0.8)")
            result = {
                "status": "ok", 
                "message": "Variance acceptable", 
                "cumulative_variance": cumulative_variance,
                "individual_variances": pca.explained_variance_ratio_.tolist()
            }
            
        # Ensure output directory exists and write results
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
            
        logger.info(f"PCA results written to {output_path}")
        return result
        
    except Exception as e:
        logger.error(f"PCA check failed with exception: {e}", exc_info=True)
        result = {"status": "error", "message": str(e), "cumulative_variance": 0.0}
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as write_err:
            logger.error(f"Failed to write error result: {write_err}")
        return result

def main() -> None:
    """Main entry point for T051: PCA dimensionality check."""
    logger = get_logger(__name__)
    logger.info("Starting PCA dimensionality check (T051)...")
    result = run_pca_check()
    logger.info(f"PCA Result: {result}")
    
    if result["status"] == "warning":
        logger.warning("PCA Warning: Metrics explain less than 80% of variance. Consider reviewing metric selection.")
    elif result["status"] == "error":
        logger.error("PCA Error: Check failed. See logs for details.")
    else:
        logger.info("PCA Validation: Passed. Metrics form a coherent construct.")

if __name__ == "__main__":
    main()