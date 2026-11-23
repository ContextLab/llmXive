"""
Integration tests for the cost curve generation (T029).
Verifies that the report generator produces valid JSON and PNG artifacts.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import numpy as np
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.report_generator import (
    load_ablation_results,
    load_ablation_stats,
    count_active_constraints,
    generate_cost_curve,
    COST_CURVE_JSON_PATH,
    COST_CURVE_PNG_PATH
)

class TestCostCurveGeneration:
    """Tests for T029: Cost Curve Generation"""

    def test_count_active_constraints_logic(self):
        """Verify the constraint counting logic matches T026a definitions."""
        assert count_active_constraints("full") == 3
        assert count_active_constraints("no_recurrence") == 2
        assert count_active_constraints("no_inhibition") == 2
        assert count_active_constraints("no_homeostasis") == 2
        assert count_active_constraints("no_recurrence_no_inhibition") == 1
        assert count_active_constraints("no_constraints") == 0
        assert count_active_constraints("unknown_variant") == 3  # Default fallback

    def test_generate_cost_curve_creates_files(self, tmp_path):
        """
        Test that generate_cost_curve creates the required JSON and PNG files.
        This test mocks the input data to ensure the function runs end-to-end.
        """
        # Create temporary directories for data/results
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock ablation_results.json
        mock_results = {
            "variants": [
                {"name": "full", "mae": 0.05, "active_constraints": 3},
                {"name": "no_recurrence", "mae": 0.08, "active_constraints": 2},
                {"name": "no_inhibition", "mae": 0.09, "active_constraints": 2},
                {"name": "no_homeostasis", "mae": 0.12, "active_constraints": 2},
                {"name": "no_constraints", "mae": 0.25, "active_constraints": 0}
            ]
        }
        
        mock_results_path = results_dir / "ablation_results.json"
        with open(mock_results_path, 'w') as f:
            json.dump(mock_results, f)
        
        # Temporarily override the module's path constants
        original_json_path = generate_cost_curve.__globals__.get('ABULATION_RESULTS_PATH')
        original_json_out = generate_cost_curve.__globals__.get('COST_CURVE_JSON_PATH')
        original_png_out = generate_cost_curve.__globals__.get('COST_CURVE_PNG_PATH')
        
        # We need to patch the global variables used inside the function
        # Since the function reads global constants defined at module level, 
        # we patch the module's globals directly for the duration of the test.
        import src.utils.report_generator as rg_module
        
        rg_module.ABULATION_RESULTS_PATH = str(mock_results_path)
        rg_module.COST_CURVE_JSON_PATH = str(results_dir / "test_cost_curve.json")
        rg_module.COST_CURVE_PNG_PATH = str(results_dir / "test_cost_curve.png")
        
        try:
            data, png_path = rg_module.generate_cost_curve()
            
            # Verify JSON file exists and is valid
            assert os.path.exists(rg_module.COST_CURVE_JSON_PATH), "JSON output file not created"
            with open(rg_module.COST_CURVE_JSON_PATH, 'r') as f:
                loaded_json = json.load(f)
            
            assert "data_points" in loaded_json
            assert len(loaded_json["data_points"]) > 0
            
            # Verify PNG file exists
            assert os.path.exists(rg_module.COST_CURVE_PNG_PATH), "PNG output file not created"
            assert os.path.getsize(rg_module.COST_CURVE_PNG_PATH) > 0, "PNG file is empty"
            
            # Verify data integrity
            # We expect points for 0, 2, and 3 constraints
            constraint_counts = [p['active_constraints'] for p in loaded_json['data_points']]
            assert 0 in constraint_counts
            assert 2 in constraint_counts
            assert 3 in constraint_counts
            
        finally:
            # Restore original paths
            if original_json_path:
                rg_module.ABULATION_RESULTS_PATH = original_json_path
            if original_json_out:
                rg_module.COST_CURVE_JSON_PATH = original_json_out
            if original_png_out:
                rg_module.COST_CURVE_PNG_PATH = original_png_out

    def test_generate_cost_curve_fails_gracefully_on_missing_input(self, tmp_path):
        """Test that the function raises FileNotFoundError if input is missing."""
        # Create a temp dir but don't put ablation_results.json
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        import src.utils.report_generator as rg_module
        original_path = rg_module.ABULATION_RESULTS_PATH
        rg_module.ABULATION_RESULTS_PATH = str(results_dir / "nonexistent.json")
        
        try:
            with pytest.raises(FileNotFoundError, match="Ablation results not found"):
                rg_module.generate_cost_curve()
        finally:
            rg_module.ABULATION_RESULTS_PATH = original_path