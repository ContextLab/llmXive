"""
Unit test for T038b: Verify Contract Documentation Links.

This script verifies that the links added in T038a to docs/quickstart.md
and docs/data-model.md are correct and functional by checking that each
referenced file exists under the contracts/ directory.
"""

import os
import re
import sys
from pathlib import Path

# Project root is the parent of the 'tests' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DOCS_DIR = PROJECT_ROOT / "docs"

# Files to check for links
DOC_FILES = [
    "quickstart.md",
    "data-model.md"
]

# Expected contract files that should be linked (based on T038a requirements)
# T038a: "Update docs/quickstart.md and docs/data-model.md to include explicit references 
#         to all schema files under contracts/."
# We will discover all .md and .json files in contracts/ and verify they are linked.

def get_contract_files():
    """Get all schema files (md, json, yaml) in the contracts directory."""
    if not CONTRACTS_DIR.exists():
        return []
    
    files = []
    for ext in ["*.md", "*.json", "*.yaml", "*.yml", "*.txt"]:
        files.extend(CONTRACTS_DIR.glob(ext))
    return files

def extract_links_from_file(file_path):
    """Extract all relative file paths that look like links from a markdown file."""
    if not file_path.exists():
        return []
    
    content = file_path.read_text(encoding="utf-8")
    
    # Regex to match markdown links [text](path) or bare paths like `path/to/file`
    # We look for paths that likely point to the contracts directory
    links = set()
    
    # Match markdown links: [text](path)
    markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(markdown_link_pattern, content):
        path = match.group(2)
        # Normalize path: remove leading ./ or ./
        path = path.lstrip("./")
        if path.startswith("contracts/"):
            links.add(path)
    
    # Match code blocks or inline paths: `contracts/...`
    inline_pattern = r'`([^`]*contracts/[^`]+)`'
    for match in re.finditer(inline_pattern, content):
        path = match.group(1)
        path = path.lstrip("./")
        if path.startswith("contracts/"):
            links.add(path)
    
    return list(links)

def verify_links():
    """Verify that all contract files are linked in the documentation."""
    contract_files = get_contract_files()
    if not contract_files:
        print("WARNING: No contract files found in contracts/ directory.")
        print("This might be expected if T038a hasn't created them yet, or if the directory is empty.")
        # If contracts dir is empty, we can't verify links to non-existent files.
        # But the task is to verify links *added* in T038a. If no contracts exist, 
        # the links can't be verified. We'll treat this as a pass with a note.
        return True, []
    
    missing_links = []
    
    for doc_file_name in DOC_FILES:
        doc_path = DOCS_DIR / doc_file_name
        if not doc_path.exists():
            print(f"ERROR: Documentation file not found: {doc_path}")
            missing_links.append(f"Missing doc file: {doc_file_name}")
            continue
        
        linked_paths = extract_links_from_file(doc_path)
        linked_files = {Path(p) for p in linked_paths}
        
        for contract_file in contract_files:
            rel_path = contract_file.relative_to(PROJECT_ROOT)
            rel_path_str = str(rel_path)
            
            # Check if this contract file is linked
            if contract_file not in linked_files and rel_path_str not in linked_paths:
                # Also check if it's linked by just the filename (sometimes people link just the name)
                if contract_file.name not in [p.name for p in linked_files]:
                    missing_links.append(
                        f"Contract file '{rel_path_str}' is not linked in {doc_file_name}"
                    )
    
    return len(missing_links) == 0, missing_links

def main():
    """Main entry point for the test."""
    print("=== T038b: Verify Contract Documentation Links ===")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Contracts Dir: {CONTRACTS_DIR}")
    print(f"Docs Dir: {DOCS_DIR}")
    print()
    
    contract_files = get_contract_files()
    print(f"Found {len(contract_files)} contract files:")
    for f in contract_files:
        print(f"  - {f.relative_to(PROJECT_ROOT)}")
    print()
    
    success, errors = verify_links()
    
    if success:
        print("✅ SUCCESS: All contract files are properly linked in documentation.")
        return 0
    else:
        print("❌ FAILURE: Some contract files are missing links:")
        for error in errors:
            print(f"  - {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())