import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure, LTImage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ARXIV_API_URL = "https://export.arxiv.org/api/query"
FLAGGED_FILE = Path("data/flagged_psd.json")
RAW_DIR = Path("data/raw")
SEARCH_QUERY_TEMPLATE = "ball milling particle size distribution"
MAX_RESULTS = 10  # Limit for initial extraction to avoid overwhelming

def _calculate_hash(data: bytes) -> str:
    """Calculate SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()

def _search_arxiv(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search arXiv API for relevant papers."""
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    try:
        response = requests.get(ARXIV_API_URL, params=params, timeout=30)
        response.raise_for_status()
        # Parse XML response (simplified for this context, usually uses feedparser)
        # For robustness, we assume the response contains entry IDs and PDF links
        # In a full implementation, we would parse the Atom feed properly.
        # Here we mock the parsing structure based on standard arXiv API responses.
        # Since we can't import feedparser without adding it, we use regex on the raw text
        # to extract IDs and links for the purpose of this implementation.
        content = response.text
        entries = []
        # Extract IDs
        id_matches = re.findall(r'<id>http://arxiv.org/abs/(.*?)</id>', content)
        # Extract links (PDF)
        link_matches = re.findall(r'<link href="(.*?\.pdf)"', content)
        
        # Map them (assuming order matches)
        for i, id_val in enumerate(id_matches):
            entries.append({
                "id": id_val,
                "pdf_url": link_matches[i] if i < len(link_matches) else None,
                "title": "Unknown Title" # Placeholder, parsing title requires more regex
            })
        return entries
    except Exception as e:
        logger.error(f"Failed to search arXiv: {e}")
        return []

def _download_pdf(pdf_url: str, save_path: Path) -> bool:
    """Download PDF from URL."""
    if not pdf_url:
        return False
    try:
        response = requests.get(pdf_url, stream=True, timeout=60)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download PDF {pdf_url}: {e}")
        return False

def _detect_psd_images(layout_pages: List) -> List[Dict[str, Any]]:
    """
    Detect potential PSD curves/images in PDF layout.
    Returns list of detected image/figure locations that might contain data.
    """
    detected = []
    for page_num, page_layout in enumerate(layout_pages):
        for element in page_layout:
            # Look for figures or images that might be plots
            if isinstance(element, (LTFigure, LTImage)):
                # Heuristic: Figures with certain dimensions or containing text like "Figure"
                # are likely plots.
                detected.append({
                    "page": page_num,
                    "bbox": element.bbox,
                    "type": "figure",
                    "confidence": "low" # Placeholder for OCR confidence
                })
    return detected

def _extract_text_from_layout(layout_pages: List) -> str:
    """Extract all text content from PDF pages."""
    text_content = []
    for page_layout in layout_pages:
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text_content.append(element.get_text())
    return "\n".join(text_content)

