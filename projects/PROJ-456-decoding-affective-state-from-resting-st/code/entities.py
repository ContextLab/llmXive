from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
from datetime import datetime

@dataclass
class EEGRecording:
    """
    Represents a raw or preprocessed EEG recording session.
    Corresponds to a single subject's data file (e.g., from OpenNeuro).
    """
    subject_id: str
    session_id: Optional[str]
    task: str
    sampling_frequency: float
    channel_count: int
    data: np.ndarray  # Shape: (channels, timepoints)
    channel_names: List[str]
    events: Optional[np.ndarray] = None  # Shape: (n_events, 3)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    data_path: Optional[str] = None
    preprocessing_steps: List[str] = field(default_factory=list)

@dataclass
class MicrostateSegmentation:
    """
    Represents the segmentation of an EEG recording into microstate classes.
    Stores the sequence of class labels and associated parameters.
    """
    subject_id: str
    session_id: Optional[str]
    segment_labels: np.ndarray  # 1D array of class labels (A, B, C, D)
    global_explained_variance: float
    template_path: Optional[str] = None
    segmentation_params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    analysis_type: str = "associational"

@dataclass
class MicrostateFeatures:
    """
    Extracted temporal features for each microstate class.
    Aggregated metrics per subject.
    """
    subject_id: str
    session_id: Optional[str]
    # Features per class (A, B, C, D)
    mean_duration: Dict[str, float]
    occurrence_rate: Dict[str, float]
    coverage: Dict[str, float]
    transition_probabilities: Dict[str, Dict[str, float]]
    # Global features
    global_ev: float
    created_at: datetime = field(default_factory=datetime.now)
    analysis_type: str = "associational"

@dataclass
class AffectiveScores:
    """
    Questionnaire scores for a subject.
    Supports PANAS (Positive/Negative Affect) and SAM (Self-Assessment Manikin).
    """
    subject_id: str
    session_id: Optional[str]
    instrument_type: str  # 'PANAS', 'SAM', etc.
    scores: Dict[str, float]  # e.g., {'positive': 25.0, 'negative': 12.0}
    response_rate: float  # 0.0 to 1.0
    raw_items: Optional[List[int]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CorrelationResult:
    """
    Result of a correlation analysis between microstate features and affective scores.
    """
    feature_name: str
    feature_class: str  # 'A', 'B', 'C', 'D'
    affective_dimension: str  # 'positive', 'negative', etc.
    correlation_coefficient: float
    p_value: float
    corrected_p_value: Optional[float] = None
    method: str  # 'pearson', 'spearman'
    n_subjects: int
    effect_size: Optional[float] = None  # Cohen's d or r
    confidence_interval: Optional[tuple] = None  # (lower, upper)
    is_significant: bool = False
    analysis_type: str = "associational"
    computed_at: datetime = field(default_factory=datetime.now)
