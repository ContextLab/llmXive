"""
MixedAgent: Trains on mixed task domains randomly per generation.

Implements the Mixed-task condition for User Story 2.
Unlike SequentialAgent, this agent draws training instances from a mixed pool
of both Logic Proofs and Grid Worlds at every step, ensuring no temporal
separation of domains.
"""
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
    Agent that trains on a random mix of logic proofs and grid worlds.

    This agent maintains a single population of rules that are evaluated
    against both task types indiscriminately during the training loop.
    """

    def __init__(self, config: Config, agent_id: str = "mixed_0"):
        """
        Initialize the MixedAgent.

        Args:
            config: The configuration object containing seeds and hyperparameters.
            agent_id: Unique identifier for this agent instance.
        """
        super().__init__(config, agent_id)
        self.logic_gen = LogicProofGenerator(config)
        self.grid_gen = GridWorldGenerator(config)
        
        # Initialize parity checker for this agent
        self.parity_checker = ParityChecker(agent_id)
        
        # State tracking
        self.current_rules: List[Dict[str, Any]] = []
        self.evaluation_count: int = 0
        self.generation_count: int = 0
        self.history: List[Dict[str, Any]] = []

    def _initialize_population(self, population_size: int) -> List[Dict[str, Any]]:
        """
        Initialize a population of random rule-sets.
        
        Args:
            population_size: Number of individuals in the population.
            
        Returns:
            List of rule-set dictionaries.
        """
        population = []
        for _ in range(population_size):
            # Generate a random rule set for logic (using sympy symbols)
            # and a random heuristic for grids
            rule_set = {
                "logic_rules": self._generate_random_logic_rules(),
                "grid_heuristics": self._generate_random_grid_heuristics(),
                "fitness": 0.0,
                "age": 0
            }
            population.append(rule_set)
        return population

    def _generate_random_logic_rules(self) -> Dict[str, Any]:
        """Generate a random set of logical implications."""
        # Create 3-5 random symbols
        num_symbols = random.randint(3, 6)
        sym_names = [f"p{i}" for i in range(num_symbols)]
        syms = symbols(sym_names)
        
        rules = []
        for _ in range(random.randint(1, 3)):
            # Create a random implication: (A & B) -> C
            antecedents = random.sample(list(syms), k=random.randint(1, 2))
            consequent = random.choice(list(syms))
            if len(antecedents) > 1:
                antecedent_expr = And(*antecedents)
            else:
                antecedent_expr = antecedents[0]
            
            implication = Implies(antecedent_expr, consequent)
            rules.append({
                "expr": implication,
                "simplified": simplify_logic(implication)
            })
        
        return {"rules": rules, "symbols": sym_names}

    def _generate_random_grid_heuristics(self) -> List[str]:
        """Generate a random set of grid navigation heuristics."""
        possible_heuristics = [
            "avoid_red", "avoid_blue", "prefer_diagonal", 
            "shortest_path", "avoid_corners", "follow_wall"
        ]
        num_heuristics = random.randint(1, 3)
        return random.sample(possible_heuristics, num_heuristics)

    def _generate_mixed_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        Generate a batch of mixed training instances (logic + grid).
        
        Args:
            batch_size: Total number of instances to generate.
            
        Returns:
            List of instance dictionaries with 'type' ('logic' or 'grid') and data.
        """
        batch = []
        for _ in range(batch_size):
            if random.random() < 0.5:
                # Generate a logic proof instance
                proof_data = self.logic_gen.generate_proof()
                batch.append({
                    "type": "logic",
                    "data": proof_data,
                    "domain": "propositional_logic"
                })
            else:
                # Generate a grid world instance
                grid_data = self.grid_gen.generate_grid()
                batch.append({
                    "type": "grid",
                    "data": grid_data,
                    "domain": "grid_navigation"
                })
        return batch

    def _evaluate_individual(self, individual: Dict[str, Any], instance: Dict[str, Any]) -> float:
        """
        Evaluate a single individual on a single instance.
        
        Args:
            individual: The rule-set to evaluate.
            instance: The task instance (logic or grid).
            
        Returns:
            Fitness score (0.0 to 1.0).
        """
        score = 0.0
        instance_type = instance["type"]
        
        if instance_type == "logic":
            # Evaluate logic rules against the proof
            logic_data = instance["data"]
            target = logic_data.get("target")
            premises = logic_data.get("premises", [])
            
            # Check if individual's rules can derive the target
            # Simplified evaluation: check rule overlap and validity
            valid_derivations = 0
            total_checks = 0
            
            for rule in individual["logic_rules"]["rules"]:
                simplified_rule = rule["simplified"]
                # Try to verify if the rule helps in derivation
                # In a real scenario, this would involve a theorem prover
                # Here we use a heuristic based on symbol overlap
                rule_symbols = list(simplified_rule.free_symbols)
                target_symbols = list(target.free_symbols)
                
                if any(s in target_symbols for s in rule_symbols):
                    valid_derivations += 1
                total_checks += 1
            
            if total_checks > 0:
                score = min(1.0, valid_derivations / total_checks)
        
        elif instance_type == "grid":
            # Evaluate grid heuristics
            grid_data = instance["data"]
            solution_length = grid_data.get("solution_length", 0)
            grid_size = grid_data.get("size", 0)
            
            # Heuristic score based on rule adherence
            heuristic_count = len(individual["grid_heuristics"])
            # Simplified: assume more heuristics = better coverage, capped at 1.0
            score = min(1.0, heuristic_count / 3.0)
            
            # Bonus if solution is found (simulated)
            if solution_length > 0:
                score = min(1.0, score + 0.1)
        
        return score

    def train_generation(self, batch_size: int = 10, generations: int = 1) -> Dict[str, Any]:
        """
        Execute one or more generations of training.
        
        Args:
            batch_size: Number of instances per generation.
            generations: Number of generations to run.
            
        Returns:
            Training results dictionary.
        """
        # Initialize population if empty
        if not self.current_rules:
            self.current_rules = self._initialize_population(self.config.population_size)
        
        results = {
            "agent_id": self.agent_id,
            "generation_start": self.generation_count,
            "instances_evaluated": 0,
            "fitness_history": []
        }

        for gen in range(generations):
            # 1. Generate mixed batch
            batch = self._generate_mixed_batch(batch_size)
            
            # 2. Evaluate all individuals on the batch
            for individual in self.current_rules:
                total_fitness = 0.0
                count = 0
                for instance in batch:
                    # Increment evaluation counter
                    self.evaluation_count += 1
                    self.parity_checker.record_evaluation("mixed", instance["domain"])
                    
                    fitness = self._evaluate_individual(individual, instance)
                    total_fitness += fitness
                    count += 1
                
                if count > 0:
                    individual["fitness"] = total_fitness / count
                individual["age"] += 1

            # 3. Selection and Evolution (Simple tournament + mutation)
            self._evolve_population()
            
            # 4. Record history
            avg_fitness = sum(ind["fitness"] for ind in self.current_rules) / len(self.current_rules)
            self.history.append({
                "generation": self.generation_count,
                "avg_fitness": avg_fitness,
                "max_fitness": max(ind["fitness"] for ind in self.current_rules),
                "evaluations": self.evaluation_count
            })
            
            results["fitness_history"].append(avg_fitness)
            self.generation_count += 1

        results["generation_end"] = self.generation_count
        results["total_evaluations"] = self.evaluation_count
        results["final_population"] = self.current_rules
        
        # Update parity stats
        stats = self.parity_checker.get_stats()
        results["parity_stats"] = stats.to_dict() if hasattr(stats, 'to_dict') else stats

        return results

    def _evolve_population(self) -> None:
        """Perform selection and mutation to evolve the population."""
        # Tournament selection
        tournament_size = 3
        new_population = []
        
        for _ in range(self.config.population_size):
            # Select best from tournament
            candidates = random.sample(self.current_rules, tournament_size)
            winner = max(candidates, key=lambda x: x["fitness"])
            new_population.append(winner.copy())
        
        # Mutation
        for individual in new_population:
            if random.random() < self.config.mutation_rate:
                # Mutate logic rules
                if random.random() < 0.5:
                    individual["logic_rules"] = self._generate_random_logic_rules()
                # Mutate grid heuristics
                if random.random() < 0.5:
                    individual["grid_heuristics"] = self._generate_random_grid_heuristics()
            
            individual["age"] = 0 # Reset age for new offspring

        self.current_rules = new_population

    def get_state(self) -> Dict[str, Any]:
        """Return the current state of the agent for checkpointing."""
        return {
            "agent_id": self.agent_id,
            "type": "mixed",
            "generation_count": self.generation_count,
            "evaluation_count": self.evaluation_count,
            "population": self.current_rules,
            "history": self.history
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """Load a previously saved state."""
        if state.get("type") != "mixed":
            raise ValueError(f"State type '{state.get('type')}' does not match MixedAgent")
        
        self.agent_id = state["agent_id"]
        self.generation_count = state["generation_count"]
        self.evaluation_count = state["evaluation_count"]
        self.current_rules = state["population"]
        self.history = state["history"]


def main():
    """
    Entry point for running MixedAgent training directly.
    Usage: python -m src.agents.mixed_agent --config path/to/config.json
    """
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Run MixedAgent Training")
    parser.add_argument("--config", type=str, required=True, help="Path to config file")
    parser.add_argument("--output", type=str, default="data/results/mixed_training.json", help="Output path")
    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        config_dict = json.load(f)
    
    config = Config(**config_dict)

    # Initialize agent
    agent = MixedAgent(config, agent_id="mixed_main")

    # Run training
    print(f"Starting MixedAgent training with {config.population_size} population...")
    result = agent.train_generation(
        batch_size=config.batch_size, 
        generations=config.generations
    )

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"Training complete. Results saved to {output_path}")
    print(f"Total evaluations: {result['total_evaluations']}")
    print(f"Final avg fitness: {result['fitness_history'][-1]:.4f}")

if __name__ == "__main__":
    main()