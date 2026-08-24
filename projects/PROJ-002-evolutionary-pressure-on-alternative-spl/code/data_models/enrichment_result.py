from dataclasses import dataclass, asdict
from typing import Optional
import json
from datetime import datetime

@dataclass
class EnrichmentResult:
    """
    Represents the result of an enrichment analysis for a specific lineage.
    
    Attributes:
        lineage (str): The name of the evolutionary lineage being tested (e.g., 'Human', 'PanTro6').
        odds_ratio (float): The calculated odds ratio from the phylogenetic logistic regression.
        p_raw (float): The raw p-value from the statistical test.
        p_corrected_phylo (float): The p-value corrected for phylogenetic non-independence.
        p_fdr (float): The Benjamini-Hochberg False Discovery Rate corrected p-value.
        p_empirical (float): The empirical p-value derived from permutation testing.
    """
    lineage: str
    odds_ratio: float
    p_raw: float
    p_corrected_phylo: float
    p_fdr: float
    p_empirical: float

    def to_dict(self) -> dict:
        """Convert the EnrichmentResult instance to a dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert the EnrichmentResult instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> 'EnrichmentResult':
        """Create an EnrichmentResult instance from a dictionary."""
        return cls(
            lineage=data['lineage'],
            odds_ratio=float(data['odds_ratio']),
            p_raw=float(data['p_raw']),
            p_corrected_phylo=float(data['p_corrected_phylo']),
            p_fdr=float(data['p_fdr']),
            p_empirical=float(data['p_empirical'])
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'EnrichmentResult':
        """Create an EnrichmentResult instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __post_init__(self):
        """Validate numeric fields after initialization."""
        if not isinstance(self.lineage, str) or not self.lineage.strip():
            raise ValueError("lineage must be a non-empty string")
        
        numeric_fields = ['odds_ratio', 'p_raw', 'p_corrected_phylo', 'p_fdr', 'p_empirical']
        for field in numeric_fields:
            val = getattr(self, field)
            if not isinstance(val, (int, float)):
                raise TypeError(f"{field} must be numeric, got {type(val)}")
            if field != 'odds_ratio' and not (0.0 <= val <= 1.0):
                raise ValueError(f"{field} must be between 0.0 and 1.0, got {val}")
            if field == 'odds_ratio' and val < 0.0:
                raise ValueError(f"odds_ratio must be non-negative, got {val}")
