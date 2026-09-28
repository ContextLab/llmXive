import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

def generate_workflow(depth: int, complexity: int, workflow_id: int, seed: int) -> Dict[str, Any]:
    """
    Generate a single synthetic workflow.
    
    Args:
        depth: The depth of the workflow graph
        complexity: Number of constraints (1-8)
        workflow_id: Unique identifier for the workflow
        seed: Random seed for reproducibility
    
    Returns:
        A dictionary representing the workflow
    """
    random.seed(seed + workflow_id)
    
    nodes = []
    edges = []
    
    # Create a linear chain with possible branches
    # Depth 1: Single node
    # Depth > 1: Chain with possible branching
    
    num_nodes = depth + 1
    for i in range(num_nodes):
        node_type = "agent" if i % 2 == 0 else "action"
        node = {
            "id": f"node_{workflow_id}_{i}",
            "type": node_type,
            "constraints": []
        }
        
        # Add constraints based on complexity
        constraint_types = ["budget", "sovereignty", "latency"]
        num_constraints = min(complexity, len(constraint_types))
        selected_constraints = random.sample(constraint_types, num_constraints)
        
        for constraint in selected_constraints:
            if constraint == "budget":
                node["constraints"].append({
                    "type": "budget",
                    "value": random.randint(10, 100),
                    "operator": "<="
                })
            elif constraint == "sovereignty":
                node["constraints"].append({
                    "type": "sovereignty",
                    "region": random.choice(["EU", "US", "ASIA"]),
                    "operator": "=="
                })
            elif constraint == "latency":
                node["constraints"].append({
                    "type": "latency",
                    "value": random.randint(100, 1000),
                    "operator": "<="
                })
        
        nodes.append(node)
        
        # Create edges
        if i > 0:
            edges.append({
                "source": f"node_{workflow_id}_{i-1}",
                "target": f"node_{workflow_id}_{i}",
                "type": "sequential"
            })
        
        # Add branching for higher depths
        if depth > 3 and i > 0 and random.random() < 0.3:
            extra_node_id = f"node_{workflow_id}_{i}_branch"
            nodes.append({
                "id": extra_node_id,
                "type": "action",
                "constraints": []
            })
            edges.append({
                "source": f"node_{workflow_id}_{i-1}",
                "target": extra_node_id,
                "type": "parallel"
            })
    
    return {
        "id": f"workflow_{workflow_id}",
        "depth": depth,
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "generated_seed": seed,
            "complexity_level": complexity,
            "is_valid": True  # Will be updated by Oracle
        }
    }

def generate_invalid_workflow(depth: int, workflow_id: int, seed: int) -> Dict[str, Any]:
    """
    Generate an invalid workflow with conflicting constraints.
    """
    random.seed(seed + workflow_id + 1000)  # Different seed for invalid workflows
    
    nodes = []
    edges = []
    
    # Create a simple workflow
    num_nodes = max(1, depth)
    for i in range(num_nodes):
        node = {
            "id": f"node_{workflow_id}_{i}",
            "type": "agent" if i % 2 == 0 else "action",
            "constraints": []
        }
        
        # Add conflicting constraints
        node["constraints"].append({
            "type": "budget",
            "value": 10,
            "operator": "<="
        })
        node["constraints"].append({
            "type": "budget",
            "value": 5,
            "operator": ">="  # Conflict: must be <= 10 AND >= 5 (ok if in range, but let's make it impossible)
        })
        node["constraints"].append({
            "type": "sovereignty",
            "region": "EU",
            "operator": "=="
        })
        node["constraints"].append({
            "type": "sovereignty",
            "region": "US",
            "operator": "=="  # Conflict: must be EU AND US
        })
        
        nodes.append(node)
        
        if i > 0:
            edges.append({
                "source": f"node_{workflow_id}_{i-1}",
                "target": f"node_{workflow_id}_{i}",
                "type": "sequential"
            })
    
    return {
        "id": f"workflow_{workflow_id}",
        "depth": depth,
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "generated_seed": seed,
            "complexity_level": 4,
            "is_valid": False,  # Explicitly marked as invalid
            "invalid_reason": "conflicting_constraints"
        }
    }

class SyntheticWorkflowGenerator:
    """
    Generates deterministic synthetic workflows with varying depths and complexities.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.workflows = []
    
    def generate_all(self, count: int = 500, output_path: str = "data/raw/workflows.json") -> None:
        """
        Generate a set of workflows with uniform depth distribution.
        
        Args:
            count: Total number of workflows to generate
            output_path: Path to save the generated workflows
        """
        # Ensure at least 25 workflows per depth level 1-20
        # That's 20 * 25 = 500 minimum
        min_per_depth = 25
        depths = list(range(1, 21))
        
        # Calculate how many per depth
        workflows_per_depth = count // len(depths)
        remainder = count % len(depths)
        
        self.workflows = []
        workflow_id = 0
        
        # Generate valid workflows
        for depth in depths:
            num_for_this_depth = workflows_per_depth + (1 if depth <= remainder else 0)
            
            for i in range(num_for_this_depth):
                # Vary complexity randomly between low (1-3) and high (4-8)
                if random.random() < 0.5:
                    complexity = random.randint(1, 3)  # Low
                else:
                    complexity = random.randint(4, 8)  # High

            # Generate some invalid workflows (about 10% of total)
            # We'll generate them separately to ensure we have enough valid ones
        
        # Generate invalid workflows (10% of total count)
        num_invalid = count // 10
        invalid_start_id = 9000  # Use a different ID range for invalid workflows
        
        for i in range(num_invalid):
            depth = random.randint(1, 20)
            workflow = generate_invalid_workflow(depth, invalid_start_id + i, self.seed)
            self.workflows.append(workflow)
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.workflows, f, indent=2)
        
        print(f"Generated {len(self.workflows)} workflows (including {num_invalid} invalid)")
        print(f"Saved to {output_path}")
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """
        Return the generated workflows.
        """
        return self.workflows

def main():
    """
    CLI entry point for generating synthetic workflows.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic workflows")
    parser.add_argument("--count", type=int, default=500, help="Number of workflows to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, required=True, help="Output file path for workflows")
    
    args = parser.parse_args()
    
    generator = SyntheticWorkflowGenerator(seed=args.seed)
    generator.generate_all(count=args.count, output_path=args.output)

if __name__ == "__main__":
    main()
