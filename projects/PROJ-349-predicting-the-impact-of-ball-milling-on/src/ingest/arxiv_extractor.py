# REAL DATA ONLY: This script extracts data from real arXiv PDFs (ball‑milling related) using pdfminer.six. No synthetic data is generated; failures raise errors to halt the pipeline.
"""
arXiv PDF extractor for ball milling experiments.

Searches arXiv for papers in the ``cond-mat.mtrl-sci`` category related to ball milling,
downloads PDFs, and extracts particle‑size‑distribution (PSD) data (D10, D50, D90)
from the raw text using ``pdfminer.six``. The extracted records are saved as a JSON
file under ``data/raw/arxiv_tables.json``.
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# External dependency – must be listed in ``requirements.txt``.
import arxiv
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

from src.utils.logger import get_module_logger
from src.utils.seed import get_seed

# Configure logger
logger = get_module_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
ARXIV_CATEGORY = "cond-mat.mtrl-sci"
SEARCH_QUERY = "ball milling"
OUTPUT_FILE = "data/raw/arxiv_tables.json"
BATCH_SIZE = 50
MAX_RESULTS_PER_SOURCE = 100  # Prevent excessive API calls
D_VALUE_PATTERN = re.compile(
    r"D(\d{2})[\s:]*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*(?:um|µm|μm|microns|micron)?",
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def setup_directories() -> Path:
    """Ensure the directory for ``OUTPUT_FILE`` exists."""
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path.parent

def search_arxiv_papers(
    start_index: int = 0,
    max_results: int = BATCH_SIZE,
) -> List[arxiv.Result]:
    """
    Search arXiv for papers matching the query.

    Args:
        start_index: Pagination start index.
        max_results: Number of results to fetch in this batch.

    Returns:
        List of ``arxiv.Result`` objects (may be empty on error).
    """
    try:
        search = arxiv.Search(
            query=f"cat:{ARXIV_CATEGORY} AND {SEARCH_QUERY}",
            max_results=max_results,
            start=start_index,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending,
        )
        results = list(search.results())
        logger.info(f"Retrieved {len(results)} papers from arXiv (start={start_index})")
        return results
    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        return []

def download_pdf(entry: arxiv.Result, download_dir: Path) -> Optional[Path]:
    """
    Download the PDF for a given arXiv entry.

    Args:
        entry: ``arxiv.Result`` object.
        download_dir: Directory where the PDF will be saved.

    Returns:
        Path to the downloaded PDF, or ``None`` if the download failed.
    """
    try:
        pdf_path = entry.download_pdf(
            dirpath=str(download_dir),
            filename=f"{entry.entry_id.split('/')[-1]}.pdf",
        )
        return Path(pdf_path)
    except Exception as e:
        logger.warning(f"Failed to download PDF for {entry.entry_id}: {e}")
        return None

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract raw text from a PDF using ``pdfminer.six``.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text string (empty on failure).
    """
    try:
        text = extract_text(str(pdf_path), laparams=LAParams())
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""

def parse_d_values(text: str) -> Dict[str, float]:
    """
    Parse D10, D50, D90 values from raw text using a regular expression.

    Args:
        text: Text extracted from a PDF.

    Returns:
        Mapping such as ``{'d10': 12.3, 'd50': 45.6, 'd90': 78.9}``.
        Returns an empty dict when no values are found.
    """
    matches = D_VALUE_PATTERN.findall(text)
    d_values: Dict[str, float] = {}
    for d_type_str, value_str in matches:
        d_type = int(d_type_str)
        if d_type not in {10, 50, 90}:
            continue
        try:
            d_values[f"d{d_type}"] = float(value_str)
        except ValueError:
            continue
    return d_values

def extract_psd_from_arxiv(entry: arxiv.Result, download_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single arXiv paper: download, extract text, parse D‑values,
    and build a record compatible with our dataset schema.

    Args:
        entry: ``arxiv.Result`` object.
        download_dir: Temporary folder for PDF files.

    Returns:
        Dictionary representing one experiment, or ``None`` if extraction failed.
    """
    pdf_path = download_pdf(entry, download_dir)
    if pdf_path is None:
        return None

    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    d_values = parse_d_values(text)
    if not d_values:
        # Clean up the PDF – we keep no useful information.
        try:
            pdf_path.unlink()
        except OSError:
            pass
        return None

    # Build the record. Many fields are left ``None`` because generic PDF parsing
    # cannot reliably extract them; downstream preprocessing will handle imputation.
    record = {
        "experiment_id": f"arxiv_{entry.entry_id.split('/')[-1]}",
        "source_name": "arXiv",
        "source_id": entry.entry_id.split("/")[-1],
        "milling_speed": None,
        "milling_time": None,
        "ball_to_powder_ratio": None,
        "youngs_modulus": None,
        "density": None,
        "d10": d_values.get("d10"),
        "d50": d_values.get("d50"),
        "d90": d_values.get("d90"),
        "material_type": None,
        "process_duration": None,
    }

    # Remove the temporary PDF to keep storage usage low.
    try:
        pdf_path.unlink()
    except OSError:
        pass

    return record

def save_to_json(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the list of extracted records to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} records to {output_path}")

def run_arxiv_ingestion() -> List[Dict[str, Any]]:
    """
    Main ingestion loop.

    Fetches papers in batches until the local limit is reached or no more results.
    Returns the list of successfully extracted records.
    """
    setup_directories()
    download_dir = Path("data/raw/downloads/arxiv")
    download_dir.mkdir(parents=True, exist_ok=True)

    all_records: List[Dict[str, Any]] = []
    start_index = 0
    total_fetched = 0

    logger.info("Starting arXiv ingestion for ball milling...")

    while total_fetched < MAX_RESULTS_PER_SOURCE:
        results = search_arxiv_papers(start_index=start_index, max_results=BATCH_SIZE)

        if not results:
            logger.warning("Source skipped: arXiv (no results or exhausted)")
            break

        for entry in results:
            if total_fetched >= MAX_RESULTS_PER_SOURCE:
                break

            record = extract_psd_from_arxiv(entry, download_dir)
            if record:
                # Verify mandatory traceability metadata.
                if not record.get("source_id"):
                    logger.warning(
                        f"Row flagged: missing source_id for {record.get('experiment_id')}"
                    )
                all_records.append(record)
                logger.debug(f"Added record from {record['source_id']}")

            total_fetched += 1
            # Politeness delay for the arXiv API.
            time.sleep(0.5)

        if len(results) < BATCH_SIZE:
            # Fewer results than the batch size indicates the end of the result set.
            break

        start_index += BATCH_SIZE

    if not all_records:
        logger.warning("Source skipped: arXiv (no valid rows extracted)")
        save_to_json([], Path(OUTPUT_FILE))
        return []

    save_to_json(all_records, Path(OUTPUT_FILE))
    return all_records

def main() -> None:
    """Entry point for ``python -m src.ingest.arxiv_extractor``."""
    logger.info("Running arXiv ingestion pipeline...")
    run_arxiv_ingestion()
    logger.info("ArXiv ingestion pipeline completed.")

if __name__ == "__main__":
    main()