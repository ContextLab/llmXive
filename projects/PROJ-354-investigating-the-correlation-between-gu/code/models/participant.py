"""
Participant entity definition.

Represents a study subject with demographic and clinical characteristics.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date
import pandas as pd


@dataclass
class Participant:
    """
    Represents a single participant in the study.
    
    Attributes:
        participant_id: Unique identifier for the participant (UK Biobank ID).
        age: Age at recruitment or assessment (years).
        sex: Biological sex (0: Female, 1: Male in UK Biobank).
        bmi: Body Mass Index (kg/m^2).
        age_group: Categorical age group derived from age.
        diet_score: Dietary quality score if available.
        activity_level: Physical activity level if available.
        medication_count: Number of medications taken.
        antibiotic_use_recent: Boolean indicating recent antibiotic use.
        ethnicity: Self-reported ethnicity.
        education_level: Education level attained.
        batch_id: Processing batch identifier.
        metadata: Additional arbitrary metadata.
    """
    participant_id: int
    age: Optional[float] = None
    sex: Optional[int] = None
    bmi: Optional[float] = None
    age_group: Optional[str] = None
    diet_score: Optional[float] = None
    activity_level: Optional[float] = None
    medication_count: Optional[int] = None
    antibiotic_use_recent: Optional[bool] = None
    ethnicity: Optional[str] = None
    education_level: Optional[str] = None
    batch_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert participant to dictionary representation."""
        return {
            "participant_id": self.participant_id,
            "age": self.age,
            "sex": self.sex,
            "bmi": self.bmi,
            "age_group": self.age_group,
            "diet_score": self.diet_score,
            "activity_level": self.activity_level,
            "medication_count": self.medication_count,
            "antibiotic_use_recent": self.antibiotic_use_recent,
            "ethnicity": self.ethnicity,
            "education_level": self.education_level,
            "batch_id": self.batch_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_row(cls, row: pd.Series) -> "Participant":
        """
        Create a Participant instance from a pandas Series row.
        
        Args:
            row: A pandas Series containing participant data.
                
        Returns:
            A Participant instance.
        """
        return cls(
            participant_id=int(row["participant_id"]),
            age=float(row["age"]) if pd.notna(row.get("age")) else None,
            sex=int(row["sex"]) if pd.notna(row.get("sex")) else None,
            bmi=float(row["bmi"]) if pd.notna(row.get("bmi")) else None,
            age_group=str(row["age_group"]) if pd.notna(row.get("age_group")) and row["age_group"] != "" else None,
            diet_score=float(row["diet_score"]) if pd.notna(row.get("diet_score")) else None,
            activity_level=float(row["activity_level"]) if pd.notna(row.get("activity_level")) else None,
            medication_count=int(row["medication_count"]) if pd.notna(row.get("medication_count")) else None,
            antibiotic_use_recent=bool(row["antibiotic_use_recent"]) if pd.notna(row.get("antibiotic_use_recent")) else None,
            ethnicity=str(row["ethnicity"]) if pd.notna(row.get("ethnicity")) and row["ethnicity"] != "" else None,
            education_level=str(row["education_level"]) if pd.notna(row.get("education_level")) and row["education_level"] != "" else None,
            batch_id=str(row["batch_id"]) if pd.notna(row.get("batch_id")) and row["batch_id"] != "" else None,
            metadata={}
        )
    
    def validate(self) -> List[str]:
        """
        Validate participant data integrity.
        
        Returns:
            A list of validation error messages. Empty if valid.
        """
        errors = []
        
        if self.participant_id is None or self.participant_id <= 0:
            errors.append("participant_id must be a positive integer")
        
        if self.age is not None and (self.age < 0 or self.age > 120):
            errors.append(f"Invalid age: {self.age}")
        
        if self.sex is not None and self.sex not in [0, 1]:
            errors.append(f"Invalid sex code: {self.sex}. Expected 0 (Female) or 1 (Male)")
        
        if self.bmi is not None and (self.bmi < 10 or self.bmi > 80):
            errors.append(f"Invalid BMI: {self.bmi}")
        
        if self.antibiotic_use_recent is not None and not isinstance(self.antibiotic_use_recent, bool):
            errors.append("antibiotic_use_recent must be boolean")
        
        return errors
