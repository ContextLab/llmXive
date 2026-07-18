"""
arXiv PDF extractor for ball milling PSD data.
Uses pdfminer.six to scrape tables and detect unstructured PSD data (images/curves).
Flags unstructured entries to data/flagged_psd.json.
"""

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTImage, LTChar
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFPageInterpreter
import requests
from tqdm import tqdm

from src.exceptions import DataIngestionError, SourceConnectionError
from src.utils.exceptions import MissingTimestampError
from src.config.env_config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ARXIV_BASE_URL = "https://export.arxiv.org/api/query"
ARXIV_SEARCH_SIZE = 1000
PDF_DOWNLOAD_TIMEOUT = 60
FLAGGED_PSD_PATH = Path("data/flagged_psd.json")

# Regex patterns for PSD data extraction
PSD_PATTERN = re.compile(r"d\d0\s*[:=]\s*([\d.]+)\s*(?:μm|µm|um|microns?)?", re.IGNORECASE)
MILLING_SPEED_PATTERN = re.compile(r"milling\s+speed\s*[:=]\s*(\d+)\s*(?:rpm|r\.p\.m\.)", re.IGNORECASE)
MILLING_TIME_PATTERN = re.compile(r"milling\s+time\s*[:=]\s*(\d+)\s*(?:h|hours?|min|minutes?)", re.IGNORECASE)
BALL_RATIO_PATTERN = re.compile(r"ball\s*[-/]?to\s*[-/]?powder\s+ratio\s*[:=]\s*([\d.]+)", re.IGNORECASE)

def load_config() -> Dict[str, Any]:
    """Load configuration from env_config."""
    try:
        return get_config()
    except Exception as e:
        logger.warning(f"Failed to load config, using defaults: {e}")
        return {
            "ocr_fallback_enabled": False,
            "max_pdfs_to_process": 100,
            "arxiv_query_terms": "ball milling particle size distribution"
        }

def calculate_hash(content: bytes) -> str:
    """Calculate SHA256 hash of content."""
    return hashlib.sha256(content).hexdigest()

def download_pdf(pdf_url: str, timeout: int = PDF_DOWNLOAD_TIMEOUT) -> Optional[bytes]:
    """Download PDF from URL."""
    try:
        response = requests.get(pdf_url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.warning(f"Failed to download PDF from {pdf_url}: {e}")
        return None

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF using pdfminer.six."""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(pdf_content)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise DataIngestionError(f"PDF text extraction failed: {e}")

def detect_psd_images(pdf_content: bytes) -> List[Dict[str, Any]]:
    """
    Detect PSD curves/images in PDFs.
    Returns list of detected images with metadata.
    """
    images = []
    try:
        from io import BytesIO
        from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
        from pdfminer.converter import PDFPageAggregator
        from pdfminer.layout import LAParams, LTImage

        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        pdf_file = BytesIO(pdf_content)
        parser = PDFParser(pdf_file)
        doc = PDFDocument(parser)

        for page_num, page in enumerate(extract_pages(BytesIO(pdf_content))):
            for element in page:
                if isinstance(element, LTImage):
                    images.append({
                        "page": page_num + 1,
                        "type": "image",
                        "width": element.width,
                        "height": element.height,
                        "description": "Potential PSD curve or chart"
                    })
    except Exception as e:
        logger.warning(f"Image detection failed: {e}")

    return images

def extract_psd_metrics(text: str) -> Dict[str, Any]:
    """
    Extract PSD metrics and milling parameters from text.
    Returns dict with extracted values or None if not found.
    """
    metrics = {}

    # Extract D10, D50, D90
    for match in PSD_PATTERN.finditer(text):
        value = float(match.group(1))
        # Determine which d-value based on context
        context = text[max(0, match.start()-20):match.end()+20]
        if "d10" in context.lower():
            metrics["d10"] = value
        elif "d50" in context.lower():
            metrics["d50"] = value
        elif "d90" in context.lower():
            metrics["d90"] = value

    # Extract milling speed
    speed_match = MILLING_SPEED_PATTERN.search(text)
    if speed_match:
        metrics["milling_speed"] = int(speed_match.group(1))

    # Extract milling time
    time_match = MILLING_TIME_PATTERN.search(text)
    if time_match:
        time_val = int(time_match.group(1))
        unit_match = re.search(r"(\d+)\s*(h|hours?|min|minutes?)", text[time_match.end():time_match.end()+20])
        if unit_match and unit_match.group(2) in ["min", "minutes?"]:
            time_val = time_val / 60.0  # Convert to hours
        metrics["milling_time"] = time_val

    # Extract ball to powder ratio
    ratio_match = BALL_RATIO_PATTERN.search(text)
    if ratio_match:
        metrics["ball_to_powder_ratio"] = float(ratio_match.group(1))

    return metrics

def flag_unstructured_entry(
    experiment_id: str,
    source: str,
    issue_type: str,
    raw_blob_hash: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Flag unstructured entries to data/flagged_psd.json.
    Schema: experiment_id, source, issue_type, raw_blob_hash, [optional details]
    """
    FLAGGED_PSD_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "experiment_id": experiment_id,
        "source": source,
        "issue_type": issue_type,
        "raw_blob_hash": raw_blob_hash
    }
    if details:
        entry["details"] = details

    # Load existing flags
    if FLAGGED_PSD_PATH.exists():
        try:
            with open(FLAGGED_PSD_PATH, "r") as f:
                flags = json.load(f)
        except json.JSONDecodeError:
            flags = []
    else:
        flags = []

    # Append new entry
    flags.append(entry)

    # Write back
    with open(FLAGGED_PSD_PATH, "w") as f:
        json.dump(flags, f, indent=2)

    logger.info(f"Flagged unstructured entry: {experiment_id} ({issue_type})")

