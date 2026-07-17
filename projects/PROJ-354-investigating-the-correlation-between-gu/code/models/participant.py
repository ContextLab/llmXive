"""
Participant entity definition.
Represents a single individual in the UK Biobank cohort.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date
import pandas as pd
import numpy as np

@dataclass
class Participant:
    """
    Represents a study participant with demographic and cohort metadata.
    
    Attributes:
        participant_id: Unique UK Biobank identifier.
        sex: Sex at birth (0: Female, 1: Male).
        age: Age at assessment (years).
        age_at_baseline: Age at study baseline.
        bmi: Body Mass Index (kg/m^2).
        ethnicity: Self-reported ethnicity.
        assessment_center: ID of the assessment center.
        recruitment_date: Date of recruitment.
        antibiotic_use: List of recent antibiotic usage records (if any).
        age_group: Categorical age group (e.g., 'Young', 'Middle', 'Old').
        metadata: Additional raw metadata fields.
    """
    participant_id: int
    sex: Optional[int] = None
    age: Optional[float] = None
    age_at_baseline: Optional[float] = None
    bmi: Optional[float] = None
    ethnicity: Optional[str] = None
    assessment_center: Optional[int] = None
    recruitment_date: Optional[date] = None
    antibiotic_use: List[Dict[str, Any]] = field(default_factory=list)
    age_group: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: pd.Series) -> "Participant":
        """
        Create a Participant instance from a pandas Series row.
        Handles type coercion and missing values.
        """
        # Map UK Biobank field codes to attributes if necessary
        # Assuming row keys are already mapped or raw field IDs
        participant = cls(
            participant_id=int(row.get("eid") or row.get("participant_id", 0)),
            sex=int(row.get("sex")) if pd.notna(row.get("sex")) else None,
            age=float(row.get("age")) if pd.notna(row.get("age")) else None,
            bmi=float(row.get("bmi")) if pd.notna(row.get("bmi")) else None,
            ethnicity=str(row.get("ethnicity")) if pd.notna(row.get("ethnicity")) else None,
            assessment_center=int(row.get("assessment_center")) if pd.notna(row.get("assessment_center")) else None,
            age_group=str(row.get("age_group")) if pd.notna(row.get("age_group")) else None,
        )
        
        # Store raw row data in metadata for traceability
        participant.metadata = row.to_dict()
        
        return participant

    def to_dict(self) -> Dict[str, Any]:
        """Convert the participant to a dictionary."""
        return {
            "participant_id": self.participant_id,
            "sex": self.sex,
            "age": self.age,
            "age_at_baseline": self.age_at_baseline,
            "bmi": self.bmi,
            "ethnicity": self.ethnicity,
            "assessment_center": self.assessment_center,
            "age_group": self.age_group,
            "antibiotic_use": self.antibiotic_use,
        }

    def is_valid(self) -> bool:
        """
        Check if the participant has essential fields populated.
        """
        return self.participant_id is not None and self.participant_id > 0
