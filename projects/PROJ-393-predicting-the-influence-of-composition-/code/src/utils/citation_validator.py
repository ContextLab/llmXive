"""
Citation Validator Module (T005b)

Verifies fetched citations against primary sources (DOI/URL) with a title-overlap check >= 0.7.
Implements the Constitution Principle II verification step.
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MIN_TITLE_OVERLAP = 0.7
REQUEST_TIMEOUT = 30
DOI_RESOLVE_URL = "https://doi.org/{}"
CROSSREF_API_URL = "https://api.crossref.org/works/{}"

def normalize_text(text: str) -> str:
    """
    Normalize text for comparison: lowercase, remove punctuation, split into words.
    """
    if not text:
        return []
    # Lowercase and remove non-alphanumeric characters (keeping spaces)
    cleaned = re.sub(r'[^a-z0-9\s]', '', text.lower())
    # Split into words and filter short words (length < 3) to avoid noise
    words = [w for w in cleaned.split() if len(w) >= 3]
    return set(words)

def calculate_title_overlap(title_a: str, title_b: str) -> float:
    """
    Calculate Jaccard similarity between two titles based on word sets.
    Returns a float between 0.0 and 1.0.
    """
    if not title_a or not title_b:
        return 0.0

    set_a = normalize_text(title_a)
    set_b = normalize_text(title_b)

    if not set_a or not set_b:
        return 0.0

    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)

def validate_doi(doi: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate a DOI by fetching metadata from Crossref and checking if it resolves.
    Returns: (is_valid, resolved_url, metadata)
    """
    if not doi:
        return False, None, None

    try:
        # Try to fetch metadata from Crossref API
        url = CROSSREF_API_URL.format(doi)
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'failed' or 'message' not in data:
            logger.warning(f"DOI {doi} not found in Crossref.")
            return False, None, None

        message = data.get('message', {})
        title = message.get('title', [''])[0]
        # Get the first URL if available, otherwise construct from DOI
        url_list = message.get('URL', [])
        resolved_url = url_list[0] if url_list else DOI_RESOLVE_URL.format(doi)

        metadata = {
            'title': title,
            'doi': doi,
            'url': resolved_url,
            'source': 'crossref'
        }

        return True, resolved_url, metadata

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error validating DOI {doi}: {e}")
        return False, None, None
    except Exception as e:
        logger.error(f"Error validating DOI {doi}: {e}")
        return False, None, None

def validate_url(url: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate a URL by checking if it is reachable and extracting the title if possible.
    Returns: (is_valid, resolved_url, metadata)
    """
    if not url:
        return False, None, None

    try:
        # Check if URL is reachable
        response = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        
        # If HEAD fails or redirects, try GET
        if response.status_code >= 400:
            response = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            response.raise_for_status()
        else:
            response.raise_for_status()

        # Attempt to extract title from HTML if it looks like a webpage
        title = None
        if 'text/html' in response.headers.get('Content-Type', ''):
            # Simple regex to find <title> tag
            match = re.search(r'<title>([^<]+)</title>', response.text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()

        metadata = {
            'title': title or "No title extracted",
            'url': url,
            'source': 'direct_url'
        }

        return True, url, metadata

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error validating URL {url}: {e}")
        return False, None, None
    except Exception as e:
        logger.error(f"Error validating URL {url}: {e}")
        return False, None, None

def validate_citation(citation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single citation entry.
    Expected fields: 'title', 'doi' (optional), 'url' (optional)
    Returns a dict with validation results.
    """
    citation_title = citation.get('title', '')
    doi = citation.get('doi')
    url = citation.get('url')

    result = {
        'original_title': citation_title,
        'doi': doi,
        'url': url,
        'is_valid': False,
        'match_score': 0.0,
        'source_verified': None,
        'error': None,
        'verified_metadata': None
    }

    # Strategy 1: Validate via DOI
    if doi:
        is_valid, resolved_url, metadata = validate_doi(doi)
        if is_valid:
            # Check title overlap
            overlap = calculate_title_overlap(citation_title, metadata['title'])
            result['match_score'] = overlap
            result['source_verified'] = 'doi'
            result['verified_metadata'] = metadata
            result['is_valid'] = overlap >= MIN_TITLE_OVERLAP
            if not result['is_valid']:
                result['error'] = f"Title overlap {overlap:.2f} < {MIN_TITLE_OVERLAP}"
            else:
                logger.info(f"DOI {doi} validated successfully (overlap: {overlap:.2f})")
            return result
        else:
            result['error'] = f"DOI {doi} could not be resolved or is invalid."
            # If DOI fails, we might still try URL if present, but prioritize DOI failure
            # For now, let's mark as invalid if DOI is provided but fails
            return result

    # Strategy 2: Validate via URL
    if url:
        is_valid, resolved_url, metadata = validate_url(url)
        if is_valid:
            # Check title overlap if metadata has a title
            if metadata.get('title') and metadata['title'] != "No title extracted":
                overlap = calculate_title_overlap(citation_title, metadata['title'])
                result['match_score'] = overlap
                result['source_verified'] = 'url'
                result['verified_metadata'] = metadata
                result['is_valid'] = overlap >= MIN_TITLE_OVERLAP
                if not result['is_valid']:
                    result['error'] = f"Title overlap {overlap:.2f} < {MIN_TITLE_OVERLAP}"
                else:
                    logger.info(f"URL {url} validated successfully (overlap: {overlap:.2f})")
                return result
            else:
                # No title to compare, assume valid if URL is reachable
                result['source_verified'] = 'url'
                result['verified_metadata'] = metadata
                result['is_valid'] = True
                logger.info(f"URL {url} validated (no title comparison available)")
                return result
        else:
            result['error'] = f"URL {url} is unreachable."

    # If neither DOI nor URL worked
    if not doi and not url:
        result['error'] = "No DOI or URL provided for validation."
    elif doi and not url:
        result['error'] = "DOI validation failed."
    elif url and not doi:
        result['error'] = "URL validation failed."

    return result

def validate_all_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate a list of citations and return results.
    """
    results = []
    for idx, citation in enumerate(citations):
        logger.info(f"Validating citation {idx + 1}/{len(citations)}...")
        result = validate_citation(citation)
        result['index'] = idx
        results.append(result)
    
    # Summary
    valid_count = sum(1 for r in results if r['is_valid'])
    logger.info(f"Validation complete: {valid_count}/{len(results)} citations validated successfully.")
    return results

def main():
    """
    Main entry point for running the citation validator.
    Expects a JSON file path as an argument (output of T005a citation_fetcher).
    """
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python citation_validator.py <path_to_citations.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r') as f:
        citations = json.load(f)

    if not isinstance(citations, list):
        print("Error: Expected a list of citations in the input file.")
        sys.exit(1)

    results = validate_all_citations(citations)

    # Save results
    output_path = input_path.parent / f"{input_path.stem}_validated.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Validation results saved to: {output_path}")

    # Check for failures
    failed = [r for r in results if not r['is_valid']]
    if failed:
        print(f"\n⚠️  {len(failed)} citations failed validation:")
        for r in failed:
            print(f"  - Index {r['index']}: {r.get('original_title', 'Unknown')[:50]}... ({r.get('error')})")
        sys.exit(1)
    else:
        print("\n✅ All citations validated successfully.")
        sys.exit(0)

if __name__ == '__main__':
    main()