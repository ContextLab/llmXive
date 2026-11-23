"""
Tests for generate_test_params module.
"""
import json
import tempfile
from pathlib import Path
import pytest

from generate_test_params import get_default_test_params, save_test_params


class TestGenerateTestParams:
    """Tests for parameter generation and saving."""

    def test_get_default_test_params_structure(self):
        """Verify the structure of default test parameters."""
        params = get_default_test_params()
        
        assert "maxwell_boltzmann" in params
        assert "pareto" in params
        assert "metadata" in params

    def test_maxwell_boltzmann_parameters(self):
        """Verify Maxwell-Boltzmann parameters match specification."""
        params = get_default_test_params()
        mb = params["maxwell_boltzmann"]
        
        assert mb["mean"] == pytest.approx(1.0)
        assert mb["scale"] == pytest.approx(0.1)
        assert "description" in mb

    def test_pareto_parameters(self):
        """Verify Pareto parameters match specification."""
        params = get_default_test_params()
        pareto = params["pareto"]
        
        assert pareto["shape"] == pytest.approx(2.0)
        assert "description" in pareto

    def test_save_and_load_params(self):
        """Verify parameters can be saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_params.json"
            
            params = get_default_test_params()
            save_test_params(params, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded_params = json.load(f)
            
            assert loaded_params == params

    def test_json_format(self):
        """Verify the saved JSON is valid and properly formatted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_params.json"
            
            params = get_default_test_params()
            save_test_params(params, output_path)
            
            with open(output_path, 'r') as f:
                content = f.read()
            
            # Verify it's valid JSON
                loaded = json.loads(content)
            
            # Verify indentation (pretty-printed)
            assert "  " in content  # Should have spaces for indentation
            assert loaded["maxwell_boltzmann"]["mean"] == 1.0
            assert loaded["pareto"]["shape"] == 2.0