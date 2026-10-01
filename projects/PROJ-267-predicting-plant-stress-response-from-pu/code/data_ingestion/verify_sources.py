"""
verify_sources.py

Implements the "Verified Accuracy Gate" for the plant stress response pipeline.
Fetches metadata for all citations in research.md and verifies title-token overlap
against a configured threshold.
"""

import os
import re
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import shared config and logging utilities
# Note: config.py is expected to exist per T004 (though T004 is marked incomplete in feedback,
# we must implement this task assuming the standard project structure).
# We will attempt to import config, and if it fails, we will define a minimal fallback
# to ensure this script can run and report the failure of the gate.
try:
    from utils.config import REFERENCE_VALIDATOR_THRESHOLD, LOG_PATH, LOG_LEVEL
except ImportError:
    # Fallback defaults if config.py is not yet available
    REFERENCE_VALIDATOR_THRESHOLD = 0.7
    LOG_PATH = Path("logs/pipeline.log")
    LOG_LEVEL = logging.INFO

from utils.logging_config import setup_logging, get_logger, log_warning

# Constants
RESEARCH_MD_PATH = Path("research.md")
VALIDATION_REPORT_PATH = Path("results/verification_report.json")
GATE_FAILURE_MESSAGE = "Verified Accuracy Gate Failure"

# Setup logging
setup_logging(level=LOG_LEVEL, log_path=LOG_PATH)
logger = get_logger(__name__)


