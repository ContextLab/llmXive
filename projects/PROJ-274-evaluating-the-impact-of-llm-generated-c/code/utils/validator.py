"""
Reference Validator Agent for validating citations in research documents.
Validates references by fetching metadata via DOI/URL and comparing titles using Jaccard similarity.
"""
import json
import os
import sys
import hashlib
import logging
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import requests, but fail loudly if not available
try:
    import requests
except ImportError:
    logger.error("The 'requests' library is required but not installed.")
    sys.exit(1)


def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a title into a set of lowercase words.
    Removes punctuation and splits on whitespace.
    """
    if not title:
        return []
    # Convert to lowercase and remove non-alphanumeric characters
    title = title.lower()
    tokens = re.findall(r'\b[a-z0-9]+\b', title)
    return tokens


def calculate_jaccard_similarity(tokens1: List[str], tokens2: List[str]) -> float:
    """
    Calculate Jaccard similarity between two sets of tokens.
    Jaccard = |A ∩ B| / |A ∪ B|
    """
    if not tokens1 or not tokens2:
        return 0.0
    
    set1 = set(tokens1)
    set2 = set(tokens2)
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def fetch_citation_metadata(identifier: str, identifier_type: str) -> Optional[Dict]:
    """
    Fetch metadata for a citation using DOI or URL.
    
    Args:
        identifier: The DOI or URL of the citation
        identifier_type: Either 'doi' or 'url'
        
    Returns:
        Dictionary containing metadata (title, authors, etc.) or None if fetch fails
    """
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'llmXive-ReferenceValidator/1.0'
    }
    
    try:
        if identifier_type == 'doi':
            # Use Crossref API for DOI resolution
            url = f"https://api.crossref.org/works/{identifier}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch DOI {identifier}: HTTP {response.status_code}")
                return None
            
            data = response.json()
            if 'message' not in data:
                logger.warning(f"Invalid response format for DOI {identifier}")
                return None
            
            message = data['message']
            title = message.get('title', [None])[0] if isinstance(message.get('title'), list) else message.get('title')
            
            if not title:
                logger.warning(f"No title found for DOI {identifier}")
                return None
            
            return {
                'title': title,
                'source': 'crossref',
                'identifier': identifier
            }
            
        elif identifier_type == 'url':
            # For URLs, we'll try to get metadata from the page or use a fallback
            # This is a simplified approach - in production, we'd use OpenURL or similar
            logger.info(f"URL validation not fully implemented for: {identifier}")
            return None
            
        else:
            logger.warning(f"Unknown identifier type: {identifier_type}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Network error fetching {identifier_type} {identifier}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {identifier_type} {identifier}: {e}")
        return None


def validate_reference(reference: Dict, threshold: float = 0.7) -> Dict:
    """
    Validate a single reference by fetching its metadata and comparing titles.
    
    Args:
        reference: Dictionary containing reference information
        threshold: Minimum Jaccard similarity threshold (default 0.7)
        
    Returns:
        Validation result dictionary
    """
    identifier = reference.get('id') or reference.get('doi') or reference.get('url')
    identifier_type = reference.get('type', 'doi')
    expected_title = reference.get('title', '')
    
    if not identifier:
        return {
            'id': identifier,
            'status': 'invalid',
            'reason': 'No identifier found',
            'similarity': 0.0
        }
    
    # Fetch metadata
    metadata = fetch_citation_metadata(identifier, identifier_type)
    
    if not metadata:
        return {
            'id': identifier,
            'status': 'invalid',
            'reason': 'Failed to fetch metadata',
            'similarity': 0.0
        }
    
    fetched_title = metadata.get('title', '')
    
    # Tokenize and compare
    expected_tokens = tokenize_title(expected_title)
    fetched_tokens = tokenize_title(fetched_title)
    
    similarity = calculate_jaccard_similarity(expected_tokens, fetched_tokens)
    
    status = 'valid' if similarity >= threshold else 'invalid'
    reason = f"Jaccard similarity {similarity:.3f} {'>= ' if similarity >= threshold else '< '}{threshold}"
    
    return {
        'id': identifier,
        'status': status,
        'reason': reason,
        'similarity': similarity,
        'expected_title': expected_title,
        'fetched_title': fetched_title
    }


def validate_citation(citation: Dict, threshold: float = 0.7) -> Dict:
    """
    Validate a citation entry from citations.yaml.
    
    Args:
        citation: Dictionary containing citation information
        threshold: Minimum Jaccard similarity threshold
        
    Returns:
        Validation result dictionary
    """
    return validate_reference(citation, threshold)


def validate_document_references(citations_path: str, research_path: str, output_path: str, threshold: float = 0.7) -> bool:
    """
    Validate all references in a document against their sources.
    
    Args:
        citations_path: Path to state/citations.yaml
        research_path: Path to the research document (for context)
        output_path: Path to write validation_log.json
        threshold: Minimum Jaccard similarity threshold
        
    Returns:
        True if all references are valid, False otherwise
    """
    # Load citations
    if not os.path.exists(citations_path):
        logger.error(f"Citations file not found: {citations_path}")
        return False
    
    try:
        with open(citations_path, 'r') as f:
            import yaml
            citations = yaml.safe_load(f)
            if not isinstance(citations, list):
                citations = [citations]
    except Exception as e:
        logger.error(f"Failed to load citations: {e}")
        return False
    
    if not citations:
        logger.warning("No citations found in citations.yaml")
        return True
    
    # Validate each citation
    results = []
    all_valid = True
    
    for citation in citations:
        result = validate_citation(citation, threshold)
        results.append(result)
        if result['status'] != 'valid':
            all_valid = False
            logger.warning(f"Citation {result['id']} is invalid: {result['reason']}")
        else:
            logger.info(f"Citation {result['id']} is valid (similarity: {result['similarity']:.3f})")
    
    # Prepare output
    output_data = {
        'research_document': research_path,
        'citations_file': citations_path,
        'threshold': threshold,
        'all_valid': all_valid,
        'total_citations': len(citations),
        'valid_count': sum(1 for r in results if r['status'] == 'valid'),
        'invalid_count': sum(1 for r in results if r['status'] != 'valid'),
        'results': results
    }
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Validation complete. Results written to {output_path}")
    logger.info(f"Overall status: {'ALL VALID' if all_valid else 'SOME INVALID'}")
    
    return all_valid


def main():
    """Main entry point for the Reference Validator Agent."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    citations_path = project_root / "state" / "citations.yaml"
    research_path = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c" / "research.md"
    output_path = project_root / "state" / "validation_log.json"
    lock_path = project_root / "state" / "research_validated.lock"
    
    logger.info("Starting Reference Validator Agent")
    logger.info(f"Citations path: {citations_path}")
    logger.info(f"Research path: {research_path}")
    logger.info(f"Output path: {output_path}")
    
    # Check if citations file exists
    if not citations_path.exists():
        logger.error(f"Citations file not found: {citations_path}")
        logger.error("Please run T070a first to generate state/citations.yaml")
        sys.exit(1)
    
    # Validate references
    all_valid = validate_document_references(
        str(citations_path),
        str(research_path),
        str(output_path),
        threshold=0.7
    )
    
    # Create lock file if all valid
    if all_valid:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, 'w') as f:
            f.write(f"Research validated at {os.popen('date -Iseconds').read().strip()}\n")
            f.write(f"Validation log: {output_path}\n")
        logger.info(f"Lock file created: {lock_path}")
        logger.info("✅ T071b PASSED: All references validated successfully")
    else:
        logger.error("❌ T071b FAILED: Some references could not be validated")
        logger.error("Pipeline cannot proceed to Phase 1 until this gate passes")
        # Do not create lock file
        sys.exit(1)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
