"""
Data model definitions for the project.
Defines core entities: Dataset, PreprocessedRecord, AnalysisResult.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import pandas as pd


class DesignType(Enum):
    """Enumeration of possible experimental design types."""
    WITHIN_SUBJECTS = "Within-Subjects"
    BETWEEN_SUBJECTS = "Between-Subjects"
    UNKNOWN = "Unknown"


@dataclass
class Dataset:
    """
    Represents a raw or loaded dataset.
    """
    source_id: str
    path: str
    design_type: DesignType
    records: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Converts records to a pandas DataFrame."""
        return pd.DataFrame(self.records)


@dataclass
class PreprocessedRecord:
    """
    Represents a single record after preprocessing (cleaning, normalization).
    """
    participant_id: str
    condition: str
    reaction_time: float
    mood_score: float
    is_outlier: bool = False
    normalized_rt: Optional[float] = None


@dataclass
class AnalysisResult:
    """
    Represents the output of a statistical analysis.
    """
    test_name: str
    design_type: DesignType
    statistic: float
    p_value: float
    p_fdr: Optional[float] = None
    effect_size: Optional[float] = None
    confidence_interval: Optional[tuple] = None
    conclusion: str = ""
    limitations: List[str] = field(default_factory=list)
    raw_results: Dict[str, Any] = field(default_factory=dict)