"""
Aggregate analysis results from various statistical outputs into a single summary file.

This module implements T030d: Aggregate Stats. It loads results from:
- Correlation stats (T030a)
- Regression stats (T030b)
- MDC stats (T030c)
- Robustness checks (T026, T026b)

And combines them into data/processed/analysis_results.json.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import config for path handling
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}. This may be expected if the generating task has not run yet.")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path}: {e}")
        return None

def load_csv_file(file_path: Path) -> Optional[pd.DataFrame]:
    """Load a CSV file and return it as a DataFrame."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}. This may be expected if the generating task has not run yet.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path}: {e}")
        return None

def aggregate_analysis_results(
    correlation_stats: Optional[Dict[str, Any]],
    regression_stats: Optional[Dict[str, Any]],
    mdc_stats: Optional[Dict[str, Any]],
    robustness_variable: Optional[Dict[str, Any]],
    robustness_tau: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate all analysis results into a single dictionary.
    
    Args:
        correlation_stats: Results from T030a (correlation_stats.json)
        regression_stats: Results from T030b (regression_stats.json)
        mdc_stats: Results from T030c (mdc_stats.json)
        robustness_variable: Results from T026 (robustness_report_variable.json)
        robustness_tau: Results from T026b (robustness_report_tau.json)
        
    Returns:
        A dictionary containing all aggregated results.
    """
    logger.info("Aggregating analysis results...")
    
    aggregated = {
        "status": "partial",  # Will be updated to "complete" if all sources are present
        "sources_loaded": [],
        "correlation_analysis": {},
        "regression_analysis": {},
        "mdc_analysis": {},
        "robustness_checks": {
            "variable_ci_width": {},
            "tau_ci_width": {}
        },
        "summary": {}
    }
    
    # Add correlation stats
    if correlation_stats:
        aggregated["correlation_analysis"] = correlation_stats
        aggregated["sources_loaded"].append("correlation_stats.json")
    else:
        logger.warning("Correlation stats not found. Skipping correlation analysis section.")
    
    # Add regression stats
    if regression_stats:
        aggregated["regression_analysis"] = regression_stats
        aggregated["sources_loaded"].append("regression_stats.json")
    else:
        logger.warning("Regression stats not found. Skipping regression analysis section.")
    
    # Add MDC stats
    if mdc_stats:
        aggregated["mdc_analysis"] = mdc_stats
        aggregated["sources_loaded"].append("mdc_stats.json")
    else:
        logger.warning("MDC stats not found. Skipping MDC analysis section.")
    
    # Add robustness checks
    if robustness_variable:
        aggregated["robustness_checks"]["variable_ci_width"] = robustness_variable
        aggregated["sources_loaded"].append("robustness_report_variable.json")
    else:
        logger.warning("Robustness report (variable) not found.")
        
    if robustness_tau:
        aggregated["robustness_checks"]["tau_ci_width"] = robustness_tau
        aggregated["sources_loaded"].append("robustness_report_tau.json")
    else:
        logger.warning("Robustness report (tau) not found.")
    
    # Determine overall status
    required_sources = [
        "correlation_stats.json",
        "regression_stats.json",
        "mdc_stats.json",
        "robustness_report_variable.json",
        "robustness_report_tau.json"
    ]
    
    missing_sources = [src for src in required_sources if src not in aggregated["sources_loaded"]]
    if not missing_sources:
        aggregated["status"] = "complete"
        logger.info("All required sources loaded. Status: complete")
    else:
        logger.warning(f"Missing sources: {missing_sources}. Status: partial")
    
    # Generate summary
    summary = {
        "total_sources_processed": len(aggregated["sources_loaded"]),
        "missing_sources_count": len(missing_sources),
        "missing_sources": missing_sources,
        "correlation_tau": correlation_stats.get("tau") if correlation_stats else None,
        "correlation_ci_width": None,
        "regression_model_type": regression_stats.get("model_type") if regression_stats else None,
        "regression_fallback_triggered": regression_stats.get("fallback_triggered") if regression_stats else None,
        "mdc_global_95th_percentile": mdc_stats.get("global_95th_percentile") if mdc_stats else None,
        "robustness_variable_threshold_met": robustness_variable.get("threshold_met") if robustness_variable else None,
        "robustness_tau_threshold_met": robustness_tau.get("threshold_met") if robustness_tau else None
    }
    
    # Calculate CI width for correlation if available
    if correlation_stats and "ci_lower" in correlation_stats and "ci_upper" in correlation_stats:
        summary["correlation_ci_width"] = correlation_stats["ci_upper"] - correlation_stats["ci_lower"]
    
    aggregated["summary"] = summary
    
    return aggregated

def save_aggregated_results(aggregated_data: Dict[str, Any], output_path: Path) -> bool:
    """
    Save the aggregated results to a JSON file.
    
    Args:
        aggregated_data: The dictionary of aggregated results.
        output_path: The path to save the JSON file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(aggregated_data, f, indent=2)
        logger.info(f"Aggregated results saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving aggregated results to {output_path}: {e}")
        return False

def main():
    """Main entry point for the aggregation script."""
    config = get_config()
    processed_dir = Path(config.get("data_dir", "data")) / "processed"
    
    # Define paths for input files
    correlation_stats_path = processed_dir / "correlation_stats.json"
    regression_stats_path = processed_dir / "regression_stats.json"
    mdc_stats_path = processed_dir / "mdc_stats.json"
    robustness_variable_path = processed_dir / "robustness_report_variable.json"
    robustness_tau_path = processed_dir / "robustness_report_tau.json"
    
    # Define output path
    output_path = processed_dir / "analysis_results.json"
    
    logger.info(f"Loading correlation stats from {correlation_stats_path}")
    correlation_stats = load_json_file(correlation_stats_path)
    
    logger.info(f"Loading regression stats from {regression_stats_path}")
    regression_stats = load_json_file(regression_stats_path)
    
    logger.info(f"Loading MDC stats from {mdc_stats_path}")
    mdc_stats = load_json_file(mdc_stats_path)
    
    logger.info(f"Loading robustness report (variable) from {robustness_variable_path}")
    robustness_variable = load_json_file(robustness_variable_path)
    
    logger.info(f"Loading robustness report (tau) from {robustness_tau_path}")
    robustness_tau = load_json_file(robustness_tau_path)
    
    # Aggregate results
    aggregated_data = aggregate_analysis_results(
        correlation_stats=correlation_stats,
        regression_stats=regression_stats,
        mdc_stats=mdc_stats,
        robustness_variable=robustness_variable,
        robustness_tau=robustness_tau
    )
    
    # Save results
    success = save_aggregated_results(aggregated_data, output_path)
    
    if success:
        logger.info("Aggregation completed successfully.")
        return 0
    else:
        logger.error("Aggregation failed.")
        return 1

if __name__ == "__main__":
    exit(main())