"""
Implements the arXiv PDF extractor for ball milling data.
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
from pdfminer.layout import LAParams

# Import the correct logger function from the API surface
from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# Constants
ARXIV_CATEGORY = "cond-mat.mtrl-sci"
SEARCH_QUERY = "ball milling"
MAX_RESULTS = 50
OUTPUT_PATH = Path("data/raw/arxiv_tables.json")
TEMP_DIR = Path("data/raw/temp_pdfs")

def _ensure_dirs():
    """Ensure output directories exist."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def _download_pdf(entry: arxiv.Result, dest_path: Path) -> bool:
    """
    Downloads the PDF for a given arXiv entry.
    Returns True if successful, False otherwise.
    """
    try:
        # Download to a temporary file first to avoid partial writes
        download_path = entry.download_pdf(dirpath=dest_path, filename=f"{entry.entry_id.split('/')[-1]}.pdf")
        return download_path.exists()
    except Exception as e:
        logger.warning(f"Failed to download PDF for {entry.entry_id}: {e}")
        return False

def _extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts text from a PDF file using pdfminer.six."""
    try:
        laparams = LAParams(
            line_margin=0.2,
            word_margin=0.1,
            char_margin=2.0,
            detect_vertical=True,
            all_texts=True
        )
        text = extract_text(str(pdf_path), laparams=laparams)
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""

def _parse_d_values(text: str) -> Dict[str, float]:
    """
    Scans text for D10, D50, D90 values.
    Returns a dict with found values.
    """
    d_values = {}
    # Regex to find D followed by number (10, 50, 90) and a value
    # Matches patterns like "D10: 1.2", "D10 = 1.2", "D10 1.2"
    pattern = r"D(10|50|90)[\s:=]*([0-9]+(?:\.[0-9]+)?)"
    
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    for match in matches:
        d_type = match[0]
        try:
            value = float(match[1])
            d_values[f"D{d_type}"] = value
        except ValueError:
            continue
    
    return d_values

def _extract_rows_from_text(text: str, entry_id: str) -> List[Dict[str, Any]]:
    """
    Extracts potential data rows from the text of a paper.
    Looks for tables or lists containing D10, D50, D90.
    """
    rows = []
    lines = text.split('\n')
    
    # Simple heuristic: look for lines containing multiple D-values
    # or lines that look like table rows with numbers
    for line in lines:
        # Skip very short lines or headers
        if len(line.strip()) < 10:
            continue
        
        # Check for D-values in this line
        d_vals = _parse_d_values(line)
        if len(d_vals) >= 1:
            # Found at least one D-value
            row = {
                "source_name": "arXiv",
                "source_id": entry_id,
                "raw_text_snippet": line.strip()[:200] # Store context
            }
            row.update(d_vals)
            rows.append(row)
    
    return rows

def extract_psd_from_arxiv() -> List[Dict[str, Any]]:
    """
    Main function to search arXiv, download PDFs, and extract data.
    Returns a list of extracted data rows.
    """
    _ensure_dirs()
    all_rows = []
    
    logger.info(f"Searching arXiv for '{SEARCH_QUERY}' in category '{ARXIV_CATEGORY}'...")
    
    try:
        search = arxiv.Search(
            query=SEARCH_QUERY,
            max_results=MAX_RESULTS,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending,
            id_list=[] # Not filtering by ID, just query
        )
        
        # Add category filter if possible (arxiv package query syntax)
        # The query string is usually sufficient, but we can refine
        search = arxiv.Search(
            query=f"cat:{ARXIV_CATEGORY} AND {SEARCH_QUERY}",
            max_results=MAX_RESULTS,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending
        )

        results = list(search.results())
        
        if not results:
            logger.warning("Source skipped: arXiv (no results found)")
            return []
        
        logger.info(f"Found {len(results)} papers. Processing...")
        
        for i, entry in enumerate(results):
            entry_id = entry.entry_id.split('/')[-1] # e.g., 2301.12345
            logger.info(f"Processing paper {i+1}/{len(results)}: {entry_id}")
            
            # Download PDF
            pdf_filename = f"{entry_id}.pdf"
            pdf_path = TEMP_DIR / pdf_filename
            
            if not _download_pdf(entry, TEMP_DIR):
                continue
            
            # Extract text
            text = _extract_text_from_pdf(pdf_path)
            if not text:
                continue
            
            # Parse D-values
            rows = _extract_rows_from_text(text, entry_id)
            
            # Filter rows that lack source_id (should not happen here, but for safety)
            valid_rows = [r for r in rows if r.get("source_id")]
            
            if valid_rows:
                all_rows.extend(valid_rows)
                logger.info(f"  -> Extracted {len(valid_rows)} potential data points.")
            else:
                logger.debug(f"  -> No D-values found in {entry_id}.")
            
            # Clean up PDF to save space
            if pdf_path.exists():
                pdf_path.unlink()
            
            # Small delay to be nice to the server
            time.sleep(0.5)
            
    except Exception as e:
        logger.error(f"Error during arXiv extraction: {e}")
        raise
    
    return all_rows

def save_to_json(data: List[Dict[str, Any]], output_path: Path):
    """Saves data to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} rows to {output_path}")

def run_arxiv_ingestion():
    """
    Entry point for the ingestion pipeline.
    """
    try:
        data = extract_psd_from_arxiv()
        
        if not data:
            logger.warning("Source skipped: arXiv (no rows extracted)")
            # Even if empty, we might want to create an empty file or skip?
            # The task says: "Output: data/raw/arxiv_tables.json". 
            # If no rows, we still write an empty list to be consistent.
            save_to_json([], OUTPUT_PATH)
            return
        
        save_to_json(data, OUTPUT_PATH)
        
    except Exception as e:
        logger.error(f"ArXiv ingestion failed: {e}")
        raise

if __name__ == "__main__":
    run_arxiv_ingestion()
