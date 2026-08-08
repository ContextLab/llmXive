"""
Task T050b: Verify Plan Alignment
Scans plan.md and spec.md for contradictions and writes findings to data/provenance/plan_conflicts.json.
"""
import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_file_text(file_path: Path) -> str:
    """Load text content from a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_terms(text: str) -> List[str]:
    """Extract potential terms (uppercase acronyms, FR-, US-, SC- references) from text."""
    # Pattern to match terms like US-1, FR-002, SC-001, or all-caps acronyms (3+ letters)
    # This is a heuristic to find "terms" that might be referenced
    terms = re.findall(r'\b(?:US-\d+|FR-\d+|[A-Z]{3,})\b', text)
    return list(set(terms))

def check_mandatory_a_priori_gp(plan_text: str, spec_text: str) -> List[Dict[str, str]]:
    """
    Check if plan.md contains "mandatory a priori GP" (matches spec US-2).
    Returns a list of contradictions if the term exists in plan but not in spec.
    """
    contradictions = []
    plan_has_gp = "mandatory a priori GP" in plan_text or "mandatory a priori" in plan_text and "GP" in plan_text
    spec_has_gp = "mandatory a priori GP" in spec_text or "US-2" in spec_text and "GP" in spec_text

    # If plan mentions it but spec doesn't, it's a potential contradiction (plan adds requirement not in spec)
    if plan_has_gp and not spec_has_gp:
        contradictions.append({
            "location": "plan.md - GP Requirement",
            "spec_req": "US-2 (implied)",
            "plan_text": "Plan mentions 'mandatory a priori GP' but spec US-2 does not explicitly confirm it."
        })
    return contradictions

def check_critical_data_scope_note(plan_text: str) -> List[Dict[str, str]]:
    """
    Check if plan.md contains "Critical Data Scope Note" regarding the sample dataset.
    """
    contradictions = []
    # The task description asks to check if it contains this note.
    # If it's missing, it might be a gap, but the task specifically asks to check for the *presence*
    # and then check for terms *in plan* that don't exist in *spec*.
    # We will log if it's missing as a potential gap, but not a direct contradiction unless spec requires it.
    if "Critical Data Scope Note" not in plan_text:
        logger.warning("Plan.md does not contain 'Critical Data Scope Note'.")
        # This is a warning, not necessarily a contradiction unless spec mandates it.
        # We will not add it to contradictions unless we find a spec requirement for it.
    return contradictions

def check_unknown_terms(plan_text: str, spec_text: str) -> List[Dict[str, str]]:
    """
    Check for any terms in plan.md that do not exist in spec.md.
    """
    contradictions = []
    plan_terms = set(extract_terms(plan_text))
    spec_terms = set(extract_terms(spec_text))

    # Find terms in plan that are not in spec
    unknown_terms = plan_terms - spec_terms

    # Filter out common terms that are expected to be in both or are generic
    common_terms = {"THE", "AND", "DATA", "MODEL", "SPEC", "PLAN", "US", "FR", "SC", "T050B", "T050A"}
    unknown_terms = [t for t in unknown_terms if t not in common_terms]

    if unknown_terms:
        for term in unknown_terms:
            # Find context in plan
            context_match = re.search(rf'.{{0,50}}{re.escape(term)}.{{0,50}}', plan_text)
            context = context_match.group(0) if context_match else term

            contradictions.append({
                "location": f"plan.md - Term '{term}'",
                "spec_req": "N/A",
                "plan_text": f"Found term '{term}' in plan: ...{context}..."
            })

    return contradictions

def verify_alignment(plan_path: Path, spec_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Main function to verify alignment between plan and spec.
    """
    logger.info(f"Verifying alignment between {plan_path} and {spec_path}")

    try:
        plan_text = load_file_text(plan_path)
        spec_text = load_file_text(spec_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return {"error": str(e), "contradictions": []}

    contradictions = []

    # 1. Check mandatory a priori GP
    gp_contradictions = check_mandatory_a_priori_gp(plan_text, spec_text)
    contradictions.extend(gp_contradictions)

    # 2. Check Critical Data Scope Note (Warning if missing, not a contradiction unless spec requires)
    check_critical_data_scope_note(plan_text)

    # 3. Check for unknown terms
    term_contradictions = check_unknown_terms(plan_text, spec_text)
    contradictions.extend(term_contradictions)

    result = {
        "plan_path": str(plan_path),
        "spec_path": str(spec_path),
        "contradictions": contradictions,
        "contradiction_count": len(contradictions)
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    if not contradictions:
        logger.info("No contradictions found.")
    else:
        logger.warning(f"Found {len(contradictions)} potential contradictions.")

    return result

def main():
    """Entry point for the script."""
    # Define paths relative to project root
    # Assuming this script is run from code/ or code/src/plan/
    # We need to resolve paths relative to the project root (parent of 'code')
    current_dir = Path(__file__).resolve()
    project_root = current_dir.parent.parent.parent # code/src/plan -> project root

    plan_path = project_root / "plan.md"
    spec_path = project_root / "spec.md"
    output_path = project_root / "data" / "provenance" / "plan_conflicts.json"

    if not plan_path.exists():
        logger.error(f"plan.md not found at {plan_path}")
        sys.exit(1)
    if not spec_path.exists():
        logger.error(f"spec.md not found at {spec_path}")
        sys.exit(1)

    result = verify_alignment(plan_path, spec_path, output_path)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
