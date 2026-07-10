import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..config import get_project_root, get_data_path

logger = logging.getLogger(__name__)

def run_pca_check(complexity_scores_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run a PCA dimensionality check on complexity metrics to verify construct validity.
    
    Args:
        complexity_scores_path: Path to the complexity scores CSV. If None, uses default path.
        
    Returns:
        Dictionary containing PCA results including explained variance and component loadings.
    """
    if complexity_scores_path is None:
        data_path = get_data_path()
        complexity_scores_path = data_path / "processed" / "complexity_scores.csv"
    
    if not complexity_scores_path.exists():
        logger.warning(f"Complexity scores file not found at {complexity_scores_path}. Skipping PCA check.")
        return {"status": "skipped", "reason": "file_not_found"}
    
    try:
        df = pd.read_csv(complexity_scores_path)
        
        required_cols = ["edge_density", "entropy", "fractal_dim"]
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"Missing required columns: {missing}")
        
        metrics_df = df[required_cols].dropna()
        
        if metrics_df.empty:
            logger.warning("No valid data points for PCA analysis.")
            return {"status": "skipped", "reason": "no_valid_data"}
        
        from sklearn.decomposition import PCA
        
        pca = PCA(n_components=len(required_cols))
        pca_result = pca.fit_transform(metrics_df)
        
        explained_variance = pca.explained_variance_ratio_.tolist()
        cumulative_variance = [sum(explained_variance[:i+1]) for i in range(len(explained_variance))]
        component_loadings = {
            col: pca.components_[i].tolist() 
            for i, col in enumerate(required_cols)
        }
        
        results = {
            "status": "success",
            "n_samples": len(metrics_df),
            "n_components": len(required_cols),
            "explained_variance_ratio": explained_variance,
            "cumulative_variance": cumulative_variance,
            "component_loadings": component_loadings,
            "metric_columns": required_cols
        }
        
        logger.info(f"PCA check completed. Cumulative variance: {cumulative_variance[-1]:.4f}")
        return results
        
    except Exception as e:
        logger.error(f"PCA check failed: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}

def main() -> int:
    """Main entry point for PCA check script."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting PCA dimensionality check...")
    
    results = run_pca_check()
    
    output_path = get_data_path() / "results" / "pca_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"PCA results saved to {output_path}")
    return 0 if results.get("status") == "success" else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
