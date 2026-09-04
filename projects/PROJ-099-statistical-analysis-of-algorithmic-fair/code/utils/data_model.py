from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import hashlib
import json

class DatasetCharacteristic(Enum):
    """Enumeration of dataset characteristics for analysis."""
    BINARY_PROTECTED_ATTRIBUTE = "binary_protected_attribute"
    BINARY_OUTCOME = "binary_outcome"
    HIGH_DIMENSIONAL = "high_dimensional"
    CLASS_IMBALANCE = "class_imbalance"
    SAMPLE_SIZE_LARGE = "sample_size_large"

class FairnessMetric(Enum):
    """Enumeration of fairness metrics supported by the pipeline."""
    DEMOGRAPHIC_PARRY_DIFFERENCE = "demographic_parity_difference"
    EQUALIZED_ODDS_DIFFERENCE = "equalized_odds_difference"
    PREDICTIVE_PARITY = "predictive_parity"
    CALIBRATION_WITHIN_GROUPS = "calibration_within_groups"
    DISPARATE_IMPACT_RATIO = "disparate_impact_ratio"
    FALSE_POSITIVE_RATE_DISPARITY = "false_positive_rate_disparity"

@dataclass
class Model:
    """Data class representing a trained model."""
    model_id: str
    model_type: str
    dataset_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    checksum: Optional[str] = None

@dataclass
class Dataset:
    """Data class representing a dataset in the pipeline."""
    dataset_id: str
    source: str
    path: Optional[str] = None
    characteristics: List[DatasetCharacteristic] = field(default_factory=list)
    checksum: Optional[str] = None
    row_count: int = 0
    column_count: int = 0