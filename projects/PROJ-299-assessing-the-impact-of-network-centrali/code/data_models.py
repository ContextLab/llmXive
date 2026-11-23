from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

@dataclass
class Participant:
    """
    Represents a single study participant.
    Corresponds to FR-001 (Data Hygiene) and FR-006 (Data Merging).
    """
    participant_id: str
    age: int
    sex: str  # 'M' or 'F'
    education_years: int
    diagnosis: str  # e.g., 'CN', 'MCI', 'AD'
    enrollment_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'participant_id': self.participant_id,
            'age': self.age,
            'sex': self.sex,
            'education_years': self.education_years,
            'diagnosis': self.diagnosis,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            **self.metadata
        }

@dataclass
class ImagingSession:
    """
    Represents a single imaging acquisition session for a participant.
    Includes QC metrics derived during preprocessing.
    """
    session_id: str
    participant_id: str
    acquisition_date: datetime
    modality: str  # e.g., 'rs-fMRI', 'T1w'
    raw_file_path: Optional[str] = None
    preprocessed_file_path: Optional[str] = None
    mean_fd: float = 0.0
    excluded: bool = False
    exclusion_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'participant_id': self.participant_id,
            'acquisition_date': self.acquisition_date.isoformat(),
            'modality': self.modality,
            'raw_file_path': self.raw_file_path,
            'preprocessed_file_path': self.preprocessed_file_path,
            'mean_fd': self.mean_fd,
            'excluded': self.excluded,
            'exclusion_reason': self.exclusion_reason,
            **self.metadata
        }

@dataclass
class CentralityMetrics:
    """
    Stores network centrality metrics for a specific participant/session.
    Includes raw ROI-level metrics and aggregated network means.
    Corresponds to FR-004 (Centrality Calculation) and FR-016 (Aggregation).
    """
    session_id: str
    participant_id: str
    # Raw ROI metrics: Dict[roi_name, Dict[metric_name, value]]
    # Example: {'Hippocampus_L': {'degree': 0.85, 'betweenness': 0.12, 'closeness': 0.45}}
    roi_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Aggregated network means (loaded from code/config/network_rois.json)
    # Example: {'degree_DMN': 0.72, 'betweenness_FPN': 0.15}
    network_aggregates: Dict[str, float] = field(default_factory=dict)
    
    # Global means across all ROIs
    global_degree: Optional[float] = None
    global_betweenness: Optional[float] = None
    global_closeness: Optional[float] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        # Flatten ROI metrics for CSV export if needed, but keep structure for internal use
        # Here we return a flat structure for the aggregated view which is often needed for regression
        flat_data = {
            'session_id': self.session_id,
            'participant_id': self.participant_id,
            'global_degree': self.global_degree,
            'global_betweenness': self.global_betweenness,
            'global_closeness': self.global_closeness,
            **self.network_aggregates
        }
        
        # Optional: Include a JSON string of raw ROI metrics for detailed inspection
        # or keep them separate. For the CSV requirement (centrality_metrics.csv),
        # we typically export the aggregated columns.
        # We will include the raw metrics as a JSON string column if needed by downstream tasks,
        # but the primary regression inputs are the aggregates.
        return flat_data

@dataclass
class CognitiveScore:
    """
    Represents a cognitive assessment score for a participant.
    Corresponds to FR-006 (Data Merging) and FR-001 (Data Hygiene).
    """
    participant_id: str
    assessment_date: datetime
    domain: str  # e.g., 'Memory', 'Executive', 'Attention'
    test_name: str  # e.g., 'ADAS-Cog', 'TMT-A', 'WAIS-R'
    score: float
    raw_value: Optional[float] = None  # Original untransformed value if applicable
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'participant_id': self.participant_id,
            'assessment_date': self.assessment_date.isoformat(),
            'domain': self.domain,
            'test_name': self.test_name,
            'score': self.score,
            'raw_value': self.raw_value,
            **self.metadata
        }

@dataclass
class RegressionResult:
    """
    Stores the results of a linear regression model.
    Corresponds to FR-005 (Regression Engine) and FR-008 (Diagnostics).
    """
    model_id: str
    dependent_variable: str  # e.g., 'Memory_Score'
    independent_variable: str  # e.g., 'degree_DMN'
    covariates: List[str] = field(default_factory=list)  # e.g., ['age', 'sex', 'education']
    
    # Coefficients
    intercept: float = 0.0
    coef: float = 0.0
    std_err: float = 0.0
    p_value: float = 1.0
    q_value: float = 1.0  # FDR corrected
    partial_r: float = 0.0
    
    # Model Fit
    r_squared: float = 0.0
    adj_r_squared: float = 0.0
    f_statistic: float = 0.0
    p_f_stat: float = 1.0
    
    # Diagnostics
    vif_values: Dict[str, float] = field(default_factory=dict)
    shapiro_p: Optional[float] = None
    breusch_pagan_p: Optional[float] = None
    assumption_flags: List[str] = field(default_factory=list)  # e.g., ['Non-Normal Residuals']
    
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_id': self.model_id,
            'dependent_variable': self.dependent_variable,
            'independent_variable': self.independent_variable,
            'covariates': ','.join(self.covariates),
            'intercept': self.intercept,
            'coef': self.coef,
            'std_err': self.std_err,
            'p_value': self.p_value,
            'q_value': self.q_value,
            'partial_r': self.partial_r,
            'r_squared': self.r_squared,
            'adj_r_squared': self.adj_r_squared,
            'f_statistic': self.f_statistic,
            'p_f_stat': self.p_f_stat,
            'vif_values': self.vif_values,
            'shapiro_p': self.shapiro_p,
            'breusch_pagan_p': self.breusch_pagan_p,
            'assumption_flags': ','.join(self.assumption_flags),
            **self.metadata
        }