"""
State Store for buffer cycles.
Stores historical confidence, prompt lengths, and cycle IDs.
Required for T021 (CAP Classifier).
"""
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from utils.logging import get_logger
from utils.seeds import get_seed

logger = get_logger(__name__)

@dataclass
class CycleRecord:
    """Record for a single cycle's interaction."""
    cycle_id: int
    question_id: str
    prompt_length: int
    confidence: float
    is_correct: int
    candidates_used: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class StateStore:
    """
    In-memory buffer state schema and storage class.
    Manages history of cycles for CAP analysis.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.records: List[CycleRecord] = []
        self.logger = get_logger(self.__class__.__name__)

    def add_record(self, record: CycleRecord):
        """Adds a cycle record to the store."""
        self.records.append(record)
        self.logger.debug(f"Added record for cycle {record.cycle_id}, question {record.question_id}")

    def get_history(self, question_id: Optional[str] = None, limit: Optional[int] = None) -> List[CycleRecord]:
        """Retrieves history, optionally filtered by question_id."""
        if question_id:
            filtered = [r for r in self.records if r.question_id == question_id]
        else:
            filtered = self.records
        
        if limit:
            return filtered[-limit:]
        return filtered

    def get_confidence_history(self, question_id: str) -> List[float]:
        """Returns list of confidence scores for a specific question."""
        history = self.get_history(question_id=question_id)
        return [r.confidence for r in history]

    def get_prompt_lengths(self, question_id: str) -> List[int]:
        """Returns list of prompt lengths for a specific question."""
        history = self.get_history(question_id=question_id)
        return [r.prompt_length for r in history]

    def export_to_json(self, filepath: str):
        """Exports all records to a JSON file."""
        data = [asdict(r) for r in self.records]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        self.logger.info(f"State store exported to {filepath}")

    def clear(self):
        """Clears all records."""
        self.records = []
        self.logger.info("State store cleared.")
