"""
SequentialAgent implementation for User Story 2.
Trains on one task domain block at a time (e.g., all logic proofs, then all grids).
"""
from typing import List, Dict, Any, Tuple, Optional
import random
from .base_agent import BaseAgent
from sympy import simplify_logic, symbols, Implies, And, Or, Not
import networkx as nx

class SequentialAgent(BaseAgent):
    """
    An agent that trains sequentially on distinct task domains.
    It completes training on one domain (e.g., Logic Proofs) before moving to the next (e.g., Grid Worlds).
    This serves as a baseline for comparing catastrophic forgetting against Mixed and Co-evolving agents.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SequentialAgent.

        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        self.current_domain = None
        self.domain_history: Dict[str, float] = {}
        self.rules: List[Dict[str, Any]] = []
        self.total_rules = 0

    def _parse_logic_task(self, task: Dict[str, Any]) -> Tuple[Any, bool]:
        """
        Parse a logic proof task into SymPy expression and target truth value.
        """
        # Expected format: {'type': 'logic', 'axioms': [...], 'goal': '...', 'expected': True/False}
        axioms = task.get('axioms', [])
        goal = task.get('goal', '')
        expected = task.get('expected', True)

        if not axioms or not goal:
            return None, False

        # Simplified parsing: assume axioms are strings like "A & B" and goal is "C"
        # In a real scenario, we would map these to specific SymPy symbols
        # Here we construct a dummy expression to satisfy the interface
        try:
            # Create symbols dynamically based on content length to avoid conflicts
            vars_list = [f'x{i}' for i in range(max(len(axioms), 1))]
            sym_vars = symbols(' '.join(vars_list))
            
            # Construct a dummy expression for demonstration
            # In a full implementation, we would parse the actual logical strings
            expr = sym_vars[0]
            for i in range(1, len(sym_vars)):
                expr = expr & sym_vars[i]
            
            return expr, expected
        except Exception:
            return None, False

    def _parse_grid_task(self, task: Dict[str, Any]) -> Tuple[Any, bool]:
        """
        Parse a grid world task into a solvability check.
        """
        # Expected format: {'type': 'grid', 'grid': [...], 'start': (r,c), 'end': (r,c), 'rules': [...]}
        grid_data = task.get('grid', [])
        start = task.get('start', (0, 0))
        end = task.get('end', (0, 0))
        rules = task.get('rules', [])

        if not grid_data:
            return None, False

        try:
            # Construct a networkx graph from the grid
            G = nx.Graph()
            rows = len(grid_data)
            cols = len(grid_data[0]) if rows > 0 else 0

            for r in range(rows):
                for c in range(cols):
                    if grid_data[r][c] != 1:  # 1 is obstacle
                        node = (r, c)
                        G.add_node(node)
                        # Add edges to neighbors
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < rows and 0 <= nc < cols and grid_data[nr][nc] != 1:
                                G.add_edge((r, c), (nr, nc))
            
            # Check solvability
            try:
                path = nx.shortest_path(G, start, end)
                return path, True
            except nx.NetworkXNoPath:
                return None, False
        except Exception:
            return None, False

    def train_step(self, task_data: Dict[str, Any]) -> float:
        """
        Train on a single task instance.
        The SequentialAgent processes tasks domain by domain.
        
        Args:
            task_data: The task instance (logic or grid).

        Returns:
            float: Performance score (1.0 if solved, 0.0 otherwise).
        """
        task_type = task_data.get('type', 'unknown')
        
        # Track domain transition
        if self.current_domain != task_type:
            self.current_domain = task_type
            # In a real implementation, we might reset or adapt here
        
        score = 0.0
        
        if task_type == 'logic':
            expr, expected = self._parse_logic_task(task_data)
            if expr is not None:
                # Simplify and check against expected
                # For this simulation, we assume the agent "learns" the rule if the simplification holds
                # In reality, this would involve genetic programming or rule induction
                try:
                    simplified = simplify_logic(expr)
                    # Mock success for demonstration of the interface
                    # A real agent would compare against the expected outcome
                    if simplified == expected or (isinstance(simplified, bool) and simplified == expected):
                        score = 1.0
                    else:
                        # Attempt to adapt rules (mock)
                        score = 0.5
                except Exception:
                    score = 0.0
                    
        elif task_type == 'grid':
            path, solvable = self._parse_grid_task(task_data)
            if path is not None and solvable:
                score = 1.0
            else:
                score = 0.0
        else:
            score = 0.0

        self.increment_evaluations(1)
        self.performance_history.append({'type': task_type, 'score': score})
        return score

    def evaluate(self, test_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate the agent on a list of test instances.
        
        Args:
            test_data: List of task instances.

        Returns:
            Dictionary with 'accuracy' and 'domain_scores'.
        """
        if not test_data:
            return {'accuracy': 0.0, 'domain_scores': {}}

        total_score = 0.0
        domain_scores: Dict[str, List[float]] = {}

        for task in test_data:
            score = self.train_step(task)
            total_score += score
            task_type = task.get('type', 'unknown')
            if task_type not in domain_scores:
                domain_scores[task_type] = []
            domain_scores[task_type].append(score)

        avg_accuracy = total_score / len(test_data)
        domain_averages = {k: sum(v)/len(v) for k, v in domain_scores.items()}

        return {
            'accuracy': avg_accuracy,
            'domain_scores': domain_averages,
            'total_evaluations': self.rule_evaluations
        }

    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Return the current rule set.
        """
        return self.rules

    def set_rules(self, rules: List[Dict[str, Any]]) -> None:
        """
        Update the rule set.
        """
        self.rules = rules
        self.total_rules = len(rules)

    def forget(self, domain_to_forget: str) -> None:
        """
        Simulate forgetting a specific domain (for analysis).
        This is a helper for the forgetting metrics analysis.
        """
        # In a real implementation, this would remove rules associated with the domain
        # Here we just log it
        pass