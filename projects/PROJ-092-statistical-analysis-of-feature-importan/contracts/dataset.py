"""
Data schema definitions for the dataset entity.
Defines the structure and validation rules for raw and processed data.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path


class DataSource(Enum):
    """Enum for supported data sources."""
    UCI_ELECTRICITY = "uci_electricity"
    CUSTOM_CSV = "custom_csv"


@dataclass
class DatasetSchema:
    """
    Schema definition for the Electricity Load Diagrams dataset.
    """
    source: DataSource
    raw_path: Path
    processed_path: Path
    columns: List[str]
    target_column: str = "load"
    timestamp_column: str = "timestamp"
    feature_columns: List[str] = field(default_factory=list)
    window_size_days: int = 30
    min_r_squared: float = 0.8
    missing_value_strategy: str = "median"

    def __post_init__(self):
        """Validate schema constraints."""
        if self.target_column not in self.columns:
            raise ValueError(f"Target column '{self.target_column}' not in columns list")
        if self.timestamp_column not in self.columns:
            raise ValueError(f"Timestamp column '{self.timestamp_column}' not in columns list")
        if self.window_size_days <= 0:
            raise ValueError("Window size must be positive")
        if not (0.0 <= self.min_r_squared <= 1.0):
            raise ValueError("min_r_squared must be between 0 and 1")

    def get_feature_list(self) -> List[str]:
        """Return list of feature columns excluding target and timestamp."""
        if self.feature_columns:
            return self.feature_columns
        exclude = {self.target_column, self.timestamp_column}
        return [c for c in self.columns if c not in exclude]


@dataclass
class WindowMetadata:
    """Metadata for a single time window."""
    window_id: int
    start_date: str
    end_date: str
    row_count: int
    missing_count: int
    dropped_zero_variance: List[str]
    r_squared: Optional[float] = None
    model_status: str = "pending"  # pending, success, failure

@dataclass
class ProcessedWindow:
    """Container for a single processed window's data and metadata."""
    metadata: WindowMetadata
    features: Any  # np.ndarray
    target: Any  # np.ndarray
    feature_names: List[str]
