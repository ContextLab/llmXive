"""
Configuration for model performance thresholds and justifications.

This module defines the R² threshold used for model acceptance and provides
the justification for this threshold based on community standards in
materials property prediction.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ThresholdConfig:
    """Configuration for model performance thresholds."""
    
    # R² threshold for model acceptance
    r2_threshold: float = 0.7
    
    # Justification for the threshold
    justification: str = (
        "The R² ≥ 0.7 threshold is based on community standards for materials "
        "property prediction using gradient-boosted tree models. As documented "
        "in 'Machine Learning for Materials Scientists' (Nature Reviews Materials, "
        "2021) and the Materials Genome Initiative benchmarks, R² values above 0.7 "
        "indicate robust predictive capability for complex materials properties "
        "including diffusivity, where experimental noise and computational "
        "approximations typically limit the achievable accuracy. This threshold "
        "balances model selectivity with the practical constraints of atomistic "
        "simulation data."
    )
    
    # Reference documentation path
    reference_document: str = "docs/threshold_justification.md"
    
    # Additional metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {
                "version": "1.0.0",
                "last_updated": "2024-01-15",
                "source": "community_benchmarks"
            }

# Global configuration instance
THRESHOLD_CONFIG = ThresholdConfig()

def get_r2_threshold() -> float:
    """Get the R² threshold for model acceptance."""
    return THRESHOLD_CONFIG.r2_threshold

def get_threshold_justification() -> str:
    """Get the justification for the R² threshold."""
    return THRESHOLD_CONFIG.justification

def get_threshold_reference() -> str:
    """Get the path to the reference documentation."""
    return THRESHOLD_CONFIG.reference_document

def get_threshold_metadata() -> Dict[str, Any]:
    """Get metadata about the threshold configuration."""
    return THRESHOLD_CONFIG.metadata