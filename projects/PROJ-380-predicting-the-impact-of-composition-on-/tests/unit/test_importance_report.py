"""
Unit tests for the importance report generation (T040).

Tests the generation of importance_report.json with ranked descriptors and p-values.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.importance_report_generator import (
    load_importance_results,
    rank_descriptors,
    extract_p_values,
    generate_importance_report
)


class TestLoadImportanceResults:
    """Tests for load_importance_results function."""

    def test_load_existing_file(self, tmp_path):
        """Test loading from an existing file."""
        # Create a mock importance file
        mock_data = {
            'results': [
                {'feature': 'delta', 'mean_importance': 0.5, 'p_value': 0.01},
                {'feature': 'vh', 'mean_importance': 0.3, 'p_value': 0.05}
            ]
        }
        
        test_file = tmp_path / "mock_importance.json"
        with open(test_file, 'w') as f:
            json.dump(mock_data, f)
        
        results = load_importance_results(str(test_file))
        
        assert len(results) == 2
        assert results[0]['feature'] == 'delta'
        assert results[1]['feature'] == 'vh'

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_importance_results("/nonexistent/path.json")

    def test_empty_results(self, tmp_path):
        """Test loading empty results."""
        mock_data = {'results': []}
        
        test_file = tmp_path / "empty_importance.json"
        with open(test_file, 'w') as f:
            json.dump(mock_data, f)
        
        results = load_importance_results(str(test_file))
        assert results == []


class TestRankDescriptors:
    """Tests for rank_descriptors function."""

    def test_ranking_order(self):
        """Test that descriptors are ranked correctly by importance."""
        importance_data = [
            {'feature': 'delta', 'mean_importance': 0.5},
            {'feature': 'vh', 'mean_importance': 0.3},
            {'feature': 'vec', 'mean_importance': 0.8}
        ]
        
        ranked = rank_descriptors(importance_data)
        
        assert ranked[0]['rank'] == 1
        assert ranked[0]['feature'] == 'vec'
        assert ranked[1]['rank'] == 2
        assert ranked[1]['feature'] == 'delta'
        assert ranked[2]['rank'] == 3
        assert ranked[2]['feature'] == 'vh'

    def test_ranking_with_ties(self):
        """Test ranking when there are ties in importance."""
        importance_data = [
            {'feature': 'delta', 'mean_importance': 0.5},
            {'feature': 'vh', 'mean_importance': 0.5},
            {'feature': 'vec', 'mean_importance': 0.3}
        ]
        
        ranked = rank_descriptors(importance_data)
        
        # First two should have ranks 1 and 2 (order may vary)
        assert ranked[0]['rank'] == 1
        assert ranked[1]['rank'] == 2
        assert ranked[2]['rank'] == 3

    def test_empty_input(self):
        """Test ranking with empty input."""
        ranked = rank_descriptors([])
        assert ranked == []


class TestExtractPValues:
    """Tests for extract_p_values function."""

    def test_extract_all_p_values(self):
        """Test extracting p-values from importance data."""
        importance_data = [
            {'feature': 'delta', 'p_value': 0.01},
            {'feature': 'vh', 'p_value': 0.05},
            {'feature': 'vec', 'p_value': 0.10}
        ]
        
        p_values = extract_p_values(importance_data)
        
        assert p_values['delta'] == 0.01
        assert p_values['vh'] == 0.05
        assert p_values['vec'] == 0.10

    def test_default_p_value(self):
        """Test default p-value when not present."""
        importance_data = [
            {'feature': 'delta'},
            {'feature': 'vh', 'p_value': 0.05}
        ]
        
        p_values = extract_p_values(importance_data)
        
        assert p_values['delta'] == 1.0  # Default
        assert p_values['vh'] == 0.05


class TestGenerateImportanceReport:
    """Tests for generate_importance_report function."""

    @patch('models.importance_report_generator.load_importance_results')
    @patch('models.importance_report_generator.ensure_state_directory')
    @patch('models.importance_report_generator.record_artifact')
    def test_generate_report_structure(
        self,
        mock_record,
        mock_ensure_dir,
        mock_load,
        tmp_path
    ):
        """Test that the generated report has the correct structure."""
        # Mock the loaded data
        mock_load.return_value = [
            {'feature': 'delta', 'mean_importance': 0.5, 'std_importance': 0.1, 'p_value': 0.01},
            {'feature': 'vh', 'mean_importance': 0.3, 'std_importance': 0.05, 'p_value': 0.05}
        ]
        
        output_path = tmp_path / "importance_report.json"
        
        with patch('models.importance_report_generator.get_paths') as mock_paths:
            mock_paths.return_value = {'artifacts': str(tmp_path)}
            generate_importance_report(
                importance_file="mock.json",
                output_path=str(output_path)
            )
        
        # Verify the file was created
        assert output_path.exists()
        
        # Load and verify structure
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert 'metadata' in report
        assert 'ranking' in report
        assert 'p_values' in report
        assert 'summary' in report
        
        # Verify ranking structure
        assert len(report['ranking']) == 2
        assert report['ranking'][0]['rank'] == 1
        assert report['ranking'][0]['feature'] == 'delta'
        assert report['ranking'][0]['significant'] == True  # p < 0.05
        
        # Verify p_values
        assert report['p_values']['delta'] == 0.01
        assert report['p_values']['vh'] == 0.05
        
        # Verify summary
        assert report['summary']['top_feature'] == 'delta'
        assert report['summary']['significant_features_count'] == 2

    @patch('models.importance_report_generator.load_importance_results')
    def test_empty_data_raises_error(self, mock_load, tmp_path):
        """Test that empty importance data raises an error."""
        mock_load.return_value = []
        
        output_path = tmp_path / "importance_report.json"
        
        with patch('models.importance_report_generator.get_paths') as mock_paths:
            mock_paths.return_value = {'artifacts': str(tmp_path)}
            with pytest.raises(ValueError, match="Importance data is empty"):
                generate_importance_report(
                    importance_file="mock.json",
                    output_path=str(output_path)
                )