"""
Dataset Schema Definitions.

Defines the structure for metadata regarding the source dataset
used in the analysis (UCI Electricity Load Diagrams).
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class DatasetMetadata:
    """
    Schema for dataset source and processing metadata.
    
    Attributes:
        name: Name of the dataset (e.g., 'Electricity Load Diagrams 2011-2014')
        source_url: Original URL or location of the dataset
        version: Version identifier of the dataset
        download_date: ISO format timestamp of when the data was fetched
        file_hash: SHA-256 hash of the downloaded file for verification
        total_rows: Total number of records in the raw dataset
        total_features: Number of features (columns) in the raw dataset
        target_column: Name of the target variable (e.g., 'MWH')
        feature_columns: List of feature column names
        time_column: Name of the timestamp column
        time_frequency: Frequency of the time series (e.g., '15min')
        start_date: ISO format start date of the time series
        end_date: ISO format end date of the time series
        preprocessing_steps: List of applied preprocessing steps (e.g., 'median_imputation')
    """
    name: str
    source_url: str
    version: str = "1.0"
    download_date: Optional[str] = None
    file_hash: Optional[str] = None
    total_rows: Optional[int] = None
    total_features: Optional[int] = None
    target_column: str = "MWH"
    feature_columns: List[str] = field(default_factory=list)
    time_column: str = "timestamp"
    time_frequency: str = "15min"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    preprocessing_steps: List[str] = field(default_factory=lambda: ["median_imputation", "zero_variance_drop"])

    def to_dict(self) -> dict:
        """Convert the dataclass instance to a dictionary."""
        return {
            "name": self.name,
            "source_url": self.source_url,
            "version": self.version,
            "download_date": self.download_date,
            "file_hash": self.file_hash,
            "total_rows": self.total_rows,
            "total_features": self.total_features,
            "target_column": self.target_column,
            "feature_columns": self.feature_columns,
            "time_column": self.time_column,
            "time_frequency": self.time_frequency,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "preprocessing_steps": self.preprocessing_steps
        }
