"""
Reference Engine for generating ground-truth execution plans.

Provides deterministic plan generation based on query complexity.
"""
import random
import json
from typing import Dict, Any, List, Optional

class ReferenceEngine:
    """
    Generates independent, deterministic ground-truth execution plans.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        
    def generate_plan(self, query_text: str, complexity_level: int) -> Dict[str, Any]:
        """
        Generates a plan for the given query and complexity level.
        
        The plan structure is deterministic based on the seed and inputs.
        """
        # Reset seed based on query and level to ensure determinism
        # In a real system, this might use a hash of the query
        plan_seed = hash((self.seed, query_text, complexity_level))
        rng = random.Random(plan_seed)
        
        plan = {
            "id": f"plan_{rng.randint(1000, 9999)}",
            "steps": [],
            "estimated_cost": 0.0
        }
        
        if complexity_level == 1:
            plan["steps"] = [{"op": "scan", "target": "passages", "filter": "simple"}]
            plan["estimated_cost"] = 1.0
        elif complexity_level == 2:
            plan["steps"] = [
                {"op": "scan", "target": "passages", "filter": "simple"},
                {"op": "aggregate", "func": "count"}
            ]
            plan["estimated_cost"] = 2.5
        elif complexity_level == 3:
            plan["steps"] = [
                {"op": "scan", "target": "passages", "filter": "simple"},
                {"op": "lookup", "target": "metadata"},
                {"op": "join", "keys": ["pid"]}
            ]
            plan["estimated_cost"] = 5.0
        elif complexity_level >= 4:
            plan["steps"] = [
                {"op": "scan", "target": "passages", "filter": "complex"},
                {"op": "lookup", "target": "metadata"},
                {"op": "join", "keys": ["pid"]},
                {"op": "aggregate", "func": "complex_aggr"},
                {"op": "sort", "key": "score"}
            ]
            plan["estimated_cost"] = 10.0 + (complexity_level * 2)
        
        return plan

def main():
    """
    Standalone test runner.
    """
    engine = ReferenceEngine(seed=42)
    
    for level in [1, 2, 3, 4]:
        plan = engine.generate_plan("test query", level)
        print(f"Level {level}: {json.dumps(plan)}")

if __name__ == "__main__":
    main()