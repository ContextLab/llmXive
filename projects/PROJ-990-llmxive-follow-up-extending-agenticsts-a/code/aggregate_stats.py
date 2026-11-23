import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/processed/aggregate_stats.log')
    ]
)
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file from the specified path.
    
    Args:
        filepath: Path to the JSON file.
        
    Returns:
        Dictionary containing the JSON data, or None if file not found/invalid.
    """
    path = Path(filepath)
    if not path.exists():
        logger.error(f"File not found: {filepath}")
        return None
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded {filepath}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {filepath}: {e}")
        return None

def aggregate_statistics() -> Dict[str, Any]:
    """
    Aggregate statistical results from McNemar, T-Test, and Power Analysis.
    
    Reads:
        - data/processed/mcnemar_results.json
        - data/processed/ttest_results.json
        - data/processed/power_analysis.json
    
    Writes:
        - data/processed/agg_stats.json
        
    Returns:
        Dictionary containing the aggregated statistics.
    """
    # Define file paths
    base_dir = Path("data/processed")
    mcnemar_path = base_dir / "mcnemar_results.json"
    ttest_path = base_dir / "ttest_results.json"
    power_path = base_dir / "power_analysis.json"
    output_path = base_dir / "agg_stats.json"

    # Load individual results
    logger.info("Loading statistical results...")
    mcnemar_data = load_json_file(str(mcnemar_path))
    ttest_data = load_json_file(str(ttest_path))
    power_data = load_json_file(str(power_path))

    # Check for missing data
    missing_files = []
    if mcnemar_data is None:
        missing_files.append("mcnemar_results.json")
    if ttest_data is None:
        missing_files.append("ttest_results.json")
    if power_data is None:
        missing_files.append("power_analysis.json")

    if missing_files:
        error_msg = f"Missing required input files: {', '.join(missing_files)}. Cannot aggregate statistics."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Aggregate data
    aggregated = {
        "status": "success",
        "timestamp": "generated", # Will be updated by caller if needed, or left as generic
        "tests": {
            "mcnemar": {
                "statistic": mcnemar_data.get("statistic"),
                "p_value": mcnemar_data.get("p_value"),
                "significant": mcnemar_data.get("significant", False),
                "interpretation": mcnemar_data.get("interpretation", "N/A")
            },
            "paired_ttest": {
                "statistic": ttest_data.get("statistic"),
                "p_value": ttest_data.get("p_value"),
                "significant": ttest_data.get("significant", False),
                "interpretation": ttest_data.get("interpretation", "N/A"),
                "mean_savings": ttest_data.get("mean_savings"),
                "std_savings": ttest_data.get("std_savings")
            },
            "power_analysis": {
                "sample_size": power_data.get("sample_size"),
                "achieved_power": power_data.get("achieved_power"),
                "effect_size": power_data.get("effect_size"),
                "limitation": power_data.get("limitation", "None")
            }
        },
        "summary": {
            "mcnemar_passed": mcnemar_data.get("significant", False),
            "ttest_passed": ttest_data.get("significant", False),
            "power_adequate": power_data.get("achieved_power", 0) >= 0.8,
            "overall_conclusion": "Pending full aggregation logic"
        }
    }

    # Determine overall conclusion
    if aggregated["summary"]["mcnemar_passed"] and aggregated["summary"]["ttest_passed"]:
        aggregated["summary"]["overall_conclusion"] = "Dynamic policy shows statistically significant improvement over static baseline in win rate and token efficiency."
    elif aggregated["summary"]["mcnemar_passed"]:
        aggregated["summary"]["overall_conclusion"] = "Dynamic policy shows significant win rate improvement, but token efficiency improvement is not statistically significant."
    elif aggregated["summary"]["ttest_passed"]:
        aggregated["summary"]["overall_conclusion"] = "Dynamic policy shows significant token efficiency improvement, but win rate improvement is not statistically significant."
    else:
        aggregated["summary"]["overall_conclusion"] = "No statistically significant difference detected between dynamic and static policies in current sample."

    # Write output
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=2)
        logger.info(f"Aggregated statistics written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write aggregated stats to {output_path}: {e}")
        raise

    return aggregated

def main():
    """Main entry point for the aggregate statistics script."""
    logger.info("Starting statistical aggregation process...")
    try:
        result = aggregate_statistics()
        logger.info("Aggregation completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing required data: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())