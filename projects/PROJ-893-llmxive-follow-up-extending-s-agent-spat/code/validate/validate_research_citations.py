import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

from config import Config

def read_file(file_path: Path) -> str:
    """Read the content of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_verified_datasets(content: str) -> Set[str]:
    """
    Extract dataset identifiers from the 'Verified Datasets' block.
    Looks for a section header and extracts lines that look like dataset IDs or titles.
    """
    verified_datasets = set()
    # Pattern to find the block (case insensitive)
    pattern = r"Verified Datasets.*?(?=##|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        return verified_datasets

    block_content = match.group(0)
    
    # Extract lines that look like dataset references (e.g., "llmXive/S-AgentK", "S-Agent-300K")
    # Assuming the format is a list or bullet points
    lines = block_content.split('\n')
    for line in lines:
        line = line.strip()
        # Remove bullet points or numbering
        line = re.sub(r'^[-*•]\s*', '', line)
        line = re.sub(r'^\d+\.\s*', '', line)
        
        if not line or line.startswith('#'):
            continue
            
        # Extract potential dataset IDs (e.g., user/repo or just descriptive names)
        # We look for strings that contain '/' or are clearly dataset names
        if '/' in line:
            # Likely a HuggingFace ID
            verified_datasets.add(line.split()[0]) # Take first token if there's trailing text
        else:
            # Descriptive name, store as is
            verified_datasets.add(line)
            
    return verified_datasets

def tokenize_title(title: str) -> Set[str]:
    """Convert a title string into a set of lowercase tokens."""
    # Split on non-alphanumeric characters, lower case
    tokens = re.split(r'[^a-zA-Z0-9]+', title.lower())
    return {t for t in tokens if len(t) > 1} # Filter out single chars

def calculate_token_overlap(tokens1: Set[str], tokens2: Set[str]) -> float:
    """Calculate Jaccard similarity (token overlap) between two sets."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    if union == 0:
        return 0.0
    return intersection / union

def extract_citations_from_markdown(content: str) -> List[Dict[str, str]]:
    """
    Extract citations from markdown content.
    Returns a list of dicts with 'title' and 'ref' (or identifier).
    """
    citations = []
    
    # Pattern for markdown link: [Title](URL) or [Title](ref)
    # Also handle footnotes or simple references if present
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)
    
    for title, ref in matches:
        # Filter out non-citation links (e.g., images, internal nav if not citation)
        # For this task, we assume all [Title](ref) in the body are candidates
        # or specifically look for references to datasets
        citations.append({
            'title': title,
            'ref': ref
        })
        
    # Also check for explicit citations like "[1] Title" or similar if the format varies
    # But the primary format in research.md is likely markdown links
    return citations

def validate_citations(research_md_path: Path, verified_datasets: Set[str], threshold: float = 0.7) -> Tuple[bool, List[Dict]]:
    """
    Validate that citations in research.md match the Verified Datasets.
    Returns (is_valid, list_of_failures).
    """
    content = read_file(research_md_path)
    citations = extract_citations_from_markdown(content)
    
    failures = []
    is_valid = True
    
    # If no verified datasets found in spec, we might skip or warn, 
    # but per task, we assume they exist.
    if not verified_datasets:
        # Fallback: if no verified datasets defined, we cannot validate against them.
        # However, the task implies we must check against the block.
        # If the block is empty, we might treat it as a failure of the source document.
        pass

    for citation in citations:
        title = citation['title']
        ref = citation['ref']
        
        # Check against verified datasets
        match_found = False
        best_overlap = 0.0
        
        # Tokenize the citation title
        citation_tokens = tokenize_title(title)
        
        for dataset_id in verified_datasets:
            dataset_tokens = tokenize_title(dataset_id)
            overlap = calculate_token_overlap(citation_tokens, dataset_tokens)
            if overlap > best_overlap:
                best_overlap = overlap
            if overlap >= threshold:
                match_found = True
                break
        
        if not match_found:
            is_valid = False
            failures.append({
                'citation': title,
                'ref': ref,
                'reason': f"No match found in verified datasets (best overlap: {best_overlap:.2f} < {threshold})"
            })
    
    return is_valid, failures

def main():
    parser = argparse.ArgumentParser(description="Validate citations in research.md against Verified Datasets.")
    parser.add_argument("--research-file", type=str, default="research.md", help="Path to research.md")
    parser.add_argument("--spec-file", type=str, default="specs/001-symbolic-spatial-reasoning/spec.md", help="Path to spec.md containing Verified Datasets")
    parser.add_argument("--threshold", type=float, default=0.7, help="Token overlap threshold")
    args = parser.parse_args()

    research_path = Path(args.research_file)
    spec_path = Path(args.spec_file)

    if not research_path.exists():
        print(f"ERROR: research.md not found at {research_path}.")
        print("The pipeline cannot proceed until research.md is generated (Phase 0 output).")
        sys.exit(1)

    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}.")
        sys.exit(1)

    try:
        spec_content = read_file(spec_path)
        verified_datasets = extract_verified_datasets(spec_content)
        
        if not verified_datasets:
            print("WARNING: No verified datasets found in spec.md. Cannot validate citations.")
            # Depending on strictness, this could be an error. 
            # For now, we proceed but warn.
        
        is_valid, failures = validate_citations(research_path, verified_datasets, args.threshold)

        if not is_valid:
            print("CITATION VALIDATION FAILED:")
            for f in failures:
                print(f"  - {f['citation']}: {f['reason']}")
            print("\nThis is the final Verified Accuracy Gate. The pipeline MUST NOT proceed.")
            sys.exit(1)
        else:
            print("CITATION VALIDATION PASSED: All citations match verified datasets.")
            sys.exit(0)

    except Exception as e:
        print(f"ERROR during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()