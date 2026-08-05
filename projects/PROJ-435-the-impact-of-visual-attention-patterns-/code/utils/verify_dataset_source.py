"""
Verify that the dataset source used in T005 matches the "Verified datasets" block in research.md.

This script parses `research.md` to extract the verified dataset URL/ID and compares it
with the source used in T005 (which is defined in `code/utils/data_loading.py` via
`fetch_eye_tracking_data` or `load_dundee_eye_tracking`/`load_boston_eye_tracking`).

Output: `state/dataset_verification.json` with `status: "verified"` or `status: "failed"`.
"""

import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def parse_research_md_for_verified_source(research_md_path: Path) -> Optional[str]:
    """
    Parse research.md to extract the verified dataset URL/ID from the "Verified datasets" block.

    Expected format in research.md:
    ### Verified datasets
    - Source: <url_or_id>

    Returns the URL/ID string or None if not found.
    """
    if not research_md_path.exists():
        logger.error(f"research.md not found at {research_md_path}")
        return None

    try:
        content = research_md_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read research.md: {e}")
        return None

    # Look for the "Verified datasets" section
    # Pattern to match the section and extract the source
    pattern = r'### Verified datasets\s*\n(?:.*\n)*?[-*]\s*Source:\s*(.+?)(?:\n|$)'
    match = re.search(pattern, content, re.MULTILINE)

    if match:
        source = match.group(1).strip()
        logger.info(f"Found verified source in research.md: {source}")
        return source
    else:
        logger.warning("Could not find 'Verified datasets' section or 'Source' entry in research.md")
        return None

def get_actual_dataset_source() -> Optional[str]:
    """
    Determine the actual dataset source used by T005.

    This function inspects the `code/utils/data_loading.py` module to determine
    which dataset is being fetched. It looks for hardcoded URLs or dataset identifiers
    in the `fetch_eye_tracking_data` or specific loader functions.

    Returns the source URL/ID or None if not determinable.
    """
    data_loading_path = get_project_root() / "code" / "utils" / "data_loading.py"

    if not data_loading_path.exists():
        logger.error(f"data_loading.py not found at {data_loading_path}")
        return None

    try:
        content = data_loading_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read data_loading.py: {e}")
        return None

    # Strategy 1: Look for explicit URL assignments
    url_patterns = [
        r'url\s*=\s*[\'"]([^\'"]+)[\'"]',
        r'dataset_url\s*=\s*[\'"]([^\'"]+)[\'"]',
        r'source_url\s*=\s*[\'"]([^\'"]+)[\'"]',
    ]

    for pattern in url_patterns:
        matches = re.findall(pattern, content)
        if matches:
            # Return the first URL found (assuming one primary source)
            source = matches[0]
            logger.info(f"Found dataset URL in data_loading.py: {source}")
            return source

    # Strategy 2: Look for Hugging Face dataset IDs
    hf_patterns = [
        r'load_dataset\s*\(\s*[\'"]([^\'"]+)[\'"]',
        r'dataset\s*=\s*[\'"]([^\'"]+)[\'"]',
    ]

    for pattern in hf_patterns:
        matches = re.findall(pattern, content)
        if matches:
            source = matches[0]
            logger.info(f"Found dataset ID in data_loading.py: {source}")
            return source

    # Strategy 3: Look for specific dataset names in function calls
    if "load_dundee_eye_tracking" in content:
        logger.info("Detected 'load_dundee_eye_tracking' usage - source is Dundee Eye Tracking dataset")
        return "Dundee Eye Tracking dataset"
    elif "load_boston_eye_tracking" in content:
        logger.info("Detected 'load_boston_eye_tracking' usage - source is Boston Eye Tracking dataset")
        return "Boston Eye Tracking dataset"

    logger.warning("Could not determine dataset source from data_loading.py")
    return None

def compare_sources(expected: str, actual: str) -> bool:
    """
    Compare the expected and actual dataset sources.

    Performs a flexible comparison that normalizes URLs and handles common variations.
    """
    if not expected or not actual:
        return False

    # Normalize both strings for comparison
    def normalize(s: str) -> str:
        s = s.lower().strip()
        # Remove trailing slashes
        s = s.rstrip('/')
        # Remove http/https protocol prefix for comparison
        s = re.sub(r'^https?://', '', s)
        # Remove www prefix
        s = re.sub(r'^www\.', '', s)
        return s

    return normalize(expected) == normalize(actual)

def write_verification_result(status: str, expected: Optional[str], actual: Optional[str], message: str) -> Path:
    """
    Write the verification result to state/dataset_verification.json.
    """
    state_dir = get_project_root() / "state"
    state_dir.mkdir(exist_ok=True)

    result_path = state_dir / "dataset_verification.json"

    result = {
        "status": status,
        "expected_source": expected,
        "actual_source": actual,
        "message": message,
        "verified_at": "2026-01-01T00:00:00Z"  # Placeholder; actual timestamp could be added
    }

    try:
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Verification result written to {result_path}")
    except Exception as e:
        logger.error(f"Failed to write verification result: {e}")
        raise

    return result_path

def main():
    """Main entry point for dataset source verification."""
    logger.info("Starting dataset source verification (T005b)...")

    # Paths
    project_root = get_project_root()
    research_md_path = project_root / "research.md"

    # Step 1: Parse research.md for verified source
    expected_source = parse_research_md_for_verified_source(research_md_path)
    if not expected_source:
        logger.error("Could not extract verified source from research.md")
        write_verification_result(
            status="failed",
            expected=None,
            actual=None,
            message="Failed to extract verified source from research.md"
        )
        return 1

    # Step 2: Determine actual source from data_loading.py
    actual_source = get_actual_dataset_source()
    if not actual_source:
        logger.error("Could not determine actual dataset source from data_loading.py")
        write_verification_result(
            status="failed",
            expected=expected_source,
            actual=None,
            message="Failed to determine actual dataset source from data_loading.py"
        )
        return 1

    # Step 3: Compare sources
    if compare_sources(expected_source, actual_source):
        logger.info("Dataset sources MATCH - verification PASSED")
        write_verification_result(
            status="verified",
            expected=expected_source,
            actual=actual_source,
            message="Dataset source in data_loading.py matches the verified source in research.md"
        )
        return 0
    else:
        logger.error(f"Dataset sources DO NOT MATCH - verification FAILED")
        logger.error(f"  Expected: {expected_source}")
        logger.error(f"  Actual:   {actual_source}")
        write_verification_result(
            status="failed",
            expected=expected_source,
            actual=actual_source,
            message=f"Dataset source mismatch: expected '{expected_source}', got '{actual_source}'"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())