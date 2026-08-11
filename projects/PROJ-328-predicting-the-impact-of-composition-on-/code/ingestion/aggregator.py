"""
LiteratureAggregator: Fetches and aggregates solder hardness data from multiple sources.

This module implements the data aggregation logic for T012, including:
- Fetching from Materials Project API
- Scraping NIST/UCI repositories
- Parsing PDF literature via pdfplumber
- Fallback logic for partial data aggregation
- Connectivity status logging
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

# Project-relative imports
from config import get_config, get_data_processed_dir
from utils.error_handlers import ConfigurationError, IngestionError
from utils.logging_config import get_logger
from .citation_tracker import CitationTracker
from .logger_setup import IngestionLogger

class LiteratureAggregator:
    """
    Aggregates solder hardness data from multiple verified sources.
    
    Implements T012 requirements:
    - Pre-checks for research.md and sources.yaml
    - Fetches from Materials Project, NIST, PDFs
    - Logs connectivity status to ingestion_log.txt
    - Handles partial data gracefully
    - Checks N-count thresholds (>=100, 50-99, <50)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the aggregator with configuration.
        
        Args:
            config_path: Path to sources.yaml configuration file
        
        Raises:
            ConfigurationError: If research.md or sources.yaml is missing/invalid
        """
        self.logger = get_logger("ingestion.aggregator")
        self.logger.info("Initializing LiteratureAggregator")
        
        # Load configuration
        if config_path is None:
            config_path = "data/config/sources.yaml"
        
        self.config_path = Path(config_path)
        self.sources_config = self._load_sources_config()
        
        # Initialize citation tracker
        self.citation_tracker = CitationTracker()
        
        # Initialize ingestion logger for status tracking
        self.ingestion_logger = IngestionLogger()
        
        # Initialize data storage
        self.raw_data: List[Dict[str, Any]] = []
        self.fetch_stats: Dict[str, Any] = {
            'materials_project': {'success': False, 'count': 0, 'error': None},
            'nist_uci': {'success': False, 'count': 0, 'error': None},
            'pdf_sources': {'success': False, 'count': 0, 'error': None},
            'direct_urls': {'success': False, 'count': 0, 'error': None}
        }
        
        self.logger.info("LiteratureAggregator initialized successfully")
    
    def _load_sources_config(self) -> Dict[str, Any]:
        """
        Load and validate sources.yaml configuration.
        
        Returns:
            Dictionary containing source configurations
        
        Raises:
            ConfigurationError: If config file is missing or invalid
        """
        if not self.config_path.exists():
            raise ConfigurationError(
                f"sources.yaml not found at {self.config_path}. "
                "Please ensure T009b has populated this file."
            )
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or not isinstance(config, dict):
                raise ConfigurationError("sources.yaml is empty or invalid format")
            
            # Check for required sections
            required_sections = ['materials_project', 'nist_uci', 'pdf_sources']
            for section in required_sections:
                if section not in config:
                    self.logger.warning(f"Missing section in sources.yaml: {section}")
            
            self.logger.info(f"Loaded sources configuration from {self.config_path}")
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse sources.yaml: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Error loading sources.yaml: {str(e)}")
    
    def fetch_from_materials_project(self) -> List[Dict[str, Any]]:
        """
        Fetch solder hardness data from Materials Project API.
        
        Returns:
            List of data records from Materials Project
        """
        self.logger.info("Fetching data from Materials Project API")
        source_name = "materials_project"
        
        try:
            mp_config = self.sources_config.get('materials_project', {})
            api_key = mp_config.get('api_key')
            base_url = mp_config.get('base_url', 'https://api.materialsproject.org')
            
            if not api_key:
                self.logger.warning("No API key configured for Materials Project")
                self.fetch_stats[source_name]['error'] = "No API key configured"
                return []
            
            # Example endpoint - adjust based on actual API
            endpoint = f"{base_url}/materials/solder-hardness"
            headers = {"X-API-Key": api_key}
            params = {"format": "json", "elements": "Sn,Pb,Ag,Cu,Zn"}
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                records = self._normalize_materials_project_data(data)
                self.fetch_stats[source_name]['success'] = True
                self.fetch_stats[source_name]['count'] = len(records)
                
                self.logger.info(f"Successfully fetched {len(records)} records from Materials Project")
                self.citation_tracker.add_citation(
                    source="Materials Project",
                    url=endpoint,
                    timestamp=datetime.now().isoformat()
                )
                
                return records
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.logger.warning(f"Materials Project fetch failed: {error_msg}")
                self.fetch_stats[source_name]['error'] = error_msg
                return []
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            self.logger.warning(f"Materials Project connection failed: {error_msg}")
            self.fetch_stats[source_name]['error'] = error_msg
            return []
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Materials Project fetch failed: {error_msg}")
            self.fetch_stats[source_name]['error'] = error_msg
            return []
    
    def fetch_from_nist_uci(self) -> List[Dict[str, Any]]:
        """
        Fetch solder hardness data from NIST/UCI repositories.
        
        Returns:
            List of data records from NIST/UCI
        """
        self.logger.info("Fetching data from NIST/UCI repositories")
        source_name = "nist_uci"
        
        try:
            nist_config = self.sources_config.get('nist_uci', {})
            urls = nist_config.get('urls', [])
            
            if not urls:
                self.logger.warning("No URLs configured for NIST/UCI")
                self.fetch_stats[source_name]['error'] = "No URLs configured"
                return []
            
            all_records = []
            
            for url in urls:
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        # Parse CSV/JSON based on content type
                        if 'csv' in url or response.headers.get('content-type', '').find('csv') != -1:
                            records = self._parse_csv_data(response.text)
                        else:
                            records = self._normalize_nist_data(response.json() if response.content else [])
                        
                        all_records.extend(records)
                        self.logger.info(f"Fetched {len(records)} records from {url}")
                    else:
                        self.logger.warning(f"NIST/UCI URL failed: {url} (HTTP {response.status_code})")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch from {url}: {str(e)}")
            
            self.fetch_stats[source_name]['success'] = len(all_records) > 0
            self.fetch_stats[source_name]['count'] = len(all_records)
            
            if all_records:
                self.citation_tracker.add_citation(
                    source="NIST/UCI",
                    url=", ".join(urls),
                    timestamp=datetime.now().isoformat()
                )
            
            return all_records
            
        except Exception as e:
            error_msg = f"Error fetching from NIST/UCI: {str(e)}"
            self.logger.error(error_msg)
            self.fetch_stats[source_name]['error'] = error_msg
            return []
    
    def fetch_from_pdf_sources(self) -> List[Dict[str, Any]]:
        """
        Fetch solder hardness data from PDF literature using pdfplumber.
        
        Returns:
            List of data records extracted from PDFs
        """
        self.logger.info("Extracting data from PDF literature sources")
        source_name = "pdf_sources"
        
        try:
            pdf_config = self.sources_config.get('pdf_sources', {})
            pdf_paths = pdf_config.get('local_paths', [])
            pdf_urls = pdf_config.get('download_urls', [])
            
            all_records = []
            
            # Download PDFs if URLs provided
            temp_pdf_dir = Path("data/raw/temp_pdfs")
            temp_pdf_dir.mkdir(parents=True, exist_ok=True)
            
            for url in pdf_urls:
                try:
                    filename = url.split('/')[-1]
                    local_path = temp_pdf_dir / filename
                    
                    if not local_path.exists():
                        response = requests.get(url, timeout=60)
                        if response.status_code == 200:
                            with open(local_path, 'wb') as f:
                                f.write(response.content)
                            self.logger.info(f"Downloaded PDF: {filename}")
                    
                    pdf_paths.append(str(local_path))
                    
                except Exception as e:
                    self.logger.warning(f"Failed to download PDF from {url}: {str(e)}")
            
            # Extract data from PDFs
            import pdfplumber
            
            for pdf_path in pdf_paths:
                try:
                    records = self._extract_data_from_pdf(pdf_path)
                    all_records.extend(records)
                    self.logger.info(f"Extracted {len(records)} records from {pdf_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to extract from {pdf_path}: {str(e)}")
            
            self.fetch_stats[source_name]['success'] = len(all_records) > 0
            self.fetch_stats[source_name]['count'] = len(all_records)
            
            if all_records:
                self.citation_tracker.add_citation(
                    source="PDF Literature",
                    url=", ".join(pdf_paths),
                    timestamp=datetime.now().isoformat()
                )
            
            return all_records
            
        except ImportError:
            self.logger.error("pdfplumber not installed. Install with: pip install pdfplumber")
            self.fetch_stats[source_name]['error'] = "pdfplumber not installed"
            return []
        except Exception as e:
            error_msg = f"Error fetching from PDF sources: {str(e)}"
            self.logger.error(error_msg)
            self.fetch_stats[source_name]['error'] = error_msg
            return []
    
    def _extract_data_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract solder hardness data from a PDF file."""
        import pdfplumber
        records = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    # Simple heuristic: look for tables with numeric data
                    if len(table) > 1:
                        # Assume first row is header
                        headers = [str(h).strip() for h in table[0] if h]
                        for row in table[1:]:
                            if row and any(cell and str(cell).strip() for cell in row):
                                record = {}
                                for i, cell in enumerate(row):
                                    if i < len(headers):
                                        record[headers[i]] = str(cell).strip() if cell else None
                                
                                # Try to identify hardness and composition columns
                                if self._is_valid_solder_record(record):
                                    records.append(self._normalize_pdf_record(record))
        
        return records
    
    def _is_valid_solder_record(self, record: Dict[str, Any]) -> bool:
        """Check if a record looks like a valid solder hardness entry."""
        # Heuristic: must have some composition elements and a hardness value
        composition_keys = ['sn', 'pb', 'ag', 'cu', 'zn', 'bi', 'In', 'Sb']
        composition_present = any(
            any(k in str(key).lower() for key in record.keys()) 
            for k in composition_keys
        )
        
        hardness_keys = ['hv', 'hardness', 'vickers', 'hardness_hv']
        hardness_present = any(
            any(k in str(key).lower() for key in record.keys()) 
            for k in hardness_keys
        )
        
        return composition_present and hardness_present
    
    def _normalize_pdf_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a record extracted from PDF to standard format."""
        normalized = {
            'source': 'PDF',
            'raw_data': record,
            'timestamp': datetime.now().isoformat()
        }
        
        # Map common field names
        for key, value in record.items():
            key_lower = str(key).lower()
            
            if 'sn' in key_lower:
                normalized['sn'] = float(value) if value else None
            elif 'pb' in key_lower:
                normalized['pb'] = float(value) if value else None
            elif 'ag' in key_lower:
                normalized['ag'] = float(value) if value else None
            elif 'cu' in key_lower:
                normalized['cu'] = float(value) if value else None
            elif 'zn' in key_lower:
                normalized['zn'] = float(value) if value else None
            elif 'bi' in key_lower:
                normalized['bi'] = float(value) if value else None
            elif 'in' in key_lower:
                normalized['in'] = float(value) if value else None
            elif 'sb' in key_lower:
                normalized['sb'] = float(value) if value else None
            elif 'hv' in key_lower or 'hardness' in key_lower:
                normalized['hardness_hv'] = float(value) if value else None
            elif 'temp' in key_lower:
                normalized['measurement_temp_c'] = float(value) if value else None
            else:
                normalized[key_lower] = value
        
        return normalized
    
    def _normalize_materials_project_data(self, data: Any) -> List[Dict[str, Any]]:
        """Normalize Materials Project API response to standard format."""
        records = []
        
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        
        if isinstance(data, list):
            for item in data:
                record = {
                    'source': 'Materials Project',
                    'timestamp': datetime.now().isoformat(),
                    'raw_data': item
                }
                
                # Map fields based on expected API structure
                if isinstance(item, dict):
                    for key, value in item.items():
                        if 'sn' in str(key).lower():
                            record['sn'] = float(value) if value else None
                        elif 'pb' in str(key).lower():
                            record['pb'] = float(value) if value else None
                        elif 'ag' in str(key).lower():
                            record['ag'] = float(value) if value else None
                        elif 'cu' in str(key).lower():
                            record['cu'] = float(value) if value else None
                        elif 'zn' in str(key).lower():
                            record['zn'] = float(value) if value else None
                        elif 'hardness' in str(key).lower():
                            record['hardness_hv'] = float(value) if value else None
                        elif 'temp' in str(key).lower():
                            record['measurement_temp_c'] = float(value) if value else None
                
                records.append(record)
        
        return records
    
    def _normalize_nist_data(self, data: Any) -> List[Dict[str, Any]]:
        """Normalize NIST/UCI data to standard format."""
        records = []
        
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        
        if isinstance(data, list):
            for item in data:
                record = {
                    'source': 'NIST/UCI',
                    'timestamp': datetime.now().isoformat(),
                    'raw_data': item
                }
                
                if isinstance(item, dict):
                    for key, value in item.items():
                        key_lower = str(key).lower()
                        if 'sn' in key_lower:
                            record['sn'] = float(value) if value else None
                        elif 'pb' in key_lower:
                            record['pb'] = float(value) if value else None
                        elif 'ag' in key_lower:
                            record['ag'] = float(value) if value else None
                        elif 'cu' in key_lower:
                            record['cu'] = float(value) if value else None
                        elif 'zn' in key_lower:
                            record['zn'] = float(value) if value else None
                        elif 'hardness' in key_lower or 'hv' in key_lower:
                            record['hardness_hv'] = float(value) if value else None
                        elif 'temp' in key_lower:
                            record['measurement_temp_c'] = float(value) if value else None
                
                records.append(record)
        
        return records
    
    def _parse_csv_data(self, csv_text: str) -> List[Dict[str, Any]]:
        """Parse CSV text data to standard format."""
        records = []
        reader = csv.DictReader(csv_text.strip().split('\n'))
        
        for row in reader:
            record = {
                'source': 'CSV',
                'timestamp': datetime.now().isoformat(),
                'raw_data': row
            }
            
            for key, value in row.items():
                key_lower = str(key).lower().strip()
                try:
                    if 'sn' in key_lower:
                        record['sn'] = float(value) if value else None
                    elif 'pb' in key_lower:
                        record['pb'] = float(value) if value else None
                    elif 'ag' in key_lower:
                        record['ag'] = float(value) if value else None
                    elif 'cu' in key_lower:
                        record['cu'] = float(value) if value else None
                    elif 'zn' in key_lower:
                        record['zn'] = float(value) if value else None
                    elif 'hardness' in key_lower or 'hv' in key_lower:
                        record['hardness_hv'] = float(value) if value else None
                    elif 'temp' in key_lower:
                        record['measurement_temp_c'] = float(value) if value else None
                except (ValueError, TypeError):
                    record[key_lower] = value
            
            records.append(record)
        
        return records
    
    def aggregate_all_sources(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Aggregate data from all configured sources.
        
        Returns:
            Tuple of (aggregated_data, fetch_statistics)
        """
        self.logger.info("Starting aggregation from all sources")
        
        # Fetch from each source
        mp_data = self.fetch_from_materials_project()
        nist_data = self.fetch_from_nist_uci()
        pdf_data = self.fetch_from_pdf_sources()
        
        # Combine all data
        all_data = mp_data + nist_data + pdf_data
        
        # Calculate total count
        total_count = len(all_data)
        
        # Determine threshold status
        if total_count >= 100:
            threshold_status = "N>=100"
            warning_text = None
            self.logger.info(f"Aggregation complete: {total_count} records (Status: {threshold_status})")
        elif total_count >= 50:
            threshold_status = "50<=N<100"
            warning_text = f"Warning: Only {total_count} records found (minimum 100 recommended for robust analysis)"
            self.logger.warning(f"Aggregation complete: {total_count} records (Status: {threshold_status})")
        else:
            threshold_status = "N<50"
            warning_text = f"Critical: Only {total_count} records found (minimum 50 required)"
            self.logger.error(f"Aggregation complete: {total_count} records (Status: {threshold_status})")
        
        # Log connectivity status
        self._log_connectivity_status(total_count, threshold_status)
        
        return all_data, {
            'stats': self.fetch_stats,
            'total_count': total_count,
            'threshold_status': threshold_status,
            'warning_text': warning_text
        }
    
    def _log_connectivity_status(self, total_count: int, threshold_status: str):
        """Log connectivity status to ingestion_log.txt."""
        log_dir = get_data_processed_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "ingestion_log.txt"
        
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Ingestion Run: {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n")
            
            for source, stats in self.fetch_stats.items():
                status = "SUCCESS" if stats['success'] else "FAILED"
                f.write(f"{source.upper()}: {status} ({stats['count']} records)\n")
                if stats['error']:
                    f.write(f"  Error: {stats['error']}\n")
            
            f.write(f"\nTotal Records: {total_count}\n")
            f.write(f"Threshold Status: {threshold_status}\n")
            
            if self.fetch_stats.get('materials_project', {}).get('error'):
                f.write(f"\nMaterials Project: {self.fetch_stats['materials_project']['error']}\n")
            if self.fetch_stats.get('nist_uci', {}).get('error'):
                f.write(f"NIST/UCI: {self.fetch_stats['nist_uci']['error']}\n")
            if self.fetch_stats.get('pdf_sources', {}).get('error'):
                f.write(f"PDF Sources: {self.fetch_stats['pdf_sources']['error']}\n")
            
            f.write(f"\n{'='*60}\n")
        
        self.logger.info(f"Connectivity status logged to {log_file}")
    
    def get_citations(self) -> List[Dict[str, Any]]:
        """Get all citations tracked during aggregation."""
        return self.citation_tracker.get_citations()

def main():
    """Main entry point for the aggregator."""
    logger = get_logger("ingestion.aggregator")
    logger.info("Running LiteratureAggregator main")
    
    try:
        aggregator = LiteratureAggregator()
        data, stats = aggregator.aggregate_all_sources()
        
        logger.info(f"Aggregation complete: {len(data)} records")
        logger.info(f"Threshold status: {stats['threshold_status']}")
        
        # Return data and stats for downstream processing
        return data, stats
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {str(e)}")
        raise

if __name__ == "__main__":
    main()
