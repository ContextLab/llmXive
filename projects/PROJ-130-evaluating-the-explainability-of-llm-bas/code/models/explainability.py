"""
Explainability module defining the ExplainabilityScore entity.

This entity captures the multi-faceted explainability metrics for a bug fix:
- attention_score: Aggregated attention weight magnitude (float).
- saliency_score: Integrated Gradients saliency magnitude (float).
- coherence_score: Semantic similarity of rationale to code change (float or None).
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExplainabilityScore:
    """
    Represents the explainability metrics for a specific bug fix.

    Attributes:
        bug_id (str): Unique identifier for the bug (matches Defects4J ID).
        attention_score (float): Aggregated attention weight score (e.g., mean/max of last layer).
        saliency_score (float): Aggregated saliency score from Integrated Gradients.
        coherence_score (Optional[float]): Cosine similarity between rationale text and code semantics.
                                           None if rationale is missing or coherence could not be computed.
    """
    bug_id: str
    attention_score: float
    saliency_score: float
    coherence_score: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert the entity to a dictionary for serialization."""
        return {
            "bug_id": self.bug_id,
            "attention_score": self.attention_score,
            "saliency_score": self.saliency_score,
            "coherence_score": self.coherence_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExplainabilityScore":
        """Create an instance from a dictionary."""
        return cls(
            bug_id=data["bug_id"],
            attention_score=data["attention_score"],
            saliency_score=data["saliency_score"],
            coherence_score=data.get("coherence_score"),
        )