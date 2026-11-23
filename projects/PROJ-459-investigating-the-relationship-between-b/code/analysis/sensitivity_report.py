"""
Sensitivity Report Generation for US2.

Generates a SensitivityReport JSON/Parquet containing stability metrics and ICC values
derived from the sensitivity analysis run across different window sizes.

Output: data/derived/sensitivity_report.json
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from config import get_derived_path
from utils.io import save_json, save_parquet, ensure_dir
from data.models import SensitivityReport as SensitivityReportModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_sensitivity_report(
    metrics_by_window: Dict[int, Dict[str, float]],
    icc_values: Dict[str, float],
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a SensitivityReport dictionary and save it to disk.
    
    Args:
        metrics_by_window: Dictionary mapping window_size (int) to a dict of metric values.
        icc_values: Dictionary mapping metric_name to ICC score.
        output_path: Optional path to save the report. Defaults to config derived path.
        
    Returns:
        The generated report dictionary.
    """
    if output_path is None:
        output_path = get_derived_path("sensitivity_report.json")
    
    ensure_dir(output_path.parent)
    
    # Structure the report according to the SensitivityReport model expectations
    # The model defines: window_size, icc, and potentially other stability metrics
    report_data = {
        "analysis_type": "sensitivity_analysis",
        "window_sizes_analyzed": sorted(metrics_by_window.keys()),
        "icc_results": []
    }
    
    # Convert ICC values into the list of SensitivityReport objects structure
    # Assuming the 'icc_values' dict contains per-metric ICCs, we aggregate or list them.
    # If the model expects a list of objects per window, we structure accordingly.
    # Based on T027, compute_icc returns a value. Here we aggregate across metrics or per metric.
    # We will structure it as a list of sensitivity entries per metric.
    
    # Flatten metrics to compute stability (e.g., std dev across windows)
    all_metrics = set()
    for w_metrics in metrics_by_window.values():
        all_metrics.update(w_metrics.keys())
        
    stability_metrics = {}
    for metric_name in all_metrics:
        values = []
        for w in sorted(metrics_by_window.keys()):
            if metric_name in metrics_by_window[w]:
                values.append(metrics_by_window[w][metric_name])
        if len(values) > 1:
            stability_metrics[metric_name] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "cv": float(np.std(values) / np.mean(values)) if np.mean(values) != 0 else 0.0,
                "values": values,
                "window_sizes": sorted(metrics_by_window.keys())
            }
    
    report_data["stability_metrics"] = stability_metrics
    
    # Add ICC results
    for metric_name, icc_val in icc_values.items():
        report_data["icc_results"].append({
            "metric": metric_name,
            "icc": float(icc_val),
            "stability_category": "stable" if icc_val > 0.75 else "moderate" if icc_val > 0.5 else "unstable"
        })
    
    # Save as JSON
    save_json(report_data, output_path)
    logger.info(f"Sensitivity report saved to {output_path}")
    
    # Also save a Parquet version if needed for downstream analysis (optional but good practice)
    parquet_path = output_path.with_suffix(".parquet")
    # Flatten for parquet: one row per metric per window
    rows = []
    for w, w_metrics in metrics_by_window.items():
        for m, v in w_metrics.items():
            rows.append({
                "window_size": w,
                "metric_name": m,
                "value": v,
                "icc": icc_values.get(m, None)
            })
    df = pd.DataFrame(rows)
    save_parquet(df, parquet_path)
    logger.info(f"Sensitivity data saved to {parquet_path}")
    
    return report_data

def main():
    """
    Entry point to generate the sensitivity report.
    
    This function assumes that the sensitivity analysis (T026) and ICC calculation (T027)
    have already been performed and the results are available in the state or
    passed via arguments. For this task, we simulate the retrieval of these results
    from the expected output of T026/T027 if they were run, or we construct the
    report structure to be filled by the pipeline orchestrator.
    
    However, per the task requirement to "Generate ... with stability metrics and ICC values",
    and assuming the pipeline has run T026/T026 previously, we need to load those intermediate
    results. Since T026/T027 outputs are not explicitly defined as files in the prompt,
    we assume the data is passed or we re-run the analysis logic if inputs are available.
    
    In a real pipeline, T026 would save `data/derived/sensitivity_metrics.json` and T027
    would save `data/derived/icc_results.json`. We will attempt to load these.
    If they don't exist, we raise an error as we cannot fabricate data.
    """
    # Expected intermediate file paths (convention based on project structure)
    metrics_path = get_derived_path("sensitivity_metrics.json")
    icc_path = get_derived_path("icc_results.json")
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Required intermediate file not found: {metrics_path}. "
                                "Please ensure T026 (Sensitivity Analysis) has been run.")
    if not icc_path.exists():
        raise FileNotFoundError(f"Required intermediate file not found: {icc_path}. "
                                "Please ensure T027 (ICC Calculation) has been run.")
    
    # Load intermediate results
    metrics_by_window = load_json(metrics_path)
    icc_values = load_json(icc_path)
    
    # Generate and save final report
    report = generate_sensitivity_report(metrics_by_window, icc_values)
    
    logger.info("Sensitivity report generation completed successfully.")
    return report

if __name__ == "__main__":
    main()
