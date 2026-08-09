"""
Citation tracking module for the ingestion pipeline.
Provides functionality to register, track, and save data source citations.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import csv

from config import get_data_processed_dir
from utils.logging_config import get_logger

CITATION_LOG_FILE = "data/processed/citations.json"
CITATION_CSV_FILE = "data/processed/citations.csv"


class CitationTracker:
    """
    Tracks and manages data source citations for the ingestion pipeline.
    """
    
    def __init__(self):
        self.citations: dict = {}
        self.processed_dir = get_data_processed_dir()
        self.citation_file = self.processed_dir / CITATION_LOG_FILE
        self.citation_csv_file = self.processed_dir / CITATION_CSV_FILE
        self.logger = get_logger("ingestion")
    
    def add_citation(self, source_name: str, citation_info: dict):
        """
        Add a citation for a data source.
        
        Args:
            source_name: Unique identifier for the source
            citation_info: Dictionary with citation metadata (authors, year, title, url, etc.)
        """
        citation_info['_added_at'] = datetime.now().isoformat()
        citation_info['_source_name'] = source_name
        self.citations[source_name] = citation_info
        self.logger.debug(f"Citation added for source: {source_name}")
    
    def save_to_file(self):
        """Save all citations to both JSON and CSV files."""
        if not self.processed_dir.exists():
            self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        with open(self.citation_file, 'w', encoding='utf-8') as f:
            json.dump(self.citations, f, indent=2, default=str)
        
        # Save as CSV for easier inspection
        self._save_to_csv()
        
        self.logger.info(f"CITATIONS_SAVED | Total citations: {len(self.citations)} | File: {self.citation_file}")
    
    def _save_to_csv(self):
        """Save citations to a CSV file."""
        if not self.citations:
            return
        
        fieldnames = ['source_name', 'authors', 'year', 'title', 'url', 'type', '_added_at']
        
        with open(self.citation_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for source_name, info in self.citations.items():
                row = {'source_name': source_name}
                row.update(info)
                writer.writerow(row)
        
        self.logger.debug(f"Citations saved to CSV: {self.citation_csv_file}")
    
    def get_summary(self) -> dict:
        """
        Get a summary of all citations (excluding internal fields).
        
        Returns:
            Dictionary with source names and their public citation metadata
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
        Load citations from the JSON file if it exists.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.citation_file.exists():
            self.logger.debug("No existing citation file found")
            return False
        
        try:
            with open(self.citation_file, 'r', encoding='utf-8') as f:
                self.citations = json.load(f)
            self.logger.info(f"Citations loaded from file: {len(self.citations)} sources")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load citations: {e}")
            return False
    
    def get_citation_string(self, source_name: str) -> Optional[str]:
        """
        Get a formatted citation string for a specific source.
        
        Args:
            source_name: The source identifier
        
        Returns:
            Formatted citation string or None if not found
        """
        if source_name not in self.citations:
            return None
        
        info = self.citations[source_name]
        authors = info.get('authors', ['Unknown'])
        year = info.get('year', 'n.d.')
        title = info.get('title', 'Untitled')
        
        return f"{', '.join(authors)} ({year}). {title}."
    
    def get_all_citation_strings(self) -> List[str]:
        """
        Get formatted citation strings for all sources.
        
        Returns:
            List of formatted citation strings
        """
        return [
            self.get_citation_string(name) 
            for name in self.citations.keys()
            if self.get_citation_string(name)
        ]


# Global tracker instance
_tracker_instance: Optional[CitationTracker] = None


def get_tracker() -> CitationTracker:
    """Get the global citation tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = CitationTracker()
    return _tracker_instance


def reset_tracker():
    """Reset the global citation tracker instance."""
    global _tracker_instance
    _tracker_instance = CitationTracker()


def main():
    """
    Main entry point for testing the citation tracker.
    """
    tracker = get_tracker()
    
    # Add test citations
    tracker.add_citation(
        "Materials Project",
        {
            "authors": ["Jain, A.", "Ong, S.P.", "Hautier, G.", "Chen, W.", "Richie, V.D."],
            "year": 2013,
            "title": "Commentary: The Materials Project: A materials genome approach to accelerating materials innovation",
            "url": "https://doi.org/10.1063/1.4812323",
            "type": "journal"
        }
    )
    
    tracker.add_citation(
        "NIST",
        {
            "authors": ["National Institute of Standards and Technology"],
            "year": 2023,
            "title": "NIST Solder Alloy Database",
            "url": "https://www.nist.gov/",
            "type": "database"
        }
    )
    
    tracker.save_to_file()
    
    print("Citation Tracker Test")
    print("=" * 50)
    print("Summary:")
    for source, info in tracker.get_summary().items():
        print(f"  {source}: {info.get('title', 'N/A')}")
    
    print("\nFormatted Citations:")
    for citation in tracker.get_all_citation_strings():
        print(f"  {citation}")
    
    print("\nTest completed successfully.")


if __name__ == "__main__":
    main()
