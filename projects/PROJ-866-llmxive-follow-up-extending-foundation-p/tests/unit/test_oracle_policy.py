"""
Unit tests for the Oracle Policy Engine.
"""

import pytest
from code.engines.oracle_policy import OraclePolicyEngine


class TestOraclePolicyEngine:
    """Tests for the OraclePolicyEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = OraclePolicyEngine()
        self.valid_workflow = {
            "id": "wf_valid",
            "nodes": {
                "N1": {"depth": 1, "resource_cost": 10, "accesses_data": ["D1"], "allowed_data_access": ["D1"]},
                "N2": {"depth": 2, "resource_cost": 20, "accesses_data": [], "allowed_data_access": []}
            },
            "edges": [{"source": "N1", "target": "N2"}],
            "parents": {"N1": [], "N2": ["N1"]}
        }
        self.invalid_workflow = {
            "id": "wf_invalid",
            "nodes": {
                "N1": {"depth": 1, "resource_cost": 10, "accesses_data": [], "allowed_data_access": []},
                "N2": {"depth": 2, "resource_cost": 20, "accesses_data": ["D2"], "allowed_data_access": []}
            },
            "edges": [{"source": "N1", "target": "N2"}],
            "parents": {"N1": [], "N2": ["N1"]}
        }

    def test_validate_step_valid(self):
        """Test validation of a valid step."""
        is_valid, reason = self.engine.validate_step(
            current_node_id="N1",
            current_node_data=self.valid_workflow["nodes"]["N1"],
            workflow_graph=self.valid_workflow,
            execution_log=[]
        )
        assert is_valid is True
        assert reason is None

    def test_validate_step_dependency_violation(self):
        """Test validation fails if dependency not met."""
        # Try to execute N2 before N1
        is_valid, reason = self.engine.validate_step(
            current_node_id="N2",
            current_node_data=self.valid_workflow["nodes"]["N2"],
            workflow_graph=self.valid_workflow,
            execution_log=[]
        )
        assert is_valid is False
        assert "Dependency violation" in reason

    def test_validate_step_data_sovereignty_violation(self):
        """Test validation fails if data access is denied."""
        is_valid, reason = self.engine.validate_step(
            current_node_id="N2",
            current_node_data=self.invalid_workflow["nodes"]["N2"],
            workflow_graph=self.invalid_workflow,
            execution_log=[{"node_id": "N1"}]
        )
        assert is_valid is False
        assert "Data sovereignty violation" in reason

    def test_validate_workflow_valid(self):
        """Test full workflow validation for a valid graph."""
        plan = ["N1", "N2"]
        results = self.engine.validate_workflow(self.valid_workflow, plan)
        assert all(r["is_valid"] for r in results)

    def test_validate_workflow_invalid(self):
        """Test full workflow validation for an invalid graph."""
        plan = ["N1", "N2"]
        results = self.engine.validate_workflow(self.invalid_workflow, plan)
        # N1 should be valid, N2 should be invalid
        assert results[0]["is_valid"] is True
        assert results[1]["is_valid"] is False
        assert "Data sovereignty violation" in results[1]["reason"]

    def test_get_ground_truth_log(self):
        """Test generation of ground truth log."""
        result = self.engine.get_ground_truth_log(self.valid_workflow)
        assert "workflow_id" in result
        assert "execution_order" in result
        assert result["is_valid"] is True
        assert len(result["violations"]) == 0

    def test_get_ground_truth_log_invalid(self):
        """Test generation of ground truth log for invalid workflow."""
        result = self.engine.get_ground_truth_log(self.invalid_workflow)
        assert result["is_valid"] is False
        assert len(result["violations"]) > 0
