"""
Unit tests for generate_sensitivity_table.py (T026).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module functions
from code.analysis.generate_sensitivity_table import (
    format_p_value,
    format_effect_size,
    generate_table_markdown,
    generate_table_csv
)

class TestFormatting:
    def test_format_p_value_less_than_0001(self):
        assert format_p_value(0.0001) == "< 0.001"
        assert format_p_value(0.00001) == "< 0.001"
    
    def test_format_p_value_normal(self):
        assert format_p_value(0.05) == "0.0500"
        assert format_p_value(0.12345) == "0.1235"
    
    def test_format_p_value_none(self):
        assert format_p_value(None) == "N/A"

    def test_format_effect_size_normal(self):
        assert format_effect_size(0.15) == "0.1500"
    
    def test_format_effect_size_none(self):
        assert format_effect_size(None) == "N/A"

class TestMarkdownGeneration:
    def test_generate_table_with_data(self):
        mock_results = {
            "sweep_results": [
                {"threshold_definition": "2-hop", "optimal_knot": 2, "p_value": 0.01, "effect_size": 0.15},
                {"threshold_definition": "3-hop", "optimal_knot": 3, "p_value": 0.04, "effect_size": 0.12},
                {"threshold_definition": "4-hop", "optimal_knot": 4, "p_value": 0.06, "effect_size": 0.08}
            ]
        }
        md = generate_table_markdown(mock_results)
        
        assert "# Sensitivity Analysis" in md
        assert "2-hop" in md
        assert "3-hop" in md
        assert "4-hop" in md
        assert "Yes" in md  # Significant
        assert "No" in md   # Not significant
        assert "robust" in md.lower() # Conclusion logic

    def test_generate_table_empty(self):
        mock_results = {"sweep_results": []}
        md = generate_table_markdown(mock_results)
        assert "*No data available*" in md

    def test_generate_table_no_sweep_key(self):
        mock_results = []
        md = generate_table_markdown(mock_results)
        assert "*No data available*" in md

class TestCSVGeneration:
    def test_generate_csv_with_data(self):
        mock_results = {
            "sweep_results": [
                {"threshold_definition": "2-hop", "optimal_knot": 2, "p_value": 0.01, "effect_size": 0.15},
                {"threshold_definition": "3-hop", "optimal_knot": 3, "p_value": 0.06, "effect_size": 0.08}
            ]
        }
        rows = generate_table_csv(mock_results)
        
        assert len(rows) == 2
        assert rows[0]["threshold_definition"] == "2-hop"
        assert rows[0]["significant"] == "Yes"
        assert rows[1]["significant"] == "No"

    def test_generate_csv_empty(self):
        mock_results = {"sweep_results": []}
        rows = generate_table_csv(mock_results)
        assert len(rows) == 0

class TestIntegration:
    @patch('code.analysis.generate_sensitivity_table.get_path')
    @patch('code.analysis.generate_sensitivity_table.ensure_dir')
    @patch('builtins.open', new_callable=MagicMock)
    def test_main_execution(self, mock_open, mock_ensure_dir, mock_get_path):
        # Setup mocks
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_get_path.side_effect = lambda x: mock_path if "sensitivity_results.json" in x else mock_path
        
        # Mock file content
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps({
            "sweep_results": [
                {"threshold_definition": "2-hop", "optimal_knot": 2, "p_value": 0.01, "effect_size": 0.15}
            ]
        })
        
        # Run main
        from code.analysis.generate_sensitivity_table import main
        main()
        
        # Verify calls
        assert mock_ensure_dir.called
        assert mock_open.call_count >= 2 # Read input, write md, write csv
