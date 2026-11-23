"""
Unit tests for save_pathway_results.py (T027)

Tests verify that pathway mapping results are correctly saved to JSON.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from code.modeling.save_pathway_results import load_json_file, save_json_file, main


class TestLoadSaveJson:
    """Test JSON load/save utility functions."""

    def test_load_json_file(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        test_file = tmp_path / "test.json"
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(test_file)
        assert result == test_data

    def test_save_json_file(self, tmp_path):
        """Test saving data to a JSON file."""
        test_data = {"test": "data", "list": [1, 2, 3]}
        test_file = tmp_path / "output.json"
        
        save_json_file(test_data, test_file)
        
        assert test_file.exists()
        
        with open(test_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == test_data

class TestMainFunction:
    """Test the main function of save_pathway_results."""

    def test_main_creates_output_file(self, tmp_path, monkeypatch):
        """Test that main creates the pathway_analysis.json file."""
        # Setup temporary directories
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        # Create a mock shap_analysis.json
        shap_data = {
            "top_metabolites": [
                {
                    "metabolite": "Test_Metabolite_1",
                    "shap_value": 0.5,
                    "pathways": ["KEGG:00010", "MetaCyc:PWY-123"]
                },
                {
                    "metabolite": "Test_Metabolite_2",
                    "shap_value": 0.3,
                    "pathways": ["KEGG:00020"]
                }
            ],
            "pathway_mappings": {
                "KEGG:00010": "Glycolysis",
                "KEGG:00020": "Citrate Cycle",
                "MetaCyc:PWY-123": "Phenylpropanoid Biosynthesis"
            }
        }
        
        shap_file = results_dir / "shap_analysis.json"
        with open(shap_file, 'w') as f:
            json.dump(shap_data, f)
        
        # Mock the constants module to use our temp directory
        with patch('code.modeling.save_pathway_results.RESULTS_DIR', results_dir):
            result = main()
        
        # Verify output file was created
        output_file = results_dir / "pathway_analysis.json"
        assert output_file.exists()
        
        # Verify content structure
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        assert "metadata" in output_data
        assert "summary" in output_data
        assert "top_metabolites" in output_data
        assert "pathway_mappings" in output_data
        assert "interpretation" in output_data

    def test_main_exits_when_shap_file_missing(self, tmp_path, monkeypatch):
        """Test that main exits gracefully when shap_analysis.json is missing."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        with patch('code.modeling.save_pathway_results.RESULTS_DIR', results_dir):
            with pytest.raises(SystemExit) as excinfo:
                main()
            
            assert excinfo.value.code == 1

    def test_main_exits_when_top_metabolites_missing(self, tmp_path, monkeypatch):
        """Test that main exits when shap_analysis.json is missing top_metabolites."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        # Create invalid shap_analysis.json
        shap_file = results_dir / "shap_analysis.json"
        with open(shap_file, 'w') as f:
            json.dump({"invalid_key": "value"}, f)
        
        with patch('code.modeling.save_pathway_results.RESULTS_DIR', results_dir):
            with pytest.raises(SystemExit) as excinfo:
                main()
            
            assert excinfo.value.code == 1

    def test_main_exits_when_pathway_mappings_missing(self, tmp_path, monkeypatch):
        """Test that main exits when shap_analysis.json is missing pathway_mappings."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        # Create invalid shap_analysis.json
        shap_file = results_dir / "shap_analysis.json"
        with open(shap_file, 'w') as f:
            json.dump({"top_metabolites": []}, f)
        
        with patch('code.modeling.save_pathway_results.RESULTS_DIR', results_dir):
            with pytest.raises(SystemExit) as excinfo:
                main()
            
            assert excinfo.value.code == 1

    def test_output_contains_correct_summary(self, tmp_path, monkeypatch):
        """Test that output summary matches input data."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        shap_data = {
            "top_metabolites": [
                {"metabolite": "M1", "shap_value": 0.5, "pathways": ["P1"]},
                {"metabolite": "M2", "shap_value": 0.4, "pathways": ["P1", "P2"]},
                {"metabolite": "M3", "shap_value": 0.3, "pathways": []}
            ],
            "pathway_mappings": {"P1": "Pathway 1", "P2": "Pathway 2"}
        }
        
        shap_file = results_dir / "shap_analysis.json"
        with open(shap_file, 'w') as f:
            json.dump(shap_data, f)
        
        with patch('code.modeling.save_pathway_results.RESULTS_DIR', results_dir):
            main()
        
        output_file = results_dir / "pathway_analysis.json"
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        summary = output_data["summary"]
        assert summary["total_top_metabolites"] == 3
        assert summary["metabolites_with_pathways"] == 2
        assert summary["pathways_identified"] == 2  # P1 and P2
