"""
Artifact Verification Script for PROJ-530.

This script performs a final review to ensure all required artifacts 
(plots, tables, reports, data files) are generated in the correct directories
as specified in tasks.md and the project plan.

It checks for the existence and non-emptiness of:
- data/processed/ (EEG epoch files)
- results/models/ (Model summary files)
- results/figures/ (Scatter plots, sensitivity plots)
- results/diagnostics/ (Feasibility report, validation report, sensitivity summary)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (assumed to be the parent of 'code')
PROJECT_ROOT = Path(__file__).parent.parent

# Define expected artifact paths relative to PROJECT_ROOT
EXPECTED_ARTIFACTS: Dict[str, List[str]] = {
    "data/processed": [
        "epochs.csv",  # Standard processed epoch file name
        "preprocessing.yaml"  # Preprocessing parameters log
    ],
    "results/models": [
        "primary_model_summary.json",  # LMM/GAM results
        "sensitivity_model_summaries.json"  # Sensitivity sweep results
    ],
    "results/figures": [
        "mfn_vs_error_scatter.png",  # Primary analysis plot
        "sensitivity_analysis_plot.png",  # Sensitivity sweep plot
        "multi_electrode_comparison.png"  # FCz/Cz/Fz comparison
    ],
    "results/diagnostics": [
        "feasibility_report.json",  # Runtime/memory metrics
        "validation_report.md",  # VIF, Bonferroni, conclusion
        "sensitivity_summary.csv"  # Threshold sweep results
    ]
}

def check_file_exists(path: Path) -> Tuple[bool, str]:
    """Check if a file exists and is non-empty."""
    if not path.exists():
        return False, f"Missing: {path}"
    if path.stat().st_size == 0:
        return False, f"Empty: {path}"
    return True, f"OK: {path}"

def validate_json_content(path: Path) -> bool:
    """Validate that a JSON file contains valid JSON."""
    try:
        with open(path, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError:
        return False

def validate_csv_content(path: Path) -> bool:
    """Validate that a CSV file has at least a header row."""
    try:
        with open(path, 'r') as f:
            line = f.readline()
            return len(line.strip()) > 0
    except Exception:
        return False

def validate_md_content(path: Path) -> bool:
    """Validate that a Markdown file exists and has content."""
    try:
        with open(path, 'r') as f:
            content = f.read()
            return len(content.strip()) > 0
    except Exception:
        return False

def main() -> int:
    """
    Main verification routine.
    
    Returns:
        int: 0 if all artifacts are present and valid, 1 otherwise.
    """
    logger.info(f"Starting artifact verification for project: {PROJECT_ROOT}")
    
    all_valid = True
    missing_count = 0
    invalid_count = 0

    for directory, files in EXPECTED_ARTIFACTS.items():
        dir_path = PROJECT_ROOT / directory
        
        # Check directory existence
        if not dir_path.exists():
            logger.error(f"Directory missing: {dir_path}")
            all_valid = False
            missing_count += len(files)
            continue

        for filename in files:
            file_path = dir_path / filename
            exists, message = check_file_exists(file_path)
            
            if not exists:
                logger.error(message)
                all_valid = False
                missing_count += 1
            else:
                # Additional content validation based on extension
                suffix = file_path.suffix.lower()
                is_valid_content = True
                
                if suffix == '.json':
                    is_valid_content = validate_json_content(file_path)
                elif suffix == '.csv':
                    is_valid_content = validate_csv_content(file_path)
                elif suffix == '.md':
                    is_valid_content = validate_md_content(file_path)
                
                if not is_valid_content:
                    logger.error(f"Invalid content in: {file_path}")
                    all_valid = False
                    invalid_count += 1
                else:
                    logger.info(message)

    # Summary
    logger.info("-" * 50)
    logger.info("Verification Summary:")
    logger.info(f"  Missing/Empty files: {missing_count}")
    logger.info(f"  Invalid content files: {invalid_count}")
    logger.info(f"  Total directories checked: {len(EXPECTED_ARTIFACTS)}")
    
    if all_valid:
        logger.info("SUCCESS: All required artifacts are present and valid.")
        return 0
    else:
        logger.error("FAILURE: Some artifacts are missing, empty, or invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())