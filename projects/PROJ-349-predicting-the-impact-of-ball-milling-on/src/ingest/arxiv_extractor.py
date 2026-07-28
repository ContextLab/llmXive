"""
arXiv PDF Extractor (T013b).

Extracts PSD data from arXiv papers using PDF mining.
Strictly real data only: no synthetic fallbacks, no mock data generators.
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
import pdfminer.high_level

from src.utils.logger import get_module_logger
from src.exceptions import SourceConnectionError

logger = get_module_logger(__name__)

def extract_psd_from_arxiv(query: str = "ball milling", max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Searches arXiv for papers and extracts PSD data.
    
    Args:
        query: Search query.
        max_results: Maximum number of papers to process.
        
    Returns:
        List of extracted data dictionaries.
    """
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=f"cat:cond-mat.mtrl-sci AND {query}",
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        logger.info(f"Searching arXiv for: {query}")
        results = list(client.results(search))
        
        if not results:
            logger.warning("arXiv search returned no results.")
            return []
        
        extracted_data = []
        
        for i, result in enumerate(results):
            logger.info(f"Processing paper {i+1}/{len(results)}: {result.title}")
            
            try:
                # Download PDF
                pdf_path = Path(f"data/raw/tmp_arxiv_{result.entry_id.split('/')[-1]}.pdf")
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                result.download_pdf(dirpath=pdf_path.parent, filename=pdf_path.name)
                
                # Extract text
                text = pdfminer.high_level.extract_text(str(pdf_path))
                
                # Parse tables for D10, D50, D90
                # This is a simplified regex-based extraction.
                # Real implementation would use more robust table parsing.
                pattern = r'D(10|50|90)[\s:]*([0-9]+(?:\.[0-9]+)?)'
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                if matches:
                    entry = {
                        "source": "arxiv",
                        "title": result.title,
                        "entry_id": result.entry_id,
                        "extracted_values": {f"D{m[0]}": float(m[1]) for m in matches}
                    }
                    extracted_data.append(entry)
                    logger.info(f"Extracted values from {result.title}: {entry['extracted_values']}")
                
                # Clean up temp file
                if pdf_path.exists():
                    pdf_path.unlink()
                    
            except Exception as e:
                logger.warning(f"Failed to process paper {result.entry_id}: {e}")
                continue
        
        return extracted_data

    except Exception as e:
        logger.error(f"Failed to search arXiv: {e}")
        raise SourceConnectionError(f"arXiv connection failed: {e}")

def save_to_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves extracted data to JSON.
    
    Args:
        data: List of extracted data dictionaries.
        output_path: Path to output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(data)} records to {output_path}")

def run_arxiv_ingestion(output_dir: str = "data/raw") -> Optional[str]:
    """
    Orchestrates the arXiv ingestion pipeline.
    
    Args:
        output_dir: Directory to save the raw data.
        
    Returns:
        Path to the saved file, or None if skipped/failed.
    """
    output_path = Path(output_dir) / "arxiv_tables.json"
    
    try:
        logger.info("Starting arXiv ingestion...")
        data = extract_psd_from_arxiv(max_results=5)
        
        if not data:
            logger.warning("Source skipped: arXiv (no rows or error)")
            return None
        
        save_to_json(data, str(output_path))
        return str(output_path)
        
    except SourceConnectionError as e:
        logger.warning(f"Source skipped: arXiv (connection error: {e})")
        return None
    except Exception as e:
        logger.warning(f"Source skipped: arXiv (unexpected error: {e})")
        return None
