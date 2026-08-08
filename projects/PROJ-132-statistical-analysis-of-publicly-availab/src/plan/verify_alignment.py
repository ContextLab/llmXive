"""
Task T050b: Verify Plan Alignment
Scans plan.md and spec.md for contradictions and documents findings.
"""
import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_PATH = PROJECT_ROOT / "plan.md"
SPEC_PATH = PROJECT_ROOT / "spec.md"
OUTPUT_PATH = PROJECT_ROOT / "data" / "provenance" / "plan_conflicts.json"


def load_file_text(path: Path) -> str:
    """Load text content from a file."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_terms(text: str) -> List[str]:
    """
    Extract potential identifiers (e.g., FR-XXX, US-XX, SC-XXX) from text.
    Returns a list of unique terms found.
    """
    # Pattern for common spec identifiers: FR, US, SC, etc.
    pattern = r"\b(FR|US|SC|GP|CR)-\d+[-]?\w*\b"
    matches = re.findall(pattern, text, re.IGNORECASE)
    # Reconstruct full terms
    terms = []
    for match in re.finditer(pattern, text, re.IGNORECASE):
        terms.append(match.group(0))
    return list(set(terms))


def check_mandatory_a_priori_gp(plan_text: str, spec_text: str) -> List[Dict[str, str]]:
    """
    Check if plan.md contains "mandatory a priori GP" (matches spec US-2).
    Returns a list of contradictions if the requirement is missing or mismatched.
    """
    contradictions = []
    required_phrase = "mandatory a priori GP"
    # Normalize for search
    plan_lower = plan_text.lower()
    spec_lower = spec_text.lower()

    # Check if spec mentions US-2 or GP requirement
    spec_has_gp = "us-2" in spec_lower or "mandatory a priori gp" in spec_lower
    
    if spec_has_gp and required_phrase not in plan_lower:
        contradictions.append({
            "location": "plan.md",
            "spec_req": "US-2 (Mandatory a priori GP)",
            "plan_text": f"Missing phrase: '{required_phrase}'"
        })
    elif not spec_has_gp:
        logger.warning("Spec does not clearly define US-2 GP requirement; skipping check.")
    
    return contradictions


def check_critical_data_scope_note(plan_text: str) -> List[Dict[str, str]]:
    """
    Check if plan.md contains "Critical Data Scope Note" regarding the sample dataset.
    """
    contradictions = []
    required_phrase = "Critical Data Scope Note"
    if required_phrase not in plan_text:
        contradictions.append({
            "location": "plan.md",
            "spec_req": "Data Scope Documentation",
            "plan_text": f"Missing phrase: '{required_phrase}'"
        })
    return contradictions


def check_unknown_terms(plan_text: str, spec_text: str) -> List[Dict[str, str]]:
    """
    Check for terms in plan.md that do not exist in spec.md.
    """
    contradictions = []
    plan_terms = set(extract_terms(plan_text))
    spec_terms = set(extract_terms(spec_text))
    
    unknown = plan_terms - spec_terms
    # Filter out common noise if necessary, but for now strict check
    if unknown:
        for term in unknown:
            # Skip if it's a very generic number or common word fragment
            if len(term) < 4:
                continue
            contradictions.append({
                "location": "plan.md",
                "spec_req": "Missing in spec.md",
                "plan_text": f"Unknown term found: {term}"
            })
    return contradictions


def verify_alignment() -> Dict[str, Any]:
    """
    Main logic to verify alignment between plan.md and spec.md.
    """
    try:
        plan_text = load_file_text(PLAN_PATH)
        spec_text = load_file_text(SPEC_PATH)
    except FileNotFoundError as e:
        logger.error(str(e))
        return {"error": str(e), "contradictions": []}

    all_contradictions = []
    all_contradictions.extend(check_mandatory_a_priori_gp(plan_text, spec_text))
    all_contradictions.extend(check_critical_data_scope_note(plan_text))
    all_contradictions.extend(check_unknown_terms(plan_text, spec_text))

    output = {
        "contradictions": all_contradictions,
        "plan_path": str(PLAN_PATH),
        "spec_path": str(SPEC_PATH),
        "verified_at": "2023-10-27T12:00:00Z" # Placeholder for actual timestamp logic if needed
    }

    if not all_contradictions:
        logger.info("No contradictions found.")
    else:
        logger.warning(f"Found {len(all_contradictions)} potential contradictions.")

    return output


def main():
    """Entry point for the script."""
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    result = verify_alignment()
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Findings written to {OUTPUT_PATH}")
    return result


if __name__ == "__main__":
    main()
