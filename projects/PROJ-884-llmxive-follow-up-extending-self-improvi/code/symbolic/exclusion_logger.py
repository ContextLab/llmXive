"""
Exclusion Logger for recording invalid puzzle instances.

This module provides functionality to log exclusion events when puzzles
fail to parse or contain contradictions, ensuring traceability and
auditability of the data filtering process.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class ExclusionEvent:
    """Represents a single exclusion event."""
    puzzle_id: str
    reason: str
    error_code: str
    error_message: str
    source_file: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class ExclusionLogger:
    """
    Logger for recording puzzle exclusion events.
    
    This logger writes exclusion events to a JSON file, maintaining
    a history of all filtered-out instances for audit purposes.
    """

    def __init__(self, output_path: Optional[Path] = None):
        """
        Initialize the exclusion logger.
        
        Args:
            output_path: Path to the exclusion log file. Defaults to 'data/processed/exclusions.json'.
        """
        self.output_path = output_path or Path("data/processed/exclusions.json")
        self.events: List[ExclusionEvent] = []
        
        # Ensure the output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing events if the file exists
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            self.events.append(ExclusionEvent(**item))
            except (json.JSONDecodeError, TypeError):
                self.events = []

    def log_exclusion(self, event: ExclusionEvent):
        """
        Log a new exclusion event.
        
        Args:
            event: The ExclusionEvent to log.
        """
        self.events.append(event)
        self._flush_to_disk()

    def _flush_to_disk(self):
        """Write all events to the output file."""
        with open(self.output_path, 'w') as f:
            json.dump([asdict(e) for e in self.events], f, indent=2)

    def get_events(self) -> List[ExclusionEvent]:
        """Return all logged exclusion events."""
        return self.events

    def get_count(self) -> int:
        """Return the number of logged exclusion events."""
        return len(self.events)

    def clear(self):
        """Clear all logged events and reset the file."""
        self.events = []
        self._flush_to_disk()

def main():
    """Main entry point for testing the exclusion logger."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Exclusion Logger")
    parser.add_argument("--output", type=str, default="data/processed/exclusions.json", help="Output path")
    parser.add_argument("--test", action="store_true", help="Run a simple test")
    
    args = parser.parse_args()
    
    if args.test:
        logger = ExclusionLogger(output_path=Path(args.output))
        
        # Create a test event
        event = ExclusionEvent(
            puzzle_id="test_puzzle_001",
            reason="PARSE_FAILURE",
            error_code="PARSE_FAILURE",
            error_message="Failed to parse constraint syntax",
            source_file="test_data.json",
            timestamp=datetime.now().isoformat()
        )
        
        logger.log_exclusion(event)
        print(f"Logged exclusion event. Total events: {logger.get_count()}")
        print(f"Output written to: {args.output}")

if __name__ == "__main__":
    main()
