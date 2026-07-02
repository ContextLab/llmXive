"""
Base data models and entities for the network centrality research pipeline.

This module defines the core data structures used throughout the project
for representing participants, imaging sessions, centrality metrics,
cognitive scores, and regression results.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


@dataclass
class Participant:
    """Represents a study participant with demographic and clinical information."""
    participant_id: str
    age: int
    sex: str  # 'M' or 'F'
    education_years: int
    diagnosis: str  # e.g., 'CN', 'MCI', 'AD'
    adni_id: Optional[str] = None  # Original ADNI identifier
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.participant_id:
            raise ValueError("participant_id cannot be empty")


@dataclass
class ImagingSession:
    """Represents a single imaging session for a participant."""
    session_id: str
    participant_id: str
    acquisition_date: datetime
    modality: str  # e.g., 'rs-fMRI', 'T1', 'DTI'
    raw_file_path: str
    preprocessed_file_path: Optional[str] = None
    qc_passed: bool = True
    framewise_displacement: Optional[float] = None  # Mean FD in mm
    motion_excluded: bool = False
    exclusion_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.session_id or not self.participant_id:
            raise ValueError("session_id and participant_id are required")


@dataclass
class CentralityMetrics:
    """
    Stores centrality metrics for a specific imaging session.
    Contains raw ROI-level metrics and optionally network-aggregated metrics.
    """
    session_id: str
    participant_id: str
    roi_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Structure: {roi_name: {'degree': float, 'betweenness': float, 'closeness': float}}
    
    network_aggregates: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Structure: {network_name: {'degree_mean': float, 'betweenness_mean': float, ...}}
    
    global_aggregates: Dict[str, float] = field(default_factory=dict)
    # Structure: {'degree_mean': float, 'betweenness_mean': float, ...}
    
    created_at: datetime = field(default_factory=datetime.now)

    def add_roi_metric(self, roi_name: str, degree: float, betweenness: float, closeness: float):
        """Add centrality metrics for a single ROI."""
        self.roi_metrics[roi_name] = {
            'degree': degree,
            'betweenness': betweenness,
            'closeness': closeness
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'participant_id': self.participant_id,
            'roi_metrics': self.roi_metrics,
            'network_aggregates': self.network_aggregates,
            'global_aggregates': self.global_aggregates,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class CognitiveScore:
    """Represents cognitive assessment scores for a participant."""
    participant_id: str
    assessment_date: datetime
    domain: str  # e.g., 'memory', 'executive', 'attention'
    test_name: str  # e.g., 'ADAS13', 'MMSE', 'TrailMakingA'
    score: float
    raw_score: Optional[float] = None
    normalized_score: Optional[float] = None
    age_adjusted: bool = False
    education_adjusted: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.participant_id or not self.domain or not self.test_name:
            raise ValueError("participant_id, domain, and test_name are required")
        if self.score is None:
            raise ValueError("score cannot be None")


@dataclass
class RegressionResult:
    """
    Stores the results of a single regression analysis.
    Represents one (Centrality Metric × Cognitive Domain) pair.
    """
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    centrality_metric: str = ''  # e.g., 'degree', 'betweenness', 'closeness'
    network: str = ''  # e.g., 'DMN', 'FPN', 'global'
    cognitive_domain: str = ''  # e.g., 'memory', 'executive', 'attention'
    model_type: str = 'linear'
    
    # Regression coefficients
    beta: Optional[float] = None
    beta_se: Optional[float] = None
    p_value: Optional[float] = None
    q_value: Optional[float] = None  # FDR-adjusted
    partial_r: Optional[float] = None
    r_squared: Optional[float] = None
    
    # Diagnostics
    vif: Optional[float] = None
    shapiro_p: Optional[float] = None
    breusch_pagan_p: Optional[float] = None
    assumption_violations: List[str] = field(default_factory=list)
    
    # Metadata
    sample_size: int = 0
    covariates: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'analysis_id': self.analysis_id,
            'centrality_metric': self.centrality_metric,
            'network': self.network,
            'cognitive_domain': self.cognitive_domain,
            'model_type': self.model_type,
            'beta': self.beta,
            'beta_se': self.beta_se,
            'p_value': self.p_value,
            'q_value': self.q_value,
            'partial_r': self.partial_r,
            'r_squared': self.r_squared,
            'vif': self.vif,
            'shapiro_p': self.shapiro_p,
            'breusch_pagan_p': self.breusch_pagan_p,
            'assumption_violations': self.assumption_violations,
            'sample_size': self.sample_size,
            'covariates': self.covariates,
            'created_at': self.created_at.isoformat()
        }

    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if the result is statistically significant after FDR correction."""
        if self.q_value is None:
            return False
        return self.q_value < alpha