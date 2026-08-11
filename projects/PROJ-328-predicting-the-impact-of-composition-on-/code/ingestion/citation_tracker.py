import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import csv

class CitationTracker:
    """
    Tracks data source citations and fetch status for reproducibility and 
    audit purposes. This is a lightweight version that can be used independently
    of the full IngestionLogger.
    """

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Ensure the citation log file exists and is initialized."""
        if not self.log_file.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, 'w') as f:
                json.dump({"sources": [], "timestamp": datetime.now().isoformat()}, f, indent=2)

    def add_citation(self, source_name: str, url: str, status: str,
                   records_fetched: int = 0, error: Optional[str] = None,
                   timestamp: Optional[str] = None):
        """
        Add a citation entry to the log.

        Args:
            source_name: Name of the data source (e.g., 'NIST', 'Materials Project')
            url: URL or identifier for the source
            status: 'SUCCESS', 'FAILED', or 'PARTIAL'
            records_fetched: Number of records successfully retrieved
            error: Error message if status is FAILED or PARTIAL
            timestamp: ISO format timestamp (defaults to now)
        """
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
            logging.error(f"Failed to add citation: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all citations.

        Returns:
            Dictionary with summary statistics and list of all sources
        """
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            summary = {
                "total_sources": len(data["sources"]),
                "successful": sum(1 for s in data["sources"] if s["status"] == "SUCCESS"),
                "failed": sum(1 for s in data["sources"] if s["status"] == "FAILED"),
                "partial": sum(1 for s in data["sources"] if s["status"] == "PARTIAL"),
                "total_records": sum(s.get("records_fetched", 0) for s in data["sources"]),
                "sources": data["sources"]
            }
            return summary
        except Exception as e:
            return {"error": str(e)}

    def export_to_csv(self, output_path: Optional[Path] = None) -> Path:
        """
        Export citation log to CSV format.

        Args:
            output_path: Path for the CSV file (defaults to log_file with .csv extension)

        Returns:
            Path to the exported CSV file
        """
        if output_path is None:
            output_path = self.log_file.with_suffix('.csv')
        
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "source_name", "url", "status", "records_fetched", "error", "timestamp"
                ])
                writer.writeheader()
                writer.writerows(data["sources"])
            
            return output_path
        except Exception as e:
            logging.error(f"Failed to export citations to CSV: {e}")
            raise


# Global tracker instance (singleton pattern)
_global_tracker: Optional[CitationTracker] = None


def get_tracker(log_file: Optional[Path] = None) -> CitationTracker:
    """
    Get or create the global citation tracker instance.

    Args:
        log_file: Path to the citation log file

    Returns:
        CitationTracker instance
    """
    global _global_tracker
    if _global_tracker is None:
        if log_file is None:
            from pathlib import Path
            log_file = Path("data/processed/source_citations.json")
        _global_tracker = CitationTracker(log_file)
    return _global_tracker


def reset_tracker():
    """Reset the global tracker (useful for testing)."""
    global _global_tracker
    _global_tracker = None


def main():
    """Test the citation tracker."""
    from pathlib import Path
    
    # Use a test file
    test_file = Path("data/processed/test_citations.json")
    tracker = CitationTracker(test_file)
    
    # Add test citations
    tracker.add_citation(
        source_name="Test Source 1",
        url="https://example.com/data1",
        status="SUCCESS",
        records_fetched=100
    )
    
    tracker.add_citation(
        source_name="Test Source 2",
        url="https://example.com/data2",
        status="FAILED",
        error="Connection timeout",
        records_fetched=0
    )
    
    tracker.add_citation(
        source_name="Test Source 3",
        url="https://example.com/data3",
        status="PARTIAL",
        error="Some records missing",
        records_fetched=50
    )
    
    # Get summary
    summary = tracker.get_summary()
    print("Citation Summary:")
    print(json.dumps(summary, indent=2))
    
    # Export to CSV
    csv_path = tracker.export_to_csv()
    print(f"\nCitations exported to: {csv_path}")
    
    # Cleanup
    test_file.unlink(missing_ok=True)
    csv_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()