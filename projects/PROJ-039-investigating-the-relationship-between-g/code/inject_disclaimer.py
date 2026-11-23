"""
T025: Inject associational disclaimer into all result JSONs and reports.

Mandated String: "Note: This analysis is associational only; no causal inference is made."

Target Artifacts:
1. artifacts/correlation_results.json
2. artifacts/analysis_results.json
3. artifacts/strata_report.json

This script loads each JSON file, injects the disclaimer string into a 
'disclaimer' key at the root level, and writes the file back.
"""
import json
import sys
import logging
from pathlib import Path
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DISCLAIMER_STRING = "Note: This analysis is associational only; no causal inference is made."

def inject_disclaimer(file_path: Path) -> bool:
    """
    Inject the disclaimer into a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        True if successful, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Inject the disclaimer at the root level
        data['disclaimer'] = DISCLAIMER_STRING
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Successfully injected disclaimer into: {file_path}")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path}: {e}")
        return False

def main():
    """Main entry point for T025."""
    # Define target artifacts relative to project root
    # Assuming script runs from project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    artifacts_dir = project_root / "artifacts"
    
    target_files = [
        artifacts_dir / "correlation_results.json",
        artifacts_dir / "analysis_results.json",
        artifacts_dir / "strata_report.json"
    ]
    
    success_count = 0
    failure_count = 0
    
    logger.info(f"Starting disclaimer injection for {len(target_files)} artifacts.")
    
    for file_path in target_files:
        if inject_disclaimer(file_path):
            success_count += 1
        else:
            failure_count += 1
    
    logger.info(f"Disclaimers injected: {success_count} succeeded, {failure_count} failed.")
    
    if failure_count > 0:
        logger.error("Some files failed to update. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All disclaimers injected successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()