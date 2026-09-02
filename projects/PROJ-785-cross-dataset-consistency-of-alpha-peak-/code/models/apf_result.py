"""
Data model for Alpha Peak Frequency (APF) estimation results.
Matches the schema expected by contracts and used throughout the pipeline.
"""
from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
import json

@dataclass
class APFResult:
    """
    Represents an APF estimation result for a single subject/session.
    
    Attributes:
        dataset_id: Source dataset identifier
        subject_id: Subject identifier
        session_id: Session identifier (if available)
        pipeline_type: 'Pipeline A' or 'Pipeline B'
        estimation_method: 'psd' or 'autocorr'
        apf_value: Estimated Alpha Peak Frequency in Hz
        apf_status: 'valid', 'indeterminate', or 'out_of_band'
        peak_power: Power at the detected peak (for PSD method)
        lag_index: Lag index of the peak (for autocorr method)
        confidence_interval: Optional tuple (lower, upper) for bootstrap CI
        created_at: Timestamp of result generation
    """
    dataset_id: str
    subject_id: str
    session_id: Optional[str] = None
    pipeline_type: Literal["Pipeline A", "Pipeline B"] = "Pipeline A"
    estimation_method: Literal["psd", "autocorr"] = "psd"
    apf_value: Optional[float] = None
    apf_status: Literal["valid", "indeterminate", "out_of_band"] = "valid"
    peak_power: Optional[float] = None
    lag_index: Optional[int] = None
    confidence_interval: Optional[tuple] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert the result to a dictionary for serialization."""
        ci = None
        if self.confidence_interval:
            ci = list(self.confidence_interval)
        
        return {
            "dataset_id": self.dataset_id,
            "subject_id": self.subject_id,
            "session_id": self.session_id,
            "pipeline_type": self.pipeline_type,
            "estimation_method": self.estimation_method,
            "apf_value": self.apf_value,
            "apf_status": self.apf_status,
            "peak_power": self.peak_power,
            "lag_index": self.lag_index,
            "confidence_interval": ci,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "APFResult":
        """Create an APFResult instance from a dictionary."""
        ci = data.get("confidence_interval")
        if ci:
            ci = tuple(ci)
        
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            dataset_id=data["dataset_id"],
            subject_id=data["subject_id"],
            session_id=data.get("session_id"),
            pipeline_type=data.get("pipeline_type", "Pipeline A"),
            estimation_method=data.get("estimation_method", "psd"),
            apf_value=data.get("apf_value"),
            apf_status=data.get("apf_status", "valid"),
            peak_power=data.get("peak_power"),
            lag_index=data.get("lag_index"),
            confidence_interval=ci,
            created_at=created_at or datetime.utcnow(),
        )

    def to_csv_row(self) -> dict:
        """Convert to a flat dictionary suitable for CSV export."""
        row = self.to_dict()
        if row["confidence_interval"]:
            row["ci_lower"] = row["confidence_interval"][0]
            row["ci_upper"] = row["confidence_interval"][1]
            del row["confidence_interval"]
        return row
