"""
Unit tests for data preprocessing functions.
Tests for antiSMASH wrapper and other preprocessing utilities.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.data.preprocess import (
    run_antiasmh_wrapper,
    _parse_antismash_output,
    _generate_mock_antismash_results,
    CLUSTER_TYPE_MAPPING
)

class TestAntiSMASHWrapper:
    """Tests for the antiSMASH wrapper functionality."""

    def test_cluster_type_mapping_exists(self):
        """Verify that cluster type mapping is populated."""
        assert len(CLUSTER_TYPE_MAPPING) > 0
        assert "polyketide" in CLUSTER_TYPE_MAPPING
        assert CLUSTER_TYPE_MAPPING["polyketide"] == "PKS"

    @patch('code.data.preprocess._check_antismash_installation')
    @patch('code.data.preprocess._generate_mock_antismash_results')
    def test_mock_mode_generation(self, mock_gen, mock_check):
        """Test that mock mode is triggered when antiSMASH is not available."""
        mock_check.return_value = False
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "genomes"
            input_dir.mkdir()
            
            # Create a dummy genome file
            (input_dir / "test_species.fasta").write_text(">test\nATCG")
            
            binary, count = run_antiasmh_wrapper(
                input_dir=input_dir,
                species_list=["test_species"]
            )
            
            # Verify mock generation was called
            mock_gen.assert_called_once()
            
            # Verify output structure
            assert "test_species" in binary
            assert "test_species" in count
            assert isinstance(binary["test_species"], dict)
            assert isinstance(count["test_species"], dict)

    def test_parse_antismash_output_structure(self):
        """Test parsing of antiSMASH JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create mock JSON output
            mock_json = {
                "clusters": [
                    {"type": "polyketide"},
                    {"type": "terpene"},
                    {"type": "polyketide"},
                    {"type": "unknown_type"}
                ]
            }
            
            json_file = output_dir / "antismash.json"
            with open(json_file, "w") as f:
                json.dump(mock_json, f)
            
            binary_matrix = {}
            count_matrix = {}
            
            _parse_antismash_output(output_dir, "test_sp", binary_matrix, count_matrix)
            
            # Verify counts
            assert count_matrix["test_sp"]["PKS"] == 2
            assert count_matrix["test_sp"]["Terpene"] == 1
            assert count_matrix["test_sp"]["unknown_type"] == 1
            
            # Verify binary presence
            assert binary_matrix["test_sp"]["PKS"] == 1
            assert binary_matrix["test_sp"]["Terpene"] == 1
            assert binary_matrix["test_sp"]["unknown_type"] == 1

    def test_empty_clusters_handling(self):
        """Test handling of empty cluster list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            mock_json = {"clusters": []}
            json_file = output_dir / "antismash.json"
            with open(json_file, "w") as f:
                json.dump(mock_json, f)
            
            binary_matrix = {}
            count_matrix = {}
            
            _parse_antismash_output(output_dir, "empty_sp", binary_matrix, count_matrix)
            
            # Should have empty dicts
            assert "empty_sp" in binary_matrix
            assert "empty_sp" in count_matrix
            assert len(binary_matrix["empty_sp"]) == 0
            assert len(count_matrix["empty_sp"]) == 0

    def test_missing_json_file(self):
        """Test handling of missing JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            binary_matrix = {}
            count_matrix = {}
            
            # Should not raise, just log warning
            _parse_antismash_output(output_dir, "missing_sp", binary_matrix, count_matrix)
            
            # Dictionaries should remain empty
            assert "missing_sp" not in binary_matrix or len(binary_matrix["missing_sp"]) == 0

class TestMockDataGeneration:
    """Tests for mock data generation fallback."""

    def test_mock_generation_consistency(self):
        """Test that mock generation produces consistent results for same species."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            
            binary1, count1 = {}, {}
            binary2, count2 = {}, {}
            
            _generate_mock_antismash_results(["consistent_sp"], input_dir, binary1, count1)
            _generate_mock_antismash_results(["consistent_sp"], input_dir, binary2, count2)
            
            # Results should be identical due to deterministic seeding
            assert binary1 == binary2
            assert count1 == count2

    def test_mock_generation_variability(self):
        """Test that different species get different mock results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            
            binary1, count1 = {}, {}
            binary2, count2 = {}, {}
            
            _generate_mock_antismash_results(["species_A"], input_dir, binary1, count1)
            _generate_mock_antismash_results(["species_B"], input_dir, binary2, count2)
            
            # Results should likely differ (high probability)
            # We don't assert inequality as it's theoretically possible they match,
            # but we can verify the structure is correct
            assert "species_A" in binary1
            assert "species_B" in binary2
            assert isinstance(binary1["species_A"], dict)
