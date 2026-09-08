import random
from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx
from src.utils.config import Config
import json
from pathlib import Path
from datetime import datetime

class MixedAgent(BaseAgent):
    """
    MixedAgent: Trains on mixed task domains randomly per generation.
    
    This agent implements the "Mixed-task" condition where the agent is exposed
    to both logic proofs and grid-world tasks in a randomized interleaved order
    during the evolutionary training process. This prevents the agent from
    specializing on one domain before seeing the other, testing resilience
    against catastrophic forgetting in a continuous mixed stream.
    """

    def __init__(self, config: Config, seed: Optional[int] = None):
        super().__init__(config, seed)
        self.rule_sets: List[Dict[str, Any]] = []
        self.evaluation_count = 0
        self.training_history: List[Dict[str, Any]] = []
        self.current_domain = None
        
        # Initialize random state
        if seed is not None:
            random.seed(seed)

    def _load_training_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Load training data for both logic and grid domains.
        
        Returns:
            Tuple of (logic_proofs, grid_worlds)
        """
        data_path = Path(self.config.data_dir)
        
        # Load logic proofs
        logic_file = data_path / "logic_proofs.json"
        if logic_file.exists():
            with open(logic_file, 'r') as f:
                logic_proofs = json.load(f)
        else:
            raise FileNotFoundError(f"Logic proofs not found at {logic_file}")
        
        # Load grid worlds
        grid_file = data_path / "grid_worlds.json"
        if grid_file.exists():
            with open(grid_file, 'r') as f:
                grid_worlds = json.load(f)
        else:
            raise FileNotFoundError(f"Grid worlds not found at {grid_file}")
        
        return logic_proofs, grid_worlds

    def _evaluate_rule_set(self, rule_set: Dict[str, Any], task: Dict[str, Any]) -> bool:
        """
        Evaluate a rule set against a specific task (logic or grid).
        
        Args:
            rule_set: The rule set to evaluate
            task: The task instance to solve
            
        Returns:
            True if the rule set successfully solves the task, False otherwise
        """
        self.evaluation_count += 1
        
        task_type = task.get('type', 'unknown')
        
        if task_type == 'logic_proof':
            return self._evaluate_logic(rule_set, task)
        elif task_type == 'grid_world':
            return self._evaluate_grid(rule_set, task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _evaluate_logic(self, rule_set: Dict[str, Any], task: Dict[str, Any]) -> bool:
        """
        Evaluate rule set on a logic proof task.
        
        Args:
            rule_set: Dictionary containing 'rules' (list of sympy expressions)
            task: Dictionary containing 'premises' and 'conclusion'
            
        Returns:
            True if the conclusion can be derived from premises using the rules
        """
        rules = rule_set.get('rules', [])
        premises = task.get('premises', [])
        conclusion = task.get('conclusion')
        
        if not conclusion or not premises:
            return False
        
        try:
            # Parse premises and conclusion if they are strings
            if isinstance(conclusion, str):
                # Simplify the conclusion expression
                concl_expr = simplify_logic(conclusion)
            else:
                concl_expr = conclusion
            
            # Start with premises as known truths
            current_state = And(*premises) if premises else And()
            
            # Apply rules iteratively to derive new facts
            max_iterations = 10
            for _ in range(max_iterations):
                new_facts = []
                for rule in rules:
                    if isinstance(rule, str):
                        rule_expr = simplify_logic(rule)
                    else:
                        rule_expr = rule
                        
                    # Check if rule antecedent is satisfied by current state
                    if isinstance(rule_expr, Implies):
                        antecedent = rule_expr.args[0]
                        consequent = rule_expr.args[1]
                        
                        # Check if antecedent is implied by current state
                        # Simplify: (current_state AND antecedent) == current_state
                        combined = And(current_state, antecedent)
                        if simplify_logic(combined) == simplify_logic(current_state):
                            new_facts.append(consequent)
                
                if not new_facts:
                    break
                
                # Add new facts to current state
                current_state = And(current_state, *new_facts)
            
            # Check if conclusion is implied by final state
            final_check = And(current_state, Not(concl_expr))
            if simplify_logic(final_check) == False:
                return True
                
            return False
            
        except Exception as e:
            # Log error but return False for failed evaluation
            print(f"Logic evaluation error: {e}")
            return False

    def _evaluate_grid(self, rule_set: Dict[str, Any], task: Dict[str, Any]) -> bool:
        """
        Evaluate rule set on a grid world navigation task.
        
        Args:
            rule_set: Dictionary containing 'rules' (navigation constraints)
            task: Dictionary containing 'grid', 'start', 'goal'
            
        Returns:
            True if a valid path exists from start to goal following rules
        """
        rules = rule_set.get('rules', [])
        grid_data = task.get('grid', {})
        start = task.get('start')
        goal = task.get('goal')
        
        if not all([grid_data, start, goal]):
            return False
        
        try:
            # Reconstruct grid graph
            grid_size = grid_data.get('size', (5, 5))
            obstacles = grid_data.get('obstacles', [])
            
            G = nx.DiGraph()
            rows, cols = grid_size
            
            # Create nodes
            for r in range(rows):
                for c in range(cols):
                    if (r, c) not in obstacles:
                        G.add_node((r, c))
            
            # Add edges based on movement rules
            for r in range(rows):
                for c in range(cols):
                    if (r, c) not in obstacles:
                        # Check all 4 directions
                        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < rows and 0 <= nc < cols:
                                if (nr, nc) not in obstacles:
                                    # Check if edge violates any rules
                                    if self._check_grid_rules(G, (r, c), (nr, nc), rules):
                                        G.add_edge((r, c), (nr, nc))
            
            # Check if path exists
            if start in G and goal in G:
                try:
                    path = nx.shortest_path(G, source=start, target=goal)
                    return True
                except nx.NetworkXNoPath:
                    return False
            return False
            
        except Exception as e:
            print(f"Grid evaluation error: {e}")
            return False

    def _check_grid_rules(self, G: nx.DiGraph, current: Tuple[int, int], next_node: Tuple[int, int], rules: List[str]) -> bool:
        """
        Check if moving from current to next_node violates any rules.
        
        Args:
            G: The grid graph
            current: Current position
            next_node: Target position
            rules: List of rule strings
            
        Returns:
            True if move is valid, False if it violates a rule
        """
        for rule in rules:
            # Simple rule checking logic
            # In a real implementation, this would parse and evaluate rule expressions
            if isinstance(rule, str):
                # Example: "avoid_red" would check if next_node is a red cell
                if "avoid" in rule.lower():
                    # Placeholder: assume no red cells unless specified in task
                    pass
            else:
                # Assume valid if not a string
                pass
        return True

    def _generate_offspring(self, parent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an offspring rule set from a parent via mutation.
        
        Args:
            parent: Parent rule set dictionary
            
        Returns:
            Mutated offspring rule set
        """
        offspring = {
            'rules': [],
            'fitness': 0.0,
            'generation': parent.get('generation', 0) + 1
        }
        
        # Mutate rules
        for rule in parent.get('rules', []):
            # 10% chance to mutate a rule
            if random.random() < 0.1:
                # Simple mutation: add a random symbol or negate
                if isinstance(rule, str):
                    # Add a random variable or operator
                    new_var = f"X{random.randint(0, 99)}"
                    if random.random() > 0.5:
                        mutated = f"({rule} AND {new_var})"
                    else:
                        mutated = f"(NOT {new_var} OR {rule})"
                    offspring['rules'].append(mutated)
                else:
                    offspring['rules'].append(rule)
            else:
                offspring['rules'].append(rule)
        
        # 20% chance to add a new random rule
        if random.random() < 0.2:
            new_var = f"X{random.randint(0, 99)}"
            offspring['rules'].append(new_var)
        
        return offspring

    def _calculate_fitness(self, rule_set: Dict[str, Any], tasks: List[Dict[str, Any]]) -> float:
        """
        Calculate fitness of a rule set on a batch of tasks.
        
        Args:
            rule_set: The rule set to evaluate
            tasks: List of tasks to evaluate on
            
        Returns:
            Fitness score (0.0 to 1.0)
        """
        if not tasks:
            return 0.0
        
        correct = 0
        for task in tasks:
            if self._evaluate_rule_set(rule_set, task):
                correct += 1
        
        return correct / len(tasks)

    def train(self, num_generations: int, population_size: int, batch_size: int) -> Dict[str, Any]:
        """
        Train the mixed agent over multiple generations.
        
        This method implements the mixed-task training loop where tasks are
        randomly sampled from both logic and grid domains for each generation.
        
        Args:
            num_generations: Number of evolutionary generations to run
            population_size: Size of the population per generation
            batch_size: Number of tasks to evaluate per individual per generation
            
        Returns:
            Dictionary containing training results and final best rule set
        """
        # Load data
        logic_proofs, grid_worlds = self._load_training_data()
        
        # Prepare mixed task pool
        mixed_tasks = []
        for proof in logic_proofs:
            mixed_tasks.append({'type': 'logic_proof', 'data': proof})
        for grid in grid_worlds:
            mixed_tasks.append({'type': 'grid_world', 'data': grid})
        
        if not mixed_tasks:
            raise ValueError("No mixed tasks available for training")
        
        # Initialize population
        population = []
        for _ in range(population_size):
            # Create initial random rule set
            initial_rules = []
            num_initial_rules = random.randint(2, 5)
            for _ in range(num_initial_rules):
                var = f"X{random.randint(0, 99)}"
                initial_rules.append(var)
            
            population.append({
                'rules': initial_rules,
                'fitness': 0.0,
                'generation': 0
            })
        
        best_rule_set = None
        best_fitness = -1.0
        
        # Evolutionary loop
        for gen in range(num_generations):
            # Shuffle tasks for this generation
            random.shuffle(mixed_tasks)
            
            # Evaluate population
            for individual in population:
                # Sample tasks for this individual
                task_sample = mixed_tasks[:batch_size] if len(mixed_tasks) >= batch_size else mixed_tasks
                fitness = self._calculate_fitness(individual, [t['data'] for t in task_sample])
                individual['fitness'] = fitness
                
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_rule_set = individual.copy()
            
            # Selection: Keep top 50%
            population.sort(key=lambda x: x['fitness'], reverse=True)
            survivors = population[:population_size // 2]
            
            # Reproduction: Create offspring
            new_population = list(survivors)
            while len(new_population) < population_size:
                # Tournament selection
                parent1 = random.choice(survivors)
                parent2 = random.choice(survivors)
                
                # Crossover (simple: take rules from one parent)
                if random.random() > 0.5:
                    child = self._generate_offspring(parent1)
                else:
                    child = self._generate_offspring(parent2)
                
                child['generation'] = gen + 1
                new_population.append(child)
            
            population = new_population
            
            # Record history
            avg_fitness = sum(ind['fitness'] for ind in population) / len(population)
            self.training_history.append({
                'generation': gen,
                'average_fitness': avg_fitness,
                'best_fitness': best_fitness,
                'evaluation_count': self.evaluation_count
            })
        
        # Final result
        result = {
            'best_rule_set': best_rule_set,
            'best_fitness': best_fitness,
            'total_generations': num_generations,
            'total_evaluations': self.evaluation_count,
            'training_history': self.training_history,
            'config': {
                'population_size': population_size,
                'batch_size': batch_size,
                'num_generations': num_generations
            }
        }
        
        return result

    def save_state(self, output_path: str):
        """Save agent state to a file."""
        state = {
            'rule_sets': self.rule_sets,
            'evaluation_count': self.evaluation_count,
            'training_history': self.training_history,
            'timestamp': datetime.now().isoformat()
        }
        with open(output_path, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, input_path: str):
        """Load agent state from a file."""
        with open(input_path, 'r') as f:
            state = json.load(f)
        self.rule_sets = state.get('rule_sets', [])
        self.evaluation_count = state.get('evaluation_count', 0)
        self.training_history = state.get('training_history', [])

def main():
    """
    Main entry point for MixedAgent training.
    
    This function loads configuration, instantiates the MixedAgent,
    runs the training loop, and saves results to disk.
    """
    import sys
    from src.utils.config import load_config
    
    # Load configuration
    config = load_config()
    
    # Set seed for reproducibility
    if config.seed is not None:
        random.seed(config.seed)
    
    # Initialize agent
    agent = MixedAgent(config, seed=config.seed)
    
    # Run training
    print(f"Starting MixedAgent training with seed {config.seed}")
    print(f"Population size: {config.population_size}")
    print(f"Generations: {config.num_generations}")
    print(f"Batch size: {config.batch_size}")
    
    results = agent.train(
        num_generations=config.num_generations,
        population_size=config.population_size,
        batch_size=config.batch_size
    )
    
    # Save results
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = output_dir / f"mixed_agent_results_{config.seed}.json"
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Training complete. Results saved to {result_file}")
    print(f"Best fitness: {results['best_fitness']:.4f}")
    print(f"Total evaluations: {results['total_evaluations']}")
    
    return results

if __name__ == "__main__":
    main()