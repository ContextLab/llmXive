"""
ArXiv PDF Extractor for Ball Milling PSD Data.

This module implements the extraction of Particle Size Distribution (PSD) data
from ArXiv PDFs. It uses pdfminer.six to parse text and tables, and includes
logic to detect unstructured data (images/curves) for potential OCR fallback.

Per FR-008, unstructured entries are flagged to data/flagged_psd.json with
the required schema.
"""

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LAParams, LTTextContainer, LTImage, LTChar
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage

from src.exceptions import DataIngestionError, DataFormatError, InsufficientDataError
from src.utils.error_handler import handle_ingestion_errors

# Configure logging
logger = logging.getLogger(__name__)

# Constants
FLAGGED_PSD_PATH = Path("data/flagged_psd.json")
ARXIV_API_BASE = "https://export.arxiv.org/api/query"
ARXIV_SEARCH_SIZE = 10  # Number of papers to fetch initially for this task

# Regex patterns for extracting potential numeric PSD data from text
PSD_PATTERNS = [
    r"D\d+\s*[:=]?\s*([\d.]+)\s*(?:μm|um|mm|nm)",
    r"particle size\s*[:=]?\s*([\d.]+)\s*(?:μm|um|mm|nm)",
    r"mean size\s*[:=]?\s*([\d.]+)\s*(?:μm|um|mm|nm)",
    r"[\d.]+\s*μm\s*[-–]\s*[\d.]+\s*μm",  # Range
]

def _hash_bytes(data: bytes) -> str:
    """Generate a SHA-256 hash for raw blob identification."""
    return hashlib.sha256(data).hexdigest()

def _load_flagged_entries() -> List[Dict[str, Any]]:
    """Load existing flagged entries from JSON."""
    if not FLAGGED_PSD_PATH.exists():
        return []
    try:
        with open(FLAGGED_PSD_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load flagged entries: {e}")
        return []

def _save_flagged_entries(entries: List[Dict[str, Any]]) -> None:
    """Save flagged entries to JSON."""
    FLAGGED_PSD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FLAGGED_PSD_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)

def _flag_unstructured_entry(
    experiment_id: str,
    source: str,
    issue_type: str,
    raw_blob_hash: str
) -> None:
    """
    Flag an entry as unstructured in data/flagged_psd.json.

    Schema: experiment_id, source, issue_type, raw_blob_hash
    """
    entries = _load_flagged_entries()
    new_entry = {
        "experiment_id": experiment_id,
        "source": source,
        "issue_type": issue_type,
        "raw_blob_hash": raw_blob_hash
    }
    # Avoid duplicates
    if not any(e["experiment_id"] == new_entry["experiment_id"] for e in entries):
        entries.append(new_entry)
        _save_flagged_entries(entries)
        logger.info(f"Flagged unstructured entry: {experiment_id} ({issue_type})")

def _extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract raw text from a PDF using pdfminer.six."""
    try:
        text = extract_text(str(pdf_path), laparams=LAParams())
        return text
    except Exception as e:
        raise DataFormatError(f"Failed to extract text from {pdf_path}: {e}")

def _detect_images_in_pdf(pdf_path: Path) -> List[LTImage]:
    """
    Detect images in a PDF. This is a heuristic for unstructured PSD curves.
    Returns a list of image objects found.
    """
    images = []
    try:
        rsrcmgr = PDFResourceManager()
        retstr = ""
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        with open(pdf_path, 'rb') as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            pages = PDFPage.create_pages(doc)

            for page in pages:
                interpreter.process_page(page)
                layout = device.get_result()
                for element in layout:
                    if isinstance(element, LTImage):
                        images.append(element)
    except Exception as e:
        logger.warning(f"Error detecting images in {pdf_path}: {e}")
    
    return images

def _parse_psd_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to parse PSD metrics from extracted text using regex.
    Returns a dict if found, None otherwise.
    """
    for pattern in PSD_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Simple heuristic: return the first match as a potential D50
            # In a full implementation, we would try to distinguish D10/D50/D90
            return {
                "raw_text_match": matches[0],
                "source": "text_extraction",
                "confidence": "low"
            }
    return None

