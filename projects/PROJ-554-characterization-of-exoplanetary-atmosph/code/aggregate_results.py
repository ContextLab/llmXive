import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Dictionary containing the JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r') as f:
        return json.load(f)

def load_csv_file(file_path: Path) -> pd.DataFrame:
    """
    Load a CSV file and return its contents as a DataFrame.

    Args:
        file_path: Path to the CSV file.

    Returns:
        DataFrame containing the CSV data.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return pd.read_csv(file_path)

def aggregate_analysis_results(
    correlation_stats: Dict[str, Any],
    regression_results: Dict[str, Any],
    mdc_stats: Dict[str, Any],
    robustness_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate analysis results from multiple sources into a single object.

    Args:
        correlation_stats: Results from correlation analysis (T025b).
        regression_results: Results from regression analysis (T027).
        mdc_stats: Results from MDC statistics (T030a).
        robustness_report: Results from robustness checks (T028).

    Returns:
        Aggregated dictionary containing all analysis results.
    """
    logger.info("Aggregating analysis results...")

    aggregated = {
        "correlation_analysis": correlation_stats,
        "regression_analysis": regression_results,
        "mdc_statistics": mdc_stats,
        "robustness_checks": robustness_report
    }

    logger.info(f"Aggregated results contain keys: {list(aggregated.keys())}")
    return aggregated

def save_aggregated_results(
    aggregated_results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save aggregated analysis results to a JSON file.

    Args:
        aggregated_results: Dictionary containing aggregated results.
        output_path: Path to the output JSON file.
    """
    logger.info(f"Saving aggregated results to: {output_path}")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(aggregated_results, f, indent=2)

    logger.info("Successfully saved aggregated results")

def main():
    """
    Main function to generate analysis results by aggregating data from
    correlation_stats.json, regression_results.json, mdc_stats.json, and
    robustness_report.json.
    """
    config = get_config()
    processed_dir = Path(config.data_dir) / "processed"

    # Define input file paths
    correlation_stats_path = processed_dir / "correlation_stats.json"
    regression_results_path = processed_dir / "regression_results.json"
    mdc_stats_path = processed_dir / "mdc_stats.json"
    robustness_report_path = processed_dir / "robustness_report.json"

    # Define output file path
    output_path = processed_dir / "analysis_results.json"

    try:
        # Load input files
        logger.info(f"Loading correlation stats from: {correlation_stats_path}")
        correlation_stats = load_json_file(correlation_stats_path)

        logger.info(f"Loading regression results from: {regression_results_path}")
        regression_results = load_json_file(regression_results_path)

        logger.info(f"Loading MDC stats from: {mdc_stats_path}")
        mdc_stats = load_json_file(mdc_stats_path)

        logger.info(f"Loading robustness report from: {robustness_report_path}")
        robustness_report = load_json_file(robustness_report_path)

        # Aggregate results
        aggregated_results = aggregate_analysis_results(
            correlation_stats=correlation_stats,
            regression_results=regression_results,
            mdc_stats=mdc_stats,
            robustness_report=robustness_report
        )

        # Save aggregated results
        save_aggregated_results(aggregated_results, output_path)

        logger.info("Analysis results aggregation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        raise

if __name__ == "__main__":
    main()