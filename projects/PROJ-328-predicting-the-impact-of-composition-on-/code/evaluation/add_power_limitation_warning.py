"""
T057: Add Power Limitation Warning to Final Report.

This script reads the ingestion status to determine the sample size (N).
If N < 100, it updates both the paper draft and the report YAML with a
specific "Statistical Power Limitation" warning referencing the exact N value.
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_data_processed_dir, get_data_outputs_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Paths
PROCESSED_DIR = get_data_processed_dir()
INGESTION_STATUS_PATH = PROCESSED_DIR / ".ingestion_status.json"
REPORT_YAML_PATH = PROCESSED_DIR / "report.yaml"
PAPER_DRAFT_PATH = project_root / "specs" / "001-predict-solder-hardness" / "paper_draft.md"

def load_ingestion_status() -> Optional[Dict[str, Any]]:
    """Load the ingestion status JSON file."""
    if not INGESTION_STATUS_PATH.exists():
        logger.warning(f"Ingestion status file not found at {INGESTION_STATUS_PATH}. "
                       "Cannot determine sample size for power limitation check.")
        return None

    try:
        with open(INGESTION_STATUS_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ingestion status JSON: {e}")
        return None

def load_report_yaml() -> Optional[Dict[str, Any]]:
    """Load the existing report YAML file."""
    if not REPORT_YAML_PATH.exists():
        logger.warning(f"Report YAML not found at {REPORT_YAML_PATH}. "
                       "Creating a new one.")
        return {"metadata": {}, "results": {}}

    try:
        with open(REPORT_YAML_PATH, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse report YAML: {e}")
        return None

def save_report_yaml(report_data: Dict[str, Any]) -> bool:
    """Save the updated report YAML file."""
    try:
        with open(REPORT_YAML_PATH, 'w') as f:
            yaml.dump(report_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved updated report to {REPORT_YAML_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to save report YAML: {e}")
        return False

def update_paper_draft(n_value: int, threshold: int = 100) -> bool:
    """
    Update the paper draft to include a Statistical Power Limitation warning
    if N < threshold.
    """
    if not PAPER_DRAFT_PATH.exists():
        logger.error(f"Paper draft not found at {PAPER_DRAFT_PATH}. "
                     "Cannot add power limitation warning.")
        return False

    try:
        with open(PAPER_DRAFT_PATH, 'r') as f:
            content = f.read()

        warning_text = f"""
### Statistical Power Limitation

**Warning**: The total number of unique solder alloy compositions in the final dataset is **N = {n_value}**, which is below the target threshold of {threshold}.
Consequently, the statistical power of the regression analysis and model comparison (e.g., XGBoost vs. Linear Regression) is reduced.
Results should be interpreted with caution, particularly regarding the detection of subtle compositional effects or small effect sizes.
The confidence intervals reported may be wider than those achievable with a larger dataset.
"""

        # Check if warning already exists to avoid duplication
        if "Statistical Power Limitation" in content:
            logger.info("Power limitation warning already exists in paper draft.")
            return True

        # Inject into the Limitations section if it exists, otherwise append
        if "### Limitations" in content:
            # Insert after the Limitations header
            parts = content.split("### Limitations")
            if len(parts) > 1:
                new_content = parts[0] + "### Limitations" + warning_text + parts[1]
            else:
                new_content = content + warning_text
        else:
            # Append to the end if no Limitations section exists
            new_content = content + "\n" + warning_text

        with open(PAPER_DRAFT_PATH, 'w') as f:
            f.write(new_content)

        logger.info(f"Updated paper draft with power limitation warning (N={n_value}).")
        return True

    except Exception as e:
        logger.error(f"Failed to update paper draft: {e}")
        return False

def main():
    """Main entry point for T057."""
    logger.info("Starting T057: Add Power Limitation Warning to Final Report")

    # 1. Load Ingestion Status
    status = load_ingestion_status()
    if not status:
        logger.error("Could not load ingestion status. Aborting T057.")
        sys.exit(1)

    exact_n = status.get('exact_N', 0)
    threshold_status = status.get('threshold_status', 'unknown')

    logger.info(f"Current dataset size: N = {exact_n}")

    # 2. Determine if warning is needed (N < 100)
    # The task specifies: "If ... indicates N < 100"
    if exact_n >= 100:
        logger.info(f"N ({exact_n}) is >= 100. No power limitation warning required.")
        # Still ensure the report is clean (optional, but good practice)
        report = load_report_yaml()
        if report:
            # Remove existing warning if N is now sufficient
            if 'limitations' in report and 'power_limitation_warning' in report['limitations']:
                del report['limitations']['power_limitation_warning']
                save_report_yaml(report)
        return

    # 3. Update Report YAML
    logger.info(f"N ({exact_n}) < 100. Adding power limitation warning to report.yaml.")
    report = load_report_yaml()
    if report:
        if 'limitations' not in report:
            report['limitations'] = {}
        
        warning_msg = (
            f"Statistical power is limited due to small sample size (N = {exact_n}). "
            f"Target N was 100. Results may lack power to detect small effect sizes."
        )
        report['limitations']['power_limitation_warning'] = warning_msg
        report['limitations']['sample_size'] = exact_n
        report['limitations']['threshold'] = 100

        if not save_report_yaml(report):
            logger.error("Failed to save report.yaml with warning.")
            sys.exit(1)
    else:
        logger.error("Could not load or create report.yaml.")
        sys.exit(1)

    # 4. Update Paper Draft
    logger.info(f"Updating paper draft with power limitation warning.")
    if not update_paper_draft(exact_n):
        logger.error("Failed to update paper draft.")
        sys.exit(1)

    logger.info("T057 completed successfully.")

if __name__ == "__main__":
    main()