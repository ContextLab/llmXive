from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import pandas as pd

class DesignType(str, Enum):
    """Enumeration of experimental design types."""
    WITHIN_SUBJECTS = "Within-Subjects"
    BETWEEN_SUBJECTS = "Between-Subjects"
    UNKNOWN = "Unknown"

@dataclass
class Dataset:
    """Represents a dataset entity."""
    url: str
    status: str
    checksum: Optional[str] = None
    design_type: Optional[DesignType] = None
    size_gb: Optional[float] = None

@dataclass
class PreprocessedRecord:
    """Represents a preprocessed data record."""
    participant_id: str
    condition: str
    reaction_time: float
    mood: float
    design_type: DesignType
    outlier_flag: bool = False

@dataclass
class AnalysisResult:
    """Represents the result of a statistical analysis."""
    test_type: str
    statistic: float
    p_value: float
    p_fdr: float
    effect_size: Optional[float] = None
    design_type: Optional[DesignType] = None
    confidence_interval: Optional[tuple] = None
    convergence_warning: bool = False
