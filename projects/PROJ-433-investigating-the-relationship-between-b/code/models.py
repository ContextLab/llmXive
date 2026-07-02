"""
Data models for the llmXive project.

This module defines the core entity models used throughout the pipeline,
including the Subject entity which represents a single participant in the study.
"""
import os
from typing import Dict, Optional, Any


class Subject:
    """
    Represents a single subject in the study.
    
    Attributes:
        id (str): Unique identifier for the subject.
        fMRI_path (str): Path to the subject's fMRI data file.
        DSST_score (float | None): Digit Symbol Substitution Test score, or None if unavailable.
        qc_metrics (dict): Dictionary containing quality control metrics for the subject.
    """
    
    def __init__(
        self,
        id: str,
        fMRI_path: str,
        DSST_score: Optional[float] = None,
        qc_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize a Subject instance.
        
        Args:
            id: Unique subject identifier.
            fMRI_path: Path to the fMRI data file.
            DSST_score: DSST behavioral score (optional).
            qc_metrics: Dictionary of QC metrics (defaults to empty dict).
        """
        self.id = id
        self.fMRI_path = fMRI_path
        self.DSST_score = DSST_score
        self.qc_metrics = qc_metrics if qc_metrics is not None else {}
    
    def has_valid_data(self) -> bool:
        """
        Check if the subject has all required data for analysis.
        
        Returns:
            True if fMRI_path exists on disk AND DSST_score is not None.
            False otherwise.
        """
        # Check if fMRI_path exists and is not empty string
        if not self.fMRI_path or not isinstance(self.fMRI_path, str):
            return False
        
        # Check if the file actually exists on disk
        if not os.path.exists(self.fMRI_path):
            return False
        
        # Check if DSST_score is available (not None)
        if self.DSST_score is None:
            return False
        
        return True
    
    def __repr__(self) -> str:
        return (
            f"Subject(id={self.id!r}, fMRI_path={self.fMRI_path!r}, "
            f"DSST_score={self.DSST_score!r}, qc_metrics={self.qc_metrics!r})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Subject instance to a dictionary representation.
        
        Returns:
            Dictionary containing all subject attributes.
        """
        return {
            'id': self.id,
            'fMRI_path': self.fMRI_path,
            'DSST_score': self.DSST_score,
            'qc_metrics': self.qc_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subject':
        """
        Create a Subject instance from a dictionary.
        
        Args:
            data: Dictionary containing subject data.
                
        Returns:
            New Subject instance.
        """
        return cls(
            id=data['id'],
            fMRI_path=data['fMRI_path'],
            DSST_score=data.get('DSST_score'),
            qc_metrics=data.get('qc_metrics', {})
        )
