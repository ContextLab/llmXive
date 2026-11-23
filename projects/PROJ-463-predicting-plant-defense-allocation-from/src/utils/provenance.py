"""
Provenance tracking for the plant defense allocation pipeline.

This module provides functionality to track the origin, transformation, and
history of data artifacts throughout the pipeline execution.
"""

import json
import hashlib
import datetime
import platform
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field, asdict


class ArtifactType(Enum):
    """Enumeration of artifact types tracked in the pipeline."""
    RAW_DATA = "raw_data"
    PROCESSED_DATA = "processed_data"
    MODEL = "model"
    CONFIG = "config"
    LOG = "log"
    METADATA = "metadata"
    MANIFEST = "manifest"
    RESULTS = "results"
    OTHER = "other"


@dataclass
class ProvenanceRecord:
    """
    Represents a single provenance record for an artifact.
    
    Attributes:
        artifact_id: Unique identifier for the artifact.
        artifact_type: Type of the artifact.
        file_path: Path to the artifact file.
        checksum: SHA256 checksum of the artifact content.
        created_at: Timestamp when the artifact was created.
        created_by: Name of the module/function that created the artifact.
        parameters: Dictionary of parameters used to create the artifact.
        input_artifacts: List of artifact IDs that were inputs to this artifact.
        metadata: Additional metadata about the artifact.
    """
    artifact_id: str
    artifact_type: ArtifactType
    file_path: str
    checksum: str
    created_at: str
    created_by: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for JSON serialization."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "file_path": self.file_path,
            "checksum": self.checksum,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "parameters": self.parameters,
            "input_artifacts": self.input_artifacts,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvenanceRecord':
        """Create a ProvenanceRecord from a dictionary."""
        data["artifact_type"] = ArtifactType(data["artifact_type"])
        return cls(**data)

    def compute_checksum(self, file_path: Optional[Union[str, Path]] = None) -> str:
        """
        Compute SHA256 checksum of the artifact file.
        
        Args:
            file_path: Optional path override. Uses self.file_path if not provided.
        
        Returns:
            SHA256 checksum as a hexadecimal string.
        """
        path = Path(file_path) if file_path else Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"Cannot compute checksum: file not found - {path}")
        
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def update_checksum(self):
        """Update the checksum field based on the current file content."""
        self.checksum = self.compute_checksum()