def _parse_psd_metrics(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to parse PSD metrics (D10, D50, D90) from extracted text.
    Returns dict if found, None otherwise.
    """
    # Regex patterns for D10, D50, D90
    # Examples: "D50 = 10.5 µm", "d50: 15.2 um", "particle size (D50): 20"
    patterns = {
        "D10": r"D10\s*[:=\s]+([\d.]+)\s*(?:µm|um|μm|mm|nm)?",
        "D50": r"D50\s*[:=\s]+([\d.]+)\s*(?:µm|um|μm|mm|nm)?",
        "D90": r"D90\s*[:=\s]+([\d.]+)\s*(?:µm|um|μm|mm|nm)?"
    }
    
    metrics = {}
    found_any = False
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                metrics[key] = float(match.group(1))
                found_any = True
            except ValueError:
                continue
    
    if found_any:
        return metrics
    return None

def _flag_unstructured_entry(entry_id: str, source: str, issue_type: str, raw_blob: bytes):
    """
    Flag an entry as unstructured and write to data/flagged_psd.json.
    Schema: experiment_id, source, issue_type, raw_blob_hash
    """
    FLAGGED_FILE.parent.mkdir(parents=True, exist_ok=True)
    raw_hash = _calculate_hash(raw_blob)
    
    new_entry = {
        "experiment_id": entry_id,
        "source": source,
        "issue_type": issue_type,
        "raw_blob_hash": raw_hash
    }
    
    existing = []
    if FLAGGED_FILE.exists():
        try:
            with open(FLAGGED_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = []
    
    # Avoid duplicates
    if not any(e["experiment_id"] == new_entry["experiment_id"] for e in existing):
        existing.append(new_entry)
        with open(FLAGGED_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2)
        logger.info(f"Flagged unstructured entry: {entry_id} -> {FLAGGED_FILE}")

def extract_psd_from_arxiv(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract PSD data from a single arXiv entry.
    Returns a dict with extracted metrics or None if extraction fails.
    If unstructured data is detected, flags it and returns None.
    """
    entry_id = entry["id"]
    pdf_url = entry["pdf_url"]
    
    if not pdf_url:
        logger.warning(f"No PDF URL for entry {entry_id}")
        return None

    pdf_path = RAW_DIR / f"{entry_id}.pdf"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    if not _download_pdf(pdf_url, pdf_path):
        logger.error(f"Could not download PDF for {entry_id}")
        return None

    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        # Initialize PDF parser
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        
        parser = PDFParser(pdf_path)
        document = PDFDocument(parser)
        pages = list(PDFPage.create_pages(document))
        
        layout_pages = []
        for page in pages:
            interpreter.process_page(page)
            layout_pages.append(device.get_result())
        
        # 1. Try to extract text-based metrics
        text_content = _extract_text_from_layout(layout_pages)
        metrics = _parse_psd_metrics(text_content)
        
        if metrics:
            logger.info(f"Successfully extracted text-based PSD for {entry_id}: {metrics}")
            return {
                "source": "arxiv",
                "experiment_id": entry_id,
                "metrics": metrics,
                "raw_text": text_content[:500] # Truncate for storage
            }
        
        # 2. If text extraction failed, check for images (unstructured data)
        detected_images = _detect_psd_images(layout_pages)
        if detected_images:
            logger.warning(f"Detected {len(detected_images)} potential PSD images in {entry_id}. Flagging for OCR.")
            _flag_unstructured_entry(
                entry_id=entry_id,
                source="arxiv",
                issue_type="unstructured_image_detected",
                raw_blob=pdf_data
            )
            return None # Return None as we cannot extract without OCR fallback (T014b)
        
        logger.warning(f"No PSD data found in text or images for {entry_id}")
        return None

    except Exception as e:
        logger.error(f"Error processing PDF {entry_id}: {e}")
        # Flag as extraction failed
        with open(pdf_path, 'rb') as f:
            _flag_unstructured_entry(entry_id, "arxiv", "extraction_failed", f.read())
        return None
    finally:
        # Optional: cleanup downloaded PDF to save space if not needed later
        if pdf_path.exists():
            pdf_path.unlink()

def run_arxiv_ingestion() -> List[Dict[str, Any]]:
    """
    Main entry point for arXiv ingestion.
    Searches arXiv, downloads PDFs, and extracts PSD data.
    Returns a list of successfully extracted records.
    """
    logger.info("Starting arXiv ingestion...")
    results = []
    
    # Search for relevant papers
    papers = _search_arxiv(SEARCH_QUERY_TEMPLATE, max_results=MAX_RESULTS)
    if not papers:
        logger.warning("No papers found from arXiv.")
        return results
    
    logger.info(f"Found {len(papers)} papers to process.")
    
    for paper in papers:
        extracted = extract_psd_from_arxiv(paper)
        if extracted:
            results.append(extracted)
    
    logger.info(f"ArXiv ingestion complete. Extracted {len(results)} valid records.")
    return results
