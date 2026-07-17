"""
Base entity classes for the llmXive automated science pipeline.

Defines the core data structures for audio clips, distortion vectors,
and stress curves used throughout the semantic collapse threshold analysis.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import hashlib


@dataclass(frozen=True)
class AudioClip:
    """
    Represents a single audio sample with its metadata.

    Attributes:
        path: Absolute or relative path to the audio file.
        speaker_id: Unique identifier for the speaker.
        transcript: Ground truth text transcription.
        snr_bucket: Signal-to-Noise Ratio bucket assignment (e.g., "clean", "low_snr").
        duration_seconds: Duration of the audio clip in seconds.
        sample_rate: Audio sample rate in Hz.
    """
    path: str
    speaker_id: str
    transcript: str
    snr_bucket: str
    duration_seconds: float
    sample_rate: int

    def __post_init__(self):
        # Validate path existence if it's a local file path (optional check)
        # We do not enforce existence here to allow for lazy loading or remote paths
        if not isinstance(self.path, str):
            raise TypeError("path must be a string")
        if not isinstance(self.speaker_id, str):
            raise TypeError("speaker_id must be a string")
        if not isinstance(self.transcript, str):
            raise TypeError("transcript must be a string")
        if not isinstance(self.snr_bucket, str):
            raise TypeError("snr_bucket must be a string")
        if not isinstance(self.duration_seconds, (int, float)):
            raise TypeError("duration_seconds must be numeric")
        if not isinstance(self.sample_rate, int):
            raise TypeError("sample_rate must be an integer")

    @property
    def id(self) -> str:
        """Generate a unique ID based on path hash."""
        return hashlib.md5(self.path.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "speaker_id": self.speaker_id,
            "transcript": self.transcript,
            "snr_bucket": self.snr_bucket,
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "id": self.id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioClip":
        """Create an AudioClip instance from a dictionary."""
        return cls(
            path=data["path"],
            speaker_id=data["speaker_id"],
            transcript=data["transcript"],
            snr_bucket=data["snr_bucket"],
            duration_seconds=data["duration_seconds"],
            sample_rate=data["sample_rate"]
        )


@dataclass(frozen=True)
class DistortionVector:
    """
    Represents a specific combination of acoustic distortions.

    Attributes:
        vector_id: Unique identifier for this distortion combination.
        snr_db: Signal-to-Noise Ratio in decibels.
        rt60_seconds: Reverberation time (RT60) in seconds.
        distortion_type: Label for the type of distortion (e.g., "compound_snr_rt60").
        intensity: Normalized intensity level (0.0 to 1.0) if applicable.
    """
    vector_id: str
    snr_db: float
    rt60_seconds: float
    distortion_type: str = "compound_snr_rt60"
    intensity: Optional[float] = None

    def __post_init__(self):
        if not isinstance(self.vector_id, str):
            raise TypeError("vector_id must be a string")
        if not isinstance(self.snr_db, (int, float)):
            raise TypeError("snr_db must be numeric")
        if not isinstance(self.rt60_seconds, (int, float)):
            raise TypeError("rt60_seconds must be numeric")
        if self.intensity is not None and not isinstance(self.intensity, (int, float)):
            raise TypeError("intensity must be numeric or None")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "vector_id": self.vector_id,
            "snr_db": self.snr_db,
            "rt60_seconds": self.rt60_seconds,
            "distortion_type": self.distortion_type,
            "intensity": self.intensity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DistortionVector":
        """Create a DistortionVector instance from a dictionary."""
        return cls(
            vector_id=data["vector_id"],
            snr_db=data["snr_db"],
            rt60_seconds=data["rt60_seconds"],
            distortion_type=data.get("distortion_type", "compound_snr_rt60"),
            intensity=data.get("intensity")
        )


@dataclass
class StressCurve:
    """
    Represents the stress curve for a single audio clip under a specific distortion scenario.

    This entity aggregates the results of applying multiple distortion intensities
    to a single audio clip, tracking the Semantic Similarity Score (SSS) and
    Word Error Rate (WER) at each step.

    Attributes:
        audio_clip: The AudioClip being tested.
        distortion_vector: The base DistortionVector configuration for this curve.
        data_points: List of dictionaries containing intensity, sss, wer, and hypothesis.
        collapse_point: The intensity value where semantic collapse is detected (if any).
        baseline_sss: The SSS at intensity 0 (clean audio).
        baseline_wer: The WER at intensity 0 (clean audio).
    """
    audio_clip: AudioClip
    distortion_vector: DistortionVector
    data_points: List[Dict[str, Any]] = field(default_factory=list)
    collapse_point: Optional[float] = None
    baseline_sss: Optional[float] = None
    baseline_wer: Optional[float] = None

    def add_point(self, intensity: float, sss: float, wer: float, hypothesis: str):
        """
        Add a data point to the stress curve.

        Args:
            intensity: The distortion intensity level (0.0 to 1.0).
            sss: Semantic Similarity Score.
            wer: Word Error Rate.
            hypothesis: The ASR hypothesis text.
        """
        if not isinstance(intensity, (int, float)):
            raise TypeError("intensity must be numeric")
        if not isinstance(sss, (int, float)):
            raise TypeError("sss must be numeric")
        if not isinstance(wer, (int, float)):
            raise TypeError("wer must be numeric")
        if not isinstance(hypothesis, str):
            raise TypeError("hypothesis must be a string")

        point = {
            "intensity": intensity,
            "sss": sss,
            "wer": wer,
            "hypothesis": hypothesis
        }
        self.data_points.append(point)

        # Update baselines if this is the first point (intensity 0)
        if intensity == 0.0:
            self.baseline_sss = sss
            self.baseline_wer = wer

    def get_curve_data(self) -> List[Dict[str, Any]]:
        """Return the sorted list of data points."""
        return sorted(self.data_points, key=lambda x: x["intensity"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entire curve to a dictionary for serialization."""
        return {
            "audio_clip_id": self.audio_clip.id,
            "audio_clip_path": self.audio_clip.path,
            "speaker_id": self.audio_clip.speaker_id,
            "distortion_vector_id": self.distortion_vector.vector_id,
            "distortion_params": self.distortion_vector.to_dict(),
            "data_points": self.get_curve_data(),
            "collapse_point": self.collapse_point,
            "baseline_sss": self.baseline_sss,
            "baseline_wer": self.baseline_wer
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StressCurve":
        """Create a StressCurve instance from a dictionary."""
        audio_clip = AudioClip.from_dict({
            "path": data["audio_clip_path"],
            "speaker_id": data["speaker_id"],
            "transcript": "", # Transcript not stored in curve dict usually, or needs separate lookup
            "snr_bucket": "", # Similar to above
            "duration_seconds": 0.0,
            "sample_rate": 0
        })
        # Note: Reconstructing AudioClip fully requires transcript/duration which might not be in the curve file.
        # For now, we create a minimal clip or assume external lookup.
        # To make this robust, we might just store the ID and look up the full object.
        # However, for serialization round-trip, we assume the caller handles the full object reconstruction
        # or we store minimal necessary info. Here we store the ID and path.

        # A better approach for from_dict is to expect the full audio_clip dict if available,
        # or reconstruct a minimal one. Let's assume the dict passed has the necessary fields for AudioClip
        # if they were serialized. If not, we rely on the ID.
        
        # For simplicity in this base class, we assume the dict contains the full audio_clip data
        # if it was serialized via to_dict.
        if "audio_clip" in data:
            audio_clip = AudioClip.from_dict(data["audio_clip"])
        else:
            # Fallback if only ID/path available (common in derived data)
            audio_clip = AudioClip(
                path=data.get("audio_clip_path", "unknown"),
                speaker_id=data.get("speaker_id", "unknown"),
                transcript="",
                snr_bucket="",
                duration_seconds=0.0,
                sample_rate=16000
            )

        distortion_vector = DistortionVector.from_dict(data["distortion_params"])

        curve = cls(
            audio_clip=audio_clip,
            distortion_vector=distortion_vector,
            data_points=data.get("data_points", []),
            collapse_point=data.get("collapse_point"),
            baseline_sss=data.get("baseline_sss"),
            baseline_wer=data.get("baseline_wer")
        )
        return curve

    def save_to_json(self, filepath: str):
        """Save the stress curve to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str) -> "StressCurve":
        """Load a stress curve from a JSON file."""
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)