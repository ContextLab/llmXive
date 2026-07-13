"""
Citation Tracker: Tracks data sources and citations.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import csv

from seed import init_reproducibility
from utils.logging_config import get_logger

logger = get_logger(__name__)


class CitationTracker:
    """
    Tracks citations for data sources used in the pipeline.
    """

    def __init__(self):
        init_reproducibility()
        self.citations = []

    def add_citation(self, source: str, url: str, description: str):
        """
        Adds a citation for a data source.
        """
        citation = {
            "source": source,
            "url": url,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        self.citations.append(citation)
        logger.info(f"Added citation for {source}")

    def get_citations(self) -> List[Dict[str, Any]]:
        """
        Returns the list of citations.
        """
        return self.citations

    def save_citations(self, output_path: Path):
        """
        Saves citations to a JSON file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.citations, f, indent=2)
        logger.info(f"Saved citations to {output_path}")


# Singleton pattern for global tracking
_tracker_instance = None


def get_tracker() -> CitationTracker:
    """
    Returns the singleton CitationTracker instance.
    """
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = CitationTracker()
    return _tracker_instance


def reset_tracker():
    """
    Resets the singleton CitationTracker instance.
    """
    global _tracker_instance
    _tracker_instance = CitationTracker()

def main():
    """
    Entry point for the citation tracker.
    """
    logger.info("Citation Tracker module loaded.")

if __name__ == "__main__":
    main()
