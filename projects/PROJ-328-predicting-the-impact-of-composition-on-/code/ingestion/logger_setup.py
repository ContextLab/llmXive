"""
Logging setup and configuration for the ingestion module.
Provides structured logging for ingestion operations and data source citations.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

from utils.logging_config import get_logger
from config import get_data_processed_dir

# Constants
INGESTION_LOG_FILE = "data/processed/ingestion_log.txt"
CITATION_LOG_FILE = "data/processed/citations.json"


def setup_ingestion_logging():
    """
    Configure logging for ingestion operations.
    Returns a configured logger instance.
    """
    logger = get_logger("ingestion")
    
    # Ensure processed directory exists
    processed_dir = get_data_processed_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    log_file_path = processed_dir / INGESTION_LOG_FILE
    
    # File handler for ingestion operations
    if not log_file_path.exists():
        log_file_path.touch()
    
    file_handler = logging.FileHandler(log_file_path, mode='a')
    file_handler.setLevel(logging.DEBUG)
    
    # Format: timestamp | level | operation | details
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Avoid duplicate handlers
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        logger.addHandler(file_handler)
    
    return logger


class IngestionLogger:
    """
    Specialized logger for tracking ingestion operations and data source citations.
    """
    
    def __init__(self):
        self.logger = setup_ingestion_logging()
        self.citation_tracker = CitationTracker()
    
    def log_source_fetch_start(self, source_name: str, url: Optional[str] = None):
        """Log the start of a data fetch from a specific source."""
        msg = f"FETCH_START | Source: {source_name}"
        if url:
            msg += f" | URL: {url}"
        self.logger.info(msg)
    
    def log_source_fetch_success(self, source_name: str, records_count: int, duration_ms: float):
        """Log successful data fetch."""
        self.logger.info(
            f"FETCH_SUCCESS | Source: {source_name} | Records: {records_count} | Duration: {duration_ms:.2f}ms"
        )
    
    def log_source_fetch_failure(self, source_name: str, error_msg: str, retry_count: int = 0):
        """Log failed data fetch."""
        self.logger.warning(
            f"FETCH_FAILURE | Source: {source_name} | Error: {error_msg} | Retries: {retry_count}"
        )
    
    def log_partial_data_aggregation(self, sources_attempted: int, sources_success: int, total_records: int):
        """Log partial data aggregation status."""
        self.logger.info(
            f"PARTIAL_AGGREGATION | Sources Attempted: {sources_attempted} | "
            f"Sources Success: {sources_success} | Total Records: {total_records}"
        )
    
    def log_validation_start(self):
        """Log the start of data validation."""
        self.logger.info("VALIDATION_START | Beginning data validation pipeline")
    
    def log_validation_complete(self, total_records: int, passed: int, failed: int):
        """Log validation completion."""
        self.logger.info(
            f"VALIDATION_COMPLETE | Total: {total_records} | Passed: {passed} | Failed: {failed}"
        )
    
    def log_record_filtered(self, record_id: str, reason: str):
        """Log a filtered record."""
        self.logger.debug(f"RECORD_FILTERED | ID: {record_id} | Reason: {reason}")
    
    def log_pipeline_start(self):
        """Log the start of the full ingestion pipeline."""
        self.logger.info("PIPELINE_START | Starting full ingestion pipeline")
    
    def log_pipeline_complete(self, final_count: int, status: str):
        """Log pipeline completion."""
        self.logger.info(f"PIPELINE_COMPLETE | Final Count: {final_count} | Status: {status}")
    
    def register_citation(self, source_name: str, citation_info: dict):
        """
        Register a citation for a data source.
        
        Args:
            source_name: Name of the data source
            citation_info: Dictionary containing citation details (authors, year, title, url, etc.)
        """
        self.citation_tracker.add_citation(source_name, citation_info)
    
    def save_citations(self):
        """Save all registered citations to the citation log file."""
        self.citation_tracker.save_to_file()
    
    def get_citation_summary(self) -> dict:
        """Get a summary of all registered citations."""
        return self.citation_tracker.get_summary()


class CitationTracker:
    """
    Tracks and manages data source citations for the ingestion pipeline.
    """
    
    def __init__(self):
        self.citations: dict = {}
        self.processed_dir = get_data_processed_dir()
        self.citation_file = self.processed_dir / CITATION_LOG_FILE
    
    def add_citation(self, source_name: str, citation_info: dict):
        """
        Add a citation for a data source.
        
        Args:
            source_name: Unique identifier for the source
            citation_info: Dictionary with citation metadata
        """
        citation_info['_added_at'] = datetime.now().isoformat()
        citation_info['_source_name'] = source_name
        self.citations[source_name] = citation_info
    
    def save_to_file(self):
        """Save all citations to the JSON file."""
        if not self.processed_dir.exists():
            self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.citation_file, 'w', encoding='utf-8') as f:
            json.dump(self.citations, f, indent=2, default=str)
        
        # Also log to the main ingestion log
        logger = get_logger("ingestion")
        logger.info(f"CITATIONS_SAVED | Total citations: {len(self.citations)} | File: {self.citation_file}")
    
    def get_summary(self) -> dict:
        """
        Get a summary of all citations.
        
        Returns:
            Dictionary with source names and their citation metadata
        """
        return {
            source: {
                k: v for k, v in info.items() 
                if not k.startswith('_')
            }
            for source, info in self.citations.items()
        }
    
    def load_from_file(self) -> bool:
        """
        Load citations from the file if it exists.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.citation_file.exists():
            return False
        
        try:
            with open(self.citation_file, 'r', encoding='utf-8') as f:
                self.citations = json.load(f)
            return True
        except Exception as e:
            logger = get_logger("ingestion")
            logger.error(f"Failed to load citations: {e}")
            return False


def main():
    """
    Main entry point for testing the ingestion logging setup.
    """
    logger = IngestionLogger()
    
    # Test logging operations
    logger.log_pipeline_start()
    logger.log_source_fetch_start("Materials Project", "https://api.materialsproject.org")
    logger.log_source_fetch_success("Materials Project", 50, 123.45)
    logger.log_source_fetch_failure("NIST", "Connection timeout", 3)
    logger.log_partial_data_aggregation(2, 1, 50)
    
    # Test citation tracking
    logger.register_citation(
        "Materials Project",
        {
            "authors": ["Jain, A.", "Ong, S.P.", "et al."],
            "year": 2013,
            "title": "Commentary: The Materials Project: A materials genome approach to accelerating materials innovation",
            "url": "https://doi.org/10.1063/1.4812323",
            "type": "journal"
        }
    )
    
    logger.register_citation(
        "NIST",
        {
            "authors": ["NIST"],
            "year": 2023,
            "title": "NIST Solder Alloy Database",
            "url": "https://www.nist.gov/",
            "type": "database"
        }
    )
    
    logger.save_citations()
    logger.log_pipeline_complete(50, "PARTIAL")
    
    print("Ingestion logging test completed successfully.")
    print(f"Citation summary: {logger.get_citation_summary()}")


if __name__ == "__main__":
    main()
