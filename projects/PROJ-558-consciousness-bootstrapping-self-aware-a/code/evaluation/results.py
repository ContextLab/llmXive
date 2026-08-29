from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class EvaluationResult:
    """
    Represents the result of a single evaluation run or benchmark question.
    Designed to capture the outputs required for meta-cognitive metrics.
    """
    result_id: str
    dataset_name: str  # e.g., 'gsm8k', 'mmlu'
    question_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Generation Data
    generated_paths: List[str] = field(default_factory=list)
    majority_vote_answer: Optional[str] = None
    tie_break_used: bool = False
    
    # Confidence & Calibration Data
    confidence_scores: List[float] = field(default_factory=list)
    average_confidence: Optional[float] = None
    
    # Ground Truth & Accuracy
    ground_truth: Optional[str] = None
    is_correct: Optional[bool] = None
    
    # Metrics (pre-calculated or aggregated)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Raw diagnostic data for reproducibility
    raw_log_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        return {
            'result_id': self.result_id,
            'dataset_name': self.dataset_name,
            'question_id': self.question_id,
            'timestamp': self.timestamp.isoformat(),
            'generated_paths': self.generated_paths,
            'majority_vote_answer': self.majority_vote_answer,
            'tie_break_used': self.tie_break_used,
            'confidence_scores': self.confidence_scores,
            'average_confidence': self.average_confidence,
            'ground_truth': self.ground_truth,
            'is_correct': self.is_correct,
            'metrics': self.metrics,
            'raw_log_data': self.raw_log_data
        }

    def save_to_json(self, output_path: Path) -> None:
        """Save the result to a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Reconstruct from a dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            result_id=data['result_id'],
            dataset_name=data['dataset_name'],
            question_id=data['question_id'],
            timestamp=timestamp,
            generated_paths=data.get('generated_paths', []),
            majority_vote_answer=data.get('majority_vote_answer'),
            tie_break_used=data.get('tie_break_used', False),
            confidence_scores=data.get('confidence_scores', []),
            average_confidence=data.get('average_confidence'),
            ground_truth=data.get('ground_truth'),
            is_correct=data.get('is_correct'),
            metrics=data.get('metrics', {}),
            raw_log_data=data.get('raw_log_data', {})
        )
