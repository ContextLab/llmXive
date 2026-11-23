"""
Script to verify novelty and hypothesis in spec.md.
Parses for 'Novelty and Research Gap' and validates hypothesis structure.
"""
import os
import re
import sys
from pathlib import Path

def get_project_root():
    return Path(__file__).resolve().parents[1]

def check_novelty_section(spec_content):
    """Check for 'Novelty and Research Gap' subsection with multiple citations."""
    if "Novelty and Research Gap" not in spec_content:
        return False, "Missing 'Novelty and Research Gap' subsection"
    
    # Count citations (simple heuristic: look for (Author, Year))
    citations = re.findall(r'\([A-Za-z]+\s*,\s*\d{4}\)', spec_content)
    if len(citations) < 2:
        return False, f"Insufficient citations in Novelty section (found {len(citations)}, need >= 2)"
    return True, f"Novelty section found with {len(citations)} citations."

def check_hypothesis_structure(spec_content):
    """Validate hypothesis contains directional expectations and measurable thresholds."""
    if "Research Hypothesis" not in spec_content:
        return False, "Missing 'Research Hypothesis' section"
    
    # Extract hypothesis section (rough heuristic)
    match = re.search(r'Research Hypothesis(.*?)(?:\n\n|\Z)', spec_content, re.DOTALL)
    if not match:
        return False, "Could not extract Research Hypothesis section"
    
    hypothesis_text = match.group(1)
    
    # Check for directional expectations
    directional_terms = ["increase", "decrease", "positive", "negative", "higher", "lower"]
    has_direction = any(term in hypothesis_text.lower() for term in directional_terms)
    
    # Check for measurable thresholds (numbers, percentages)
    has_threshold = bool(re.search(r'\d+|%', hypothesis_text))
    
    if not has_direction:
        return False, "Hypothesis lacks directional expectation"
    if not has_threshold:
        return False, "Hypothesis lacks measurable threshold"
    
    return True, "Hypothesis is directional and measurable."

def main():
    project_root = get_project_root()
    spec_path = project_root / "specs" / "001-agriculture-optimization" / "spec.md"

    if not spec_path.exists():
        print(f"Error: {spec_path} not found.")
        sys.exit(1)

    spec_content = spec_path.read_text()
    errors = []

    # Check Novelty
    nov_ok, nov_msg = check_novelty_section(spec_content)
    if not nov_ok:
        errors.append(nov_msg)

    # Check Hypothesis
    hyp_ok, hyp_msg = check_hypothesis_structure(spec_content)
    if not hyp_ok:
        errors.append(hyp_msg)

    if errors:
        print("Novelty & Hypothesis Verification FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("Novelty & Hypothesis Verification PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
