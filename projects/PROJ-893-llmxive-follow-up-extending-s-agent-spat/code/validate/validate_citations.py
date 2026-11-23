"""
validate_citations.py
Verifies citations in spec.md and plan.md against the "Verified Datasets" block.
Requirement: Must check title-token-overlap >= 0.7. Exit with error if any citation
is unreachable or mismatched. (Constitution Principle II).
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

# Configuration for the project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent.parent
SPEC_MD_PATH = PROJECT_ROOT / "specs" / "001-symbolic-spatial-reasoning" / "spec.md"
PLAN_MD_PATH = PROJECT_ROOT / "plan.md"

# Regex to extract citations from markdown text
# Matches patterns like [Title](url) or just [Title]
CITATION_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
# Regex to extract "Verified Datasets" block content
VERIFIED_BLOCK_PATTERN = re.compile(
    r'##\s*Verified\s+Datasets\s*\n(.*?)(?=\n##|\Z)', 
    re.DOTALL | re.IGNORECASE
)
# Regex to extract dataset entries from the block
# Looks for lines like: - Dataset: Name | URL: ...
DATASET_ENTRY_PATTERN = re.compile(
    r'-\s*Dataset:\s*(.+?)\s*\|\s*URL:\s*(.+?)(?:\s*\||\n|$)',
    re.IGNORECASE
)

def tokenize_title(title: str) -> Set[str]:
    """
    Tokenize a title into a set of lowercase words for overlap calculation.
    Removes punctuation and splits on whitespace.
    """
    # Remove punctuation and split
    words = re.sub(r'[^\w\s]', '', title.lower()).split()
    # Filter out very short tokens (optional, but good for noise reduction)
    return {w for w in words if len(w) > 2}

def calculate_token_overlap(title1: str, title2: str) -> float:
    """
    Calculate Jaccard similarity (token overlap) between two titles.
    Returns a float between 0.0 and 1.0.
    """
    tokens1 = tokenize_title(title1)
    tokens2 = tokenize_title(title2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def extract_verified_datasets(content: str) -> Dict[str, str]:
    """
    Extract verified datasets from the content.
    Returns a dictionary mapping Dataset Name -> URL.
    """
    verified_datasets = {}
    match = VERIFIED_BLOCK_PATTERN.search(content)
    if not match:
        return verified_datasets
    
    block_content = match.group(1)
    entries = DATASET_ENTRY_PATTERN.findall(block_content)
    
    for name, url in entries:
        name = name.strip()
        url = url.strip()
        if name and url:
            verified_datasets[name] = url
    
    return verified_datasets

def extract_citations_from_markdown(content: str) -> List[Tuple[str, str]]:
    """
    Extract all citations from markdown content.
    Returns a list of tuples: (title, url).
    """
    return CITATION_PATTERN.findall(content)

def validate_citations(citations: List[Tuple[str, str]], verified_datasets: Dict[str, str], threshold: float = 0.7) -> Tuple[bool, List[Dict]]:
    """
    Validate that every citation in the text matches a verified dataset.
    A match is defined as title-token-overlap >= threshold.
    Returns (is_valid, list_of_failures).
    """
    failures = []
    
    for title, url in citations:
        matched = False
        best_overlap = 0.0
        best_match_name = None
        
        for verified_name, verified_url in verified_datasets.items():
            # Check URL match first (exact or substring)
            if url == verified_url or verified_url in url or url in verified_url:
                matched = True
                break
            
            # Check title overlap
            overlap = calculate_token_overlap(title, verified_name)
            if overlap > best_overlap:
                best_overlap = overlap
                best_match_name = verified_name
            
            if overlap >= threshold:
                matched = True
                break
        
        if not matched:
            failure_info = {
                "citation_title": title,
                "citation_url": url,
                "reason": "No match found in verified datasets",
                "best_match": best_match_name,
                "best_overlap": round(best_overlap, 2) if best_match_name else None
            }
            failures.append(failure_info)
    
    return len(failures) == 0, failures

def read_file(path: Path) -> str:
    """Read file content, handling potential errors."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not read {path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Validate citations in spec.md and plan.md against Verified Datasets."
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=0.7, 
        help="Minimum token overlap threshold (default: 0.7)"
    )
    parser.add_argument(
        "--spec-path",
        type=Path,
        default=None,
        help="Path to spec.md (optional, overrides default)"
    )
    parser.add_argument(
        "--plan-path",
        type=Path,
        default=None,
        help="Path to plan.md (optional, overrides default)"
    )
    
    args = parser.parse_args()
    
    spec_path = args.spec_path or SPEC_MD_PATH
    plan_path = args.plan_path or PLAN_MD_PATH
    
    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}", file=sys.stderr)
        sys.exit(1)
    if not plan_path.exists():
        print(f"ERROR: plan.md not found at {plan_path}", file=sys.stderr)
        sys.exit(1)
    
    # Read files
    spec_content = read_file(spec_path)
    plan_content = read_file(plan_path)
    
    # Extract verified datasets from spec.md (usually contains the block)
    # If not found in spec, try plan
    verified_datasets = extract_verified_datasets(spec_content)
    if not verified_datasets:
        verified_datasets = extract_verified_datasets(plan_content)
    
    if not verified_datasets:
        print("ERROR: No 'Verified Datasets' block found in spec.md or plan.md", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(verified_datasets)} verified datasets.")
    for name in verified_datasets:
        print(f"  - {name}")
    
    # Extract citations
    spec_citations = extract_citations_from_markdown(spec_content)
    plan_citations = extract_citations_from_markdown(plan_content)
    all_citations = spec_citations + plan_citations
    
    print(f"Found {len(all_citations)} citations to validate.")
    
    # Validate
    is_valid, failures = validate_citations(all_citations, verified_datasets, args.threshold)
    
    if not is_valid:
        print("\nVALIDATION FAILED:", file=sys.stderr)
        print(f"Found {len(failures)} uncited or mismatched references.", file=sys.stderr)
        for i, f in enumerate(failures, 1):
            print(f"\n{i}. Citation: [{f['citation_title']}]({f['citation_url']})", file=sys.stderr)
            print(f"   Reason: {f['reason']}", file=sys.stderr)
            if f['best_match']:
                print(f"   Best match: {f['best_match']} (overlap: {f['best_overlap']})", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nVALIDATION PASSED: All citations are verified.", file=sys.stdout)
        sys.exit(0)

if __name__ == "__main__":
    main()