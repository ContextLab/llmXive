"""
Aggregate Results Module (T030d)

Aggregates all statistics from previous analysis steps into a single
`data/processed/analysis_results.json` file.

Imports from this module:
  - load_json_file
  - load_csv_file
  - aggregate_analysis_results
  - save_aggregated_results
  - main
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its content as a dictionary."""
    if not file_path.exists():
        logger.warning(f"JSON file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return None

def load_csv_file(file_path: Path) -> Optional[pd.DataFrame]:
    """Load a CSV file and return it as a DataFrame."""
    if not file_path.exists():
        logger.warning(f"CSV file not found: {file_path}")
        return None
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {e}")
        return None

def aggregate_analysis_results(
    correlation_stats: Optional[Dict[str, Any]],
    regression_stats: Optional[Dict[str, Any]],
    mdc_stats: Optional[Dict[str, Any]],
    bootstrap_ci: Optional[Dict[str, Any]],
    robustness_report: Optional[Dict[str, Any]],
    sample_size_report: Optional[Dict[str, Any]],
    metadata_df: Optional[pd.DataFrame]
) -> Dict[str, Any]:
    """
    Aggregate all analysis statistics into a single dictionary.
    
    Args:
        correlation_stats: Result from T030a
        regression_stats: Result from T030b
        mdc_stats: Result from T030c
        bootstrap_ci: Result from T025c
        robustness_report: Result from T026
        sample_size_report: Result from T013b
        metadata_df: Metadata DataFrame from T012
    
    Returns:
        Dictionary containing all aggregated results.
    """
    aggregated = {
        "pipeline_version": "1.0.0",
        "task_id": "T030d",
        "description": "Aggregated analysis results for exoplanetary atmosphere characterization",
        "summary": {},
        "correlation": {},
        "regression": {},
        "mdc": {},
        "bootstrap": {},
        "robustness": {},
        "sample_size": {},
        "instrument_summary": {}
    }

    # Correlation Statistics
    if correlation_stats:
        aggregated["correlation"] = correlation_stats
        aggregated["summary"]["kendall_tau"] = correlation_stats.get("kendall_tau")
        aggregated["summary"]["p_value"] = correlation_stats.get("p_value")

    # Regression Statistics
    if regression_stats:
        aggregated["regression"] = regression_stats
        # Extract key coefficients if available
        if "coefficients" in regression_stats:
            aggregated["summary"]["regression_coefficients"] = regression_stats["coefficients"]

    # MDC Statistics
    if mdc_stats:
        aggregated["mdc"] = mdc_stats
        aggregated["summary"]["global_mdc_95th"] = mdc_stats.get("global_95th_percentile_mdc")

    # Bootstrap Confidence Intervals
    if bootstrap_ci:
        aggregated["bootstrap"] = bootstrap_ci
        aggregated["summary"]["bootstrap_iterations"] = bootstrap_ci.get("iterations")
        aggregated["summary"]["ci_lower"] = bootstrap_ci.get("ci_lower")
        aggregated["summary"]["ci_upper"] = bootstrap_ci.get("ci_upper")

    # Robustness Report
    if robustness_report:
        aggregated["robustness"] = robustness_report
        aggregated["summary"]["ci_width_threshold_met"] = robustness_report.get("threshold_met")
        aggregated["summary"]["ci_width"] = robustness_report.get("ci_width")

    # Sample Size Report
    if sample_size_report:
        aggregated["sample_size"] = sample_size_report
        aggregated["summary"]["sample_size"] = sample_size_report.get("count")
        aggregated["summary"]["validation_status"] = sample_size_report.get("validation_status")

    # Instrument Summary from Metadata
    if metadata_df is not None and not metadata_df.empty:
        if 'instrument' in metadata_df.columns:
            instrument_counts = metadata_df['instrument'].value_counts().to_dict()
            aggregated["instrument_summary"] = {
                "instruments": instrument_counts,
                "total_observations": len(metadata_df)
            }
        
        # Calculate median resolution if available
        if 'resolution' in metadata_df.columns:
            median_res = metadata_df['resolution'].median()
            min_res = metadata_df['resolution'].min()
            max_res = metadata_df['resolution'].max()
            aggregated["instrument_summary"]["resolution_stats"] = {
                "median": median_res,
                "min": min_res,
                "max": max_res
            }

    return aggregated

def save_aggregated_results(aggregated: Dict[str, Any], output_path: Path) -> bool:
    """
    Save aggregated results to a JSON file.
    
    Args:
        aggregated: The aggregated dictionary to save.
        output_path: Path to the output JSON file.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(aggregated, f, indent=2, default=str)
        logger.info(f"Aggregated results saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving aggregated results to {output_path}: {e}")
        return False

def main():
    """Main entry point for T030d."""
    config = get_config()
    output_path = Path(config.get("data_processed_dir", "data/processed")) / "analysis_results.json"
    
    logger.info("Starting T030d: Aggregate all statistics into analysis_results.json")
    
    # Define paths to input files
    correlation_stats_path = Path(config.get("data_processed_dir", "data/processed")) / "correlation_stats.json"
    regression_stats_path = Path(config.get("data_processed_dir", "data/processed")) / "regression_stats.json"
    mdc_stats_path = Path(config.get("data_processed_dir", "data/processed")) / "mdc_stats.json"
    bootstrap_ci_path = Path(config.get("data_processed_dir", "data/processed")) / "bootstrap_ci.json"
    robustness_report_path = Path(config.get("results_dir", "results")) / "robustness_report.json"
    sample_size_report_path = Path(config.get("data_processed_dir", "data/processed")) / "sample_size_report.json"
    metadata_path = Path(config.get("data_processed_dir", "data/processed")) / "metadata.csv"
    
    # Load inputs
    correlation_stats = load_json_file(correlation_stats_path)
    regression_stats = load_json_file(regression_stats_path)
    mdc_stats = load_json_file(mdc_stats_path)
    bootstrap_ci = load_json_file(bootstrap_ci_path)
    robustness_report = load_json_file(robustness_report_path)
    sample_size_report = load_json_file(sample_size_report_path)
    metadata_df = load_csv_file(metadata_path)
    
    # Check if any critical inputs are missing
    missing = []
    if not correlation_stats: missing.append("correlation_stats.json")
    if not regression_stats: missing.append("regression_stats.json")
    if not mdc_stats: missing.append("mdc_stats.json")
    if not bootstrap_ci: missing.append("bootstrap_ci.json")
    if not robustness_report: missing.append("robustness_report.json")
    if not sample_size_report: missing.append("sample_size_report.json")
    if metadata_df is None: missing.append("metadata.csv")
    
    if missing:
        logger.error(f"Missing critical input files: {missing}")
        # We proceed with what we have, but log the warning
    
    # Aggregate
    aggregated = aggregate_analysis_results(
        correlation_stats=correlation_stats,
        regression_stats=regression_stats,
        mdc_stats=mdc_stats,
        bootstrap_ci=bootstrap_ci,
        robustness_report=robustness_report,
        sample_size_report=sample_size_report,
        metadata_df=metadata_df
    )
    
    # Save
    success = save_aggregated_results(aggregated, output_path)
    
    if success:
        logger.info("T030d completed successfully.")
    else:
        logger.error("T030d failed to save output.")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())