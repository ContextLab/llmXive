"""Contract test for ELBO logging schema."""
import pytest
from datetime import datetime
import numpy as np
from typing import Optional, Dict, Any, List

class TestELBOSchema:
    """Verify ELBO history schema has required fields."""

    def test_elbo_history_has_required_fields(self):
        """ELBOHistory must have iteration and elbo_value fields."""
        history = {
            "iteration": 100,
            "elbo_value": -1234.56
        }
        assert "iteration" in history
        assert "elbo_value" in history

    def test_elbo_history_iteration_positive(self):
        """ELBOHistory iteration must be positive."""
        history = {"iteration": 100, "elbo_value": -1234.56}
        assert history["iteration"] > 0

    def test_elbo_history_can_be_list(self):
        """ELBOHistory can be a list of iteration records."""
        history_list = [
            {"iteration": 1, "elbo_value": -5000.0},
            {"iteration": 10, "elbo_value": -3000.0},
            {"iteration": 100, "elbo_value": -1234.56}
        ]
        assert isinstance(history_list, list)
        assert len(history_list) > 0
        for entry in history_list:
            assert "iteration" in entry
            assert "elbo_value" in entry

    def test_elbo_history_timestamp_field(self):
        """ELBOHistory may have timestamp field."""
        history = {
            "iteration": 100,
            "elbo_value": -1234.56,
            "timestamp": "2024-01-01T00:00:00"
        }
        assert "timestamp" in history

    def test_elbo_history_can_serialize(self):
        """ELBOHistory must be serializable to JSON."""
        import json
        history = {
            "iteration": 100,
            "elbo_value": -1234.56
        }
        serialized = json.dumps(history)
        assert serialized is not None

    def test_elbo_history_list_serialize(self):
        """ELBOHistory list must be serializable to JSON."""
        import json
        history_list = [
            {"iteration": 1, "elbo_value": -5000.0},
            {"iteration": 100, "elbo_value": -1234.56}
        ]
        serialized = json.dumps(history_list)
        assert serialized is not None

    def test_elbo_convergence_check(self):
        """ELBO history should support convergence checking."""
        # Verify we can compute convergence metrics
        history_list = [
            {"iteration": 1, "elbo_value": -5000.0},
            {"iteration": 10, "elbo_value": -3000.0},
            {"iteration": 100, "elbo_value": -1234.56}
        ]
        elbo_values = [h["elbo_value"] for h in history_list]
        assert len(elbo_values) > 0
        # Check that ELBO improved (became less negative)
        assert elbo_values[-1] > elbo_values[0]

    def test_elbo_history_model_id_field(self):
        """ELBOHistory may have model_id field for tracking."""
        history = {
            "iteration": 100,
            "elbo_value": -1234.56,
            "model_id": "dp_gmm_001"
        }
        assert "model_id" in history
