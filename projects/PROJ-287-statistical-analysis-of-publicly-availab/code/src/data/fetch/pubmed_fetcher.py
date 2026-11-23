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

# Constants
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
MAX_RESULTS_PER_QUERY = 10000  # PubMed max per request
BATCH_SIZE = 5000  # Process in batches to avoid timeout
YEAR_START = 2000
YEAR_END = 2024

logger = get_logger(__name__)

def _delayed_retry(func, *args, **kwargs):
    """Execute a function with exponential backoff retry logic (max 3 attempts)."""
    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {MAX_RETRIES} attempts failed for {func.__name__}. Last error: {e}")
                raise
    raise last_exception

def _fetch_pubmed_ids(year_start: int, year_end: int, term: str = "Abstract") -> List[str]:
    """Fetch PubMed IDs (PMIDs) for a given year range and search term."""
    params = {
        "db": "pubmed",
        "term": f"{year_start}:{year_end}[Date - Publication] AND {term}[Title/Abstract]",
        "retmax": MAX_RESULTS_PER_QUERY,
        "retmode": "xml",
        "usehistory": "y"
    }

    def _do_request():
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{PUBMED_BASE_URL}?{query_string}"
        req = urllib.request.Request(url, headers={"User-Agent": "llmXive-TopicDrift/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()

    xml_data = _delayed_retry(_do_request)
    root = ET.fromstring(xml_data)

    ids = []
    for id_elem in root.findall(".//Id"):
        ids.append(id_elem.text)
    
    logger.info(f"Found {len(ids)} PMIDs for years {year_start}-{year_end}")
    return ids

def _fetch_abstract_batch(pmids: List[str]) -> Generator[Dict[str, Any], None, None]:
    """Fetch abstracts for a batch of PMIDs."""
    if not pmids:
        return

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract"
    }

    def _do_request():
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{PUBMED_FETCH_URL}?{query_string}"
        req = urllib.request.Request(url, headers={"User-Agent": "llmXive-TopicDrift/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read()

    xml_data = _delayed_retry(_do_request)
    root = ET.fromstring(xml_data)

    for article in root.findall(".//Article"):
        record = {}
        
        # Extract PMID
        pmid_elem = article.find(".//PMID")
        record["pmid"] = pmid_elem.text if pmid_elem is not None else None

        # Extract Title
        title_elem = article.find(".//ArticleTitle")
        record["title"] = title_elem.text if title_elem is not None else ""

        # Extract Abstract
        abstract_text = ""
        abstract_elem = article.find(".//Abstract")
        if abstract_elem is not None:
            for section in abstract_elem.findall(".//AbstractText"):
                if section.text:
                    abstract_text += section.text + " "
        record["abstract"] = abstract_text.strip()

        # Extract Publication Date
        pub_date = "0000"
        date_elem = article.find(".//PubDate")
        if date_elem is not None:
            year_elem = date_elem.find("Year")
            if year_elem is not None and year_elem.text:
                pub_date = year_elem.text
        record["year"] = pub_date

        # Extract Journal
        journal_elem = article.find(".//Journal/Title")
        record["journal"] = journal_elem.text if journal_elem is not None else ""

        # Extract Authors
        authors = []
        for author in article.findall(".//Author/LastName"):
            if author.text:
                authors.append(author.text)
        record["authors"] = ", ".join(authors)

        yield record

def fetch_pubmed_abstracts(year_start: int = YEAR_START, year_end: int = YEAR_END, output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch PubMed abstracts for the specified year range.
    
    Args:
        year_start: Start year (inclusive)
        year_end: End year (inclusive)
        output_path: Optional path to save raw JSONL data
    
    Returns:
        List of abstract records as dictionaries
    """
    logger.info(f"Starting PubMed fetch for years {year_start}-{year_end}")
    
    # Step 1: Fetch IDs
    pmids = _fetch_pubmed_ids(year_start, year_end)
    if not pmids:
        logger.warning("No PMIDs found for the specified criteria.")
        return []

    # Step 2: Fetch abstracts in batches
    all_records = []
    for i in range(0, len(pmids), BATCH_SIZE):
        batch_pmids = pmids[i:i + BATCH_SIZE]
        logger.info(f"Fetching batch {i//BATCH_SIZE + 1}: {len(batch_pmids)} PMIDs")
        
        for record in _fetch_abstract_batch(batch_pmids):
            # Filter by year strictly (in case of edge cases in search)
            try:
                year_val = int(record["year"])
                if year_start <= year_val <= year_end:
                    all_records.append(record)
                else:
                    logger.debug(f"Skipping record {record['pmid']} (year={record['year']}) outside range")
            except (ValueError, TypeError):
                logger.debug(f"Skipping record {record['pmid']} with invalid year: {record['year']}")
        
        # Small delay between batches to be polite to the API
        if i + BATCH_SIZE < len(pmids):
            time.sleep(0.5)

    logger.info(f"Successfully fetched {len(all_records)} valid abstracts")

    # Step 3: Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for record in all_records:
                f.write(json.dumps(record) + "\n")
        logger.info(f"Saved {len(all_records)} records to {output_path}")

    return all_records

def main():
    """Main entry point for standalone execution."""
    logger.info("Running PubMed fetcher standalone")
    
    # Define output path
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "pubmed_raw_2000_2024.jsonl"
    
    # Run fetch
    records = fetch_pubmed_abstracts(year_start=2000, year_end=2024, output_path=output_file)
    
    if not records:
        logger.error("No records fetched. Check logs for errors.")
        return 1
    
    logger.info(f"Fetch complete. Total records: {len(records)}")
    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())
