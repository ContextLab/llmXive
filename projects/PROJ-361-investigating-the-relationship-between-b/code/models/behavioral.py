from dataclasses import dataclass
from typing import Optional


@dataclass
class IllusionScore:
    """
    Dataclass representing visual illusion susceptibility scores.
    Captures Müller-Lyer and Ponzo illusion magnitudes.
    """
    subject_id: str
    muller_lyer_score: Optional[float] = None
    ponzo_score: Optional[float] = None
    study_id: Optional[str] = None
    trial_count: int = 0
    data_source: Optional[str] = None
    extraction_timestamp: Optional[str] = None
    
    def is_complete(self) -> bool:
        """Check if both illusion scores are present."""
        return (self.muller_lyer_score is not None and 
                self.ponzo_score is not None)

    def average_illusion_score(self) -> Optional[float]:
        """
        Calculate the average susceptibility score across both illusions.
        Returns None if either score is missing.
        """
        if self.is_complete():
            return (self.muller_lyer_score + self.ponzo_score) / 2.0
        return None
