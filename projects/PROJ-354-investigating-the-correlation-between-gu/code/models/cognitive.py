"""
CognitiveScore entity definition.

Represents cognitive assessment results for a participant.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import date
import pandas as pd


@dataclass
class CognitiveScore:
    """
    Represents cognitive assessment results for a single participant.
    
    Attributes:
        participant_id: Link to the associated Participant.
        assessment_date: Date of cognitive assessment.
        fluid_intelligence_score: Fluid intelligence score (UK Biobank field 20016).
        reaction_time_ms: Reaction time in milliseconds (field 20023).
        pairs_matching_accuracy: Accuracy in pairs matching task (field 20026).
        numeric_memory_score: Numeric memory score (field 20018).
        prospective_memory_score: Prospective memory score (field 20002).
        trail_making_b: Trail making test part B time (field 20202).
        trail_making_a: Trail making test part A time (field 20201).
        symbol_digit_substitution: Symbol digit substitution score (field 20102).
        metadata: Additional assessment metadata.
    """
    participant_id: int
    assessment_date: Optional[str] = None
    fluid_intelligence_score: Optional[float] = None
    reaction_time_ms: Optional[float] = None
    pairs_matching_accuracy: Optional[float] = None
    numeric_memory_score: Optional[float] = None
    prospective_memory_score: Optional[float] = None
    trail_making_b: Optional[float] = None
    trail_making_a: Optional[float] = None
    symbol_digit_substitution: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary representation."""
        return {
            "participant_id": self.participant_id,
            "assessment_date": self.assessment_date,
            "fluid_intelligence_score": self.fluid_intelligence_score,
            "reaction_time_ms": self.reaction_time_ms,
            "pairs_matching_accuracy": self.pairs_matching_accuracy,
            "numeric_memory_score": self.numeric_memory_score,
            "prospective_memory_score": self.prospective_memory_score,
            "trail_making_b": self.trail_making_b,
            "trail_making_a": self.trail_making_a,
            "symbol_digit_substitution": self.symbol_digit_substitution,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_row(cls, row: pd.Series) -> "CognitiveScore":
        """
        Create a CognitiveScore from a pandas Series row.
        
        Args:
            row: A pandas Series containing cognitive assessment data.
                
        Returns:
            A CognitiveScore instance.
        """
        return cls(
            participant_id=int(row["participant_id"]),
            assessment_date=str(row["assessment_date"]) if pd.notna(row.get("assessment_date")) and row["assessment_date"] != "" else None,
            fluid_intelligence_score=float(row["fluid_intelligence_score"]) if pd.notna(row.get("fluid_intelligence_score")) else None,
            reaction_time_ms=float(row["reaction_time_ms"]) if pd.notna(row.get("reaction_time_ms")) else None,
            pairs_matching_accuracy=float(row["pairs_matching_accuracy"]) if pd.notna(row.get("pairs_matching_accuracy")) else None,
            numeric_memory_score=float(row["numeric_memory_score"]) if pd.notna(row.get("numeric_memory_score")) else None,
            prospective_memory_score=float(row["prospective_memory_score"]) if pd.notna(row.get("prospective_memory_score")) else None,
            trail_making_b=float(row["trail_making_b"]) if pd.notna(row.get("trail_making_b")) else None,
            trail_making_a=float(row["trail_making_a"]) if pd.notna(row.get("trail_making_a")) else None,
            symbol_digit_substitution=float(row["symbol_digit_substitution"]) if pd.notna(row.get("symbol_digit_substitution")) else None,
            metadata={}
        )
    
    def get_primary_score(self) -> Optional[float]:
        """
        Get the primary cognitive score for analysis.
        
        Currently defaults to fluid intelligence score as the primary outcome.
        
        Returns:
            The primary score value or None if not available.
        """
        return self.fluid_intelligence_score
    
    def get_all_scores(self) -> Dict[str, Optional[float]]:
        """Return a dictionary of all cognitive scores."""
        return {
            "fluid_intelligence": self.fluid_intelligence_score,
            "reaction_time": self.reaction_time_ms,
            "pairs_matching": self.pairs_matching_accuracy,
            "numeric_memory": self.numeric_memory_score,
            "prospective_memory": self.prospective_memory_score,
            "trail_making_b": self.trail_making_b,
            "trail_making_a": self.trail_making_a,
            "symbol_digit": self.symbol_digit_substitution
        }
    
    def validate(self) -> List[str]:
        """
        Validate cognitive score data integrity.
        
        Returns:
            A list of validation error messages. Empty if valid.
        """
        errors = []
        
        if self.participant_id is None or self.participant_id <= 0:
            errors.append("participant_id must be a positive integer")
        
        # Validate fluid intelligence score range (0-13 in UK Biobank)
        if self.fluid_intelligence_score is not None:
            if self.fluid_intelligence_score < 0 or self.fluid_intelligence_score > 13:
                errors.append(f"Fluid intelligence score out of range: {self.fluid_intelligence_score}")
        
        # Validate reaction time (should be positive)
        if self.reaction_time_ms is not None and self.reaction_time_ms <= 0:
            errors.append(f"Reaction time must be positive: {self.reaction_time_ms}")
        
        return errors
    
    def has_valid_primary_score(self) -> bool:
        """Check if the primary cognitive score is available."""
        return self.get_primary_score() is not None