def parse_citations(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses research.md to extract citation blocks.
    Expects a format like:
    [1] Title: "..." URL: "..." or similar structured text.
    Returns a list of dicts with 'id', 'title', 'url', 'doi' (if present).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Research file not found: {file_path}")

    citations = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to capture citation blocks.
    # Assumes a pattern like: [ID] ... Title: ... URL: ...
    # This is a heuristic; adjust based on actual research.md format if needed.
    # Pattern looks for lines starting with [X] or similar markers.
    citation_pattern = re.compile(
        r'\[(\d+)\]\s*(?P<text>.*?)(?=\n\[\d+\]|\Z)',
        re.DOTALL | re.IGNORECASE
    )

    matches = citation_pattern.findall(content)

    for match_id, text in matches:
        # Extract title
        title_match = re.search(r'Title:\s*["\']?(.*?)["\']?', text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "Unknown Title"

        # Extract URL
        url_match = re.search(r'URL:\s*["\']?(.*?)["\']?', text, re.IGNORECASE)
        url = url_match.group(1).strip() if url_match else None

        # Extract DOI
        doi_match = re.search(r'DOI:\s*["\']?(.*?)["\']?', text, re.IGNORECASE)
        doi = doi_match.group(1).strip() if doi_match else None

        if title != "Unknown Title" or url or doi:
            citations.append({
                'id': match_id,
                'title': title,
                'url': url,
                'doi': doi
            })

    if not citations:
        logger.warning("No citations found in research.md. Gate may fail.")
    
    return citations


def fetch_doi_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """
    Fetches metadata from Crossref API for a given DOI.
    Returns title and authors if successful, None otherwise.
    """
    import requests
    if not doi:
        return None

    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            item = data.get('message', {}).get('items', [{}])[0]
            title = item.get('title', [None])[0]
            return {'title': title, 'source': 'crossref'}
        else:
            logger.warning(f"Crossref API returned {response.status_code} for DOI {doi}")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch DOI metadata for {doi}: {e}")
        return None


def fetch_url_metadata(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetches basic metadata from a URL (e.g., arXiv, NCBI).
    For arXiv, tries to parse title from HTML or API.
    For others, returns a placeholder or attempts generic title extraction.
    """
    import requests
    from bs4 import BeautifulSoup
    
    if not url:
        return None

    try:
        # Handle arXiv specifically as it's common in research
        if 'arxiv.org' in url:
            # Try arXiv API
            api_url = url.replace('abs', 'json')
            if 'abs' not in api_url: # Fallback if abs wasn't in original
                api_url = url + '.json'
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                title = data.get('entry', {}).get('title', [None])[0]
                if title:
                    return {'title': title, 'source': 'arxiv'}
            # Fallback to scraping
        
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return {'title': title_tag.get_text().strip(), 'source': 'scraped'}
        
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch URL metadata for {url}: {e}")
        return None


def calculate_token_overlap(title1: str, title2: str) -> float:
    """
    Calculates the Jaccard similarity (token overlap) between two titles.
    """
    if not title1 or not title2:
        return 0.0

    # Normalize: lowercase, remove punctuation, split into tokens
    def tokenize(text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return set(text.split())

    tokens1 = tokenize(title1)
    tokens2 = tokenize(title2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)

    return len(intersection) / len(union) if union else 0.0


def verify_semantic_relevance(citation: Dict[str, Any], threshold: float) -> Tuple[bool, float, Optional[str]]:
    """
    Verifies if the fetched metadata matches the citation title sufficiently.
    Returns (is_valid, overlap_score, source_type).
    """
    citation_title = citation.get('title', '')
    fetched_title = None
    source_type = None

    # Try DOI first
    if citation.get('doi'):
        meta = fetch_doi_metadata(citation['doi'])
        if meta:
            fetched_title = meta['title']
            source_type = meta['source']

    # Try URL if DOI failed or no DOI
    if not fetched_title and citation.get('url'):
        meta = fetch_url_metadata(citation['url'])
        if meta:
            fetched_title = meta['title']
            source_type = meta['source']

    if not fetched_title:
        logger.warning(f"Could not fetch metadata for citation {citation['id']}")
        return False, 0.0, None

    overlap = calculate_token_overlap(citation_title, fetched_title)
    is_valid = overlap >= threshold

    return is_valid, overlap, source_type


def validate_citation(citation: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    """
    Validates a single citation.
    """
    is_valid, score, source = verify_semantic_relevance(citation, threshold)
    return {
        'id': citation['id'],
        'title': citation['title'],
        'verified': is_valid,
        'overlap_score': score,
        'source': source,
        'threshold': threshold
    }


def main():
    """
    Main entry point for the verification gate.
    1. Parse research.md.
    2. Validate each citation.
    3. If any fail, exit with 'Verified Accuracy Gate Failure'.
    4. Write report to results/verification_report.json.
    """
    logger.info("Starting Source Verification Gate (T035)...")

    # Ensure results directory exists
    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    citations = parse_citations(RESEARCH_MD_PATH)
    if not citations:
        logger.error("No citations found in research.md. Cannot proceed.")
        print(GATE_FAILURE_MESSAGE)
        sys.exit(1)

    logger.info(f"Found {len(citations)} citations to validate.")

    results = []
    all_passed = True

    for citation in citations:
        result = validate_citation(citation, REFERENCE_VALIDATOR_THRESHOLD)
        results.append(result)
        if not result['verified']:
            all_passed = False
            logger.error(f"Citation {result['id']} failed validation (Score: {result['overlap_score']:.2f} < {REFERENCE_VALIDATOR_THRESHOLD})")
        else:
            logger.info(f"Citation {result['id']} passed (Score: {result['overlap_score']:.2f})")

    # Write report
    report = {
        'timestamp': str(Path().absolute()), # Simple timestamp placeholder
        'total_citations': len(citations),
        'passed': all_passed,
        'threshold': REFERENCE_VALIDATOR_THRESHOLD,
        'details': results
    }

    with open(VALIDATION_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Verification report written to {VALIDATION_REPORT_PATH}")

    if not all_passed:
        logger.critical(GATE_FAILURE_MESSAGE)
        print(GATE_FAILURE_MESSAGE)
        sys.exit(1)
    
    logger.info("Source Verification Gate PASSED.")
    sys.exit(0)


if __name__ == '__main__':
    main()