import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

@dataclass
class PromptSet:
    id: str
    prompts: List[str]
    category: str  # 'in_distribution' or 'out_distribution'
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "prompts": self.prompts,
            "category": self.category,
            "created_at": self.created_at.isoformat()
        }

@dataclass
class ModelWeights:
    model_id: str
    path: Path
    checksum: str
    loaded_at: datetime = field(default_factory=datetime.now)

@dataclass
class GeneratedImage:
    id: str
    prompt_id: str
    model_id: str
    path: Path
    seed: int
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class EvaluationScore:
    image_id: str
    metric_name: str
    score: float
    model_id: str
    evaluated_at: datetime = field(default_factory=datetime.now)
