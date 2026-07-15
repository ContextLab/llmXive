"""
Synthetic Query Generator.

Generates queries with exact integer plan depths (1, 2, 3, 4+).
Assigns ground_truth_plan via ReferenceEngine.
"""
import json
import os
import random
from typing import List, Dict, Any, Optional
from .reference_engine import ReferenceEngine

class SyntheticQueryGenerator:
    """
    Generates synthetic queries for testing execution engines.
    """
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.reference_engine = ReferenceEngine(seed=seed)
        
        self.text_templates = [
            "what is {topic}",
            "how to {action} {topic}",
            "why is {topic} important",
            "list {count} {topic}",
            "compare {topic1} and {topic2}"
        ]
        
        self.topics = ["python", "machine learning", "data science", "artificial intelligence", "cloud computing"]
        self.actions = ["build", "use", "learn", "optimize"]
        
    def generate_query(self, complexity_level: int) -> Dict[str, Any]:
        """
        Generates a single query with the specified complexity level.
        
        Args:
            complexity_level: Integer 1, 2, 3, or 4+.
        
        Returns:
            A dictionary representing the query instance.
        """
        # Generate text
        template = random.choice(self.text_templates)
        if "{topic}" in template:
            template = template.replace("{topic}", random.choice(self.topics))
        if "{action}" in template:
            template = template.replace("{action}", random.choice(self.actions))
        if "{count}" in template:
            template = template.replace("{count}", str(random.randint(1, 10)))
        if "{topic1}" in template:
            template = template.replace("{topic1}", random.choice(self.topics))
            template = template.replace("{topic2}", random.choice(self.topics))
        
        query_text = template
        
        # Generate ground truth plan using ReferenceEngine
        ground_truth_plan = self.reference_engine.generate_plan(query_text, complexity_level)
        
        query_obj = {
            "id": f"syn_{random.randint(10000, 99999)}",
            "text": query_text,
            "complexity_level": complexity_level,
            "ground_truth_plan": ground_truth_plan,
            "source_type": "text"
        }
        
        return query_obj
    
    def generate_batch(self, count: int, levels: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Generates a batch of queries.
        
        Args:
            count: Number of queries to generate.
            levels: List of complexity levels to distribute. If None, randomizes 1-4.
        
        Returns:
            List of query dictionaries.
        """
        if levels is None:
            levels = [1, 2, 3, 4]
        
        queries = []
        for _ in range(count):
            level = random.choice(levels)
            queries.append(self.generate_query(level))
        
        return queries

def main():
    """
    Standalone test runner.
    """
    generator = SyntheticQueryGenerator(seed=42)
    
    # Generate a small batch
    queries = generator.generate_batch(5, levels=[1, 2, 3, 4])
    
    print(json.dumps(queries, indent=2))

if __name__ == "__main__":
    main()
