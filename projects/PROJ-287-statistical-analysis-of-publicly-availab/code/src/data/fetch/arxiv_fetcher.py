import time
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
import requests
from urllib.parse import quote
import xml.etree.ElementTree as ET

from src.utils.logging import get_logger

# Constants
ARXIV_API_URL = "http://export.arxiv.org/api/query"
MAX_RETRIES = 3
INITIAL_DELAY = 1.0
MAX_DELAY = 10.0
YEAR_START = 2000
YEAR_END = 2024
DEFAULT_MAX_RESULTS = 1000
BATCH_SIZE = 100

def _get_logger():
    return get_logger(__name__)

def _parse_arxiv_date(date_str: str) -> Optional[int]:
    """Extract year from arXiv date string (e.g., '2001.00001' or ISO format)."""
    if not date_str:
        return None
    # arXiv IDs often start with YYMM or YYYY
    # Or dates come in ISO format: 2023-01-01T00:00:00Z
    if '-' in date_str:
        try:
            return int(date_str.split('-')[0])
        except (ValueError, IndexError):
            return None
    # Fallback: try to parse as YYYY or YY
    try:
        year_str = date_str[:4]
        if len(year_str) == 4 and year_str.isdigit():
            return int(year_str)
        elif len(year_str) == 2 and year_str.isdigit():
            # Assume 2000s for 2-digit years in this context
            return 2000 + int(year_str)
    except ValueError:
        pass
    return None

def _fetch_with_backoff(url: str, params: Dict[str, Any]) -> Optional[bytes]:
    """
    Fetch data from URL with exponential backoff and max 3 retries.
    Returns response content or None if all retries fail.
    """
    logger = _get_logger()
    delay = INITIAL_DELAY
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Attempt {attempt}/{MAX_RETRIES} for {url}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.content
            
            # Rate limited (429) or server error (5xx) -> retry
            if response.status_code in [429, 500, 502, 503, 504]:
                logger.warning(f"Status {response.status_code}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, MAX_DELAY)
                continue
            
            # Client error (4xx) -> do not retry
            logger.error(f"Client error {response.status_code}: {response.text[:200]}")
            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                return None
            time.sleep(delay)
            delay = min(delay * 2, MAX_DELAY)
    
    logger.error(f"Failed after {MAX_RETRIES} attempts.")
    return None

def _parse_response_to_records(content: bytes) -> List[Dict[str, Any]]:
    """Parse Atom XML response from arXiv API into list of records."""
    records = []
    try:
        root = ET.fromstring(content)
        # Define namespaces
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        
        entries = root.findall('atom:entry', ns)
        
        for entry in entries:
            record = {}
            
            # ID
            id_elem = entry.find('atom:id', ns)
            record['arxiv_id'] = id_elem.text if id_elem is not None else ""
            
            # Title
            title_elem = entry.find('atom:title', ns)
            record['title'] = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
            
            # Abstract
            summary_elem = entry.find('atom:summary', ns)
            record['abstract'] = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
            
            # Published date
            published_elem = entry.find('atom:published', ns)
            record['published'] = published_elem.text if published_elem is not None else ""
            
            # Year
            year = _parse_arxiv_date(record['published'])
            record['year'] = year
            
            # Categories
            categories = []
            for cat in entry.findall('atom:category', ns):
                term = cat.get('term')
                if term:
                    categories.append(term)
            record['categories'] = categories
            
            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text)
            record['authors'] = authors
            
            records.append(record)
            
    except ET.ParseError as e:
        _get_logger().error(f"XML parsing error: {e}")
    except Exception as e:
        _get_logger().error(f"Unexpected error parsing response: {e}")
    
    return records

def fetch_arxiv_abstracts(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    start: int = 0,
    output_path: Optional[Path] = None,
    filter_year_range: tuple = (YEAR_START, YEAR_END)
) -> List[Dict[str, Any]]:
    """
    Fetch abstracts from arXiv API with exponential backoff.
    
    Args:
        query: Search query string (e.g., 'all:deep learning')
        max_results: Maximum number of results to fetch
        start: Starting index for pagination
        output_path: Optional path to save raw JSONL
        filter_year_range: Tuple (start_year, end_year) to filter records
    
    Returns:
        List of dictionaries containing abstract data
    """
    logger = _get_logger()
    logger.info(f"Fetching arXiv abstracts for query: {query}")
    
    all_records = []
    current_start = start
    fetched_count = 0
    
    # Ensure we don't fetch more than requested
    remaining = max_results
    
    while remaining > 0:
        params = {
            'search_query': query,
            'start': current_start,
            'max_results': min(BATCH_SIZE, remaining),
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        content = _fetch_with_backoff(ARXIV_API_URL, params)
        
        if content is None:
            logger.error(f"Failed to fetch batch starting at {current_start}. Stopping.")
            break
        
        batch_records = _parse_response_to_records(content)
        
        if not batch_records:
            logger.info("No more records found in response.")
            break
        
        # Filter by year
        start_year, end_year = filter_year_range
        filtered_batch = [
            r for r in batch_records 
            if r['year'] is not None and start_year <= r['year'] <= end_year
        ]
        
        all_records.extend(filtered_batch)
        fetched_count += len(batch_records)
        remaining -= len(batch_records)
        
        # Check if we've hit the max_results limit (including filtered out)
        # Note: We continue fetching until we get enough raw records or API says no more
        # But we stop if we have enough *filtered* records? No, task says filter by year.
        # We stop when API returns no more or we hit the raw max_results limit.
        if len(batch_records) < BATCH_SIZE:
            # API returned fewer than requested, likely end of results
            break
        
        current_start += BATCH_SIZE
        
        # Small delay to be polite to the API even if not rate limited
        time.sleep(0.5)
    
    logger.info(f"Fetched {fetched_count} raw records, {len(all_records)} passed year filter ({filter_year_range}).")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record) + '\n')
        logger.info(f"Saved {len(all_records)} records to {output_path}")
    
    return all_records

def main():
    """
    Main entry point for running the arXiv fetcher directly.
    Fetches a sample set of abstracts and saves them to data/raw/arxiv_sample.jsonl
    """
    logger = _get_logger()
    logger.info("Starting arXiv fetcher (main mode)")
    
    # Example query: Computer Science - Artificial Intelligence
    # Filter for 2000-2024
    query = "cat:cs.AI"
    output_file = Path("data/raw/arxiv_abstracts_2000_2024.jsonl")
    
    try:
        records = fetch_arxiv_abstracts(
            query=query,
            max_results=500,  # Limit for demo/runtime safety
            output_path=output_file,
            filter_year_range=(2000, 2024)
        )
        
        if not records:
            logger.warning("No records retrieved.")
            return
        
        logger.info(f"Successfully fetched and saved {len(records)} records.")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
