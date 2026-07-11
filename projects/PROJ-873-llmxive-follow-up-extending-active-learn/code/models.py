from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib

@dataclass
class CandidateList:
    query_id: str
    candidates: List[Dict[str, Any]]
    ground_truth: Dict[str, int]
    
    def __post_init__(self):
        # Ensure candidates is a list
        if not isinstance(self.candidates, list):
            self.candidates = list(self.candidates)

@dataclass
class ComparisonPair:
    query_id: str
    doc_a_id: str
    doc_b_id: str
    similarity_score: float
    is_redundant: bool = False
    timestamp: Optional[float] = None
    
    def to_hash(self) -> str:
        """Generate a unique hash for this comparison pair."""
        data = f"{self.query_id}:{self.doc_a_id}:{self.doc_b_id}"
        return hashlib.sha256(data.encode()).hexdigest()