import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import asdict

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatasetStatus:
    def __init__(self, accession: str, found: bool, path: str = None, checksum: str = None, reason: str = None):
        self.accession = accession
        self.found = found
        self.path = path
        self.checksum = checksum
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession": self.accession,
            "found": self.found,
            "path": self.path,
            "checksum": self.checksum,
            "reason": self.reason
        }

class DataGapResolver:
    def __init__(self, config: Config):
        self.config = config
        self.datasets: List[DatasetStatus] = []
        self.results_dir = config.results_dir
        self.data_dir = config.data_dir

    def check_dataset(self, accession: str) -> DatasetStatus:
        """
        Check if a dataset exists in the data directory and validate it.
        This simulates the check performed in T039/T040.
        In a real run, this would verify file existence and checksums.
        """
        logger.info(f"Checking dataset: {accession}")
        
        # Define expected file pattern (simulating T039 logic)
        # In real implementation, this would check for specific GEO raw count files
        expected_files = [
            f"{accession}_counts.h5ad",
            f"{accession}_raw_counts.csv",
            f"GSE{accession}_matrix.mtx"
        ]
        
        found_path = None
        checksum = None
        reason = None
        
        for potential_file in expected_files:
            file_path = self.data_dir / "raw" / potential_file
            if file_path.exists():
                found_path = str(file_path)
                # Calculate checksum if file exists
                try:
                    with open(file_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        checksum = file_hash
                    reason = "File found and validated"
                    break
                except Exception as e:
                    reason = f"File found but checksum validation failed: {str(e)}"
        
        if not found_path:
            reason = "No raw count matrix file found for this accession"
            logger.warning(f"Dataset {accession} not found: {reason}")
        
        return DatasetStatus(
            accession=accession,
            found=found_path is not None,
            path=found_path,
            checksum=checksum,
            reason=reason
        )

    def resolve_all(self) -> Dict[str, Any]:
        """
        Check all configured datasets and generate a report.
        Returns the final status (Full/Case-Study/Aborted) and details.
        """
        logger.info("Starting data gap resolution for all datasets")
        
        self.datasets = []
        found_count = 0
        
        for accession in self.config.dataset_accessions:
            status = self.check_dataset(accession)
            self.datasets.append(status)
            if status.found:
                found_count += 1
        
        # Determine final status based on T041 logic
        if found_count == 0:
            final_status = "Aborted"
            reason = "No datasets found. Pipeline cannot proceed."
        elif found_count == 1:
            final_status = "Case-Study"
            reason = f"Exactly 1 dataset found ({found_count}). Switching to Case-Study mode."
        else:
            final_status = "Full"
            reason = f"{found_count} datasets found. Proceeding with full analysis."
        
        report = {
            "timestamp": str(Path(self.results_dir).parent / "timestamp_placeholder"), # Will be overwritten by caller if needed
            "total_datasets_checked": len(self.datasets),
            "datasets_found": found_count,
            "datasets_missing": len(self.datasets) - found_count,
            "final_status": final_status,
            "status_reason": reason,
            "dataset_details": [ds.to_dict() for ds in self.datasets]
        }
        
        # Write report to file
        report_path = self.results_dir / "data_gap_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Data gap report written to: {report_path}")
        return report

def main():
    """
    Main entry point for data gap resolution and report generation.
    This function is called by main.py to check data availability.
    """
    config = Config()
    resolver = DataGapResolver(config)
    
    try:
        report = resolver.resolve_all()
        
        # Print summary to stdout for immediate visibility
        print(f"Data Gap Resolution Complete")
        print(f"Status: {report['final_status']}")
        print(f"Datasets Found: {report['datasets_found']}/{report['total_datasets_checked']}")
        
        if report['final_status'] == "Aborted":
            print("ERROR: No datasets found. Aborting pipeline.")
            sys.exit(1)
        
        return report
        
    except Exception as e:
        logger.error(f"Data gap resolution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
