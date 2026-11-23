from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json


class MetricRecordSchema(BaseModel):
    """Pydantic schema for a single metric record (e.g., SSIM, Memory, Latency)."""
    record_id: str = Field(..., description="Unique identifier for the record")
    clip_id: str = Field(..., description="Reference to the video clip")
    metric_type: str = Field(..., description="Type of metric (e.g., 'ssim', 'memory_peak', 'latency')")
    value: float = Field(..., description="The metric value")
    unit: str = Field(default="unitless", description="Unit of measurement")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of measurement")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context (e.g., flow magnitude, invalid flags)")

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Value must be numeric")
        return float(v)


class MetricSchema(BaseModel):
    """Pydantic schema for a collection of metric records."""
    experiment_id: str = Field(..., description="Reference to the experiment")
    model_name: str = Field(..., description="Name of the model used (e.g., 'baseline', 'flow_coherence')")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    records: List[MetricRecordSchema] = Field(..., description="List of metric records")
    total_records: int = Field(..., description="Total number of records")

    @field_validator('total_records')
    @classmethod
    def validate_total_records(cls, v, info):
        records = info.data.get('records', [])
        if v != len(records):
            raise ValueError(f"total_records ({v}) must match number of records ({len(records)})")
        return v


class MetricValidator:
    """
    Validator class to enforce MetricSchema constraints and validate JSON records.
    """
    @staticmethod
    def validate_from_json(json_str: str) -> MetricSchema:
        """
        Validates a JSON string against MetricSchema.
        Raises pydantic.ValidationError on mismatch.
        """
        data = json.loads(json_str)
        return MetricSchema(**data)

    @staticmethod
    def validate_from_dict(data: Dict[str, Any]) -> MetricSchema:
        """
        Validates a dictionary against MetricSchema.
        """
        return MetricSchema(**data)

    @staticmethod
    def validate_record_from_json(json_str: str) -> MetricRecordSchema:
        """
        Validates a JSON string against MetricRecordSchema.
        """
        data = json.loads(json_str)
        return MetricRecordSchema(**data)

    @staticmethod
    def validate_record_from_dict(data: Dict[str, Any]) -> MetricRecordSchema:
        """
        Validates a dictionary against MetricRecordSchema.
        """
        return MetricRecordSchema(**data)
