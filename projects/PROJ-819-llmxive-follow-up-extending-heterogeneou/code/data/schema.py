"""
Schema definitions for the llmXive benchmark pipeline.

This module defines the data structures used to represent benchmark queries,
ensuring type safety and validation across the pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json


@dataclass
class BenchmarkQuery:
    """
    Represents a single benchmark query with its ground truth and metadata.

    Attributes:
        prompt: The input query string.
        ground_truth: The expected correct answer or result.
        steps: A list of intermediate steps or reasoning traces leading to the answer.
        seed: The random seed used to generate this specific query (for reproducibility).
        domain: The scientific domain or category this query belongs to.
    """
    prompt: str
    ground_truth: str
    steps: List[str] = field(default_factory=list)
    seed: int = 0
    domain: str = "general"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkQuery":
        """
        Create a BenchmarkQuery instance from a dictionary.

        Args:
            data: Dictionary containing query data.

        Returns:
            A new BenchmarkQuery instance.

        Raises:
            KeyError: If required fields are missing.
            ValueError: If field types are invalid.
        """
        if "prompt" not in data:
            raise KeyError("Missing required field: 'prompt'")
        if "ground_truth" not in data:
            raise KeyError("Missing required field: 'ground_truth'")

        return cls(
            prompt=str(data["prompt"]),
            ground_truth=str(data["ground_truth"]),
            steps=list(data.get("steps", [])),
            seed=int(data.get("seed", 0)),
            domain=str(data.get("domain", "general"))
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the BenchmarkQuery instance to a dictionary.

        Returns:
            Dictionary representation of the query.
        """
        return {
            "prompt": self.prompt,
            "ground_truth": self.ground_truth,
            "steps": self.steps,
            "seed": self.seed,
            "domain": self.domain
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """
        Convert the BenchmarkQuery instance to a JSON string.

        Args:
            indent: Indentation level for pretty-printing.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent)
