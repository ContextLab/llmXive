import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from utils import read_json, write_json, get_logger
from config import ensure_directories

logger = get_logger(__name__)

def load_existing_results(results_dir: Path) -> Dict[str, Any]:
    """
    Load existing results from modeling pipeline.
    Expects:
      - data/results/delta_r2.json
      - data/results/diagnostics.json (optional, for context)
      - data/results/null_distribution_stats.json (if T021/T022 produced it separately)
    """
    results = {}
    
    delta_r2_path = results_dir / "delta_r2.json"
    if delta_r2_path.exists():
        results["delta_r2"] = read_json(delta_r2_path)
    else:
        logger.warning(f"Delta R² file not found at {delta_r2_path}. Skipping delta_r2 in report.")
    
    diagnostics_path = results_dir / "diagnostics.json"
    if diagnostics_path.exists():
        results["diagnostics"] = read_json(diagnostics_path)
    else:
        logger.warning(f"Diagnostics file not found at {diagnostics_path}. Skipping diagnostics in report.")
    
    # The modeling.py main() should have written the primary model stats and null stats
    # We assume they are aggregated in a single file or we reconstruct from known outputs.
    # Based on T019/T020/T021/T022, we expect:
    # - data/results/model_metrics.json (or similar) with MAE, r, R2
    # - data/results/null_stats.json with null mean, std, p-value
    
    model_metrics_path = results_dir / "model_metrics.json"
    if model_metrics_path.exists():
        results["model_metrics"] = read_json(model_metrics_path)
    else:
        # Fallback: try to find any json with metrics if naming differs
        logger.warning(f"Model metrics file not found at {model_metrics_path}. "
                       "Assuming modeling.py main() did not produce it or used different name.")
    
    null_stats_path = results_dir / "null_stats.json"
    if null_stats_path.exists():
        results["null_stats"] = read_json(null_stats_path)
    else:
        logger.warning(f"Null stats file not found at {null_stats_path}. "
                       "Assuming null distribution stats not produced separately.")
    
    return results

def compute_null_distribution_stats(null_maes: np.ndarray, observed_mae: float) -> Dict[str, Any]:
    """
    Compute statistics for the null distribution and empirical p-value.
    
    Args:
        null_maes: Array of MAEs from permuted (null) models.
        observed_mae: MAE from the real model.
    
    Returns:
        Dictionary with null_mean, null_std, p_value, and null_distribution_stats.
    """
    if len(null_maes) == 0:
        raise ValueError("Null MAEs array is empty. Cannot compute statistics.")
    
    null_mean = float(np.mean(null_maes))
    null_std = float(np.std(null_maes))
    
    # Empirical p-value: proportion of null MAEs <= observed MAE
    # (Lower MAE is better, so we count how often null performed as well or better than observed)
    p_value = float(np.mean(null_maes <= observed_mae))
    
    return {
        "null_mean": null_mean,
        "null_std": null_std,
        "p_value": p_value,
        "null_distribution_stats": {
            "count": len(null_maes),
            "min": float(np.min(null_maes)),
            "max": float(np.max(null_maes)),
            "median": float(np.median(null_maes))
        }
    }

