import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import log_stage_start, log_stage_complete, log_stage_error, log_event
from config import get_paths

def load_result_report(path: str) -> Dict[str, Any]:
    """Load existing result report or return empty structure."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {
        "metadata": {},
        "model_metrics": {},
        "permutation_test": {},
        "bootstrap_ci": {},
        "sensitivity_analysis": {},
        "interpretation": {},
        "visualization": {}
    }

def save_result_report(report: Dict[str, Any], path: str) -> None:
    """Save result report to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    log_event("Result report saved", {"path": path})

def load_permutation_p_value(path: str) -> Optional[float]:
    """Load permutation test p-value."""
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get("approximate_p_value")

def load_bootstrap_ci(path: str) -> Optional[Dict[str, Any]]:
    """Load bootstrap confidence interval results."""
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def load_model_metrics(path: str) -> Optional[Dict[str, Any]]:
    """Load model metrics from training."""
    # For now, we assume metrics are embedded in the main report or derived
    # In a full implementation, this might load from a specific metrics file
    return None

def load_sensitivity_results(path: str) -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis results."""
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def generate_result_report(
    permutation_p_value: Optional[float] = None,
    bootstrap_ci: Optional[Dict[str, Any]] = None,
    sensitivity_results: Optional[Dict[str, Any]] = None,
    plot_path: Optional[str] = None,
    model_metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate the final ResultReport.json combining all analysis results.
    """
    paths = get_paths()
    report = load_result_report(paths["result_report"])

    # Update metadata
    report["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "pipeline_version": "1.0.0",
        "notes": "Bootstrap CI is an approximation based on outer-fold predictions."
    }

    # Update permutation test section
    if permutation_p_value is not None:
        report["permutation_test"] = {
            "approximate_p_value": permutation_p_value,
            "note": "Approximation derived from 100-subject stratified subset (Plan Override of FR-006)"
        }

    # Update bootstrap CI section
    if bootstrap_ci is not None:
        report["bootstrap_ci"] = {
            "r2_original": bootstrap_ci.get("r2_original"),
            "ci_lower": bootstrap_ci.get("ci_lower"),
            "ci_upper": bootstrap_ci.get("ci_upper"),
            "confidence_level": bootstrap_ci.get("confidence_level"),
            "n_resamples": bootstrap_ci.get("n_resamples"),
            "note": "Computed via 1000 bootstrap resamples of outer-fold predictions"
        }

    # Update sensitivity analysis section
    if sensitivity_results is not None:
        report["sensitivity_analysis"] = sensitivity_results

    # Update visualization section
    if plot_path is not None and os.path.exists(plot_path):
        report["visualization"] = {
            "plot_path": plot_path,
            "format": "svg" if plot_path.endswith(".svg") else "png"
        }

    # Update model metrics if provided
    if model_metrics:
        report["model_metrics"] = model_metrics

    return report

def finalize_report() -> None:
    """
    Finalize the ResultReport.json by loading all component results and combining them.
    """
    log_stage_start("Finalizing ResultReport.json")
    paths = get_paths()

    try:
        # Load individual components
        perm_p_val = load_permutation_p_value(paths["permutation_results"])
        boot_ci = load_bootstrap_ci(paths["bootstrap_ci"])
        sens_results = load_sensitivity_results(paths["sensitivity_results"])
        
        # Check if plot exists
        plot_path = paths["plot_file"] if os.path.exists(paths["plot_file"]) else None

        # Generate combined report
        report = generate_result_report(
            permutation_p_value=perm_p_val,
            bootstrap_ci=boot_ci,
            sensitivity_results=sens_results,
            plot_path=plot_path
        )

        # Save final report
        save_result_report(report, paths["result_report"])

        log_stage_complete("ResultReport.json finalized", {"path": paths["result_report"]})
        print(f"Final report saved to: {paths['result_report']}")

    except Exception as e:
        log_stage_error("Failed to finalize report", str(e))
        raise

def main():
    """Entry point for report generation."""
    finalize_report()

if __name__ == "__main__":
    main()