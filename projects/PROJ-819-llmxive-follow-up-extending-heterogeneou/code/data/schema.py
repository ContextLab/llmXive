"""
Schema definitions for the llmXive benchmark pipeline.

This module defines the data structures used to represent benchmark queries
and their associated metadata.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json


@dataclass
class BenchmarkQuery:
    """
    Represents a single benchmark query with its ground truth and metadata.

    Attributes:
        prompt: The natural language question or task description.
        ground_truth: The expected answer or solution.
        steps: A list of reasoning steps or solution outline.
        seed: The random seed used to generate this query (for reproducibility).
        domain: The scientific domain of the query (e.g., 'physics', 'chemistry').
    """
    prompt: str
    ground_truth: str
    steps: List[str]
    seed: int
    domain: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkQuery':
        """
        Create a BenchmarkQuery instance from a dictionary.

        Args:
            data: Dictionary containing the query fields.

        Returns:
            A new BenchmarkQuery instance.

        Raises:
            KeyError: If a required field is missing.
            ValueError: If a field has an invalid type.
        """
        required_fields = ['prompt', 'ground_truth', 'steps', 'seed', 'domain']
        for field_name in required_fields:
            if field_name not in data:
                raise KeyError(f"Missing required field: {field_name}")

        if not isinstance(data['prompt'], str):
            raise ValueError(f"Field 'prompt' must be a string, got {type(data['prompt']).__name__}")
        if not isinstance(data['ground_truth'], str):
            raise ValueError(f"Field 'ground_truth' must be a string, got {type(data['ground_truth']).__name__}")
        if not isinstance(data['steps'], list):
            raise ValueError(f"Field 'steps' must be a list, got {type(data['steps']).__name__}")
        if not all(isinstance(s, str) for s in data['steps']):
            raise ValueError("All items in 'steps' must be strings")
        if not isinstance(data['seed'], int):
            raise ValueError(f"Field 'seed' must be an integer, got {type(data['seed']).__name__}")
        if not isinstance(data['domain'], str):
            raise ValueError(f"Field 'domain' must be a string, got {type(data['domain']).__name__}")

        return cls(
            prompt=data['prompt'],
            ground_truth=data['ground_truth'],
            steps=data['steps'],
            seed=data['seed'],
            domain=data['domain']
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the BenchmarkQuery instance to a dictionary.

        Returns:
            Dictionary representation of the query.
        """
        return {
            'prompt': self.prompt,
            'ground_truth': self.ground_truth,
            'steps': self.steps,
            'seed': self.seed,
            'domain': self.domain
        }