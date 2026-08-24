from dataclasses import dataclass, asdict
from typing import Optional
import json
from datetime import datetime
from pathlib import Path

@dataclass
class SplicingEvent:
    """
    Represents a lineage-specific alternative splicing event.
    
    Attributes:
        event_id: Unique identifier for the splicing event (e.g., SE_chr1_12345)
        gene_id: Ensembl or gene symbol identifier
        delta_psi: Change in Percent Spliced In (PSI) between lineages
        fdr: False Discovery Rate adjusted p-value
        flank_seq: Flanking intronic sequence (±500 bp) as string
        phyloP_score: Average phyloP conservation score for the flanking region
        accelerated_flag: Boolean indicating if the region shows accelerated evolution (phyloP <= -2.0)
        created_at: Timestamp of object creation
    """
    event_id: str
    gene_id: str
    delta_psi: float
    fdr: float
    flank_seq: str
    phyloP_score: Optional[float]
    accelerated_flag: bool
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Validate phyloP_score and accelerated_flag consistency
        if self.phyloP_score is not None:
            expected_flag = self.phyloP_score <= -2.0
            if self.accelerated_flag != expected_flag:
                # Log warning or raise error depending on strictness requirements
                # For now, we trust the input but could enforce consistency:
                # self.accelerated_flag = expected_flag
                pass

    def to_dict(self) -> dict:
        """Convert the SplicingEvent to a dictionary for serialization."""
        result = asdict(self)
        # Convert datetime to ISO format string for JSON compatibility
        if isinstance(result['created_at'], datetime):
            result['created_at'] = result['created_at'].isoformat()
        return result

    def to_json(self) -> str:
        """Serialize the SplicingEvent to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> 'SplicingEvent':
        """Create a SplicingEvent from a dictionary."""
        # Handle datetime conversion if present
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'SplicingEvent':
        """Create a SplicingEvent from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __eq__(self, other) -> bool:
        if not isinstance(other, SplicingEvent):
            return False
        return (
            self.event_id == other.event_id and
            self.gene_id == other.gene_id and
            abs(self.delta_psi - other.delta_psi) < 1e-6 and
            abs(self.fdr - other.fdr) < 1e-6 and
            self.flank_seq == other.flank_seq and
            (self.phyloP_score is None and other.phyloP_score is None or 
             (self.phyloP_score is not None and other.phyloP_score is not None and 
              abs(self.phyloP_score - other.phyloP_score) < 1e-6)) and
            self.accelerated_flag == other.accelerated_flag
        )

    def __hash__(self) -> int:
        return hash((self.event_id, self.gene_id, self.delta_psi, self.fdr, 
                     self.flank_seq, self.phyloP_score, self.accelerated_flag))
