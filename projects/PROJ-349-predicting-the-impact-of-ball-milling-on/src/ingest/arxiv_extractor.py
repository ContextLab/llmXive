"""
arXiv PDF extractor for ball milling data.

Searches arXiv for papers in cond-mat.mtrl-sci related to ball milling,
downloads PDFs, and extracts PSD tables (D10, D50, D90) using pdfminer.six.
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
from pdfminer.layout import LAParams

# Add src to path for imports if running as script
if __name__ == "__main__" and "code" not in os.getcwd():
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.logger import get_module_logger
from src.utils.seed import get_seed

logger = get_module_logger(__name__)

# Configuration
ARXIV_CATEGORY = "cond-mat.mtrl-sci"
SEARCH_QUERY = "ball milling"
MAX_RESULTS = 50  # Limit corpus for representative subset
OUTPUT_PATH = Path("data/raw/arxiv_tables.json")
TIMEOUT_SECONDS = 300  # Max runtime for the whole ingestion


def search_arxiv_papers(query: str, category: str, max_results: int) -> List[arxiv.Result]:
    """
    Search arXiv for papers matching the query and category.
    
    Args:
        query: Search query string
        category: arXiv category (e.g., 'cond-mat.mtrl-sci')
        max_results: Maximum number of results to fetch
        
    Returns:
        List of arxiv.Result objects
    """
    logger.info(f"Searching arXiv for '{query}' in category '{category}'...")
    
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=f"cat:{category} AND all:{query}",
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = list(client.results(search))
        logger.info(f"Found {len(results)} papers from arXiv search.")
        
        if len(results) == 0:
            logger.warning("Source skipped: arXiv (no results found)")
            return []
        
        return results
        
    except Exception as e:
        logger.warning(f"Source skipped: arXiv (error during search: {e})")
        return []


def download_pdf(result: arxiv.Result, output_dir: Path) -> Optional[Path]:
    """
    Download PDF for a given arXiv result.
    
    Args:
        result: arxiv.Result object
        output_dir: Directory to save the PDF
        
    Returns:
        Path to downloaded PDF or None if failed
    """
    try:
        # Download the PDF
        pdf_path = result.download_pdf(dirpath=output_dir, filename=f"{result.entry_id}.pdf")
        logger.debug(f"Downloaded PDF: {pdf_path}")
        return pdf_path
    except Exception as e:
        logger.warning(f"Failed to download PDF for {result.entry_id}: {e}")
        return None


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from a PDF file using pdfminer.six.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text string
    """
    try:
        text = extract_text(
            pdf_path,
            laparams=LAParams(
                detect_vertical=True,
                line_overlap=0.5,
                char_margin=2.0,
                line_margin=0.5,
                word_margin=0.1
            )
        )
        return text
    except Exception as e:
        logger.warning(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def parse_tables_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse potential PSD data from extracted text.
    
    Looks for patterns containing D10, D50, D90 values.
    
    Args:
        text: Extracted text from PDF
        
    Returns:
        List of dictionaries with extracted PSD values
    """
    extracted_data = []
    
    # Pattern to match D-values: D10: 12.5, D50: 45.2, etc.
    # Also handles formats like "D10 = 12.5" or "D10 12.5"
    d10_pattern = re.compile(r'D10[\s:=]+([0-9]+(?:\.[0-9]+)?)', re.IGNORECASE)
    d50_pattern = re.compile(r'D50[\s:=]+([0-9]+(?:\.[0-9]+)?)', re.IGNORECASE)
    d90_pattern = re.compile(r'D90[\s:=]+([0-9]+(?:\.[0-9]+)?)', re.IGNORECASE)
    
    # Also check for material type or milling parameters if available in context
    material_pattern = re.compile(r'material[:\s]+([A-Za-z0-9\s\-]+?)(?:\s+at\s+|\.|\,|;)', re.IGNORECASE)
    speed_pattern = re.compile(r'milling\s+speed[:\s]+([0-9]+(?:\.[0-9]+)?\s*(?:rpm|rpm))', re.IGNORECASE)
    time_pattern = re.compile(r'milling\s+time[:\s]+([0-9]+(?:\.[0-9]+)?\s*(?:h|hours?|min|minutes?))', re.IGNORECASE)
    
    # Find all matches
    d10_matches = d10_pattern.findall(text)
    d50_matches = d50_pattern.findall(text)
    d90_matches = d90_pattern.findall(text)
    
    if not (d10_matches or d50_matches or d90_matches):
        return []
    
    # Try to extract material, speed, time from nearby context
    material_matches = material_pattern.findall(text)
    speed_matches = speed_pattern.findall(text)
    time_matches = time_pattern.findall(text)
    
    # Create records for each set of D-values found
    # If multiple D10/D50/D90 sets are found, we'll create multiple records
    # For simplicity, we'll combine them into one record if they appear in the same context
    record = {
        "d10": float(d10_matches[0]) if d10_matches else None,
        "d50": float(d50_matches[0]) if d50_matches else None,
        "d90": float(d90_matches[0]) if d90_matches else None,
        "material_type": material_matches[0].strip() if material_matches else None,
        "milling_speed": speed_matches[0].strip() if speed_matches else None,
        "milling_time": time_matches[0].strip() if time_matches else None
    }
    
    # Only add if we have at least one valid D-value
    if record["d10"] or record["d50"] or record["d90"]:
        extracted_data.append(record)
    
    return extracted_data


def extract_psd_from_arxiv(paper_id: str) -> List[Dict[str, Any]]:
    """
    Extract PSD data from a single arXiv paper.
    
    Args:
        paper_id: arXiv paper ID (e.g., '2301.12345')
        
    Returns:
        List of dictionaries with extracted data including source metadata
    """
    # Search for the specific paper
    client = arxiv.Client()
    try:
        search = arxiv.Search(id_list=[paper_id])
        results = list(client.results(search))
        
        if not results:
            logger.warning(f"Paper {paper_id} not found on arXiv")
            return []
        
        result = results[0]
        
        # Download PDF
        pdf_path = download_pdf(result, Path("data/raw"))
        if not pdf_path:
            return []
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        # Parse tables
        data_records = parse_tables_from_text(text)
        
        # Enrich with source metadata
        enriched_records = []
        for record in data_records:
            enriched_record = {
                "source_name": "arXiv",
                "source_id": result.entry_id.split("/")[-1],  # e.g., "2301.12345"
                "arxiv_id": result.entry_id,
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "published": result.published.isoformat() if result.published else None,
                **record
            }
            enriched_records.append(enriched_record)
        
        # Clean up PDF
        try:
            os.remove(pdf_path)
        except OSError:
            pass
        
        return enriched_records
        
    except Exception as e:
        logger.warning(f"Failed to extract data from paper {paper_id}: {e}")
        return []

def run_arxiv_ingestion() -> List[Dict[str, Any]]:
    """
    Run the full arXiv ingestion pipeline.
    
    Returns:
        List of all extracted records
    """
    logger.info("Starting arXiv ingestion pipeline...")
    
    # Search for papers
    papers = search_arxiv_papers(SEARCH_QUERY, ARXIV_CATEGORY, MAX_RESULTS)
    
    if not papers:
        return []
    
    all_records = []
    start_time = time.time()
    
    for i, paper in enumerate(papers):
        # Check timeout
        if time.time() - start_time > TIMEOUT_SECONDS:
            logger.warning("Timeout reached, stopping arXiv ingestion")
            break
        
        logger.info(f"Processing paper {i+1}/{len(papers)}: {paper.entry_id}")
        
        records = extract_psd_from_arxiv(paper.entry_id.split("/")[-1])
        all_records.extend(records)
        
        # Small delay to be polite to the API
        time.sleep(0.5)
    
    logger.info(f"ArXiv ingestion complete. Extracted {len(all_records)} records.")
    
    # Filter out records without source_id (shouldn't happen, but safety check)
    valid_records = [r for r in all_records if r.get("source_id")]
    skipped_count = len(all_records) - len(valid_records)
    if skipped_count > 0:
        logger.warning(f"Filtered out {skipped_count} records missing source_id")
    
    return valid_records

def save_to_json(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save extracted data to JSON file.
    
    Args:
        data: List of dictionaries to save
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Saved {len(data)} records to {output_path}")

def main():
    """Main entry point for arXiv ingestion."""
    logger.info("=== arXiv Ingestion Pipeline ===")
    
    # Run ingestion
    records = run_arxiv_ingestion()
    
    if not records:
        logger.warning("No records extracted from arXiv")
        # Create empty output file to indicate completion
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return
    
    # Save results
    save_to_json(records, OUTPUT_PATH)
    
    logger.info("=== arXiv Ingestion Complete ===")

if __name__ == "__main__":
    main()