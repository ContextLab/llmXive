from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from pathlib import Path
import uuid


@dataclass
class Participant:
    """
    Represents a human participant in the study.
    """
    participant_id: str
    consent_timestamp: datetime
    demographic_data: Dict[str, Any] = field(default_factory=dict)
    group_assignment: Optional[str] = None  # e.g., "Group A", "Group B" for Latin-square
    completed_tasks: List[str] = field(default_factory=list)
    dropout_flag: bool = False
    dropout_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "consent_timestamp": self.consent_timestamp.isoformat(),
            "demographic_data": self.demographic_data,
            "group_assignment": self.group_assignment,
            "completed_tasks": self.completed_tasks,
            "dropout_flag": self.dropout_flag,
            "dropout_reason": self.dropout_reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Participant":
        return cls(
            participant_id=data["participant_id"],
            consent_timestamp=datetime.fromisoformat(data["consent_timestamp"]),
            demographic_data=data.get("demographic_data", {}),
            group_assignment=data.get("group_assignment"),
            completed_tasks=data.get("completed_tasks", []),
            dropout_flag=data.get("dropout_flag", False),
            dropout_reason=data.get("dropout_reason")
        )


@dataclass
class Task:
    """
    Represents a specific bug localization task instance (a method from Defects4J).
    """
    task_id: str
    method_name: str
    file_path: str
    project_name: str
    buggy_line_number: int  # Ground truth line
    context_window: int = 50  # Lines of context provided
    code_snippet: str = ""
    ground_truth_line: int = 0  # Alias or specific ground truth for analysis

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "method_name": self.method_name,
            "file_path": self.file_path,
            "project_name": self.project_name,
            "buggy_line_number": self.buggy_line_number,
            "context_window": self.context_window,
            "code_snippet": self.code_snippet,
            "ground_truth_line": self.ground_truth_line
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            task_id=data["task_id"],
            method_name=data["method_name"],
            file_path=data["file_path"],
            project_name=data["project_name"],
            buggy_line_number=data["buggy_line_number"],
            context_window=data.get("context_window", 50),
            code_snippet=data.get("code_snippet", ""),
            ground_truth_line=data.get("ground_truth_line", data["buggy_line_number"])
        )


@dataclass
class Summary:
    """
    Represents a generated summary for a specific task.
    """
    summary_id: str
    task_id: str
    summary_type: str  # "llm_sim", "rule", "real_llm"
    content: str
    generation_timestamp: datetime
    model_version: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "task_id": self.task_id,
            "summary_type": self.summary_type,
            "content": self.content,
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "model_version": self.model_version,
            "parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Summary":
        return cls(
            summary_id=data["summary_id"],
            task_id=data["task_id"],
            summary_type=data["summary_type"],
            content=data["content"],
            generation_timestamp=datetime.fromisoformat(data["generation_timestamp"]),
            model_version=data.get("model_version"),
            parameters=data.get("parameters", {})
        )


@dataclass
class InteractionLog:
    """
    Records a single interaction event from a participant.
    """
    log_id: str
    participant_id: str
    task_id: str
    condition: str  # e.g., "baseline", "llm_sim", "rule"
    timestamp_ms: int
    selected_line: int
    ground_truth_line: int
    latency_ms: Optional[int] = None
    is_correct: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "participant_id": self.participant_id,
            "task_id": self.task_id,
            "condition": self.condition,
            "timestamp_ms": self.timestamp_ms,
            "selected_line": self.selected_line,
            "ground_truth_line": self.ground_truth_line,
            "latency_ms": self.latency_ms,
            "is_correct": self.is_correct
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InteractionLog":
        return cls(
            log_id=data["log_id"],
            participant_id=data["participant_id"],
            task_id=data["task_id"],
            condition=data["condition"],
            timestamp_ms=data["timestamp_ms"],
            selected_line=data["selected_line"],
            ground_truth_line=data["ground_truth_line"],
            latency_ms=data.get("latency_ms"),
            is_correct=data.get("is_correct", False)
        )


@dataclass
class AnalysisResult:
    """
    Stores the statistical results of an analysis comparison.
    """
    result_id: str
    analysis_type: str  # "mcnemar", "lme", "bootstrap"
    comparison: str  # e.g., "baseline_vs_llm"
    metric: str  # e.g., "accuracy", "speed"
    statistic: float
    p_value: float
    effect_size: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None
    corrected_p_value: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "analysis_type": self.analysis_type,
            "comparison": self.comparison,
            "metric": self.metric,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": self.confidence_interval,
            "corrected_p_value": self.corrected_p_value,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        return cls(
            result_id=data["result_id"],
            analysis_type=data["analysis_type"],
            comparison=data["comparison"],
            metric=data["metric"],
            statistic=data["statistic"],
            p_value=data["p_value"],
            effect_size=data.get("effect_size"),
            confidence_interval=data.get("confidence_interval"),
            corrected_p_value=data.get("corrected_p_value"),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )