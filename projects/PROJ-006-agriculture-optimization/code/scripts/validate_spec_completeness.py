"""
Script to validate spec completeness.
Checks for _TODO: markers, Research Hypothesis, and quantifiable success criteria.
"""
import os
import re
import sys
from pathlib import Path

def get_project_root():
    return Path(__file__).resolve().parents[1]

def check_todos(file_path):
    """Check for _TODO: markers in a file."""
    content = file_path.read_text()
    pattern = r'_TODO:'
    matches = re.findall(pattern, content)
    return len(matches) > 0, matches

def check_research_hypothesis(spec_content):
    """Check for a 'Research Hypothesis' section with falsifiable statements."""
    # Simple heuristic: look for "Hypothesis" and a directional claim
    if "Research Hypothesis" not in spec_content:
        return False, "Missing 'Research Hypothesis' section"
    
    # Check for falsifiable elements (directional, measurable)
    # This is a basic check; a more robust one would use NLP.
    if re.search(r'correlation|increase|decrease|effect|impact', spec_content, re.IGNORECASE):
        return True, "Hypothesis section found with directional language."
    return False, "Hypothesis section found but lacks directional/measurable language."

def check_success_criteria(spec_content):
    """Check for quantifiable success criteria (e.g., '>= 95%')."""
    # Look for percentage signs or numeric thresholds
    if re.search(r'\d+\s*%', spec_content) or re.search(r'>=|<=|>|<\s*\d+', spec_content):
        return True, "Quantifiable success criteria found."
    return False, "No quantifiable success criteria found."

def main():
    project_root = get_project_root()
    spec_path = project_root / "specs" / "001-agriculture-optimization" / "spec.md"
    plan_path = project_root / "specs" / "001-agriculture-optimization" / "plan.md"

    if not spec_path.exists():
        print(f"Error: {spec_path} not found.")
        sys.exit(1)
    if not plan_path.exists():
        print(f"Error: {plan_path} not found.")
        sys.exit(1)

    spec_content = spec_path.read_text()
    plan_content = plan_path.read_text()

    errors = []

    # Check for TODOs in spec
    has_todos, todos = check_todos(spec_path)
    if has_todos:
        errors.append(f"TODOs found in spec.md: {todos}")

    # Check for TODOs in plan
    has_todos_plan, todos_plan = check_todos(plan_path)
    if has_todos_plan:
        errors.append(f"TODOs found in plan.md: {todos_plan}")

    # Check Hypothesis
    hyp_ok, hyp_msg = check_research_hypothesis(spec_content)
    if not hyp_ok:
        errors.append(hyp_msg)

    # Check Success Criteria
    crit_ok, crit_msg = check_success_criteria(spec_content)
    if not crit_ok:
        errors.append(crit_msg)

    if errors:
        print("Spec Completeness Check FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("Spec Completeness Check PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
