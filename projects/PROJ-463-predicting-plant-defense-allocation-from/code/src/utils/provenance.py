import json
import hashlib
import datetime
import platform
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from src.utils.config import get_data_path, get_config

@dataclass
class ProvenanceRecord:
    """
    Represents a single record of data transformation or generation.
    """
    record_id: str
    timestamp: str
    action: str  # e.g., "download", "preprocess", "analysis"
    input_files: List[str]
    output_files: List[str]
    parameters: Dict[str, Any]
    tool_version: str
    code_hash: str
    user: str
    host: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @staticmethod
    def generate_id() -> str:
        return hashlib.sha256(
            datetime.datetime.now().isoformat().encode()
        ).hexdigest()[:16]

@dataclass
class PipelineRun:
    """
    Represents a full execution run of the pipeline.
    """
    run_id: str
    start_time: str
    end_time: Optional[str]
    status: str  # "running", "completed", "failed"
    config_snapshot: Dict[str, Any]
    provenance_records: List[ProvenanceRecord] = field(default_factory=list)
    error_message: Optional[str] = None

    def add_record(self, record: ProvenanceRecord) -> None:
        self.provenance_records.append(record)

    def finish(self, status: str, error: Optional[str] = None) -> None:
        self.end_time = datetime.datetime.now().isoformat()
        self.status = status
        self.error_message = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "config_snapshot": self.config_snapshot,
            "provenance_records": [r.to_dict() for r in self.provenance_records],
            "error_message": self.error_message
        }

    def save(self, filepath: Optional[Path] = None) -> None:
        if filepath is None:
            log_dir = get_data_path() / "processed" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            filepath = log_dir / f"run_{self.run_id}_provenance.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        
        return filepath

class ProvenanceTracker:
    """
    Singleton-like tracker for managing the current pipeline run state
    and recording provenance events.
    """
    _instance: Optional['ProvenanceTracker'] = None
    _current_run: Optional[PipelineRun] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start_run(self, config: Dict[str, Any]) -> PipelineRun:
        """Initialize a new pipeline run."""
        run_id = ProvenanceRecord.generate_id()
        self._current_run = PipelineRun(
            run_id=run_id,
            start_time=datetime.datetime.now().isoformat(),
            end_time=None,
            status="running",
            config_snapshot=config
        )
        return self._current_run

    def get_run(self) -> Optional[PipelineRun]:
        return self._current_run

    def record(self, action: str, input_files: List[str], output_files: List[str], 
               parameters: Dict[str, Any], tool_version: str = "unknown") -> ProvenanceRecord:
        """Record a specific action in the current run."""
        if not self._current_run:
            raise RuntimeError("No active pipeline run. Call start_run() first.")

        # Calculate code hash for the current module or a generic hash if not applicable
        # For simplicity in this utility, we hash the current timestamp + action
        code_hash = hashlib.sha256(
            f"{action}_{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        record = ProvenanceRecord(
            record_id=ProvenanceRecord.generate_id(),
            timestamp=datetime.datetime.now().isoformat(),
            action=action,
            input_files=input_files,
            output_files=output_files,
            parameters=parameters,
            tool_version=tool_version,
            code_hash=code_hash,
            user=os.getenv("USER", "unknown"),
            host=platform.node()
        )

        self._current_run.add_record(record)
        return record

    def finish_run(self, status: str, error: Optional[str] = None) -> None:
        """Mark the current run as finished."""
        if self._current_run:
            self._current_run.finish(status, error)
            self._current_run.save()
            self._current_run = None

# Global tracker instance
_tracker: Optional[ProvenanceTracker] = None

def get_provenance_tracker() -> ProvenanceTracker:
    """Get or create the global provenance tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ProvenanceTracker()
    return _tracker

def record_provenance(action: str, input_files: List[str], output_files: List[str], 
                     parameters: Dict[str, Any], tool_version: str = "unknown") -> ProvenanceRecord:
    """
    Convenience function to record a provenance event using the global tracker.
    """
    return get_provenance_tracker().record(action, input_files, output_files, parameters, tool_version)
