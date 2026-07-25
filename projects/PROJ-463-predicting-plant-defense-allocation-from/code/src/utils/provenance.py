"""
Provenance tracking for the plant defense allocation pipeline.
Records metadata about pipeline runs, data transformations, and artifacts
to ensure reproducibility and auditability.
"""
import json
import hashlib
import datetime
import platform
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

from .config import get_config
from .logger import get_logger


class ArtifactType(Enum):
    """Enumeration of artifact types for provenance tracking."""
    RAW_DATA = "raw_data"
    PROCESSED_DATA = "processed_data"
    MODEL = "model"
    CONFIGURATION = "configuration"
    LOG = "log"
    REPORT = "report"
    METADATA = "metadata"
    OTHER = "other"


@dataclass
class ProvenanceRecord:
    """
    Represents a single provenance record for an artifact or operation.
    """
    record_id: str
    timestamp: str
    operation: str
    artifact_type: str
    artifact_path: str
    input_artifacts: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None
    status: str = "completed"
    error_message: Optional[str] = None
    git_commit: Optional[str] = None
    python_version: str = field(default_factory=lambda: sys.version)
    platform_info: str = field(default_factory=lambda: platform.platform())
    hostname: str = field(default_factory=lambda: platform.node())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for JSON serialization."""
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "operation": self.operation,
            "artifact_type": self.artifact_type,
            "artifact_path": self.artifact_path,
            "input_artifacts": self.input_artifacts,
            "parameters": self.parameters,
            "checksum": self.checksum,
            "status": self.status,
            "error_message": self.error_message,
            "git_commit": self.git_commit,
            "python_version": self.python_version,
            "platform_info": self.platform_info,
            "hostname": self.hostname
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvenanceRecord':
        """Create a ProvenanceRecord from a dictionary."""
        return cls(**data)


@dataclass
class PipelineRun:
    """
    Represents a complete pipeline run with all associated provenance records.
    """
    run_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    records: List[ProvenanceRecord] = field(default_factory=list)
    error_traceback: Optional[str] = None

    def add_record(self, record: ProvenanceRecord):
        """Add a provenance record to this run."""
        self.records.append(record)

    def complete(self, status: str = "completed", error_traceback: Optional[str] = None):
        """Mark the pipeline run as complete."""
        self.end_time = datetime.datetime.now().isoformat()
        self.status = status
        if error_traceback:
            self.error_traceback = error_traceback

    def to_dict(self) -> Dict[str, Any]:
        """Convert the run to a dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "config_snapshot": self.config_snapshot,
            "records": [r.to_dict() for r in self.records],
            "error_traceback": self.error_traceback
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineRun':
        """Create a PipelineRun from a dictionary."""
        records = [ProvenanceRecord.from_dict(r) for r in data.get("records", [])]
        return cls(
            run_id=data["run_id"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            status=data.get("status", "running"),
            config_snapshot=data.get("config_snapshot", {}),
            records=records,
            error_traceback=data.get("error_traceback")
        )


class ProvenanceTracker:
    """
    Centralized provenance tracker for the pipeline.
    Manages pipeline runs and persists provenance records to disk.
    """
    _instance: Optional['ProvenanceTracker'] = None
    _current_run: Optional[PipelineRun] = None
    _provenance_dir: Optional[Path] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, provenance_dir: Optional[Path] = None):
        if self._provenance_dir is not None:
            return

        self._provenance_dir = provenance_dir or get_config().provenance_dir
        self._provenance_dir.mkdir(parents=True, exist_ok=True)
        
        self._logger = get_logger("provenance")
        self._logger.info(f"Provenance tracker initialized. Directory: {self._provenance_dir}")

    def start_run(self, config_snapshot: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new pipeline run.
        
        Args:
            config_snapshot: Optional snapshot of the current configuration
        
        Returns:
            The run_id of the new run
        """
        run_id = f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.sha256(str(datetime.datetime.now()).encode()).hexdigest()[:8]}"
        
        self._current_run = PipelineRun(
            run_id=run_id,
            start_time=datetime.datetime.now().isoformat(),
            config_snapshot=config_snapshot or {}
        )
        
        self._logger.info(f"Started new pipeline run: {run_id}")
        return run_id

    def record_artifact(
        self,
        operation: str,
        artifact_path: str,
        artifact_type: Union[str, ArtifactType],
        input_artifacts: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        checksum: Optional[str] = None,
        status: str = "completed",
        error_message: Optional[str] = None
    ):
        """
        Record the creation or processing of an artifact.
        
        Args:
            operation: Description of the operation performed
            artifact_path: Path to the artifact
            artifact_type: Type of the artifact
            input_artifacts: List of input artifact paths
            parameters: Parameters used in the operation
            checksum: SHA256 checksum of the artifact
            status: Status of the operation (completed, failed, skipped)
            error_message: Error message if status is failed
        """
        if self._current_run is None:
            self._logger.warning("No active pipeline run. Creating a temporary run for this record.")
            self.start_run()

        if isinstance(artifact_type, ArtifactType):
            artifact_type = artifact_type.value

        # Generate a unique record ID
        record_id = hashlib.sha256(
            f"{self._current_run.run_id}_{operation}_{artifact_path}".encode()
        ).hexdigest()[:16]

        record = ProvenanceRecord(
            record_id=record_id,
            timestamp=datetime.datetime.now().isoformat(),
            operation=operation,
            artifact_type=artifact_type,
            artifact_path=artifact_path,
            input_artifacts=input_artifacts or [],
            parameters=parameters or {},
            checksum=checksum,
            status=status,
            error_message=error_message,
            git_commit=self._get_git_commit()
        )

        self._current_run.add_record(record)
        self._logger.debug(f"Recorded provenance: {record_id} - {operation}")

    def complete_run(self, status: str = "completed", error_traceback: Optional[str] = None):
        """
        Mark the current pipeline run as complete.
        
        Args:
            status: Final status of the run
            error_traceback: Optional traceback if the run failed
        """
        if self._current_run is None:
            self._logger.warning("No active pipeline run to complete.")
            return

        self._current_run.complete(status, error_traceback)
        
        # Persist the run to disk
        self._persist_run()
        
        self._logger.info(f"Pipeline run completed: {self._current_run.run_id} ({status})")
        self._current_run = None

    def _persist_run(self):
        """Persist the current run to disk as a JSON file."""
        if self._current_run is None:
            return

        run_file = self._provenance_dir / f"{self._current_run.run_id}.json"
        with open(run_file, 'w') as f:
            json.dump(self._current_run.to_dict(), f, indent=2)
        
        self._logger.info(f"Persisted provenance run to: {run_file}")

    def _get_git_commit(self) -> Optional[str]:
        """Attempt to get the current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def get_current_run(self) -> Optional[PipelineRun]:
        """Get the current active pipeline run."""
        return self._current_run

    def load_run(self, run_id: str) -> Optional[PipelineRun]:
        """Load a specific run from disk."""
        run_file = self._provenance_dir / f"{run_id}.json"
        if not run_file.exists():
            self._logger.warning(f"Run file not found: {run_file}")
            return None

        with open(run_file, 'r') as f:
            data = json.load(f)
        
        return PipelineRun.from_dict(data)

    def list_runs(self) -> List[str]:
        """List all run IDs in the provenance directory."""
        runs = []
        for file in self._provenance_dir.glob("run_*.json"):
            runs.append(file.stem)
        return sorted(runs)

    def get_run_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a specific run."""
        run = self.load_run(run_id)
        if run is None:
            return None

        return {
            "run_id": run.run_id,
            "start_time": run.start_time,
            "end_time": run.end_time,
            "status": run.status,
            "record_count": len(run.records),
            "artifacts": [
                {
                    "path": r.artifact_path,
                    "type": r.artifact_type,
                    "status": r.status
                }
                for r in run.records
            ]
        }


# Global instance management
_tracker_instance: Optional[ProvenanceTracker] = None

def get_provenance_tracker() -> ProvenanceTracker:
    """Get or create the global provenance tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ProvenanceTracker()
    return _tracker_instance

def record_provenance(
    operation: str,
    artifact_path: str,
    artifact_type: Union[str, ArtifactType] = ArtifactType.PROCESSED_DATA,
    input_artifacts: Optional[List[str]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    checksum: Optional[str] = None,
    status: str = "completed",
    error_message: Optional[str] = None
):
    """
    Convenience function to record a provenance record without manually managing the tracker.
    
    Args:
        operation: Description of the operation
        artifact_path: Path to the artifact
        artifact_type: Type of the artifact
        input_artifacts: List of input artifact paths
        parameters: Parameters used
        checksum: SHA256 checksum
        status: Status of the operation
        error_message: Error message if failed
    """
    tracker = get_provenance_tracker()
    tracker.record_artifact(
        operation=operation,
        artifact_path=artifact_path,
        artifact_type=artifact_type,
        input_artifacts=input_artifacts,
        parameters=parameters,
        checksum=checksum,
        status=status,
        error_message=error_message
    )

def start_pipeline_run(config_snapshot: Optional[Dict[str, Any]] = None) -> str:
    """Start a new pipeline run."""
    tracker = get_provenance_tracker()
    return tracker.start_run(config_snapshot)

def complete_pipeline_run(status: str = "completed", error_traceback: Optional[str] = None):
    """Complete the current pipeline run."""
    tracker = get_provenance_tracker()
    tracker.complete_run(status, error_traceback)