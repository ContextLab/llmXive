"""
arXiv PDF Extractor for Ball Milling Data.

Searches arXiv for ball milling papers, downloads PDFs, and extracts
particle size distribution (D10, D50, D90) data from tables.

Output: data/raw/arxiv_tables.json
"""
import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import logger from the existing utility
from src.utils.logger import get_module_logger
from src.utils.seed import get_seed

# Set up logging
logger = get_module_logger(__name__)

# Constants
ARXIV_CATEGORY = "cond-mat.mtrl-sci"
SEARCH_QUERY = f"cat:{ARXIV_CATEGORY} AND ball milling"
MAX_RESULTS = 50
OUTPUT_PATH = Path("data/raw/arxiv_tables.json")
PDF_DOWNLOAD_DIR = Path("data/raw/arxiv_pdfs")

# Regex pattern for D-values
D_VALUE_PATTERN = re.compile(r'D(\d+)[\s:]*([0-9]+(?:\.[0-9]+)?)', re.IGNORECASE)

def setup_directories():
    """Ensure output directories exist."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PDF_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

def search_arxiv_papers(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Search arXiv for papers matching the query.
    
    Uses the arxiv Python package to search.
    """
    try:
        import arxiv
    except ImportError:
        logger.error("The 'arxiv' package is not installed. Please install it via 'pip install arxiv'.")
        raise

    logger.info(f"Searching arXiv for: {query}")
    
    # Search with relevance sorting
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending
    )
    
    papers = []
    count = 0
    for result in search.results():
        if count >= max_results:
            break
        
        # Extract relevant metadata
        paper_info = {
            "arxiv_id": result.entry_id.split("/")[-1], # e.g., 2301.12345
            "title": result.title,
            "published": result.published.isoformat() if result.published else None,
            "authors": [author.name for author in result.authors[:5]], # Limit authors
            "summary": result.summary,
            "pdf_url": result.pdf_url,
            "downloaded_pdf_path": None
        }
        papers.append(paper_info)
        count += 1
    
    logger.info(f"Found {count} papers from arXiv search.")
    return papers

def download_pdf(pdf_url: str, paper_id: str) -> Optional[Path]:
    """
    Download a PDF from arXiv URL.
    
    Returns the path to the downloaded file, or None if failed.
    """
    import requests
    
    output_path = PDF_DOWNLOAD_DIR / f"{paper_id}.pdf"
    if output_path.exists():
        logger.debug(f"PDF already exists: {output_path}")
        return output_path

    try:
        logger.info(f"Downloading PDF for {paper_id}...")
        response = requests.get(pdf_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"PDF downloaded successfully: {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"Failed to download PDF for {paper_id}: {e}")
        return None

def extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
    """
    Extract text from a PDF using pdfminer.six.
    
    Returns the extracted text or None if failed.
    """
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        logger.error("The 'pdfminer.six' package is not installed.")
        raise

    try:
        logger.debug(f"Extracting text from {pdf_path}")
        text = extract_text(str(pdf_path))
        return text
    except Exception as e:
        logger.warning(f"Failed to extract text from {pdf_path}: {e}")
        return None

def parse_d_values(text: str) -> List[Dict[str, float]]:
    """
    Scan text for D10, D50, D90 values using regex.
    
    Returns a list of dicts with d10, d50, d90 keys.
    """
    matches = D_VALUE_PATTERN.findall(text)
    if not matches:
        return []
    
    # Parse matches: (digit, value_str)
    parsed_values = {}
    for digit_str, value_str in matches:
        try:
            digit = int(digit_str)
            value = float(value_str)
            # We are looking for D10, D50, D90 specifically
            if digit in [10, 50, 90]:
                parsed_values[digit] = value
        except ValueError:
            continue
    
    # If we found at least one, return it as a row (might be partial)
    # The task implies extracting rows. If multiple D-values are on one line,
    # we map them. Here we aggregate found values for the paper.
    if parsed_values:
        return [parsed_values]
    
    return []

def extract_psd_from_arxiv(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of arXiv papers to extract PSD data.
    
    Returns a list of extracted records with source_name and source_id.
    """
    extracted_data = []
    
    for paper in papers:
        paper_id = paper["arxiv_id"]
        pdf_path = paper.get("downloaded_pdf_path")
        
        if not pdf_path or not pdf_path.exists():
            continue
        
        text = extract_text_from_pdf(pdf_path)
        if not text:
            continue
        
        d_values = parse_d_values(text)
        
        for d_row in d_values:
            # Mandatory: source_name and source_id
            record = {
                "source_name": "arXiv",
                "source_id": paper_id,
                "title": paper["title"],
                "d10": d_row.get(10),
                "d50": d_row.get(50),
                "d90": d_row.get(90),
                "material_type": None, # Not always available in abstract
                "milling_speed": None,
                "milling_time": None,
                "ball_to_powder_ratio": None,
                "youngs_modulus": None,
                "density": None,
                "process_duration": None
            }
            
            # CRITICAL: Filter out rows without source_id (already ensured by loop, but explicit check)
            if not record["source_id"]:
                logger.warning(f"Row filtered: missing source_id for paper {paper_id}")
                continue
            
            extracted_data.append(record)
    
    return extracted_data

def save_to_json(data: List[Dict[str, Any]], output_path: Path):
    """Save extracted data to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} records to {output_path}")

def run_arxiv_ingestion():
    """
    Main entry point for arXiv ingestion.
    
    1. Search arXiv.
    2. Download PDFs.
    3. Extract text and parse D-values.
    4. Save to JSON.
    """
    setup_directories()
    
    # Search
    papers = search_arxiv_papers(SEARCH_QUERY, MAX_RESULTS)
    
    if not papers:
        logger.warning("Source skipped: arXiv (no results found)")
        # Still create an empty file to satisfy the "file exists" check if needed,
        # but the task says "at least one row" is verification.
        # If no results, we cannot fake data. We save empty list.
        save_to_json([], OUTPUT_PATH)
        return

    # Download and Extract
    for paper in papers:
        pdf_path = download_pdf(paper["pdf_url"], paper["arxiv_id"])
        if pdf_path:
            paper["downloaded_pdf_path"] = pdf_path
    
    extracted_data = extract_psd_from_arxiv(papers)
    
    # CRITICAL: Verify traceability before saving
    valid_data = []
    for row in extracted_data:
        if row.get("source_name") and row.get("source_id"):
            valid_data.append(row)
        else:
            logger.warning(f"Row filtered: missing traceability metadata: {row}")
    
    logger.info(f"Total valid rows extracted: {len(valid_data)}")
    
    if len(valid_data) == 0:
        logger.warning("Source skipped: arXiv (no valid rows extracted)")
    
    save_to_json(valid_data, OUTPUT_PATH)

if __name__ == "__main__":
    run_arxiv_ingestion()
