"""
Evaluation result models matching contracts/evaluation_schema.yaml.
"""
from typing import Any, Dict, List, Optional
from .base import BaseModel

class EvaluationResult(BaseModel):
    """Single evaluation result for a question."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question_id": {
                    "type": "string",
                    "required": True,
                    "description": "Unique question identifier"
                },
                "doc_id": {
                    "type": "string",
                    "required": True,
                    "description": "Document identifier"
                },
                "position": {
                    "type": "string",
                    "required": True,
                    "description": "Question position: 'first', 'middle', or 'last'"
                },
                "model_name": {
                    "type": "string",
                    "required": True,
                    "description": "VLM model name"
                },
                "answer": {
                    "type": "string",
                    "required": True,
                    "description": "Generated answer"
                },
                "is_correct": {
                    "type": "boolean",
                    "required": True,
                    "description": "Whether the answer is correct"
                },
                "latency_ms": {
                    "type": "number",
                    "required": False,
                    "description": "Inference latency in milliseconds"
                },
                "memory_mb": {
                    "type": "number",
                    "required": False,
                    "description": "Memory usage in MB"
                }
            }
        }

    def __init__(
        self,
        question_id: str,
        doc_id: str,
        position: str,
        model_name: str,
        answer: str,
        is_correct: bool,
        latency_ms: Optional[float] = None,
        memory_mb: Optional[float] = None
    ):
        data = {
            "question_id": question_id,
            "doc_id": doc_id,
            "position": position,
            "model_name": model_name,
            "answer": answer,
            "is_correct": is_correct
        }
        if latency_ms is not None:
            data["latency_ms"] = latency_ms
        if memory_mb is not None:
            data["memory_mb"] = memory_mb
        self._data = self.validate(data)
        self.question_id = question_id
        self.doc_id = doc_id
        self.position = position
        self.model_name = model_name
        self.answer = answer
        self.is_correct = is_correct
        self.latency_ms = latency_ms
        self.memory_mb = memory_mb

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "question_id": self.question_id,
            "doc_id": self.doc_id,
            "position": self.position,
            "model_name": self.model_name,
            "answer": self.answer,
            "is_correct": self.is_correct
        }
        if self.latency_ms is not None:
            result["latency_ms"] = self.latency_ms
        if self.memory_mb is not None:
            result["memory_mb"] = self.memory_mb
        return result

class BaselineMetrics(BaseModel):
    """Baseline evaluation metrics per model."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "required": True,
                    "description": "VLM model name"
                },
                "overall_accuracy": {
                    "type": "number",
                    "required": True,
                    "description": "Overall accuracy (0.0-1.0)"
                },
                "first_third_accuracy": {
                    "type": "number",
                    "required": True,
                    "description": "Accuracy for first third questions"
                },
                "middle_third_accuracy": {
                    "type": "number",
                    "required": True,
                    "description": "Accuracy for middle third questions"
                },
                "last_third_accuracy": {
                    "type": "number",
                    "required": True,
                    "description": "Accuracy for last third questions"
                },
                "delta_middle_vs_others": {
                    "type": "number",
                    "required": True,
                    "description": "Delta between middle and average of first/last"
                },
                "bias_threshold_met": {
                    "type": "boolean",
                    "required": True,
                    "description": "True if delta >= 0.05"
                },
                "total_questions": {
                    "type": "integer",
                    "required": True,
                    "description": "Total number of questions evaluated"
                },
                "correct_count": {
                    "type": "integer",
                    "required": True,
                    "description": "Number of correct answers"
                }
            }
        }

    def __init__(
        self,
        model_name: str,
        overall_accuracy: float,
        first_third_accuracy: float,
        middle_third_accuracy: float,
        last_third_accuracy: float,
        delta_middle_vs_others: float,
        bias_threshold_met: bool,
        total_questions: int,
        correct_count: int
    ):
        data = {
            "model_name": model_name,
            "overall_accuracy": overall_accuracy,
            "first_third_accuracy": first_third_accuracy,
            "middle_third_accuracy": middle_third_accuracy,
            "last_third_accuracy": last_third_accuracy,
            "delta_middle_vs_others": delta_middle_vs_others,
            "bias_threshold_met": bias_threshold_met,
            "total_questions": total_questions,
            "correct_count": correct_count
        }
        self._data = self.validate(data)
        self.model_name = model_name
        self.overall_accuracy = overall_accuracy
        self.first_third_accuracy = first_third_accuracy
        self.middle_third_accuracy = middle_third_accuracy
        self.last_third_accuracy = last_third_accuracy
        self.delta_middle_vs_others = delta_middle_vs_others
        self.bias_threshold_met = bias_threshold_met
        self.total_questions = total_questions
        self.correct_count = correct_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "overall_accuracy": self.overall_accuracy,
            "first_third_accuracy": self.first_third_accuracy,
            "middle_third_accuracy": self.middle_third_accuracy,
            "last_third_accuracy": self.last_third_accuracy,
            "delta_middle_vs_others": self.delta_middle_vs_others,
            "bias_threshold_met": self.bias_threshold_met,
            "total_questions": self.total_questions,
            "correct_count": self.correct_count
        }

class RetrievalMetrics(BaseModel):
    """Retrieval-augmented evaluation metrics."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "required": True,
                    "description": "VLM model name"
                },
                "overall_accuracy": {
                    "type": "number",
                    "required": True,
                    "description": "Overall accuracy with retrieval"
                },
                "middle_third_accuracy": {
                    "type": "number",
                    "required": True,
                    "description": "Accuracy for middle third questions with retrieval"
                },
                "retrieval_precision": {
                    "type": "number",
                    "required": True,
                    "description": "Retrieval precision"
                },
                "retrieval_recall": {
                    "type": "number",
                    "required": True,
                    "description": "Retrieval recall"
                },
                "false_positive_rate": {
                    "type": "number",
                    "required": True,
                    "description": "Rate of false positive retrievals"
                },
                "avg_tokens_used": {
                    "type": "number",
                    "required": True,
                    "description": "Average tokens used in context"
                },
                "total_questions": {
                    "type": "integer",
                    "required": True,
                    "description": "Total number of questions evaluated"
                }
            }
        }

    def __init__(
        self,
        model_name: str,
        overall_accuracy: float,
        middle_third_accuracy: float,
        retrieval_precision: float,
        retrieval_recall: float,
        false_positive_rate: float,
        avg_tokens_used: float,
        total_questions: int
    ):
        data = {
            "model_name": model_name,
            "overall_accuracy": overall_accuracy,
            "middle_third_accuracy": middle_third_accuracy,
            "retrieval_precision": retrieval_precision,
            "retrieval_recall": retrieval_recall,
            "false_positive_rate": false_positive_rate,
            "avg_tokens_used": avg_tokens_used,
            "total_questions": total_questions
        }
        self._data = self.validate(data)
        self.model_name = model_name
        self.overall_accuracy = overall_accuracy
        self.middle_third_accuracy = middle_third_accuracy
        self.retrieval_precision = retrieval_precision
        self.retrieval_recall = retrieval_recall
        self.false_positive_rate = false_positive_rate
        self.avg_tokens_used = avg_tokens_used
        self.total_questions = total_questions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "overall_accuracy": self.overall_accuracy,
            "middle_third_accuracy": self.middle_third_accuracy,
            "retrieval_precision": self.retrieval_precision,
            "retrieval_recall": self.retrieval_recall,
            "false_positive_rate": self.false_positive_rate,
            "avg_tokens_used": self.avg_tokens_used,
            "total_questions": self.total_questions
        }
