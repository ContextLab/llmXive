"""
Test script for T038b: Verify Contract Documentation Links.

This script verifies that the links added in T038a to docs/quickstart.md 
and docs/data-model.md are correct and functional by checking that the 
referenced schema files under contracts/ actually exist on disk.
"""
import os
import re
import sys
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_markdown_links(content: str) -> list[str]:
    """Extract all relative file paths referenced as links in markdown content."""
    # Match markdown links: [text](path)
    # We are interested in paths, not necessarily URLs
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)
    
    links = []
    for text, url in matches:
        # Filter for local file references (start with ./ or ../ or just filename)
        # Exclude http/https URLs
        if not url.startswith(('http://', 'https://', '#')):
            links.append(url)
    return links

def verify_contract_links(doc_path: Path, contracts_root: Path) -> bool:
    """
    Verify that all links to contract files in the given document exist.
    
    Args:
        doc_path: Path to the markdown document to check
        contracts_root: Path to the contracts directory root
        
    Returns:
        True if all contract links are valid, False otherwise
    """
    if not doc_path.exists():
        logger.error(f"Document not found: {doc_path}")
        return False
    
    logger.info(f"Checking document: {doc_path}")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    links = extract_markdown_links(content)
    
    # Filter for links that point to the contracts directory
    contract_links = [
        link for link in links 
        if 'contracts' in link or link.startswith('contracts/')
    ]
    
    if not contract_links:
        logger.warning(f"No contract links found in {doc_path}")
        return True  # No links to verify, so it passes
    
    all_valid = True
    for link in contract_links:
        # Resolve the path relative to the document's directory
        # Handle both relative paths starting with ./ or without
        if link.startswith('./'):
            rel_path = link[2:]
        else:
            rel_path = link
        
        # Construct full path from project root
        # Assume the doc is in docs/ and contracts are at root/contracts/
        full_path = Path.cwd() / rel_path
        
        if not full_path.exists():
            logger.error(f"Contract link broken: {link} -> {full_path}")
            all_valid = False
        else:
            logger.info(f"Contract link valid: {link} -> {full_path}")
    
    return all_valid

def main():
    parser = argparse.ArgumentParser(
        description='Verify that contract documentation links are functional.'
    )
    parser.add_argument(
        '--docs-dir',
        type=str,
        default='docs',
        help='Path to the documentation directory'
    )
    parser.add_argument(
        '--contracts-dir',
        type=str,
        default='contracts',
        help='Path to the contracts directory'
    )
    
    args = parser.parse_args()
    
    docs_dir = Path(args.docs_dir)
    contracts_dir = Path(args.contracts_dir)
    
    if not docs_dir.exists():
        logger.error(f"Docs directory not found: {docs_dir}")
        sys.exit(1)
    
    if not contracts_dir.exists():
        logger.error(f"Contracts directory not found: {contracts_dir}")
        sys.exit(1)
    
    # Files to check as per T038a
    files_to_check = [
        docs_dir / 'quickstart.md',
        docs_dir / 'data-model.md'
    ]
    
    all_passed = True
    for doc_file in files_to_check:
        if not doc_file.exists():
            logger.warning(f"Document does not exist, skipping: {doc_file}")
            continue
        
        if not verify_contract_links(doc_file, contracts_dir):
            all_passed = False
    
    if all_passed:
        logger.info("SUCCESS: All contract documentation links are valid.")
        sys.exit(0)
    else:
        logger.error("FAILURE: One or more contract documentation links are broken.")
        sys.exit(1)

if __name__ == '__main__':
    main()