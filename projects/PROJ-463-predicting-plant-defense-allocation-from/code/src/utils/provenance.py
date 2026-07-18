"""
Provenance tracking for data lineage and pipeline execution history.

Records metadata about data sources, transformations, and processing steps
to ensure reproducibility and auditability.
"""
import json
import hashlib
import datetime
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict, field
import logging

from .config import get_config
from .logger import get_logger


@dataclass
class ProvenanceRecord:
    """
    A single provenance record capturing metadata about a data artifact or operation.
    """
    artifact_id: str
    artifact_type: str  # e.g., 'raw_data', 'processed_data', 'model', 'manifest'
    source_type: str    # 'real', 'synthetic', 'derived'
    created_at: str
    created_by: str
    input_artifacts: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None
    file_path: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvenanceRecord':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PipelineRun:
    """
    Tracks a complete pipeline execution run.
    """
    run_id: str
    started_at: str
    ended_at: Optional[str] = None
    status: str = "running"  # running, completed, failed
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    artifacts_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class ProvenanceTracker:
    """
    Centralized provenance tracking system.
    
    Manages records of data lineage, transformations, and pipeline execution.
    """
    
    def __init__(self, manifest_dir: Optional[Path] = None):
        """
        Initialize the provenance tracker.
        
        Args:
            manifest_dir: Directory to store provenance manifests. Defaults to data/manifests.
        """
        self.logger = get_logger("provenance")
        config = get_config()
        
        if manifest_dir is None:
            from .config import get_data_path
            data_path = get_data_path()
            manifest_dir = data_path / "manifests"
        
        self.manifest_dir = Path(manifest_dir)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_run: Optional[PipelineRun] = None
        self.records: List[ProvenanceRecord] = []
        self._run_counter = 0
        
        self.logger.info("Provenance tracker initialized. Manifest dir: %s", self.manifest_dir)
    
    def start_run(self, run_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new pipeline run.
        
        Args:
            run_id: Optional custom run ID. If None, generates one.
            config: Optional configuration snapshot to record.
        
        Returns:
            The run ID.
        """
        if run_id is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self._run_counter += 1
            run_id = f"run_{timestamp}_{self._run_counter}"
        
        self.current_run = PipelineRun(
            run_id=run_id,
            started_at=datetime.datetime.now().isoformat(),
            config_snapshot=config or {}
        )
        
        self.logger.info("Started pipeline run: %s", run_id)
        return run_id
    
    def end_run(self, status: str = "completed", error: Optional[str] = None) -> None:
        """
        End the current pipeline run.
        
        Args:
            status: Final status ('completed' or 'failed').
            error: Optional error message if failed.
        """
        if self.current_run is None:
            self.logger.warning("No active run to end")
            return
        
        self.current_run.ended_at = datetime.datetime.now().isoformat()
        self.current_run.status = status
        
        if error:
            self.current_run.errors.append(error)
        
        self._save_run()
        self.logger.info("Ended pipeline run: %s with status: %s", self.current_run.run_id, status)
    
    def add_step(self, step_name: str, step_type: str, parameters: Dict[str, Any] = None) -> None:
        """
        Record a pipeline step execution.
        
        Args:
            step_name: Name of the step.
            step_type: Type of step (e.g., 'download', 'preprocess', 'analyze').
        """
        if self.current_run is None:
            self.logger.warning("No active run to add step to")
            return
        
        step_record = {
            "step_name": step_name,
            "step_type": step_type,
            "parameters": parameters or {},
            "executed_at": datetime.datetime.now().isoformat(),
            "status": "completed"
        }
        
        self.current_run.steps.append(step_record)
        self.logger.debug("Added step: %s", step_name)
    
    def record_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        source_type: str,
        file_path: Union[str, Path],
        checksum: Optional[str] = None,
        input_artifacts: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> ProvenanceRecord:
        """
        Record the creation of a new artifact.
        
        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of artifact (e.g., 'raw_data', 'processed_data').
            source_type: Source type ('real', 'synthetic', 'derived').
            file_path: Path to the artifact file.
            checksum: Optional SHA256 checksum.
            input_artifacts: List of input artifact IDs used to create this one.
            parameters: Parameters used in creation.
            notes: Optional notes.
        
        Returns:
            The created ProvenanceRecord.
        """
        record = ProvenanceRecord(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            source_type=source_type,
            created_at=datetime.datetime.now().isoformat(),
            created_by=self._get_creator_info(),
            input_artifacts=input_artifacts or [],
            parameters=parameters or {},
            checksum=checksum,
            file_path=str(file_path),
            notes=notes
        )
        
        self.records.append(record)
        
        if self.current_run:
            self.current_run.artifacts_created.append(artifact_id)
        
        self.logger.info("Recorded artifact: %s (type: %s, source: %s)", 
                       artifact_id, artifact_type, source_type)
        
        return record
    
    def compute_checksum(self, file_path: Union[str, Path]) -> str:
        """
        Compute SHA256 checksum of a file.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            Hex string of the SHA256 checksum.
        """
        sha256_hash = hashlib.sha256()
        file_path = Path(file_path)
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def save_manifest(self, manifest_name: str = "provenance_manifest.json") -> Path:
        """
        Save all provenance records to a manifest file.
        
        Args:
            manifest_name: Name of the manifest file.
        
        Returns:
            Path to the saved manifest file.
        """
        manifest_path = self.manifest_dir / manifest_name
        
        manifest_data = {
            "generated_at": datetime.datetime.now().isoformat(),
            "run_id": self.current_run.run_id if self.current_run else None,
            "total_records": len(self.records),
            "records": [r.to_dict() for r in self.records]
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2, default=str)
        
        self.logger.info("Saved provenance manifest: %s", manifest_path)
        return manifest_path
    
    def _get_creator_info(self) -> str:
        """Get information about the creator/environment."""
        return f"{platform.system()}|{platform.python_version()}|{sys.executable}"
    
    def _save_run(self) -> None:
        """Save the current run record."""
        if self.current_run is None:
            return
        
        run_path = self.manifest_dir / f"run_{self.current_run.run_id}.json"
        
        with open(run_path, "w") as f:
            f.write(self.current_run.to_json())
        
        self.logger.debug("Saved run record: %s", run_path)


# Global tracker instance
_tracker: Optional[ProvenanceTracker] = None


def get_provenance_tracker() -> ProvenanceTracker:
    """
    Get or create the global provenance tracker instance.
    
    Returns:
        ProvenanceTracker instance.
    """
    global _tracker
    if _tracker is None:
        _tracker = ProvenanceTracker()
    return _tracker


def record_provenance(
    artifact_id: str,
    artifact_type: str,
    source_type: str,
    file_path: Union[str, Path],
    checksum: Optional[str] = None,
    input_artifacts: Optional[List[str]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None
) -> ProvenanceRecord:
    """
    Convenience function to record artifact provenance.
    
    Args:
        artifact_id: Unique identifier for the artifact.
        artifact_type: Type of artifact.
        source_type: Source type ('real', 'synthetic', 'derived').
        file_path: Path to the artifact file.
        checksum: Optional SHA256 checksum.
        input_artifacts: List of input artifact IDs.
        parameters: Parameters used in creation.
        notes: Optional notes.
    
    Returns:
        The created ProvenanceRecord.
    """
    tracker = get_provenance_tracker()
    return tracker.record_artifact(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        source_type=source_type,
        file_path=file_path,
        checksum=checksum,
        input_artifacts=input_artifacts,
        parameters=parameters,
        notes=notes
    )
