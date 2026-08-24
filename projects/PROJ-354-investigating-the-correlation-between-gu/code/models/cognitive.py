"""
Cognitive score data model for the Gut Microbiome-Cognitive Correlation Study.

Represents cognitive assessment results and metadata, including field mappings
to UK Biobank cognitive test instruments and validation logic.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import date
import pandas as pd
import numpy as np

@dataclass
class CognitiveScore:
    """
    Represents a cognitive assessment score for a participant.
    
    Attributes:
        participant_id: Link to the Participant (UK Biobank e.g., 'eid')
        assessment_id: Unique assessment instance identifier
        assessment_date: Date of cognitive assessment
        test_type: Type of cognitive test (e.g., 'fluid_intelligence', 'reaction_time')
        raw_score: Raw score from the test
        scaled_score: Normalized/scaled score (if applicable)
        z_score: Z-score relative to population (if applicable)
        percentile: Percentile rank (if applicable)
        time_taken: Time taken to complete test (seconds)
        num_trials: Number of trials in the assessment
        num_correct: Number of correct responses
        accuracy: Proportion of correct responses
        test_version: Version of the test administered
        assessment_center: UK Biobank assessment center ID
        instrument_id: Reference to the specific cognitive instrument (FR-009)
        quality_flag: Flag for data quality issues
    """
    participant_id: str
    assessment_id: str
    assessment_date: Optional[str] = None
    test_type: str = 'fluid_intelligence'
    raw_score: Optional[float] = None
    scaled_score: Optional[float] = None
    z_score: Optional[float] = None
    percentile: Optional[float] = None
    time_taken: Optional[float] = None
    num_trials: Optional[int] = None
    num_correct: Optional[int] = None
    accuracy: Optional[float] = None
    test_version: Optional[str] = None
    assessment_center: Optional[int] = None
    instrument_id: Optional[str] = None
    quality_flag: bool = False
    
    # Composite scores (derived)
    composite_cognitive_score: Optional[float] = None
    
    def __post_init__(self):
        """Validate cognitive data after initialization."""
        # Validate accuracy calculation if num_trials and num_correct are present
        if self.num_trials is not None and self.num_correct is not None:
            if self.num_trials > 0:
                expected_accuracy = self.num_correct / self.num_trials
                if self.accuracy is None:
                    self.accuracy = expected_accuracy
                elif abs(self.accuracy - expected_accuracy) > 0.01:
                    # Log warning but don't fail
                    pass
        
        # Validate test_type against known instruments
        valid_types = [
            'fluid_intelligence', 'reaction_time', 'matching', 
            'pairs_matching', 'prospective_memory', 'n_back'
        ]
        if self.test_type not in valid_types:
            # Log warning for unknown test type
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary representation."""
        return {
            'participant_id': self.participant_id,
            'assessment_id': self.assessment_id,
            'assessment_date': self.assessment_date,
            'test_type': self.test_type,
            'raw_score': self.raw_score,
            'scaled_score': self.scaled_score,
            'z_score': self.z_score,
            'percentile': self.percentile,
            'time_taken': self.time_taken,
            'num_trials': self.num_trials,
            'num_correct': self.num_correct,
            'accuracy': self.accuracy,
            'test_version': self.test_version,
            'assessment_center': self.assessment_center,
            'instrument_id': self.instrument_id,
            'quality_flag': self.quality_flag,
            'composite_cognitive_score': self.composite_cognitive_score
        }
    
    @classmethod
    def from_row(cls, row: pd.Series) -> 'CognitiveScore':
        """
        Create a CognitiveScore instance from a pandas Series row.
        
        Args:
            row: pandas Series containing cognitive data
            
        Returns:
            CognitiveScore instance
        """
        return cls(
            participant_id=str(row.get('participant_id', row.get('eid', ''))),
            assessment_id=str(row.get('assessment_id', row.get('field_id', ''))),
            assessment_date=row.get('assessment_date', None),
            test_type=row.get('test_type', 'fluid_intelligence'),
            raw_score=row.get('raw_score', None),
            scaled_score=row.get('scaled_score', None),
            z_score=row.get('z_score', None),
            percentile=row.get('percentile', None),
            time_taken=row.get('time_taken', None),
            num_trials=int(row.get('num_trials', None)) if pd.notna(row.get('num_trials', None)) else None,
            num_correct=int(row.get('num_correct', None)) if pd.notna(row.get('num_correct', None)) else None,
            accuracy=row.get('accuracy', None),
            test_version=row.get('test_version', None),
            assessment_center=int(row.get('assessment_center', None)) if pd.notna(row.get('assessment_center', None)) else None,
            instrument_id=row.get('instrument_id', None),
            quality_flag=bool(row.get('quality_flag', False)),
            composite_cognitive_score=row.get('composite_cognitive_score', None)
        )
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> List['CognitiveScore']:
        """
        Create a list of CognitiveScore instances from a DataFrame.
        
        Args:
            df: DataFrame with cognitive data
            
        Returns:
            List of CognitiveScore instances
        """
        return [cls.from_row(row) for _, row in df.iterrows()]

def create_cognitive_dataframe(scores: List[CognitiveScore]) -> pd.DataFrame:
    """
    Convert a list of CognitiveScore instances to a DataFrame.
    
    Args:
        scores: List of CognitiveScore instances
        
    Returns:
        DataFrame with cognitive data
    """
    data = [s.to_dict() for s in scores]
    return pd.DataFrame(data)

def compute_composite_score(scores: List[CognitiveScore]) -> Dict[str, float]:
    """
    Compute composite cognitive scores for participants with multiple assessments.
    
    Args:
        scores: List of CognitiveScore instances
        
    Returns:
        Dictionary mapping participant_id to composite score
    """
    # Group by participant
    participant_scores: Dict[str, List[CognitiveScore]] = {}
    for s in scores:
        if s.participant_id not in participant_scores:
            participant_scores[s.participant_id] = []
        participant_scores[s.participant_id].append(s)
    
    composites = {}
    for pid, p_scores in participant_scores.items():
        # Filter for valid scores
        valid_scores = [s for s in p_scores if s.scaled_score is not None]
        if valid_scores:
            # Average of scaled scores
            avg_score = np.mean([s.scaled_score for s in valid_scores])
            composites[pid] = avg_score
            # Update original objects
            for s in valid_scores:
                s.composite_cognitive_score = avg_score
    
    return composites