@dataclass
class PipelineRun:
    """
    Represents a single execution of the pipeline.
    
    Attributes:
        run_id: Unique identifier for the pipeline run.
        start_time: When the pipeline run started.
        end_time: When the pipeline run ended (None if still running).
        status: Current status of the run (running, completed, failed).
        user: User who initiated the run.
        host: Hostname where the run was executed.
        python_version: Python version used.
        platform: Platform information.
        artifacts: List of provenance records for artifacts created in this run.
        parameters: Global parameters for the run.
    """
    run_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"
    user: str = ""
    host: str = ""
    python_version: str = ""
    platform: str = ""
    artifacts: List[ProvenanceRecord] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize system information if not provided."""
        if not self.user:
            try:
                import getpass
                self.user = getpass.getuser()
            except Exception:
                self.user = "unknown"
        
        if not self.host:
            self.host = platform.node()
        
        if not self.python_version:
            self.python_version = platform.python_version()
        
        if not self.platform:
            self.platform = f"{platform.system()} {platform.release()}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the run to a dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "user": self.user,
            "host": self.host,
            "python_version": self.python_version,
            "platform": self.platform,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineRun':
        """Create a PipelineRun from a dictionary."""
        data["artifacts"] = [ProvenanceRecord.from_dict(a) for a in data.get("artifacts", [])]
        return cls(**data)

    def complete(self, status: str = "completed"):
        """Mark the pipeline run as complete."""
        self.end_time = datetime.datetime.now().isoformat()
        self.status = status

    def add_artifact(self, artifact: ProvenanceRecord):
        """Add an artifact to the run."""
        self.artifacts.append(artifact)

    def get_artifact(self, artifact_id: str) -> Optional[ProvenanceRecord]:
        """Get an artifact by ID."""
        for artifact in self.artifacts:
            if artifact.artifact_id == artifact_id:
                return artifact
        return None

class ProvenanceTracker:
    """
    Tracks provenance for the entire pipeline execution.
    
    This class manages pipeline runs and their associated artifacts,
    providing methods to record, retrieve, and export provenance data.
    """
    
    _instance: Optional['ProvenanceTracker'] = None
    _current_run: Optional[PipelineRun] = None
    _provenance_dir: Path = Path("data/manifests/provenance")

    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern for the tracker instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, provenance_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the ProvenanceTracker.
        
        Args:
            provenance_dir: Directory to store provenance records.
        """
        if provenance_dir:
            self._provenance_dir = Path(provenance_dir)
        self._provenance_dir.mkdir(parents=True, exist_ok=True)

    def start_run(self, parameters: Optional[Dict[str, Any]] = None) -> PipelineRun:
        """
        Start a new pipeline run.
        
        Args:
            parameters: Global parameters for the run.
        
        Returns:
            The new PipelineRun instance.
        """
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + os.urandom(4).hex()
        self._current_run = PipelineRun(
            run_id=run_id,
            start_time=datetime.datetime.now().isoformat(),
            parameters=parameters or {}
        )
        return self._current_run

    def get_current_run(self) -> Optional[PipelineRun]:
        """Get the current active pipeline run."""
        return self._current_run

    def record_artifact(
        self,
        artifact_id: str,
        artifact_type: ArtifactType,
        file_path: Union[str, Path],
        created_by: str,
        parameters: Optional[Dict[str, Any]] = None,
        input_artifacts: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProvenanceRecord:
        """
        Record a new artifact in the current run.
        
        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of the artifact.
            file_path: Path to the artifact file.
            created_by: Name of the module/function that created it.
            parameters: Parameters used to create the artifact.
            input_artifacts: List of input artifact IDs.
            metadata: Additional metadata.
        
        Returns:
            The created ProvenanceRecord.
        """
        if self._current_run is None:
            raise RuntimeError("No active pipeline run. Call start_run() first.")
        
        file_path = str(file_path)
        record = ProvenanceRecord(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            file_path=file_path,
            checksum="",  # Will be computed
            created_at=datetime.datetime.now().isoformat(),
            created_by=created_by,
            parameters=parameters or {},
            input_artifacts=input_artifacts or [],
            metadata=metadata or {}
        )
        
        # Compute checksum if file exists
        if Path(file_path).exists():
            record.update_checksum()
        
        self._current_run.add_artifact(record)
        return record

    def complete_run(self, status: str = "completed"):
        """
        Complete the current pipeline run and save its record.
        
        Args:
            status: Final status of the run.
        """
        if self._current_run is None:
            raise RuntimeError("No active pipeline run to complete.")
        
        self._current_run.complete(status)
        
        # Save the run record to a JSON file
        run_file = self._provenance_dir / f"run_{self._current_run.run_id}.json"
        with open(run_file, 'w') as f:
            json.dump(self._current_run.to_dict(), f, indent=2)
        
        return self._current_run.run_id

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """
        Retrieve a saved pipeline run by ID.
        
        Args:
            run_id: The run ID to look up.
        
        Returns:
            The PipelineRun if found, None otherwise.
        """
        run_file = self._provenance_dir / f"run_{run_id}.json"
        if not run_file.exists():
            return None
        
        with open(run_file, 'r') as f:
            data = json.load(f)
        return PipelineRun.from_dict(data)

    def list_runs(self) -> List[str]:
        """List all run IDs."""
        runs = []
        for file in self._provenance_dir.glob("run_*.json"):
            run_id = file.stem.replace("run_", "")
            runs.append(run_id)
        return runs

    def export_provenance(self, output_path: Union[str, Path]) -> None:
        """
        Export all provenance data to a JSON file.
        
        Args:
            output_path: Path to the output file.
        """
        output_path = Path(output_path)
        all_runs = {}
        for run_id in self.list_runs():
            run = self.get_run(run_id)
            if run:
                all_runs[run_id] = run.to_dict()
        
        with open(output_path, 'w') as f:
            json.dump({"runs": all_runs}, f, indent=2)

# Global tracker instance
_tracker: Optional[ProvenanceTracker] = None

def get_provenance_tracker(provenance_dir: Optional[str] = None) -> ProvenanceTracker:
    """
    Get or create the global provenance tracker instance.
    
    Args:
        provenance_dir: Optional directory for provenance files.
    
    Returns:
        ProvenanceTracker instance.
    """
    global _tracker
    if _tracker is None:
        _tracker = ProvenanceTracker(provenance_dir=provenance_dir)
    return _tracker

def record_provenance(
    artifact_id: str,
    artifact_type: ArtifactType,
    file_path: Union[str, Path],
    created_by: str,
    parameters: Optional[Dict[str, Any]] = None,
    input_artifacts: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ProvenanceRecord:
    """
    Convenience function to record an artifact in the current run.
    
    Args:
        artifact_id: Unique identifier for the artifact.
        artifact_type: Type of the artifact.
        file_path: Path to the artifact file.
        created_by: Name of the module/function that created it.
        parameters: Parameters used to create the artifact.
        input_artifacts: List of input artifact IDs.
        metadata: Additional metadata.
    
    Returns:
        The created ProvenanceRecord.
    """
    tracker = get_provenance_tracker()
    return tracker.record_artifact(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        file_path=file_path,
        created_by=created_by,
        parameters=parameters,
        input_artifacts=input_artifacts,
        metadata=metadata
    )

def start_pipeline_run(parameters: Optional[Dict[str, Any]] = None) -> PipelineRun:
    """
    Convenience function to start a new pipeline run.
    
    Args:
        parameters: Global parameters for the run.
    
    Returns:
        The new PipelineRun instance.
    """
    tracker = get_provenance_tracker()
    return tracker.start_run(parameters=parameters)

def complete_pipeline_run(status: str = "completed") -> str:
    """
    Convenience function to complete the current pipeline run.
    
    Args:
        status: Final status of the run.
    
    Returns:
        The run ID.
    """
    tracker = get_provenance_tracker()
    return tracker.complete_run(status=status)
