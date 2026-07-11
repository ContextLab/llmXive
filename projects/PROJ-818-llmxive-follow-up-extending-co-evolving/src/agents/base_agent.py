"""
Base abstract agent class for the Co-Evolving Policy Distillation pipeline.

This module defines the interface for rule-set management and evaluation
that all specific agent implementations (Sequential, Mixed, Co-evolving)
must adhere to.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import hashlib
import json
import logging

from ..utils.config import Config
from ..utils.checksums import ChecksumManager

logger = logging.getLogger(__name__)


@dataclass
class RuleSet:
    """Represents a distinct set of logical rules or navigation policies."""
    rules: List[Dict[str, Any]]
    task_domain: str  # e.g., 'logic' or 'grid'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Generate a hash based on the rule content for deduplication."""
        content_str = json.dumps(self.rules, sort_keys=True)
        return int(hashlib.sha256(content_str.encode()).hexdigest(), 16)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RuleSet):
            return False
        return self.rules == other.rules and self.task_domain == other.task_domain


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the distillation pipeline.

    Defines the core interface for:
    - Managing rule-sets (population)
    - Evaluating performance on tasks
    - Updating internal state based on feedback
    """

    def __init__(self, config: Config, checksum_manager: Optional[ChecksumManager] = None):
        """
        Initialize the agent.

        Args:
            config: Project configuration containing seeds and hyperparameters.
            checksum_manager: Optional manager for tracking data integrity.
        """
        self.config = config
        self.checksum_manager = checksum_manager
        self.population: List[RuleSet] = []
        self.evaluation_history: List[Dict[str, float]] = []
        self.total_rule_evaluations: int = 0
        self.task_history: List[str] = []

    @abstractmethod
    def initialize_population(self, seed: int) -> None:
        """
        Initialize the agent's population of rule-sets.

        Args:
            seed: Random seed for reproducibility.
        """
        pass

    @abstractmethod
    def evaluate(self, tasks: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate the current population against a set of tasks.

        Args:
            tasks: List of task instances (proofs or grid worlds).

        Returns:
            Dictionary of evaluation metrics (e.g., accuracy, success rate).
        """
        pass

    @abstractmethod
    def update(self, feedback: Dict[str, Any]) -> None:
        """
        Update the agent's internal state based on evaluation feedback.

        Args:
            feedback: Results from the evaluation step.
        """
        pass

    @abstractmethod
    def get_best_rule_set(self) -> Optional[RuleSet]:
        """
        Retrieve the best performing rule-set from the current population.

        Returns:
            The best RuleSet or None if population is empty.
        """
        pass

    def track_evaluation(self, metrics: Dict[str, float]) -> None:
        """Record evaluation metrics for analysis."""
        self.evaluation_history.append(metrics)
        logger.debug(f"Evaluated agent: {metrics}")

    def increment_rule_evaluations(self, count: int) -> None:
        """Increment the total rule evaluation counter."""
        self.total_rule_evaluations += count

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the agent for serialization.

        Returns:
            Dictionary containing agent state.
        """
        return {
            "population_size": len(self.population),
            "total_rule_evaluations": self.total_rule_evaluations,
            "evaluation_history_len": len(self.evaluation_history),
            "task_history_len": len(self.task_history)
        }

    def apply_mutation(self, rule_set: RuleSet, mutation_rate: float = 0.1) -> RuleSet:
        """
        Apply a mutation to a rule-set.

        Note: This is a default implementation; specific agents may override.
        """
        # Placeholder logic: deep copy and potentially modify
        new_rules = []
        for rule in rule_set.rules:
            if hash(str(rule)) % 100 < (mutation_rate * 100):
                # Simple mutation: add a random tag
                mutated_rule = rule.copy()
                mutated_rule['_mutated'] = True
                new_rules.append(mutated_rule)
            else:
                new_rules.append(rule)
        
        return RuleSet(
            rules=new_rules,
            task_domain=rule_set.task_domain,
            metadata={**rule_set.metadata, "mutated": True}
        )

    def validate_population(self) -> bool:
        """
        Ensure the current population is valid (non-empty, consistent domains).

        Returns:
            True if valid, False otherwise.
        """
        if not self.population:
            logger.warning("Population is empty.")
            return False
        
        # Optional: Check for consistency if required by specific agents
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(pop_size={len(self.population)}, evals={self.total_rule_evaluations})"
