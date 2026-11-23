"""
T013b: Implement arXiv PDF extractor for ball milling data.
Fetches papers from arXiv, downloads PDFs, and extracts PSD metrics (D10, D50, D90).
"""
import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import arxiv
from pdfminer.high_level import extract_text
from tqdm import tqdm

# Import from project utils
from src.utils.logger import get_module_logger
from src.utils.seed import get_seed

logger = get_module_logger("arxiv_extractor")

# Configuration
SEARCH_CATEGORY = "cond-mat.mtrl-sci"
SEARCH_QUERY = f"cat:{SEARCH_CATEGORY} AND ball milling"
BATCH_SIZE = 50
MAX_EXPERIMENTS_PER_SOURCE = 500
OUTPUT_PATH = Path("data/raw/arxiv_tables.json")
FLAGGED_OUTPUT_PATH = Path("data/flagged_psd.json")

def setup_directories() -> None:
    """Ensure output directories exist."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FLAGGED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def search_arxiv_papers(start_index: int = 0) -> List[arxiv.Result]:
    """
    Search arXiv for papers matching the query.
    Returns a list of results.
    """
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=SEARCH_QUERY,
            max_results=BATCH_SIZE,
            start=start_index,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending
        )
        results = list(client.results(search))
        return results
    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        return []

def download_pdf(paper: arxiv.Result, download_dir: Path) -> Optional[Path]:
    """
    Download the PDF for a given paper.
    Returns the path to the downloaded file, or None if failed.
    """
    try:
        pdf_path = download_dir / f"{paper.arxiv_id.replace('/', '_')}.pdf"
        if not pdf_path.exists():
            paper.download_pdf(filename=pdf_path)
        return pdf_path
    except Exception as e:
        logger.warning(f"Failed to download PDF for {paper.arxiv_id}: {e}")
        return None

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from a PDF file."""
    try:
        return extract_text(str(pdf_path))
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""

def parse_d_values(text: str) -> Dict[str, float]:
    """
    Scan text for D10, D50, D90 values.
    Uses regex to find patterns like 'D10: 100 um' or 'd50=500'.
    """
    d_values = {}
    # Pattern: D followed by 2 digits, optional colon/space, number (int or float), optional unit
    pattern = r"D(\d{2})[\s:]*([0-9]+(?:\.[0-9]+)?)(?:\s*(?:um|µm|µ|micron|micrometers|meters|m)?)?"
    
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    for match in matches:
        d_key = f"d{match[0]}"
        try:
            value = float(match[1])
            # Basic validation: PSD values should be positive
            if value > 0:
                d_values[d_key] = value
        except ValueError:
            continue
    
    return d_values

def extract_psd_from_arxiv(paper: arxiv.Result, download_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Extract PSD data from a single arXiv paper.
    Returns a dict with experiment data or None if extraction fails.
    """
    pdf_path = download_pdf(paper, download_dir)
    if not pdf_path:
        return None

    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    d_vals = parse_d_values(text)
    
    # We need at least one D value to consider this a valid extraction
    if not d_vals:
        return None

    # Construct the record
    # Note: arXiv papers often lack specific milling parameters like speed/time in structured tables.
    # We extract what we can and leave others as None/NaN for later imputation.
    record = {
        "experiment_id": f"arxiv_{paper.arxiv_id.replace('/', '_')}",
        "source_name": "arXiv",
        "source_id": paper.arxiv_id,
        "milling_speed": None,
        "milling_time": None,
        "ball_to_powder_ratio": None,
        "youngs_modulus": None,
        "density": None,
        "d10": d_vals.get("d10"),
        "d50": d_vals.get("d50"),
        "d90": d_vals.get("d90"),
        "material_type": None,
        "process_duration": None
    }
    
    # Flag if source_id is missing (though arxiv_id is always present)
    if not record["source_id"]:
        logger.warning(f"Row flagged: missing source_id for {record['experiment_id']}")
    
    return record

def save_to_json(data: List[Dict], path: Path) -> None:
    """Save extracted data to a JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} records to {path}")

def run_arxiv_ingestion() -> List[Dict[str, Any]]:
    """
    Main ingestion loop for arXiv.
    Fetches papers in batches until target is met or source exhausted.
    """
    setup_directories()
    
    download_dir = Path("data/raw/arxiv_downloads")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    all_records = []
    start_index = 0
    flagged_entries = []

    logger.info(f"Starting arXiv ingestion with query: {SEARCH_QUERY}")

    while len(all_records) < MAX_EXPERIMENTS_PER_SOURCE:
        logger.info(f"Fetching batch starting at index {start_index}...")
        papers = search_arxiv_papers(start_index)
        
        if not papers:
            logger.warning("Source skipped: arXiv (no results found)")
            break

        logger.info(f"Retrieved {len(papers)} papers.")
        
        batch_records = []
        for paper in tqdm(papers, desc="Processing papers"):
            record = extract_psd_from_arxiv(paper, download_dir)
            if record:
                batch_records.append(record)
                # Check for missing source_id (should not happen with arXiv, but for safety)
                if not record.get("source_id"):
                    flagged_entries.append({
                        "experiment_id": record.get("experiment_id", "unknown"),
                        "source": "arXiv",
                        "issue_type": "missing_source_id",
                        "raw_blob_hash": hashlib.md5(json.dumps(record).encode()).hexdigest()
                    })

        all_records.extend(batch_records)
        
        # If we got no new records in this batch, we might be exhausted
        if not batch_records and len(papers) > 0:
            logger.info("No more valid records found in this batch. Stopping.")
            break
        
        start_index += BATCH_SIZE
        
        # Small delay to be polite to the API
        time.sleep(0.5)

    if not all_records:
        logger.warning("Source skipped: arXiv (no rows extracted)")
    else:
        logger.info(f"Successfully extracted {len(all_records)} experiments from arXiv.")
        save_to_json(all_records, OUTPUT_PATH)

    # Save flagged entries if any
    if flagged_entries:
        logger.info(f"Saving {len(flagged_entries)} flagged entries.")
        # Append to existing flagged file if it exists, or create new
        existing_flagged = []
        if FLAGGED_OUTPUT_PATH.exists():
            try:
                with open(FLAGGED_OUTPUT_PATH, 'r') as f:
                    existing_flagged = json.load(f)
            except json.JSONDecodeError:
                existing_flagged = []
        
        combined_flagged = existing_flagged + flagged_entries
        save_to_json(combined_flagged, FLAGGED_OUTPUT_PATH)

    return all_records

def main():
    """Entry point for the script."""
    logger.info("Running arXiv ingestion pipeline...")
    run_arxiv_ingestion()
    logger.info("ArXiv ingestion complete.")

if __name__ == "__main__":
    main()