import os
import re
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any, Set

# Ensure we can import from the project root if run as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.setup_paths import ensure_project_dirs

def extract_citations_from_text(text: str) -> List[Dict[str, str]]:
    """
    Extract citations from a markdown/text block.
    Looks for patterns like:
    - [1] DOI: 10.xxxx/xxxxx
    - URL: https://...
    - (Author, Year) -> attempts to extract if possible, but prioritizes DOI/URL
    
    Returns a list of dicts with 'url' (DOI or URL) and 'title' (if found).
    """
    citations = []
    
    # Regex for DOI
    doi_pattern = r'DOI[:\s]+(10\.\d{4,9}/[-._;()/:A-Z0-9]+)'
    # Regex for HTTP/HTTPS URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    # Find DOIs
    doi_matches = re.findall(doi_pattern, text, re.IGNORECASE)
    for doi in doi_matches:
        citations.append({
            'url': doi,
            'title': f"DOI: {doi}", # Placeholder title, real fetch happens in validator
            'source_type': 'doi'
        })
    
    # Find URLs (excluding DOIs which are already caught)
    url_matches = re.findall(url_pattern, text)
    for url in url_matches:
        # Skip if it looks like a DOI in a URL (rare) or already found
        if not any(c['url'] == url for c in citations):
            citations.append({
                'url': url,
                'title': f"URL: {url}",
                'source_type': 'url'
            })
    
    # Deduplicate based on URL
    unique_citations = []
    seen_urls = set()
    for c in citations:
        if c['url'] not in seen_urls:
            seen_urls.add(c['url'])
            unique_citations.append(c)
    
    return unique_citations

def parse_markdown_file(file_path: str) -> List[Dict[str, str]]:
    """
    Parse a markdown file and extract all citations.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return extract_citations_from_text(content)

def main():
    """
    Main entry point for T070a:
    Parse research.md and plan.md, extract citations, write to state/citations.yaml.
    """
    # Paths relative to project root
    project_root = PROJECT_ROOT
    research_md_path = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c" / "research.md"
    plan_md_path = project_root / "plan.md"
    output_path = project_root / "state" / "citations.yaml"
    
    # Ensure state directory exists
    ensure_project_dirs(project_root)
    
    all_citations = []
    
    # Parse research.md
    if research_md_path.exists():
        print(f"Parsing {research_md_path}...")
        all_citations.extend(parse_markdown_file(str(research_md_path)))
    else:
        print(f"Warning: {research_md_path} not found.")
    
    # Parse plan.md
    if plan_md_path.exists():
        print(f"Parsing {plan_md_path}...")
        all_citations.extend(parse_markdown_file(str(plan_md_path)))
    else:
        print(f"Warning: {plan_md_path} not found.")
    
    if not all_citations:
        print("No citations found in the provided documents.")
        # Still write an empty list to satisfy the requirement of creating the file
        final_output = []
    else:
        # Assign IDs and format for YAML
        final_output = []
        for i, c in enumerate(all_citations, 1):
            final_output.append({
                'id': f'C{i:03d}',
                'url': c['url'],
                'title': c['title']
            })
    
    # Write to YAML
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(final_output, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Successfully wrote {len(final_output)} citations to {output_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
