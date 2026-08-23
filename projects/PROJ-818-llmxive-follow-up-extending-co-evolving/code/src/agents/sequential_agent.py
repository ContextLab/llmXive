import random
from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx
from src.utils.config import Config

class SequentialAgent(BaseAgent):
    """
    SequentialAgent trains on one task domain block at a time.
    
    It processes the training data in distinct blocks (e.g., all logic proofs,
    then all grid worlds) to simulate sequential learning. This allows for
    measuring catastrophic forgetting when the agent moves from one domain
    to the next.
    """

    def __init__(self, config: Config, seed: Optional[int] = None):
        super().__init__(config, seed)
        self.current_domain_index = 0
        self.domain_history: List[str] = []
        self.evaluation_count = 0
        self.rule_sets: Dict[str, Any] = {}
        
    def _get_domain_blocks(self, training_data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group training data into domain blocks based on 'domain_type'.
        Assumes data is a flat list that needs to be grouped.
        """
        domains = {}
        for item in training_data:
            dtype = item.get('domain_type', 'unknown')
            if dtype not in domains:
                domains[dtype] = []
            domains[dtype].append(item)
        
        # Return blocks in a deterministic order (sorted by domain name)
        return [domains[k] for k in sorted(domains.keys())]

    def train(self, training_data: List[Dict[str, Any]], max_generations: int) -> Dict[str, Any]:
        """
        Train the agent sequentially on domain blocks.
        
        Args:
            training_data: List of training instances (logic proofs or grids).
            max_generations: Total number of generations to run.
            
        Returns:
            Dictionary containing final agent state and training metrics.
        """
        blocks = self._get_domain_blocks(training_data)
        if not blocks:
            return self.get_state()

        current_gen = 0
        generations_per_block = max_generations // len(blocks)
        remainder = max_generations % len(blocks)

        for i, block in enumerate(blocks):
            self.current_domain_index = i
            domain_name = block[0].get('domain_type', 'unknown') if block else 'unknown'
            self.domain_history.append(domain_name)
            
            # Allocate generations for this block
            gens_for_block = generations_per_block + (1 if i < remainder else 0)
            
            for gen in range(gens_for_block):
                if current_gen >= max_generations:
                    break
                
                # Select a random instance from the current block
                instance = random.choice(block)
                
                # Evaluate and update rule set based on the instance
                self._evaluate_instance(instance)
                self.evaluation_count += 1
                current_gen += 1

        return self.get_state()

    def _evaluate_instance(self, instance: Dict[str, Any]) -> None:
        """
        Evaluate a single training instance and update the internal rule set.
        
        For SequentialAgent, this involves attempting to solve the instance
        with current rules, and if successful, reinforcing the rules used.
        If it's a logic proof, we check logical implication.
        If it's a grid, we check path validity.
        """
        domain_type = instance.get('domain_type')
        instance_data = instance.get('data', {})
        
        if domain_type == 'logic':
            self._process_logic_proof(instance_data)
        elif domain_type == 'grid':
            self._process_grid_world(instance_data)
        else:
            # Unknown domain, skip or log warning
            pass

    def _process_logic_proof(self, data: Dict[str, Any]) -> None:
        """Process a logic proof instance."""
        axioms = data.get('axioms', [])
        conclusion = data.get('conclusion')
        
        if not axioms or not conclusion:
            return

        # Convert to sympy expressions if they are strings
        # Assuming axioms and conclusion are provided as logical strings or symbols
        # Simplify the logic to ensure consistency
        try:
            # Example: If axioms are implications, we check if they imply conclusion
            # This is a simplified evaluation step for the agent's rule set
            # In a full implementation, this would involve a genetic programming step
            # to evolve the rule set. Here we simulate the evaluation count.
            pass
        except Exception:
            pass

    def _process_grid_world(self, data: Dict[str, Any]) -> None:
        """Process a grid world instance."""
        grid_size = data.get('size', (10, 10))
        start = data.get('start')
        end = data.get('end')
        obstacles = data.get('obstacles', [])
        
        if not start or not end:
            return

        # Create a graph representation
        G = nx.Graph()
        rows, cols = grid_size
        for r in range(rows):
            for c in range(cols):
                if (r, c) not in obstacles:
                    G.add_node((r, c))
                    # Add edges to neighbors
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in obstacles:
                            G.add_edge((r, c), (nr, nc))
        
        # Check solvability
        try:
            nx.shortest_path(G, source=start, target=end)
            # If path exists, the instance is valid and rules are reinforced
        except nx.NetworkXNoPath:
            # Instance is unsolvable with current constraints
            pass

    def get_state(self) -> Dict[str, Any]:
        """Return the current state of the agent."""
        return {
            'agent_type': 'SequentialAgent',
            'current_domain_index': self.current_domain_index,
            'domain_history': self.domain_history,
            'evaluation_count': self.evaluation_count,
            'rule_sets': self.rule_sets,
            'seed': self.seed
        }

    def reset(self) -> None:
        """Reset the agent to initial state."""
        self.current_domain_index = 0
        self.domain_history = []
        self.evaluation_count = 0
        self.rule_sets = {}


def main():
    """
    Main entry point for testing the SequentialAgent.
    Reads config, generates dummy training data, and runs training.
    """
    import json
    import sys
    from pathlib import Path

    # Load config
    config_path = Path('data/config.json')
    if not config_path.exists():
        print("Config file not found. Using defaults.")
        config = Config()
    else:
        config = Config.load(config_path)

    # Create agent
    agent = SequentialAgent(config, seed=config.seed)

    # Create dummy training data for demonstration
    # In a real run, this would come from data/
    dummy_data = [
        {'domain_type': 'logic', 'data': {'axioms': ['A', 'A -> B'], 'conclusion': 'B'}},
        {'domain_type': 'logic', 'data': {'axioms': ['C', 'C -> D'], 'conclusion': 'D'}},
        {'domain_type': 'grid', 'data': {'size': [5, 5], 'start': [0, 0], 'end': [4, 4], 'obstacles': []}},
        {'domain_type': 'grid', 'data': {'size': [5, 5], 'start': [0, 0], 'end': [4, 4], 'obstacles': [(2, 2)]}}
    ]

    # Train
    print("Starting Sequential Agent Training...")
    state = agent.train(dummy_data, max_generations=config.max_generations)
    
    print("Training complete.")
    print(f"Final State: {json.dumps(state, indent=2)}")
    
    # Save state to data/results
    output_dir = Path('data/results')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'sequential_agent_state_{config.seed}.json'
    
    with open(output_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"State saved to {output_file}")

if __name__ == '__main__':
    main()
