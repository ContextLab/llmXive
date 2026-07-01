"""
Parse publications associated with OpenML datasets to extract statistical parameters.
Implements US2: Extract Statistical Parameters via Full-Text Parsing.
"""
import json
import os
import sys
import time
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import project utilities
from utils.logging_config import setup_logging
from utils.oa_checker import is_open_access
from utils.parsers import extract_sample_size, extract_effect_size

# Setup logging
logger = logging.getLogger(__name__)
setup_logging()

# Constants
RAW_DATA_PATH = Path("data/raw/openml_metadata_filtered.json")
PROCESSED_DATA_PATH = Path("data/processed/extracted_params.json")
TIMEOUT_SECONDS = 10

def fetch_full_text(url: str) -> Optional[str]:
    """
    Fetch full text from a URL if it is Open Access.
    Returns None if paywalled or fetch fails.
    """
    if not url:
        return None

    # Check Open Access status
    if not is_open_access(url):
        logger.info(f"URL {url} is paywalled. Skipping full text fetch.")
        return None

    try:
        import requests
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        # Simple heuristic: if content type is HTML, try to extract text
        # In a real scenario, we might use a PDF parser or HTML cleaner
        # For now, we return the raw text as a fallback
        return response.text
    except Exception as e:
        logger.warning(f"Failed to fetch full text from {url}: {e}")
        return None

def fetch_doi_abstract(doi: str) -> Optional[str]:
    """
    Fetch abstract from DOI metadata API.
    """
    if not doi:
        return None
    try:
        import requests
        url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        message = data.get("message", {})
        abstract = message.get("abstract")
        title = message.get("title", [""])[0]
        # Construct a simple text block for parsing
        text = f"{title} {abstract}" if abstract else title
        return text
    except Exception as e:
        logger.warning(f"Failed to fetch abstract for DOI {doi}: {e}")
        return None

def parse_publication_data(dataset_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a single dataset entry to extract sample size and effect size.
    Returns a record with fields: dataset_id, sample_size, effect_size, metric_type,
    degrees_of_freedom, source_url, status.
    """
    dataset_id = dataset_entry.get("dataset_id")
    publication_link = dataset_entry.get("publication_link")
    task_id = dataset_entry.get("task_id")
    doi = dataset_entry.get("doi")

    record = {
        "dataset_id": dataset_id,
        "sample_size": None,
        "effect_size": None,
        "metric_type": None,
        "degrees_of_freedom": None,
        "source_url": publication_link or doi or task_id,
        "status": "unparseable"
    }

    text_to_parse = None
    source_type = None

    # 1. Try Full Text
    if publication_link:
        full_text = fetch_full_text(publication_link)
        if full_text:
            text_to_parse = full_text
            source_type = "full_text"

    # 2. Fallback to Abstract if full text failed or not available
    if not text_to_parse and (doi or publication_link):
        # If we have a DOI, try abstract
        abstract_text = None
        if doi:
            abstract_text = fetch_doi_abstract(doi)
        elif publication_link:
            # If no DOI but link exists, maybe try to extract DOI or just use link text?
            # For this implementation, we rely on the DOI field being present if available.
            # If not, we might try to fetch the link again as a fallback, but that's risky.
            # Let's assume DOI is the primary source for abstracts.
            pass
        
        if abstract_text:
            text_to_parse = abstract_text
            source_type = "abstract"
        elif not text_to_parse:
            # If we had a link but it was paywalled and no DOI, we might try fetching the link
            # again assuming it might be an HTML page with some text, but the OA check already
            # said no. So we skip.
            pass

    if not text_to_parse:
        logger.warning(f"No text source available for dataset {dataset_id}")
        return record

    # Extract Sample Size
    sample_size = extract_sample_size(text_to_parse)
    if sample_size:
        record["sample_size"] = sample_size

    # Extract Effect Size
    effect_result = extract_effect_size(text_to_parse)
    if effect_result:
        # effect_result is (value, metric_type, dof_tuple)
        record["effect_size"] = effect_result[0]
        record["metric_type"] = effect_result[1]
        if effect_result[2]:
            record["degrees_of_freedom"] = list(effect_result[2])

    # Determine status based on extraction success
    if record["sample_size"] is not None and record["effect_size"] is not None:
        record["status"] = "success"
        logger.info(f"Successfully parsed dataset {dataset_id} from {source_type}")
    elif record["sample_size"] is not None or record["effect_size"] is not None:
        # Partial success? The task implies we save the record anyway.
        record["status"] = "partial"
        logger.warning(f"Partial extraction for dataset {dataset_id}")
    else:
        record["status"] = "unparseable"
        logger.warning(f"Failed to extract parameters for dataset {dataset_id}")

    return record

def main():
    """
    Main entry point to process all filtered datasets.
    """
    if not RAW_DATA_PATH.exists():
        logger.error(f"Raw data file not found: {RAW_DATA_PATH}")
        sys.exit(1)

    logger.info(f"Loading raw data from {RAW_DATA_PATH}")
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        datasets = json.load(f)

    records = []
    for entry in datasets:
        try:
            record = parse_publication_data(entry)
            records.append(record)
        except Exception as e:
            logger.error(f"Error processing dataset {entry.get('dataset_id')}: {e}")
            # Add a failure record
            records.append({
                "dataset_id": entry.get("dataset_id"),
                "sample_size": None,
                "effect_size": None,
                "metric_type": None,
                "degrees_of_freedom": None,
                "source_url": entry.get("publication_link") or entry.get("doi"),
                "status": "error"
            })

    # Ensure output directory exists
    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving {len(records)} records to {PROCESSED_DATA_PATH}")
    with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    logger.info("Processing complete.")

if __name__ == "__main__":
    main()