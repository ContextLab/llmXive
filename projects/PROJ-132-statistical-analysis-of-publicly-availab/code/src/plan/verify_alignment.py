"""
T050a: Verify Plan Alignment
Scans plan.md and spec.md for contradictions and writes findings to data/provenance/plan_conflicts.json.
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

def load_file_text(file_path: Path) -> str:
    """Load file content as text."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return ""
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return ""

def extract_terms(text: str) -> List[str]:
    """Extract potential terms/IDs (e.g., FR-002, US-1, SC-005) from text."""
    # Pattern for common requirement IDs: FR-XXX, US-X, SC-XXX, etc.
    pattern = r'\b(FR|US|SC|T\d+)\-\d+[A-Z]?\b'
    return list(set(re.findall(pattern, text, re.IGNORECASE)))

def check_mandatory_a_priori_gp(plan_text: str, spec_text: str) -> List[Dict[str, str]]:
    """Check if plan.md contains 'mandatory a priori GP' matching spec US-2."""
    contradictions = []
    
    # Check spec for US-2 requirement
    spec_has_us2 = "US-2" in spec_text or "US2" in spec_text
    plan_has_gp = "mandatory a priori GP" in plan_text or "mandatory a priori" in plan_text.lower()
    
    if spec_has_us2 and not plan_has_gp:
        contradictions.append({
            "location": "plan.md vs spec.md (US-2)",
            "spec_req": "US-2 requires mandatory a priori GP",
            "plan_text": "Plan does not mention 'mandatory a priori GP' despite US-2 requirement"
        })
    elif not spec_has_us2:
        logger.info("US-2 requirement not found in spec.md, skipping GP check.")
        
    return contradictions

def check_critical_data_scope_note(plan_text: str, spec_text: str) -> List[Dict[str, str]]:
    """Check if plan.md contains 'Critical Data Scope Note' regarding sample dataset."""
    contradictions = []
    
    plan_has_scope_note = "Critical Data Scope Note" in plan_text
    spec_has_scope = "sample" in spec_text.lower() or "scope" in spec_text.lower()
    
    if spec_has_scope and not plan_has_scope_note:
        contradictions.append({
            "location": "plan.md vs spec.md (Data Scope)",
            "spec_req": "Spec mentions sample dataset scope",
            "plan_text": "Plan does not contain 'Critical Data Scope Note'"
        })
        
    return contradictions

def check_unknown_terms(plan_text: str, spec_text: str) -> List[Dict[str, str]]:
    """Check for terms in plan.md that do not exist in spec.md."""
    contradictions = []
    
    plan_terms = set(extract_terms(plan_text))
    spec_terms = set(extract_terms(spec_text))
    
    unknown_terms = plan_terms - spec_terms
    
    # Filter out common generic terms
    generic_terms = {"T050", "T050a", "T002", "T003", "T004", "T005", "T006", "T007", "T009", "T010"}
    unknown_terms = unknown_terms - generic_terms
    
    if unknown_terms:
        for term in list(unknown_terms)[:5]:  # Limit to first 5 for brevity
            contradictions.append({
                "location": f"plan.md (term: {term})",
                "spec_req": f"Term '{term}' not found in spec.md",
                "plan_text": f"Found term '{term}' in plan.md but not in spec.md"
            })
            
    return contradictions

def verify_alignment(plan_path: Path, spec_path: Path, output_path: Path) -> None:
    """Main logic to verify plan/spec alignment."""
    logger.info(f"Starting alignment verification between {plan_path} and {spec_path}")
    
    plan_text = load_file_text(plan_path)
    spec_text = load_file_text(spec_path)
    
    if not plan_text or not spec_text:
        logger.error("Could not load plan.md or spec.md. Aborting.")
        return
    
    all_contradictions = []
    
    # Check 1: Mandatory a priori GP
    gp_contradictions = check_mandatory_a_priori_gp(plan_text, spec_text)
    all_contradictions.extend(gp_contradictions)
    
    # Check 2: Critical Data Scope Note
    scope_contradictions = check_critical_data_scope_note(plan_text, spec_text)
    all_contradictions.extend(scope_contradictions)
    
    # Check 3: Unknown terms
    term_contradictions = check_unknown_terms(plan_text, spec_text)
    all_contradictions.extend(term_contradictions)
    
    # Prepare output
    result = {
        "contradictions": all_contradictions,
        "summary": {
            "total_contradictions": len(all_contradictions),
            "plan_file": str(plan_path),
            "spec_file": str(spec_path)
        }
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    if all_contradictions:
        logger.warning(f"Found {len(all_contradictions)} potential contradictions. See {output_path}")
    else:
        logger.info("No contradictions found.")
    
    logger.info(f"Alignment verification complete. Results written to {output_path}")

def main():
    """Entry point for the script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    plan_path = project_root / "plan.md"
    spec_path = project_root / "specs" / "001-bird-migration-climate-correlation" / "spec.md"
    output_path = project_root / "data" / "provenance" / "plan_conflicts.json"
    
    # If spec.md is not in the expected location, try common alternatives
    if not spec_path.exists():
        alt_spec_path = project_root / "spec.md"
        if alt_spec_path.exists():
            spec_path = alt_spec_path
        else:
            logger.error(f"Could not find spec.md at {spec_path} or {alt_spec_path}")
            sys.exit(1)
    
    verify_alignment(plan_path, spec_path, output_path)

if __name__ == "__main__":
    main()
