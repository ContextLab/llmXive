"""
arXiv PDF Extractor.

Extracts PSD data from ball milling papers on arXiv.
Strictly uses real data. No synthetic fallbacks.
"""
import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import arxiv
import pandas as pd
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

from src.utils.logger import get_module_logger
from src.exceptions import SourceConnectionError, DataIngestionError

logger = get_module_logger(__name__)

# Regex pattern for D10, D50, D90
PSD_PATTERN = re.compile(r'D(10|50|90)[\s:]*([0-9]+(?:\.[0-9]+)?)', re.IGNORECASE)

def extract_psd_from_arxiv(paper: arxiv.Result) -> Optional[Dict[str, Any]]:
    """
    Extracts PSD data from a single arXiv paper.

    Args:
        paper: arXiv paper result.

    Returns:
        Dictionary with extracted data, or None if failed.
    """
    try:
        # Download PDF
        pdf_path = paper.download_pdf(dirpath="data/raw/arxiv_temp", filename=f"{paper.pdf_id}.pdf")
        
        # Extract text
        text = extract_text(pdf_path, laparams=LAParams())
        
        # Search for PSD values
        d_values = {}
        for match in PSD_PATTERN.finditer(text):
            key = f"d{match.group(1)}"
            value = float(match.group(2))
            d_values[key] = value

        if not d_values:
            logger.debug(f"No PSD values found in {paper.title}")
            return None

        # Construct entry
        entry = {
            "experiment_id": f"arxiv_{paper.pdf_id}",
            "source": "arxiv",
            "material_type": "unknown", # Extract from title or abstract if possible
            "milling_speed": None,
            "milling_time": None,
            "ball_to_powder_ratio": None,
            "youngs_modulus": None,
            "density": None,
            "process_duration": None
        }
        entry.update(d_values)

        return entry

    except Exception as e:
        logger.warning(f"Failed to extract data from {paper.pdf_id}: {e}")
        return None

def run_arxiv_ingestion(output_dir: str = "data/raw", max_papers: int = 10) -> Optional[str]:
    """
    Orchestrates the arXiv data ingestion.

    Args:
        output_dir: Directory to save the raw data.
        max_papers: Maximum number of papers to process.

    Returns:
        Path to the saved JSON file, or None if no data was fetched.
    """
    output_path = os.path.join(output_dir, "arxiv_tables.json")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path("data/raw/arxiv_temp").mkdir(parents=True, exist_ok=True)

    client = arxiv.Client()
    search = arxiv.Search(
        query="cat:cond-mat.mtrl-sci AND ball milling",
        max_results=max_papers
    )

    results = list(client.results(search))

    if not results:
        logger.warning("Source skipped: arXiv (no results found)")
        return None

    entries = []
    for i, paper in enumerate(results):
        logger.info(f"Processing paper {i+1}/{len(results)}: {paper.title}")
        entry = extract_psd_from_arxiv(paper)
        if entry:
            entries.append(entry)
        # Small delay to respect API limits
        time.sleep(0.5)

    if not entries:
        logger.warning("Source skipped: arXiv (no rows or error)")
        return None

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2)
    
    logger.info(f"Saved {len(entries)} entries from arXiv to {output_path}")
    return output_path
