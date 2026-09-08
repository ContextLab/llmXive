import random
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict
from sympy import simplify_logic, symbols, Implies, And, Or, Not, Symbol
from .base_agent import BaseAgent
from src.utils.config import Config

class CoevolvingAgent(BaseAgent):
    """
    Co-evolving Agent that manages sub-populations for different task domains
    and executes bidirectional rule-set exchanges at every generation step.
    
    Implements selection pressure to discard non-performing rule-sets to prevent
    population collapse (T021).
    """

    def __init__(self, config: Config, task_domains: List[str]):
        """
        Initialize the co-evolving agent.
        
        Args:
            config: Configuration object containing seeds and population parameters.
            task_domains: List of task domain identifiers (e.g., ['logic', 'grid']).
        """
        super().__init__(config)
        self.task_domains = task_domains
        self.sub_populations: Dict[str, List[Dict[str, Any]]] = {
            domain: [] for domain in task_domains
        }
        self.exchange_history: List[Dict[str, Any]] = []
        self.generation_count = 0
        
        # Selection pressure parameters (configurable)
        self.selection_pressure_threshold = config.get('selection_pressure_threshold', 0.1)
        self.min_population_size = config.get('min_population_size', 5)
        self.elite_count = config.get('elite_count', 2)

    def _initialize_population(self, domain: str, count: int) -> List[Dict[str, Any]]:
        """Initialize a random population for a specific domain."""
        population = []
        for _ in range(count):
            rule_set = self._generate_random_rule_set(domain)
            population.append({
                'rules': rule_set,
                'fitness': 0.0,
                'age': 0,
                'id': f"{domain}_{len(population)}"
            })
        return population

    def _generate_random_rule_set(self, domain: str) -> List[str]:
        """Generate a random rule set for a specific domain."""
        # Simplified rule generation for demonstration
        # In a real implementation, this would use the domain-specific generators
        if domain == 'logic':
            # Generate random propositional logic rules
            n_rules = random.randint(2, 5)
            rules = []
            for i in range(n_rules):
                vars = [f'x{j}' for j in range(random.randint(2, 4))]
                rule = self._random_logic_rule(vars)
                rules.append(rule)
            return rules
        elif domain == 'grid':
            # Generate random grid navigation rules
            n_rules = random.randint(2, 4)
            rules = []
            rule_types = ['avoid_red', 'diagonal', 'shortest_path', 'avoid_blue']
            for _ in range(n_rules):
                rules.append(random.choice(rule_types))
            return rules
        else:
            return [f"random_rule_{i}" for i in range(random.randint(2, 3))]

    def _random_logic_rule(self, variables: List[str]) -> str:
        """Generate a random propositional logic rule."""
        if len(variables) < 2:
            return f"{variables[0]} -> {variables[0]}"
        
        op = random.choice(['and', 'or', 'implies'])
        if op == 'and':
            return f"({variables[0]} & {variables[1]})"
        elif op == 'or':
            return f"({variables[0]} | {variables[1]})"
        else:
            return f"({variables[0]} -> {variables[1]})"

    def evaluate_population(self, domain: str, test_instances: List[Dict[str, Any]]) -> None:
        """
        Evaluate all individuals in a sub-population against test instances.
        
        Args:
            domain: The task domain to evaluate.
            test_instances: List of test instances for evaluation.
        """
        if domain not in self.sub_populations:
            raise ValueError(f"Unknown domain: {domain}")
        
        for individual in self.sub_populations[domain]:
            score = self._evaluate_individual(individual, domain, test_instances)
            individual['fitness'] = score
            individual['age'] += 1

    def _evaluate_individual(self, individual: Dict[str, Any], domain: str, 
                             test_instances: List[Dict[str, Any]]) -> float:
        """
        Evaluate a single individual against test instances.
        
        Returns:
            float: Fitness score (0.0 to 1.0)
        """
        if not test_instances:
            return 0.0
        
        correct = 0
        total = len(test_instances)
        
        for instance in test_instances:
            if self._apply_rules(individual['rules'], instance, domain):
                correct += 1
        
        return correct / total if total > 0 else 0.0

    def _apply_rules(self, rules: List[str], instance: Dict[str, Any], domain: str) -> bool:
        """Apply a set of rules to an instance and return the result."""
        # Simplified rule application for demonstration
        # In a real implementation, this would parse and evaluate the rules
        if domain == 'logic':
            # For logic, we'd evaluate the propositional formulas
            return random.choice([True, False])  # Placeholder
        elif domain == 'grid':
            # For grids, we'd check path validity
            return random.choice([True, False])  # Placeholder
        else:
            return random.choice([True, False])

    def apply_selection_pressure(self) -> Dict[str, int]:
        """
        T021: Apply selection pressure to discard non-performing rule-sets.
        
        This method prevents population collapse by:
        1. Removing low-fitness individuals below a threshold
        2. Ensuring minimum population size is maintained
        3. Preserving elite individuals
        
        Returns:
            Dict[str, int]: Number of individuals removed per domain
        """
        removals = {}
        
        for domain, population in self.sub_populations.items():
            if not population:
                removals[domain] = 0
                continue
            
            # Sort by fitness (descending)
            population.sort(key=lambda x: x['fitness'], reverse=True)
            
            # Identify elite individuals to preserve
            elite_count = min(self.elite_count, len(population))
            elites = population[:elite_count]
            
            # Filter out low-performing individuals
            threshold = self.selection_pressure_threshold
            surviving = [ind for ind in population if ind['fitness'] >= threshold]
            
            # Ensure minimum population size
            if len(surviving) < self.min_population_size:
                # Keep at least the minimum (including elites)
                surviving = list(elites) + surviving[len(elites):self.min_population_size]
                # If still too small, we keep what we have to avoid collapse
                if len(surviving) < self.min_population_size:
                    surviving = population[:self.min_population_size]
            
            # Remove duplicates (elites might be in surviving)
            surviving = list({ind['id']: ind for ind in surviving}.values())
            
            removed_count = len(population) - len(surviving)
            removals[domain] = removed_count
            
            # Update population
            self.sub_populations[domain] = surviving
            
            # Log selection event
            self.exchange_history.append({
                'generation': self.generation_count,
                'domain': domain,
                'action': 'selection_pressure',
                'removed': removed_count,
                'remaining': len(surviving),
                'avg_fitness': sum(ind['fitness'] for ind in surviving) / len(surviving) if surviving else 0.0
            })
        
        return removals

    def bidirectional_exchange(self) -> Dict[str, Any]:
        """
        Execute bidirectional rule-set exchanges between sub-populations.
        
        Returns:
            Dict[str, Any]: Exchange statistics
        """
        exchange_stats = {
            'generation': self.generation_count,
            'exchanges': [],
            'total_migrants': 0
        }
        
        domain_list = list(self.sub_populations.keys())
        
        for i, domain_a in enumerate(domain_list):
            for domain_b in domain_list[i+1:]:
                # Select migrants from both populations
                if not self.sub_populations[domain_a] or not self.sub_populations[domain_b]:
                    continue
                
                # Select top performers from A to send to B
                pop_a = sorted(self.sub_populations[domain_a], key=lambda x: x['fitness'], reverse=True)
                pop_b = sorted(self.sub_populations[domain_b], key=lambda x: x['fitness'], reverse=True)
                
                # Migrate elites
                migrant_a = pop_a[0].copy()
                migrant_a['id'] = f"{domain_b}_{migrant_a['id']}"
                migrant_a['origin'] = domain_a
                
                migrant_b = pop_b[0].copy()
                migrant_b['id'] = f"{domain_a}_{migrant_b['id']}"
                migrant_b['origin'] = domain_b
                
                # Add to target populations
                self.sub_populations[domain_b].append(migrant_a)
                self.sub_populations[domain_a].append(migrant_b)
                
                exchange_stats['exchanges'].append({
                    'source_a': domain_a,
                    'source_b': domain_b,
                    'migrants': 2
                })
                exchange_stats['total_migrants'] += 2
        
        self.exchange_history.append(exchange_stats)
        return exchange_stats

    def evolve(self, test_instances: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """
        Perform one generation of evolution: evaluate, apply selection, exchange.
        
        Args:
            test_instances: Dictionary mapping domains to their test instances.
        
        Returns:
            Dict[str, float]: Average fitness per domain after evolution.
        """
        # Evaluate all sub-populations
        for domain in self.task_domains:
            if domain in test_instances:
                self.evaluate_population(domain, test_instances[domain])
        
        # Apply selection pressure (T021)
        removals = self.apply_selection_pressure()
        
        # Bidirectional exchange
        exchange_stats = self.bidirectional_exchange()
        
        # Calculate average fitness
        avg_fitness = {}
        for domain, population in self.sub_populations.items():
            if population:
                avg_fitness[domain] = sum(ind['fitness'] for ind in population) / len(population)
            else:
                avg_fitness[domain] = 0.0
        
        self.generation_count += 1
        
        return {
            'avg_fitness': avg_fitness,
            'selection_removals': removals,
            'exchange_stats': exchange_stats
        }

    def get_state(self) -> Dict[str, Any]:
        """Return the current state of the agent for serialization."""
        return {
            'task_domains': self.task_domains,
            'sub_populations': {
                domain: [
                    {
                        'id': ind['id'],
                        'rules': ind['rules'],
                        'fitness': ind['fitness'],
                        'age': ind['age']
                    }
                    for ind in population
                ]
                for domain, population in self.sub_populations.items()
            },
            'generation_count': self.generation_count,
            'exchange_history': self.exchange_history[-10:]  # Last 10 events
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """Load agent state from a serialized dictionary."""
        self.task_domains = state['task_domains']
        self.generation_count = state['generation_count']
        self.exchange_history = state.get('exchange_history', [])
        
        for domain, population_data in state['sub_populations'].items():
            self.sub_populations[domain] = [
                {
                    'id': ind['id'],
                    'rules': ind['rules'],
                    'fitness': ind['fitness'],
                    'age': ind['age'],
                    'origin': ind.get('origin', domain)
                }
                for ind in population_data
            ]

def main():
    """Main entry point for testing the CoevolvingAgent."""
    import json
    from pathlib import Path
    
    # Load configuration
    config_path = Path("data/config.json")
    if config_path.exists():
        config = Config.load_config(config_path)
    else:
        config = Config()
    
    # Create agent
    agent = CoevolvingAgent(config, ['logic', 'grid'])
    
    # Initialize populations
    for domain in ['logic', 'grid']:
        agent.sub_populations[domain] = agent._initialize_population(domain, 10)
    
    # Run a few generations
    test_instances = {
        'logic': [{'id': 'test1', 'type': 'logic'}],
        'grid': [{'id': 'test1', 'type': 'grid'}]
    }
    
    for _ in range(5):
        result = agent.evolve(test_instances)
        print(f"Generation {agent.generation_count}: {result['avg_fitness']}")
    
    # Save state
    state = agent.get_state()
    output_path = Path("data/results/coevolving_agent_state.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"Agent state saved to {output_path}")

if __name__ == '__main__':
    main()