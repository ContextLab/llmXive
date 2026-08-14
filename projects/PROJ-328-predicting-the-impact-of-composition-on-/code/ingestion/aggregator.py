"""
Literature Aggregator for Solder Hardness Data.

Fetches data from verified sources including:
1. Materials Project API
2. NIST/UCI repositories  
3. PDFs from research_verified.md
"""

import os
import csv
import requests
import logging
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from utils.logging_config import get_logger
from utils.error_handlers import ConfigurationError, IngestionError
from ingestion.citation_tracker import CitationTracker

logger = get_logger(__name__)


class LiteratureAggregator:
    """Aggregates solder hardness data from multiple sources."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the aggregator.
        
        Args:
            config_path: Path to sources.yaml configuration file.
                        If None, uses default path from project structure.
        """
        self.logger = get_logger(__name__)
        self.citation_tracker = CitationTracker()
        
        # Default config path
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / "data" / "config" / "sources.yaml"
        else:
            self.config_path = Path(config_path)
        
        self.sources = {}
        self.raw_data: List[Dict[str, Any]] = []
        
    def load_sources_config(self) -> Dict[str, Any]:
        """
        Load verified sources from sources.yaml.
        
        Returns:
            Dictionary of source configurations.
            
        Raises:
            ConfigurationError: If sources.yaml is missing or invalid.
        """
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Sources configuration not found at {self.config_path}. "
                "Ensure T009c has populated data/config/sources.yaml."
            )
        
        try:
            with open(self.config_path, 'r') as f:
                self.sources = yaml.safe_load(f)
            self.logger.info(f"Loaded {len(self.sources)} sources from config")
            return self.sources
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in sources config: {e}")
    
    def fetch_from_materials_project(self) -> List[Dict[str, Any]]:
        """
        Fetch solder data from Materials Project API.
        
        Returns:
            List of data records with composition and hardness.
        """
        api_key = os.getenv("MATERIALS_PROJECT_API_KEY")
        if not api_key:
            self.logger.warning("MATERIALS_PROJECT_API_KEY not set, skipping Materials Project")
            return []
        
        # Materials Project API endpoint for materials with specific elements
        # Note: This is a placeholder implementation - actual API calls would need
        # to be tailored to the specific data structure in Materials Project
        base_url = "https://api.materialsproject.org/v2/materials"
        
        records = []
        try:
            # Example: Query for Sn-Pb-Sb alloys
            params = {"elements": "Sn,Pb,Sb", "api_key": api_key}
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            for material in data.get("results", []):
                record = {
                    "source": "materials_project",
                    "material_id": material.get("material_id"),
                    "composition": material.get("composition", {}),
                    "properties": material.get("properties", {}),
                    "citation": f"Materials Project: {material.get('material_id')}"
                }
                records.append(record)
                self.citation_tracker.track(material.get('citation', 'Materials Project'))
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch from Materials Project: {e}")
        
        return records
    
    def fetch_from_nist_uci(self) -> List[Dict[str, Any]]:
        """
        Fetch data from NIST/UCI repositories.
        
        Returns:
            List of data records.
        """
        records = []
        nist_urls = self.sources.get("nist_uci", {}).get("urls", [])
        
        for url in nist_urls:
            try:
                self.logger.info(f"Fetching from NIST/UCI: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse based on content type
                if url.endswith('.csv'):
                    # Parse CSV
                    reader = csv.DictReader(response.text.splitlines())
                    for row in reader:
                        record = {
                            "source": "nist_uci",
                            "url": url,
                            "data": row,
                            "citation": f"NIST/UCI: {url}"
                        }
                        records.append(record)
                else:
                    self.logger.warning(f"Unsupported format from NIST/UCI: {url}")
                
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch from {url}: {e}")
        
        return records
    
    def fetch_from_verified_urls(self) -> List[Dict[str, Any]]:
        """
        Fetch data from direct URLs specified in sources.yaml.
        
        Returns:
            List of data records.
        """
        records = []
        direct_urls = self.sources.get("direct_urls", [])
        
        for source_config in direct_urls:
            url = source_config.get("url")
            source_name = source_config.get("name", "unknown")
            
            if not url:
                continue
            
            try:
                self.logger.info(f"Fetching from {source_name}: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse based on format
                if url.endswith('.json'):
                    data = response.json()
                    for item in data if isinstance(data, list) else [data]:
                        record = {
                            "source": source_name,
                            "data": item,
                            "citation": source_config.get("citation", url)
                        }
                        records.append(record)
                elif url.endswith('.csv'):
                    reader = csv.DictReader(response.text.splitlines())
                    for row in reader:
                        record = {
                            "source": source_name,
                            "data": row,
                            "citation": source_config.get("citation", url)
                        }
                        records.append(record)
                
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch from {source_name} ({url}): {e}")
        
        return records
    
    def scrape_pdfs(self, pdf_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape data from PDF files using pdfplumber.
        
        Args:
            pdf_paths: List of paths to PDF files.
        
        Returns:
            List of extracted data records.
        """
        try:
            import pdfplumber
        except ImportError:
            self.logger.error("pdfplumber not installed. Install with: pip install pdfplumber")
            return []
        
        records = []
        
        for pdf_path in pdf_paths:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                self.logger.warning(f"PDF not found: {pdf_path}")
                continue
            
            try:
                self.logger.info(f"Scraping PDF: {pdf_path}")
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        tables = page.extract_tables()
                        for table in tables:
                            # Parse table rows
                            if len(table) < 2:
                                continue
                            
                            headers = table[0]
                            for row in table[1:]:
                                if len(row) != len(headers):
                                    continue
                                
                                record = {
                                    "source": "pdf",
                                    "file": str(pdf_path),
                                    "page": page_num + 1,
                                    "data": dict(zip(headers, row)),
                                    "citation": f"PDF: {pdf_path.name}, page {page_num + 1}"
                                }
                                records.append(record)
                
                self.citation_tracker.track(f"PDF: {pdf_path.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to scrape {pdf_path}: {e}")
        
        return records
    
    def aggregate_all(self) -> List[Dict[str, Any]]:
        """
        Aggregate data from all configured sources.
        
        Returns:
            Combined list of all data records.
        """
        self.load_sources_config()
        all_records = []
        
        # Fetch from APIs
        mp_records = self.fetch_from_materials_project()
        all_records.extend(mp_records)
        self.logger.info(f"Collected {len(mp_records)} records from Materials Project")
        
        nist_records = self.fetch_from_nist_uci()
        all_records.extend(nist_records)
        self.logger.info(f"Collected {len(nist_records)} records from NIST/UCI")
        
        direct_records = self.fetch_from_verified_urls()
        all_records.extend(direct_records)
        self.logger.info(f"Collected {len(direct_records)} records from direct URLs")
        
        # Scrape PDFs
        pdf_paths = self.sources.get("pdfs", [])
        if pdf_paths:
            pdf_records = self.scrape_pdfs(pdf_paths)
            all_records.extend(pdf_records)
            self.logger.info(f"Collected {len(pdf_records)} records from PDFs")
        
        self.raw_data = all_records
        self.logger.info(f"Total aggregated records: {len(all_records)}")
        
        return all_records
    
    def save_raw_data(self, output_path: Optional[str] = None) -> str:
        """
        Save aggregated raw data to CSV.
        
        Args:
            output_path: Path to save the CSV file.
        
        Returns:
            Path to the saved file.
        """
        if not self.raw_data:
            raise IngestionError("No raw data to save. Run aggregate_all() first.")
        
        if output_path is None:
            project_root = Path(__file__).parent.parent.parent
            output_path = project_root / "data" / "raw" / "solder_hardness_raw.csv"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Flatten data for CSV
        flattened_data = []
        for record in self.raw_data:
            flat_record = {
                "source": record.get("source"),
                "citation": record.get("citation"),
                **record.get("data", {}),
                **record.get("properties", {}),
                "composition": json.dumps(record.get("composition", {}))
            }
            flattened_data.append(flat_record)
        
        if flattened_data:
            fieldnames = flattened_data[0].keys()
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_data)
        
        self.logger.info(f"Saved raw data to {output_path}")
        return str(output_path)

def main():
    """Main entry point for the aggregator."""
    logger = get_logger(__name__)
    logger.info("Starting Literature Aggregator")
    
    aggregator = LiteratureAggregator()
    records = aggregator.aggregate_all()
    
    if records:
        output_path = aggregator.save_raw_data()
        logger.info(f"Aggregation complete. Saved {len(records)} records to {output_path}")
    else:
        logger.warning("No records were aggregated.")
    
    return records

if __name__ == "__main__":
    main()
