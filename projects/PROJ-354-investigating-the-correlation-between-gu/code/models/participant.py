"""
Participant data model for the Gut Microbiome-Cognitive Correlation Study.

Represents demographic and clinical information for study participants,
including UK Biobank field mappings and validation logic.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date
import pandas as pd
import numpy as np

@dataclass
class Participant:
    """
    Represents a single study participant with demographic and clinical data.
    
    Attributes:
        participant_id: Unique identifier (UK Biobank e.g., 'eid')
        age: Age at recruitment (years)
        sex: Biological sex (0=Female, 1=Male in UK Biobank)
        bmi: Body Mass Index (kg/m^2)
        age_at_assessment: Age when cognitive assessment was performed
        education_years: Years of formal education
        smoking_status: Current smoking status (0=Never, 1=Previous, 2=Current)
        alcohol_frequency: Frequency of alcohol consumption
        physical_activity: Physical activity level (METs or categorical)
        diet_score: Diet quality score (e.g., Mediterranean Diet Score)
        medication_count: Number of current medications
        antibiotic_use_3mo: Antibiotic use in last 3 months (True/False)
        antibiotic_use_6mo: Antibiotic use in last 6 months (True/False)
        chronic_conditions: List of chronic conditions (ICD-10 codes)
        assessment_center: UK Biobank assessment center ID
        cohort_entry_date: Date of cohort entry
        data_collection_wave: Wave of data collection (if applicable)
    """
    participant_id: str
    age: Optional[float] = None
    sex: Optional[int] = None
    bmi: Optional[float] = None
    age_at_assessment: Optional[float] = None
    education_years: Optional[float] = None
    smoking_status: Optional[int] = None
    alcohol_frequency: Optional[int] = None
    physical_activity: Optional[float] = None
    diet_score: Optional[float] = None
    medication_count: Optional[int] = None
    antibiotic_use_3mo: Optional[bool] = None
    antibiotic_use_6mo: Optional[bool] = None
    chronic_conditions: List[str] = field(default_factory=list)
    assessment_center: Optional[int] = None
    cohort_entry_date: Optional[date] = None
    data_collection_wave: Optional[int] = None
    
    # Computed fields
    age_group: Optional[str] = None  # Derived from age (e.g., "Young", "Middle", "Old")
    
    def __post_init__(self):
        """Validate and compute derived fields after initialization."""
        if self.age is not None:
            self.age_group = self._compute_age_group(self.age)
        
        # Validate sex coding (UK Biobank: 0=Female, 1=Male)
        if self.sex is not None and self.sex not in [0, 1]:
            raise ValueError(f"Invalid sex value: {self.sex}. Must be 0 (Female) or 1 (Male).")
    
    @staticmethod
    def _compute_age_group(age: float) -> str:
        """
        Compute age group category based on configurable cutoffs.
        
        Args:
            age: Age in years
            
        Returns:
            Category string: "Young" (<50), "Middle" (50-65), "Old" (>=65)
        """
        if age < 50:
            return "Young"
        elif age < 65:
            return "Middle"
        else:
            return "Old"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert participant to dictionary representation."""
        return {
            'participant_id': self.participant_id,
            'age': self.age,
            'sex': self.sex,
            'bmi': self.bmi,
            'age_at_assessment': self.age_at_assessment,
            'education_years': self.education_years,
            'smoking_status': self.smoking_status,
            'alcohol_frequency': self.alcohol_frequency,
            'physical_activity': self.physical_activity,
            'diet_score': self.diet_score,
            'medication_count': self.medication_count,
            'antibiotic_use_3mo': self.antibiotic_use_3mo,
            'antibiotic_use_6mo': self.antibiotic_use_6mo,
            'chronic_conditions': self.chronic_conditions,
            'assessment_center': self.assessment_center,
            'cohort_entry_date': self.cohort_entry_date.isoformat() if self.cohort_entry_date else None,
            'data_collection_wave': self.data_collection_wave,
            'age_group': self.age_group
        }
    
    @classmethod
    def from_row(cls, row: pd.Series) -> 'Participant':
        """
        Create a Participant instance from a pandas Series row.
        
        Args:
            row: pandas Series containing participant data with expected column names
            
        Returns:
            Participant instance
        """
        return cls(
            participant_id=str(row.get('participant_id', row.get('eid', ''))),
            age=row.get('age', None),
            sex=int(row.get('sex', None)) if pd.notna(row.get('sex', None)) else None,
            bmi=row.get('bmi', None),
            age_at_assessment=row.get('age_at_assessment', None),
            education_years=row.get('education_years', None),
            smoking_status=int(row.get('smoking_status', None)) if pd.notna(row.get('smoking_status', None)) else None,
            alcohol_frequency=int(row.get('alcohol_frequency', None)) if pd.notna(row.get('alcohol_frequency', None)) else None,
            physical_activity=row.get('physical_activity', None),
            diet_score=row.get('diet_score', None),
            medication_count=int(row.get('medication_count', None)) if pd.notna(row.get('medication_count', None)) else None,
            antibiotic_use_3mo=bool(row.get('antibiotic_use_3mo', False)),
            antibiotic_use_6mo=bool(row.get('antibiotic_use_6mo', False)),
            chronic_conditions=list(row.get('chronic_conditions', [])),
            assessment_center=int(row.get('assessment_center', None)) if pd.notna(row.get('assessment_center', None)) else None,
            age_group=row.get('age_group', None)
        )
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> List['Participant']:
        """
        Create a list of Participant instances from a DataFrame.
        
        Args:
            df: DataFrame with participant data
            
        Returns:
            List of Participant instances
        """
        return [cls.from_row(row) for _, row in df.iterrows()]

def create_participant_dataframe(participants: List[Participant]) -> pd.DataFrame:
    """
    Convert a list of Participant instances to a DataFrame.
    
    Args:
        participants: List of Participant instances
        
    Returns:
        DataFrame with participant data
    """
    data = [p.to_dict() for p in participants]
    return pd.DataFrame(data)
