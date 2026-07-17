"""
Base data models/entities for the pipeline.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

@dataclass
class PromptItem:
    prompt_id: str
    text: str
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "text": self.text,
            "label": self.label,
            "metadata": self.metadata
        }

@dataclass
class ModelResponse:
    response_id: str
    prompt_id: str
    model_id: str
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_adherent: Optional[bool] = None
    is_resilient: Optional[bool] = None
    refusal_flag: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "prompt_id": self.prompt_id,
            "model_id": self.model_id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "is_adherent": self.is_adherent,
            "is_resilient": self.is_resilient,
            "refusal_flag": self.refusal_flag,
            "metadata": self.metadata
        }

@dataclass
class AnalysisResult:
    result_id: str
    model_name: str
    metric_name: str
    value: float
    p_value: Optional[float] = None
    confidence_interval: Optional[tuple] = None
    timestamp: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "model_name": self.model_name,
            "metric_name": self.metric_name,
            "value": self.value,
            "p_value": self.p_value,
            "confidence_interval": self.confidence_interval,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes
        }
