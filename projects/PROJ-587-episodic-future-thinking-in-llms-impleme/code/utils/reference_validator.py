"""
Reference Validator for Constitution Principle II.

This module validates that the implementation plan (plan.md) correctly cites
the design documents and data sources specified in the project specifications.
It also provides a pre-commit hook entry point to enforce citation verification.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
PLAN_PATH = PROJECT_ROOT / "plan.md"
SPECS_DIR = PROJECT_ROOT / "specs"
DATA_DIR = PROJECT_ROOT / "data"

# Required citations pattern (Constitution Principle II)
# Must cite at least one design doc from specs/ and one data source
REQUIRED_CITATION_PATTERNS = [
    r"specs/[\w-]+",          # Design documents
    r"data/[\w/-]+\.(csv|json|parquet|txt)", # Data files
    r"ALFWorld|TextWorld",    # Dataset names
]

class ReferenceValidationError(Exception):
    """Raised when citation validation fails."""
    pass

def load_plan_content() -> str:
    """Load the content of plan.md."""
    if not PLAN_PATH.exists():
        raise FileNotFoundError(f"Plan file not found: {PLAN_PATH}")
    return PLAN_PATH.read_text(encoding="utf-8")

def extract_citations(text: str) -> List[str]:
    """
    Extract all potential citations from text.
    Looks for patterns like 'specs/...', 'data/...', or dataset names.
    """
    citations = []
    # Match file paths and dataset names
    patterns = [
        r"specs/[\w/-]+",
        r"data/[\w/-]+\.(csv|json|parquet|txt)",
        r"(?i)ALFWorld",
        r"(?i)TextWorld",
        r"(?i)commit_hashes\.txt",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        citations.extend(matches)
    
    return list(set(citations))

def extract_file_references(text: str) -> Dict[str, List[str]]:
    """
    Extract file references and their context from the plan.
    Returns a dict mapping file path to list of context lines.
    """
    references = {}
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # Look for file references in the line
        if 'specs/' in line or 'data/' in line:
            # Extract the file path
            match = re.search(r'(specs/[\w/-]+|data/[\w/-]+\.\w+)', line)
            if match:
                file_path = match.group(1)
                if file_path not in references:
                    references[file_path] = []
                # Add context (previous and next lines)
                context = []
                if i > 0:
                    context.append(lines[i-1].strip())
                context.append(line.strip())
                if i < len(lines) - 1:
                    context.append(lines[i+1].strip())
                references[file_path].append('\n'.join(context))
    
    return references

def validate_citations(citations: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that all citations point to existing files or valid sources.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    for citation in citations:
        # Check if it's a file path
        if citation.startswith('specs/') or citation.startswith('data/'):
            full_path = PROJECT_ROOT / citation
            if not full_path.exists():
                errors.append(f"Missing referenced file: {citation}")
        # Check for dataset names
        elif 'ALFWorld' in citation or 'TextWorld' in citation:
            # These are expected to be downloaded, so we just check they are mentioned
            pass
        elif 'commit_hashes.txt' in citation:
            # This should exist in data/
            expected_path = PROJECT_ROOT / "data" / "commit_hashes.txt"
            if not expected_path.exists():
                errors.append(f"Missing commit hashes file: {citation}")
    
    return len(errors) == 0, errors

def validate_plan_references() -> Tuple[bool, List[str]]:
    """
    Main validation function for Constitution Principle II.
    Checks that plan.md contains required citations and they are valid.
    """
    try:
        content = load_plan_content()
    except FileNotFoundError as e:
        return False, [str(e)]
    
    # Extract citations
    citations = extract_citations(content)
    
    if not citations:
        return False, ["No citations found in plan.md"]
    
    # Validate citations
    is_valid, errors = validate_citations(citations)
    
    # Check for minimum required citations
    has_specs = any('specs/' in c for c in citations)
    has_data = any('data/' in c or 'ALFWorld' in c or 'TextWorld' in c for c in citations)
    
    if not has_specs:
        errors.append("Missing reference to specs/ directory (design documents)")
    if not has_data:
        errors.append("Missing reference to data sources (ALFWorld/TextWorld)")
    
    return len(errors) == 0, errors

def pre_commit_hook() -> int:
    """
    Pre-commit hook entry point.
    Returns 0 if validation passes, 1 if it fails.
    """
    print("Running Constitution Principle II citation validation...")
    
    is_valid, errors = validate_plan_references()
    
    if is_valid:
        print("✓ All citations validated successfully.")
        return 0
    else:
        print("✗ Citation validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

def main():
    """Command-line entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate plan.md citations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()
    
    try:
        content = load_plan_content()
        citations = extract_citations(content)
        references = extract_file_references(content)
        
        print(f"Found {len(citations)} citations in plan.md")
        if args.verbose:
            print("\nCitations found:")
            for c in citations:
                print(f"  - {c}")
            
            print("\nFile references with context:")
            for file_path, contexts in references.items():
                print(f"\n  File: {file_path}")
                for ctx in contexts:
                    print(f"    {ctx}")
        
        is_valid, errors = validate_plan_references()
        
        if is_valid:
            print("\n✓ Validation PASSED")
            sys.exit(0)
        else:
            print("\n✗ Validation FAILED")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()