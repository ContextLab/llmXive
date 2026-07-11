import random
from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx
from src.utils.config import Config
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator

class MixedAgent(BaseAgent):
    """
    Agent that trains on mixed task domains randomly per generation.
    
    This agent implements the Mixed-task condition for User Story 2.
    At each generation step, it randomly selects a task domain (logic or grid)
    and generates a sample from that domain to evaluate against the current rule set.
    """

    def __init__(self, config: Config, seed: Optional[int] = None):
        super().__init__(config, seed)
        self.logic_generator = LogicProofGenerator(config)
        self.grid_generator = GridWorldGenerator(config)
        self.evaluation_history: List[Dict[str, Any]] = []
        self.rule_evaluation_count = 0
        self.current_rule_set: Optional[Dict[str, Any]] = None
        
        # Initialize rule set based on config
        self._initialize_rule_set()

    def _initialize_rule_set(self):
        """Initialize the agent's rule set based on configuration."""
        if self.config.initial_rule_set:
            self.current_rule_set = self.config.initial_rule_set
        else:
            # Create a default empty rule set
            self.current_rule_set = {
                "logic_rules": [],
                "grid_rules": [],
                "metadata": {
                    "created_at": self._get_timestamp(),
                    "version": "1.0"
                }
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat()

    def train_generation(self) -> Dict[str, Any]:
        """
        Execute one generation of training with mixed task domains.
        
        Randomly selects between logic and grid tasks, generates a sample,
        evaluates the current rule set, and updates internal state.
        
        Returns:
            Dict containing generation results including task type, evaluation score,
            and updated rule evaluation count.
        """
        # Randomly select task domain (50/50 chance)
        task_type = random.choice(["logic", "grid"])
        
        if task_type == "logic":
            result = self._train_logic_generation()
        else:
            result = self._train_grid_generation()
        
        # Record history
        self.evaluation_history.append({
            "generation": len(self.evaluation_history),
            "task_type": task_type,
            "rule_evaluations": self.rule_evaluation_count,
            "result": result
        })
        
        return {
            "task_type": task_type,
            "rule_evaluations": self.rule_evaluation_count,
            "current_score": result.get("score", 0.0),
            "rule_set_updated": result.get("updated", False)
        }

    def _train_logic_generation(self) -> Dict[str, Any]:
        """
        Train on a single logic proof generation step.
        
        Generates a logic proof, evaluates the current rule set against it,
        and potentially updates the rule set based on performance.
        
        Returns:
            Dict with score, updated flag, and generation details.
        """
        try:
            # Generate a logic proof instance
            proof_data = self.logic_generator.generate_single_proof()
            
            if not proof_data:
                return {"score": 0.0, "updated": False, "error": "Generation failed"}
            
            # Evaluate current rule set against the proof
            score, rule_changes = self._evaluate_logic_rule_set(proof_data)
            
            # Apply rule set updates if any
            updated = False
            if rule_changes:
                self.current_rule_set["logic_rules"].extend(rule_changes)
                updated = True
                self.rule_evaluation_count += len(rule_changes)
            else:
                self.rule_evaluation_count += 1
            
            return {
                "score": score,
                "updated": updated,
                "proof_id": proof_data.get("id"),
                "rule_count": len(self.current_rule_set["logic_rules"])
            }
            
        except Exception as e:
            return {"score": 0.0, "updated": False, "error": str(e)}

    def _train_grid_generation(self) -> Dict[str, Any]:
        """
        Train on a single grid world generation step.
        
        Generates a grid world, evaluates the current rule set against it,
        and potentially updates the rule set based on performance.
        
        Returns:
            Dict with score, updated flag, and generation details.
        """
        try:
            # Generate a grid world instance
            grid_data = self.grid_generator.generate_single_grid()
            
            if not grid_data:
                return {"score": 0.0, "updated": False, "error": "Generation failed"}
            
            # Evaluate current rule set against the grid
            score, rule_changes = self._evaluate_grid_rule_set(grid_data)
            
            # Apply rule set updates if any
            updated = False
            if rule_changes:
                self.current_rule_set["grid_rules"].extend(rule_changes)
                updated = True
                self.rule_evaluation_count += len(rule_changes)
            else:
                self.rule_evaluation_count += 1
            
            return {
                "score": score,
                "updated": updated,
                "grid_id": grid_data.get("id"),
                "rule_count": len(self.current_rule_set["grid_rules"])
            }
            
        except Exception as e:
            return {"score": 0.0, "updated": False, "error": str(e)}

    def _evaluate_logic_rule_set(self, proof_data: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Evaluate the current rule set against a logic proof.
        
        Args:
            proof_data: Generated logic proof data structure.
        
        Returns:
            Tuple of (score, list of new rules learned/updated).
        """
        if not self.current_rule_set:
            return 0.0, []
        
        # Simple evaluation: check if proof matches any existing rules
        # In a real implementation, this would use sympy to verify logical consistency
        score = 0.0
        new_rules = []
        
        # Extract logical components from proof
        premises = proof_data.get("premises", [])
        conclusion = proof_data.get("conclusion")
        
        # Evaluate based on rule coverage
        if self.current_rule_set["logic_rules"]:
            # Calculate coverage score
            covered = 0
            for rule in self.current_rule_set["logic_rules"]:
                if self._logic_rule_matches(premises, conclusion, rule):
                    covered += 1
            score = covered / max(len(self.current_rule_set["logic_rules"]), 1)
        else:
            # No rules yet, generate a new rule from the proof
            if premises and conclusion:
                new_rule = {
                    "premises": premises,
                    "conclusion": conclusion,
                    "confidence": 1.0,
                    "source": "mixed_generation"
                }
                new_rules.append(new_rule)
                score = 1.0
        
        return score, new_rules

    def _evaluate_grid_rule_set(self, grid_data: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Evaluate the current rule set against a grid world.
        
        Args:
            grid_data: Generated grid world data structure.
        
        Returns:
            Tuple of (score, list of new rules learned/updated).
        """
        if not self.current_rule_set:
            return 0.0, []
        
        score = 0.0
        new_rules = []
        
        grid_size = grid_data.get("size", (5, 5))
        obstacles = grid_data.get("obstacles", [])
        start_pos = grid_data.get("start")
        end_pos = grid_data.get("end")
        rules = grid_data.get("rules", [])
        
        # Evaluate based on rule adherence
        if self.current_rule_set["grid_rules"]:
            # Check how many existing rules are satisfied
            satisfied = 0
            for rule in self.current_rule_set["grid_rules"]:
                if self._grid_rule_satisfied(grid_size, obstacles, start_pos, end_pos, rule):
                    satisfied += 1
            score = satisfied / max(len(self.current_rule_set["grid_rules"]), 1)
        else:
            # No rules yet, derive rules from the grid configuration
            if rules:
                for rule in rules:
                    new_rules.append({
                        "type": rule.get("type"),
                        "parameters": rule.get("parameters", {}),
                        "confidence": 1.0,
                        "source": "mixed_generation"
                    })
                score = 1.0
        
        return score, new_rules

    def _logic_rule_matches(self, premises: List[str], conclusion: str, rule: Dict[str, Any]) -> bool:
        """
        Check if a logic rule matches the current premises and conclusion.
        
        Args:
            premises: List of premise strings.
            conclusion: Conclusion string.
            rule: Rule dictionary with premises and conclusion.
        
        Returns:
            True if the rule matches, False otherwise.
        """
        rule_premises = rule.get("premises", [])
        rule_conclusion = rule.get("conclusion")
        
        # Simple string comparison for now
        # In a real implementation, use sympy for logical equivalence
        if set(premises) == set(rule_premises) and conclusion == rule_conclusion:
            return True
        return False

    def _grid_rule_satisfied(self, size: Tuple[int, int], obstacles: List[Tuple[int, int]], 
                             start: Tuple[int, int], end: Tuple[int, int], 
                             rule: Dict[str, Any]) -> bool:
        """
        Check if a grid rule is satisfied by the current grid configuration.
        
        Args:
            size: Grid dimensions.
            obstacles: List of obstacle coordinates.
            start: Starting position.
            end: Ending position.
            rule: Rule dictionary with type and parameters.
        
        Returns:
            True if the rule is satisfied, False otherwise.
        """
        rule_type = rule.get("type")
        params = rule.get("parameters", {})
        
        if rule_type == "avoid_color":
            # Check if path avoids red cells (simplified)
            # In real implementation, would check actual grid colors
            return True
        elif rule_type == "diagonal_movement":
            # Check if diagonal movement is allowed
            return params.get("allowed", False)
        elif rule_type == "shortest_path":
            # Check if path is shortest (simplified)
            return True
        
        return True  # Default to satisfied for unknown rules

    def get_rule_set(self) -> Dict[str, Any]:
        """Return the current rule set."""
        return self.current_rule_set

    def get_evaluation_history(self) -> List[Dict[str, Any]]:
        """Return the evaluation history."""
        return self.evaluation_history

    def get_rule_evaluation_count(self) -> int:
        """Return the total number of rule evaluations."""
        return self.rule_evaluation_count

    def reset(self):
        """Reset the agent to initial state."""
        self.evaluation_history = []
        self.rule_evaluation_count = 0
        self._initialize_rule_set()
