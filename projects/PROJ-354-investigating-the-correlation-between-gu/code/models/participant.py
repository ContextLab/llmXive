"""
Participant entity definition.

Represents a study participant with demographic and baseline health information.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date
import pandas as pd
import numpy as np


@dataclass
class Participant:
    """
    Represents a single participant in the UK Biobank study.

    Attributes:
        participant_id: Unique identifier for the participant.
        sex: Sex of the participant (0: Female, 1: Male).
        age: Age at recruitment (years).
        bmi: Body Mass Index at baseline.
        ethnicity: Self-reported ethnicity.
        education_level: Education level (categorical).
        recruitment_center: ID of the recruitment assessment center.
        assessment_date: Date of the baseline assessment.
        antibiotic_history: List of recent antibiotic usage codes (if available).
        medication_history: List of current medication codes.
        diet_score: Dietary quality score if available.
        activity_level: Physical activity level (categorical or continuous).
    """
    participant_id: int
    sex: Optional[int] = None
    age: Optional[float] = None
    bmi: Optional[float] = None
    ethnicity: Optional[str] = None
    education_level: Optional[str] = None
    recruitment_center: Optional[int] = None
    assessment_date: Optional[date] = None
    antibiotic_history: List[str] = field(default_factory=list)
    medication_history: List[str] = field(default_factory=list)
    diet_score: Optional[float] = None
    activity_level: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the participant instance to a dictionary."""
        return {
            "participant_id": self.participant_id,
            "sex": self.sex,
            "age": self.age,
            "bmi": self.bmi,
            "ethnicity": self.ethnicity,
            "education_level": self.education_level,
            "recruitment_center": self.recruitment_center,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
            "antibiotic_history": self.antibiotic_history,
            "medication_history": self.medication_history,
            "diet_score": self.diet_score,
            "activity_level": self.activity_level,
        }


def create_participant_dataframe(participants: List[Participant]) -> pd.DataFrame:
    """
    Convert a list of Participant objects into a pandas DataFrame.

    Args:
        participants: List of Participant instances.

    Returns:
        A pandas DataFrame with participant attributes as columns.
    """
    if not participants:
        return pd.DataFrame()

    data = [p.to_dict() for p in participants]
    df = pd.DataFrame(data)

    # Ensure consistent column types where possible
    # Convert date strings back to datetime if needed for analysis, or keep as string
    if "assessment_date" in df.columns:
        df["assessment_date"] = pd.to_datetime(df["assessment_date"], errors="coerce")

    return df
