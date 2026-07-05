"""
ArXiv Abstract Fetcher with Exponential Backoff and Year Filtering.

This module implements the data acquisition component for ArXiv abstracts,
adhering to the project's constraints:
- Exponential backoff with a maximum of 3 retry attempts.
- Filtering by publication year (2000–2024).
- Real data retrieval from the ArXiv API.
"""

import time
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException, HTTPError, Timeout

# Import project utilities
from src.utils.logging import get_logger
from src.utils.config import get_random_seed
from src.models.entities import AbstractRecord

# Constants
ARXIV_API_BASE = "http://export.arxiv.org/api/query"
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 10.0     # seconds
YEAR_START = 2000
YEAR_END = 2024
DEFAULT_MAX_RESULTS = 1000  # Default batch size for demonstration

logger = get_logger(__name__)


def _calculate_backoff(attempt: int, seed: Optional[int] = None) -> float:
    """
    Calculate exponential backoff duration with jitter.
    """
    base_delay = INITIAL_BACKOFF * (2 ** attempt)
    # Add jitter to prevent thundering herd
    jitter = 0.1 * base_delay
    if seed is not None:
        # Use simple deterministic jitter if seed is provided for reproducibility
        import random
        rng = random.Random(seed + attempt)
        jitter = rng.uniform(0, jitter)
    else:
        import random
        jitter = random.uniform(0, jitter)
    
    return min(base_delay + jitter, MAX_BACKOFF)


def _parse_arxiv_date(date_str: str) -> Optional[int]:
    """
    Parse an ISO 8601 date string from ArXiv to extract the year.
    Example: "2023-01-15T12:00:00Z" -> 2023
    """
    if not date_str:
        return None
    try:
        # ArXiv dates are typically YYYY-MM-DDTHH:MM:SSZ
        year = int(date_str[:4])
        return year
    except (ValueError, IndexError):
        return None


def _is_valid_year(year: Optional[int]) -> bool:
    """
    Check if the year falls within the target range (2000–2024).
    """
    if year is None:
        return False
    return YEAR_START <= year <= YEAR_END


def fetch_arxiv_abstracts(
    query: str = "all:topic_drift",
    max_results: int = DEFAULT_MAX_RESULTS,
    start: int = 0,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
    output_dir: Optional[str] = None,
    seed: Optional[int] = None
) -> List[AbstractRecord]:
    """
    Fetch abstracts from ArXiv with exponential backoff and year filtering.

    Args:
        query: ArXiv search query (e.g., "all:topic_drift").
        max_results: Maximum number of results to fetch.
        start: Starting index for pagination.
        sort_by: Sorting criteria ('submittedDate', 'lastUpdatedDate', 'relevance').
        sort_order: Sorting order ('ascending', 'descending').
        output_dir: Optional directory to save raw JSONL output.
        seed: Random seed for jitter reproducibility.

    Returns:
        A list of AbstractRecord objects that passed the year filter.
    """
    if seed is None:
        seed = get_random_seed()

    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order
    }

    url = f"{ARXIV_API_BASE}?{urlencode(params)}"
    
    logger.info(f"Fetching from ArXiv: {url}")
    
    fetched_records: List[AbstractRecord] = []
    retry_count = 0
    last_exception: Optional[Exception] = None

    # Prepare output file if directory provided
    output_path: Optional[Path] = None
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        output_path = Path(output_dir) / f"arxiv_raw_{timestamp}.jsonl"
        logger.info(f"Saving raw data to: {output_path}")

    while retry_count < MAX_RETRIES:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Reset retry count on success
            retry_count = 0 
            
            # Parse response (Atom XML)
            # For robustness, we use a simple string parsing approach 
            # as lxml might not be in requirements, but requests is.
            # However, standard practice suggests using xml.etree.ElementTree
            import xml.etree.ElementTree as ET
            
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                logger.error(f"Failed to parse XML response: {e}")
                raise ValueError("Invalid XML response from ArXiv")

            # Define namespaces
            namespaces = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom"
            }

            entries = root.findall("atom:entry", namespaces)
            
            if not entries:
                logger.info("No entries found in response.")
                break

            for entry in entries:
                record = _parse_arxiv_entry(entry, namespaces)
                if record and _is_valid_year(record.published_year):
                    fetched_records.append(record)
                    if output_path:
                        with open(output_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(record.to_dict()) + "\n")

            # If we got fewer results than requested, we've reached the end
            if len(entries) < max_results:
                break
            
            # Prepare next page
            start += max_results
            params["start"] = start
            url = f"{ARXIV_API_BASE}?{urlencode(params)}"
            logger.debug(f"Next page URL: {url}")

        except (HTTPError, Timeout) as e:
            last_exception = e
            retry_count += 1
            if retry_count < MAX_RETRIES:
                backoff = _calculate_backoff(retry_count, seed)
                logger.warning(
                    f"Request failed (Attempt {retry_count}/{MAX_RETRIES}). "
                    f"Retrying in {backoff:.2f}s... Error: {e}"
                )
                time.sleep(backoff)
            else:
                logger.error(f"Max retries ({MAX_RETRIES}) exceeded. Failing.")
                raise RuntimeError(f"Failed to fetch data after {MAX_RETRIES} attempts: {e}") from e
        except RequestException as e:
            logger.error(f"Network error: {e}")
            raise RuntimeError(f"Network error during fetch: {e}") from e
        except ValueError as e:
            logger.error(f"Data parsing error: {e}")
            raise

    logger.info(f"Successfully fetched {len(fetched_records)} records within year range {YEAR_START}-{YEAR_END}.")
    return fetched_records


