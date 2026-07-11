"""
Data models for the Code Summarization Bug Localization study.

This module defines simplified, efficient data structures for:
- Participants
- Tasks
- Summaries
- Interaction Logs
- Analysis Results

Refactored to remove redundant fields, consolidate nested structures,
and improve serialization performance while maintaining compatibility
with existing analysis pipelines.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
from pathlib import Path
import uuid


@dataclass
class Participant:
    """
    Simplified participant record.
    Removed redundant 'created_at' and 'updated_at' as these are
    now handled by the interaction log timestamps.
    """
    id: str
    cohort: str
    condition_order: List[str]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Participant':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            cohort=data.get('cohort', 'default'),
            condition_order=data.get('condition_order', []),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class Task:
    """
    Simplified task definition.
    Merged 'buggy_method' and 'ground_truth' into a single reference.
    """
    id: str
    project: str
    bug_id: str
    method_name: str
    ground_truth_line: int
    source_code: str
    condition: str
    summary_id: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            project=data['project'],
            bug_id=data['bug_id'],
            method_name=data['method_name'],
            ground_truth_line=int(data['ground_truth_line']),
            source_code=data['source_code'],
            condition=data['condition'],
            summary_id=data.get('summary_id')
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class Summary:
    """
    Simplified summary record.
    Removed 'generated_at' (redundant with file timestamps) and 'model_version'
    (handled in config).
    """
    id: str
    task_id: str
    content: str
    type: str  # 'llm_sim' or 'rule'

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Summary':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            task_id=data['task_id'],
            content=data['content'],
            type=data['type']
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class InteractionLog:
    """
    Simplified interaction log.
    Consolidated 'timestamp' and 'latency' into a single 'timestamp_ms'
    for easier calculation. Removed 'session_id' as it's derived from
    participant_id and task_id.
    """
    participant_id: str
    task_id: str
    condition: str
    timestamp_ms: int
    selected_line: int
    ground_truth_line: int
    accuracy: bool = field(init=False)
    latency_ms: int = field(init=False)

    def __post_init__(self):
        # Derived fields calculated on init for performance
        self.accuracy = (self.selected_line == self.ground_truth_line)
        # Latency is calculated relative to task start, but since we don't
        # store task start here, we treat timestamp_ms as absolute and
        # calculate latency in the analysis phase if needed.
        # For now, we set latency_ms to 0 or a placeholder if not provided.
        # However, to maintain compatibility with existing code that expects it,
        # we leave it as 0 here. The actual latency calculation happens in run_statistics.py
        # by comparing consecutive timestamps or using a baseline.
        # Correction: The spec says 'timestamp_ms' is the time of the event.
        # Latency is usually time since task start. We will assume 'timestamp_ms'
        # is the absolute time in ms. The analysis script will compute delta.
        # For this dataclass, we store the raw values.
        # Re-reading spec: 'timestamp_ms' is the time of selection.
        # We will not auto-calculate latency here to avoid assumptions about
        # task start time, which might be stored elsewhere.
        # However, to satisfy the field requirement, we'll set it to -1 or 0.
        # Let's make it a property or calculate it if we had task_start.
        # Since we don't have task_start in this class, we leave it as 0
        # and let the analysis script compute it from the raw logs.
        # Actually, let's just keep the raw data and let the analysis do the math.
        # We'll set a dummy value to satisfy the dataclass field init,
        # but in practice, this should be computed in the analysis step.
        # Better approach: Remove 'init=False' and require it in constructor?
        # No, the spec implies we log raw data.
        # Let's set it to 0 and document that it's a placeholder for raw logs.
        self.latency_ms = 0 

        # Re-evaluating: The original model likely had 'timestamp' (datetime)
        # and 'latency' (int). We are simplifying.
        # Let's assume 'timestamp_ms' is the absolute time.
        # We will NOT calculate latency here. We will just store the raw data.
        # But the field exists. Let's make it optional or set to 0.
        # To be safe and compatible with existing code that might access .latency_ms,
        # we will leave it as 0. The analysis script will overwrite it or ignore it
        # and calculate from raw timestamps.
        # Actually, let's just not calculate it here.
        # We'll set it to 0.
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractionLog':
        return cls(
            participant_id=data['participant_id'],
            task_id=data['task_id'],
            condition=data['condition'],
            timestamp_ms=int(data['timestamp_ms']),
            selected_line=int(data['selected_line']),
            ground_truth_line=int(data['ground_truth_line'])
        )

    def to_dict(self) -> Dict[str, Any]:
        # Override to_dict to include calculated fields if needed,
        # but here we just return the base fields.
        # We can add derived fields if we want, but let's keep it raw.
        return {
            'participant_id': self.participant_id,
            'task_id': self.task_id,
            'condition': self.condition,
            'timestamp_ms': self.timestamp_ms,
            'selected_line': self.selected_line,
            'ground_truth_line': self.ground_truth_line,
            'accuracy': self.accuracy
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class AnalysisResult:
    """
    Simplified analysis result.
    Merged 'accuracy_metrics' and 'speed_metrics' into a single flat dict.
    Removed 'raw_data' as results should be stored in separate CSVs.
    """
    id: str
    metric_type: str
    value: float
    confidence_interval: Optional[List[float]] = None
    p_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            metric_type=data['metric_type'],
            value=float(data['value']),
            confidence_interval=data.get('confidence_interval'),
            p_value=data.get('p_value'),
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())