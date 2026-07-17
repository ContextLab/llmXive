"""
Base data structures for the EvalVerse feature distillation pipeline.

This module defines the core data models used throughout the pipeline:
- VideoClip: Represents a single video clip with metadata and paths.
- FeatureVector: Represents extracted numerical features (visual/audio).
- DimensionScore: Represents human expert scores or model predictions for specific dimensions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class VideoClip:
    """
    Represents a single video clip from the EvalVerse dataset.

    Attributes:
        clip_id: Unique identifier for the clip (e.g., from the dataset metadata).
        file_path: Absolute or relative path to the video file on disk.
        duration: Duration of the video in seconds.
        metadata: Dictionary containing any additional metadata (resolution, fps, etc.).
        source: Source of the video (e.g., 'EvalVerse', 'YouTube').
    """
    clip_id: str
    file_path: str
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "EvalVerse"

    def __post_init__(self):
        if not self.clip_id:
            raise ValueError("clip_id cannot be empty")
        if not self.file_path:
            raise ValueError("file_path cannot be empty")
        if self.duration < 0:
            raise ValueError("duration cannot be negative")


@dataclass
class FeatureVector:
    """
    Represents a collection of extracted features for a video clip.

    Attributes:
        clip_id: ID of the video clip this vector belongs to.
        visual_features: Dictionary of visual feature names to values (e.g., optical flow stats).
        audio_features: Dictionary of audio feature names to values (e.g., spectral centroid).
        combined_vector: Optional pre-computed numpy array combining all features.
        extraction_time: Time taken to extract features in seconds.
    """
    clip_id: str
    visual_features: Dict[str, float] = field(default_factory=dict)
    audio_features: Dict[str, float] = field(default_factory=dict)
    combined_vector: Optional[np.ndarray] = None
    extraction_time: float = 0.0

    def __post_init__(self):
        if not self.clip_id:
            raise ValueError("clip_id cannot be empty")

    def to_numpy(self) -> np.ndarray:
        """
        Combines visual and audio features into a single numpy array.
        If combined_vector is already set, returns it. Otherwise, constructs it
        by concatenating values from visual_features and audio_features.
        """
        if self.combined_vector is not None:
            return self.combined_vector

        # Ensure deterministic ordering for reproducibility
        visual_keys = sorted(self.visual_features.keys())
        audio_keys = sorted(self.audio_features.keys())

        visual_vals = [self.visual_features[k] for k in visual_keys]
        audio_vals = [self.audio_features[k] for k in audio_keys]

        all_vals = np.array(visual_vals + audio_vals, dtype=np.float32)
        self.combined_vector = all_vals
        return all_vals

    def get_feature_names(self) -> List[str]:
        """Returns a sorted list of all feature names (visual + audio)."""
        return sorted(list(self.visual_features.keys()) + list(self.audio_features.keys()))

    def __len__(self):
        """Returns the total number of features."""
        return len(self.visual_features) + len(self.audio_features)


@dataclass
class DimensionScore:
    """
    Represents a score for a specific evaluation dimension (e.g., 'Motion', 'Audio Quality').

    This can represent either a human expert score or a model-predicted score.

    Attributes:
        dimension_name: Name of the dimension (e.g., "Motion", "Temporal Coherence").
        score: The numerical score (typically 0.0 to 1.0 or 0-5).
        source: Who/what generated the score ('human_expert', 'vlm_proxy', 'model').
        confidence: Optional confidence score for the prediction (0.0 to 1.0).
        clip_id: ID of the video clip this score applies to.
    """
    dimension_name: str
    score: float
    source: str
    clip_id: str
    confidence: Optional[float] = None

    def __post_init__(self):
        if not self.dimension_name:
            raise ValueError("dimension_name cannot be empty")
        if not self.source:
            raise ValueError("source cannot be empty")
        if not self.clip_id:
            raise ValueError("clip_id cannot be empty")
        
        # Basic validation for score range if it looks like a normalized score
        # We allow any float but flag extreme values if they look like errors
        if self.score < -10.0 or self.score > 10.0:
            # Log a warning or raise if strict validation is needed
            pass 
    
    def is_human(self) -> bool:
        """Returns True if the score comes from a human expert."""
        return self.source == "human_expert"

    def is_proxy(self) -> bool:
        """Returns True if the score comes from a VLM proxy or model."""
        return self.source in ("vlm_proxy", "model")