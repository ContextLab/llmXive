import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from config import get_config

logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return {}

def load_csv_file(file_path: Path) -> pd.DataFrame:
    """Load a CSV file and return it as a DataFrame."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        return pd.DataFrame()

def aggregate_analysis_results(
    correlation_stats: Dict[str, Any],
    regression_stats: Dict[str, Any],
    mdc_stats: Dict[str, Any],
    bootstrap_ci: Dict[str, Any],
    robustness_report: Dict[str, Any],
    power_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Aggregate all statistics into a single analysis results dictionary.
    
    This function combines outputs from T030a, T030b, T030c, T025c, T026, and T031
    into the final deliverable for T030d.
    """
    aggregated = {
        "summary": {
            "total_planets": correlation_stats.get("total_planets", 0),
            "censored_count": correlation_stats.get("censored_count", 0),
            "uncensored_count": correlation_stats.get("uncensored_count", 0),
        },
        "correlation_analysis": {
            "kendall_tau": correlation_stats.get("kendall_tau"),
            "p_value": correlation_stats.get("p_value"),
            "ci_width": correlation_stats.get("ci_width"),
            "ci_lower": correlation_stats.get("ci_lower"),
            "ci_upper": correlation_stats.get("ci_upper"),
        },
        "regression_analysis": {
            "coefficients": regression_stats.get("coefficients", {}),
            "p_values": regression_stats.get("p_values", {}),
            "model_fit": regression_stats.get("model_fit", {}),
            "fallback_triggered": regression_stats.get("fallback_triggered", False),
            "fallback_reason": regression_stats.get("fallback_reason", None),
        },
        "mdc_analysis": {
            "global_95th_percentile_mdc": mdc_stats.get("global_95th_percentile_mdc"),
            "mean_mdc": mdc_stats.get("mean_mdc"),
            "min_mdc": mdc_stats.get("min_mdc"),
            "max_mdc": mdc_stats.get("max_mdc"),
        },
        "bootstrap_results": {
            "iterations": bootstrap_ci.get("iterations", 0),
            "ci_lower": bootstrap_ci.get("ci_lower"),
            "ci_upper": bootstrap_ci.get("ci_upper"),
        },
        "robustness": {
            "ci_width": robustness_report.get("ci_width"),
            "threshold_met": robustness_report.get("threshold_met", False),
            "threshold_value": 0.2,
        },
        "power_analysis": power_analysis if power_analysis else {
            "power_estimate": None,
            "power_sufficient": None,
            "note": "Power analysis not yet performed (T031 pending)"
        },
        "metadata": {
            "aggregation_timestamp": pd.Timestamp.now().isoformat(),
            "source_files": {
                "correlation_stats": "data/processed/correlation_stats.json",
                "regression_stats": "data/processed/regression_stats.json",
                "mdc_stats": "data/processed/mdc_stats.json",
                "bootstrap_ci": "data/processed/bootstrap_ci.json",
                "robustness_report": "results/robustness_report.json",
            }
        }
    }
    return aggregated

def save_aggregated_results(data: Dict[str, Any], output_path: Path) -> None:
    """Save the aggregated results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Aggregated results saved to {output_path}")

def main():
    """
    Main entry point for T030d: Aggregate all statistics into analysis_results.json.
    
    This script loads intermediate results from T030a, T030b, T030c, T025c, T026,
    and optionally T031, then combines them into a single JSON file.
    """
    config = get_config()
    output_path = Path("data/processed/analysis_results.json")
    
    # Load intermediate results
    correlation_stats = load_json_file(Path("data/processed/correlation_stats.json"))
    regression_stats = load_json_file(Path("data/processed/regression_stats.json"))
    mdc_stats = load_json_file(Path("data/processed/mdc_stats.json"))
    bootstrap_ci = load_json_file(Path("data/processed/bootstrap_ci.json"))
    robustness_report = load_json_file(Path("results/robustness_report.json"))
    power_analysis = load_json_file(Path("results/power_analysis.json"))
    
    # Check if critical files are missing
    missing_files = []
    if not correlation_stats:
        missing_files.append("data/processed/correlation_stats.json")
    if not regression_stats:
        missing_files.append("data/processed/regression_stats.json")
    if not mdc_stats:
        missing_files.append("data/processed/mdc_stats.json")
    if not bootstrap_ci:
        missing_files.append("data/processed/bootstrap_ci.json")
    
    if missing_files:
        logger.warning(f"Missing intermediate result files: {missing_files}")
        logger.warning("Proceeding with aggregation using available data. "
                     "Missing files will result in null/empty values in the output.")
    
    # Aggregate
    aggregated = aggregate_analysis_results(
        correlation_stats=correlation_stats,
        regression_stats=regression_stats,
        mdc_stats=mdc_stats,
        bootstrap_ci=bootstrap_ci,
        robustness_report=robustness_report,
        power_analysis=power_analysis if power_analysis else None
    )
    
    # Save
    save_aggregated_results(aggregated, output_path)
    
    logger.info("T030d completed: Analysis results aggregated successfully.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()