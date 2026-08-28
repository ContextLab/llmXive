"""
Citation Extraction Utility for llmXive Project.

Parses research.md and plan.md to extract all cited DOIs and URLs.
Outputs a structured YAML file: state/citations.yaml
"""
import os
import re
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any, Set

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SPECS_DIR = PROJECT_ROOT / "specs" / "001-evaluating-the-impact-of-llm-generated-c"
STATE_DIR = PROJECT_ROOT / "state"

# Paths to parse
RESEARCH_MD_PATH = SPECS_DIR / "research.md"
PLAN_MD_PATH = PROJECT_ROOT / "plan.md"

# Regex patterns for extraction
# Matches standard DOI format: 10.xxxx/xxxxx
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)

# Matches URLs (http/https)
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')

def extract_citations_from_text(text: str, source_name: str) -> List[Dict[str, Any]]:
    """
    Extract DOIs and URLs from a block of text.
    Returns a list of citation objects.
    """
    citations = []
    seen_ids = set()

    # Extract DOIs
    dois = DOI_PATTERN.findall(text)
    for doi in dois:
        if doi not in seen_ids:
            seen_ids.add(doi)
            # Construct a standard DOI URL
            url = f"https://doi.org/{doi}"
            citations.append({
                "id": doi,
                "url": url,
                "title": f"DOI: {doi}", # Title will be resolved later or kept as ID if not fetched
                "source": source_name
            })

    # Extract URLs (excluding those that are just DOI redirects if already caught)
    urls = URL_PATTERN.findall(text)
    for url in urls:
        # Clean trailing punctuation often attached to URLs in markdown
        clean_url = url.rstrip('.,;:')
        if clean_url not in seen_ids and not clean_url.startswith('https://doi.org/'):
            seen_ids.add(clean_url)
            # Heuristic for title: extract domain or use URL itself
            title = clean_url
            if '://' in clean_url:
                domain = clean_url.split('://')[1].split('/')[0]
                title = f"URL from {domain}"
            
            citations.append({
                "id": clean_url, # Use URL as ID for non-DOI
                "url": clean_url,
                "title": title,
                "source": source_name
            })

    return citations

def parse_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Reads a markdown file and extracts citations.
    """
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}", file=sys.stderr)
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    source_name = file_path.name
    return extract_citations_from_text(content, source_name)

def main():
    """
    Main entry point for citation extraction.
    """
    all_citations = []
    
    # Parse research.md
    if RESEARCH_MD_PATH.exists():
        print(f"Parsing {RESEARCH_MD_PATH}...")
        all_citations.extend(parse_markdown_file(RESEARCH_MD_PATH))
    else:
        print(f"Error: {RESEARCH_MD_PATH} not found. Cannot proceed without research.md.", file=sys.stderr)
        sys.exit(1)

    # Parse plan.md
    if PLAN_MD_PATH.exists():
        print(f"Parsing {PLAN_MD_PATH}...")
        all_citations.extend(parse_markdown_file(PLAN_MD_PATH))

    # Deduplicate by ID (URL or DOI)
    unique_citations = []
    seen_ids = set()
    for c in all_citations:
        if c['id'] not in seen_ids:
            seen_ids.add(c['id'])
            unique_citations.append(c)

    if not unique_citations:
        print("Warning: No citations found in the specified files.", file=sys.stderr)
        # Still create an empty file to satisfy the artifact requirement
        output_data = {"citations": []}
    else:
        output_data = {"citations": unique_citations}

    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = STATE_DIR / "citations.yaml"

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)

    print(f"Successfully wrote {len(unique_citations)} citations to {output_path}")

if __name__ == "__main__":
    main()
