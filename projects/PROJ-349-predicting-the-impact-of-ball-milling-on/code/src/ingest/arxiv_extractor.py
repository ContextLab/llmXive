import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import arxiv
import fitz  # PyMuPDF for PDF handling
import pandas as pd

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

def extract_psd_from_arxiv(paper: arxiv.Result) -> Optional[Dict[str, Any]]:
    """
    Extract PSD data from an arXiv paper.
    
    CRITICAL: This function does NOT generate synthetic data. 
    If extraction fails, it returns None and logs a warning.
    """
    try:
        # Download PDF
        pdf_path = f"/tmp/{paper.arxiv_id}.pdf"
        paper.download_pdf(filename=pdf_path)
        
        # Read PDF and extract text
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        # Search for D10, D50, D90 patterns
        d10_match = re.search(r'D10[:\s]*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        d50_match = re.search(r'D50[:\s]*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        d90_match = re.search(r'D90[:\s]*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        
        if d10_match and d50_match and d90_match:
            return {
                "experiment_id": paper.arxiv_id,
                "source": "arxiv",
                "d10": float(d10_match.group(1)),
                "d50": float(d50_match.group(1)),
                "d90": float(d90_match.group(1)),
                # Other fields like milling_speed would need more specific extraction
                # For now, we only return if we found PSD data
                "material_type": "unknown",
                "milling_speed": None,
                "milling_time": None,
                "ball_to_powder_ratio": None,
                "youngs_modulus": None,
                "density": None,
                "process_duration": None
            }
        else:
            logger.warning(f"No PSD data found in {paper.arxiv_id}")
            return None
            
    except Exception as e:
        logger.warning(f"Failed to extract from {paper.arxiv_id}: {e}")
        return None

def run_arxiv_ingestion(output_path: str = "data/raw/arxiv_tables.json", max_papers: int = 10) -> int:
    """
    Run the arXiv ingestion pipeline.
    
    Returns:
        int: Number of rows fetched.
    """
    logger.info("Starting arXiv ingestion...")
    
    # Search for papers
    client = arxiv.Client()
    search = arxiv.Search(
        query="cond-mat.mtrl-sci ball milling",
        max_results=max_papers,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    count = 0
    
    try:
        for paper in client.results(search):
            extracted = extract_psd_from_arxiv(paper)
            if extracted:
                results.append(extracted)
                count += 1
    except Exception as e:
        logger.warning(f"arXiv search failed: {e}")
    
    if count == 0:
        logger.warning("Source skipped: arXiv (no rows or error)")
        # Create an empty file to indicate the run happened but yielded nothing
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([], f)
        return 0
    
    # Save data
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved {count} rows to {output_path}")
    return count
