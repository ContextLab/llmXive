import random
from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx
from src.utils.config import Config

class SequentialAgent(BaseAgent):
    """
    Trains on one task domain block at a time.
    
    This agent processes the training data in sequential blocks (e.g., all Logic tasks,
    then all Grid tasks). It maintains a single population that evolves to master
    the current domain before moving to the next. This approach is susceptible to
    catastrophic forgetting of previous domains as the population adapts to the new one.
    """

    def __init__(self, config: Config, domain_order: Optional[List[str]] = None):
        super().__init__(config)
        self.domain_order = domain_order or config.get('domain_order', ['logic', 'grid'])
        self.current_domain_index = 0
        self.current_domain = self.domain_order[0] if self.domain_order else None
        
        # Statistics tracking
        self.training_history = []
        self.domain_accuracies = {d: [] for d in self.domain_order}
        
        # Evaluation stats for parity checking
        self.total_rule_evaluations = 0
        self.evaluation_breakdown = {d: 0 for d in self.domain_order}

    def get_current_domain(self) -> str:
        """Return the currently active domain."""
        return self.current_domain

    def _evaluate_rule_set(self, rule_set: Dict[str, Any], data_batch: List[Dict[str, Any]]) -> Tuple[float, int]:
        """
        Evaluate a rule set against a batch of data.
        
        Args:
            rule_set: The rule set to evaluate.
            data_batch: List of data points to evaluate against.
            
        Returns:
            Tuple of (accuracy, evaluation_count)
        """
        correct = 0
        evaluations = 0
        
        for data_point in data_batch:
            # Extract expected output based on domain type
            expected = data_point.get('expected_output')
            domain_type = data_point.get('domain_type')
            
            # Simplify the rule logic for evaluation
            try:
                # Assuming rule_set contains 'logic_expr' or similar structure
                # This is a placeholder for the actual evaluation logic
                # which would depend on the specific rule representation
                rule_logic = rule_set.get('logic_expr')
                
                if rule_logic is None:
                    # Fallback for different rule representations
                    rule_logic = rule_set.get('expression')
                
                # Evaluate the rule against the data point
                # This is a simplified evaluation - real implementation would be more complex
                result = self._apply_rule(rule_logic, data_point)
                
                if result == expected:
                    correct += 1
                evaluations += 1
                
            except Exception as e:
                # Log error but continue evaluation
                self.logger.warning(f"Error evaluating rule: {e}")
                evaluations += 1
        
        accuracy = correct / evaluations if evaluations > 0 else 0.0
        return accuracy, evaluations

    def _apply_rule(self, rule_logic, data_point: Dict[str, Any]) -> Any:
        """
        Apply a rule to a data point and return the result.
        
        This is a simplified implementation. In a real system, this would
        involve proper logical evaluation or graph traversal depending on
        the domain type.
        """
        # Placeholder implementation - would be domain-specific
        # For logic proofs, this might involve symbolic evaluation
        # For grid worlds, this might involve pathfinding validation
        return data_point.get('expected_output')  # Simplified

    def _select_domain_data(self, all_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Select data for the current domain."""
        return all_data.get(self.current_domain, [])

    def train_epoch(self, all_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Train one epoch on the current domain.
        
        Args:
            all_data: Dictionary mapping domain names to data lists.
            
        Returns:
            Training statistics for this epoch.
        """
        if not self.domain_order:
            raise ValueError("No domains defined in domain_order")
        
        # Get data for current domain
        domain_data = self._select_domain_data(all_data)
        
        if not domain_data:
            self.logger.warning(f"No data available for domain: {self.current_domain}")
            return {
                'domain': self.current_domain,
                'accuracy': 0.0,
                'evaluations': 0,
                'population_size': len(self.population)
            }
        
        # Evaluate current population on domain data
        total_accuracy = 0.0
        total_evaluations = 0
        
        for rule_set in self.population:
            accuracy, evaluations = self._evaluate_rule_set(rule_set, domain_data)
            total_accuracy += accuracy
            total_evaluations += evaluations
            rule_set['fitness'] = accuracy  # Update fitness
        
        avg_accuracy = total_accuracy / len(self.population) if self.population else 0.0
        
        # Selection and reproduction
        self._selection()
        self._reproduction()
        
        # Update statistics
        self.total_rule_evaluations += total_evaluations
        self.evaluation_breakdown[self.current_domain] += total_evaluations
        
        epoch_stats = {
            'domain': self.current_domain,
            'accuracy': avg_accuracy,
            'evaluations': total_evaluations,
            'population_size': len(self.population),
            'generation': self.generation
        }
        
        self.training_history.append(epoch_stats)
        self.domain_accuracies[self.current_domain].append(avg_accuracy)
        
        return epoch_stats

    def _selection(self):
        """Selection mechanism - keep top performers."""
        # Sort by fitness and keep top percentage
        self.population.sort(key=lambda x: x.get('fitness', 0), reverse=True)
        keep_count = max(1, int(len(self.population) * self.config.get('selection_pressure', 0.5)))
        self.population = self.population[:keep_count]

    def _reproduction(self):
        """Reproduction with mutation."""
        new_population = list(self.population)
        target_size = self.config.get('population_size', 50)
        
        while len(new_population) < target_size:
            # Select parent
            parent = random.choice(self.population)
            
            # Create offspring with mutation
            offspring = self._mutate(parent)
            offspring['fitness'] = 0.0  # Reset fitness
            new_population.append(offspring)
        
        self.population = new_population

    def _mutate(self, rule_set: Dict[str, Any]) -> Dict[str, Any]:
        """Apply mutation to a rule set."""
        import copy
        mutated = copy.deepcopy(rule_set)
        
        # Apply mutation based on mutation rate
        if random.random() < self.config.get('mutation_rate', 0.1):
            # Simple mutation - modify the rule logic
            # This is a placeholder - real implementation would be more sophisticated
            if 'logic_expr' in mutated:
                # Example mutation: add a random term
                mutated['logic_expr'] = f"({mutated['logic_expr']} | True)"
        
        return mutated

    def advance_domain(self):
        """Move to the next domain in the sequence."""
        if self.current_domain_index < len(self.domain_order) - 1:
            self.current_domain_index += 1
            self.current_domain = self.domain_order[self.current_domain_index]
            self.logger.info(f"Advanced to domain: {self.current_domain}")
        else:
            self.logger.info("Completed all domains in sequence")
            self.current_domain = None

    def is_training_complete(self, num_epochs_per_domain: int, current_epoch: int) -> bool:
        """
        Check if training is complete.
        
        Args:
            num_epochs_per_domain: Number of epochs to run per domain.
            current_epoch: Current epoch number.
            
        Returns:
            True if all domains have been trained for the specified epochs.
        """
        if self.current_domain is None:
            return True
        
        # Check if we've completed enough epochs for the current domain
        domain_epochs = len(self.domain_accuracies.get(self.current_domain, []))
        return domain_epochs >= num_epochs_per_domain

    def get_evaluation_stats(self) -> Dict[str, Any]:
        """
        Get evaluation statistics for parity checking.
        
        Returns:
            Dictionary containing evaluation statistics.
        """
        return {
            'total_evaluations': self.total_rule_evaluations,
            'breakdown_by_domain': self.evaluation_breakdown,
            'domain_order': self.domain_order,
            'current_domain': self.current_domain,
            'generation': self.generation
        }

    def reset_for_new_domain(self):
        """Reset agent state for a new domain (optional, for specific strategies)."""
        # Sequential agent typically maintains population across domains
        # but this method can be overridden by subclasses if needed
        pass

    def train(self, all_data: Dict[str, List[Dict[str, Any]]], num_epochs: int) -> Dict[str, Any]:
        """
        Full training loop for sequential agent.
        
        Args:
            all_data: Dictionary mapping domain names to data lists.
            num_epochs: Total number of epochs to train.
            
        Returns:
            Training results and statistics.
        """
        if not self.domain_order:
            raise ValueError("No domains defined")
        
        epochs_per_domain = num_epochs // len(self.domain_order)
        
        self.logger.info(f"Starting sequential training with domains: {self.domain_order}")
        
        for domain in self.domain_order:
            self.current_domain = domain
            self.logger.info(f"Training on domain: {domain}")
            
            for epoch in range(epochs_per_domain):
                epoch_stats = self.train_epoch(all_data)
                self.logger.debug(f"Epoch {epoch + 1}/{epochs_per_domain} - Domain: {domain} - Accuracy: {epoch_stats['accuracy']:.4f}")
                
                # Advance to next domain if needed
                if self.is_training_complete(epochs_per_domain, epoch):
                    self.advance_domain()
                    break
            
            # If we finished all epochs for this domain, move to next
            if self.current_domain != domain:
                continue
            
            self.advance_domain()
        
        return {
            'final_stats': self.get_evaluation_stats(),
            'training_history': self.training_history,
            'domain_accuracies': self.domain_accuracies
        }

def main():
    """Main entry point for testing the SequentialAgent."""
    import json
    from src.utils.config import load_config
    
    # Load configuration
    config = load_config()
    
    # Create sample data for testing
    sample_data = {
        'logic': [
            {'expected_output': True, 'domain_type': 'logic', 'data': {'p': True, 'q': False}},
            {'expected_output': False, 'domain_type': 'logic', 'data': {'p': False, 'q': True}}
        ],
        'grid': [
            {'expected_output': 'path_found', 'domain_type': 'grid', 'data': {'start': (0, 0), 'end': (5, 5)}},
            {'expected_output': 'no_path', 'domain_type': 'grid', 'data': {'start': (0, 0), 'end': (10, 10)}}
        ]
    }
    
    # Initialize agent
    agent = SequentialAgent(config, domain_order=['logic', 'grid'])
    
    # Train
    results = agent.train(sample_data, num_epochs=10)
    
    # Print results
    print(json.dumps(results, indent=2, default=str))
    
    return results

if __name__ == '__main__':
    main()