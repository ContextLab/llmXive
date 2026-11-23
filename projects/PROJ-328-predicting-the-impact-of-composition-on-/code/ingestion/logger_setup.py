import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
import csv
from config import get_log_level, get_log_format
from utils.logging_config import get_logger

class IngestionLogger:
    """
    Specialized logger for ingestion operations that tracks:
    1. Standard operation logs (info, warnings, errors)
    2. Data source citations and fetch status
    3. Aggregation metrics
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.processed_dir = self.project_root / "data" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.processed_dir / "ingestion_log.txt"
        self.citation_log_file = self.processed_dir / "source_citations.json"
        self.metrics_log_file = self.processed_dir / "ingestion_metrics.json"
        
        # Initialize log files if they don't exist
        if not self.log_file.exists():
            self.log_file.touch()
        if not self.citation_log_file.exists():
            with open(self.citation_log_file, 'w') as f:
                json.dump({"sources": [], "timestamp": datetime.now().isoformat()}, f, indent=2)
        if not self.metrics_log_file.exists():
            with open(self.metrics_log_file, 'w') as f:
                json.dump({"total_records": 0, "sources_processed": [], "errors": []}, f, indent=2)

        # Configure standard logger
        self.logger = get_logger("ingestion")
        self.logger.setLevel(get_log_level())

        # Add file handler for ingestion log
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(get_log_level())
        formatter = logging.Formatter(
            fmt=get_log_format(),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Avoid duplicate handlers
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(self.log_file) 
                  for h in self.logger.handlers):
            self.logger.addHandler(file_handler)

        # Track citations
        self.citation_tracker = CitationTracker(self.citation_log_file)

    def log_source_fetch(self, source_name: str, url: str, status: str, 
                       records_fetched: int = 0, error_msg: Optional[str] = None):
        """Log a data source fetch attempt with citation details."""
        timestamp = datetime.now().isoformat()
        
        log_msg = f"[{timestamp}] SOURCE: {source_name} | URL: {url} | STATUS: {status}"
        if records_fetched > 0:
            log_msg += f" | RECORDS: {records_fetched}"
        if error_msg:
            log_msg += f" | ERROR: {error_msg}"
        
        self.logger.info(log_msg)
        
        # Update citation tracker
        self.citation_tracker.add_citation(
            source_name=source_name,
            url=url,
            status=status,
            records_fetched=records_fetched,
            error=error_msg,
            timestamp=timestamp
        )

    def log_aggregation_step(self, step_name: str, details: dict):
        """Log an aggregation step with metadata."""
        timestamp = datetime.now().isoformat()
        self.logger.info(f"[{timestamp}] AGGREGATION: {step_name} | DETAILS: {json.dumps(details)}")
        
        # Update metrics
        self._update_metrics({
            "step": step_name,
            "details": details,
            "timestamp": timestamp
        })

    def log_validation_result(self, total_records: int, filtered_records: int, 
                            reason_codes: list):
        """Log validation results."""
        timestamp = datetime.now().isoformat()
        self.logger.info(
            f"[{timestamp}] VALIDATION: Total={total_records}, "
            f"Filtered={filtered_records}, "
            f"Reasons={len(reason_codes)}"
        )

    def log_partial_data_warning(self, source_name: str, reason: str):
        """Log a warning when a source returns partial data."""
        timestamp = datetime.now().isoformat()
        self.logger.warning(
            f"[{timestamp}] PARTIAL_DATA: {source_name} | REASON: {reason}"
        )

    def log_critical_failure(self, message: str):
        """Log a critical failure that halts processing."""
        timestamp = datetime.now().isoformat()
        self.logger.error(f"[{timestamp}] CRITICAL_FAILURE: {message}")

    def _update_metrics(self, update_data: dict):
        """Update the metrics log file."""
        try:
            with open(self.metrics_log_file, 'r') as f:
                metrics = json.load(f)
            
            if "steps" not in metrics:
                metrics["steps"] = []
            
            metrics["steps"].append(update_data)
            metrics["last_updated"] = datetime.now().isoformat()
            
            with open(self.metrics_log_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")

    def get_citation_summary(self) -> dict:
        """Get a summary of all data source citations."""
        return self.citation_tracker.get_summary()


class CitationTracker:
    """Tracks data source citations and fetch status."""

    def __init__(self, log_file: Path):
        self.log_file = log_file

    def add_citation(self, source_name: str, url: str, status: str,
                   records_fetched: int = 0, error: Optional[str] = None,
                   timestamp: Optional[str] = None):
        """Add a citation entry."""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            entry = {
                "source_name": source_name,
                "url": url,
                "status": status,
                "records_fetched": records_fetched,
                "error": error,
                "timestamp": timestamp or datetime.now().isoformat()
            }
            
            data["sources"].append(entry)
            data["timestamp"] = datetime.now().isoformat()
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            # Log error but don't fail the ingestion
            print(f"Warning: Failed to log citation: {e}", file=sys.stderr)

    def get_summary(self) -> dict:
        """Get a summary of all citations."""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            summary = {
                "total_sources": len(data["sources"]),
                "successful": sum(1 for s in data["sources"] if s["status"] == "SUCCESS"),
                "failed": sum(1 for s in data["sources"] if s["status"] == "FAILED"),
                "total_records": sum(s.get("records_fetched", 0) for s in data["sources"]),
                "sources": data["sources"]
            }
            return summary
        except Exception as e:
            return {"error": str(e)}


def setup_ingestion_logging(project_root: Optional[Path] = None) -> IngestionLogger:
    """Factory function to create and configure the ingestion logger."""
    return IngestionLogger(project_root)


def main():
    """Test the logger setup."""
    logger = setup_ingestion_logging()
    
    # Test logging
    logger.log_source_fetch(
        source_name="Test Source",
        url="https://example.com/data",
        status="SUCCESS",
        records_fetched=100
    )
    
    logger.log_aggregation_step(
        step_name="test_step",
        details={"records": 100, "status": "ok"}
    )
    
    logger.log_validation_result(
        total_records=100,
        filtered_records=95,
        reason_codes=["temp_outlier"]
    )
    
    print("Ingestion logger test completed successfully.")
    print(f"Citation summary: {logger.get_citation_summary()}")


if __name__ == "__main__":
    main()
