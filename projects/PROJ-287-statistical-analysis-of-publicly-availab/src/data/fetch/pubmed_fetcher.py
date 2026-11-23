"""
PubMed Abstract Fetcher for Topic Drift Analysis.

Implements exponential backoff with at most 3 retry attempts per endpoint.
Filters by publication year from the early 2000s to the present.
Uses the NCBI E-utilities API (efetch) to retrieve abstracts in XML format.
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
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 10.0
BATCH_SIZE = 100  # Max IDs per request allowed by NCBI
MIN_YEAR = 2000   # "Early 2000s"
MAX_YEAR = 2024   # Current year

logger = get_logger(__name__)


def fetch_pubmed_abstracts(
    query: str,
    max_results: int = 10000,
    output_dir: str = "data/raw",
    batch_size: int = BATCH_SIZE,
    email: str = "researcher@example.com"
) -> Dict[str, Any]:
    """
    Fetches PubMed abstracts matching a query, applying year filters and
    exponential backoff with a maximum of 3 retries.

    Args:
        query: PubMed search query (e.g., "topic_drift[Title/Abstract] AND 2000:2024[pdat]")
        max_results: Maximum number of IDs to fetch (NCBI limit applies per batch)
        output_dir: Directory to save the raw JSONL file
        batch_size: Number of records to fetch per API call
        email: Email address for NCBI compliance

    Returns:
        Dictionary containing fetch status, record count, and file path.
    """
    log = get_logger(__name__)
    log.info(f"Starting PubMed fetch for query: {query}")
    
    # Ensure output directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    output_file = out_path / "pubmed_raw.jsonl"
    record_count = 0
    error_count = 0
    fetched_ids = set()
    
    # First, get the list of IDs (esearch)
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&usehistory=y&retmode=json"
    
    try:
        with urllib.request.urlopen(search_url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            id_list = data['esearchresult']['idlist']
            log.info(f"Found {len(id_list)} IDs matching query.")
    except Exception as e:
        log.error(f"Failed to execute search query: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "count": 0,
            "file": str(output_file)
        }

    if not id_list:
        log.warning("No IDs found for the query.")
        return {
            "status": "no_results",
            "count": 0,
            "file": str(output_file)
        }

    # Process in batches
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i + batch_size]
            batch_str = ",".join(batch_ids)
            
            retry_count = 0
            success = False
            last_error = None

            while retry_count < MAX_RETRIES and not success:
                try:
                    # Construct fetch URL
                    fetch_url = (
                        f"{BASE_URL}?db=pubmed&id={batch_str}&retmode=xml&email={email}"
                    )
                    
                    req = urllib.request.Request(fetch_url)
                    req.add_header('User-Agent', 'TopicDriftAnalysis/1.0')
                    
                    with urllib.request.urlopen(req, timeout=60) as response:
                        xml_content = response.read().decode('utf-8')
                        records = parse_pubmed_xml(xml_content)
                        
                        for record in records:
                            # Filter by year explicitly just in case search query was loose
                            year = record.get('year')
                            if year and MIN_YEAR <= int(year) <= MAX_YEAR:
                                f_out.write(json.dumps(record, ensure_ascii=False) + '\n')
                                record_count += 1
                            else:
                                error_count += 1
                        
                        success = True
                        log.info(f"Fetched batch {i//batch_size + 1} ({len(batch_ids)} IDs).")

                except urllib.error.HTTPError as e:
                    last_error = f"HTTP Error {e.code}: {e.reason}"
                    retry_count += 1
                    backoff = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
                    log.warning(f"HTTP Error {e.code}. Retry {retry_count}/{MAX_RETRIES} in {backoff:.1f}s. {last_error}")
                    time.sleep(backoff)
                except urllib.error.URLError as e:
                    last_error = f"URL Error: {e.reason}"
                    retry_count += 1
                    backoff = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
                    log.warning(f"URL Error. Retry {retry_count}/{MAX_RETRIES} in {backoff:.1f}s. {last_error}")
                    time.sleep(backoff)
                except Exception as e:
                    last_error = str(e)
                    retry_count += 1
                    backoff = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
                    log.warning(f"Unexpected error. Retry {retry_count}/{MAX_RETRIES} in {backoff:.1f}s. {last_error}")
                    time.sleep(backoff)

            if not success:
                log.error(f"Failed to fetch batch {i//batch_size + 1} after {MAX_RETRIES} retries. Error: {last_error}")

    log.info(f"Fetch complete. Total valid records: {record_count}, filtered out: {error_count}")
    
    # Compute checksum
    checksum = compute_file_checksum(output_file)
    
    return {
        "status": "success" if record_count > 0 else "no_valid_records",
        "count": record_count,
        "filtered_count": error_count,
        "file": str(output_file),
        "checksum": checksum
    }


def parse_pubmed_xml(xml_string: str) -> List[Dict[str, Any]]:
    """
    Parses PubMed XML response into a list of dictionaries.
    """
    records = []
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")
        return records

    for article in root.findall(".//PubmedArticle"):
        medline_citation = article.find("MedlineCitation")
        if medline_citation is None:
            continue
        
        article_data = medline_citation.find("Article")
        if article_data is None:
            continue

        pmid = medline_citation.find("PMID")
        pmid_val = pmid.text if pmid is not None else "unknown"

        # Extract Year
        year = None
        date_created = medline_citation.find("DateCreated")
        if date_created is not None:
            year_elem = date_created.find("Year")
            if year_elem is not None and year_elem.text:
                year = int(year_elem.text)
        
        # If DateCreated is missing, try ArticleDate
        if year is None:
            article_date = article_data.find("ArticleDate")
            if article_date is not None:
                year_elem = article_date.find("Year")
                if year_elem is not None and year_elem.text:
                    year = int(year_elem.text)

        # Extract Title
        title = ""
        title_elem = article_data.find("ArticleTitle")
        if title_elem is not None and title_elem.text:
            title = title_elem.text

        # Extract Abstract
        abstract_text = ""
        abstract_elem = article_data.find("Abstract")
        if abstract_elem is not None:
            abstract_text_elem = abstract_elem.find("AbstractText")
            if abstract_text_elem is not None and abstract_text_elem.text:
                abstract_text = abstract_text_elem.text
            else:
                # Handle multiple abstract text parts
                parts = abstract_elem.findall("AbstractText")
                if parts:
                    abstract_text = " ".join([p.text or "" for p in parts])

        # Extract Authors
        authors = []
        author_list = article_data.find("AuthorList")
        if author_list is not None:
            for author in author_list.findall("Author"):
                name = ""
                last_name = author.find("LastName")
                first_name = author.find("FirstName")
                if last_name is not None and last_name.text:
                    name += last_name.text
                if first_name is not None and first_name.text:
                    name += f" {first_name.text}"
                if name:
                    authors.append(name.strip())

        # Extract Journal
        journal = ""
        journal_elem = article_data.find("Journal")
        if journal_elem is not None:
            title_elem = journal_elem.find("Title")
            if title_elem is not None and title_elem.text:
                journal = title_elem.text

        record = {
            "source": "pubmed",
            "pmid": pmid_val,
            "year": year,
            "title": title,
            "abstract": abstract_text,
            "authors": authors,
            "journal": journal
        }
        records.append(record)

    return records


def compute_file_checksum(file_path: Path) -> str:
    """Computes SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    """
    Entry point for running the PubMed fetcher directly.
    Reads query from environment or uses a default example.
    """
    import os
    query = os.getenv("PUBMED_QUERY", "machine learning[Title/Abstract] AND 2000:2024[pdat]")
    max_results = int(os.getenv("PUBMED_MAX_RESULTS", "500"))
    output_dir = os.getenv("PUBMED_OUTPUT_DIR", "data/raw")
    email = os.getenv("NCBI_EMAIL", "example@example.com")

    logger.info(f"Running PubMed fetcher with query: {query}")
    
    result = fetch_pubmed_abstracts(
        query=query,
        max_results=max_results,
        output_dir=output_dir,
        email=email
    )
    
    print(json.dumps(result, indent=2))
    if result["status"] != "success":
        exit(1)


if __name__ == "__main__":
    main()