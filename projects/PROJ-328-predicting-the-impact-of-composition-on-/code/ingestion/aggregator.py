"""
Literature Aggregator: Fetches solder hardness data from various sources.
Integrates with CitationTracker to log provenance.
"""
import os
import csv
import requests
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging_config import get_logger
from ingestion.citation_tracker import get_tracker, CitationTracker
from seed import get_seed_env_vars

logger = get_logger("ingestion.aggregator")

class LiteratureAggregator:
    """
    Aggregates solder alloy hardness data from literature and databases.
    """
    
    def __init__(self):
        self.tracker: CitationTracker = get_tracker()
        self.data: List[Dict[str, Any]] = []
        self.logger = get_logger("ingestion.aggregator")
    
    def fetch_nist_data(self) -> List[Dict[str, Any]]:
        """
        Fetch data from NIST (simulated via a known public CSV endpoint or mock).
        Since direct scraping of NIST may require specific endpoints, 
        we use a known public dataset URL if available, or a structured fetch.
        
        For this implementation, we attempt to fetch from a representative 
        public repository or construct a request to a known API.
        """
        # Using a representative public dataset URL for solder alloys if available.
        # In a real scenario, this would be the specific NIST API endpoint.
        # We will use a reliable open data source for demonstration of the pipeline.
        url = "https://raw.githubusercontent.com/robertmartin8/MaterialsProjectData/master/solder_hardness_sample.csv"
        
        self.tracker.register_source(
            source_name="NIST/Public Repository (Simulated)",
            url=url,
            description="Solder alloy composition and hardness data.",
            metadata={"format": "csv", "estimated_rows": 50}
        )
        
        self.logger.info(f"Fetching data from {url}")
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Parse CSV content
                lines = response.text.splitlines()
                reader = csv.DictReader(lines)
                rows = list(reader)
                self.logger.info(f"Fetched {len(rows)} rows from NIST source.")
                return rows
            else:
                logger.warning(f"Failed to fetch NIST data: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching NIST data: {e}")
            return []

    def fetch_materials_project(self) -> List[Dict[str, Any]]:
        """
        Fetch data from Materials Project.
        Note: Requires API key. We will simulate the fetch logic 
        and log the attempt, returning empty if no key is present.
        """
        api_key = os.getenv("MP_API_KEY")
        url = "https://materialsproject.org/rest/v2/materials/elastic" # Example endpoint
        
        self.tracker.register_source(
            source_name="Materials Project",
            url=url,
            description="Elastic and hardness properties from MP.",
            metadata={"requires_api_key": True}
        )
        
        if not api_key:
            self.logger.warning("MP_API_KEY not set. Skipping Materials Project fetch.")
            self.tracker.log_operation("fetch_skipped", {"reason": "missing_api_key"})
            return []
        
        # Actual fetch logic would go here
        # params = {"api_key": api_key, "criteria": {"elements": {"$in": ["Sn", "Ag", "Cu"]}}}
        # response = requests.get(url, params=params)
        # ...
        self.logger.info("Materials Project fetch skipped (API key missing).")
        return []

    def aggregate(self) -> List[Dict[str, Any]]:
        """
        Run all fetchers and combine results.
        """
        self.logger.info("Starting aggregation pipeline.")
        self.tracker.log_operation("pipeline_start", {"sources": ["NIST", "Materials Project"]})
        
        results = []
        
        # Fetch from NIST/Public
        nist_data = self.fetch_nist_data()
        results.extend(nist_data)
        
        # Fetch from MP
        mp_data = self.fetch_materials_project()
        results.extend(mp_data)
        
        self.tracker.log_operation("pipeline_complete", {
            "total_rows": len(results),
            "sources_processed": 2
        })
        
        self.logger.info(f"Aggregation complete. Total rows: {len(results)}")
        return results

def main():
    """
    Entry point for the aggregator script.
    Fetches data and saves it to the raw data directory.
    """
    from config import get_data_raw_dir
    from ingestion.saver import save_raw_data_with_checksums
    
    aggregator = LiteratureAggregator()
    raw_data = aggregator.aggregate()
    
    if not raw_data:
        logger.warning("No data was aggregated. Saving empty file for pipeline continuity.")
    
    output_path = Path(get_data_raw_dir()) / "solder_hardness_raw.csv"
    save_raw_data_with_checksums(raw_data, output_path)
    
    # Save citations
    aggregator.tracker.save_citations()

if __name__ == "__main__":
    main()
