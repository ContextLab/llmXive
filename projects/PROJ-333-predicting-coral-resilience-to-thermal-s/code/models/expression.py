from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from pathlib import Path

@dataclass
class ExpressionMatrix:
    """
    Represents a gene expression matrix with samples as columns and genes as rows.
    
    Attributes:
        counts (pd.DataFrame): Raw count matrix (genes x samples)
        metadata (Dict[str, Any]): Optional sample metadata
    """
    counts: pd.DataFrame
    metadata: Optional[Dict[str, Any]] = None

    def to_csv(self, path: Path) -> None:
        """Saves the count matrix to a CSV file."""
        self.counts.to_csv(path)

    @classmethod
    def from_csv(cls, path: Path) -> 'ExpressionMatrix':
        """Loads an expression matrix from a CSV file."""
        counts = pd.read_csv(path, index_col=0)
        return cls(counts=counts)
