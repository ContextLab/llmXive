"""
Unit tests for runtime verification script (T032b).
"""
import pytest
import json
import os
import time
from unittest.mock import Mock, patch, MagicMock
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from runtime_verification import (
    load_representative_subset,
    extrapolate_runtime,
    load_smell_mapping,
    load_prompt_template
)


class TestLoadRepresentativeSubset:
    """Tests for load_representative_subset function."""

    @patch('runtime_verification.pd')
    def test_load_subset_from_baseline(self, mock_pd):
        """Test loading a subset from baseline."""
        # Setup mock dataframe
        mock_df = MagicMock()
        mock_df.head.return_value.to_dict.return_value = [
            {'code': 'def test(): pass', 'loc': 1, 'cyclomatic_complexity': 1, 'static_smell_labels': '[]'}
        ]
        mock_pd.read_csv.return_value = mock_df
        mock_df.__len__ = lambda self: 100

        # Call function
        result = load_representative_subset('dummy_path.csv', subset_size=10)

        # Assertions
        mock_pd.read_csv.assert_called_once_with('dummy_path.csv')
        mock_df.head.assert_called_once_with(10)
        assert len(result) == 1
        assert result[0]['code'] == 'def test(): pass'


    @patch('runtime_verification.pd')
    def test_subset_larger_than_available(self, mock_pd):
        """Test handling when subset size exceeds available data."""
        # Setup mock dataframe with only 5 rows
        mock_df = MagicMock()
        mock_df.head.return_value.to_dict.return_value = [
            {'code': f'def test_{i}(): pass'} for i in range(5)
        ]
        mock_pd.read_csv.return_value = mock_df
        mock_df.__len__ = lambda self: 5

        # Call function with subset_size=10 (larger than available)
        result = load_representative_subset('dummy_path.csv', subset_size=10)

        # Should return all 5 available
        assert len(result) == 5


    def test_file_not_found(self):
        """Test handling of missing baseline file."""
        with pytest.raises(FileNotFoundError):
            load_representative_subset('non_existent_path.csv', subset_size=10)


class TestExtrapolateRuntime:
    """Tests for extrapolate_runtime function."""

    def test_extrapolate_within_constraint(self):
        """Test extrapolation when runtime is within constraint."""
        result = extrapolate_runtime(
            subset_size=50,
            subset_time=3000.0,  # 50 minutes
            total_sample_size=800
        )

        assert result['subset_size'] == 50
        assert result['subset_time_seconds'] == 3000.0
        assert result['total_sample_size'] == 800
        assert result['time_per_function_seconds'] == 60.0
        assert result['extrapolated_total_time_hours'] == pytest.approx(13.33, rel=0.01)
        assert result['is_compliant'] is False  # 13.33h > 6h constraint
        assert result['margin_hours'] == pytest.approx(-7.33, rel=0.01)


    def test_extrapolate_within_constraint_compliant(self):
        """Test extrapolation when runtime is within constraint."""
        # Subset of 50 functions takes 100 seconds
        # Total sample 800 functions -> 1600 seconds = 0.44 hours
        result = extrapolate_runtime(
            subset_size=50,
            subset_time=100.0,
            total_sample_size=800
        )

        assert result['extrapolated_total_time_hours'] == pytest.approx(0.44, rel=0.01)
        assert result['is_compliant'] is True
        assert result['margin_hours'] == pytest.approx(5.56, rel=0.01)


    def test_extrapolate_edge_case(self):
        """Test extrapolation with equal subset and total size."""
        result = extrapolate_runtime(
            subset_size=100,
            subset_time=600.0,
            total_sample_size=100
        )

        assert result['extrapolated_total_time_hours'] == 0.1666
        assert result['is_compliant'] is True


class TestLoadSmellMapping:
    """Tests for load_smell_mapping function."""

    def test_load_valid_mapping(self, tmp_path):
        """Test loading a valid smell mapping."""
        mapping_file = tmp_path / "smell_mapping.json"
        mapping_data = {"C0111": "Missing Docstring", "R0913": "Too Many Parameters"}
        mapping_file.write_text(json.dumps(mapping_data))

        result = load_smell_mapping(str(mapping_file))

        assert result == mapping_data


    def test_mapping_not_found(self):
        """Test handling of missing mapping file."""
        with pytest.raises(FileNotFoundError):
            load_smell_mapping('non_existent.json')


class TestLoadPromptTemplate:
    """Tests for load_prompt_template function."""

    def test_load_valid_prompt(self, tmp_path):
        """Test loading a valid prompt template."""
        prompt_file = tmp_path / "llm_prompt.txt"
        prompt_content = "Analyze this code for smells: {code}"
        prompt_file.write_text(prompt_content)

        result = load_prompt_template(str(prompt_file))

        assert result == prompt_content


    def test_prompt_not_found(self):
        """Test handling of missing prompt file."""
        with pytest.raises(FileNotFoundError):
            load_prompt_template('non_existent.txt')


class TestRuntimeVerificationIntegration:
    """Integration tests for runtime verification workflow."""

    @patch('runtime_verification.load_representative_subset')
    @patch('runtime_verification.load_smell_mapping')
    @patch('runtime_verification.load_prompt_template')
    @patch('runtime_verification.load_embeddings_model')
    @patch('runtime_verification.load_llama_model')
    @patch('runtime_verification.run_subset_data_pipeline')
    @patch('runtime_verification.run_subset_semantic_analysis')
    def test_full_verification_flow(
        self,
        mock_semantic,
        mock_data,
        mock_llm,
        mock_embeddings,
        mock_prompt,
        mock_mapping,
        mock_subset
    ):
        """Test the full verification flow with mocked components."""
        # Setup mocks
        mock_subset.return_value = [{'code': 'def test(): pass'}]
        mock_mapping.return_value = {'C0111': 'Missing Docstring'}
        mock_prompt.return_value = "Analyze: {code}"
        mock_embeddings.return_value = Mock()
        mock_llm.return_value = Mock()
        mock_data.return_value = [{'code': 'def test(): pass', 'loc': 1, 'cyclomatic_complexity': 1, 'static_smell_labels': '[]'}]
        mock_semantic.return_value = [{'code': 'def test(): pass', 'embedding': [0.1, 0.2], 'llm_labels': []}]

        # Mock time to avoid actual timing
        with patch('runtime_verification.time.time') as mock_time:
            mock_time.side_effect = [0, 10, 10, 20]  # Start data, End data, Start semantic, End semantic

            # Run the main logic (partial)
            from runtime_verification import (
                load_representative_subset,
                run_subset_data_pipeline,
                run_subset_semantic_analysis,
                extrapolate_runtime
            )

            subset_data = load_representative_subset('dummy.csv', 10)
            processed = run_subset_data_pipeline(subset_data, {'C0111': 'Missing Docstring'})
            semantic = run_subset_semantic_analysis(processed, Mock(), Mock(), "Prompt")

            extrapolation = extrapolate_runtime(10, 20, 800)

            assert extrapolation['is_compliant'] is False  # 20s * 80 = 1600s = 0.44h < 6h, but we used 20s for 10 funcs
            # Actually: 20s / 10 = 2s per func, 2s * 800 = 1600s = 0.44h -> compliant
            # Let me recalculate: subset_time=20, subset_size=10 -> 2s/func, total=800 -> 1600s = 0.44h
            assert extrapolation['is_compliant'] is True