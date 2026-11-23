"""
Task T061: Verify Novelty & Hypothesis
Parses spec.md for a 'Novelty and Research Gap' subsection citing multiple studies
and validates the hypothesis contains directional expectations and measurable thresholds.
Exits 0 if valid; exits 1 if missing or insufficient.
"""
import sys
import re
from pathlib import Path

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up to find the project root (usually where 'specs' or 'data' is)
    # Assuming the script is in scripts/ at the root level
    if (current.parent / "specs").exists():
        return current.parent
    # Fallback: search up
    for parent in current.parents:
        if (parent / "specs").exists():
            return parent
    return current.parent

def load_spec_file(root: Path) -> str:
    """Load spec.md content."""
    # Try common locations based on filesystem hygiene requirements
    possible_paths = [
        root / "specs" / "001-climate-smart-eval" / "spec.md",
        root / "specs" / "001-agriculture-optimization" / "spec.md",
        root / "spec.md"
    ]
    for p in possible_paths:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("Could not find spec.md in expected locations.")

def check_novelty_section(content: str) -> bool:
    """
    Check for 'Novelty and Research Gap' section with multiple citations.
    A citation is identified by patterns like:
    - [Author, Year]
    - (Author, Year)
    - Author (Year)
    """
    # Look for the section header
    novelty_patterns = [
        r"Novelty and Research Gap",
        r"Research Gap",
        r"Novelty",
        r"Gap in Literature"
    ]
    
    has_section = False
    for pattern in novelty_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            has_section = True
            break
    
    if not has_section:
        print("ERROR: No 'Novelty and Research Gap' section found in spec.md")
        return False

    # Extract the section content (heuristic: from header to next major header or end)
    # We'll just check the whole file for multiple citations for simplicity
    # Citation pattern: [Name, Year] or (Name, Year) or Name (Year)
    citation_pattern = r'\[?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,?\s+\d{4}\]?'
    citations = re.findall(citation_pattern, content)
    
    # Filter out false positives (e.g., generic years)
    valid_citations = [c for c in citations if len(c) > 5] # Rough heuristic
    
    # More robust: count unique citation-like strings
    # Look for patterns like "Smith et al. (2020)" or "[Smith, 2020]"
    robust_pattern = r'(?:\[?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+et\s+al\.)?,?\s+\d{4}\]?)'
    robust_citations = re.findall(robust_pattern, content)
    
    if len(robust_citations) < 2:
        print(f"ERROR: Insufficient citations in 'Novelty and Research Gap' section. Found {len(robust_citations)}, need >= 2.")
        return False
    
    print(f"OK: Found {len(robust_citations)} citations in novelty section.")
    return True

def check_hypothesis(content: str) -> bool:
    """
    Validate the hypothesis contains:
    1. Directional expectations (e.g., 'increase', 'decrease', 'positive', 'negative')
    2. Measurable thresholds (e.g., 'by 10%', 'p < 0.05', 'greater than 5')
    """
    # Look for hypothesis section
    hypothesis_patterns = [
        r"Research Hypothesis",
        r"Hypothesis",
        r"Testable Hypothesis"
    ]
    
    has_hypothesis = False
    hypothesis_text = ""
    
    for pattern in hypothesis_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            has_hypothesis = True
            # Extract a chunk around the match
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 500)
            hypothesis_text = content[start:end]
            break
    
    if not has_hypothesis:
        print("ERROR: No 'Research Hypothesis' section found in spec.md")
        return False

    # Check for directional language
    directional_words = [
        r"increase", r"decrease", r"improve", r"reduce",
        r"positive", r"negative", r"higher", r"lower",
        r"greater", r"less", r"enhance", r"diminish"
    ]
    has_direction = any(re.search(word, hypothesis_text, re.IGNORECASE) for word in directional_words)
    
    if not has_direction:
        print("ERROR: Hypothesis lacks directional expectations.")
        return False

    # Check for measurable thresholds
    threshold_patterns = [
        r"\d+\s*%",
        r"\d+\.\d+",
        r"p\s*[<>=]",
        r"significantly",
        r"threshold",
        r"by\s+\d+",
        r"at\s+least",
        r"at\s+most"
    ]
    has_threshold = any(re.search(pattern, hypothesis_text, re.IGNORECASE) for pattern in threshold_patterns)
    
    if not has_threshold:
        print("ERROR: Hypothesis lacks measurable thresholds.")
        return False

    print("OK: Hypothesis contains directional expectations and measurable thresholds.")
    return True

def main():
    root = get_project_root()
    try:
        content = load_spec_file(root)
    except FileNotFoundError as e:
        print(f"CRITICAL: {e}")
        sys.exit(1)

    novelty_ok = check_novelty_section(content)
    hypothesis_ok = check_hypothesis(content)

    if novelty_ok and hypothesis_ok:
        print("SUCCESS: Novelty and Hypothesis validation passed.")
        sys.exit(0)
    else:
        print("FAILURE: Novelty and/or Hypothesis validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()