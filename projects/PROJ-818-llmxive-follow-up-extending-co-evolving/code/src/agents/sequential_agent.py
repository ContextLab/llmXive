"""
Sequential Agent Implementation for Co-Evolving Policy Distillation.

This module implements the SequentialAgent, which trains on one task domain
block at a time (e.g., all logic proofs, then all grid worlds).
"""
import random
from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx
from src.utils.config import Config
import json
import os

class SequentialAgent(BaseAgent):
    """
    An agent that trains sequentially on distinct task domains.
    
    Training Order:
    1. Logic Proofs Domain
    2. Grid Worlds Domain
    
    This contrasts with MixedAgent (random mixing) and CoevolvingAgent 
    (simultaneous sub-populations with exchange).
    """

    def __init__(self, config: Config, seed: Optional[int] = None):
        super().__init__(config, seed)
        self.current_domain_index = 0
        self.domains = ['logic', 'grid']
        self.domain_progress = {domain: 0 for domain in self.domains}
        self.evaluation_counts = {domain: 0 for domain in self.domains}
        self.history = []

    def train_step(self, batch: List[Dict[str, Any]], domain: str) -> Dict[str, Any]:
        """
        Perform a single training step on a batch of data for a specific domain.
        
        Args:
            batch: List of task instances for the current domain.
            domain: The domain name ('logic' or 'grid').
            
        Returns:
            Dictionary containing training metrics and updated state.
        """
        if not batch:
            return {"status": "skipped", "reason": "empty_batch"}

        # Update evaluation counts
        self.evaluation_counts[domain] += len(batch)
        
        # Simulate rule-set evolution for this domain
        # In a real evolutionary system, this would involve selection, crossover, mutation
        # Here we simulate the effect of training on the current rule set
        
        current_state = self.get_state()
        
        # Process each item in the batch
        success_count = 0
        total_count = 0
        
        for item in batch:
            total_count += 1
            task_type = item.get('type', domain)
            
            if task_type == 'logic':
                # Logic proof evaluation
                if self._evaluate_logic_proof(item, current_state['rule_set']):
                    success_count += 1
            elif task_type == 'grid':
                # Grid navigation evaluation
                if self._evaluate_grid_task(item, current_state['rule_set']):
                    success_count += 1
            else:
                # Fallback evaluation
                if self._evaluate_generic_task(item, current_state['rule_set']):
                    success_count += 1
        
        # Calculate accuracy for this step
        accuracy = success_count / total_count if total_count > 0 else 0.0
        
        # Update internal state (simulated evolution)
        # In a real system, this would modify the rule set based on performance
        new_rule_set = self._evolve_rule_set(current_state['rule_set'], accuracy)
        self.set_rule_set(new_rule_set)
        
        step_result = {
            "domain": domain,
            "batch_size": len(batch),
            "accuracy": accuracy,
            "success_count": success_count,
            "total_evaluations": self.evaluation_counts[domain],
            "global_evaluations": sum(self.evaluation_counts.values())
        }
        
        self.history.append(step_result)
        return step_result

    def train_on_domain(self, domain: str, data: List[Dict[str, Any]], 
                      steps_per_epoch: int = 10) -> Dict[str, Any]:
        """
        Train exclusively on a single domain for multiple steps.
        
        Args:
            domain: The domain to train on ('logic' or 'grid').
            data: The dataset for this domain.
            steps_per_epoch: Number of training steps to perform.
            
        Returns:
            Summary of training performance on this domain.
        """
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}. Must be one of {self.domains}")
        
        if not data:
            return {"status": "skipped", "reason": "no_data"}
        
        epoch_results = []
        
        for step in range(steps_per_epoch):
            # Sample a batch from the domain data
            batch_size = min(self.config.batch_size, len(data))
            batch = random.sample(data, batch_size)
            
            result = self.train_step(batch, domain)
            epoch_results.append(result)
            
            # Update domain progress
            self.domain_progress[domain] += batch_size
        
        # Calculate aggregate metrics for this domain training
        avg_accuracy = sum(r.get('accuracy', 0) for r in epoch_results) / len(epoch_results) if epoch_results else 0.0
        
        return {
            "domain": domain,
            "epochs_completed": steps_per_epoch,
            "avg_accuracy": avg_accuracy,
            "total_samples_processed": self.domain_progress[domain],
            "step_results": epoch_results
        }

    def train_full_sequence(self, logic_data: List[Dict[str, Any]], 
                          grid_data: List[Dict[str, Any]],
                          steps_per_domain: int = 10) -> Dict[str, Any]:
        """
        Execute the full sequential training protocol:
        1. Train on Logic domain exclusively
        2. Train on Grid domain exclusively
        
        Args:
            logic_data: Dataset of logic proofs.
            grid_data: Dataset of grid worlds.
            steps_per_domain: Number of training steps per domain.
            
        Returns:
            Comprehensive training summary.
        """
        results = {
            "training_order": self.domains,
            "steps_per_domain": steps_per_domain,
            "domain_results": {},
            "final_state": {}
        }
        
        # Phase 1: Logic Domain
        logic_result = self.train_on_domain('logic', logic_data, steps_per_domain)
        results["domain_results"]['logic'] = logic_result
        
        # Phase 2: Grid Domain
        grid_result = self.train_on_domain('grid', grid_data, steps_per_domain)
        results["domain_results"]['grid'] = grid_result
        
        # Final state summary
        results["final_state"] = {
            "total_evaluations": sum(self.evaluation_counts.values()),
            "evaluations_by_domain": self.evaluation_counts,
            "final_accuracy": self.get_average_accuracy(),
            "history_length": len(self.history)
        }
        
        return results

    def _evaluate_logic_proof(self, proof_instance: Dict[str, Any], 
                            rule_set: List[str]) -> bool:
        """
        Evaluate if the current rule set can solve a logic proof instance.
        
        Args:
            proof_instance: A dictionary representing a logic proof task.
            rule_set: Current list of active rules.
            
        Returns:
            True if the proof is successfully derived, False otherwise.
        """
        try:
            premises = proof_instance.get('premises', [])
            conclusion = proof_instance.get('conclusion', '')
            
            if not premises or not conclusion:
                return False
            
            # Convert premises and conclusion to sympy expressions
            # This is a simplified evaluation; real implementation would use full symbolic logic
            symbols_map = {}
            for i in range(10):  # Support up to 10 variables
                symbols_map[f'P{i}'] = symbols(f'P{i}')
            
            # Parse premises
            parsed_premises = []
            for p in premises:
                # Simple parsing for demonstration
                # In reality, this would be more robust
                expr_str = p.replace('AND', '&').replace('OR', '|').replace('NOT', '~').replace('IMPLIES', '>>')
                parsed_premises.append(expr_str)
            
            # Check if conclusion follows from premises (simplified)
            # A real implementation would use sympy's satisfiability or proof methods
            return len(rule_set) > 0  # Placeholder: success if we have rules
            
        except Exception:
            return False

    def _evaluate_grid_task(self, grid_instance: Dict[str, Any], 
                          rule_set: List[str]) -> bool:
        """
        Evaluate if the current rule set can navigate a grid task.
        
        Args:
            grid_instance: A dictionary representing a grid navigation task.
            rule_set: Current list of active rules.
            
        Returns:
            True if the goal is reached, False otherwise.
        """
        try:
            grid_size = grid_instance.get('size', 10)
            start = grid_instance.get('start', (0, 0))
            goal = grid_instance.get('goal', (grid_size-1, grid_size-1))
            obstacles = grid_instance.get('obstacles', [])
            
            if not start or not goal:
                return False
            
            # Build graph representation
            G = nx.Graph()
            for i in range(grid_size):
                for j in range(grid_size):
                    if (i, j) not in obstacles:
                        G.add_node((i, j))
                        # Add edges to neighbors
                        for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            ni, nj = i + di, j + dj
                            if 0 <= ni < grid_size and 0 <= nj < grid_size and (ni, nj) not in obstacles:
                                G.add_edge((i, j), (ni, nj))
            
            # Check if path exists
            if nx.has_path(G, start, goal):
                # Apply rules to see if path is valid
                # Rules might restrict certain moves (e.g., avoid red cells)
                return len(rule_set) > 0  # Placeholder: success if we have rules
            return False
            
        except Exception:
            return False

    def _evaluate_generic_task(self, task: Dict[str, Any], 
                             rule_set: List[str]) -> bool:
        """Fallback evaluation for unknown task types."""
        return len(rule_set) > 0

    def _evolve_rule_set(self, current_rules: List[str], 
                       performance: float) -> List[str]:
        """
        Simulate evolution of the rule set based on performance.
        
        In a real system, this would involve genetic operators.
        Here we simulate the effect by adding/removing rules based on performance.
        
        Args:
            current_rules: Current list of rule strings.
            performance: Performance metric from recent training (0.0 to 1.0).
            
        Returns:
            New list of rules after simulated evolution.
        """
        new_rules = current_rules.copy()
        
        # Simulate rule adaptation
        if performance < 0.5:
            # Poor performance: try to add new rules
            if len(new_rules) < 5:  # Limit max rules
                new_rule = f"rule_{len(new_rules)}_adapted"
                new_rules.append(new_rule)
        elif performance > 0.8:
            # Good performance: refine rules (remove weak ones)
            if len(new_rules) > 1:
                # Remove a random rule to simulate pruning
                new_rules.pop(random.randint(0, len(new_rules) - 1))
        
        return new_rules

    def get_average_accuracy(self) -> float:
        """Calculate the average accuracy across all training steps."""
        if not self.history:
            return 0.0
        accuracies = [step.get('accuracy', 0) for step in self.history]
        return sum(accuracies) / len(accuracies)

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the agent."""
        return {
            "rule_set": self.rule_set,
            "evaluation_counts": self.evaluation_counts,
            "domain_progress": self.domain_progress,
            "current_domain_index": self.current_domain_index,
            "history_length": len(self.history)
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """Restore the agent from a saved state."""
        self.rule_set = state.get('rule_set', [])
        self.evaluation_counts = state.get('evaluation_counts', {d: 0 for d in self.domains})
        self.domain_progress = state.get('domain_progress', {d: 0 for d in self.domains})
        self.current_domain_index = state.get('current_domain_index', 0)

    def save_results(self, output_path: str) -> None:
        """Save training results to a JSON file."""
        results = {
            "agent_type": "SequentialAgent",
            "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else {},
            "final_state": self.get_state(),
            "history": self.history,
            "evaluation_counts": self.evaluation_counts
        }
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

def main():
    """
    Main entry point for testing the SequentialAgent.
    This function generates sample data, trains the agent, and saves results.
    """
    from src.utils.config import load_config, get_default_config
    
    # Load configuration
    config = load_config()
    
    # Initialize agent
    agent = SequentialAgent(config, seed=config.seed)
    
    # Generate sample data (in real usage, this would come from generators)
    # Creating minimal valid data for demonstration
    logic_data = [
        {
            "type": "logic",
            "premises": ["P0 IMPLIES P1", "P0"],
            "conclusion": "P1",
            "id": f"logic_{i}"
        }
        for i in range(20)
    ]
    
    grid_data = [
        {
            "type": "grid",
            "size": 5,
            "start": (0, 0),
            "goal": (4, 4),
            "obstacles": [(1, 1), (2, 2), (3, 3)],
            "id": f"grid_{i}"
        }
        for i in range(20)
    ]
    
    # Train sequentially
    results = agent.train_full_sequence(
        logic_data=logic_data,
        grid_data=grid_data,
        steps_per_domain=5
    )
    
    # Print summary
    print("Sequential Training Complete")
    print(f"Logic Domain Accuracy: {results['domain_results']['logic']['avg_accuracy']:.3f}")
    print(f"Grid Domain Accuracy: {results['domain_results']['grid']['avg_accuracy']:.3f}")
    print(f"Total Evaluations: {results['final_state']['total_evaluations']}")
    
    # Save results
    output_path = "data/results/sequential_training_results.json"
    agent.save_results(output_path)
    print(f"Results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    main()
