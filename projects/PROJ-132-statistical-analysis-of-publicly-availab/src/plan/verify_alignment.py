"""
Plan and Spec Verification Script.

This script loads the project's spec.md and plan.md, verifies their existence,
scans for contradictory statements (specifically data source mismatches),
and checks against a whitelist of deviations stored in a JSON file.

It fails loudly with RuntimeError if contradictions exist that are NOT whitelisted.
It outputs a JSON report of the alignment status.
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_PATH = PROJECT_ROOT / "specs" / "001-bird-migration-climate-correlation" / "spec.md"
PLAN_PATH = PROJECT_ROOT / "plan.md"
DEVIATION_SCHEMA_PATH = PROJECT_ROOT / "data" / "provenance" / "spec_plan_deviation_schema.json"
DEVIATION_LIST_PATH = PROJECT_ROOT / "data" / "provenance" / "spec_plan_deviation.json"
OUTPUT_REPORT_PATH = PROJECT_ROOT / "reports" / "plan_spec_alignment.json"


def load_file_text(file_path: Path) -> str:
    """Load and return the text content of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    if file_path.stat().st_size == 0:
        raise ValueError(f"File is empty: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_terms(text: str) -> Dict[str, List[str]]:
    """
    Extract key terms related to data sources and methodologies from the text.
    Returns a dict of categories to lists of found terms.
    """
    terms = {
        "data_sources": [],
        "methodologies": [],
        "locations": []
    }

    # Simple regex patterns for extraction (can be expanded)
    # Look for common data source names
    source_patterns = [
        r'(?:eBird|NOAA|PRISM|Daymet|MODIS|Copernicus)',
        r'(?:vvud/eb-data|daymet/annual)'
    ]
    for pattern in source_patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        terms["data_sources"].extend(found)

    # Look for methodology keywords
    method_patterns = [
        r'(?:GAMM|Generalized Additive Mixed Model)',
        r'(?:Fréchet mean|geodesic)',
        r'(?:permutation test)'
    ]
    for pattern in method_patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        terms["methodologies"].extend(found)

    return terms


def check_data_source_mismatch(
    spec_terms: Dict[str, List[str]],
    plan_terms: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """
    Check for contradictions in data sources between spec and plan.
    Returns a list of detected mismatches.
    """
    mismatches = []
    spec_sources = set(s.lower() for s in spec_terms.get("data_sources", []))
    plan_sources = set(s.lower() for s in plan_terms.get("data_sources", []))

    # Define known conflicting pairs or sets
    # Example: If Spec says NOAA and Plan says Daymet, that's a mismatch unless whitelisted.
    # We look for sources present in one but not the other, specifically focusing on major climate/bird data.
    major_sources = {"noaa", "prism", "daymet", "ebird", "vvud/eb-data"}

    spec_major = spec_sources.intersection(major_sources)
    plan_major = plan_sources.intersection(major_sources)

    # Check for direct conflicts (e.g., NOAA in Spec vs Daymet in Plan)
    if "noaa" in spec_major or "prism" in spec_major:
        if "daymet" in plan_major and "noaa" not in plan_major:
            mismatches.append({
                "type": "data_source_mismatch",
                "spec_source": "NOAA/PRISM",
                "plan_source": "Daymet",
                "description": "Spec requires NOAA/PRISM but Plan uses Daymet."
            })

    if "ebird" in spec_major or "vvud/eb-data" in spec_major:
        # Assuming eBird is consistent, but check if Plan mentions a different bird source
        pass # Add logic if other bird sources are possible

    return mismatches


def load_deviation_whitelist() -> List[Dict[str, Any]]:
    """Load the whitelist of deviations from the JSON file."""
    if not DEVIATION_LIST_PATH.exists():
        logger.warning(f"Deviation whitelist not found at {DEVIATION_LIST_PATH}. Proceeding without whitelist.")
        return []

    try:
        with open(DEVIATION_LIST_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle if it's a list or a single object
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                logger.error("Deviation whitelist format invalid. Expected list or dict.")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse deviation whitelist JSON: {e}")
        return []


def is_whitelisted(mismatch: Dict[str, Any], whitelist: List[Dict[str, Any]]) -> bool:
    """Check if a specific mismatch is covered by the whitelist."""
    for entry in whitelist:
        # Check if the description or type matches
        # We look for the specific "implemented_source" vs "spec_requirement" match
        if (entry.get("spec_requirement", "").lower() in mismatch.get("description", "").lower() or
            entry.get("implemented_source", "").lower() in mismatch.get("description", "").lower()):
            return True
        # Fuzzy check on type
        if entry.get("spec_requirement", "").lower() == mismatch.get("spec_source", "").lower():
            return True
    return False


def verify_alignment() -> Dict[str, Any]:
    """
    Main verification logic.
    Returns a report dictionary.
    """
    report = {
        "status": "success",
        "spec_path": str(SPEC_PATH),
        "plan_path": str(PLAN_PATH),
        "deviation_whitelist_path": str(DEVIATION_LIST_PATH),
        "output_report_path": str(OUTPUT_REPORT_PATH),
        "errors": [],
        "warnings": [],
        "mismatches_found": [],
        "mismatches_whitelisted": [],
        "timestamp": None
    }

    try:
        # 1. Verify file existence and non-empty
        logger.info(f"Loading Spec from {SPEC_PATH}")
        spec_text = load_file_text(SPEC_PATH)
        logger.info(f"Loading Plan from {PLAN_PATH}")
        plan_text = load_file_text(PLAN_PATH)

        # 2. Extract terms
        spec_terms = extract_terms(spec_text)
        plan_terms = extract_terms(plan_text)
        logger.info(f"Spec terms: {spec_terms}")
        logger.info(f"Plan terms: {plan_terms}")

        # 3. Check for mismatches
        mismatches = check_data_source_mismatch(spec_terms, plan_terms)
        report["mismatches_found"] = mismatches

        if not mismatches:
            logger.info("No data source mismatches detected.")
            return report

        # 4. Load whitelist
        whitelist = load_deviation_whitelist()
        logger.info(f"Loaded {len(whitelist)} whitelisted deviations.")

        # 5. Filter mismatches
        whitelisted_count = 0
        fatal_mismatches = []

        for mismatch in mismatches:
            if is_whitelisted(mismatch, whitelist):
                report["mismatches_whitelisted"].append(mismatch)
                whitelisted_count += 1
                logger.info(f"Mismatch whitelisted: {mismatch}")
            else:
                fatal_mismatches.append(mismatch)
                logger.warning(f"Fatal mismatch detected (not whitelisted): {mismatch}")

        if fatal_mismatches:
            report["status"] = "failed"
            error_msg = f"Found {len(fatal_mismatches)} non-whitelisted contradictions between Spec and Plan."
            report["errors"].append(error_msg)
            raise RuntimeError(error_msg)
        else:
            logger.info(f"All {len(mismatches)} mismatches were whitelisted.")

    except FileNotFoundError as e:
        report["status"] = "failed"
        report["errors"].append(str(e))
        raise
    except ValueError as e:
        report["status"] = "failed"
        report["errors"].append(str(e))
        raise
    except RuntimeError as e:
        report["status"] = "failed"
        report["errors"].append(str(e))
        raise

    return report


def main():
    """Entry point for the script."""
    try:
        report = verify_alignment()
        
        # Ensure output directory exists
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Verification complete. Report saved to {OUTPUT_REPORT_PATH}")
        
        if report["status"] == "failed":
            logger.error("Verification FAILED. See errors in report.")
            sys.exit(1)
        else:
            logger.info("Verification PASSED.")
            sys.exit(0)

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"Verification failed with exception: {e}")
        # Still try to write a failure report if possible
        try:
            OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            error_report = {
                "status": "failed",
                "error": str(e),
                "timestamp": None
            }
            with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
                json.dump(error_report, f, indent=2)
        except Exception:
            pass
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()