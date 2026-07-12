"""
Unit tests for code/symbolic/planner.py
Specifically testing edge cases: non-linear constraints and impossible goals.
"""
import pytest
import sys
import os
from pathlib import Path

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.symbolic.planner import SymbolicPlanner
from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, raise_parse_failure, raise_contradiction

class TestSymbolicPlannerEdgeCases:
    """Tests for planner handling of edge cases."""

    def setup_method(self):
        """Initialize the planner for each test."""
        self.planner = SymbolicPlanner()

    def test_planner_handles_nonlinear_constraints(self):
        """
        Test that the planner correctly processes and decomposes non-linear constraints.
        
        Non-linear constraints here refer to constraints where the solution path
        is not a simple linear sequence but involves branching or dependency loops,
        e.g., "To reach C, you must have visited A AND B", where A and B are independent.
        """
        # Define a puzzle with non-linear dependency: Goal requires (A and B)
        # represented in the internal constraint format.
        # Assuming the parser converts natural language to a structure like:
        # {'goal': 'Reach_C', 'preconditions': [{'type': 'AND', 'items': ['Visited_A', 'Visited_B']}]}
        
        test_constraints = {
            "start": "Node_Start",
            "goal": "Node_Goal",
            "nodes": ["Node_Start", "Node_A", "Node_B", "Node_Goal"],
            "edges": [
                ("Node_Start", "Node_A"),
                ("Node_Start", "Node_B"),
                ("Node_A", "Node_Goal"),
                ("Node_B", "Node_Goal")
            ],
            "nonlinear_constraints": [
                {
                    "target": "Node_Goal",
                    "condition": "AND",
                    "requirements": ["Node_A", "Node_B"]
                }
            ]
        }

        # The planner should decompose this into sub-goals:
        # 1. Reach Node_A
        # 2. Reach Node_B
        # 3. Reach Node_Goal (only after 1 and 2)
        
        sub_goals = self.planner.generate_sub_goals(test_constraints)
        
        assert sub_goals is not None, "Sub-goals should not be None"
        assert len(sub_goals) >= 2, "Non-linear constraints should generate multiple sub-goals"
        
        # Verify that the specific requirements are present in the sub-goals
        goal_targets = [g.get('target') for g in sub_goals if 'target' in g]
        assert "Node_A" in goal_targets, "Sub-goal for Node_A should exist"
        assert "Node_B" in goal_targets, "Sub-goal for Node_B should exist"
        assert "Node_Goal" in goal_targets, "Sub-goal for Node_Goal should exist"

    def test_planner_handles_impossible_goals(self):
        """
        Test that the planner raises CONTRADICTION_DETECTED when the goal is unreachable
        due to missing edges or conflicting constraints.
        """
        # Define a puzzle where the goal is isolated (no path from start)
        impossible_constraints = {
            "start": "Node_Start",
            "goal": "Node_Isolated_Goal",
            "nodes": ["Node_Start", "Node_Isolated_Goal"],
            "edges": [], # No edges connect start to goal
            "nonlinear_constraints": []
        }

        # The planner should detect that no path exists or constraints are contradictory
        # and raise the appropriate exception.
        with pytest.raises(CONTRADICTION_DETECTED):
            self.planner.generate_sub_goals(impossible_constraints)

    def test_planner_handles_parse_failure_on_malformed_input(self):
        """
        Test that the planner raises PARSE_FAILURE when given malformed constraints.
        """
        malformed_constraints = {
            "start": 123, # Invalid type for start node
            "goal": "Node_Goal",
            "nodes": None, # Invalid type for nodes
            "edges": "invalid_edges",
            "nonlinear_constraints": []
        }

        with pytest.raises(PARSE_FAILURE):
            self.planner.generate_sub_goals(malformed_constraints)

    def test_planner_handles_impossible_nonlinear_constraints(self):
        """
        Test a scenario where a non-linear constraint is logically impossible.
        E.g., Goal requires visiting a node that has no incoming edges.
        """
        impossible_nonlinear = {
            "start": "Node_Start",
            "goal": "Node_Goal",
            "nodes": ["Node_Start", "Node_Goal", "Node_Unreachable"],
            "edges": [
                ("Node_Start", "Node_Goal")
            ],
            "nonlinear_constraints": [
                {
                    "target": "Node_Goal",
                    "condition": "AND",
                    "requirements": ["Node_Unreachable"] # Node_Unreachable has no incoming edges
                }
            ]
        }

        # The planner should detect that the requirement "Node_Unreachable" cannot be met
        # from the start node and raise CONTRADICTION_DETECTED.
        with pytest.raises(CONTRADICTION_DETECTED):
            self.planner.generate_sub_goals(impossible_nonlinear)
