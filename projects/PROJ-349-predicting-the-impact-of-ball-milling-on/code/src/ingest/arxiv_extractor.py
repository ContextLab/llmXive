"""
arXiv PDF Extractor for Ball Milling Data.

This module implements the extraction of PSD metrics (D10, D50, D90) from
arXiv PDFs related to ball milling. It uses pdfminer.six for table extraction
and the arxiv Python library for search.
"""
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import arxiv
import pandas as pd
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams, LTTable, LTTextContainer
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import PDFPageAggregator

from src.exceptions import DataIngestionError

# Configure logging
logger = logging.getLogger(__name__)

# Constants
ARXIV_SEARCH_QUERY = 'ball milling AND "particle size distribution"'
OUTPUT_FILE = Path("data/raw/arxiv_tables.json")
MAX_RESULTS_TO_PROCESS = 5  # Process first 5 results to avoid rate limits
REQUIRED_COLUMNS = [
    'experiment_id', 'source', 'material_type', 'milling_speed',
    'milling_time', 'ball_to_powder_ratio', 'youngs_modulus',
    'density', 'd10', 'd50', 'd90', 'process_duration', 'pdf_url'
]

def _calculate_hash(data: str) -> str:
    """Calculate SHA-256 hash of data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def _extract_tables_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract tabular data from text using regex patterns.
    This is a heuristic approach since pdfminer table extraction can be unreliable.
    """
    tables = []
    lines = text.split('\n')
    
    # Look for lines that look like table rows (contain numbers and units)
    number_pattern = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')
    unit_pattern = re.compile(r'(?:µm|nm|mm|Hz|rpm|s|min|hr|GPa|g/cm³|g/cc)')
    
    current_table = []
    for line in lines:
        # Check if line contains numbers and units (potential table row)
        if number_pattern.search(line) and unit_pattern.search(line):
            current_table.append(line.strip())
        else:
            if len(current_table) >= 2:  # Minimum rows for a table
                tables.append(current_table)
            current_table = []
    
    # Don't forget the last table
    if len(current_table) >= 2:
        tables.append(current_table)
    
    return tables

def _parse_table_to_metrics(table_rows: List[str]) -> Optional[Dict[str, float]]:
    """
    Parse table rows to extract D10, D50, D90 values.
    Returns a dictionary with extracted values or None if parsing fails.
    """
    metrics = {}
    d_patterns = {
        'd10': re.compile(r'[Dd]10\s*[:\s=]+([0-9.]+)\s*(?:µm|nm|mm)?'),
        'd50': re.compile(r'[Dd]50\s*[:\s=]+([0-9.]+)\s*(?:µm|nm|mm)?'),
        'd90': re.compile(r'[Dd]90\s*[:\s=]+([0-9.]+)\s*(?:µm|nm|mm)?')
    }
    
    for row in table_rows:
        for metric, pattern in d_patterns.items():
            match = pattern.search(row)
            if match:
                try:
                    value = float(match.group(1))
                    # Convert to micrometers if needed (assume input is in µm or nm)
                    if 'nm' in row.lower():
                        value = value / 1000.0
                    metrics[metric] = value
                except ValueError:
                    continue
    
    # Only return if we found at least one metric
    if metrics:
        return metrics
    return None

def _extract_psd_from_pdf(pdf_path: str, paper_id: str) -> List[Dict[str, Any]]:
    """
    Extract PSD metrics from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        paper_id: arXiv paper ID for reference
        
    Returns:
        List of extracted experiment records
    """
    records = []
    try:
        # Extract text from PDF
        text = extract_text(pdf_path)
        
        # Calculate hash for tracking
        text_hash = _calculate_hash(text)
        
        # Extract tables from text
        tables = _extract_tables_from_text(text)
        
        if not tables:
            logger.warning(f"No tables found in PDF for paper {paper_id}")
            return records
        
        # Parse each table for metrics
        for table_rows in tables:
            metrics = _parse_table_to_metrics(table_rows)
            if metrics:
                record = {
                    'experiment_id': f"arxiv_{paper_id}_{len(records)}",
                    'source': 'arXiv',
                    'material_type': 'unknown',  # Would need NLP to extract
                    'milling_speed': None,
                    'milling_time': None,
                    'ball_to_powder_ratio': None,
                    'youngs_modulus': None,
                    'density': None,
                    'd10': metrics.get('d10'),
                    'd50': metrics.get('d50'),
                    'd90': metrics.get('d90'),
                    'process_duration': None,
                    'pdf_url': f"https://arxiv.org/pdf/{paper_id}",
                    'text_hash': text_hash
                }
                records.append(record)
                
    except Exception as e:
        logger.warning(f"Failed to extract from PDF {pdf_path}: {str(e)}")
        raise DataIngestionError(f"PDF extraction failed for {paper_id}: {str(e)}")
    
    return records

def extract_psd_from_arxiv(max_results: int = MAX_RESULTS_TO_PROCESS) -> List[Dict[str, Any]]:
    """
    Search arXiv for ball milling papers and extract PSD metrics.
    
    Args:
        max_results: Maximum number of papers to process
        
    Returns:
        List of extracted experiment records
    """
    all_records = []
    
    try:
        # Search arXiv
        logger.info(f"Searching arXiv with query: {ARXIV_SEARCH_QUERY}")
        search = arxiv.Search(
            query=ARXIV_SEARCH_QUERY,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        client = arxiv.Client()
        papers = list(client.results(search))
        
        if not papers:
            logger.warning("No papers found matching the search query")
            return all_records
        
        logger.info(f"Found {len(papers)} papers, processing up to {max_results}")
        
        # Process each paper
        for i, paper in enumerate(papers):
            paper_id = paper.entry_id.split('/')[-1]
            logger.info(f"Processing paper {i+1}/{len(papers)}: {paper.title}")
            
            try:
                # Download PDF
                pdf_path = f"/tmp/{paper_id}.pdf"
                paper.download_pdf(filename=pdf_path)
                
                # Extract PSD metrics
                records = _extract_psd_from_pdf(pdf_path, paper_id)
                all_records.extend(records)
                
                # Clean up
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    
            except DataIngestionError:
                # Log and continue with next paper
                continue
            except Exception as e:
                logger.warning(f"Unexpected error processing paper {paper_id}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to search arXiv: {str(e)}")
        raise DataIngestionError(f"arXiv search failed: {str(e)}")
    
    return all_records

def run_arxiv_ingestion() -> Optional[str]:
    """
    Main entry point for arXiv ingestion pipeline.
    
    Returns:
        Path to output file if successful, None otherwise
    """
    try:
        # Extract data
        records = extract_psd_from_arxiv()
        
        if not records:
            logger.warning("No data extracted from arXiv")
            # Create empty output file to indicate completion
            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_FILE, 'w') as f:
                json.dump([], f, indent=2)
            return str(OUTPUT_FILE)
        
        # Save to JSON
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(records, f, indent=2)
        
        logger.info(f"Successfully extracted {len(records)} records to {OUTPUT_FILE}")
        return str(OUTPUT_FILE)
        
    except DataIngestionError as e:
        logger.error(f"arXiv ingestion failed: {str(e)}")
        # Still create empty file to allow pipeline to continue
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump([], f, indent=2)
        return str(OUTPUT_FILE)
    except Exception as e:
        logger.error(f"Unexpected error in arXiv ingestion: {str(e)}")
        raise

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = run_arxiv_ingestion()
    if result:
        print(f"arXiv extraction complete. Output: {result}")
    else:
        print("arXiv extraction failed.")
        exit(1)
