"""
verify_sources.py

Validates that all citations in research.md are verified against primary sources.
- Fetches primary source metadata (DOI/URL).
- Verifies title-token overlap >= threshold (from config.py).
- Verifies semantic relevance (basic keyword check).
- Fails if any citation fails validation.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config, REFERENCE_VALIDATION_THRESHOLD, DATA_RAW_PATH
from utils.logging_config import get_logger, log_warning

logger = get_logger(__name__)

# Constants for citation parsing
DOI_REGEX = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)
URL_REGEX = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
CITATION_PATTERN = re.compile(r'\[(\d+)\]\s+(.*)', re.DOTALL)

def parse_citations(research_md_path: str) -> List[Dict[str, Any]]:
    """
    Parse research.md to extract citations (numbered list or bracketed references).
    Returns a list of dicts: {'id': int, 'raw_text': str, 'doi': str | None, 'url': str | None, 'title': str | None}
    """
    if not os.path.exists(research_md_path):
        raise FileNotFoundError(f"research.md not found at {research_md_path}")

    with open(research_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    citations = []
    # Simple heuristic: look for lines starting with [N] or lines containing DOIs/URLs that look like references
    # We assume research.md has a "References" section or similar structure.
    # For robustness, we look for lines that contain a DOI or a long URL and capture the surrounding text as the title/description.

    lines = content.split('\n')
    current_ref_id = 0
    in_references_section = False

    for line in lines:
        # Detect start of references section (heuristic)
        if re.match(r'^#+\s*(References|Bibliography|Citations)', line, re.IGNORECASE):
            in_references_section = True
            continue

        if in_references_section or re.search(r'\[\d+\]', line):
            # Extract DOI
            doi_match = DOI_REGEX.search(line)
            doi = doi_match.group(0) if doi_match else None

            # Extract URL
            url_match = URL_REGEX.search(line)
            url = url_match.group(0) if url_match else None

            # Extract potential title (text before DOI/URL or the whole line if no DOI/URL)
            text = line.strip()
            if not text:
                continue

            # Clean up numbering like [1], [2]
            clean_text = re.sub(r'^\[\d+\]\s*', '', text)
            # Remove URLs and DOIs from the text to get the title/description
            clean_text = re.sub(r'https?://[^\s]+', '', clean_text)
            clean_text = re.sub(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', '', clean_text)
            clean_text = clean_text.strip()

            if not clean_text and not doi and not url:
                continue

            citations.append({
                'id': len(citations) + 1,
                'raw_text': text,
                'doi': doi,
                'url': url,
                'title_candidate': clean_text
            })

    if not citations:
        logger.warning("No citations found in research.md. Assuming empty list or invalid format.")

    return citations

def fetch_doi_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a DOI from Crossref API.
    """
    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            item = data.get('message', {}).get('items', [{}])[0]
            return {
                'title': item.get('title', [''])[0],
                'author': item.get('author', []),
                'published': item.get('published-print', {}).get('date-parts', [[None]])[0][0],
                'type': item.get('type')
            }
        else:
            logger.warning(f"Failed to fetch DOI {doi}: HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Error fetching DOI {doi}: {e}")
        return None

def fetch_url_metadata(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch basic metadata (title) from a URL (HTML scraping).
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; LLMXiveBot/1.0)'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ""
            return {'title': title, 'source': url}
        else:
            logger.warning(f"Failed to fetch URL {url}: HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Error fetching URL {url}: {e}")
        return None

def calculate_token_overlap(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity (token overlap) between two strings.
    """
    if not text1 or not text2:
        return 0.0

    # Normalize: lowercase, remove punctuation, split
    def tokenize(s: str) -> set:
        s = s.lower()
        s = re.sub(r'[^\w\s]', '', s)
        return set(s.split())

    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)

    return len(intersection) / len(union) if union else 0.0

def verify_semantic_relevance(title_candidate: str, metadata: Dict[str, Any]) -> bool:
    """
    Basic semantic relevance check:
    - Ensure the fetched title contains significant words from the candidate.
    - Check for presence of 'Plant', 'Protein', 'Stress', 'Arabidopsis', 'Rice', 'Wheat' if applicable.
    """
    # If we have no candidate text, we can't verify
    if not title_candidate:
        return True  # Or False? Let's assume if no candidate, we trust the link/DOI.

    # Check for domain-specific keywords if the candidate mentions them
    keywords = ['plant', 'protein', 'stress', 'arabidopsis', 'rice', 'wheat', 'proteomic', 'transcriptomic']
    candidate_lower = title_candidate.lower()
    metadata_title = metadata.get('title', '').lower()

    # Count how many keywords from the candidate appear in the metadata title
    matches = 0
    for kw in keywords:
        if kw in candidate_lower and kw in metadata_title:
            matches += 1

    # If the candidate has specific keywords, they must appear in the metadata
    if any(kw in candidate_lower for kw in keywords) and matches == 0:
        return False

    return True

def validate_citation(citation: Dict[str, Any], threshold: float) -> Tuple[bool, str]:
    """
    Validate a single citation.
    Returns (is_valid, message)
    """
    doi = citation.get('doi')
    url = citation.get('url')
    title_candidate = citation.get('title_candidate', '')

    if not doi and not url:
        return False, "No DOI or URL found in citation."

    metadata = None
    if doi:
        logger.info(f"Validating DOI: {doi}")
        metadata = fetch_doi_metadata(doi)
    elif url:
        logger.info(f"Validating URL: {url}")
        metadata = fetch_url_metadata(url)

    if not metadata:
        return False, "Could not fetch metadata from primary source."

    # 1. Check Title Overlap
    overlap = calculate_token_overlap(title_candidate, metadata.get('title', ''))
    if overlap < threshold:
        return False, f"Title token overlap ({overlap:.2f}) is below threshold ({threshold})."

    # 2. Check Semantic Relevance
    if not verify_semantic_relevance(title_candidate, metadata):
        return False, "Semantic relevance check failed (keyword mismatch)."

    return True, "Validated successfully."

def main():
    """
    Main entry point for verify_sources.py.
    """
    config = get_config()
    threshold = config.get('reference_validation_threshold', REFERENCE_VALIDATION_THRESHOLD)
    research_path = config.get('research_md_path', 'research.md')

    # Resolve relative path if needed
    if not os.path.isabs(research_path):
        # Try relative to project root, then relative to script
        if not os.path.exists(research_path):
            parent = Path(__file__).parent.parent
            research_path = str(parent / research_path)

    logger.info(f"Starting source verification for: {research_path} with threshold {threshold}")

    try:
        citations = parse_citations(research_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if not citations:
        logger.warning("No citations found to validate. Exiting successfully.")
        return

    failed_citations = []
    for citation in citations:
        is_valid, message = validate_citation(citation, threshold)
        if is_valid:
            logger.info(f"Citation {citation['id']}: OK - {message}")
        else:
            logger.error(f"Citation {citation['id']}: FAILED - {message}")
            failed_citations.append({
                'id': citation['id'],
                'raw_text': citation['raw_text'],
                'reason': message
            })

    if failed_citations:
        logger.error(f"Validation FAILED for {len(failed_citations)} citations.")
        # Write failure report
        report_path = Path(DATA_RAW_PATH) / "source_validation_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(failed_citations, f, indent=2)
        logger.error(f"Failure report written to {report_path}")
        sys.exit(1)
    else:
        logger.info("All citations validated successfully.")

if __name__ == "__main__":
    main()