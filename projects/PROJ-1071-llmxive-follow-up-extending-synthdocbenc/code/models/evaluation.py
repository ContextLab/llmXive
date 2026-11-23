"""
Data models for evaluation results and metrics.
Matches the schema defined in contracts/evaluation_schema.yaml
"""
from typing import Any, Dict, List, Optional
from .base import BaseModel

class EvaluationResult(BaseModel):
    """
    Result of a single question evaluation.
    """
    def __init__(
        self,
        question_id: str,
        document_id: str,
        page_number: int,
        position_category: str,  # 'first', 'middle', 'last'
        ground_truth: str,
        predicted_answer: str,
        is_correct: bool,
        model_id: str,
        latency_ms: Optional[float] = None
    ):
        self.question_id = question_id
        self.document_id = document_id
        self.page_number = page_number
        self.position_category = position_category
        self.ground_truth = ground_truth
        self.predicted_answer = predicted_answer
        self.is_correct = is_correct
        self.model_id = model_id
        self.latency_ms = latency_ms

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        return super().from_dict(data)

class BaselineMetrics(BaseModel):
    """
    Aggregated metrics for the baseline (static image) evaluation.
    """
    def __init__(
        self,
        model_id: str,
        total_questions: int,
        correct_count: int,
        accuracy: float,
        accuracy_by_position: Dict[str, float],
        delta_middle_vs_others: float,
        bias_threshold_met: bool,
        latency_stats: Optional[Dict[str, float]] = None
    ):
        self.model_id = model_id
        self.total_questions = total_questions
        self.correct_count = correct_count
        self.accuracy = accuracy
        self.accuracy_by_position = accuracy_by_position
        self.delta_middle_vs_others = delta_middle_vs_others
        self.bias_threshold_met = bias_threshold_met
        self.latency_stats = latency_stats or {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaselineMetrics':
        return super().from_dict(data)

class RetrievalMetrics(BaseModel):
    """
    Aggregated metrics for the retrieval-augmented evaluation.
    """
    def __init__(
        self,
        model_id: str,
        total_questions: int,
        correct_count: int,
        accuracy: float,
        precision: float,
        recall: float,
        false_positive_rate: float,
        retrieval_latency_ms: Optional[float] = None,
        total_latency_ms: Optional[float] = None
    ):
        self.model_id = model_id
        self.total_questions = total_questions
        self.correct_count = correct_count
        self.accuracy = accuracy
        self.precision = precision
        self.recall = recall
        self.false_positive_rate = false_positive_rate
        self.retrieval_latency_ms = retrieval_latency_ms
        self.total_latency_ms = total_latency_ms

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetrievalMetrics':
        return super().from_dict(data)
