import random
from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx
from src.utils.config import Config
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MixedAgent(BaseAgent):
    """
    MixedAgent: Trains on mixed task domains randomly per generation.
    
    This agent implements the 'Mixed-task' condition where training instances
    from different domains (logic proofs, grid worlds) and rule sets are
    sampled randomly at each step, rather than in sequential blocks or
    co-evolving sub-populations.
    """

    def __init__(self, config: Config, seed: Optional[int] = None):
        super().__init__(config, seed)
        self.population: List[Dict[str, Any]] = []
        self.rule_sets: Dict[str, Any] = {}
        self.generation_count: int = 0
        self.evaluation_count: int = 0
        self.budget_exceeded = False
        
        # Initialize population with random rule sets
        self._initialize_population()

    def _initialize_population(self):
        """Initialize the agent's population with random rule sets."""
        logger.info("Initializing MixedAgent population...")
        # Create a population of rule sets based on config
        for i in range(self.config.population_size):
            rule_set_id = f"mixed_rule_set_{i}_{self.seed}"
            # Initialize with a mix of logic and grid rules
            self.rule_sets[rule_set_id] = {
                "id": rule_set_id,
                "logic_rules": self._generate_random_logic_rules(),
                "grid_rules": self._generate_random_grid_rules(),
                "fitness": 0.0,
                "age": 0
            }
            
            self.population.append({
                "rule_set_id": rule_set_id,
                "fitness": 0.0
            })

    def _generate_random_logic_rules(self) -> List[str]:
        """Generate a set of random valid logic rules."""
        # Using sympy symbols to create random valid implications
        p, q, r = symbols('p q r')
        rules = [
            Implies(p, q),
            Implies(q, r),
            And(p, q),
            Or(p, Not(q)),
            Implies(And(p, q), r)
        ]
        return [str(rule) for rule in rules]

    def _generate_random_grid_rules(self) -> List[str]:
        """Generate a set of random grid navigation rules."""
        # Representing grid rules as string constraints
        rules = [
            "avoid_red_cells",
            "diagonal_movement_allowed",
            "shortest_path_priority",
            "avoid_dead_ends"
        ]
        # Randomly select a subset
        return random.sample(rules, k=random.randint(2, len(rules)))

    def train(self, training_data: List[Dict[str, Any]], generations: int, budget: int) -> Dict[str, Any]:
        """
        Train the agent on mixed task domains.
        
        Args:
            training_data: List of training instances from all domains
            generations: Number of generations to train
            budget: Maximum number of rule evaluations allowed
        
        Returns:
            Dictionary containing training results and final state
        """
        logger.info(f"Starting MixedAgent training for {generations} generations with budget {budget}")
        
        if not training_data:
            logger.warning("No training data provided. Skipping training.")
            return self._get_training_result()

        # Shuffle training data to ensure random mixing
        shuffled_data = training_data.copy()
        random.shuffle(shuffled_data)
        
        data_index = 0
        total_evaluations = 0

        for gen in range(generations):
            self.generation_count = gen + 1
            logger.debug(f"Generation {gen + 1}/{generations}")
            
            # Sample a random batch of data for this generation
            batch_size = min(self.config.batch_size, len(shuffled_data))
            current_batch = random.sample(shuffled_data, batch_size)
            
            # Evaluate and update population
            batch_evaluations = 0
            for instance in current_batch:
                if total_evaluations >= budget:
                    self.budget_exceeded = True
                    logger.warning(f"Budget exceeded at generation {gen + 1}. Stopping training.")
                    break
                
                # Evaluate each rule set in the population against this instance
                for member in self.population:
                    rule_set_id = member["rule_set_id"]
                    rule_set = self.rule_sets[rule_set_id]
                    
                    # Evaluate logic rules if instance is logic-based
                    if instance.get("domain") == "logic":
                        score = self._evaluate_logic_rules(rule_set, instance)
                    # Evaluate grid rules if instance is grid-based
                    elif instance.get("domain") == "grid":
                        score = self._evaluate_grid_rules(rule_set, instance)
                    else:
                        score = 0.0
                    
                    # Update fitness
                    member["fitness"] = (member["fitness"] * 0.9) + (score * 0.1)
                    batch_evaluations += 1
                    total_evaluations += 1

            # Apply selection pressure and evolution
            self._evolve_population()
            
            # Log progress
            if (gen + 1) % 10 == 0:
                avg_fitness = sum(m["fitness"] for m in self.population) / len(self.population)
                logger.info(f"Gen {gen + 1}: Avg Fitness = {avg_fitness:.4f}, Evaluations = {total_evaluations}")

            if self.budget_exceeded:
                break

        self.evaluation_count = total_evaluations
        return self._get_training_result()

    def _evaluate_logic_rules(self, rule_set: Dict[str, Any], instance: Dict[str, Any]) -> float:
        """Evaluate logic rules against a logic instance."""
        try:
            instance_rules = instance.get("instance_data", {}).get("rules", [])
            target = instance.get("instance_data", {}).get("target")
            
            if not target:
                return 0.0
            
            # Check how many rules in the set contribute to proving the target
            # Simplified evaluation for demonstration
            matching_rules = 0
            for rule_str in rule_set["logic_rules"]:
                # In a real implementation, we would use sympy to check logical entailment
                # Here we do a string match for simplicity in this mixed agent
                if any(r in rule_str for r in instance_rules):
                    matching_rules += 1
            
            return matching_rules / max(len(rule_set["logic_rules"]), 1)
        except Exception as e:
            logger.warning(f"Error evaluating logic rules: {e}")
            return 0.0

    def _evaluate_grid_rules(self, rule_set: Dict[str, Any], instance: Dict[str, Any]) -> float:
        """Evaluate grid rules against a grid instance."""
        try:
            grid_rules = instance.get("instance_data", {}).get("constraints", [])
            
            if not grid_rules:
                return 0.0
            
            matching_rules = 0
            for rule_str in rule_set["grid_rules"]:
                if any(r in rule_str for r in grid_rules):
                    matching_rules += 1
            
            return matching_rules / max(len(rule_set["grid_rules"]), 1)
        except Exception as e:
            logger.warning(f"Error evaluating grid rules: {e}")
            return 0.0

    def _evolve_population(self):
        """Apply selection pressure and evolutionary operators."""
        # Sort by fitness
        self.population.sort(key=lambda x: x["fitness"], reverse=True)
        
        # Keep top 50% (selection pressure)
        keep_count = max(1, len(self.population) // 2)
        survivors = self.population[:keep_count]
        
        # Generate new members via mutation of survivors
        new_members = []
        for _ in range(len(self.population) - keep_count):
            parent = random.choice(survivors)
            parent_id = parent["rule_set_id"]
            parent_rules = self.rule_sets[parent_id]
            
            # Create mutated copy
            new_id = f"mutated_{parent_id}_{self.generation_count}_{random.randint(0, 9999)}"
            
            new_logic = parent_rules["logic_rules"].copy()
            new_grid = parent_rules["grid_rules"].copy()
            
            # Mutation: randomly add/remove rules
            if random.random() < 0.3 and len(new_logic) > 1:
                new_logic.pop(random.randint(0, len(new_logic)-1))
            if random.random() < 0.3:
                new_logic.extend(self._generate_random_logic_rules()[:1])
                
            if random.random() < 0.3 and len(new_grid) > 1:
                new_grid.pop(random.randint(0, len(new_grid)-1))
            if random.random() < 0.3:
                new_grid.extend(self._generate_random_grid_rules()[:1])
            
            self.rule_sets[new_id] = {
                "id": new_id,
                "logic_rules": new_logic,
                "grid_rules": new_grid,
                "fitness": 0.0,
                "age": 0
            }
            
            new_members.append({
                "rule_set_id": new_id,
                "fitness": 0.0
            })
        
        self.population = survivors + new_members

    def get_state(self) -> Dict[str, Any]:
        """Return the current state of the agent."""
        return {
            "population": self.population,
            "rule_sets": self.rule_sets,
            "generation_count": self.generation_count,
            "evaluation_count": self.evaluation_count,
            "agent_type": "MixedAgent",
            "seed": self.seed
        }

    def _get_training_result(self) -> Dict[str, Any]:
        """Generate a training result summary."""
        avg_fitness = sum(m["fitness"] for m in self.population) / len(self.population) if self.population else 0.0
        return {
            "generations_completed": self.generation_count,
            "total_evaluations": self.evaluation_count,
            "budget_exceeded": self.budget_exceeded,
            "final_avg_fitness": avg_fitness,
            "state": self.get_state()
        }

    def save_state(self, path: str):
        """Save agent state to a file."""
        state = self.get_state()
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info(f"Agent state saved to {path}")

    @classmethod
    def load_state(cls, path: str, config: Config) -> 'MixedAgent':
        """Load agent state from a file."""
        with open(path, 'r') as f:
            state = json.load(f)
        
        agent = cls(config, seed=state.get("seed"))
        agent.population = state["population"]
        agent.rule_sets = state["rule_sets"]
        agent.generation_count = state["generation_count"]
        agent.evaluation_count = state["evaluation_count"]
        agent.budget_exceeded = state.get("budget_exceeded", False)
        
        logger.info(f"Agent state loaded from {path}")
        return agent


def main():
    """Main entry point for MixedAgent testing/standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MixedAgent Training")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--data", type=str, default="data/generated_proofs.json", help="Path to training data")
    parser.add_argument("--generations", type=int, default=100, help="Number of generations")
    parser.add_argument("--budget", type=int, default=10000, help="Evaluation budget")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/results/mixed_agent_state.json", help="Output path")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    config = Config.load(args.config)
    config.seed = args.seed
    
    # Load training data (simplified for this example)
    try:
        with open(args.data, 'r') as f:
            training_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Training data file not found: {args.data}")
        return 1
    
    # Initialize agent
    agent = MixedAgent(config, seed=args.seed)
    
    # Train
    result = agent.train(training_data, args.generations, args.budget)
    
    # Save results
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Training complete. Results saved to {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
