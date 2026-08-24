import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils import setup_logging

# Attempt to import requests; if not available, use urllib as fallback
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error

def load_citations(input_path: str) -> List[Dict[str, Any]]:
    """Load citations from a JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Citations file not found: {input_path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('citations', [])

def load_cache(cache_path: str) -> Dict[str, Any]:
    """Load the local citation cache if it exists."""
    path = Path(cache_path)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache_path: str, cache_data: Dict[str, Any]) -> None:
    """Save the local citation cache."""
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)

def fetch_crossref_metadata(doi: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Fetch metadata from Crossref API for a given DOI."""
    url = f"https://api.crossref.org/works/{doi}"
    try:
        if HAS_REQUESTS:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        else:
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        logging.warning(f"Failed to fetch Crossref metadata for DOI {doi}: {e}")
        return None

def verify_citation(citation: Dict[str, Any], cache: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a single citation against Crossref.
    Returns a status object with verification result.
    """
    citation_id = citation.get('id', 'unknown')
    title = citation.get('title', '')
    url = citation.get('url', '')
    doi = citation.get('doi', '')

    status = {
        'id': citation_id,
        'title': title,
        'verified': False,
        'source': None,
        'error': None
    }

    # Check cache first
    if citation_id in cache:
        cached = cache[citation_id]
        if cached.get('verified'):
            status['verified'] = True
            status['source'] = cached.get('source')
            return status

    # If DOI is present, try Crossref
    if doi:
        meta = fetch_crossref_metadata(doi)
        if meta and 'message' in meta:
            msg = meta['message']
            # Basic validation: check if title matches roughly
            crossref_title = msg.get('title', [''])[0]
            if title.lower() in crossref_title.lower() or crossref_title.lower() in title.lower():
                status['verified'] = True
                status['source'] = f"Crossref (DOI: {doi})"
                # Update cache
                cache[citation_id] = {
                    'verified': True,
                    'source': status['source'],
                    'timestamp': time.time()
                }
                return status
            else:
                status['error'] = f"Title mismatch: '{title}' vs '{crossref_title}'"
        else:
            status['error'] = "Crossref returned no valid message"
    else:
        # If no DOI, try to verify via URL if it's a known publisher
        if url:
            # Heuristic: check if URL contains known publisher keywords
            known_publishers = ['nature.com', 'science.org', 'aps.org', 'rsc.org', 'wiley.com']
            if any(pub in url for pub in known_publishers):
                status['verified'] = True
                status['source'] = f"URL heuristic ({url})"
                cache[citation_id] = {
                    'verified': True,
                    'source': status['source'],
                    'timestamp': time.time()
                }
                return status
            else:
                status['error'] = "No DOI and URL not from known publisher"
        else:
            status['error'] = "No DOI or URL provided"

    # If we reach here, verification failed
    cache[citation_id] = {
        'verified': False,
        'source': None,
        'error': status['error'],
        'timestamp': time.time()
    }
    return status

def run_verification(citations: List[Dict[str, Any]], cache_path: str, timeout: int = 30) -> List[Dict[str, Any]]:
    """Run verification for all citations."""
    cache = load_cache(cache_path)
    results = []
    
    for i, citation in enumerate(citations):
        logging.info(f"Verifying citation {i+1}/{len(citations)}: {citation.get('title', 'Unknown')}")
        result = verify_citation(citation, cache)
        results.append(result)
        # Save cache incrementally to avoid data loss on interruption
        save_cache(cache_path, cache)
        
        # Respect timeout roughly
        if i > 0 and i % 5 == 0:
            time.sleep(0.5) # Small backoff

    return results

def save_report(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save the verification report to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'verification_results': results}, f, indent=2)
    logging.info(f"Verification report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Verify citations against primary sources.')
    parser.add_argument('--input', required=True, help='Path to input citations JSON file')
    parser.add_argument('--output', required=True, help='Path to output verification report JSON file')
    parser.add_argument('--cache', default='data/raw/citations_cache.json', help='Path to local cache file')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout for API calls')
    
    args = parser.parse_args()

    setup_logging()
    
    try:
        citations = load_citations(args.input)
        if not citations:
            logging.warning("No citations found in input file.")
            save_report([], args.output)
            return

        logging.info(f"Loaded {len(citations)} citations from {args.input}")
        
        results = run_verification(citations, args.cache, args.timeout)
        
        save_report(results, args.output)
        
        # Log summary
        verified_count = sum(1 for r in results if r['verified'])
        logging.info(f"Verification complete. {verified_count}/{len(results)} citations verified.")
        
    except FileNotFoundError as e:
        logging.error(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()