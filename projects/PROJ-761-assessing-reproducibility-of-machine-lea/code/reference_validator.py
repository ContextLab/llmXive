"""
Reference Validator Agent for PROJ-761.

Verifies all citations and dataset URLs in `research.md` against the
"Verified Datasets" block.

This agent implements the "Constitution Check II" requirement.
It reads `research.md`, extracts all URLs and DOIs, and checks them
against the verified list in the "Verified Datasets" section.

If any citation fails validation, the task fails and execution halts.
"""
import re
import sys
import logging
from pathlib import Path
from typing import Set, List, Tuple, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
RESEARCH_MD_PATH = Path("research.md")
VERIFIED_DATASETS_MARKER = "VERIFIED REAL DATA SOURCE"
OUTPUT_LOG_PATH = Path("artifacts/logs/reference_validation.log")

def load_research_file() -> str:
    """Load the research.md file."""
    if not RESEARCH_MD_PATH.exists():
        raise FileNotFoundError(f"Research file not found: {RESEARCH_MD_PATH}")
    return RESEARCH_MD_PATH.read_text(encoding="utf-8")

def extract_urls_and_dois(text: str) -> Set[str]:
    """Extract all URLs and DOIs from the text."""
    # URL pattern
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = set(re.findall(url_pattern, text))
    
    # DOI pattern
    doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'
    dois = set(re.findall(doi_pattern, text, re.IGNORECASE))
    
    return urls.union(dois)

def extract_verified_datasets(text: str) -> Dict[str, Any]:
    """
    Extract the "Verified Datasets" block from the text.
    
    Looks for a section starting with 'VERIFIED REAL DATA SOURCE'
    and parses the content until the next section or end of file.
    """
    verified_block = {}
    lines = text.split('\n')
    in_block = False
    current_key = None
    
    for line in lines:
        if VERIFIED_DATASETS_MARKER in line:
            in_block = True
            continue
        
        if in_block:
            # Check for new section (e.g., ##, ###, or a line starting with non-space)
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                # Likely a new section header or non-block content
                if line.startswith('##') or line.startswith('#'):
                    break
            
            # Parse key-value or list items
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            if line_stripped.startswith('- '):
                # List item
                item = line_stripped[2:].strip()
                if ':' in item:
                    key, val = item.split(':', 1)
                    current_key = key.strip()
                    verified_block[current_key] = val.strip()
                else:
                    # Simple list item
                    if not current_key:
                        current_key = "items"
                    if current_key not in verified_block:
                        verified_block[current_key] = []
                    verified_block[current_key].append(item)
            elif ':' in line_stripped:
                # Key-value pair
                key, val = line_stripped.split(':', 1)
                current_key = key.strip()
                verified_block[current_key] = val.strip()
    
    return verified_block

def validate_citation(citation: str, verified_datasets: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single citation against the verified datasets.
    
    Returns (is_valid, message).
    """
    # Check if it's a DOI
    if citation.startswith('10.'):
        # Check if DOI is in verified list
        verified_dois = verified_datasets.get('dois', [])
        if isinstance(verified_dois, list):
            if citation in verified_dois:
                return True, "DOI verified"
        elif isinstance(verified_dois, str):
            if citation in verified_dois:
                return True, "DOI verified"
        
        # If not in verified list, check if it's a known valid DOI pattern
        # For now, if not explicitly verified, we mark as failed
        return False, f"DOI not found in verified datasets: {citation}"
    
    # Check if it's a URL
    if citation.startswith('http'):
        # Check if URL is in verified list
        verified_urls = verified_datasets.get('urls', [])
        if isinstance(verified_urls, list):
            if citation in verified_urls:
                return True, "URL verified"
        elif isinstance(verified_urls, str):
            if citation in verified_urls:
                return True, "URL verified"
        
        # Check for dataset package names (e.g., 'uspto', 'reaxys')
        dataset_names = verified_datasets.get('packages', [])
        if isinstance(dataset_names, list):
            for name in dataset_names:
                if name.lower() in citation.lower():
                    return True, f"URL contains verified dataset package: {name}"
        
        return False, f"URL not found in verified datasets: {citation}"
    
    return False, f"Unrecognized citation format: {citation}"

def run_validation() -> bool:
    """
    Run the full validation pipeline.
    
    Returns True if all citations are valid, False otherwise.
    """
    logger.info("Starting Reference Validator...")
    
    # Load research file
    try:
        research_text = load_research_file()
        logger.info(f"Loaded research file: {RESEARCH_MD_PATH}")
    except Exception as e:
        logger.error(f"Failed to load research file: {e}")
        return False
    
    # Extract verified datasets
    verified_datasets = extract_verified_datasets(research_text)
    if not verified_datasets:
        logger.warning("No 'Verified Datasets' block found in research.md. "
                     "Assuming all citations are unverified.")
        # If no verified block, we cannot validate, so we fail
        # This is a critical failure for the Constitution Check
        logger.error("CRITICAL: 'Verified Datasets' block is missing. "
                   "Cannot perform Constitution Check II.")
        return False
    
    logger.info(f"Found verified datasets: {list(verified_datasets.keys())}")
    
    # Extract all citations
    citations = extract_urls_and_dois(research_text)
    logger.info(f"Found {len(citations)} citations to validate.")
    
    if not citations:
        logger.warning("No citations found in research.md.")
        # No citations to validate, so we pass
        return True
    
    # Validate each citation
    failed_citations = []
    passed_citations = []
    
    for citation in sorted(citations):
        is_valid, message = validate_citation(citation, verified_datasets)
        if is_valid:
            passed_citations.append((citation, message))
            logger.info(f"✓ Validated: {citation} - {message}")
        else:
            failed_citations.append((citation, message))
            logger.error(f"✗ Failed validation: {citation} - {message}")
    
    # Write validation log
    OUTPUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_LOG_PATH, 'w', encoding='utf-8') as f:
        f.write("Reference Validation Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total citations found: {len(citations)}\n")
        f.write(f"Passed: {len(passed_citations)}\n")
        f.write(f"Failed: {len(failed_citations)}\n")
        f.write("\n")
        
        if passed_citations:
            f.write("PASSED CITATIONS:\n")
            f.write("-" * 30 + "\n")
            for citation, msg in passed_citations:
                f.write(f"  ✓ {citation} - {msg}\n")
            f.write("\n")
        
        if failed_citations:
            f.write("FAILED CITATIONS:\n")
            f.write("-" * 30 + "\n")
            for citation, msg in failed_citations:
                f.write(f"  ✗ {citation} - {msg}\n")
            f.write("\n")
        
        f.write("=" * 50 + "\n")
        if failed_citations:
            f.write("RESULT: VALIDATION FAILED\n")
            f.write("The Constitution Check II has failed. "
                   "Execution must halt until all citations are verified.\n")
        else:
            f.write("RESULT: VALIDATION PASSED\n")
            f.write("All citations are verified against the 'Verified Datasets' block.\n")
    
    logger.info(f"Validation report written to: {OUTPUT_LOG_PATH}")
    
    # Return success only if all citations passed
    return len(failed_citations) == 0

def main():
    """Main entry point."""
    success = run_validation()
    if not success:
        logger.error("Reference validation failed. Halting execution.")
        sys.exit(1)
    else:
        logger.info("Reference validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
