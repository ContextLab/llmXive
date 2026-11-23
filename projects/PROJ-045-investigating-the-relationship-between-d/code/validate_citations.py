import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import logging setup from utils as per API surface
from utils import setup_logging

def load_citations(input_path: str) -> List[Dict[str, Any]]:
    """Load citations from a JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Citations file not found: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'citations' not in data:
        raise ValueError("Citations file must contain a 'citations' key with a list of citations.")
    
    return data['citations']

def load_cache(cache_path: str) -> Dict[str, Any]:
    """Load the local citation cache if it exists."""
    path = Path(cache_path)
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_cache(cache: Dict[str, Any], cache_path: str) -> None:
    """Save the citation cache to a file."""
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

def fetch_crossref_metadata(citation: Dict[str, Any], timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a citation from the Crossref API.
    Returns the metadata dict if successful, None otherwise.
    """
    import urllib.request
    import urllib.error
    import urllib.parse

    # Construct query based on available fields
    query_parts = []
    if citation.get('title'):
        query_parts.append(f"title={urllib.parse.quote(citation['title'])}")
    if citation.get('author'):
        query_parts.append(f"author={urllib.parse.quote(citation['author'])}")
    if citation.get('year'):
        query_parts.append(f"from-pub-date={citation['year']}-01-01&to-pub-date={citation['year']}-12-31")
    
    if not query_parts:
        logging.warning(f"No searchable fields for citation: {citation.get('id', 'unknown')}")
        return None

    query_string = "&".join(query_parts)
    url = f"https://api.crossref.org/works?filter={query_string}&rows=1"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if data.get('status') == 'ok' and data.get('message', {}).get('items'):
            return data['message']['items'][0]
        return None
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
        logging.warning(f"Failed to fetch metadata for {citation.get('id', 'unknown')}: {e}")
        return None

def verify_citation(citation: Dict[str, Any], cache: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """
    Verify a single citation against primary sources (Crossref).
    Returns a status dict with verification result.
    """
    citation_id = citation.get('id', 'unknown')
    
    # Check cache first
    if citation_id in cache:
        logging.info(f"Using cached verification for {citation_id}")
        cached_entry = cache[citation_id]
        # If cache entry says verified, return it. If not, we might retry, 
        # but for this task we assume cache is authoritative if present.
        if cached_entry.get('verified', False):
            return cached_entry

    logging.info(f"Verifying citation {citation_id}: {citation.get('title', 'Untitled')}")
    
    metadata = fetch_crossref_metadata(citation, timeout)
    
    result = {
        'id': citation_id,
        'title': citation.get('title', ''),
        'author': citation.get('author', ''),
        'year': citation.get('year'),
        'source_url': citation.get('url', ''),
        'verified': False,
        'verification_status': 'failed',
        'matched_title': None,
        'matched_author': None,
        'matched_doi': None,
        'error': None
    }

    if metadata:
        # Basic heuristic: if title or author matches reasonably well
        # Crossref returns 'title' as a list, usually single item
        crossref_title = metadata.get('title', [''])[0]
        crossref_author = metadata.get('author', [{}])[0].get('family', '')
        crossref_doi = metadata.get('DOI')
        
        # Simple string matching (case-insensitive)
        title_match = citation.get('title', '').lower() in crossref_title.lower()
        author_match = citation.get('author', '').lower() in crossref_author.lower()
        
        if title_match or (citation.get('year') and str(citation['year']) in str(metadata.get('published-print', {}).get('date-parts', [[0]])[0])):
            result['verified'] = True
            result['verification_status'] = 'verified'
            result['matched_title'] = crossref_title
            result['matched_author'] = crossref_author
            result['matched_doi'] = crossref_doi
            logging.info(f"Verified {citation_id} via Crossref (DOI: {crossref_doi})")
        else:
            result['verification_status'] = 'mismatch'
            result['matched_title'] = crossref_title
            result['matched_author'] = crossref_author
            logging.warning(f"Metadata fetched for {citation_id} but title/author mismatch.")
    else:
        result['error'] = "Could not fetch metadata from Crossref"
        logging.warning(f"Verification failed for {citation_id}: No metadata found")

    return result

def run_verification(citations: List[Dict[str, Any]], cache: Dict[str, Any], timeout: int = 10) -> List[Dict[str, Any]]:
    """Run verification for all citations."""
    results = []
    for citation in citations:
        # Rate limiting
        time.sleep(0.5) 
        status = verify_citation(citation, cache, timeout)
        results.append(status)
        # Update cache
        cache[citation.get('id', 'unknown')] = status
    return results

def save_report(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save the verification report to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_citations': len(results),
        'verified_count': sum(1 for r in results if r['verified']),
        'failed_count': sum(1 for r in results if not r['verified']),
        'citations': results
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Verification report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Verify citations against Crossref.')
    parser.add_argument('--input', required=True, help='Path to input citations JSON file')
    parser.add_argument('--output', required=True, help='Path to output verification status JSON file')
    parser.add_argument('--cache', default='data/raw/citations_cache.json', help='Path to local cache file')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout for API requests in seconds')
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = Path(args.output).parent / 'validation.log'
    setup_logging(log_file=str(log_file), level=logging.INFO)
    
    logging.info(f"Starting citation verification. Input: {args.input}, Output: {args.output}")
    
    try:
        # Load citations
        citations = load_citations(args.input)
        logging.info(f"Loaded {len(citations)} citations.")
        
        # Load or initialize cache
        cache = load_cache(args.cache)
        
        # Run verification
        results = run_verification(citations, cache, args.timeout)
        
        # Save cache
        save_cache(cache, args.cache)
        
        # Save report
        save_report(results, args.output)
        
        logging.info("Verification completed successfully.")
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
