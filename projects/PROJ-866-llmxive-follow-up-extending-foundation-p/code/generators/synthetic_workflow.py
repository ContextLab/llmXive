"""
synthetic_workflow.py
---------------------

Deterministic workflow generator for the llmXive pipeline.
Generates synthetic multi-agent workflows with varying delegation depths 
and policy complexities to serve as ground truth for compression analysis.

The generator ensures a uniform distribution of depths to satisfy SC-001 
and FR-001.
"""
import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List

import yaml

class SyntheticWorkflowGenerator:
    """
    Generator for synthetic multi-agent workflows.
    Produces workflows with a specific graph topology: a linear chain of agents
    (delegation depth) with associated policy constraints (complexity).
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def load_schema(self, schema_path: Path) -> Dict[str, Any]:
        """Load a YAML JSON-Schema contract."""
        if not schema_path.is_file():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        return yaml.safe_load(schema_path.read_text(encoding="utf-8"))

    def generate_workflow_item(self, index: int, depth: int, complexity: int, item_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a single workflow dictionary.
        
        Constructs a real graph structure:
        - Nodes: A chain of 'depth' agents.
        - Edges: Linear delegation from agent i to i+1.
        - Policies: 'complexity' number of constraints attached to random nodes.
        """
        # 1. Build the actual research data
        nodes = []
        for i in range(depth + 1):
            nodes.append({"id": f"node_{i}", "agent": f"agent_{i}", "role": f"role_{i}"})
        
        edges = []
        for i in range(depth):
            edges.append({"from": f"node_{i}", "to": f"node_{i+1}"})
        
        policies = []
        for j in range(complexity):
            target_node = f"node_{self.rng.randint(0, depth)}"
            policies.append({
                "id": f"pol_{j}", 
                "rule": f"constraint_{j}", 
                "target": target_node,
                "value": self.rng.randint(1, 100)
            })

        # 2. Map to schema properties
        properties = item_schema.get("properties", {})
        workflow: Dict[str, Any] = {}
        
        # Essential research fields
        workflow["id"] = f"wf_{index}"
        workflow["metadata"] = {
            "depth": depth,
            "complexity": complexity,
            "seed": self.seed
        }
        
        # Fill schema-required fields using the constructed graph
        # We use the constructed lists if the schema expects arrays
        for field, field_schema in properties.items():
            if field == "id": continue
            if field == "metadata": continue
            
            f_type = field_schema.get("type")
            if f_type == "array":
                if "node" in field.lower(): workflow[field] = nodes
                elif "edge" in field.lower(): workflow[field] = edges
                elif "policy" in field.lower(): workflow[field] = policies
                else: workflow[field] = []
            elif f_type == "string":
                workflow[field] = f"val_{field}_{index}"
            elif f_type == "integer" or f_type == "number":
                workflow[field] = self.rng.randint(1, 100)
            elif f_type == "boolean":
                workflow[field] = True
            elif f_type == "object":
                workflow[field] = {}
            else:
                workflow[field] = None

        return workflow

    def generate_workflows(self, count: int, schema_path: Path) -> List[Dict[str, Any]]:
        """
        Generate 'count' workflows with uniform depth distribution.
        Ensures at least 25 workflows per depth level for depths 1-20.
        """
        schema = self.load_schema(schema_path)
        
        # Extract the item schema from the top-level array/object
        if schema.get("type") == "array":
            items_schema = schema.get("items", {})
        elif schema.get("type") == "object":
            props = schema.get("properties", {})
            array_prop = next((p for p in props.values() if isinstance(p, dict) and p.get("type") == "array"), None)
            if array_prop is None:
                raise ValueError("No array property found in workflow schema.")
            items_schema = array_prop.get("items", {})
        else:
            raise ValueError("Unsupported workflow schema top-level type.")

        workflows = []
        # Define depth range [1, 20]
        depth_range = range(1, 21)
        
        for i in range(count):
            # Uniformly sample depth to ensure balanced distribution
            depth = depth_range[i % len(depth_range)]
            # Random complexity between 1 and 10
            complexity = self.rng.randint(1, 10)
            workflows.append(self.generate_workflow_item(i, depth, complexity, items_schema))
        
        return workflows

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="synthetic_workflow.py",
        description="Deterministic synthetic workflow generator for the llmXive pipeline."
    )
    parser.add_argument("--count", type=int, required=True, help="Number of workflows to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path.")
    args = parser.parse_args()

    from llmxive_toolkit import paths
    schema_path = paths.root / "contracts" / "workflow.schema.yaml"
    
    generator = SyntheticWorkflowGenerator(seed=args.seed)
    workflows = generator.generate_workflows(args.count, schema_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(workflows, f, indent=2)

    print(f"Generated {len(workflows)} synthetic workflows -> {args.output}")

if __name__ == "__main__":
    main()
