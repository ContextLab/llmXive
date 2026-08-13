import time
import logging
import hashlib
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Generator, Any

from src.utils.logging import get_logger
from src.utils.config import get_random_seed

# Constants
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
MAX_RETRIES = 3
INITIAL_DELAY = 1.0  # seconds
MAX_DELAY = 10.0     # seconds
RETRY_MULTIPLIER = 2.0
MIN_YEAR = 2000
MAX_YEAR = 2024
BATCH_SIZE = 10000   # Max IDs per efetch request
MAX_RESULTS = 100000 # Cap total results to avoid timeout/memory issues

logger = get_logger(__name__)


def _calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = min(INITIAL_DELAY * (RETRY_MULTIPLIER ** attempt), MAX_DELAY)
    # Add small jitter to prevent thundering herd if running multiple instances
    jitter = (hashlib.sha256(str(time.time()).encode()).hexdigest()[:8])
    jitter_val = int(jitter, 16) % 1000 / 1000.0
    return delay * (1 + jitter_val * 0.1)


def _fetch_ids_by_year(year: int, db: str = "pubmed") -> List[str]:
    """
    Fetch PubMed IDs for a specific year.
    Returns a list of string IDs.
    """
    query = f"pubmed[{year}/{year}] AND (abstract[Filter])"
    params = {
        "db": db,
        "term": query,
        "retmax": MAX_RESULTS,
        "usehistory": "y",
        "retmode": "xml"
    }
    
    url = f"{BASE_URL}?term={urllib.parse.quote(query)}&db={db}&retmax={MAX_RESULTS}&usehistory=y&retmode=xml"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
            root = ET.fromstring(data)
            
            # Parse count
            count_elem = root.find(".//Count")
            count = int(count_elem.text) if count_elem is not None else 0
            
            if count == 0:
                logger.warning(f"No results found for year {year}")
                return []
            
            # Parse IDs
            id_list = []
            id_tags = root.findall(".//Id")
            for tag in id_tags:
                if tag.text:
                    id_list.append(tag.text)
            
            logger.info(f"Fetched {len(id_list)} IDs for year {year} (Total available: {count})")
            return id_list

    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code} fetching IDs for year {year}: {e.reason}")
        return []
    except urllib.error.URLError as e:
        logger.error(f"URL Error fetching IDs for year {year}: {e.reason}")
        return []
    except ET.ParseError as e:
        logger.error(f"XML Parse Error fetching IDs for year {year}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching IDs for year {year}: {e}")
        return []


def _fetch_abstracts_batch(id_batch: List[str], db: str = "pubmed") -> List[Dict[str, Any]]:
    """
    Fetch abstract details for a batch of IDs.
    Returns a list of dictionaries with record data.
    """
    if not id_batch:
        return []

    ids_str = ",".join(id_batch)
    params = {
        "db": db,
        "id": ids_str,
        "retmode": "xml",
        "rettype": "abstract"
    }
    
    url = f"{FETCH_URL}?db={db}&id={ids_str}&retmode=xml&rettype=abstract"

    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
            root = ET.fromstring(data)
            
            records = []
            for article in root.findall(".//Article"):
                record = {
                    "pmid": None,
                    "title": "",
                    "abstract": "",
                    "year": None,
                    "journal": ""
                }
                
                # Extract PMID
                article_id = article.find("ArticleId")
                if article_id is not None and article_id.attrib.get("IdType") == "pubmed":
                    record["pmid"] = article_id.text
                
                # Extract Title
                title_elem = article.find(".//ArticleTitle")
                if title_elem is not None and title_elem.text:
                    record["title"] = title_elem.text
                
                # Extract Abstract
                abstract_elem = article.find(".//Abstract")
                if abstract_elem is not None:
                    abstract_texts = abstract_elem.findall(".//AbstractText")
                    abstract_parts = [t.text for t in abstract_texts if t is not None and t.text]
                    record["abstract"] = " ".join(abstract_parts)
                
                # Extract Year and Journal
                journal_elem = article.find(".//Journal")
                if journal_elem is not None:
                    title_elem = journal_elem.find(".//Title")
                    if title_elem is not None and title_elem.text:
                        record["journal"] = title_elem.text
                    
                    pub_date = journal_elem.find(".//PubDate")
                    if pub_date is not None:
                        year_elem = pub_date.find(".//Year")
                        if year_elem is not None and year_elem.text:
                            try:
                                record["year"] = int(year_elem.text)
                            except ValueError:
                                pass
                
                # Only include if we have a valid year in range and abstract
                if (record["pmid"] and 
                    record["year"] and 
                    MIN_YEAR <= record["year"] <= MAX_YEAR and
                    record["abstract"]):
                    records.append(record)
                else:
                    # Log if missing critical fields for debugging
                    if not record["abstract"] and record["pmid"]:
                        logger.debug(f"Skipping PMID {record['pmid']}: No abstract or invalid year")
            
            return records

    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code} fetching batch: {e.reason}")
        return []
    except urllib.error.URLError as e:
        logger.error(f"URL Error fetching batch: {e.reason}")
        return []
    except ET.ParseError as e:
        logger.error(f"XML Parse Error fetching batch: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching batch: {e}")
        return []