def generate_model_report(
    model_metrics: Dict[str, Any],
    null_stats: Optional[Dict[str, Any]],
    delta_r2: Optional[Dict[str, Any]],
    diagnostics: Optional[Dict[str, Any]],
    output_path: Path
) -> Dict[str, Any]:
    """
    Aggregate all results into a single model report JSON.
    
    Args:
        model_metrics: Dict with keys like 'mae', 'pearson_r', 'r2', 'best_alpha', etc.
        null_stats: Dict with 'p_value', 'null_mean', 'null_std', etc.
        delta_r2: Dict with 'delta_r2' value.
        diagnostics: Dict with VIF values and correlations.
        output_path: Path to write the final report.
    
    Returns:
        The complete report dictionary (also written to output_path).
    """
    report = {
        "report_type": "model_report",
        "version": "1.0",
        "metrics": {},
        "null_distribution": {},
        "reduced_model_analysis": {},
        "collinearity_diagnostics": {}
    }
    
    # Primary model metrics
    if model_metrics:
        report["metrics"] = {
            "mean_out_of_fold_mae": model_metrics.get("mean_out_of_fold_mae"),
            "pearson_r": model_metrics.get("pearson_r"),
            "r_squared": model_metrics.get("r_squared"),
            "best_alpha": model_metrics.get("best_alpha"),
            "n_folds": model_metrics.get("n_folds", 5)
        }
    else:
        logger.error("No model metrics provided. Report will be incomplete.")
    
    # Null distribution stats and p-value
    if null_stats:
        report["null_distribution"] = {
            "p_value": null_stats.get("p_value"),
            "null_mean_mae": null_stats.get("null_mean"),
            "null_std_mae": null_stats.get("null_std"),
            "distribution_details": null_stats.get("null_distribution_stats", {})
        }
    else:
        logger.warning("No null stats provided. P-value and null distribution will be missing.")
    
    # Reduced model analysis (Delta R²)
    if delta_r2:
        report["reduced_model_analysis"] = {
            "delta_r2": delta_r2.get("delta_r2"),
            "full_model_r2": delta_r2.get("full_model_r2"),
            "reduced_model_r2": delta_r2.get("reduced_model_r2")
        }
    else:
        logger.warning("No delta_r2 data provided. Reduced model analysis will be missing.")
    
    # Collinearity diagnostics
    if diagnostics:
        report["collinearity_diagnostics"] = {
            "vif_values": diagnostics.get("vif_values", {}),
            "gsa_fd_correlation": diagnostics.get("gsa_fd_correlation"),
            "flags": diagnostics.get("flags", [])
        }
    else:
        logger.warning("No diagnostics data provided. Collinearity diagnostics will be missing.")
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    # Write report to file
    write_json(output_path, report)
    logger.info(f"Model report written to {output_path}")
    
    return report

def main():
    """
    Main entry point to generate the model report.
    Loads results from previous steps (T019-T024) and aggregates them.
    """
    project_root = Path(__file__).parent.parent
    results_dir = project_root / "data" / "results"
    
    # Ensure results directory exists
    ensure_directories([results_dir])
    
    # Load existing results
    results = load_existing_results(results_dir)
    
    model_metrics = results.get("model_metrics", {})
    null_stats = results.get("null_stats", {})
    delta_r2 = results.get("delta_r2", {})
    diagnostics = results.get("diagnostics", {})
    
    # If null_stats is missing but we have null_maes in model_metrics (unlikely), handle it
    # For now, assume null_stats is separate or we need to compute it if data exists.
    # If null_stats is empty but model_metrics has observed_mae and we have null_maes elsewhere,
    # we would need to fetch null_maes. Since T021/T022 should have produced null_stats.json,
    # we proceed with what we have.
    
    output_path = results_dir / "model_report.json"
    report = generate_model_report(
        model_metrics=model_metrics,
        null_stats=null_stats if null_stats else None,
        delta_r2=delta_r2 if delta_r2 else None,
        diagnostics=diagnostics if diagnostics else None,
        output_path=output_path
    )
    
    # Log summary
    logger.info("=== Model Report Summary ===")
    if report["metrics"].get("pearson_r") is not None:
        logger.info(f"Primary Model Pearson r: {report['metrics']['pearson_r']:.4f}")
    if report["metrics"].get("r_squared") is not None:
        logger.info(f"Primary Model R²: {report['metrics']['r_squared']:.4f}")
    if report["metrics"].get("mean_out_of_fold_mae") is not None:
        logger.info(f"Mean Out-of-Fold MAE: {report['metrics']['mean_out_of_fold_mae']:.4f}")
    if report["null_distribution"].get("p_value") is not None:
        logger.info(f"Empirical P-value: {report['null_distribution']['p_value']:.4f}")
    if report["reduced_model_analysis"].get("delta_r2") is not None:
        logger.info(f"Delta R² (GSA effect): {report['reduced_model_analysis']['delta_r2']:.4f}")
    
    return report

if __name__ == "__main__":
    main()
