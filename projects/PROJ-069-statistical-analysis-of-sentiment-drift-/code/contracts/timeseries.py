"""
Schema definition for TimeSeries data.
Represents a single time-series variable (e.g., GDP, Sentiment) with timestamps and values.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class TimeSeries(BaseModel):
    """
    Represents a time-series data point or a collection of points.
    
    Attributes:
        variable_name: The name of the variable (e.g., 'GDP', 'Sentiment_Index')
        source: Origin of the data (e.g., 'FRED', 'GDELT')
        frequency: Frequency of the data (e.g., 'monthly', 'quarterly')
        unit: Unit of measurement (e.g., 'percent', 'index', 'billions')
        data: List of dictionaries containing 'date' and 'value'
        metadata: Additional key-value pairs for provenance
    """
    variable_name: str = Field(..., description="Name of the time series variable")
    source: str = Field(..., description="Data source identifier")
    frequency: str = Field(..., description="Data frequency (e.g., monthly, quarterly)")
    unit: str = Field(..., description="Unit of measurement")
    data: List[Dict[str, Any]] = Field(..., description="List of {date, value} dicts")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('data')
    @classmethod
    def validate_data_structure(cls, v):
        if not isinstance(v, list):
            raise ValueError("Data must be a list of dictionaries")
        if len(v) == 0:
            raise ValueError("Data list cannot be empty")
        
        for item in v:
            if not isinstance(item, dict):
                raise ValueError("Each data point must be a dictionary")
            if 'date' not in item or 'value' not in item:
                raise ValueError("Each data point must contain 'date' and 'value' keys")
        
        return v

    def get_dates(self) -> List[str]:
        """Extract list of date strings."""
        return [item['date'] for item in self.data]

    def get_values(self) -> List[float]:
        """Extract list of numeric values."""
        return [item['value'] for item in self.data]