def fetch_pubmed_abstracts(
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch PubMed abstracts for the specified year range (2000-2024).
    Implements exponential backoff with at most 3 retry attempts per endpoint.
    
    Args:
        year_start: Start year (inclusive), defaults to MIN_YEAR
        year_end: End year (inclusive), defaults to MAX_YEAR
        output_dir: Directory to save raw JSONL file (optional)
    
    Returns:
        List of dictionaries containing abstract data.
    """
    start_year = year_start if year_start is not None else MIN_YEAR
    end_year = year_end if year_end is not None else MAX_YEAR
    
    if start_year < MIN_YEAR or end_year > MAX_YEAR:
        raise ValueError(f"Year range must be between {MIN_YEAR} and {MAX_YEAR}")
    
    all_records = []
    total_ids_fetched = 0
    
    logger.info(f"Starting PubMed fetch for years {start_year} to {end_year}")
    
    for year in range(start_year, end_year + 1):
        logger.info(f"Processing year {year}...")
        
        # Fetch IDs with retry logic
        attempt = 0
        ids = []
        while attempt < MAX_RETRIES:
            ids = _fetch_ids_by_year(year)
            if ids:
                break
            attempt += 1
            if attempt < MAX_RETRIES:
                delay = _calculate_backoff(attempt)
                logger.warning(f"Failed to fetch IDs for {year}, retrying in {delay:.2f}s (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
        
        if not ids:
            logger.error(f"Failed to fetch IDs for year {year} after {MAX_RETRIES} attempts. Skipping.")
            continue
        
        total_ids_fetched += len(ids)
        logger.info(f"Found {len(ids)} IDs for {year}. Fetching details in batches...")
        
        # Fetch details in batches with retry logic
        for i in range(0, len(ids), BATCH_SIZE):
            batch = ids[i : i + BATCH_SIZE]
            attempt = 0
            batch_records = []
            
            while attempt < MAX_RETRIES:
                batch_records = _fetch_abstracts_batch(batch)
                if batch_records:
                    break
                attempt += 1
                if attempt < MAX_RETRIES:
                    delay = _calculate_backoff(attempt)
                    logger.warning(f"Batch fetch failed, retrying in {delay:.2f}s (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
            
            if not batch_records:
                logger.error(f"Failed to fetch batch starting at index {i} after {MAX_RETRIES} attempts.")
                continue
            
            all_records.extend(batch_records)
            logger.info(f"Fetched batch {i // BATCH_SIZE + 1}. Total records so far: {len(all_records)}")
    
    logger.info(f"Total IDs fetched: {total_ids_fetched}, Total valid records: {len(all_records)}")
    
    # Save to file if output_dir provided
    if output_dir:
        output_path = Path(output_dir) / "pubmed_raw.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            for record in all_records:
                f.write(json.dumps(record) + "\n")
        
        logger.info(f"Saved {len(all_records)} records to {output_path}")
    
    return all_records


def main():
    """Main entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch PubMed abstracts")
    parser.add_argument("--start-year", type=int, default=MIN_YEAR, help=f"Start year (default: {MIN_YEAR})")
    parser.add_argument("--end-year", type=int, default=MAX_YEAR, help=f"End year (default: {MAX_YEAR})")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory for raw JSONL")
    
    args = parser.parse_args()
    
    setup_logger = get_logger(__name__)
    setup_logger.setLevel(logging.INFO)
    
    fetch_pubmed_abstracts(
        year_start=args.start_year,
        year_end=args.end_year,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()