def extract_psd_from_arxiv(query_terms: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract PSD data from arXiv PDFs.
    Returns list of extracted experiments.
    """
    config = load_config()
    query_terms = query_terms or config.get("arxiv_query_terms", "ball milling particle size distribution")
    max_pdfs = config.get("max_pdfs_to_process", 100)
    ocr_enabled = config.get("ocr_fallback_enabled", False)

    # Search arXiv API
    params = {
        "search_query": query_terms,
        "start": 0,
        "max_results": ARXIV_SEARCH_SIZE
    }

    try:
        response = requests.get(ARXIV_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise SourceConnectionError(f"Failed to connect to arXiv API: {e}")

    # Parse XML response (simplified - in production use xml.etree)
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    namespace = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    entries = []
    for entry in root.findall("atom:entry", namespace):
        if len(entries) >= max_pdfs:
            break

        paper_id = entry.find("atom:id", namespace).text.split("/")[-1]
        title = entry.find("atom:title", namespace).text.strip()
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"

        # Download PDF
        pdf_content = download_pdf(pdf_url)
        if not pdf_content:
            continue

        # Calculate hash
        blob_hash = calculate_hash(pdf_content)

        # Extract text
        try:
            text = extract_text_from_pdf(pdf_content)
        except DataIngestionError as e:
            flag_unstructured_entry(
                experiment_id=f"arxiv_{paper_id}",
                source="arxiv",
                issue_type="text_extraction_failed",
                raw_blob_hash=blob_hash,
                details={"error": str(e)}
            )
            continue

        # Detect images
        images = detect_psd_images(pdf_content)
        if images and not ocr_enabled:
            flag_unstructured_entry(
                experiment_id=f"arxiv_{paper_id}",
                source="arxiv",
                issue_type="unstructured_psd_detected",
                raw_blob_hash=blob_hash,
                details={"image_count": len(images), "pages": [img["page"] for img in images]}
            )
            # Continue processing text even if images detected
        elif images and ocr_enabled:
            logger.info(f"OCR fallback enabled for arxiv_{paper_id}, {len(images)} images detected")
            # In production, would invoke OCR here

        # Extract metrics
        metrics = extract_psd_metrics(text)
        if not metrics:
            flag_unstructured_entry(
                experiment_id=f"arxiv_{paper_id}",
                source="arxiv",
                issue_type="no_psd_data_found",
                raw_blob_hash=blob_hash,
                details={"title": title[:100]}
            )
            continue

        # Build experiment record
        experiment = {
            "experiment_id": f"arxiv_{paper_id}",
            "source": "arxiv",
            "title": title,
            "pdf_hash": blob_hash,
            **metrics
        }

        # Check for required fields
        required_fields = ["d10", "d50", "d90", "milling_speed", "milling_time", "ball_to_powder_ratio"]
        missing = [f for f in required_fields if f not in experiment]
        if missing:
            flag_unstructured_entry(
                experiment_id=f"arxiv_{paper_id}",
                source="arxiv",
                issue_type="missing_required_fields",
                raw_blob_hash=blob_hash,
                details={"missing_fields": missing}
            )
            continue

        entries.append(experiment)

    logger.info(f"Extracted {len(entries)} valid experiments from arXiv")
    return entries

def run_arxiv_ingestion(output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Run full arXiv ingestion pipeline.
    Returns list of extracted experiments.
    """
    logger.info("Starting arXiv PDF ingestion...")

    experiments = extract_psd_from_arxiv()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(experiments, f, indent=2)
        logger.info(f"Saved {len(experiments)} experiments to {output_path}")

    return experiments

if __name__ == "__main__":
    # Run ingestion
    results = run_arxiv_ingestion(Path("data/raw/arxiv_experiments.json"))
    print(f"Extracted {len(results)} experiments")
