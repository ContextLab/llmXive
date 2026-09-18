"""
Literature Scraper for T012d-Execute.

Implements the systematic literature review protocol to scrape tables
from specified PDFs using pdfplumber.
"""
import os
import sys
import logging
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib

# External dependencies
import pdfplumber
import requests

from utils.logging_config import get_logger
from utils.error_handlers import ConfigurationError, DataInsufficientError

class LiteratureScraper:
    """
    Scrapes data from PDF sources listed in sources.yaml.
    """
    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        self.config = config
        self.pdf_sources = config.get('pdf_sources', [])
        self.raw_dir = Path("data/raw")
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _download_pdf(self, url: str, filename: str) -> Path:
        """Download a PDF from a URL."""
        output_path = self.raw_dir / filename
        if output_path.exists():
            self.logger.info(f"PDF already exists: {output_path}")
            return output_path

        self.logger.info(f"Downloading PDF from {url} to {output_path}")
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
        except Exception as e:
            self.logger.error(f"Failed to download PDF {url}: {e}")
            raise

    def _parse_pdf(self, pdf_path: Path) -> List[Dict]:
        """Parse a PDF and extract tables containing composition and hardness."""
        records = []
        self.logger.info(f"Parsing PDF: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        if not table:
                            continue
                        
                        # Heuristic: Look for headers containing 'Element', 'Composition', 'Hardness', 'HV'
                        # This is a simplified parser. Real implementation would need more robust logic.
                        # We assume the first row is the header.
                        if len(table) < 2:
                            continue
                            
                        headers = [str(h).strip().lower() for h in table[0]]
                        
                        # Find indices for relevant columns
                        # We look for keywords
                        element_idx = None
                        pct_idx = None
                        hardness_idx = None
                        
                        for i, h in enumerate(headers):
                            if 'element' in h or 'el' in h:
                                element_idx = i
                            elif 'perc' in h or 'comp' in h or 'wt%' in h or 'at%' in h:
                                pct_idx = i
                            elif 'hard' in h or 'hv' in h or 'vickers' in h:
                                hardness_idx = i
                            
                        # If we can't find all, skip this table or try to infer
                        if element_idx is None or pct_idx is None or hardness_idx is None:
                            self.logger.debug(f"Skipping table on page {page_num} due to missing headers.")
                            continue
                            
                        # Extract rows
                        for row in table[1:]:
                            if not row or all(cell is None for cell in row):
                                continue
                            
                            try:
                                element = str(row[element_idx]).strip()
                                percentage = float(str(row[pct_idx]).strip().replace('%', ''))
                                hardness = float(str(row[hardness_idx]).strip().replace('HV', '').strip())
                                
                                if not element or not element.isalpha():
                                    continue
                                
                                records.append({
                                    "source": pdf_path.name,
                                    "element": element,
                                    "percentage": percentage,
                                    "hardness_hv": hardness,
                                    "page": page_num + 1
                                })
                            except (ValueError, TypeError) as e:
                                self.logger.debug(f"Skipping row due to parsing error: {e}")
                                continue
                                
        except Exception as e:
            self.logger.error(f"Error parsing PDF {pdf_path}: {e}", exc_info=True)
            raise
        
        return records

    def scrape_all(self) -> List[Dict]:
        """
        Iterate through all PDF sources, download, parse, and aggregate data.
        """
        all_records = []
        
        if not self.pdf_sources:
            self.logger.warning("No PDF sources found in configuration.")
            return all_records
        
        for source in self.pdf_sources:
            url = source.get('url')
            citation = source.get('citation', 'Unknown')
            filename = source.get('filename', f"source_{hashlib.md5(url.encode()).hexdigest()[:8]}.pdf")
            
            if not url:
                self.logger.warning(f"Skipping source without URL: {citation}")
                continue
            
            try:
                pdf_path = self._download_pdf(url, filename)
                records = self._parse_pdf(pdf_path)
                
                # Add citation info to records
                for r in records:
                    r['citation'] = citation
                    r['source_type'] = 'pdf'
                
                all_records.extend(records)
                self.logger.info(f"Extracted {len(records)} records from {citation}")
                
            except Exception as e:
                self.logger.error(f"Failed to process source {citation}: {e}")
                # Continue with other sources
                continue
        
        return all_records

def main():
    """Entry point for the literature scraper."""
    # Load sources config
    config_path = Path("data/config/sources.yaml")
    if not config_path.exists():
        raise ConfigurationError(f"Sources config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    scraper = LiteratureScraper(config)
    data = scraper.scrape_all()
    
    # The aggregator will handle saving, but we can return the data
    # or save to a temporary location if needed.
    # For this task, we just return the data.
    return data

if __name__ == "__main__":
    main()
