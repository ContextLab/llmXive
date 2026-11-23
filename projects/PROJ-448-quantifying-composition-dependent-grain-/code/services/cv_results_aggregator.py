import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from code.config import PROCESSED_PATH, get_logger

logger = get_logger(__name__)

def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary as a JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def aggregate_cross_validation_results(
    cv_metrics_path: Path,
    transferability_path: Optional[Path] = None,
    overfitting_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Aggregate cross-validation results from multiple sources into a comprehensive report.
    
    Args:
        cv_metrics_path: Path to cv_metrics.json containing per-fold metrics
        transferability_path: Optional path to transferability results
        overfitting_path: Optional path to overfitting detection results
    
    Returns:
        Dictionary containing aggregated cross-validation results
    """
    # Load CV metrics
    cv_metrics = load_json_file(cv_metrics_path)
    
    # Structure the results
    results = {
        "source": "cross_validation_aggregation",
        "timestamp": cv_metrics.get("timestamp", "N/A"),
        "summary": {
            "mean_r2": cv_metrics.get("mean_r2"),
            "std_r2": cv_metrics.get("std_r2"),
            "mean_mse": cv_metrics.get("mean_mse"),
            "std_mse": cv_metrics.get("std_mse"),
            "num_folds": cv_metrics.get("num_folds", 0),
            "validation_passed": cv_metrics.get("validation_passed", False)
        },
        "fold_details": cv_metrics.get("fold_details", []),
        "transferability": None,
        "overfitting_analysis": None,
        "warnings": []
    }
    
    # Add transferability results if available
    if transferability_path and transferability_path.exists():
        try:
            transfer_data = load_json_file(transferability_path)
            results["transferability"] = {
                "train_system": transfer_data.get("train_system"),
                "test_system": transfer_data.get("test_system"),
                "test_r2": transfer_data.get("test_r2"),
                "test_mse": transfer_data.get("test_mse"),
                "status": transfer_data.get("status")
            }
            logger.info(f"Transferability check: {transfer_data.get('status')}")
        except Exception as e:
            logger.warning(f"Failed to load transferability results: {e}")
            results["warnings"].append(f"Transferability data loading failed: {e}")
    
    # Add overfitting analysis if available
    if overfitting_path and overfitting_path.exists():
        try:
            overfit_data = load_json_file(overfitting_path)
            results["overfitting_analysis"] = {
                "is_overfitting": overfit_data.get("is_overfitting"),
                "train_score": overfit_data.get("train_score"),
                "val_score": overfit_data.get("val_score"),
                "score_difference": overfit_data.get("score_difference"),
                "status": overfit_data.get("status")
            }
            if overfit_data.get("is_overfitting"):
                results["warnings"].append("Overfitting detected: High training score with low validation score")
            logger.info(f"Overfitting check: {overfit_data.get('status')}")
        except Exception as e:
            logger.warning(f"Failed to load overfitting results: {e}")
            results["warnings"].append(f"Overfitting data loading failed: {e}")
    
    # Validate overall quality
    if results["summary"]["std_r2"] is not None and results["summary"]["std_r2"] > 0.05:
        results["warnings"].append(f"High variance in CV scores (std={results['summary']['std_r2']:.4f}): Model may be unstable")
    
    return results

def main():
    """Main entry point for aggregating cross-validation results."""
    try:
        # Define paths
        cv_metrics_path = PROCESSED_PATH / "cv_metrics.json"
        transferability_path = PROCESSED_PATH / "transferability_results.json"
        overfitting_path = PROCESSED_PATH / "overfitting_report.json"
        output_path = PROCESSED_PATH / "cross_validation_results.json"
        
        logger.info("Starting cross-validation results aggregation...")
        
        # Aggregate results
        results = aggregate_cross_validation_results(
            cv_metrics_path,
            transferability_path,
            overfitting_path
        )
        
        # Save aggregated results
        save_json_file(output_path, results)
        
        logger.info(f"Cross-validation results saved to {output_path}")
        logger.info(f"Summary: Mean R²={results['summary']['mean_r2']:.4f}, "
                   f"Std R²={results['summary']['std_r2']:.4f}, "
                   f"Folds={results['summary']['num_folds']}")
        
        if results["warnings"]:
            logger.warning(f"Generated {len(results['warnings'])} warnings:")
            for warning in results["warnings"]:
                logger.warning(f"  - {warning}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
