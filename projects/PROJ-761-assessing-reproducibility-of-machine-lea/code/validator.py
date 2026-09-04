import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Configure logging
def setup_logging(log_file: str = "artifacts/logs/verification.log") -> logging.Logger:
    """Setup logging to file and console."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("ReferenceValidator")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def load_research_file(file_path: str) -> str:
    """Load the research.md file content."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Research file not found: {file_path}")
    return path.read_text(encoding='utf-8')

def extract_verified_datasets(content: str) -> Set[str]:
    """
    Extract the 'Verified Datasets' block from the research file.
    Looks for a section marked 'Verified Datasets' or similar, and extracts
    dataset identifiers (DOIs, URLs, or dataset names).
    """
    verified = set()
    # Pattern to find the block
    # Expecting a section like:
    # ## Verified Datasets
    # - dataset_name_or_doi: url
    # or a list of URLs/DOIs
    
    # Try to find the block starting with "Verified Datasets"
    match = re.search(r'##\s*Verified\s+Datasets\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if match:
        block = match.group(1)
        # Extract URLs and DOIs
        # URLs
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', block)
        verified.update(urls)
        
        # DOIs
        dois = re.findall(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', block, re.IGNORECASE)
        verified.update(dois)
        
        # Dataset names (simple heuristic: lines starting with - or *)
        lines = block.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*')):
                item = line.lstrip('-*').strip()
                # Remove URL part if present
                item = re.sub(r'\s*https?://[^\s]+', '', item).strip()
                # Remove DOI if present
                item = re.sub(r'\s*10\.\d{4,9}/[-._;()/:A-Z0-9]+', '', item, flags=re.IGNORECASE).strip()
                if item and not item.startswith('#'):
                    verified.add(item)
    else:
        # Fallback: try to find any list of URLs/DOIs in the document
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
        verified.update(urls)
        dois = re.findall(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', content, re.IGNORECASE)
        verified.update(dois)
    
    return verified

def extract_citations(content: str) -> List[Dict[str, Any]]:
    """
    Extract citations from the research file.
    Looks for patterns like:
    - [1] Author, Title, Journal, Year
    - DOI: 10.xxxx/xxxx
    - URL: https://...
    """
    citations = []
    
    # Pattern for numbered citations [1], [2], etc.
    # We look for lines that look like citations
    lines = content.split('\n')
    current_ref = None
    
    for line in lines:
        # Check for DOI
        doi_match = re.search(r'DOI:\s*(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', line, re.IGNORECASE)
        if doi_match:
            citations.append({
                'type': 'doi',
                'value': doi_match.group(1),
                'raw': line.strip()
            })
            continue
        
        # Check for URL
        url_match = re.search(r'URL:\s*(https?://[^\s<>"{}|\\^`\[\]]+)', line, re.IGNORECASE)
        if url_match:
            citations.append({
                'type': 'url',
                'value': url_match.group(1),
                'raw': line.strip()
            })
            continue
        
        # Check for inline DOI/URL
        inline_doi = re.findall(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', line, re.IGNORECASE)
        for doi in inline_doi:
            if doi not in [c['value'] for c in citations if c['type'] == 'doi']:
                citations.append({
                    'type': 'doi',
                    'value': doi,
                    'raw': line.strip()
                })
        
        inline_url = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', line)
        for url in inline_url:
            if url not in [c['value'] for c in citations if c['type'] == 'url']:
                citations.append({
                    'type': 'url',
                    'value': url,
                    'raw': line.strip()
                })
    
    return citations

def validate_citation(citation: Dict[str, Any], verified_datasets: Set[str]) -> Tuple[bool, str]:
    """
    Validate a single citation against the verified datasets.
    Returns (is_valid, message)
    """
    citation_type = citation['type']
    citation_value = citation['value']
    
    # Check if the citation value matches any verified dataset
    # We do a substring match or exact match
    for verified in verified_datasets:
        if verified.lower() in citation_value.lower() or citation_value.lower() in verified.lower():
            return True, f"Matched verified dataset: {verified}"
    
    # If no direct match, check if it's a known pattern that should be verified
    if citation_type == 'doi':
        return False, f"DOI {citation_value} not found in verified datasets"
    elif citation_type == 'url':
        return False, f"URL {citation_value} not found in verified datasets"
    
    return False, f"Citation not verified"

def run_validation(research_file: str = "research.md") -> Dict[str, Any]:
    """
    Run the full validation process.
    Returns a summary of the validation results.
    """
    logger = setup_logging()
    logger.info("Starting Reference Validation")
    
    results = {
        'total_citations': 0,
        'validated': 0,
        'failed': 0,
        'details': []
    }
    
    try:
        # Load research file
        content = load_research_file(research_file)
        logger.info(f"Loaded research file: {research_file}")
        
        # Extract verified datasets
        verified_datasets = extract_verified_datasets(content)
        logger.info(f"Found {len(verified_datasets)} verified datasets")
        
        if not verified_datasets:
            logger.warning("No verified datasets found in the research file. Validation cannot proceed.")
            results['error'] = "No verified datasets found"
            return results
        
        # Extract citations
        citations = extract_citations(content)
        results['total_citations'] = len(citations)
        logger.info(f"Found {len(citations)} citations to validate")
        
        if not citations:
            logger.warning("No citations found in the research file.")
            results['error'] = "No citations found"
            return results
        
        # Validate each citation
        for citation in citations:
            is_valid, message = validate_citation(citation, verified_datasets)
            citation_result = {
                'citation': citation['raw'],
                'type': citation['type'],
                'value': citation['value'],
                'is_valid': is_valid,
                'message': message
            }
            results['details'].append(citation_result)
            
            if is_valid:
                results['validated'] += 1
                logger.info(f"Validated: {citation['type']} - {citation['value']}")
            else:
                results['failed'] += 1
                logger.error(f"Validation failed: {citation['type']} - {citation['value']} - {message}")
        
        # Log summary
        logger.info(f"Validation complete: {results['validated']}/{results['total_citations']} validated")
        
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        results['error'] = str(e)
    
    return results

def main():
    """Main entry point for the validator."""
    logger = setup_logging()
    logger.info("ReferenceValidator - Constitution Check II")
    
    # Default research file path
    research_file = "research.md"
    
    # Check if research.md exists
    if not Path(research_file).exists():
        logger.error(f"Research file not found: {research_file}")
        sys.exit(1)
    
    # Run validation
    results = run_validation(research_file)
    
    # Write results to log (already logged during run)
    log_path = Path("artifacts/logs/verification.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write("\n--- Validation Summary ---\n")
        f.write(f"Total Citations: {results['total_citations']}\n")
        f.write(f"Validated: {results['validated']}\n")
        f.write(f"Failed: {results['failed']}\n")
        if 'error' in results:
            f.write(f"Error: {results['error']}\n")
        f.write("--------------------------\n\n")
    
    # Exit with error if any validation failed
    if results['failed'] > 0:
        logger.error(f"Validation failed for {results['failed']} citations. Halting execution.")
        sys.exit(1)
    
    logger.info("All citations validated successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
