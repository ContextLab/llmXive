import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure we can import from the project root if run as a script
# In a real execution environment, the PYTHONPATH should be set correctly.
# If this script is placed in code/src/plan/, we need to adjust imports if necessary.
# However, per the API surface, this module is expected to exist at this path.

def load_file_text(file_path: Path) -> str:
    """Load and return the text content of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_terms(text: str) -> List[str]:
    """Extract potential requirement codes or specific terms from text."""
    # Pattern for requirement codes like FR-001, US-1, SC-002, etc.
    # Also looking for specific terms mentioned in the task
    terms = re.findall(r'\b(?:FR-\d+[A-Z]?|US-\d+|SC-\d+|GP|NOAA|PRISM|Daymet|mandatory a priori|Critical Data Scope Note)\b', text, re.IGNORECASE)
    return list(set(terms))

def check_mandatory_a_priori_gp(plan_text: str, spec_text: str) -> List[Dict[str, Any]]:
    """Check if plan contains 'mandatory a priori GP' matching spec US-2."""
    contradictions = []
    
    # Check spec for US-2 requirement
    spec_has_us2 = bool(re.search(r'US-2|user.*story.*2', spec_text, re.IGNORECASE))
    
    # Check plan for the specific phrase
    plan_has_gp = bool(re.search(r'mandatory a priori GP', plan_text, re.IGNORECASE))
    
    if spec_has_us2 and not plan_has_gp:
        contradictions.append({
            "location": "plan.md vs spec.md (US-2)",
            "spec_req": "US-2 requires mandatory a priori GP",
            "plan_text": "Missing 'mandatory a priori GP' in plan.md",
            "type": "OTHER"
        })
    elif not spec_has_us2:
        # If spec doesn't have US-2, we can't verify this specific requirement
        pass
        
    return contradictions

def check_critical_data_scope_note(plan_text: str) -> List[Dict[str, Any]]:
    """Check if plan contains 'Critical Data Scope Note' regarding sample dataset."""
    contradictions = []
    
    if "Critical Data Scope Note" not in plan_text:
        contradictions.append({
            "location": "plan.md",
            "spec_req": "Critical Data Scope Note regarding sample dataset",
            "plan_text": "Missing 'Critical Data Scope Note' in plan.md",
            "type": "SCOPE_NOTE"
        })
    
    return contradictions

def check_data_source_mismatch(plan_text: str, spec_text: str) -> List[Dict[str, Any]]:
    """Check for data source mismatches (NOAA/PRISM in spec vs Daymet in plan)."""
    contradictions = []
    
    spec_has_noaa = 'NOAA' in spec_text or 'PRISM' in spec_text
    plan_has_daymet = 'Daymet' in plan_text
    plan_has_noaa = 'NOAA' in plan_text or 'PRISM' in plan_text
    
    # If spec mentions NOAA/PRISM and plan mentions Daymet (without NOAA/PRISM), flag it
    if spec_has_noaa and plan_has_daymet and not plan_has_noaa:
        contradictions.append({
            "location": "spec.md vs plan.md",
            "spec_req": "NOAA/PRISM data source",
            "plan_text": "Daymet used instead of NOAA/PRISM",
            "type": "DATA_SOURCE_MISMATCH"
        })
    
    return contradictions

def check_unknown_terms(plan_text: str, spec_text: str) -> List[Dict[str, Any]]:
    """Check for terms in plan that do not exist in spec."""
    contradictions = []
    plan_terms = set(extract_terms(plan_text))
    spec_terms = set(extract_terms(spec_text))
    
    # Find terms in plan that are not in spec (excluding common words)
    unknown = plan_terms - spec_terms
    
    # Filter out very common terms that might be false positives
    common_terms = {'GP', 'mandatory', 'a', 'priori', 'Data', 'Scope', 'Note'}
    unknown = unknown - common_terms
    
    for term in unknown:
        # Check if this term is a specific requirement code
        if re.match(r'(FR-\d+[A-Z]?|US-\d+|SC-\d+)', term):
            contradictions.append({
                "location": "plan.md",
                "spec_req": f"Requirement {term}",
                "plan_text": f"Term '{term}' found in plan.md but not in spec.md",
                "type": "OTHER"
            })
    
    return contradictions

def verify_alignment(plan_path: Path, spec_path: Path) -> Dict[str, Any]:
    """Main function to verify alignment between plan.md and spec.md."""
    logger = logging.getLogger(__name__)
    logger.info(f"Verifying alignment between {plan_path} and {spec_path}")
    
    try:
        plan_text = load_file_text(plan_path)
        spec_text = load_file_text(spec_path)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {"error": str(e), "contradictions": []}
    
    contradictions = []
    
    # Run all checks
    contradictions.extend(check_mandatory_a_priori_gp(plan_text, spec_text))
    contradictions.extend(check_critical_data_scope_note(plan_text))
    contradictions.extend(check_data_source_mismatch(plan_text, spec_text))
    contradictions.extend(check_unknown_terms(plan_text, spec_text))
    
    result = {
        "contradictions": contradictions
    }
    
    if not contradictions:
        logger.info("No contradictions found")
    else:
        logger.warning(f"Found {len(contradictions)} contradictions")
    
    return result

def main():
    """Entry point for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Determine paths relative to project root
    # Assuming this script is run from the project root or code/ directory
    project_root = Path(__file__).parent.parent.parent.parent
    plan_path = project_root / "plan.md"
    spec_path = project_root / "spec.md"
    output_path = project_root / "data" / "provenance" / "plan_conflicts.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run verification
    result = verify_alignment(plan_path, spec_path)
    
    # Write results to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results written to {output_path}")
    
    # Print summary
    if result.get("contradictions"):
        print(f"Found {len(result['contradictions'])} contradictions:")
        for c in result["contradictions"]:
            print(f"  - {c['type']}: {c['location']} - {c['plan_text']}")
    else:
        print("No contradictions found.")
    
    return result

if __name__ == "__main__":
    main()
