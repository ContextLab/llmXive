"""
Citation Fetcher Module (Task T005a).

Extracts citations from `research.md` and fetches their metadata (title, DOI, URL).
Uses Crossref API for metadata resolution.
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import requests

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RESEARCH_MD_PATH = Path("data/research.md")
OUTPUT_PATH = Path("data/raw/citations_metadata.json")
CROSSREF_API_URL = "https://api.crossref.org/works"

# Regex patterns for citation extraction
# Matches formats like: [1], [1-3], [1, 3], or "Author (Year)"
BRACKET_REF_PATTERN = re.compile(r'\[(\d+(?:,\s*\d+)*(?:-\d+)*)\]')
AUTHOR_YEAR_PATTERN = re.compile(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*\((\d{4})\)\b')

def extract_citations_from_md(md_path: Path) -> List[Dict[str, Any]]:
    """
    Reads a markdown file and extracts all citation references found.
    
    Returns a list of dicts with 'ref_id' (cleaned numbers) and 'raw_text'.
    """
    if not md_path.exists():
        raise FileNotFoundError(f"Research file not found: {md_path}")
    
    content = md_path.read_text(encoding='utf-8')
    citations = []
    
    # 1. Extract bracketed references [1], [1, 2], [1-3]
    bracket_matches = BRACKET_REF_PATTERN.findall(content)
    for match in bracket_matches:
        # Expand ranges if present (e.g., "1-3" -> "1", "2", "3")
        if '-' in match:
            parts = match.split('-')
            start, end = int(parts[0]), int(parts[1])
            ids = [str(i) for i in range(start, end + 1)]
        else:
            ids = [m.strip() for m in match.split(',')]
        
        for cid in ids:
            citations.append({'ref_id': cid, 'source_type': 'bracketed', 'raw_text': f"[{cid}]"})
    
    # 2. Extract Author (Year) references (simple heuristic)
    author_matches = AUTHOR_YEAR_PATTERN.findall(content)
    for author, year in author_matches:
        citations.append({'ref_id': f"{author}_{year}", 'source_type': 'author_year', 'raw_text': f"{author} ({year})"})
        
    return citations

def fetch_crossref_metadata(query: str) -> Optional[Dict[str, Any]]:
    """
    Fetches metadata from Crossref API using a query string (DOI or title).
    """
    headers = {
        'User-Agent': 'llmXive-research-pipeline/1.0 (contact: research@example.com)'
    }
    
    # Try as DOI first
    doi_query = f"{CROSSREF_API_URL}/{query}"
    try:
        response = requests.get(doi_query, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'message' in data:
                logger.info(f"Found DOI: {query}")
                return _normalize_crossref_response(data['message'])
    except requests.RequestException as e:
        logger.debug(f"DOI fetch failed for {query}: {e}")
    
    # Fallback to title search if DOI fails or wasn't a DOI
    # This is less reliable but necessary for author-year extraction
    title_query = f"{CROSSREF_API_URL}?query.title={query}&rows=1"
    try:
        response = requests.get(title_query, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('message', {}).get('items', [])
            if items:
                logger.info(f"Found via title search: {query}")
                return _normalize_crossref_response(items[0])
    except requests.RequestException as e:
        logger.debug(f"Title search failed for {query}: {e}")
        
    return None

def _normalize_crossref_response(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes the Crossref API response into a standard format.
    """
    title = message.get('title', ['Unknown Title'])[0]
    doi = message.get('DOI')
    url = f"https://doi.org/{doi}" if doi else None
    authors = message.get('author', [])
    author_str = ", ".join([f"{a.get('given', '')} {a.get('family', '')}" for a in authors if a.get('family')])
    published = message.get('published-print', {}).get('date-parts', [[None]])[0][0] or message.get('published-online', {}).get('date-parts', [[None]])[0][0]
    
    return {
        'title': title,
        'doi': doi,
        'url': url,
        'authors': author_str,
        'year': published,
        'container_title': message.get('container-title', [''])[0] if message.get('container-title') else None,
        'raw_crossref': message # Keep raw for debugging if needed
    }

def fetch_all_citations(md_path: Path = RESEARCH_MD_PATH, output_path: Path = OUTPUT_PATH) -> List[Dict[str, Any]]:
    """
    Main entry point: Extracts citations from research.md and fetches metadata.
    Saves results to a JSON file.
    """
    logger.info(f"Starting citation extraction from {md_path}")
    
    citations = extract_citations_from_md(md_path)
    if not citations:
        logger.warning("No citations found in the research file.")
        results = []
    else:
        logger.info(f"Found {len(citations)} citation references. Fetching metadata...")
        results = []
        for idx, citation in enumerate(citations):
            ref_id = citation['ref_id']
            logger.info(f"Fetching [{idx+1}/{len(citations)}]: {ref_id}")
            
            meta = fetch_crossref_metadata(ref_id)
            if meta:
                results.append({
                    'ref_id': ref_id,
                    'source_type': citation['source_type'],
                    'status': 'fetched',
                    **meta
                })
            else:
                results.append({
                    'ref_id': ref_id,
                    'source_type': citation['source_type'],
                    'status': 'failed',
                    'title': None,
                    'doi': None,
                    'url': None
                })
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Citation metadata saved to {output_path}")
    return results

def main():
    """CLI entry point."""
    try:
        results = fetch_all_citations()
        success_count = sum(1 for r in results if r['status'] == 'fetched')
        fail_count = len(results) - success_count
        print(f"Extraction complete. Success: {success_count}, Failed: {fail_count}")
        if fail_count > 0:
            logger.warning(f"{fail_count} citations could not be resolved.")
    except Exception as e:
        logger.error(f"Fatal error in citation fetcher: {e}")
        raise

if __name__ == "__main__":
    main()
