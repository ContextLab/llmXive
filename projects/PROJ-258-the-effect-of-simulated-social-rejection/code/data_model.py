from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import pandas as pd

class DesignType(Enum):
    """Enumeration of possible experimental designs."""
    WITHIN_SUBJECTS = "Within-Subjects"
    BETWEEN_SUBJECTS = "Between-Subjects"

@dataclass
class Dataset:
    """Represents a raw or processed dataset."""
    source_id: str
    path: str
    design_type: Optional[DesignType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PreprocessedRecord:
    """Represents a single cleaned and feature-extracted record."""
    participant_id: str
    condition: str
    reaction_time: float
    mood_score: float
    is_outlier: bool = False

@dataclass
class AnalysisResult:
    """Represents the output of a statistical analysis."""
    test_type: str
    statistic: float
    p_value: float
    p_fdr: Optional[float] = None
    effect_size: Optional[Dict[str, float]] = None
    design_type: Optional[DesignType] = None
    convergence_warning: Optional[str] = None
    sensitivity_results: Optional[Dict[str, bool]] = None
    raw_data_summary: Optional[Dict[str, Any]] = None