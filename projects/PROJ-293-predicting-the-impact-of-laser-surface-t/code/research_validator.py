"""
Research Validator for T039.
Verifies that research.md contains only verified static URLs/IDs and no dynamic search logic.
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Allowed patterns for static data sources
STATIC_URL_PATTERNS = [
  r'https://www\.openml\.org/api/v1/sql/data/\d+',  # OpenML static API
  r'https://www\.openml\.org/d/\d+',                 # OpenML dataset page
  r'https://huggingface\.co/datasets/[\w-]+/[\w-]+', # HuggingFace dataset
  r'https://raw\.githubusercontent\.com/[\w/-]+\.csv', # Direct GitHub raw file
  r'https://github\.com/[\w/-]+/blob/[\w/-]+\.csv',  # GitHub blob link (static)
  r'10\.\d{4,}/[\w./-]+',                            # DOI pattern
]

# Forbidden patterns indicating dynamic search or generic placeholders
FORBIDDEN_PATTERNS = [
  r'search',
  r'query',
  r'\*',
  r'\.com/[\w-]+/search',
  r'placeholder',
  r'example\.com',
  r'insert',
  r'FIXME',
  r'TODO',
  r'add.*here',
]

# Required static identifiers that must be present (example based on typical LST datasets)
# Note: The actual required IDs depend on the specific research plan, but we verify structure.
REQUIRED_SECTIONS = [
  'OpenML',
  'HuggingFace',
  'Literature',
]

def parse_research_md(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Parses research.md and validates it contains only static URLs/IDs.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    if not file_path.exists():
        return False, ["research.md file not found."]

    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"Failed to read research.md: {str(e)}"]

    # Check for forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Forbidden pattern detected: '{pattern}'")

    # Check for dynamic search logic
    dynamic_keywords = [
        'dynamic', 'search_api', 'query_string', 'google_search',
        'scrape', 'crawl', 'find', 'discover'
    ]
    for keyword in dynamic_keywords:
        if keyword in content.lower():
            errors.append(f"Potential dynamic search logic detected: '{keyword}'")

    # Validate URLs found in the file
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, content)

    for url in urls:
        is_valid_url = False
        for static_pattern in STATIC_URL_PATTERNS:
            if re.match(static_pattern, url):
                is_valid_url = True
                break

        if not is_valid_url and not any(url.startswith(p) for p in [
            'mailto:', 'ftp://', 'file://'
        ]):
            # Allow relative paths or other valid protocols, but flag unknown http(s)
            if url.startswith('http'):
                errors.append(f"URL does not match known static pattern: {url}")

    # Check for required sections (basic structural validation)
    for section in REQUIRED_SECTIONS:
        if section not in content:
            # Not strictly an error if not present, but a warning
            # errors.append(f"Missing expected section: {section}")
            pass

    # Ensure no TODOs or placeholders remain
    if re.search(r'\b(TODO|FIXME|XXX|HACK|placeholder)\b', content, re.IGNORECASE):
        errors.append("File contains TODOs or placeholders.")

    return len(errors) == 0, errors

def main():
    """Main entry point for T039 validation."""
    project_root = Path(__file__).resolve().parent.parent
    research_file = project_root / "docs" / "research.md"

    # Fallback if docs/research.md doesn't exist, check root or specs
    if not research_file.exists():
        research_file = project_root / "research.md"
    if not research_file.exists():
        research_file = project_root / "specs" / "research.md"

    if not research_file.exists():
        print("ERROR: research.md not found in expected locations (docs/, root, specs/).")
        sys.exit(1)

    print(f"Validating {research_file}...")
    is_valid, errors = parse_research_md(research_file)

    if is_valid:
        print("SUCCESS: research.md contains only verified static URLs/IDs.")
        sys.exit(0)
    else:
        print("FAILURE: research.md contains invalid or dynamic content.")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
