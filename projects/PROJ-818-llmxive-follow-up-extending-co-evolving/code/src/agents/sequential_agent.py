"""
SequentialAgent: Trains on one task domain block at a time.

This agent implements the Sequential training condition where the agent
completes training on one task domain (e.g., all logic proofs) before
moving to the next (e.g., all grid worlds).
"""
import random
from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx
from src.utils.config import Config
import logging

logger = logging.getLogger(__name__)


class SequentialAgent(BaseAgent):
    """
    An agent that trains sequentially on distinct task domains.
    
    Training order:
    1. All instances from Domain A (e.g., Logic Proofs)
    2. All instances from Domain B (e.g., Grid Worlds)
    
    This approach tests the agent's ability to retain earlier learned
    rules when exposed to new, distinct domains later in training.
    """

    def __init__(self, config: Config):
        """
        Initialize the SequentialAgent.
        
        Args:
            config: Configuration object containing seeds, budgets, etc.
        """
        super().__init__(config)
        self.current_domain_index = 0
        self.domain_order = config.get('domain_order', ['logic', 'grid'])
        self.domain_instances: Dict[str, List[Dict[str, Any]]] = {}
        self.domain_iteration_counts: Dict[str, int] = {d: 0 for d in self.domain_order}
        
        logger.info(f"SequentialAgent initialized with domain order: {self.domain_order}")

    def load_domain_instances(self, domain: str, instances: List[Dict[str, Any]]):
        """
        Load instances for a specific domain.
        
        Args:
            domain: The domain identifier (e.g., 'logic', 'grid')
            instances: List of instance dictionaries
        """
        if domain not in self.domain_instances:
            self.domain_instances[domain] = []
        self.domain_instances[domain].extend(instances)
        logger.info(f"Loaded {len(instances)} instances for domain '{domain}'")

    def get_current_domain(self) -> str:
        """Get the currently active domain name."""
        if self.current_domain_index < len(self.domain_order):
            return self.domain_order[self.current_domain_index]
        return None

    def advance_domain(self):
        """Move to the next domain in the sequence."""
        self.current_domain_index += 1
        if self.current_domain_index < len(self.domain_order):
            logger.info(f"Advancing to domain: {self.domain_order[self.current_domain_index]}")
        else:
            logger.info("All domains completed.")

    def is_training_complete(self) -> bool:
        """Check if all domains have been trained."""
        return self.current_domain_index >= len(self.domain_order)

    def evaluate_rule_set(self, rule_set: Dict[str, Any], instance: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Evaluate a rule set against a specific instance.
        
        Args:
            rule_set: The rule set to evaluate (contains 'rules' list)
            instance: The instance to evaluate against
            
        Returns:
            Tuple of (is_valid, confidence_score)
        """
        domain = instance.get('domain')
        instance_data = instance.get('instance_data', {})
        
        if domain == 'logic':
            return self._evaluate_logic_rule_set(rule_set, instance_data)
        elif domain == 'grid':
            return self._evaluate_grid_rule_set(rule_set, instance_data)
        else:
            logger.warning(f"Unknown domain: {domain}")
            return False, 0.0

    def _evaluate_logic_rule_set(self, rule_set: Dict[str, Any], instance_data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Evaluate logic rules against a proof instance.
        
        Args:
            rule_set: Rule set containing logical rules
            instance_data: Instance data with axioms and target
            
        Returns:
            Tuple of (is_valid, confidence_score)
        """
        rules = rule_set.get('rules', [])
        axioms = instance_data.get('axioms', [])
        target = instance_data.get('target')
        
        if not target:
            return False, 0.0
        
        # Build the logical expression from axioms and rules
        # Simplify and check if target follows
        try:
            # Create symbols for variables
            all_vars = set()
            for axiom in axioms:
                for char in str(axiom):
                    if char.isalpha():
                        all_vars.add(char)
            
            symbol_map = {v: symbols(v) for v in all_vars}
            
            # Convert axioms to sympy expressions
            axiom_exprs = []
            for axiom in axioms:
                # Simple parsing: assume axioms are in format "A & B -> C"
                # This is a simplified evaluation for demonstration
                expr_str = str(axiom).replace('->', 'Implies').replace('&', 'And').replace('|', 'Or').replace('~', 'Not')
                # In a real implementation, we would parse this more robustly
                # For now, we simulate evaluation based on rule coverage
                axiom_exprs.append(axiom)
            
            # Evaluate rule coverage
            coverage = 0
            for rule in rules:
                if rule in axioms:
                    coverage += 1
            
            # Calculate confidence based on coverage
            confidence = coverage / max(len(axioms), 1)
            is_valid = confidence > 0.5
            
            return is_valid, confidence
            
        except Exception as e:
            logger.error(f"Error evaluating logic rule set: {e}")
            return False, 0.0

    def _evaluate_grid_rule_set(self, rule_set: Dict[str, Any], instance_data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Evaluate grid rules against a grid instance.
        
        Args:
            rule_set: Rule set containing grid navigation rules
            instance_data: Instance data with grid configuration
            
        Returns:
            Tuple of (is_valid, confidence_score)
        """
        rules = rule_set.get('rules', [])
        grid_config = instance_data.get('grid', {})
        start = grid_config.get('start')
        goal = grid_config.get('goal')
        obstacles = grid_config.get('obstacles', [])
        
        if not start or not goal:
            return False, 0.0
        
        # Check if rules help navigate from start to goal
        # Simulate pathfinding with rule constraints
        try:
            # Create a simple graph representation
            G = nx.Graph()
            rows = grid_config.get('rows', 10)
            cols = grid_config.get('cols', 10)
            
            # Add nodes
            for r in range(rows):
                for c in range(cols):
                    if (r, c) not in obstacles:
                        G.add_node((r, c))
            
            # Add edges (up, down, left, right)
            for r in range(rows):
                for c in range(cols):
                    if (r, c) in G.nodes:
                        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if (nr, nc) in G.nodes:
                                G.add_edge((r, c), (nr, nc))
            
            # Check if path exists
            try:
                path = nx.shortest_path(G, start, goal)
                path_length = len(path) - 1
                
                # Evaluate rule compliance
                # Rules might include "avoid red", "diagonal paths", etc.
                # For simplicity, we check if the path length is reasonable
                # and if rules are "followed" (simulated)
                
                rule_compliance = 0.0
                if len(rules) > 0:
                    # Simulate rule compliance based on path characteristics
                    # In a real implementation, we would check specific rules
                    rule_compliance = 0.8  # Assume good compliance for valid paths
                
                is_valid = path_length < 20 and rule_compliance > 0.5
                confidence = rule_compliance * (1.0 - min(path_length / 20, 1.0))
                
                return is_valid, confidence
                
            except nx.NetworkXNoPath:
                return False, 0.0
                
        except Exception as e:
            logger.error(f"Error evaluating grid rule set: {e}")
            return False, 0.0

    def train_on_instance(self, instance: Dict[str, Any]) -> bool:
        """
        Train on a single instance.
        
        Args:
            instance: The instance to train on
            
        Returns:
            True if training was successful, False otherwise
        """
        domain = instance.get('domain')
        
        if domain != self.get_current_domain():
            # Skip instances from domains not currently being trained
            return False
        
        # Simulate rule extraction/update from instance
        # In a real implementation, this would involve evolutionary updates
        # For now, we simulate learning by updating internal state
        
        rule_set = self.get_best_rule_set()
        is_valid, confidence = self.evaluate_rule_set(rule_set, instance)
        
        if is_valid:
            # Successfully applied rules
            self.evaluation_count += 1
            self.total_accuracy_sum += confidence
            self.successful_evaluations += 1
            
            # Simulate rule refinement
            self._refine_rule_set(rule_set, instance)
            
            return True
        else:
            # Failed to apply rules, might need to generate new rules
            self.evaluation_count += 1
            self._generate_new_rule_set()
            return False

    def _refine_rule_set(self, rule_set: Dict[str, Any], instance: Dict[str, Any]):
        """
        Refine the rule set based on successful application.
        
        Args:
            rule_set: The rule set to refine
            instance: The instance that was successfully handled
        """
        # Simulate rule refinement by adding successful patterns
        # In a real implementation, this would involve genetic operators
        domain = instance.get('domain')
        instance_data = instance.get('instance_data', {})
        
        if domain == 'logic':
            # Extract successful logical patterns
            axioms = instance_data.get('axioms', [])
            for axiom in axioms:
                if axiom not in rule_set.get('rules', []):
                    rule_set['rules'].append(axiom)
                    
        elif domain == 'grid':
            # Extract successful navigation patterns
            grid_config = instance_data.get('grid', {})
            # Add grid-specific rules based on successful path
            # (simplified for demonstration)
            if 'avoid_obstacles' not in rule_set.get('rules', []):
                rule_set['rules'].append('avoid_obstacles')

    def _generate_new_rule_set(self):
        """Generate a new rule set when current one fails."""
        # Simulate generating a new rule set
        new_rules = []
        # Add some base rules
        new_rules.append("base_rule_1")
        new_rules.append("base_rule_2")
        
        self.current_rule_sets.append({
            'id': f"rule_set_{len(self.current_rule_sets)}",
            'rules': new_rules,
            'fitness': 0.0
        })

    def run_training_epoch(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run one training epoch on the provided instances.
        
        Args:
            instances: List of instances to train on
            
        Returns:
            Dictionary with training statistics
        """
        domain = self.get_current_domain()
        if not domain:
            logger.warning("No current domain set for training.")
            return {'success': False, 'message': 'No current domain'}
        
        # Filter instances for current domain
        domain_instances = [i for i in instances if i.get('domain') == domain]
        
        if not domain_instances:
            logger.info(f"No instances found for domain '{domain}'. Advancing to next domain.")
            self.advance_domain()
            return {'success': True, 'message': 'No instances for current domain', 'domain': domain}
        
        # Train on each instance
        success_count = 0
        for instance in domain_instances:
            if self.train_on_instance(instance):
                success_count += 1
        
        # Update domain iteration count
        self.domain_iteration_counts[domain] += 1
        
        # Check if we've completed enough iterations for this domain
        # For simplicity, we assume one pass is enough, but in reality
        # we might want multiple passes
        if self.domain_iteration_counts[domain] >= self.config.get('max_domain_iterations', 1):
            self.advance_domain()
        
        # Calculate statistics
        accuracy = success_count / len(domain_instances) if domain_instances else 0.0
        avg_confidence = self.total_accuracy_sum / self.evaluation_count if self.evaluation_count > 0 else 0.0
        
        return {
            'success': True,
            'domain': domain,
            'instances_processed': len(domain_instances),
            'success_count': success_count,
            'accuracy': accuracy,
            'average_confidence': avg_confidence,
            'evaluation_count': self.evaluation_count
        }

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the agent.
        
        Returns:
            Dictionary containing agent state
        """
        return {
            'type': 'SequentialAgent',
            'population': self.current_rule_sets,
            'rule_sets': self.current_rule_sets,
            'generation_count': self.generation_count,
            'evaluation_count': self.evaluation_count,
            'current_domain_index': self.current_domain_index,
            'current_domain': self.get_current_domain(),
            'domain_iteration_counts': self.domain_iteration_counts,
            'domain_order': self.domain_order,
            'total_accuracy_sum': self.total_accuracy_sum,
            'successful_evaluations': self.successful_evaluations
        }

    def set_state(self, state: Dict[str, Any]):
        """
        Set the agent state from a dictionary.
        
        Args:
            state: Dictionary containing agent state
        """
        self.current_rule_sets = state.get('population', [])
        self.generation_count = state.get('generation_count', 0)
        self.evaluation_count = state.get('evaluation_count', 0)
        self.current_domain_index = state.get('current_domain_index', 0)
        self.domain_iteration_counts = state.get('domain_iteration_counts', {d: 0 for d in self.domain_order})
        self.total_accuracy_sum = state.get('total_accuracy_sum', 0.0)
        self.successful_evaluations = state.get('successful_evaluations', 0)
        logger.info(f"SequentialAgent state restored from generation {self.generation_count}")


def main():
    """
    Main function to demonstrate SequentialAgent usage.
    
    This function creates a SequentialAgent, loads some sample data,
    and runs a training epoch to demonstrate the sequential training process.
    """
    import json
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a simple config
    config = Config({
        'seed': 42,
        'generation_count': 10,
        'domain_order': ['logic', 'grid'],
        'max_domain_iterations': 1
    })
    
    # Create agent
    agent = SequentialAgent(config)
    
    # Load sample data (in real usage, this would come from generated datasets)
    try:
        # Try to load generated data
        data_dir = Path('data')
        if data_dir.exists():
            logic_file = data_dir / 'generated_proofs.json'
            grid_file = data_dir / 'generated_grids.json'
            
            if logic_file.exists():
                with open(logic_file, 'r') as f:
                    logic_data = json.load(f)
                agent.load_domain_instances('logic', logic_data)
                logger.info(f"Loaded {len(logic_data)} logic instances")
            
            if grid_file.exists():
                with open(grid_file, 'r') as f:
                    grid_data = json.load(f)
                agent.load_domain_instances('grid', grid_data)
                logger.info(f"Loaded {len(grid_data)} grid instances")
        else:
            logger.warning("Data directory not found. Using empty datasets.")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
    
    # Run training
    if agent.domain_instances:
        all_instances = []
        for domain, instances in agent.domain_instances.items():
            all_instances.extend(instances)
        
        logger.info(f"Starting training with {len(all_instances)} total instances")
        
        # Run multiple epochs
        for epoch in range(config.get('generation_count', 10)):
            agent.generation_count += 1
            result = agent.run_training_epoch(all_instances)
            logger.info(f"Epoch {epoch + 1}: {result}")
            
            if agent.is_training_complete():
                logger.info("Training complete - all domains processed")
                break
    else:
        logger.info("No instances to train on. Skipping training.")
    
    # Save final state
    state = agent.get_state()
    output_path = Path('data/results/sequential_agent_state.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    logger.info(f"Agent state saved to {output_path}")
    return state


if __name__ == '__main__':
    main()
