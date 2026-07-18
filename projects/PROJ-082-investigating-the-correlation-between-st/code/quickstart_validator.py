"""
Quickstart Validation Script for PROJ-082.

This script executes the end-to-end pipeline as described in `quickstart.md`
to verify that all components (extraction, analysis, visualization, reporting)
function correctly with real data or the provided sample data.

It verifies:
1. Directory structure integrity.
2. Successful execution of `main.py` pipeline.
3. Existence of expected output artifacts (JSON, PNGs, MD).
4. Basic content validation of generated files.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path to allow relative imports if run as script
# Note: In a real environment, the package should be installed or PYTHONPATH set.
# We assume this script runs from the project root or code/ directory.
current_dir = Path(__file__).parent
project_root = current_dir.parent if current_dir.name == "code" else current_dir

# Add code directory to sys.path for imports
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from main import run_pipeline, main as main_entrypoint
from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

logger = get_logger(__name__)

def check_directories() -> bool:
    """Verify required directory structure exists."""
    required_dirs = [
        "code",
        "tests",
        "data",
        "data/derived",
        "docs",
        "contracts",
        "figures"
    ]
    missing = []
    for d in required_dirs:
        if not (project_root / d).exists():
            missing.append(d)
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    
    logger.info("Directory structure validation: PASSED")
    return True

def run_pipeline_execution() -> bool:
    """Execute the main pipeline and capture results."""
    logger.info("Starting pipeline execution...")
    
    # Define input/output paths
    # We assume a sample input exists or the pipeline handles missing input gracefully
    input_csv = project_root / "data" / "input" / "studies.csv"
    output_json = project_root / "data" / "derived" / "meta_analysis_result.json"
    
    # Ensure input directory exists even if file is missing (pipeline might create it)
    ensure_directory(project_root / "data" / "input")
    
    try:
        # Run the pipeline
        # The main.py script expects arguments or uses defaults
        # We simulate the command line call: python code/main.py --input ... --output ...
        args = argparse.Namespace(
            input=str(input_csv),
            output=str(output_json),
            figures_dir=str(project_root / "figures"),
            report_dir=str(project_root / "docs"),
            verbose=True
        )
        
        # Run the core logic
        result = run_pipeline(args)
        
        if result is None:
            logger.error("Pipeline returned None. Execution likely failed.")
            return False
        
        logger.info(f"Pipeline execution completed. Status: {result.get('status', 'unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return False

def verify_artifacts() -> bool:
    """Verify that expected output artifacts were created."""
    artifacts = {
        "data/derived/meta_analysis_result.json": "JSON",
        "figures/forest_plot.png": "PNG",
        "figures/funnel_plot.png": "PNG",
        "figures/correlation_summary.png": "PNG",
        "docs/paper_draft.md": "Markdown"
    }
    
    missing = []
    for rel_path, file_type in artifacts.items():
        full_path = project_root / rel_path
        if not full_path.exists():
            missing.append(rel_path)
        else:
            # Basic content check
            size = full_path.stat().st_size
            if size == 0:
                logger.warning(f"Artifact {rel_path} exists but is empty.")
            else:
                logger.info(f"Artifact {rel_path} verified ({size} bytes).")
    
    if missing:
        logger.error(f"Missing output artifacts: {missing}")
        return False
    
    logger.info("Artifact verification: PASSED")
    return True

def validate_json_content(json_path: Path) -> bool:
    """Validate the structure of the meta-analysis result JSON."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        required_keys = ["study_count", "synthesis_mode", "weighted_mean_r"]
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            logger.error(f"JSON missing required keys: {missing_keys}")
            return False
        
        logger.info("JSON content validation: PASSED")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading JSON: {e}")
        return False

def main():
    """Main entry point for the validator."""
    logger.info("=== Starting Quickstart Validation (T036) ===")
    
    # 1. Check Directory Structure
    if not check_directories():
        logger.error("Validation FAILED: Directory structure check failed.")
        return 1
    
    # 2. Run Pipeline
    if not run_pipeline_execution():
        logger.error("Validation FAILED: Pipeline execution failed.")
        return 1
    
    # 3. Verify Artifacts
    if not verify_artifacts():
        logger.error("Validation FAILED: Artifact verification failed.")
        return 1
    
    # 4. Validate JSON Content
    json_path = project_root / "data" / "derived" / "meta_analysis_result.json"
    if json_path.exists():
        if not validate_json_content(json_path):
            logger.error("Validation FAILED: JSON content validation failed.")
            return 1
    else:
        logger.warning("JSON file not found, skipping content validation.")
    
    logger.info("=== Quickstart Validation (T036) COMPLETED SUCCESSFULLY ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
