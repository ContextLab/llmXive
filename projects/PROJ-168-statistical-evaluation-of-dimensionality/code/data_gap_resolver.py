"""
Data Gap Resolver – Phase 0

This script ensures that raw count matrices for the required GEO
accessions are present. It attempts to download real data from GEO
using the utilities in code/download.py.

The resolver:
  1. Iterates over configured GEO accessions.
  2. Attempts to download raw count matrices into data/raw/<accession>/.
  3. Records availability, source URLs, and checksums in data/manifest.json.
  4. Enforces the three-dataset requirement: if < 3 datasets are available,
     it writes a summary and exits with code 1.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Project imports
from config import Config
from download import calculate_md5, download_dataset, DownloadError, LabelValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class DatasetStatus:
    """Enum-like container for dataset availability status."""
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"

class DataGapResolver:
    """
    Resolves the Phase 0 data-gap by ensuring that raw count matrices for the
    configured GEO accessions exist, are valid, and are recorded in a manifest.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config if config is not None else Config()
        self.raw_dir: Path = self.config.RAW_DATA_DIR
        self.results_dir: Path = self.config.RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.accessions: List[str] = self.config.ACCESSIONS

    def _get_source_url(self, accession: str) -> str:
        """
        Returns the base GEO URL for the accession.
        In a production environment, this would be the specific file URL.
        """
        return f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"

    def resolve(self) -> Tuple[str, List[str], List[str]]:
        """
        Main driver that attempts to obtain each dataset and writes the manifest.
        Returns (status, found_list, missing_list).
        """
        manifest_entries: List[Dict[str, Any]] = []
        found_datasets: List[str] = []
        missing_datasets: List[str] = []

        for accession in self.accessions:
            logger.info(f"Attempting to resolve data for {accession}...")
            try:
                # Use the verified download utility to get real data
                # This will raise DownloadError or LabelValidationError if it fails
                file_path_str = download_dataset(accession, str(self.raw_dir))
                file_path = Path(file_path_str)
                
                checksum = calculate_md5(file_path_str)
                
                status = DatasetStatus.AVAILABLE
                found_datasets.append(accession)
                
                entry = {
                    "dataset_id": accession,
                    "source_url": self._get_source_url(accession),
                    "status": status,
                    "checksum": checksum,
                    "raw_file_path": str(file_path),
                    "processed_file_path": None,
                }
            except (DownloadError, LabelValidationError, Exception) as e:
                logger.warning(f"Dataset {accession} is unavailable: {e}")
                status = DatasetStatus.UNAVAILABLE
                missing_datasets.append(accession)
                
                entry = {
                    "dataset_id": accession,
                    "source_url": self._get_source_url(accession),
                    "status": status,
                    "checksum": None,
                    "raw_file_path": None,
                    "processed_file_path": None,
                }
            
            manifest_entries.append(entry)

        # Write the manifest conforming to dataset.schema.yaml
        manifest_path = Path("data") / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest_entries, f, indent=2)
        logger.info(f"Manifest written to {manifest_path}")

        # Enforce the three-dataset requirement
        available_count = len(found_datasets)
        if available_count < 3:
            summary_path = self.results_dir / "data_gap_summary.txt"
            summary_msg = (
                f"Data-gap resolution failed: only {available_count} "
                f"dataset(s) available (minimum required: 3). Pipeline abort."
            )
            with summary_path.open("w", encoding="utf-8") as f:
                f.write(summary_msg + "\n")
            logger.error(summary_msg)
            
            # The task explicitly requires exit 1 if count < 3
            # We return "insufficient" so the main orchestrator can also handle it,
            # but the script entry point will call sys.exit(1).
            return "insufficient", found_datasets, missing_datasets

        return "enough", found_datasets, missing_datasets

def main() -> None:
    """
    CLI entry point. Executes resolution and exits based on the 3-dataset rule.
    """
    resolver = DataGapResolver()
    status, found, missing = resolver.resolve()
    
    if status == "insufficient":
        sys.exit(1)
    
    logger.info("Data gap resolution successful: 3 or more datasets available.")
    sys.exit(0)

if __name__ == "__main__":
    # To allow the orchestrator to call the class, but provide a CLI exit
    # We wrap the logic in a function
    def run_cli():
        resolver = DataGapResolver()
        status, found, missing = resolver.resolve()
        if status == "insufficient":
            sys.exit(1)
        sys.exit(0)
    
    run_cli()