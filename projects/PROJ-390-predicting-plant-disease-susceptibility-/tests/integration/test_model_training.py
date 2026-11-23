"""
Integration test for model training pipeline (Task T018).

Verifies model output structure.
"""
import pytest
import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class TestModelTrainingIntegration:
    """Integration tests for model training."""

    @pytest.fixture
    def contracts_dir(self):
        return project_root / "data" / "contracts"

    @pytest.fixture
    def processed_dir(self):
        return project_root / "data" / "processed"

    def test_model_output_schema_exists(self, contracts_dir):
        """Verify the model_output schema exists."""
        schema_path = contracts_dir / "model_output.schema.yaml"
        assert schema_path.exists(), "Model output schema missing"

    def test_model_performance_generated(self, processed_dir):
        """Verify model_performance.json is generated (if pipeline ran)."""
        perf_path = processed_dir / "model_performance.json"
        if perf_path.exists():
            with open(perf_path, 'r') as f:
                data = json.load(f)
            assert 'model_name' in data
            assert 'metrics' in data
        else:
            pytest.skip("model_performance.json not yet generated (T021 pending)")