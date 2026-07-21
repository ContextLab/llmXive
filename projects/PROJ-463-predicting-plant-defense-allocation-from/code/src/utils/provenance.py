import json
import hashlib
import datetime
import platform
import sys
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .config import get_config, get_data_path
from .logger import get_logger, setup_logging

@dataclass
class ProvenanceRecord:
    """
    Represents a single provenance record for a data transformation or analysis step.
    """
    timestamp: str
    step_name: str
    input_files: List[str]
    output_files: List[str]
    parameters: Dict[str, Any]
    code_hash: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "step_name": self.step_name,
            "input_files": self.input_files,
            "output_files": self.output_files,
            "parameters": self.parameters,
            "code_hash": self.code_hash,
            "environment": self.environment,
            "success": self.success,
            "error_message": self.error_message
        }

    def compute_hash(self) -> str:
        """Computes a SHA256 hash of the record for integrity checking."""
        record_str = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(record_str.encode('utf-8')).hexdigest()

@dataclass
class PipelineRun:
    """
    Aggregates provenance records for a single execution of the pipeline.
    """
    run_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"  # running, completed, failed
    records: List[ProvenanceRecord] = field(default_factory=list)
    system_info: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.system_info:
            self.system_info = {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "hostname": platform.node(),
                "cwd": os.getcwd()
            }

    def add_record(self, record: ProvenanceRecord):
        self.records.append(record)

    def finish(self, status: str = "completed"):
        self.end_time = datetime.datetime.now().isoformat()
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "system_info": self.system_info,
            "records": [r.to_dict() for r in self.records]
        }

    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

class ProvenanceTracker:
    """
    Singleton-like tracker for managing pipeline provenance across modules.
    """
    _instance: Optional['ProvenanceTracker'] = None
    _current_run: Optional[PipelineRun] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.logger = get_logger("provenance")
        self._initialized = True

    def start_run(self, run_id: Optional[str] = None) -> PipelineRun:
        """Starts a new pipeline run."""
        if run_id is None:
            run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self._current_run = PipelineRun(run_id=run_id, start_time=datetime.datetime.now().isoformat())
        self.logger.info(f"Starting pipeline run: {run_id}")
        return self._current_run

    def get_current_run(self) -> Optional[PipelineRun]:
        return self._current_run

    def record_step(self, step_name: str, inputs: List[str], outputs: List[str], 
                    params: Dict[str, Any], success: bool = True, error: Optional[str] = None):
        """Records a single step's provenance."""
        if not self._current_run:
            raise RuntimeError("No active pipeline run. Call start_run() first.")
        
        record = ProvenanceRecord(
            timestamp=datetime.datetime.now().isoformat(),
            step_name=step_name,
            input_files=inputs,
            output_files=outputs,
            parameters=params,
            success=success,
            error_message=error
        )
        
        self._current_run.add_record(record)
        self.logger.log_provenance_event(step_name, {
            "inputs": inputs,
            "outputs": outputs,
            "success": success
        })

    def finish_run(self, status: str = "completed"):
        """Finalizes the current run and saves the manifest."""
        if not self._current_run:
            self.logger.warning("No active run to finish.")
            return

        self._current_run.finish(status)
        
        try:
            data_path = get_data_path()
            manifest_dir = Path(data_path) / "manifests"
            manifest_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = manifest_dir / f"provenance_{self._current_run.run_id}.json"
            self._current_run.save(str(filepath))
            self.logger.info(f"Provenance manifest saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save provenance manifest: {e}")
            raise

    def reset(self):
        """Resets the tracker state."""
        self._current_run = None

# Global tracker instance
_tracker: Optional[ProvenanceTracker] = None

def get_provenance_tracker() -> ProvenanceTracker:
    """Returns the global provenance tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ProvenanceTracker()
    return _tracker

def record_provenance(step_name: str, inputs: List[str], outputs: List[str], 
                      params: Dict[str, Any], success: bool = True, error: Optional[str] = None):
    """
    Convenience function to record a step without manually managing the tracker.
    """
    tracker = get_provenance_tracker()
    tracker.record_step(step_name, inputs, outputs, params, success, error)
