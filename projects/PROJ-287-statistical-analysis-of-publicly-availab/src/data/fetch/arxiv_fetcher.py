"""
arxiv_fetcher.py

Fetches academic abstracts from the arXiv API with exponential backoff,
filtering by publication year (2000-2024). Implements a strict 3-retry limit.
"""
import time
import logging
import hashlib
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
import xml.etree.ElementTree as ET

from src.utils.logging import get_logger
from src.utils.config import get_random_seed

# Constants
ARXIV_API_URL = "http://export.arxiv.org/api/query"
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_YEAR = 2024
MIN_YEAR = 2000
DEFAULT_MAX_RESULTS = 1000
START_INDEX = 0

logger = get_logger(__name__)


def _parse_arxiv_entry(entry: ET.Element) -> Optional[Dict[str, Any]]:
    """
    Parses a single arXiv entry XML element into a dictionary.
    Filters by year immediately.
    """
    try:
        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom',
              'dc': 'http://purl.org/dc/elements/1.1/'}

        title_elem = entry.find('atom:title', ns)
        published_elem = entry.find('atom:published', ns)
        id_elem = entry.find('atom:id', ns)
        authors = entry.findall('atom:author/atom:name', ns)
        abstract_elem = entry.find('atom:summary', ns)

        if not all([title_elem, published_elem, id_elem, abstract_elem]):
            return None

        # Extract year
        pub_date_str = published_elem.text
        if not pub_date_str or len(pub_date_str) < 4:
            return None
        
        try:
            year = int(pub_date_str[:4])
        except ValueError:
            return None

        # Filter by year
        if year < MIN_YEAR or year > MAX_YEAR:
            return None

        return {
            "id": id_elem.text,
            "title": title_elem.text.replace('\n', ' ').strip(),
            "abstract": abstract_elem.text.replace('\n', ' ').strip(),
            "published": pub_date_str,
            "year": year,
            "authors": [a.text for a in authors] if authors else [],
            "source": "arxiv"
        }
    except Exception as e:
        logger.warning(f"Failed to parse arXiv entry: {e}")
        return None


def fetch_arxiv_abstracts(
    query: str = "all:topic+drift",
    max_results: int = DEFAULT_MAX_RESULTS,
    start_index: int = START_INDEX,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Fetches abstracts from arXiv with exponential backoff and max 3 retries.
    
    Args:
        query: Search query string.
        max_results: Maximum number of results to fetch.
        start_index: Starting index for pagination.
        output_path: Optional path to save raw JSONL immediately.
        
    Returns:
        List of filtered abstract records.
    """
    results = []
    current_start = start_index
    fetched_count = 0
    
    # Construct URL
    url = f"{ARXIV_API_URL}?search_query={query}&start={current_start}&max_results={max_results}"
    
    logger.info(f"Fetching from arXiv: {url}")

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "llmXive-Research-Project/1.0 (statistical-analysis)"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode('utf-8')
                root = ET.fromstring(data)
                
                # Parse entries
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', ns)
                
                batch_count = 0
                for entry in entries:
                    record = _parse_arxiv_entry(entry)
                    if record:
                        results.append(record)
                        batch_count += 1
                
                logger.info(f"Batch fetched: {batch_count} valid records (filtered by year {MIN_YEAR}-{MAX_YEAR})")
                fetched_count += batch_count
                
                if fetched_count >= max_results:
                    break
                    
                # Check if there are more results (total_results in response)
                total_results_elem = root.find('opensearch:totalResults', {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'})
                if total_results_elem is None or int(total_results_elem.text) <= fetched_count:
                    break
                    
                # Prepare next page
                current_start += len(entries)
                if current_start >= max_results:
                    break
                url = f"{ARXIV_API_URL}?search_query={query}&start={current_start}&max_results={max_results - fetched_count}"
                
                attempt = 0  # Reset retry on success
                time.sleep(0.5)  # Politeness delay between batches
                
        except urllib.error.HTTPError as e:
            attempt += 1
            if attempt < MAX_RETRIES:
                backoff_time = INITIAL_BACKOFF * (2 ** (attempt - 1))
                logger.warning(f"HTTP Error {e.code} fetching arXiv. Retrying in {backoff_time}s (Attempt {attempt}/{MAX_RETRIES})")
                time.sleep(backoff_time)
            else:
                logger.error(f"Max retries ({MAX_RETRIES}) exceeded for arXiv fetch. Giving up.")
                raise
        except urllib.error.URLError as e:
            attempt += 1
            if attempt < MAX_RETRIES:
                backoff_time = INITIAL_BACKOFF * (2 ** (attempt - 1))
                logger.warning(f"URL Error fetching arXiv: {e.reason}. Retrying in {backoff_time}s (Attempt {attempt}/{MAX_RETRIES})")
                time.sleep(backoff_time)
            else:
                logger.error(f"Max retries ({MAX_RETRIES}) exceeded for arXiv fetch. Giving up.")
                raise
        except Exception as e:
            logger.error(f"Unexpected error fetching arXiv: {e}")
            raise

    if output_path:
        _save_raw_jsonl(results, output_path)

    logger.info(f"Total arXiv records fetched: {len(results)}")
    return results


def _save_raw_jsonl(data: List[Dict[str, Any]], path: Path) -> None:
    """Saves a list of records to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')
    logger.info(f"Saved raw arXiv data to {path}")


def main():
    """
    Main entry point for standalone execution.
    Fetches a sample of arXiv abstracts and saves them to data/raw/.
    """
    import argparse
    from src.utils.config import ensure_directories

    ensure_directories()
    
    parser = argparse.ArgumentParser(description="Fetch arXiv abstracts")
    parser.add_argument("--query", type=str, default="all:topic+drift", help="Search query")
    parser.add_argument("--max", type=int, default=100, help="Max results to fetch")
    parser.add_argument("--output", type=str, default="data/raw/arxiv_abstracts.jsonl", help="Output path")
    args = parser.parse_args()

    output_path = Path(args.output)
    
    try:
        records = fetch_arxiv_abstracts(
            query=args.query,
            max_results=args.max,
            output_path=output_path
        )
        print(f"Successfully fetched and saved {len(records)} records to {output_path}")
    except Exception as e:
        print(f"Failed to fetch arXiv data: {e}")
        raise


if __name__ == "__main__":
    main()