import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import uuid
from datetime import datetime

class SyntheticWorkflowGenerator:
    """
    Generates a collection of deterministic synthetic workflows (DAGs) with
    varying depths (1-20) and complexities (1-10).
    
    Features:
    - Deterministic seeding for reproducibility.
    - Generates DAGs with uniform depth distribution.
    - Records budget caps and metadata.
    """

    def __init__(self, seed: int = 42):
        """
        Initialize the generator with a random seed.
        
        Args:
            seed (int): Random seed for reproducibility.
        """
        self.seed = seed
        random.seed(seed)
        self.workflow_counter = 0

    def _generate_node(self, node_id: str, depth: int, max_depth: int) -> Dict[str, Any]:
        """
        Generate a single node for the workflow.
        
        Args:
            node_id (str): Unique ID for the node.
            depth (int): Topological depth of the node.
            max_depth (int): Maximum depth of the workflow.
            
        Returns:
            Dict[str, Any]: Node dictionary.
        """
        # Determine node type based on depth
        if depth == 0:
            node_type = "start"
        elif depth == max_depth:
            node_type = "end"
        else:
            # Randomly choose between process and decision
            node_type = random.choice(["process", "decision"])
        
        # Complexity: 1-10, slightly biased towards middle values
        complexity = random.randint(1, 10)
        
        # Policy tags
        policy_tags = []
        if node_type in ["process", "decision"]:
            possible_tags = ["data_sovereignty", "audit_required", "rate_limit", "retry_policy"]
            num_tags = random.randint(0, 2)
            policy_tags = random.sample(possible_tags, num_tags)
        
        # Data requirements
        data_requirements = {
            "sovereignty_level": random.choice(["public", "internal", "confidential", "restricted"]),
            "retention_days": random.choice([30, 90, 180, 365, 730])
        }
        
        return {
            "node_id": node_id,
            "node_type": node_type,
            "depth": depth,
            "complexity": complexity,
            "policy_tags": policy_tags,
            "data_requirements": data_requirements
        }

    def _generate_edges(self, nodes: List[Dict[str, Any]], max_depth: int) -> List[Dict[str, Any]]:
        """
        Generate edges to form a valid DAG.
        
        Args:
            nodes (List[Dict[str, Any]]): List of generated nodes.
            max_depth (int): Maximum depth of the workflow.
            
        Returns:
            List[Dict[str, Any]]: List of edge dictionaries.
        """
        edges = []
        nodes_by_depth = {}
        
        # Group nodes by depth
        for node in nodes:
            depth = node["depth"]
            if depth not in nodes_by_depth:
                nodes_by_depth[depth] = []
            nodes_by_depth[depth].append(node["node_id"])
        
        # Generate edges: each node at depth d connects to 1-3 nodes at depth d+1
        for depth in range(max_depth):
            if depth not in nodes_by_depth or depth + 1 not in nodes_by_depth:
                continue
            
            current_nodes = nodes_by_depth[depth]
            next_nodes = nodes_by_depth[depth + 1]
            
            for src_id in current_nodes:
                # Connect to 1-3 random nodes in the next depth
                num_connections = min(random.randint(1, 3), len(next_nodes))
                targets = random.sample(next_nodes, num_connections)
                
                for target_id in targets:
                    edges.append({
                        "source_node_id": src_id,
                        "target_node_id": target_id,
                        "weight": round(random.uniform(0.5, 2.0), 2)
                    })
        
        return edges

    def generate_workflow(self, target_depth: int) -> Dict[str, Any]:
        """
        Generate a single workflow with a specific target depth.
        
        Args:
            target_depth (int): Target maximum depth for the workflow (1-20).
            
        Returns:
            Dict[str, Any]: Complete workflow dictionary.
        """
        self.workflow_counter += 1
        
        # Generate nodes
        nodes = []
        nodes_per_depth = {}
        
        for depth in range(target_depth + 1):
            # Number of nodes at this depth: 1-5, increasing towards middle
            if depth == 0 or depth == target_depth:
                num_nodes = 1
            else:
                # Bias towards more nodes in the middle depths
                if depth < target_depth / 2:
                    num_nodes = random.randint(1, 3)
                else:
                    num_nodes = random.randint(2, 5)
            
            nodes_per_depth[depth] = num_nodes
            
            for i in range(num_nodes):
                node_id = f"node_{depth}_{i}"
                node = self._generate_node(node_id, depth, target_depth)
                nodes.append(node)
        
        # Generate edges
        edges = self._generate_edges(nodes, target_depth)
        
        # Calculate metadata
        total_nodes = len(nodes)
        total_edges = len(edges)
        complexity_score = sum(n["complexity"] for n in nodes) / total_nodes
        budget_cap = round(total_nodes * complexity_score * 1.5, 2)
        
        workflow = {
            "workflow_id": str(uuid.uuid4()),
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "max_depth": target_depth,
                "complexity_score": round(complexity_score, 2),
                "budget_cap": budget_cap,
                "generator_seed": self.seed,
                "is_valid": True  # All generated workflows are valid DAGs
            }
        }
        
        return workflow

    def generate_workflows(self, num_workflows: int = 500) -> List[Dict[str, Any]]:
        """
        Generate a collection of workflows with uniform depth distribution.
        
        Args:
            num_workflows (int): Total number of workflows to generate.
            
        Returns:
            List[Dict[str, Any]]: List of workflow dictionaries.
        """
        workflows = []
        
        # Ensure we generate at least 25 workflows per depth (1-20)
        # If num_workflows < 500, adjust to ensure coverage
        min_workflows_per_depth = 25
        depths = list(range(1, 21))
        
        # Calculate how many workflows per depth
        workflows_per_depth = max(min_workflows_per_depth, num_workflows // len(depths))
        
        for depth in depths:
            for _ in range(workflows_per_depth):
                workflow = self.generate_workflow(depth)
                workflows.append(workflow)
        
        # If we need more workflows, add them randomly
        while len(workflows) < num_workflows:
            depth = random.choice(depths)
            workflow = self.generate_workflow(depth)
            workflows.append(workflow)
        
        return workflows[:num_workflows]

    def save_workflows(self, workflows: List[Dict[str, Any]], output_dir: str) -> List[str]:
        """
        Save workflows to individual JSON files in the specified directory.
        
        Args:
            workflows (List[Dict[str, Any]]): List of workflow dictionaries.
            output_dir (str): Output directory path.
            
        Returns:
            List[str]: List of paths to saved files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        for workflow in workflows:
            filename = f"{workflow['workflow_id']}.json"
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(workflow, f, indent=2)
            
            saved_files.append(str(filepath))
        
        return saved_files

def main():
    """
    CLI entry point for generating synthetic workflows.
    
    Usage:
        python -m generators.synthetic_workflow [--num N] [--output DIR] [--seed S]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic workflows")
    parser.add_argument("--num", type=int, default=500, help="Number of workflows to generate")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    print(f"Generating {args.num} workflows with seed {args.seed}...")
    
    generator = SyntheticWorkflowGenerator(seed=args.seed)
    workflows = generator.generate_workflows(num_workflows=args.num)
    
    saved_files = generator.save_workflows(workflows, args.output)
    
    print(f"Generated {len(workflows)} workflows.")
    print(f"Saved to {args.output}: {len(saved_files)} files.")
    
    # Print summary statistics
    depths = [w["metadata"]["max_depth"] for w in workflows]
    depth_counts = {}
    for d in depths:
        depth_counts[d] = depth_counts.get(d, 0) + 1
    
    print("Depth distribution:")
    for d in sorted(depth_counts.keys()):
        print(f"  Depth {d}: {depth_counts[d]} workflows")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
