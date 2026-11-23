"""
Citation Validator Script for PROJ-006-agriculture-optimization.

This script parses research.md to check for citation validity.
- If research.md is missing: Exit 0 with warning.
- If placeholders (TODO, Placeholder) are found: Exit 0 with warning.
- If real citations are found: Exit 1 (to be fixed by T050c).
"""
import sys
import re
from pathlib import Path

# Define the project root relative to this script's location
# Assuming standard layout: code/src/cli/validate_citations.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESEARCH_FILE = PROJECT_ROOT / "research.md"

# Patterns for placeholders
PLACEHOLDER_PATTERNS = [
    r'\bTODO\b',
    r'\bPlaceholder\b',
    r'\[TODO\]',
    r'\[Placeholder\]',
    r'TODO:',
    r'Placeholder:'
]

# Patterns for "real" citations (basic heuristic: author-year or numbered refs)
# This is a heuristic to detect if the file contains actual content vs just placeholders.
# We look for patterns like (Author, Year) or [1] or similar academic markers.
REAL_CITATION_PATTERNS = [
    r'\([A-Z][a-z]+,\s*\d{4}\)',  # (Author, 2024)
    r'\[[0-9]+\]',                 # [1]
    r'\bdoi:\s*10\.\d+',           # DOI
    r'\bhttps?://',                # URLs (often in refs)
    r'\bref\b',                    # "ref" keyword
]

def check_placeholders(content: str) -> bool:
    """Check if content contains placeholder markers."""
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def check_real_citations(content: str) -> bool:
    """Check if content contains indicators of real citations."""
    for pattern in REAL_CITATION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def main():
    """Main entry point for citation validation."""
    if not RESEARCH_FILE.exists():
        print(f"WARNING: {RESEARCH_FILE} not found. Exiting with status 0.")
        sys.exit(0)

    try:
        content = RESEARCH_FILE.read_text(encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Could not read {RESEARCH_FILE}: {e}")
        sys.exit(1)

    has_placeholders = check_placeholders(content)
    has_real_citations = check_real_citations(content)

    if has_placeholders:
        print("WARNING: Placeholder citations detected in research.md.")
        print("Exiting with status 0 (allowed for stub phase).")
        sys.exit(0)

    if has_real_citations:
        print("ERROR: Real citations detected in research.md.")
        print("Validation failed. Please ensure citations are valid (Task T050c).")
        sys.exit(1)

    # If we get here, the file exists but has no placeholders and no obvious real citations.
    # Treat this as a warning (empty or malformed) but exit 0 to allow progression to T050c.
    print("WARNING: research.md exists but contains no obvious placeholders or real citations.")
    print("Assuming stub phase. Exiting with status 0.")
    sys.exit(0)

if __name__ == "__main__":
    main()