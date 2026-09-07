"""
Verify Novelty and Hypothesis (T061).

Parses spec.md for a "Novelty and Research Gap" subsection citing multiple studies
and validates the hypothesis contains directional expectations and measurable thresholds.

Exits 0 if valid; exits 1 if missing or insufficient.
"""
import sys
import re
from pathlib import Path

def find_project_root():
    """Find the project root by looking for the specs directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "specs" / "001-climate-smart-eval").exists():
            return current
        current = current.parent
    return None

def load_spec(path: Path) -> str:
    """Load the spec.md file."""
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")
    return path.read_text(encoding="utf-8")

def check_novelty_section(text: str) -> tuple[bool, list[str]]:
    """
    Check for 'Novelty and Research Gap' section with multiple citations.
    Returns (is_valid, list_of_issues).
    """
    issues = []
    
    # Look for the section header (case insensitive)
    novelty_pattern = r'##\s*[Nn]ovelty\s+and\s+[Rr]esearch\s+[Gg]ap'
    match = re.search(novelty_pattern, text)
    if not match:
        issues.append("Missing 'Novelty and Research Gap' section header.")
        return False, issues

    # Extract the section content (until next ## or end of file)
    start = match.end()
    next_header = re.search(r'\n##\s+', text[start:])
    if next_header:
        section_text = text[start : start + next_header.start()]
    else:
        section_text = text[start:]

    # Check for multiple citations (e.g., [1], [2], (Author, Year), etc.)
    citation_patterns = [
        r'\[\d+\]',          # [1], [2]
        r'\([A-Z][a-z]+,\s*\d{4}\)', # (Smith, 2020)
        r'et\s+al\.',        # et al.
        r'Journal\s+of',     # Journal of X
    ]
    
    citation_count = 0
    for pattern in citation_patterns:
        citation_count += len(re.findall(pattern, section_text, re.IGNORECASE))
    
    if citation_count < 2:
        issues.append(f"Novelty section found but lacks multiple citations (found {citation_count}).")
        return False, issues

    return True, issues

def check_hypothesis(text: str) -> tuple[bool, list[str]]:
    """
    Check for a Research Hypothesis with directional expectations and measurable thresholds.
    Returns (is_valid, list_of_issues).
    """
    issues = []
    
    # Look for hypothesis section
    hyp_pattern = r'##\s*[Rr]esearch\s+[Hh]ypothesis|##\s*[Hh]ypothesis'
    match = re.search(hyp_pattern, text)
    if not match:
        issues.append("Missing 'Research Hypothesis' section.")
        return False, issues

    # Extract section
    start = match.end()
    next_header = re.search(r'\n##\s+', text[start:])
    if next_header:
        section_text = text[start : start + next_header.start()]
    else:
        section_text = text[start:]

    # Check for directional expectation (positive/negative, increase/decrease, etc.)
    directional_keywords = [
        r'increase', r'decrease', r'positively', r'negatively',
        r'higher', r'lower', r'greater', r'less', r'rise', r'drop',
        r'correlate', r'associated'
    ]
    has_direction = any(re.search(kw, section_text, re.IGNORECASE) for kw in directional_keywords)
    
    if not has_direction:
        issues.append("Hypothesis lacks directional expectation (e.g., increase, decrease).")

    # Check for measurable thresholds (numbers, percentages, p-values, etc.)
    threshold_patterns = [
        r'\d+%',           # 10%
        r'\d+\.\d+',       # 0.05
        r'>\s*\d+',        # > 100
        r'<\s*\d+',        # < 0.05
        r'n\s*>\s*\d+',    # n > 30
        r'p\s*<',          # p < 0.05
    ]
    has_threshold = any(re.search(p, section_text, re.IGNORECASE) for p in threshold_patterns)
    
    if not has_threshold:
        issues.append("Hypothesis lacks measurable thresholds (e.g., percentages, p-values, sample sizes).")

    if not has_direction or not has_threshold:
        return False, issues

    return True, issues

def main():
    project_root = find_project_root()
    if not project_root:
        print("ERROR: Could not find project root with specs/001-climate-smart-eval", file=sys.stderr)
        sys.exit(1)

    spec_path = project_root / "specs" / "001-climate-smart-eval" / "spec.md"
    
    try:
        spec_text = load_spec(spec_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    all_issues = []

    # Check Novelty
    novelty_valid, novelty_issues = check_novelty_section(spec_text)
    all_issues.extend(novelty_issues)

    # Check Hypothesis
    hypothesis_valid, hypothesis_issues = check_hypothesis(spec_text)
    all_issues.extend(hypothesis_issues)

    if all_issues:
        print("Verification FAILED with the following issues:")
        for issue in all_issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("Novelty and Hypothesis verification PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()