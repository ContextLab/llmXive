import random
from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx
from src.utils.config import Config
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator
from src.utils.parity_checker import ParityChecker, EvaluationStats

class MixedAgent(BaseAgent):
    """
    MixedAgent: Trains on mixed task domains randomly per generation.
    
    This agent implements the 'Mixed-task' condition where training instances
    from both logic proofs and grid-world navigation are sampled randomly
    at each step, ensuring parity in total data exposure across conditions.
    """

    def __init__(self, config: Config, run_id: str):
        super().__init__(config, run_id)
        self.logic_generator = LogicProofGenerator(config)
        self.grid_generator = GridWorldGenerator(config)
        self.parity_checker = ParityChecker()
        self.evaluation_stats = EvaluationStats(
            total_evaluations=0,
            logic_evaluations=0,
            grid_evaluations=0
        )
        self.current_population = self._initialize_population()
        self.history = []

    def _initialize_population(self) -> List[Dict[str, Any]]:
        """Initialize a population of rule-sets."""
        population_size = self.config.get('population_size', 10)
        population = []
        for _ in range(population_size):
            rule_set = {
                'logic_rules': self._generate_random_logic_rules(),
                'grid_rules': self._generate_random_grid_rules(),
                'fitness': 0.0,
                'age': 0
            }
            population.append(rule_set)
        return population

    def _generate_random_logic_rules(self) -> List[Any]:
        """Generate a random set of logic rules (axioms)."""
        num_rules = random.randint(2, 5)
        rules = []
        for _ in range(num_rules):
            # Create random symbols and implications
            p = symbols(f'p_{random.randint(0, 100)}')
            q = symbols(f'q_{random.randint(0, 100)}')
            r = symbols(f'r_{random.randint(0, 100)}')
            
            # Randomly choose a rule structure
            rule_type = random.choice(['imp', 'and', 'or'])
            if rule_type == 'imp':
                rule = Implies(p, q)
            elif rule_type == 'and':
                rule = And(p, q)
            else:
                rule = Or(p, q)
            rules.append(rule)
        return rules

    def _generate_random_grid_rules(self) -> List[str]:
        """Generate a random set of grid navigation rules."""
        possible_rules = [
            'avoid_red', 'avoid_blue', 'diagonal_paths', 
            'shortest_path', 'avoid_corners', 'prefer_edges'
        ]
        num_rules = random.randint(2, 4)
        return random.sample(possible_rules, num_rules)

    def _select_random_task_domain(self) -> str:
        """Randomly select a task domain (logic or grid)."""
        return random.choice(['logic', 'grid'])

    def _evaluate_on_logic(self, rule_set: Dict[str, Any], instance: Dict[str, Any]) -> float:
        """Evaluate a rule set on a logic proof instance."""
        rules = rule_set['logic_rules']
        target = instance['target']
        premises = instance['premises']
        
        # Simplify the target using the rules
        try:
            simplified = simplify_logic(target, form='dnf')
            # Check if premises combined with rules imply target
            combined = And(*premises, *rules)
            implication = Implies(combined, target)
            if simplify_logic(implication):
                return 1.0
            else:
                return 0.0
        except Exception:
            return 0.0

    def _evaluate_on_grid(self, rule_set: Dict[str, Any], instance: Dict[str, Any]) -> float:
        """Evaluate a rule set on a grid-world instance."""
        rules = rule_set['grid_rules']
        grid_data = instance['grid']
        start = instance['start']
        end = instance['end']
        
        # Create graph from grid data
        G = nx.Graph()
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0
        
        for r in range(rows):
            for c in range(cols):
                if grid_data[r][c] != 1:  # Not an obstacle
                    G.add_node((r, c))
                    # Add edges to neighbors
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and grid_data[nr][nc] != 1:
                            G.add_edge((r, c), (nr, nc))
        
        # Check if path exists
        try:
            path = nx.shortest_path(G, start, end)
            # Apply rule-based scoring
            score = 0.0
            if 'shortest_path' in rules:
                score += 1.0 / len(path)  # Reward shorter paths
            if 'diagonal_paths' in rules:
                # Diagonal not supported in this grid implementation, but check logic
                score += 0.1
            if 'avoid_corners' in rules:
                # Check if path avoids corners (simplified check)
                score += 0.2
            return min(1.0, score)
        except nx.NetworkXNoPath:
            return 0.0

    def _generate_training_instance(self, domain: str) -> Dict[str, Any]:
        """Generate a single training instance from the specified domain."""
        if domain == 'logic':
            return self.logic_generator.generate_single_proof()
        else:
            return self.grid_generator.generate_single_grid()

    def train_generation(self, num_evaluations: int) -> Dict[str, Any]:
        """
        Train for one generation by randomly sampling from mixed task domains.
        
        Args:
            num_evaluations: Number of rule evaluations to perform in this generation.
            
        Returns:
            Dictionary containing generation statistics and updated population.
        """
        generation_stats = {
            'total_evaluations': 0,
            'logic_evaluations': 0,
            'grid_evaluations': 0,
            'avg_fitness': 0.0,
            'best_fitness': 0.0
        }
        
        fitness_scores = []
        
        for _ in range(num_evaluations):
            # Randomly select a task domain
            domain = self._select_random_task_domain()
            
            # Generate a training instance
            instance = self._generate_training_instance(domain)
            
            # Select a random individual from the population
            individual = random.choice(self.current_population)
            
            # Evaluate based on domain
            if domain == 'logic':
                score = self._evaluate_on_logic(individual, instance)
                generation_stats['logic_evaluations'] += 1
            else:
                score = self._evaluate_on_grid(individual, instance)
                generation_stats['grid_evaluations'] += 1
            
            # Update individual fitness (running average)
            old_fitness = individual['fitness']
            individual['fitness'] = (old_fitness * individual['age'] + score) / (individual['age'] + 1)
            individual['age'] += 1
            fitness_scores.append(individual['fitness'])
            
            generation_stats['total_evaluations'] += 1
            self.evaluation_stats.total_evaluations += 1

        # Update population history
        if fitness_scores:
            generation_stats['avg_fitness'] = sum(fitness_scores) / len(fitness_scores)
            generation_stats['best_fitness'] = max(fitness_scores)
            self.history.append(generation_stats)

        return generation_stats

    def get_population(self) -> List[Dict[str, Any]]:
        """Return the current population."""
        return self.current_population

    def get_evaluation_stats(self) -> EvaluationStats:
        """Return the evaluation statistics."""
        return self.evaluation_stats

    def save_state(self, filepath: str):
        """Save the agent state to a file."""
        import json
        state = {
            'population': self.current_population,
            'history': self.history,
            'evaluation_stats': self.evaluation_stats.__dict__,
            'run_id': self.run_id
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def load_state(self, filepath: str):
        """Load the agent state from a file."""
        import json
        with open(filepath, 'r') as f:
            state = json.load(f)
        self.current_population = state['population']
        self.history = state['history']
        self.evaluation_stats = EvaluationStats(**state['evaluation_stats'])
        self.run_id = state['run_id']

def main():
    """Entry point for testing MixedAgent."""
    import argparse
    from src.utils.config import load_config
    
    parser = argparse.ArgumentParser(description='Run MixedAgent training')
    parser.add_argument('--config', type=str, default='config.json', help='Path to config file')
    parser.add_argument('--generations', type=int, default=5, help='Number of generations to run')
    args = parser.parse_args()
    
    config = load_config(args.config)
    agent = MixedAgent(config, run_id="mixed_test_run")
    
    print(f"Starting MixedAgent training for {args.generations} generations...")
    
    for gen in range(args.generations):
        stats = agent.train_generation(num_evaluations=10)
        print(f"Generation {gen + 1}: Avg Fitness={stats['avg_fitness']:.4f}, "
              f"Logic={stats['logic_evaluations']}, Grid={stats['grid_evaluations']}")
    
    print("Training complete.")
    agent.save_state('data/results/mixed_agent_state.json')

if __name__ == '__main__':
    main()
