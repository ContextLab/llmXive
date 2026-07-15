"""
Data Models for llmXive.

Defines the core data structures used in the data synthesis pipeline.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class SyntheticVideoFrame:
    """Represents a single frame in a synthetic video."""
    frame_id: str
    timestamp: float
    image_data: np.ndarray  # H, W, C
    ground_truth_label: str
    metadata: Dict[str, Any]

@dataclass
class InternalStateVector:
    """Represents the internal state vector of the JoyAI-VL model."""
    timestamp: float
    frame_id: str
    hidden_states: np.ndarray
    attention_maps: np.ndarray
    metadata: Dict[str, Any]

@dataclass
class SchedulerDecision:
    """Represents a decision made by the scheduler."""
    timestamp: float
    frame_id: str
    intervention_probability: float
    decision: str  # "interrupt", "wait"
    confidence: float
    features_used: List[str]