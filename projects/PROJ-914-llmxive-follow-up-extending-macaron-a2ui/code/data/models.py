"""
Data models and entities for the llmXive A2UI latency study.

This module defines the core data structures used throughout the pipeline:
- InteractionTurn: Represents a single turn in a user-agent interaction.
- RoutingDecision: Represents the output of the router (intent classification).
- SimulationRun: Represents a complete simulation execution with metrics.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid


@dataclass
class InteractionTurn:
    """
    Represents a single turn in a user-agent interaction.

    Attributes:
        turn_id: Unique identifier for the turn.
        query: The user's input query.
        intent: The ground truth or predicted intent (e.g., "High-Confidence", "Ambiguous").
        complexity_score: A numeric score representing query complexity (0.0-1.0).
        timestamp: When the interaction occurred.
        metadata: Additional context or raw data fields.
    """
    query: str
    intent: Optional[str] = None
    complexity_score: Optional[float] = None
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the interaction turn to a dictionary."""
        return {
            "turn_id": self.turn_id,
            "query": self.query,
            "intent": self.intent,
            "complexity_score": self.complexity_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InteractionTurn":
        """Create an InteractionTurn from a dictionary."""
        # Handle timestamp parsing
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.utcnow()

        return cls(
            turn_id=data.get("turn_id", str(uuid.uuid4())),
            query=data["query"],
            intent=data.get("intent"),
            complexity_score=data.get("complexity_score"),
            timestamp=ts,
            metadata=data.get("metadata", {})
        )


@dataclass
class RoutingDecision:
    """
    Represents a decision made by the routing model.

    Attributes:
        decision_id: Unique identifier for the decision.
        turn_id: Reference to the InteractionTurn being routed.
        predicted_intent: The intent predicted by the router.
        confidence_score: The model's confidence in the prediction (0.0-1.0).
        fallback_triggered: Whether the fallback generator was invoked.
        fallback_reason: Reason for triggering fallback (if any).
        timestamp: When the decision was made.
    """
    turn_id: str
    predicted_intent: str
    confidence_score: float
    fallback_triggered: bool = False
    fallback_reason: Optional[str] = None
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the routing decision to a dictionary."""
        return {
            "decision_id": self.decision_id,
            "turn_id": self.turn_id,
            "predicted_intent": self.predicted_intent,
            "confidence_score": self.confidence_score,
            "fallback_triggered": self.fallback_triggered,
            "fallback_reason": self.fallback_reason,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SimulationRun:
    """
    Represents a complete simulation run for a set of interaction turns.

    Attributes:
        run_id: Unique identifier for the simulation run.
        turns: List of InteractionTurn objects processed.
        decisions: List of RoutingDecision objects corresponding to turns.
        total_latency_ms: Total simulated latency for the run.
        abandonment_events: Count of user abandonment events.
        metrics: Dictionary of calculated metrics (alignment, UI completeness, etc.).
        start_time: When the simulation started.
        end_time: When the simulation ended.
        config_snapshot: Snapshot of configuration parameters used.
    """
    turns: List[InteractionTurn] = field(default_factory=list)
    decisions: List[RoutingDecision] = field(default_factory=list)
    total_latency_ms: float = 0.0
    abandonment_events: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None

    def add_turn(self, turn: InteractionTurn) -> None:
        """Add an interaction turn to the run."""
        self.turns.append(turn)

    def add_decision(self, decision: RoutingDecision) -> None:
        """Add a routing decision to the run."""
        self.decisions.append(decision)

    def finalize(self) -> None:
        """Finalize the run, setting end time."""
        self.end_time = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the simulation run to a dictionary."""
        return {
            "run_id": self.run_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_turns": len(self.turns),
            "total_latency_ms": self.total_latency_ms,
            "abandonment_events": self.abandonment_events,
            "metrics": self.metrics,
            "config_snapshot": self.config_snapshot,
            "turns": [t.to_dict() for t in self.turns],
            "decisions": [d.to_dict() for d in self.decisions]
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the simulation run to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "SimulationRun":
        """Deserialize a SimulationRun from a JSON string."""
        data = json.loads(json_str)
        run = cls(
            run_id=data["run_id"],
            total_latency_ms=data["total_latency_ms"],
            abandonment_events=data["abandonment_events"],
            metrics=data["metrics"],
            config_snapshot=data["config_snapshot"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data["end_time"] else None
        )
        
        # Reconstruct turns
        for t_data in data["turns"]:
            run.add_turn(InteractionTurn.from_dict(t_data))
        
        # Reconstruct decisions
        for d_data in data["decisions"]:
            decision = RoutingDecision(
                decision_id=d_data["decision_id"],
                turn_id=d_data["turn_id"],
                predicted_intent=d_data["predicted_intent"],
                confidence_score=d_data["confidence_score"],
                fallback_triggered=d_data["fallback_triggered"],
                fallback_reason=d_data["fallback_reason"],
                timestamp=datetime.fromisoformat(d_data["timestamp"])
            )
            run.add_decision(decision)
        
        return run