"""
Synthetic Query Generator.

Implements T006 and T017.
Generates queries with exact integer plan depths (1, 2, 3, 4+).
Calls ReferenceEngine to assign ground_truth_plan.
"""

import json
import os
import random
from typing import List, Dict, Any, Optional

from .reference_engine import ReferenceEngine

class SyntheticQueryGenerator:
    """Generates synthetic queries with ground-truth plans."""

    def __init__(self, reference_engine: ReferenceEngine, seed: int = 42):
        random.seed(seed)
        self.reference_engine = reference_engine

    def generate(self, num_queries: int = 100) -> List[Dict[str, Any]]:
        """
        Generate a set of synthetic queries.
        Each query has:
        - id
        - source_type (text, relational, graph)
        - complexity_level (integer: 1, 2, 3, 4+)
        - ground_truth_plan (from ReferenceEngine)
        """
        queries = []
        source_types = ["text", "relational", "graph"]

        for i in range(num_queries):
            source_type = random.choice(source_types)
            # Complexity level: 1, 2, 3, 4+ (capped at 5 for simulation)
            complexity = random.randint(1, 5)

            # Generate ground truth plan
            plan = self.reference_engine.generate_plan(source_type, complexity)

            query = {
                "id": f"q_{i}",
                "source_type": source_type,
                "complexity_level": complexity,
                "ground_truth_plan": plan,
                "payload": f"Query payload for {source_type} at level {complexity}"
            }
            queries.append(query)

        return queries

    def main(self):
        """Entry point."""
        print("Synthetic Query Generator initialized.")

if __name__ == "__main__":
    main()