def _fetch_arxiv_papers(query: str = "ball milling particle size", max_results: int = ARXIV_SEARCH_SIZE) -> List[Dict[str, str]]:
    """
    Fetch paper IDs and PDF URLs from ArXiv API.
    Note: This is a simplified fetcher. In production, handle pagination and rate limits.
    """
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET

    query = urllib.parse.quote(query)
    url = f"{ARXIV_API_BASE}?search_query=all:{query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
            root = ET.fromstring(data)
            namespace = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
            
            papers = []
            for entry in root.findall('atom:entry', namespace):
                id_elem = entry.find('atom:id', namespace)
                title_elem = entry.find('atom:title', namespace)
                if id_elem is not None:
                    papers.append({
                        "arxiv_id": id_elem.text.split("/")[-1],
                        "title": title_elem.text.strip() if title_elem is not None else "Unknown",
                        "pdf_url": id_elem.text.replace("abs", "pdf")
                    })
            return papers
    except Exception as e:
        raise SourceConnectionError(f"Failed to fetch ArXiv papers: {e}")

def _download_pdf(pdf_url: str, dest_dir: Path) -> Path:
    """Download a PDF from a URL to a local directory."""
    import urllib.request
    
    filename = f"arxiv_{hashlib.md5(pdf_url.encode()).hexdigest()}.pdf"
    dest_path = dest_dir / filename
    
    try:
        urllib.request.urlretrieve(pdf_url, str(dest_path))
        return dest_path
    except Exception as e:
        raise SourceConnectionError(f"Failed to download PDF from {pdf_url}: {e}")

@handle_ingestion_errors
def extract_psd_from_arxiv(
    output_dir: Optional[Path] = None,
    query: str = "ball milling particle size",
    max_papers: int = 5
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Main entry point for T014.
    
    1. Fetches ArXiv papers matching the query.
    2. Downloads PDFs.
    3. Extracts text and detects images (unstructured data).
    4. Parses text for PSD metrics.
    5. Flags unstructured entries (images) to data/flagged_psd.json.
    
    Returns:
        Tuple of (list of extracted records, count of flagged entries)
    """
    if output_dir is None:
        output_dir = Path("data/raw/arxiv")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching ArXiv papers with query: {query}")
    papers = _fetch_arxiv_papers(query, max_results=max_papers)
    
    if not papers:
        logger.warning("No papers found matching the query.")
        return [], 0

    extracted_records = []
    flagged_count = 0

    for paper in papers:
        paper_id = paper["arxiv_id"]
        logger.info(f"Processing paper: {paper_id}")
        
        try:
            # Download PDF
            pdf_path = _download_pdf(paper["pdf_url"], output_dir)
            raw_hash = _hash_bytes(open(pdf_path, "rb").read())
            
            # 1. Extract Text
            text = _extract_text_from_pdf(pdf_path)
            
            # 2. Detect Images (Unstructured Data)
            images = _detect_images_in_pdf(pdf_path)
            
            record = {
                "source": "arxiv",
                "experiment_id": f"arxiv_{paper_id}",
                "title": paper["title"],
                "pdf_hash": raw_hash,
                "text_content": text[:1000], # Store snippet
                "has_images": len(images) > 0,
                "image_count": len(images),
                "status": "processed"
            }

            # 3. Parse Text for PSD
            psd_data = _parse_psd_from_text(text)
            if psd_data:
                record["psd_metrics"] = psd_data
            else:
                record["psd_metrics"] = None
                record["status"] = "no_psd_found_in_text"

            # 4. Handle Unstructured Data (Images) per FR-008
            if images:
                logger.warning(f"Detected {len(images)} images in {paper_id}. Flagging for OCR fallback.")
                _flag_unstructured_entry(
                    experiment_id=record["experiment_id"],
                    source="arxiv",
                    issue_type="unstructured_psd_image",
                    raw_blob_hash=raw_hash
                )
                flagged_count += 1
                record["status"] = "flagged_unstructured"

            extracted_records.append(record)

        except Exception as e:
            logger.error(f"Error processing paper {paper_id}: {e}")
            # Continue processing other papers
            continue

    return extracted_records, flagged_count

def run_arxiv_ingestion():
    """CLI entry point for T014."""
    logger.info("Starting ArXiv PDF extraction (T014)...")
    try:
        records, flagged = extract_psd_from_arxiv(max_papers=10)
        logger.info(f"Extraction complete. Found {len(records)} records, {flagged} flagged for OCR.")
        
        # Save raw extraction result to a JSON file for downstream processing
        output_file = Path("data/processed/arxiv_extracted.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        
        logger.info(f"Saved extracted records to {output_file}")
        
        if flagged > 0:
            logger.info(f"Flagged entries saved to {FLAGGED_PSD_PATH}")
            
    except Exception as e:
        logger.critical(f"ArXiv ingestion failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_arxiv_ingestion()
