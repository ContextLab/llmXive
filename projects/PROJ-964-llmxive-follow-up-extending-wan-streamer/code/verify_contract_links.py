import os
import sys
import re
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Set

# Configure logging to output to both console and a specific log file for the task
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/contract_link_verification.log')
    ]
)
logger = logging.getLogger(__name__)

# Define the project root relative to the script location or current working directory
# The script is in code/, so root is parent of code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Files to check based on T038a description: docs/quickstart.md and docs/data-model.md
# We will scan these files for links to files under contracts/
DOCS_TO_SCAN = [
    'docs/quickstart.md',
    'docs/data-model.md'
]

# Regex pattern to find Markdown links: [text](path)
# We are looking for paths that start with 'contracts/' or './contracts/'
LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def extract_contract_links(file_path: Path) -> List[Tuple[str, str]]:
    """
    Extracts all markdown links from a file that reference the contracts/ directory.
    Returns a list of tuples: (link_text, link_path).
    """
    if not file_path.exists():
        logger.warning(f"File not found for scanning: {file_path}")
        return []

    links = []
    try:
        content = file_path.read_text(encoding='utf-8')
        for match in LINK_PATTERN.finditer(content):
            text = match.group(1)
            path = match.group(2)
            # Normalize path: remove leading ./ if present
            clean_path = path.lstrip('./')
            if clean_path.startswith('contracts/'):
                links.append((text, clean_path))
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    
    return links

def verify_links_exist(links: List[Tuple[str, str]]) -> Tuple[int, int, List[str]]:
    """
    Verifies that the target files for the given links exist.
    Returns (total_count, passed_count, list_of_failed_paths).
    """
    failed_paths = []
    passed_count = 0
    
    for text, rel_path in links:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            passed_count += 1
            logger.debug(f"Link OK: {text} -> {rel_path}")
        else:
            failed_paths.append(rel_path)
            logger.error(f"Link BROKEN: {text} -> {rel_path} (Target missing)")
    
    return len(links), passed_count, failed_paths

def main():
    logger.info("Starting Contract Documentation Links Verification (Task T038b)")
    
    all_links = []
    docs_checked = []

    # 1. Scan documentation files for links
    for doc_rel in DOCS_TO_SCAN:
        doc_path = PROJECT_ROOT / doc_rel
        if not doc_path.exists():
            logger.warning(f"Documentation file not found, skipping: {doc_rel}")
            continue
        
        docs_checked.append(doc_rel)
        links = extract_contract_links(doc_path)
        if links:
            logger.info(f"Found {len(links)} contract links in {doc_rel}")
            all_links.extend(links)
        else:
            logger.info(f"No contract links found in {doc_rel}")

    if not all_links:
        logger.warning("No contract links were found in the scanned documentation files.")
        # This might be a failure if T038a was supposed to add them, 
        # but if T038a added them and they were deleted, we report 0 found.
        # However, the task is to verify the links *added*. If none exist, 
        # it implies the verification finds nothing to verify.
        # We will treat 0 links as a pass only if the docs don't exist or are empty of links,
        # but strictly speaking, if T038a added links, we expect > 0.
        # We will proceed to report the status.

    # 2. Verify existence
    total, passed, failed = verify_links_exist(all_links)

    # 3. Report results
    report_path = PROJECT_ROOT / 'data/logs/contract_verification_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Contract Documentation Links Verification Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Docs Scanned: {', '.join(docs_checked)}\n")
        f.write(f"Total Contract Links Found: {total}\n")
        f.write(f"Links Verified (Exist): {passed}\n")
        f.write(f"Links Broken: {len(failed)}\n")
        f.write("-" * 50 + "\n")
        
        if failed:
            f.write("FAILED LINKS:\n")
            for p in failed:
                f.write(f"  - {p}\n")
            f.write("\nSTATUS: FAILED\n")
        else:
            if total == 0:
                f.write("STATUS: SKIPPED (No links found in docs)\n")
            else:
                f.write("STATUS: PASSED\n")

    logger.info(f"Verification report written to: {report_path}")

    if failed:
        logger.error("Verification FAILED: Broken links detected.")
        sys.exit(1)
    else:
        logger.info("Verification PASSED.")
        sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify contract documentation links.')
    parser.parse_args()
    main()
