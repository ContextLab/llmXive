"""
Exclusion Logger Module for BES Pipeline.

Logs exclusion events when the symbolic parser or planner encounters
constraints or goals that cannot be processed.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# Ensure imports work when running as script or module
try:
    from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, VERIFIER_ERROR
except ImportError:
    from exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, VERIFIER_ERROR

@dataclass
class ExclusionEvent:
    """Represents a single exclusion event."""
    puzzle_id: str
    reason_code: str
    details: str
    timestamp: str
    source_module: str

class ExclusionLogger:
    """
    Logger for exclusion events in the symbolic pipeline.

    Writes exclusion events to a JSON file, adhering to the schema
    defined in contracts/output.schema.yaml.
    """

    VALID_REASON_CODES = {
        "PARSE_FAILURE",
        "CONTRADICTION_DETECTED",
        "IMPOSSIBLE_GOAL",
        "NON_LINEAR_CONSTRAINT",
        "IMPOSSIBLE_SUBGOAL",
        "TOO_COMPLEX"
    }

    def __init__(self, log_path: Path):
        """
        Initialize the exclusion logger.

        Args:
            log_path: Path to the JSON file where exclusions will be logged.
        """
        self.log_path = Path(log_path)
        self._events: List[ExclusionEvent] = []
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Ensure the log file exists and is initialized as a JSON list."""
        if not self.log_path.exists():
            # Create parent directories if needed
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, 'w') as f:
                json.dump([], f)
        else:
            # Load existing events
            try:
                with open(self.log_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Convert dict to ExclusionEvent for internal use if needed
                        # For now, we just keep the list structure
                        pass
                    else:
                        # Reset if file is corrupted
                        with open(self.log_path, 'w') as f:
                            json.dump([], f)
            except json.JSONDecodeError:
                with open(self.log_path, 'w') as f:
                    json.dump([], f)

    def _load_events(self) -> List[Dict[str, Any]]:
        """Load existing events from the log file."""
        if not self.log_path.exists():
            return []
        try:
            with open(self.log_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_events(self, events: List[Dict[str, Any]]):
        """Save events to the log file."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'w') as f:
            json.dump(events, f, indent=2)

    def log_exclusion(self, puzzle_id: str, reason_code: str, details: str = "", source_module: str = "parser"):
        """
        Log an exclusion event.

        Args:
            puzzle_id: The ID of the puzzle that was excluded.
            reason_code: The reason for exclusion (must be in VALID_REASON_CODES).
        details: Additional details about the exclusion.
        source_module: The module that triggered the exclusion.

        Raises:
            ValueError: If reason_code is not valid.
        """
        if reason_code not in self.VALID_REASON_CODES:
            raise ValueError(f"Invalid reason_code: {reason_code}. Must be one of {self.VALID_REASON_CODES}")

        event = ExclusionEvent(
            puzzle_id=puzzle_id,
            reason_code=reason_code,
            details=details,
            timestamp=datetime.utcnow().isoformat(),
            source_module=source_module
        )

        # Load existing events, append new one, and save
        events = self._load_events()
        events.append(asdict(event))
        self._save_events(events)

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Retrieve all logged exclusion events."""
        return self._load_events()

    def get_events_by_reason(self, reason_code: str) -> List[Dict[str, Any]]:
        """Retrieve events filtered by reason code."""
        all_events = self._load_events()
        return [e for e in all_events if e.get("reason_code") == reason_code]

    def get_events_by_puzzle(self, puzzle_id: str) -> List[Dict[str, Any]]:
        """Retrieve events filtered by puzzle ID."""
        all_events = self._load_events()
        return [e for e in all_events if e.get("puzzle_id") == puzzle_id]


def main():
    """Main entry point for testing the exclusion logger."""
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="Test Exclusion Logger")
    parser.add_argument("--output", type=str, required=True, help="Path to output log file")

    args = parser.parse_args()
    log_path = Path(args.output)

    logger = ExclusionLogger(log_path)

    # Test logging
    logger.log_exclusion("puzzle_001", "NON_LINEAR_CONSTRAINT", "Constraint too deep")
    logger.log_exclusion("puzzle_002", "PARSE_FAILURE", "Syntax error in constraint")
    logger.log_exclusion("puzzle_003", "IMPOSSIBLE_GOAL", "Goal state unreachable")

    events = logger.get_all_events()
    print(f"Logged {len(events)} events:")
    for event in events:
        print(f"  - {event['puzzle_id']}: {event['reason_code']} - {event['details']}")

    print(f"Events saved to {log_path}")


if __name__ == "__main__":
    main()