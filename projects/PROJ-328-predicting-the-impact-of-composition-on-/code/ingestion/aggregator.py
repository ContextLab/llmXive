"""
Aggregator module for fetching and combining solder hardness data from multiple sources.
"""

import os
import csv
import requests
import logging
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from utils.logging_config import get_logger
from utils.error_handlers import IngestionError, ConfigurationError
from config import get_config, get_data_raw_dir, get_data_processed_dir

logger = get_logger(__name__)


class LiteratureAggregator:
    """
    Aggregates solder hardness data from verified sources:
    1. Materials Project API
    2. NIST/UCI repositories
    3. Direct URLs from sources.yaml
    4. Published Literature via PDF scraping (pdfplumber)
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the aggregator with configuration.

        Args:
            config_path: Path to sources.yaml configuration file.
        """
        self.config_path = config_path or Path("data/config/sources.yaml")
        self.config = self._load_config()
        self.raw_dir = get_data_raw_dir()
        self.processed_dir = get_data_processed_dir()
        self.ingestion_log = self.processed_dir / "ingestion_log.txt"

    def _load_config(self) -> Dict[str, Any]:
        """Load sources configuration from YAML file."""
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Sources configuration file not found: {self.config_path}. "
                "Please run T009b to populate sources.yaml."
            )

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        if not config or not config.get('sources'):
            raise ConfigurationError(
                f"Sources configuration file is empty or missing 'sources' key: {self.config_path}"
            )

        return config

    def _log_status(self, source: str, status: str, message: str = ""):
        """Log connectivity and aggregation status to ingestion_log.txt."""
        timestamp = pd.Timestamp.now().isoformat()
        log_entry = f"[{timestamp}] [{source}] {status}: {message}\n"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        with open(self.ingestion_log, 'a') as f:
            f.write(log_entry)

        logger.info(log_entry.strip())

    def fetch_materials_project(self) -> List[Dict[str, Any]]:
        """
        Fetch data from Materials Project API.
        Requires MP_API_KEY in environment variables.
        """
        api_key = os.getenv("MP_API_KEY")
        if not api_key:
            self._log_status("Materials Project", "SKIPPED", "API key not found in environment")
            return []

        try:
            # Placeholder for actual API call logic
            # This would typically query the Materials Project API for solder alloys
            self._log_status("Materials Project", "CONNECTED", "API key found, attempting fetch")
            # Simulating a fetch structure - actual implementation would use requests
            # data = requests.get(...).json()
            self._log_status("Materials Project", "PARTIAL", "Fetch logic requires live API integration")
            return []
        except Exception as e:
            self._log_status("Materials Project", "FAILED", str(e))
            return []

    def fetch_nist_uci(self) -> List[Dict[str, Any]]:
        """
        Fetch data from NIST/UCI repositories.
        """
        sources = self.config.get('sources', {})
        nist_urls = sources.get('nist_uci', [])

        if not nist_urls:
            self._log_status("NIST/UCI", "SKIPPED", "No URLs configured in sources.yaml")
            return []

        aggregated_data = []
        for url in nist_urls:
            try:
                self._log_status("NIST/UCI", "CONNECTED", f"Fetching from {url}")
                # Placeholder for actual fetch logic
                # response = requests.get(url)
                # data = parse_csv_or_json(response)
                self._log_status("NIST/UCI", "PARTIAL", f"Fetch logic for {url} requires live data")
            except Exception as e:
                self._log_status("NIST/UCI", "FAILED", f"Error fetching {url}: {str(e)}")

        return aggregated_data

    def fetch_direct_urls(self) -> List[Dict[str, Any]]:
        """
        Fetch data from direct URLs specified in sources.yaml.
        """
        sources = self.config.get('sources', {})
        direct_urls = sources.get('direct_urls', [])

        if not direct_urls:
            self._log_status("Direct URLs", "SKIPPED", "No URLs configured in sources.yaml")
            return []

        aggregated_data = []
        for url_info in direct_urls:
            url = url_info.get('url')
            source_name = url_info.get('name', 'Unknown')

            if not url:
                continue

            try:
                self._log_status(source_name, "CONNECTED", f"Fetching from {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                # Attempt to parse based on content type
                if 'application/json' in response.headers.get('Content-Type', ''):
                    data = response.json()
                elif 'text/csv' in response.headers.get('Content-Type', ''):
                    # Read as CSV string
                    data = pd.read_csv(pd.io.common.StringIO(response.text)).to_dict('records')
                else:
                    self._log_status(source_name, "WARNING", f"Unknown content type for {url}")
                    continue

                aggregated_data.extend(data)
                self._log_status(source_name, "SUCCESS", f"Retrieved {len(data)} records")

            except requests.exceptions.RequestException as e:
                self._log_status(source_name, "FAILED", f"Connection error: {str(e)}")
            except Exception as e:
                self._log_status(source_name, "FAILED", f"Parse error: {str(e)}")

        return aggregated_data

    def scrape_literature_pdfs(self) -> List[Dict[str, Any]]:
        """
        Scrape data from PDF literature using pdfplumber.
        Requires PDF files to be available locally or downloadable.
        """
        sources = self.config.get('sources', {})
        pdf_sources = sources.get('literature_pdfs', [])

        if not pdf_sources:
            self._log_status("Literature PDFs", "SKIPPED", "No PDF sources configured")
            return []

        aggregated_data = []
        # Note: pdfplumber implementation would go here
        # This is a placeholder for the scaffolding task

        self._log_status("Literature PDFs", "INFO", "PDF scraping logic requires pdfplumber implementation")
        return aggregated_data

    def aggregate(self) -> pd.DataFrame:
        """
        Aggregate data from all configured sources.
        Returns a combined DataFrame.
        """
        all_data = []

        # Fetch from all sources
        mp_data = self.fetch_materials_project()
        all_data.extend(mp_data)

        nist_data = self.fetch_nist_uci()
        all_data.extend(nist_data)

        direct_data = self.fetch_direct_urls()
        all_data.extend(direct_data)

        pdf_data = self.scrape_literature_pdfs()
        all_data.extend(pdf_data)

        if not all_data:
            self._log_status("Aggregation", "WARNING", "No data retrieved from any source")
            # Return empty DataFrame with expected schema
            return pd.DataFrame(columns=[
                'alloy_id', 'composition', 'hardness_hv', 'measurement_temp_c',
                'elemental_breakdown'
            ])

        df = pd.DataFrame(all_data)
        self._log_status("Aggregation", "SUCCESS", f"Total records aggregated: {len(df)}")

        return df

    def save_raw_data(self, df: pd.DataFrame, filename: str = "solder_hardness_raw.csv"):
        """Save aggregated raw data to CSV."""
        output_path = self.raw_dir / filename
        df.to_csv(output_path, index=False)
        self._log_status("Save", "SUCCESS", f"Raw data saved to {output_path}")
        return output_path


def main():
    """Main entry point for the aggregator."""
    logger.info("Starting LiteratureAggregator")

    try:
        aggregator = LiteratureAggregator()
        df = aggregator.aggregate()

        if len(df) > 0:
            output_path = aggregator.save_raw_data(df)
            logger.info(f"Aggregation complete. Output: {output_path}")
        else:
            logger.warning("No data aggregated. Check sources.yaml and connectivity.")

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise


if __name__ == "__main__":
    main()
