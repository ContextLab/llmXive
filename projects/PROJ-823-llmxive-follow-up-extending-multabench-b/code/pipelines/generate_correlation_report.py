import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import hashlib

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import setup_logging, get_logger, log_info, log_error, log_debug
from analysis.correlation_analysis import load_correlation_data, calculate_pearson_correlations, save_correlation_results
from analysis.fdr_correction import load_p_values_from_file, process_correlation_p_values, process_t_test_p_values
from analysis.t_test_analysis import aggregate_conditioned_metrics, load_gpu_baselines

def load_fdr_adjusted_pvalues(fdr_output_path: str) -> dict:
    """Load FDR adjusted p-values from the JSON output of T034."""
    if not os.path.exists(fdr_output_path):
        log_warning(f"FDR output file not found at {fdr_output_path}. Proceeding with raw p-values.")
        return {}
    
    with open(fdr_output_path, 'r') as f:
        data = json.load(f)
    
    # Structure expected: {"correlations": {...}, "t_tests": {...}}
    return data

def load_t_test_results(t_test_output_path: str) -> dict:
    """Load t-test results to extract significance flags and statistics."""
    if not os.path.exists(t_test_output_path):
        log_warning(f"T-test output file not found at {t_test_output_path}. Proceeding without t-test stats.")
        return {}
    
    with open(t_test_output_path, 'r') as f:
        return json.load(f)

def generate_report(
    correlation_results_path: str,
    fdr_output_path: str,
    t_test_output_path: str,
    output_path: str,
    run_id: str
):
    """
    Generate the final correlation report JSON.
    Combines:
    1. Pearson correlations (coefficients, p-values)
    2. FDR adjusted p-values
    3. T-test results (significance flags)
    """
    logger = get_logger()
    
    # 1. Load Correlation Data
    logger.info(f"Loading correlation results from {correlation_results_path}")
    try:
        correlation_data = load_correlation_data(correlation_results_path)
    except Exception as e:
        log_error(f"Failed to load correlation results: {e}")
        raise

    # 2. Load FDR Adjusted P-values
    logger.info(f"Loading FDR adjusted p-values from {fdr_output_path}")
    fdr_data = load_fdr_adjusted_pvalues(fdr_output_path)
    
    # 3. Load T-test Results
    logger.info(f"Loading T-test results from {t_test_output_path}")
    t_test_data = load_t_test_results(t_test_output_path)

    # 4. Construct Final Report
    report = {
        "run_id": run_id,
        "generated_at": datetime.utcnow().isoformat(),
        "methodology": {
            "correlation_method": "Pearson",
            "fdr_method": "Benjamini-Hochberg",
            "statistical_test": "One-sample t-test (or Wilcoxon)"
        },
        "correlations": {}
    }

    # Map FDR and T-test results to correlations
    # Assuming correlation results structure: { "feature": { "coef": float, "p_value": float } }
    # And FDR results structure: { "correlations": { "feature": float } }
    
    features = correlation_data.get("correlations", {})
    
    for feature, stats in features.items():
        entry = {
            "coefficient": stats.get("coefficient"),
            "raw_p_value": stats.get("p_value"),
            "fdr_adjusted_p_value": None,
            "is_significant_fdr": False,
            "t_test_p_value": None,
            "t_test_significant": False,
            "t_test_statistic": None
        }

        # Apply FDR correction
        if "correlations" in fdr_data:
            adj_p = fdr_data["correlations"].get(feature)
            if adj_p is not None:
                entry["fdr_adjusted_p_value"] = adj_p
                entry["is_significant_fdr"] = adj_p < 0.05

        # Apply T-test results
        if "results" in t_test_data:
            t_stats = t_test_data["results"].get(feature, {})
            if t_stats:
                entry["t_test_p_value"] = t_stats.get("p_value")
                entry["t_test_statistic"] = t_stats.get("statistic")
                # Significance usually defined by p < 0.05
                entry["t_test_significant"] = t_stats.get("p_value", 1.0) < 0.05

        report["correlations"][feature] = entry

    # Add summary of significant findings
    significant_features = [
        f for f, v in report["correlations"].items() 
        if v["is_significant_fdr"] or v["t_test_significant"]
    ]
    report["summary"] = {
        "total_features_tested": len(features),
        "significant_features_count": len(significant_features),
        "significant_features": significant_features
    }

    # 5. Save Report
    ensure_directories()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Correlation report saved to {output_file}")
    return report

def main():
    parser = argparse.ArgumentParser(description="Generate final correlation report with FDR and T-test integration.")
    parser.add_argument("--correlation-results", type=str, required=True, 
                        help="Path to correlation results JSON (from T033/correlation_analysis)")
    parser.add_argument("--fdr-output", type=str, required=True, 
                        help="Path to FDR adjusted p-values JSON (from T034)")
    parser.add_argument("--t-test-output", type=str, required=True, 
                        help="Path to T-test results JSON (from T035)")
    parser.add_argument("--output", type=str, required=True, 
                        help="Path to save the final report JSON")
    parser.add_argument("--run-id", type=str, default=None, 
                        help="Run ID for the report (defaults to timestamp if not provided)")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger = get_logger()
    
    # Determine Run ID
    run_id = args.run_id
    if not run_id:
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    log_info(f"Starting Correlation Report Generation for Run ID: {run_id}")
    
    try:
        generate_report(
            correlation_results_path=args.correlation_results,
            fdr_output_path=args.fdr_output,
            t_test_output_path=args.t_test_output,
            output_path=args.output,
            run_id=run_id
        )
        log_info("Report generation completed successfully.")
    except Exception as e:
        log_error(f"Failed to generate report: {e}")
        raise

if __name__ == "__main__":
    main()