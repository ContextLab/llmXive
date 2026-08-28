"""
Core data models for the llmXive pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class MetricRecord:
    step: int
    coherence_score: float
    diversity_score: float
    step_latency: float
    physics_violations: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SimulationRun:
    status: str
    config: Dict[str, Any]
    metrics: List[MetricRecord]
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    error: Optional[str] = None

@dataclass
class ParameterGrid:
    name: str
    parameters: Dict[str, List[Any]]
    description: Optional[str] = None
