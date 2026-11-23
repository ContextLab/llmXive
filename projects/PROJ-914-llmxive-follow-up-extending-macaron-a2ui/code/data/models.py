from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json
import uuid

@dataclass
class InteractionTurn:
    """Represents a single user-agent interaction turn."""
    query: str
    ground_truth_intent: str
    complexity_score: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "ground_truth_intent": self.ground_truth_intent,
            "complexity_score": self.complexity_score
        }

@dataclass
class RoutingDecision:
    """Represents the output of the router."""
    label: str  # "High-Confidence" or "Ambiguous"
    confidence: float
    router_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "confidence": self.confidence,
            "router_id": self.router_id,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class SimulationRun:
    """Represents a single simulation run result."""
    id: str
    query: str
    ground_truth: str
    router_label: str
    router_confidence: float
    latency_injected_ms: int
    gen_time_ms: int
    total_time_ms: float
    patience_threshold_ms: float
    abandoned: bool
    ui_element_count: int
    alignment_score: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "ground_truth": self.ground_truth,
            "router_label": self.router_label,
            "router_confidence": self.router_confidence,
            "latency_injected_ms": self.latency_injected_ms,
            "gen_time_ms": self.gen_time_ms,
            "total_time_ms": self.total_time_ms,
            "patience_threshold_ms": self.patience_threshold_ms,
            "abandoned": self.abandoned,
            "ui_element_count": self.ui_element_count,
            "alignment_score": self.alignment_score,
            "timestamp": self.timestamp.isoformat()
        }
