"""
Base data models for the llmXive LiveEdit follow-up project.

Defines core data structures for video clips, metric records, and analysis results.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import numpy as np


@dataclass
class VideoClip:
    """
    Represents a single video clip with associated metadata and processing results.

    Attributes:
        clip_id: Unique identifier for the clip.
        source_dataset: Name of the source dataset (e.g., 'DAVIS', 'YouTube-VOS').
        video_path: Path to the video file.
        mask_path: Optional path to the associated mask file.
        duration_seconds: Duration of the video in seconds.
        frame_count: Number of frames in the video.
        resolution: Tuple of (height, width).
        motion_category: Classification of motion complexity (e.g., 'Static', 'Slow Rigid', 'Fast Non-Rigid').
        flow_magnitude_mean: Mean optical flow magnitude across the clip.
        flow_magnitude_std: Standard deviation of optical flow magnitude.
        metadata: Additional arbitrary metadata.
    """
    clip_id: str
    source_dataset: str
    video_path: str
    mask_path: Optional[str] = None
    duration_seconds: float = 0.0
    frame_count: int = 0
    resolution: tuple = (0, 0)
    motion_category: str = "Unknown"
    flow_magnitude_mean: float = 0.0
    flow_magnitude_std: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "clip_id": self.clip_id,
            "source_dataset": self.source_dataset,
            "video_path": self.video_path,
            "mask_path": self.mask_path,
            "duration_seconds": self.duration_seconds,
            "frame_count": self.frame_count,
            "resolution": list(self.resolution),
            "motion_category": self.motion_category,
            "flow_magnitude_mean": self.flow_magnitude_mean,
            "flow_magnitude_std": self.flow_magnitude_std,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VideoClip":
        """Create a VideoClip instance from a dictionary."""
        resolution = data.get("resolution", [0, 0])
        if isinstance(resolution, list):
            resolution = tuple(resolution)
        return cls(
            clip_id=data["clip_id"],
            source_dataset=data["source_dataset"],
            video_path=data["video_path"],
            mask_path=data.get("mask_path"),
            duration_seconds=data.get("duration_seconds", 0.0),
            frame_count=data.get("frame_count", 0),
            resolution=resolution,
            motion_category=data.get("motion_category", "Unknown"),
            flow_magnitude_mean=data.get("flow_magnitude_mean", 0.0),
            flow_magnitude_std=data.get("flow_magnitude_std", 0.0),
            metadata=data.get("metadata", {})
        )


@dataclass
class MetricRecord:
    """
    Represents a single metric measurement for a specific frame or clip.

    Attributes:
        record_id: Unique identifier for the record.
        clip_id: Reference to the associated VideoClip.
        timestamp: Time of metric generation.
        method: Inference method used (e.g., 'baseline', 'flow_coherence').
        frame_index: Index of the specific frame (if applicable, else -1).
        peak_memory_mb: Peak RAM usage in Megabytes.
        inference_time_ms: Inference time in milliseconds.
        bss_score: Background Stability Score.
        ssim_score: Structural Similarity Index Measure (Flow-Normalized).
        flow_magnitude: Optical flow magnitude at this point.
        invalid_flow: Flag indicating if flow was invalid (NaN/Inf) and identity warp was used.
        metadata: Additional metrics or context.
    """
    record_id: str
    clip_id: str
    timestamp: datetime
    method: str
    frame_index: int = -1
    peak_memory_mb: float = 0.0
    inference_time_ms: float = 0.0
    bss_score: float = 0.0
    ssim_score: float = 0.0
    flow_magnitude: float = 0.0
    invalid_flow: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "record_id": self.record_id,
            "clip_id": self.clip_id,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "frame_index": self.frame_index,
            "peak_memory_mb": self.peak_memory_mb,
            "inference_time_ms": self.inference_time_ms,
            "bss_score": self.bss_score,
            "ssim_score": self.ssim_score,
            "flow_magnitude": self.flow_magnitude,
            "invalid_flow": self.invalid_flow,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricRecord":
        """Create a MetricRecord instance from a dictionary."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            record_id=data["record_id"],
            clip_id=data["clip_id"],
            timestamp=ts,
            method=data["method"],
            frame_index=data.get("frame_index", -1),
            peak_memory_mb=data.get("peak_memory_mb", 0.0),
            inference_time_ms=data.get("inference_time_ms", 0.0),
            bss_score=data.get("bss_score", 0.0),
            ssim_score=data.get("ssim_score", 0.0),
            flow_magnitude=data.get("flow_magnitude", 0.0),
            invalid_flow=data.get("invalid_flow", False),
            metadata=data.get("metadata", {})
        )


@dataclass
class AnalysisResult:
    """
    Represents the aggregated results of a statistical analysis task.

    Attributes:
        analysis_id: Unique identifier for the analysis run.
        timestamp: Time of analysis completion.
        method_comparison: Comparison of methods (e.g., 'baseline' vs 'flow_coherence').
        ks_statistic: Kolmogorov-Smirnov test statistic.
        ks_p_value: Kolmogorov-Smirnov test p-value.
        change_point_threshold: Identified flow magnitude threshold for artifact generation.
        change_point_confidence: Confidence interval for the change point.
        memory_reduction_pct: Percentage of memory reduction achieved by the new method.
        ssim_drop_threshold: Threshold where SSIM degradation becomes significant.
        sample_size: Number of samples used in the analysis.
        raw_data_summary: Summary statistics of the raw data used.
        metadata: Additional analysis context.
    """
    analysis_id: str
    timestamp: datetime
    method_comparison: str
    ks_statistic: Optional[float] = None
    ks_p_value: Optional[float] = None
    change_point_threshold: Optional[float] = None
    change_point_confidence: Optional[List[float]] = None
    memory_reduction_pct: Optional[float] = None
    ssim_drop_threshold: Optional[float] = None
    sample_size: int = 0
    raw_data_summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp.isoformat(),
            "method_comparison": self.method_comparison,
            "ks_statistic": self.ks_statistic,
            "ks_p_value": self.ks_p_value,
            "change_point_threshold": self.change_point_threshold,
            "change_point_confidence": self.change_point_confidence,
            "memory_reduction_pct": self.memory_reduction_pct,
            "ssim_drop_threshold": self.ssim_drop_threshold,
            "sample_size": self.sample_size,
            "raw_data_summary": self.raw_data_summary,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        """Create an AnalysisResult instance from a dictionary."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            analysis_id=data["analysis_id"],
            timestamp=ts,
            method_comparison=data["method_comparison"],
            ks_statistic=data.get("ks_statistic"),
            ks_p_value=data.get("ks_p_value"),
            change_point_threshold=data.get("change_point_threshold"),
            change_point_confidence=data.get("change_point_confidence"),
            memory_reduction_pct=data.get("memory_reduction_pct"),
            ssim_drop_threshold=data.get("ssim_drop_threshold"),
            sample_size=data.get("sample_size", 0),
            raw_data_summary=data.get("raw_data_summary", {}),
            metadata=data.get("metadata", {})
        )