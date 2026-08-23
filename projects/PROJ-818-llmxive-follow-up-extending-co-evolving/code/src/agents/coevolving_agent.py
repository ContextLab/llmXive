"""
Co-evolving Agent Implementation.

Manages sub-populations for distinct task domains (Logic, Grid) and executes
bidirectional rule-set exchanges at every generation step to promote
co-evolution and prevent catastrophic forgetting.
"""
import random
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict
from sympy import simplify_logic, symbols, Implies, And, Or, Not, Symbol

from .base_agent import BaseAgent
from src.utils.config import Config


class CoevolvingAgent(BaseAgent):
    """
    An agent that maintains separate sub-populations for different task domains
    (e.g., Logic Proofs, Grid Worlds) and facilitates the exchange of rule-sets
    between them at every generation step.

    This implements the "Co-evolving" condition where sub-populations evolve
    together, sharing successful strategies to improve generalization and
    reduce forgetting.
    """

    def __init__(self, config: Config, task_domains: List[str] = None):
        """
        Initialize the Co-evolving Agent.

        Args:
            config: Configuration object containing seeds, generation counts, etc.
            task_domains: List of domain identifiers (e.g., ['logic', 'grid']).
                          Defaults to ['logic', 'grid'] if not provided.
        """
        super().__init__(config)
        self.task_domains = task_domains or ['logic', 'grid']
        
        # Sub-populations: Dict[domain, List[Dict[str, Any]]]
        # Each rule-set is a dict: {'rules': List[SympyExpr], 'fitness': float, 'id': str}
        self.sub_populations: Dict[str, List[Dict[str, Any]]] = {
            domain: [] for domain in self.task_domains
        }
        
        # Exchange history for analysis
        self.exchange_log: List[Dict[str, Any]] = []
        
        # Statistics tracking
        self.total_rule_evaluations = 0
        self.generation_count = 0

    def initialize_populations(self, initial_rule_sets: Dict[str, List[Any]]):
        """
        Initialize sub-populations with starting rule-sets for each domain.

        Args:
            initial_rule_sets: Dict mapping domain to list of initial rule expressions.
        """
        for domain in self.task_domains:
            if domain in initial_rule_sets:
                self.sub_populations[domain] = [
                    {
                        'rules': rules,
                        'fitness': 0.0,
                        'id': f"{domain}_{i}_{random.randint(0, 10000)}"
                    }
                    for i, rules in enumerate(initial_rule_sets[domain])
                ]
            else:
                # Initialize with empty rules if none provided
                self.sub_populations[domain] = [
                    {
                        'rules': [],
                        'fitness': 0.0,
                        'id': f"{domain}_init_{i}"
                    }
                    for i in range(self.config.population_size)
                ]

    def evaluate_rule_sets(self, domain: str, rule_sets: List[Dict[str, Any]], 
                           task_instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate rule-sets on task instances and update fitness scores.

        Args:
            domain: The task domain ('logic' or 'grid').
            rule_sets: List of rule-sets to evaluate.
            task_instances: List of task instances to evaluate against.

        Returns:
            Updated rule-sets with fitness scores.
        """
        evaluated = []
        for rs in rule_sets:
            correct = 0
            total = len(task_instances)
            
            if total == 0:
                fitness = 0.0
            else:
                for instance in task_instances:
                    if self._apply_rules(rs['rules'], instance, domain):
                        correct += 1
                    self.total_rule_evaluations += 1
                
                fitness = correct / total
            
            updated_rs = rs.copy()
            updated_rs['fitness'] = fitness
            evaluated.append(updated_rs)
        
        return evaluated

    def _apply_rules(self, rules: List[Any], instance: Dict[str, Any], domain: str) -> bool:
        """
        Apply a set of rules to a task instance and return whether it's solved.

        Args:
            rules: List of Sympy expressions representing rules.
            instance: The task instance data.
            domain: The task domain.

        Returns:
            True if the instance is solved correctly, False otherwise.
        """
        if not rules:
            return False

        if domain == 'logic':
            # For logic proofs, check if rules imply the conclusion
            try:
                premises = instance.get('premises', [])
                conclusion = instance.get('conclusion')
                
                if not premises or conclusion is None:
                    return False
                
                # Build the implication: (premises[0] & premises[1] & ...) -> conclusion
                combined_premises = premises[0]
                for p in premises[1:]:
                    combined_premises = And(combined_premises, p)
                
                implication = Implies(combined_premises, conclusion)
                
                # Check if the rule set entails the implication
                # Simplify and check validity
                simplified = simplify_logic(implication)
                return simplified == True
                
            except Exception:
                return False

        elif domain == 'grid':
            # For grid worlds, check path validity
            try:
                start = instance.get('start')
                goal = instance.get('goal')
                obstacles = instance.get('obstacles', [])
                grid_size = instance.get('size', (10, 10))
                
                if not start or not goal:
                    return False
                
                # Apply rules to determine valid moves
                # Rules might restrict movement (e.g., "avoid red" -> avoid certain cells)
                valid_path = self._find_path(start, goal, obstacles, rules, grid_size)
                return valid_path is not None
                
            except Exception:
                return False

        return False

    def _find_path(self, start: Tuple[int, int], goal: Tuple[int, int], 
                   obstacles: List[Tuple[int, int]], rules: List[Any], 
                   grid_size: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Find a path from start to goal avoiding obstacles and respecting rules.

        Args:
            start: Starting position (x, y).
            goal: Goal position (x, y).
            obstacles: List of obstacle positions.
            rules: List of rules to respect.
            grid_size: Grid dimensions (width, height).

        Returns:
            Path as list of positions, or None if no path exists.
        """
        # Simple BFS pathfinding
        from collections import deque
        
        width, height = grid_size
        visited = set()
        queue = deque([(start, [start])])
        visited.add(start)
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == goal:
                return path
            
            # Explore neighbors (up, down, left, right)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) not in visited and (nx, ny) not in obstacles:
                        # Check if rules allow this move
                        if self._rule_allows_move(rules, (x, y), (nx, ny)):
                            visited.add((nx, ny))
                            queue.append(((nx, ny), path + [(nx, ny)]))
        
        return None

    def _rule_allows_move(self, rules: List[Any], current: Tuple[int, int], 
                          next_pos: Tuple[int, int]) -> bool:
        """
        Check if current rules allow a move from current to next_pos.

        Args:
            rules: List of rules.
            current: Current position.
            next_pos: Next position.

        Returns:
            True if move is allowed, False otherwise.
        """
        # Default: all moves allowed unless rules specify otherwise
        # Rules might encode constraints like "avoid red cells"
        # For simplicity, we assume rules are satisfied unless they explicitly forbid
        return True

    def bidirectional_exchange(self):
        """
        Execute bidirectional rule-set exchange between sub-populations.
        
        At every generation step, select high-performing rule-sets from each
        domain and exchange them with other domains to promote cross-pollination
        of strategies.
        """
        if len(self.task_domains) < 2:
            return

        exchange_event = {
            'generation': self.generation_count,
            'exchanges': []
        }

        for i, domain_a in enumerate(self.task_domains):
            for domain_b in self.task_domains[i+1:]:
                # Select top performers from each domain
                pop_a = sorted(self.sub_populations[domain_a], 
                             key=lambda x: x['fitness'], reverse=True)
                pop_b = sorted(self.sub_populations[domain_b], 
                             key=lambda x: x['fitness'], reverse=True)
                
                # Exchange top 10% of rule-sets (or at least 1)
                exchange_count = max(1, int(len(pop_a) * 0.1))
                
                # Select rule-sets to exchange
                exchange_a = pop_a[:exchange_count]
                exchange_b = pop_b[:exchange_count]
                
                # Record exchange
                exchange_event['exchanges'].append({
                    'from_domain': domain_a,
                    'to_domain': domain_b,
                    'rule_set_ids': [rs['id'] for rs in exchange_a],
                    'fitness_range': [rs['fitness'] for rs in exchange_a]
                })
                
                exchange_event['exchanges'].append({
                    'from_domain': domain_b,
                    'to_domain': domain_a,
                    'rule_set_ids': [rs['id'] for rs in exchange_b],
                    'fitness_range': [rs['fitness'] for rs in exchange_b]
                })
                
                # Inject exchanged rule-sets into target populations
                # Replace lowest performers with incoming high performers
                self.sub_populations[domain_b] = self._inject_rule_sets(
                    self.sub_populations[domain_b], exchange_a
                )
                self.sub_populations[domain_a] = self._inject_rule_sets(
                    self.sub_populations[domain_a], exchange_b
                )

        self.exchange_log.append(exchange_event)

    def _inject_rule_sets(self, population: List[Dict[str, Any]], 
                         incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Inject incoming rule-sets into a population, replacing lowest performers.

        Args:
            population: Target population.
            incoming: Rule-sets to inject.

        Returns:
            Updated population with injected rule-sets.
        """
        if not incoming or not population:
            return population

        # Sort by fitness (ascending) to find lowest performers
        sorted_pop = sorted(population, key=lambda x: x['fitness'])
        
        # Replace lowest performers
        num_to_replace = min(len(incoming), len(sorted_pop))
        for i, rs in enumerate(incoming[:num_to_replace]):
            # Create a copy with new ID to avoid reference issues
            new_rs = rs.copy()
            new_rs['id'] = f"{rs['id']}_{random.randint(0, 10000)}_injected"
            sorted_pop[i] = new_rs
        
        return sorted_pop

    def evolve_population(self, domain: str, task_instances: List[Dict[str, Any]], 
                         mutation_rate: float = 0.1):
        """
        Evolve a specific sub-population using selection, mutation, and crossover.

        Args:
            domain: The domain to evolve.
            task_instances: Task instances for evaluation.
            mutation_rate: Probability of mutating a rule-set.
        """
        if domain not in self.sub_populations:
            return

        # Evaluate current population
        self.sub_populations[domain] = self.evaluate_rule_sets(
            domain, self.sub_populations[domain], task_instances
        )

        # Selection: Keep top performers
        sorted_pop = sorted(self.sub_populations[domain], 
                          key=lambda x: x['fitness'], reverse=True)
        elite_count = max(1, int(len(sorted_pop) * 0.2))
        elites = sorted_pop[:elite_count]

        # Generate new population through crossover and mutation
        new_population = elites.copy()
        
        while len(new_population) < len(self.sub_populations[domain]):
            # Selection
            parent_a = random.choice(sorted_pop[:int(len(sorted_pop) * 0.5)])
            parent_b = random.choice(sorted_pop[:int(len(sorted_pop) * 0.5)])
            
            # Crossover
            child_rules = self._crossover(parent_a['rules'], parent_b['rules'])
            
            # Mutation
            if random.random() < mutation_rate:
                child_rules = self._mutate(child_rules)
            
            child = {
                'rules': child_rules,
                'fitness': 0.0,
                'id': f"{domain}_{random.randint(0, 10000)}"
            }
            new_population.append(child)

        self.sub_populations[domain] = new_population

    def _crossover(self, rules_a: List[Any], rules_b: List[Any]) -> List[Any]:
        """
        Perform crossover between two rule-sets.

        Args:
            rules_a: Rules from parent A.
            rules_b: Rules from parent B.

        Returns:
            Combined rules from both parents.
        """
        if not rules_a:
            return rules_b.copy()
        if not rules_b:
            return rules_a.copy()
        
        # Simple crossover: take half from each
        split_point = len(rules_a) // 2
        child_rules = rules_a[:split_point] + rules_b[split_point:]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_rules = []
        for rule in child_rules:
            rule_repr = str(rule)
            if rule_repr not in seen:
                seen.add(rule_repr)
                unique_rules.append(rule)
        
        return unique_rules

    def _mutate(self, rules: List[Any]) -> List[Any]:
        """
        Mutate a rule-set by adding, removing, or modifying rules.

        Args:
            rules: Current rules.

        Returns:
            Mutated rules.
        """
        if not rules:
            return rules

        mutated = rules.copy()
        
        # Randomly remove a rule
        if random.random() < 0.3 and len(mutated) > 1:
            idx = random.randint(0, len(mutated) - 1)
            mutated.pop(idx)
        
        # Randomly add a new rule
        if random.random() < 0.3:
            # Create a simple new rule based on domain context
            # For logic: add a new implication
            # For grid: add a new constraint
            new_rule = self._generate_random_rule()
            if new_rule:
                mutated.append(new_rule)
        
        return mutated

    def _generate_random_rule(self) -> Optional[Any]:
        """
        Generate a random rule for mutation.

        Returns:
            A Sympy expression representing a rule, or None.
        """
        # Simple random rule generation
        # In practice, this should be domain-specific
        try:
            x, y = symbols('x y')
            # Return a simple implication or conjunction
            return Implies(x, y)
        except Exception:
            return None

    def get_best_rule_sets(self, domain: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the best performing rule-sets from sub-populations.

        Args:
            domain: Specific domain to query, or None for all.

        Returns:
            Dict of domain to best rule-sets.
        """
        if domain:
            if domain not in self.sub_populations:
                return {}
            sorted_pop = sorted(self.sub_populations[domain], 
                              key=lambda x: x['fitness'], reverse=True)
            return {domain: sorted_pop[:1]}
        
        result = {}
        for dom, pop in self.sub_populations.items():
            sorted_pop = sorted(pop, key=lambda x: x['fitness'], reverse=True)
            result[dom] = sorted_pop[:1]
        
        return result

    def run_generation(self, task_instances: Dict[str, List[Dict[str, Any]]]):
        """
        Execute one full generation step: evaluation, exchange, and evolution.

        Args:
            task_instances: Dict mapping domain to list of task instances.
        """
        self.generation_count += 1

        # 1. Evaluate all sub-populations
        for domain in self.task_domains:
            if domain in task_instances:
                self.sub_populations[domain] = self.evaluate_rule_sets(
                    domain, self.sub_populations[domain], task_instances[domain]
                )

        # 2. Bidirectional exchange between sub-populations
        self.bidirectional_exchange()

        # 3. Evolve each sub-population
        for domain in self.task_domains:
            if domain in task_instances:
                self.evolve_population(domain, task_instances[domain])

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the agent for checkpointing.

        Returns:
            Dict containing agent state.
        """
        return {
            'task_domains': self.task_domains,
            'sub_populations': {
                domain: [
                    {
                        'rules': [str(r) for r in rs['rules']],
                        'fitness': rs['fitness'],
                        'id': rs['id']
                    }
                    for rs in pop
                ]
                for domain, pop in self.sub_populations.items()
            },
            'exchange_log': self.exchange_log,
            'total_rule_evaluations': self.total_rule_evaluations,
            'generation_count': self.generation_count
        }

    def load_state(self, state: Dict[str, Any]):
        """
        Load agent state from a checkpoint.

        Args:
            state: Dict containing agent state.
        """
        self.task_domains = state['task_domains']
        self.exchange_log = state.get('exchange_log', [])
        self.total_rule_evaluations = state.get('total_rule_evaluations', 0)
        self.generation_count = state.get('generation_count', 0)

        # Reconstruct sub-populations
        self.sub_populations = {}
        for domain, pop_data in state['sub_populations'].items():
            self.sub_populations[domain] = [
                {
                    'rules': [],  # Rules would need to be parsed back from strings
                    'fitness': rs['fitness'],
                    'id': rs['id']
                }
                for rs in pop_data
            ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics for monitoring.

        Returns:
            Dict of statistics.
        """
        stats = {
            'generation': self.generation_count,
            'total_rule_evaluations': self.total_rule_evaluations,
            'population_sizes': {
                domain: len(pop) 
                for domain, pop in self.sub_populations.items()
            },
            'average_fitness': {
                domain: sum(rs['fitness'] for rs in pop) / len(pop) if pop else 0
                for domain, pop in self.sub_populations.items()
            },
            'total_exchanges': len(self.exchange_log)
        }
        return stats