"""
Base abstract agent class defining the interface for rule-set management and evaluation.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import random

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the co-evolving policy distillation system.
    Defines the standard interface for training, evaluation, and rule-set management.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with configuration parameters.

        Args:
            config: Dictionary containing seeding, generation counts, and rule evaluation budgets.
        """
        self.config = config
        self.seed = config.get('seed', 42)
        random.seed(self.seed)
        self.rule_evaluations = 0
        self.total_rules = 0
        self.performance_history: List[Dict[str, Any]] = []

    @abstractmethod
    def train_step(self, task_data: Dict[str, Any]) -> float:
        """
        Execute a single training step on the provided task data.

        Args:
            task_data: Dictionary containing the current task instance (proof or grid).

        Returns:
            float: The performance score (accuracy/success rate) for this step.
        """
        pass

    @abstractmethod
    def evaluate(self, test_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate the agent's performance on a held-out test set.

        Args:
            test_data: List of task instances to evaluate against.

        Returns:
            Dictionary containing performance metrics (e.g., 'accuracy', 'retention_rate').
        """
        pass

    @abstractmethod
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Retrieve the current set of rules maintained by the agent.

        Returns:
            List of rule dictionaries representing the agent's current policy.
        """
        pass

    @abstractmethod
    def set_rules(self, rules: List[Dict[str, Any]]) -> None:
        """
        Update the agent's rule set with a new set of rules.

        Args:
            rules: List of rule dictionaries to adopt.
        """
        pass

    def increment_evaluations(self, count: int = 1) -> None:
        """
        Increment the rule evaluation counter.

        Args:
            count: Number of evaluations to add.
        """
        self.rule_evaluations += count

    def get_state(self) -> Dict[str, Any]:
        """
        Serialize the agent's current state for checkpointing.

        Returns:
            Dictionary containing the agent's state.
        """
        return {
            'seed': self.seed,
            'rule_evaluations': self.rule_evaluations,
            'total_rules': self.total_rules,
            'performance_history': self.performance_history,
            'rules': self.get_rules()
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Restore the agent's state from a checkpoint.

        Args:
            state: Dictionary containing the saved state.
        """
        self.seed = state.get('seed', self.seed)
        self.rule_evaluations = state.get('rule_evaluations', 0)
        self.total_rules = state.get('total_rules', 0)
        self.performance_history = state.get('performance_history', [])
        if 'rules' in state:
            self.set_rules(state['rules'])
