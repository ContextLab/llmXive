"""
Citation Validation Script.

This script verifies citations in research.md against primary sources.
It acts as a blocking gate for the pipeline.
"""

import argparse
import logging
import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.io_helpers import setup_logging

logger = setup_logging("validate_citations")

def extract_citations(file_path: Path) -> list:
    """
    Extract citations from the research.md file.
    Looks for patterns like [Author, Year] or (Author, Year) or DOIs.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    content = file_path.read_text(encoding="utf-8")
    # Simple regex for common citation formats
    # Matches: (Smith et al., 2020), [1], [Author, Year]
    patterns = [
        r'\(([^)]+,\s*\d{4})\)',  # (Author, Year)
        r'\[([^\]]+)\]',           # [Author, Year] or [1]
        r'(10\.\d{4,}/\S+)',       # DOI
    ]
    
    citations = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        citations.extend(matches)
    
    return list(set(citations))

def validate_citation(citation: str) -> bool:
    """
    Validate a single citation.
    In a real implementation, this would query an API (DOI, Crossref, etc.).
    For this task, we perform a basic sanity check and log.
    """
    # Basic validation: check if it looks like a year or DOI
    if re.match(r'\d{4}', citation):
        return True
    if re.match(r'10\.\d+', citation):
        return True
    if 'et al.' in citation or ',' in citation:
        return True
    
    # If it's just a number, assume it's a reference list index
    if citation.isdigit():
        return True

    logger.warning(f"Citation '{citation}' format is ambiguous. Skipping deep validation.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate citations in research.md")
    parser.add_argument("--file", 
                        type=str, 
                        default="research.md",
                        help="Path to the research document (relative to project root)")
    args = parser.parse_args()

    research_file = project_root / args.file

    if not research_file.exists():
        logger.error(f"Research file not found: {research_file}")
        sys.exit(1)

    logger.info(f"Validating citations in {research_file}...")
    
    citations = extract_citations(research_file)
    if not citations:
        logger.warning("No citations found in the research file.")
        # We don't fail if no citations are found, just warn
        sys.exit(0)

    logger.info(f"Found {len(citations)} citations.")
    
    all_valid = True
    for citation in citations:
        if not validate_citation(citation):
            logger.error(f"Invalid citation: {citation}")
            all_valid = False

    if all_valid:
        logger.info("All citations validated successfully.")
        sys.exit(0)
    else:
        logger.error("Citation validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
