"""
CognitiveScore entity definition.

Represents cognitive assessment results for a participant.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import date
import pandas as pd
import numpy as np


@dataclass
class CognitiveScore:
    """
    Represents cognitive assessment data for a participant.

    Attributes:
        participant_id: Link to the participant.
        assessment_date: Date of the cognitive assessment.
        reaction_time: Reaction time in milliseconds (if applicable).
        numeric_memory: Score on numeric memory test.
        pairs_matching: Score on pairs matching test.
        prospective_memory: Score on prospective memory test.
        reasoning: Score on reasoning test.
        verbal_numerical_reasoning: Score on verbal/numerical reasoning.
        composite_score: Calculated composite cognitive score (if available).
        instrument_id: Identifier for the specific cognitive instrument used.
        raw_data: Dictionary of all raw scores collected.
    """
    participant_id: int
    assessment_date: Optional[date] = None
    reaction_time: Optional[float] = None
    numeric_memory: Optional[float] = None
    pairs_matching: Optional[float] = None
    prospective_memory: Optional[float] = None
    reasoning: Optional[float] = None
    verbal_numerical_reasoning: Optional[float] = None
    composite_score: Optional[float] = None
    instrument_id: Optional[str] = None
    raw_data: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the score instance to a dictionary."""
        base = {
            "participant_id": self.participant_id,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
            "reaction_time": self.reaction_time,
            "numeric_memory": self.numeric_memory,
            "pairs_matching": self.pairs_matching,
            "prospective_memory": self.prospective_memory,
            "reasoning": self.reasoning,
            "verbal_numerical_reasoning": self.verbal_numerical_reasoning,
            "composite_score": self.composite_score,
            "instrument_id": self.instrument_id,
        }
        base.update(self.raw_data)
        return base


def create_cognitive_dataframe(scores: List[CognitiveScore]) -> pd.DataFrame:
    """
    Convert a list of CognitiveScore objects into a pandas DataFrame.

    Args:
        scores: List of CognitiveScore instances.

    Returns:
        A pandas DataFrame with cognitive metrics as columns.
    """
    if not scores:
        return pd.DataFrame()

    data = [s.to_dict() for s in scores]
    df = pd.DataFrame(data)

    # Convert assessment_date to datetime
    if "assessment_date" in df.columns:
        df["assessment_date"] = pd.to_datetime(df["assessment_date"], errors="coerce")

    return df


def compute_composite_score(df: pd.DataFrame) -> pd.Series:
    """
    Compute a composite cognitive score from available metrics.
    This is a simple example; the actual formula should be defined in the spec.

    Args:
        df: DataFrame containing cognitive metrics.

    Returns:
        A Series of composite scores (normalized to mean 0, std 1).
    """
    # Example metrics to include (adjust based on actual data availability)
    metrics = ["numeric_memory", "pairs_matching", "prospective_memory", "reasoning"]
    available_metrics = [m for m in metrics if m in df.columns]

    if not available_metrics:
        return pd.Series(dtype=float)

    # Normalize each metric (z-score)
    normalized = df[available_metrics].apply(lambda x: (x - x.mean()) / x.std(), axis=0)
    # Average the normalized scores
    composite = normalized.mean(axis=1)

    return composite
