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
    Represents cognitive assessment scores for a participant.
    
    Attributes:
        participant_id: Link to the Participant entity.
        assessment_date: Date of the cognitive assessment.
        reaction_time: Reaction time in seconds (Field 20023).
        pairs_matching: Pairs matching score (Field 20024).
        numeric_memory: Numeric memory score (Field 20025).
        reasoning: Reasoning score (Field 20026).
        fluid_intelligence: Fluid intelligence score (Field 20027).
        composite_score: Composite cognitive score (calculated).
        assessment_type: Type of assessment (e.g., 'Touchscreen', 'Interview').
        metadata: Raw assessment data.
    """
    participant_id: int
    assessment_date: Optional[date] = None
    reaction_time: Optional[float] = None
    pairs_matching: Optional[float] = None
    numeric_memory: Optional[float] = None
    reasoning: Optional[float] = None
    fluid_intelligence: Optional[float] = None
    composite_score: Optional[float] = None
    assessment_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: pd.Series) -> "CognitiveScore":
        """
        Create a CognitiveScore from a pandas Series row.
        """
        participant_id = int(row.get("eid") or row.get("participant_id", 0))
        
        # Helper to safely convert
        def safe_float(val):
            if pd.isna(val):
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        score = cls(
            participant_id=participant_id,
            reaction_time=safe_float(row.get("reaction_time")),
            pairs_matching=safe_float(row.get("pairs_matching")),
            numeric_memory=safe_float(row.get("numeric_memory")),
            reasoning=safe_float(row.get("reasoning")),
            fluid_intelligence=safe_float(row.get("fluid_intelligence")),
            assessment_type=str(row.get("assessment_type")) if pd.notna(row.get("assessment_type")) else None,
        )
        
        # Calculate composite if multiple scores exist
        scores = [v for v in [
            score.reaction_time, score.pairs_matching, 
            score.numeric_memory, score.reasoning, score.fluid_intelligence
        ] if v is not None]
        
        if scores:
            # Normalize logic would go here; for now simple average
            # Note: Reaction time is inverse (lower is better), others usually higher is better.
            # This is a placeholder for the actual normalization logic defined in spec.
            score.composite_score = np.mean(scores)

        score.metadata = row.to_dict()
        return score

    def to_dict(self) -> Dict[str, Any]:
        """Convert the score to a dictionary."""
        return {
            "participant_id": self.participant_id,
            "assessment_date": str(self.assessment_date) if self.assessment_date else None,
            "reaction_time": self.reaction_time,
            "pairs_matching": self.pairs_matching,
            "numeric_memory": self.numeric_memory,
            "reasoning": self.reasoning,
            "fluid_intelligence": self.fluid_intelligence,
            "composite_score": self.composite_score,
            "assessment_type": self.assessment_type,
        }

    def is_valid(self) -> bool:
        """Check if at least one cognitive score is present."""
        return (
            self.reaction_time is not None or
            self.pairs_matching is not None or
            self.numeric_memory is not None or
            self.reasoning is not None or
            self.fluid_intelligence is not None
        )
