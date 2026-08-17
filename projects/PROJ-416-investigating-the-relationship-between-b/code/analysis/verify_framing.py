"""
T047: Validate the reports/results.md output against the "Associational Framing" rule (FR-008).

This script verifies that the generated report explicitly states "Findings are framed as ASSOCIATIONAL"
if the metadata does not indicate a randomized study design.

Logic:
1. Load metadata from `data/metrics/metadata.json` (or similar source used by report generation).
2. Check `metadata.study_design` and `metadata.randomized`.
3. Determine if the report SHOULD be associational based on FR-008:
   - If `study_design` != 'randomized' AND `randomized` != true (or missing), then framing MUST be ASSOCIATIONAL.
4. Load `reports/results.md`.
5. Verify the report contains the required string: "Findings are framed as ASSOCIATIONAL".
6. Exit with code 0 if valid, code 1 if the framing is missing or incorrect.
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_PATH = PROJECT_ROOT / "data" / "metrics" / "metadata.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "results.md"

def load_metadata() -> Optional[Dict[str, Any]]:
    """Load metadata from the standard location."""
    if not METADATA_PATH.exists():
        logger.error(f"Metadata file not found: {METADATA_PATH}")
        return None
    
    try:
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse metadata JSON: {e}")
        return None

def determine_required_framing(metadata: Dict[str, Any]) -> str:
    """
    Determine the required framing based on metadata per FR-008.
    
    Rules:
    - If study_design == 'randomized' AND randomized == True -> CAUSAL (or not restricted)
    - Otherwise -> ASSOCIATIONAL
    """
    study_design = metadata.get('study_design')
    randomized = metadata.get('randomized')

    # Explicit check logic from T034/T047 spec
    # If NEITHER exists (fields missing OR false values), default to ASSOCIATIONAL
    is_randomized = (study_design == 'randomized') and (randomized is True)

    if is_randomized:
        return "CAUSAL" # Or specific causal framing if defined, but T047 focuses on Assoc
    else:
        return "ASSOCIATIONAL"

def validate_report_framing(report_path: Path, required_framing: str) -> bool:
    """
    Validate that the report contains the correct framing statement.
    
    For T047, we specifically check for the string "Findings are framed as ASSOCIATIONAL"
    if the required framing is ASSOCIATIONAL.
    """
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        return False

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read report: {e}")
        return False

    if required_framing == "ASSOCIATIONAL":
        target_string = "Findings are framed as ASSOCIATIONAL"
        if target_string in content:
            logger.info(f"SUCCESS: Report correctly framed as ASSOCIATIONAL.")
            return True
        else:
            logger.error(f"FAILURE: Report missing required framing statement: '{target_string}'")
            logger.error(f"Report content preview:\n{content[:500]}...")
            return False
    else:
        # If the study is randomized, we might not have a specific "ASSOCIATIONAL" string requirement,
        # but we verify the absence of the warning if that was the logic.
        # For T047, the primary failure mode is missing the ASSOCIATIONAL tag when required.
        logger.info(f"Study design indicates randomized. No ASSOCIATIONAL tag required.")
        return True

def run_verification() -> int:
    """Main entry point for verification."""
    logger.info("Starting T047: Associational Framing Verification")
    
    # 1. Load Metadata
    metadata = load_metadata()
    if metadata is None:
        # If metadata is missing, we cannot determine the required framing.
        # This is a failure condition for the verification process.
        logger.error("Cannot verify framing: Metadata missing.")
        return 1

    # 2. Determine Required Framing
    required_framing = determine_required_framing(metadata)
    logger.info(f"Metadata indicates required framing: {required_framing}")

    # 3. Validate Report
    is_valid = validate_report_framing(REPORT_PATH, required_framing)

    if not is_valid:
        logger.error("T047 VERIFICATION FAILED.")
        return 1
    
    logger.info("T047 VERIFICATION PASSED.")
    return 0

def main():
    sys.exit(run_verification())

if __name__ == "__main__":
    main()