def _parse_arxiv_entry(entry: ET.Element, namespaces: Dict[str, str]) -> Optional[AbstractRecord]:
    """
    Parse a single ArXiv entry into an AbstractRecord.
    """
    try:
        title = entry.find("atom:title", namespaces)
        summary = entry.find("atom:summary", namespaces)
        published = entry.find("atom:published", namespaces)
        id_elem = entry.find("atom:id", namespaces)
        authors = entry.findall("atom:author/atom:name", namespaces)
        
        if not all([title, summary, published, id_elem]):
            logger.warning("Skipping entry with missing required fields.")
            return None

        text_title = title.text.strip() if title.text else ""
        text_summary = summary.text.strip() if summary.text else ""
        pub_date = published.text.strip() if published.text else ""
        pub_year = _parse_arxiv_date(pub_date)
        paper_id = id_elem.text.strip() if id_elem.text else ""
        
        author_names = [a.text.strip() for a in authors if a.text]

        return AbstractRecord(
            source="arxiv",
            paper_id=paper_id,
            title=text_title,
            abstract=text_summary,
            authors=author_names,
            published_date=pub_date,
            published_year=pub_year,
            raw_data=None # Raw XML not stored in entity, only in file
        )
    except Exception as e:
        logger.warning(f"Error parsing entry: {e}")
        return None


def main():
    """
    Entry point for running the ArXiv fetcher as a standalone script.
    Fetches a sample of abstracts and saves them to data/raw/.
    """
    from src.utils.config import ensure_directories
    
    # Ensure directories exist
    ensure_directories()
    
    # Example query: "all:topic_drift" or a broader one for testing
    # Using a generic query to ensure we get data if topic_drift is rare
    query = "all:topic_drift OR all:statistical" 
    
    logger.info("Starting ArXiv fetcher...")
    
    try:
        records = fetch_arxiv_abstracts(
            query=query,
            max_results=100,  # Fetch 100 records for the task
            output_dir="data/raw",
            seed=42
        )
        
        logger.info(f"Fetch complete. Total valid records: {len(records)}")
        
        if not records:
            logger.warning("No records were fetched or filtered. Check the query or year range.")
        
    except Exception as e:
        logger.error(f"Fatal error in fetcher: {e}")
        raise


if __name__ == "__main__":
    # Setup basic logging for script execution
    setup_logging_level = logging.INFO
    import sys
    # Simple config for script run
    logger = get_logger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    main()
