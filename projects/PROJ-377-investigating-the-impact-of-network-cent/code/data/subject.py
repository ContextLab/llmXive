"""
Subject data model.

Represents a single participant in the motor memory consolidation study,
including demographic information, behavioral scores, and processing status.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
from pathlib import Path

@dataclass
class Subject:
    """
    Represents a study participant.
    
    Attributes:
        subject_id: Unique identifier (e.g., 'sub-001')
        age: Age in years
        sex: Biological sex ('M' or 'F')
        pre_motor_score: Pre-training motor task score
        post_motor_score: Post-training motor task score
        improvement_score: Calculated improvement (post - pre)
        fmriprep_path: Path to fMRIPrep processed data directory
        connectivity_matrix_path: Path to saved connectivity matrix
        excluded: Whether subject was excluded from analysis
        exclusion_reason: Reason for exclusion if applicable
        metadata: Additional key-value pairs
    """
    subject_id: str
    age: Optional[float] = None
    sex: Optional[str] = None
    pre_motor_score: Optional[float] = None
    post_motor_score: Optional[float] = None
    improvement_score: Optional[float] = None
    fmriprep_path: Optional[Path] = None
    connectivity_matrix_path: Optional[Path] = None
    excluded: bool = False
    exclusion_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize derived fields and convert paths."""
        if self.fmriprep_path:
            self.fmriprep_path = Path(self.fmriprep_path)
        if self.connectivity_matrix_path:
            self.connectivity_matrix_path = Path(self.connectivity_matrix_path)
        
        # Calculate improvement if both scores are available
        if (self.pre_motor_score is not None and 
            self.post_motor_score is not None):
            self.improvement_score = self.post_motor_score - self.pre_motor_score
    
    @property
    def is_valid_for_analysis(self) -> bool:
        """Check if subject has all required data for analysis."""
        if self.excluded:
            return False
        
        required_fields = [
            'pre_motor_score', 'post_motor_score', 
            'fmriprep_path', 'connectivity_matrix_path'
        ]
        
        for field_name in required_fields:
            value = getattr(self, field_name)
            if value is None:
                return False
            
            # Check if path exists for path fields
            if isinstance(value, Path) and not value.exists():
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subject to dictionary representation."""
        return {
            'subject_id': self.subject_id,
            'age': self.age,
            'sex': self.sex,
            'pre_motor_score': self.pre_motor_score,
            'post_motor_score': self.post_motor_score,
            'improvement_score': self.improvement_score,
            'fmriprep_path': str(self.fmriprep_path) if self.fmriprep_path else None,
            'connectivity_matrix_path': str(self.connectivity_matrix_path) if self.connectivity_matrix_path else None,
            'excluded': self.excluded,
            'exclusion_reason': self.exclusion_reason,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subject':
        """Create Subject instance from dictionary."""
        return cls(
            subject_id=data['subject_id'],
            age=data.get('age'),
            sex=data.get('sex'),
            pre_motor_score=data.get('pre_motor_score'),
            post_motor_score=data.get('post_motor_score'),
            fmriprep_path=data.get('fmriprep_path'),
            connectivity_matrix_path=data.get('connectivity_matrix_path'),
            excluded=data.get('excluded', False),
            exclusion_reason=data.get('exclusion_reason'),
            metadata=data.get('metadata', {})
        )
