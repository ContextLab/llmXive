"""
arXiv PDF extractor for ball milling data.

Searches arXiv for papers in 'cond-mat.mtrl-sci' related to 'ball milling',
downloads PDFs, extracts tables using pdfminer.six, and parses PSD metrics (D10, D50, D90).
"""
import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import arxiv
except ImportError:
    raise ImportError(
        "The 'arxiv' package is required for arXiv extraction. "
        "Install it via: pip install arxiv"
    )

try:
    from pdfminer.high_level import extract_text
except ImportError:
    raise ImportError(
        "The 'pdfminer.six' package is required for PDF text extraction. "
        "Install it via: pip install pdfminer.six"
    )

from src.utils.logger import get_module_logger
from src.exceptions import DataIngestionError

logger = get_module_logger(__name__)

# Configuration
ARXIV_CATEGORY = "cond-mat.mtrl-sci"
ARXIV_SEARCH_QUERY = "ball milling"
MAX_PAPERS_TO_PROCESS = 50
OUTPUT_FILE = "data/raw/arxiv_tables.json"

# Regex patterns for D-values
D_VALUE_PATTERN = re.compile(
    r"\b[Dd](10|50|90)[\s:]*([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE
)

def _ensure_output_dir(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def _search_arxiv_papers(query: str, category: str, max_results: int) -> List[arxiv.Result]:
    """
    Search arXiv for papers matching the query and category.

    Args:
        query: Search query string.
        category: arXiv category to filter by.
        max_results: Maximum number of results to fetch.

    Returns:
        List of arxiv.Result objects.
    """
    logger.info(f"Searching arXiv for '{query}' in category '{category}'...")
    try:
        search = arxiv.Search(
            query=f"cat:{category} AND {query}",
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        results = list(search.results())
        if not results:
            logger.warning("Source skipped: arXiv (no results found)")
            return []
        logger.info(f"Found {len(results)} papers in arXiv search.")
        return results
    except Exception as e:
        logger.warning(f"Source skipped: arXiv (error: {e})")
        return []

def _download_pdf(result: arxiv.Result, download_dir: Path) -> Optional[Path]:
    """
    Download a PDF for a given arXiv result.

    Args:
        result: arxiv.Result object.
        download_dir: Directory to save the PDF.

    Returns:
        Path to the downloaded PDF, or None if failed.
    """
    try:
        pdf_path = download_dir / f"{result.entry_id.split('/')[-1]}.pdf"
        result.download_pdf(dirpath=str(download_dir), filename=pdf_path.name)
        if pdf_path.exists():
            logger.debug(f"Downloaded PDF: {pdf_path.name}")
            return pdf_path
        else:
            logger.warning(f"PDF download failed for {result.entry_id}")
            return None
    except Exception as e:
        logger.warning(f"Failed to download PDF for {result.entry_id}: {e}")
        return None

def _extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
    """
    Extract text from a PDF using pdfminer.six.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text string, or None if failed.
    """
    try:
        text = extract_text(str(pdf_path))
        return text
    except Exception as e:
        logger.warning(f"Failed to extract text from {pdf_path}: {e}")
        return None

def _parse_tables_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse potential table data from extracted text.

    This is a heuristic approach: look for lines that resemble table rows
    and contain D10, D50, or D90.

    Args:
        text: Full text extracted from the PDF.

    Returns:
        List of dictionaries representing parsed table rows.
    """
    extracted_rows = []
    lines = text.splitlines()

    # Heuristic: look for lines containing D10, D50, or D90
    for line in lines:
        if re.search(r"D(10|50|90)", line, re.IGNORECASE):
            row_data = {}
            # Try to extract D values from the line
            matches = D_VALUE_PATTERN.findall(line)
            for match in matches:
                d_type = match[0]
                d_value = match[1]
                try:
                    row_data[f"d{d_type.lower()}"] = float(d_value)
                except ValueError:
                    continue

            # If we found at least one D value, add the row
            if row_data:
                # Try to extract other metadata if present (e.g., material, speed)
                # This is very basic; a more robust parser would be needed for production.
                extracted_rows.append(row_data)

    return extracted_rows

def _extract_psd_from_arxiv_paper(result: arxiv.Result, temp_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Extract PSD data from a single arXiv paper.

    Args:
        result: arxiv.Result object.
        temp_dir: Temporary directory for PDF storage.

    Returns:
        Dictionary with extracted PSD data, or None if extraction failed.
    """
    pdf_path = _download_pdf(result, temp_dir)
    if pdf_path is None:
        return None

    text = _extract_text_from_pdf(pdf_path)
    if text is None:
        return None

    table_data = _parse_tables_from_text(text)
    if not table_data:
        logger.debug(f"No PSD data found in {result.entry_id}")
        return None

    # Aggregate data from all found rows
    aggregated_data = {}
    for row in table_data:
        for key, value in row.items():
            # If multiple values for same key, take the first one found
            if key not in aggregated_data:
                aggregated_data[key] = value

    # Enrich with metadata
    record = {
        "experiment_id": hashlib.md5(result.entry_id.encode()).hexdigest()[:12],
        "source": "arXiv",
        "arxiv_id": result.entry_id.split("/")[-1],
        "title": result.title,
        "authors": [str(author) for author in result.authors],
        "published": str(result.published),
        "data": aggregated_data
    }

    # Clean up PDF
    try:
        pdf_path.unlink()
    except Exception:
        pass

    return record

def run_arxiv_ingestion(output_path: str = OUTPUT_FILE) -> List[Dict[str, Any]]:
    """
    Main function to run the arXiv ingestion pipeline.

    Args:
        output_path: Path to the output JSON file.

    Returns:
        List of extracted records.
    """
    logger.info("Starting arXiv ingestion pipeline...")

    # Ensure output directory exists
    output_file = Path(output_path)
    _ensure_output_dir(output_file)

    # Create a temporary directory for PDFs
    temp_dir = Path("data/raw/.temp_arxiv_pdfs")
    temp_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    total_processed = 0

    try:
        # Search arXiv
        papers = _search_arxiv_papers(ARXIV_SEARCH_QUERY, ARXIV_CATEGORY, MAX_PAPERS_TO_PROCESS)
        if not papers:
            logger.warning("Source skipped: arXiv (no results found)")
            # Write empty file to indicate completion
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
            return []

        # Process each paper
        for i, paper in enumerate(papers):
            if i >= MAX_PAPERS_TO_PROCESS:
                logger.info(f"Reached limit of {MAX_PAPERS_TO_PROCESS} papers.")
                break

            logger.info(f"Processing paper {i+1}/{len(papers)}: {paper.entry_id}")
            record = _extract_psd_from_arxiv_paper(paper, temp_dir)

            if record:
                all_records.append(record)
                logger.info(f"Extracted data from {paper.entry_id}")
            else:
                logger.warning(f"Source skipped: arXiv (no rows or error) for {paper.entry_id}")

            total_processed += 1

            # Small delay to be polite to the API
            time.sleep(0.5)

        # Write output
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_records, f, indent=2, default=str)

        logger.info(f"ArXiv ingestion complete. Extracted {len(all_records)} records from {total_processed} papers.")
        logger.info(f"Output written to {output_file}")

        return all_records

    except Exception as e:
        logger.error(f"ArXiv ingestion failed with error: {e}")
        raise DataIngestionError(f"ArXiv ingestion failed: {e}")
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

def extract_psd_from_arxiv() -> List[Dict[str, Any]]:
    """
    Convenience function to run extraction and return results.

    Returns:
        List of extracted records.
    """
    return run_arxiv_ingestion()

if __name__ == "__main__":
    # Configure root logger for CLI execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    run_arxiv_ingestion()
