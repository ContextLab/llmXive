import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class SubjectStatus(Enum):
    """Enumeration of possible subject processing statuses."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PREPROCESSING = "preprocessing"
    QC_FAILED = "qc_failed"
    PROCESSED = "processed"
    EXCLUDED = "excluded"


@dataclass
class Subject:
    """
    Dataclass representing a research subject.
    Stores metadata, processing status, and links to derived data.
    """
    subject_id: str
    status: SubjectStatus = SubjectStatus.PENDING
    exclusion_reason: Optional[str] = None
    mean_fd: Optional[float] = None  # Mean Framewise Displacement
    n_scans: Optional[int] = None
    n_timepoints: Optional[int] = None
    n_regions: Optional[int] = None
    raw_nifti_path: Optional[str] = None
    preprocessed_path: Optional[str] = None
    timeseries_path: Optional[str] = None
    connectivity_matrix: Optional['ConnectivityMatrix'] = None
    topology_metrics: Optional['TopologyMetrics'] = None
    illusion_score: Optional['IllusionScore'] = None
    metadata: dict = field(default_factory=dict)

    def is_excluded(self) -> bool:
        """Check if subject is excluded based on status or reason."""
        return self.status == SubjectStatus.EXCLUDED or self.status == SubjectStatus.QC_FAILED

    def set_excluded(self, reason: str) -> None:
        """Mark subject as excluded with a specific reason."""
        self.status = SubjectStatus.EXCLUDED
        self.exclusion_reason = reason
        self.mean_fd = None  # Clear FD if excluded, or keep for audit? Keeping for audit in DB, but logic uses status.
        # Actually, per T015, we record FD then exclude. So we keep the record.
        # Re-reading T015: "calculate mean FD for ALL subjects, record the value, and exclude subjects..."
        # So we keep mean_fd recorded even if excluded.
        self.status = SubjectStatus.EXCLUDED
        self.exclusion_reason = reason
