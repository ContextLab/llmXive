import time
import logging
import hashlib
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator

from src.utils.logging import get_logger

# PubMed ESearch/EFetch API base URLs
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
EMAIL = "system@example.com"  # Required by NCBI
TOOL = "llmXive_topic_drift"

logger = get_logger(__name__)

def _build_esearch_params(
    term: str,
    start_year: int,
    end_year: int,
    max_results: int,
    retstart: int = 0
) -> Dict[str, Any]:
    """Build query parameters for PubMed ESearch."""
    date_range = f"{start_year}/{start_year}[Date - Publication] : {end_year}/{end_year}[Date - Publication]"
    search_term = f"{term} AND {date_range}"
    
    return {
        "db": "pubmed",
        "term": search_term,
        "retmax": min(1000, max_results),  # Max 1000 per request
        "retstart": retstart,
        "retmode": "xml",
        "email": EMAIL,
        "tool": TOOL
    }

def _build_efetch_params(uids: List[str]) -> Dict[str, Any]:
    """Build query parameters for PubMed EFetch."""
    return {
        "db": "pubmed",
        "id": ",".join(uids),
        "retmode": "xml",
        "rettype": "abstract",
        "email": EMAIL,
        "tool": TOOL
    }

def _fetch_with_backoff(
    url: str,
    params: Dict[str, Any],
    max_retries: int = 3
) -> Optional[str]:
    """
    Fetch data from URL with exponential backoff.
    Retries at most `max_retries` times (3 attempts total).
    Returns the response text or None if all retries fail.
    """
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{url}?{query_string}"
    
    attempt = 0
    while attempt <= max_retries:
        try:
            logger.debug(f"Fetching URL (attempt {attempt + 1}/{max_retries + 1}): {full_url[:100]}...")
            req = urllib.request.Request(full_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            logger.warning(f"HTTP Error {e.code} on attempt {attempt + 1}: {e.reason}")
            if e.code == 429:  # Too Many Requests
                wait_time = (2 ** attempt) * 2
                logger.info(f"Rate limited. Waiting {wait_time}s before retry.")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP Error {e.code} not retryable: {e.reason}")
                return None
        except urllib.error.URLError as e:
            logger.warning(f"URL Error on attempt {attempt + 1}: {e.reason}")
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 2
                time.sleep(wait_time)
            else:
                return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
        
        attempt += 1
    
    logger.error(f"Failed to fetch after {max_retries + 1} attempts.")
    return None

def _parse_esearch_response(xml_content: str) -> List[str]:
    """Parse ESearch XML response and return list of PMIDs."""
    try:
        root = ET.fromstring(xml_content)
        id_list = []
        for id_elem in root.findall(".//Id"):
            id_list.append(id_elem.text)
        return id_list
    except ET.ParseError as e:
        logger.error(f"Failed to parse ESearch XML: {e}")
        return []

def _parse_efetch_response(xml_content: str) -> List[Dict[str, Any]]:
    """Parse EFetch XML response and return list of record dicts."""
    records = []
    try:
        root = ET.fromstring(xml_content)
        for article in root.findall(".//PubmedArticle"):
            pmid = article.find(".//PMID")
            pmid_text = pmid.text if pmid is not None else "unknown"
            
            article_data = article.find(".//Article")
            if article_data is None:
                continue
            
            # Extract title
            title_elem = article_data.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""
            
            # Extract abstract
            abstract_elem = article_data.find(".//Abstract")
            abstract_text = ""
            if abstract_elem is not None:
                abstract_blocks = abstract_elem.findall(".//AbstractText")
                abstract_parts = []
                for block in abstract_blocks:
                    if block.text:
                        abstract_parts.append(block.text)
                abstract_text = " ".join(abstract_parts)
            
            # Extract publication year
            date_elem = article_data.find(".//Journal//JournalIssue//PubDate//Year")
            pub_year = date_elem.text if date_elem is not None else None
            
            # Extract authors
            author_list = []
            for author in article_data.findall(".//Author"):
                last_name = author.find("LastName")
                first_name = author.find("ForeName")
                if last_name is not None and last_name.text:
                    name = last_name.text
                    if first_name is not None and first_name.text:
                        name = f"{first_name.text} {name}"
                    author_list.append(name)
            
            records.append({
                "pmid": pmid_text,
                "title": title,
                "abstract": abstract_text,
                "year": pub_year,
                "authors": author_list,
                "source": "pubmed"
            })
    except ET.ParseError as e:
        logger.error(f"Failed to parse EFetch XML: {e}")
    
    return records

def fetch_pubmed_abstracts(
    term: str,
    start_year: int = 2000,
    end_year: int = 2024,
    max_total: int = 5000,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Fetch abstracts from PubMed for a given term and year range.
    
    Args:
        term: Search term (e.g., "machine learning")
        start_year: Start year (inclusive)
        end_year: End year (inclusive)
        max_total: Maximum total records to fetch
        output_path: Optional path to save raw JSONL file
    
    Returns:
        List of abstract records
    """
    logger.info(f"Fetching PubMed abstracts for term='{term}', years={start_year}-{end_year}, max={max_total}")
    
    all_records = []
    retstart = 0
    batch_size = 1000
    
    # First, get total count
    esearch_params = _build_esearch_params(term, start_year, end_year, batch_size, retstart)
    xml_response = _fetch_with_backoff(PUBMED_ESEARCH_URL, esearch_params)
    
    if not xml_response:
        logger.error("Failed to get search results from PubMed.")
        return []
    
    # Parse count from XML
    try:
        root = ET.fromstring(xml_response)
        count_elem = root.find(".//Count")
        total_count = int(count_elem.text) if count_elem is not None else 0
    except (ET.ParseError, ValueError) as e:
        logger.error(f"Failed to parse total count: {e}")
        return []
    
    logger.info(f"Total PubMed records found: {total_count}")
    count_to_fetch = min(total_count, max_total)
    
    # Fetch IDs in batches
    all_uids = []
    while len(all_uids) < count_to_fetch:
        esearch_params = _build_esearch_params(term, start_year, end_year, batch_size, retstart)
        xml_response = _fetch_with_backoff(PUBMED_ESEARCH_URL, esearch_params)
        
        if not xml_response:
            logger.warning("Failed to fetch IDs batch. Stopping.")
            break
        
        uids = _parse_esearch_response(xml_response)
        if not uids:
            break
        
        all_uids.extend(uids)
        retstart += batch_size
        
        if retstart >= count_to_fetch:
            break
        
        # Small delay between requests to be polite
        time.sleep(0.3)
    
    logger.info(f"Retrieved {len(all_uids)} PMIDs.")
    
    # Fetch abstracts in batches
    fetched_count = 0
    for i in range(0, len(all_uids), 100):
        batch_uids = all_uids[i:i+100]
        efetch_params = _build_efetch_params(batch_uids)
        
        xml_response = _fetch_with_backoff(PUBMED_EFETCH_URL, efetch_params)
        
        if xml_response:
            batch_records = _parse_efetch_response(xml_response)
            all_records.extend(batch_records)
            fetched_count += len(batch_records)
            logger.debug(f"Fetched batch {i//100 + 1}: {len(batch_records)} records")
        
        time.sleep(0.3)  # Be polite to the API
    
    logger.info(f"Successfully fetched {len(all_records)} abstracts.")
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for record in all_records:
                f.write(json.dumps(record) + "\n")
        checksum = hashlib.sha256()
        with open(output_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                checksum.update(chunk)
        logger.info(f"Saved raw data to {output_path} (SHA256: {checksum.hexdigest()})")
    
    return all_records

def main():
    """Main entry point for fetching PubMed abstracts."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch PubMed abstracts")
    parser.add_argument("--term", type=str, default="machine learning", help="Search term")
    parser.add_argument("--start-year", type=int, default=2000, help="Start year")
    parser.add_argument("--end-year", type=int, default=2024, help="End year")
    parser.add_argument("--max", type=int, default=5000, help="Max records to fetch")
    parser.add_argument("--output", type=str, default="data/raw/pubmed_abstracts.jsonl", help="Output file path")
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    records = fetch_pubmed_abstracts(
        term=args.term,
        start_year=args.start_year,
        end_year=args.end_year,
        max_total=args.max,
        output_path=output_path
    )
    
    if not records:
        logger.error("No records fetched. Exiting.")
        exit(1)
    
    logger.info(f"Fetch complete. Total records: {len(records)}")

if __name__ == "__main__":
    main()
