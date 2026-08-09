import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file safely. Returns None if the file does not exist or is invalid.
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def aggregate_results() -> Dict[str, Any]:
    """
    Aggregate results from previous tasks into the final stats report.
    Collects:
      - p-values and BH-adjusted q-values from T029 (stats_report.json)
      - reconstruction errors from T022d (reconstruction_error.json)
      - linearity correlation from T030 (linearity_check.json)
    """
    base_path = Path("data/results")
    final_report: Dict[str, Any] = {
        "report_metadata": {
            "generated_by": "src/evaluation/report_generator.py",
            "task_id": "T032",
            "dependencies": ["T031", "T029", "T022d", "T030"]
        },
        "statistical_tests": {},
        "reconstruction_error": {},
        "linearity_check": {}
    }

    # 1. Load Statistical Tests (T029)
    stats_path = base_path / "stats_report.json"
    stats_data = load_json_safe(stats_path)
    if stats_data:
        # Extract p-values and q-values
        if "p_values" in stats_data:
            final_report["statistical_tests"]["p_values"] = stats_data["p_values"]
        if "bh_adjusted_q_values" in stats_data:
            final_report["statistical_tests"]["bh_adjusted_q_values"] = stats_data["bh_adjusted_q_values"]
        if "sensitivity_analysis" in stats_data:
            final_report["statistical_tests"]["sensitivity_analysis"] = stats_data["sensitivity_analysis"]
        logger.info(f"Loaded statistical tests from {stats_path}")
    else:
        logger.warning(f"Could not load {stats_path}. Statistical tests section will be empty.")

    # 2. Load Reconstruction Error (T022d)
    recon_path = base_path / "reconstruction_error.json"
    recon_data = load_json_safe(recon_path)
    if recon_data:
        final_report["reconstruction_error"] = recon_data
        logger.info(f"Loaded reconstruction error from {recon_path}")
    else:
        logger.warning(f"Could not load {recon_path}. Reconstruction error section will be empty.")

    # 3. Load Linearity Check (T030)
    linearity_path = base_path / "linearity_check.json"
    linearity_data = load_json_safe(linearity_path)
    if linearity_data:
        final_report["linearity_check"] = linearity_data
        logger.info(f"Loaded linearity check from {linearity_path}")
    else:
        logger.warning(f"Could not load {linearity_path}. Linearity check section will be empty.")

    return final_report

def main():
    """
    Main entry point to generate the final stats report.
    """
    logger.info("Starting final report generation (T032)...")
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "stats_report.json"

    report = aggregate_results()

    try:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Successfully generated final report at {output_file}")
        print(f"Report generated: {output_file}")
    except Exception as e:
        logger.error(f"Failed to write report: {e}")
        raise

if __name__ == "__main__":
    main()