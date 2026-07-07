"""
Data model for Differential Gene Expression (DGE) Results.

This module defines the schema for DGEResult, representing the
output of statistical tests comparing gene expression between conditions.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class DGEResult:
    """
    Represents a single row of differential expression analysis results.

    Attributes:
        gene_id (str): Identifier for the gene.
        log2_fold_change (float): Log2 fold change between conditions.
        base_mean (float): Mean of normalized counts across all samples.
        p_value (float): Raw p-value from the statistical test.
        p_adjust (float): Adjusted p-value (e.g., Benjamini-Hochberg FDR).
        stat (Optional[float]): Test statistic (e.g., Wald statistic).
        metadata (Optional[Dict[str, Any]]): Additional annotation.
    """
    gene_id: str
    log2_fold_change: float
    base_mean: float
    p_value: float
    p_adjust: float
    stat: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def is_significant(self) -> bool:
        """Returns True if FDR (p_adjust) is below 0.05."""
        return self.p_adjust < 0.05

    @property
    def direction(self) -> str:
        """Returns 'up', 'down', or 'neutral' based on log2FC."""
        if self.log2_fold_change > 0.5:
            return "up"
        elif self.log2_fold_change < -0.5:
            return "down"
        return "neutral"

    def to_dict(self) -> Dict[str, Any]:
        """Converts the result to a dictionary."""
        return {
            "gene_id": self.gene_id,
            "log2_fold_change": self.log2_fold_change,
            "base_mean": self.base_mean,
            "p_value": self.p_value,
            "p_adjust": self.p_adjust,
            "stat": self.stat,
            "is_significant": self.is_significant,
            "direction": self.direction
        }
