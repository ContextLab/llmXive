from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from pathlib import Path
import uuid

@dataclass
class Participant:
    """
    Represents a study participant.
    Fields are anonymized; raw consent data is stored separately in data/consent/.
    """
    participant_id: str
    cohort_id: str
    assigned_condition_order: List[str]  # e.g., ['baseline', 'llm_sim', 'rule']
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_dropout: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'participant_id': self.participant_id,
            'cohort_id': self.cohort_id,
            'assigned_condition_order': self.assigned_condition_order,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_dropout': self.is_dropout,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Participant':
        return cls(
            participant_id=data['participant_id'],
            cohort_id=data['cohort_id'],
            assigned_condition_order=data['assigned_condition_order'],
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            is_dropout=data.get('is_dropout', False),
            metadata=data.get('metadata', {})
        )

@dataclass
class Task:
    """
    Represents a specific bug localization task (a buggy method).
    Linked to a Defects4J project and method.
    """
    task_id: str
    project_id: str  # e.g., 'Math-1', 'Time-5'
    method_name: str
    file_path: str
    buggy_method_code: str
    ground_truth_line: int
    condition: str  # 'baseline', 'llm_sim', 'rule'
    summary_text: Optional[str] = None
    is_completed: bool = False
    completion_time_ms: Optional[int] = None
    selected_line: Optional[int] = None
    participant_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'project_id': self.project_id,
            'method_name': self.method_name,
            'file_path': self.file_path,
            'buggy_method_code': self.buggy_method_code,
            'ground_truth_line': self.ground_truth_line,
            'condition': self.condition,
            'summary_text': self.summary_text,
            'is_completed': self.is_completed,
            'completion_time_ms': self.completion_time_ms,
            'selected_line': self.selected_line,
            'participant_id': self.participant_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        return cls(
            task_id=data['task_id'],
            project_id=data['project_id'],
            method_name=data['method_name'],
            file_path=data['file_path'],
            buggy_method_code=data['buggy_method_code'],
            ground_truth_line=data['ground_truth_line'],
            condition=data['condition'],
            summary_text=data.get('summary_text'),
            is_completed=data.get('is_completed', False),
            completion_time_ms=data.get('completion_time_ms'),
            selected_line=data.get('selected_line'),
            participant_id=data.get('participant_id')
        )

@dataclass
class Summary:
    """
    Represents a code summary generated for a specific task.
    Used to link a summary text to a task for the study.
    """
    summary_id: str
    task_id: str
    generator_type: str  # 'llm_sim', 'rule', 'real_llm'
    summary_text: str
    generated_at: datetime
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'summary_id': self.summary_id,
            'task_id': self.task_id,
            'generator_type': self.generator_type,
            'summary_text': self.summary_text,
            'generated_at': self.generated_at.isoformat(),
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Summary':
        return cls(
            summary_id=data['summary_id'],
            task_id=data['task_id'],
            generator_type=data['generator_type'],
            summary_text=data['summary_text'],
            generated_at=datetime.fromisoformat(data['generated_at']),
            version=data.get('version', '1.0')
        )

@dataclass
class InteractionLog:
    """
    Records a single interaction event during the study.
    This is the raw log entry before anonymization or aggregation.
    """
    log_id: str
    participant_id: str
    task_id: str
    condition: str
    timestamp_ms: int
    selected_line: int
    ground_truth_line: int
    is_correct: bool
    latency_ms: Optional[int] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'log_id': self.log_id,
            'participant_id': self.participant_id,
            'task_id': self.task_id,
            'condition': self.condition,
            'timestamp_ms': self.timestamp_ms,
            'selected_line': self.selected_line,
            'ground_truth_line': self.ground_truth_line,
            'is_correct': self.is_correct,
            'latency_ms': self.latency_ms,
            'session_id': self.session_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractionLog':
        return cls(
            log_id=data['log_id'],
            participant_id=data['participant_id'],
            task_id=data['task_id'],
            condition=data['condition'],
            timestamp_ms=data['timestamp_ms'],
            selected_line=data['selected_line'],
            ground_truth_line=data['ground_truth_line'],
            is_correct=data['is_correct'],
            latency_ms=data.get('latency_ms'),
            session_id=data.get('session_id')
        )

@dataclass
class AnalysisResult:
    """
    Aggregated statistical result for a specific comparison or metric.
    """
    result_id: str
    comparison_type: str  # e.g., 'baseline_vs_llm', 'baseline_vs_rule'
    metric_type: str  # e.g., 'accuracy', 'speed', 'effect_size'
    value: float
    p_value: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None
    sample_size: int = 0
    method_details: str = ""
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'comparison_type': self.comparison_type,
            'metric_type': self.metric_type,
            'value': self.value,
            'p_value': self.p_value,
            'confidence_interval': self.confidence_interval,
            'sample_size': self.sample_size,
            'method_details': self.method_details,
            'generated_at': self.generated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        return cls(
            result_id=data['result_id'],
            comparison_type=data['comparison_type'],
            metric_type=data['metric_type'],
            value=data['value'],
            p_value=data.get('p_value'),
            confidence_interval=data.get('confidence_interval'),
            sample_size=data.get('sample_size', 0),
            method_details=data.get('method_details', ""),
            generated_at=datetime.fromisoformat(data['generated_at']) if data.get('generated_at') else datetime.now()
        )