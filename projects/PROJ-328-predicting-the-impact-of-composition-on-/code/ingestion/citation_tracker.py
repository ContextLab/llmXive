"""
Module to track data sources and citations for ingestion operations.
Ensures reproducibility and traceability of the dataset.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import csv

from utils.logging_config import get_logger
from config import get_data_processed_dir, get_data_raw_dir

logger = get_logger("ingestion.citation_tracker")

class CitationTracker:
    """
    Tracks the provenance of data sources used during ingestion.
    """
    
    def __init__(self):
        self.sources: List[Dict[str, Any]] = []
        self.operations: List[Dict[str, Any]] = []
        self.logger = get_logger("ingestion.citation_tracker")
    
    def register_source(self, source_name: str, url: Optional[str] = None, 
                      description: Optional[str] = None, 
                      access_date: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None):
        """
        Register a new data source.
        
        Args:
            source_name: Human-readable name of the source.
            url: Direct URL or identifier.
            description: Brief description of the dataset.
            access_date: Date the data was accessed (ISO format).
            metadata: Additional metadata (e.g., version, license).
        """
        if not access_date:
            access_date = datetime.now().isoformat()
        
        entry = {
            "name": source_name,
            "url": url,
            "description": description,
            "access_date": access_date,
            "metadata": metadata or {}
        }
        self.sources.append(entry)
        self.logger.info(f"Registered data source: {source_name} ({url or 'local'})")

    def log_operation(self, operation_type: str, details: Dict[str, Any]):
        """
        Log a specific ingestion operation.
        
        Args:
            operation_type: Type of operation (e.g., 'fetch', 'clean', 'filter').
            details: Dictionary of operation details.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": operation_type,
            "details": details
        }
        self.operations.append(entry)
        self.logger.debug(f"Operation logged: {operation_type} - {details}")

    def save_citations(self, output_dir: Optional[Path] = None):
        """
        Save the citation log and operation history to JSON and CSV files.
        
        Args:
            output_dir: Directory to save files. Defaults to data/processed.
        """
        if output_dir is None:
            output_dir = Path(get_data_processed_dir())
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON log
        json_path = output_dir / "data_sources_citations.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "sources": self.sources,
                "operations": self.operations,
                "generated_at": datetime.now().isoformat()
            }, f, indent=2)
        
        self.logger.info(f"Citation log saved to {json_path}")
        
        # Save CSV summary for quick reference
        csv_path = output_dir / "data_sources_summary.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["name", "url", "description", "access_date"])
            writer.writeheader()
            for source in self.sources:
                writer.writerow({
                    "name": source["name"],
                    "url": source["url"],
                    "description": source["description"],
                    "access_date": source["access_date"]
                })
        
        self.logger.info(f"Source summary saved to {csv_path}")

# Global instance for convenience
_global_tracker: Optional[CitationTracker] = None

def get_tracker() -> CitationTracker:
    """Get or create the global citation tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CitationTracker()
    return _global_tracker

def reset_tracker():
    """Reset the global tracker (useful for testing)."""
    global _global_tracker
    _global_tracker = None
