"""
Base data models (T007).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

@dataclass
class PromptItem:
    prompt_id: str
    raw_text: str
    features: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelResponse:
    prompt_id: str
    response_text: str
    adherence_label: int
    safety_refusal: bool

@dataclass
class AnalysisResult:
    model_name: str
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
