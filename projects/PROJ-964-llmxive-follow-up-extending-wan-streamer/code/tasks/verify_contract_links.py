"""
Task T038b: Verify Contract Documentation Links

This script verifies that the links added in T038a to docs/quickstart.md
and docs/data-model.md pointing to files under contracts/ are correct
and functional (i.e., the target files actually exist).
"""
import os
import sys
import re
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DOCS_DIR = PROJECT_ROOT / "docs"

def extract_contract_links(file_path: Path) -> list[str]:
    """
    Extract relative paths to contract files from a markdown file.
    Looks for patterns like `contracts/...` or `/contracts/...` in the text.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    content = file_path.read_text(encoding='utf-8')
    # Regex to find paths starting with 'contracts/' or '/contracts/'
    # Matches markdown links [text](contracts/...) or raw paths
    pattern = r'(?:\(|\s|["\'])(contracts/[^\s)"\'>]+)'
    matches = re.findall(pattern, content)
    
    # Also check for absolute paths if they exist in the text
    abs_pattern = r'(?:\(|\s|["\'])(/contracts/[^\s)"\'>]+)'
    abs_matches = re.findall(abs_pattern, content)
    
    all_matches = matches + [m.lstrip('/') for m in abs_matches]
    return list(set(all_matches))

def verify_links(docs_files: list[Path]) -> bool:
    """
    Verify that all links found in the specified docs files point to existing files.
    Returns True if all links are valid, False otherwise.
    """
    all_valid = True
    found_links = set()

    for doc_file in docs_files:
        if not doc_file.exists():
            logger.warning(f"Documentation file not found, skipping: {doc_file}")
            continue

        logger.info(f"Scanning {doc_file.name} for contract links...")
        links = extract_contract_links(doc_file)
        
        if not links:
            logger.info(f"No contract links found in {doc_file.name}")
            continue

        for link in links:
            found_links.add(link)
            target_path = CONTRACTS_DIR / link
            
            if target_path.exists():
                logger.debug(f"  OK: {link} -> {target_path}")
            else:
                logger.error(f"  MISSING: {link} (Expected at: {target_path})")
                all_valid = False

    if not found_links:
        logger.warning("No contract links were found in the scanned documentation.")
        # This might be a failure of T038a if links were supposed to be added
        # but we strictly check for existence of files if links exist.
        # However, the task is to verify links added in T038a. If none found, 
        # we assume T038a might have failed or links are in a different format.
        # We will treat "no links found" as a warning but not a hard failure 
        # unless the docs explicitly claim to have links. 
        # To be safe, we return False if we expected links but found none.
        # Given the task description "Verify that the links added... are correct",
        # if no links are added, the verification of "correctness" is moot, 
        # but likely indicates a previous step failure.
        # We will return False to indicate the verification condition (links exist and are valid) 
        # was not met because the links themselves are missing.
        logger.error("Verification failed: No contract links found in documentation.")
        return False

    return all_valid

def main():
    parser = argparse.ArgumentParser(description="Verify contract documentation links.")
    parser.add_argument(
        "--docs",
        nargs="+",
        default=["quickstart.md", "data-model.md"],
        help="List of documentation files to check (relative to docs/)."
    )
    args = parser.parse_args()

    docs_paths = [DOCS_DIR / doc for doc in args.docs]

    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Contracts Dir: {CONTRACTS_DIR}")
    logger.info(f"Checking docs: {docs_paths}")

    if not CONTRACTS_DIR.exists():
        logger.error(f"Contracts directory does not exist: {CONTRACTS_DIR}")
        sys.exit(1)

    success = verify_links(docs_paths)

    if success:
        logger.info("SUCCESS: All contract links verified.")
        sys.exit(0)
    else:
        logger.error("FAILURE: One or more contract links are broken or missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()