"""
Unit tests for analyze_subspace_ranks module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock the dependencies that are not available or not needed for unit tests
# We mock state_manager to avoid file system writes during tests
import sys
from unittest.mock import patch, MagicMock

# Add code to path if not already present
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from analyze_subspace_ranks import load_subspace_ranks, prepare_correlation_data

class TestLoadSubspaceRanks:
    def test_load_valid_file(self):
        """Test loading a valid subspace ranks JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subspace_ranks.json"
            data = {
                "ranks": {
                    "effect_1": 10,
                    "effect_2": 15,
                    "effect_3": 8
                }
            }
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            result = load_subspace_ranks(file_path)
            assert result == data["ranks"]
            assert "effect_1" in result
            assert result["effect_1"] == 10

    def test_load_flat_structure(self):
        """Test loading a flat JSON structure (no 'ranks' key)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subspace_ranks.json"
            data = {
                "effect_1": 10,
                "effect_2": 15
            }
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            result = load_subspace_ranks(file_path)
            assert result == data

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_subspace_ranks(Path("nonexistent/path/file.json"))

    def test_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "invalid.json"
            with open(file_path, 'w') as f:
                f.write("{ invalid json }")
            
            with pytest.raises(json.JSONDecodeError):
                load_subspace_ranks(file_path)

    def test_invalid_structure(self):
        """Test that ValueError is raised for non-dict structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "invalid.json"
            with open(file_path, 'w') as f:
                f.write("[1, 2, 3]") # JSON list, not object
            
            with pytest.raises(ValueError):
                load_subspace_ranks(file_path)

class TestPrepareCorrelationData:
    def test_merge_with_results(self):
        """Test merging subspace ranks with results.csv data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create ranks file
            ranks_path = Path(tmpdir) / "subspace_ranks.json"
            ranks_data = {"effect_A": 20, "effect_B": 30}
            with open(ranks_path, 'w') as f:
                json.dump({"ranks": ranks_data}, f)

            # Create results file
            results_path = Path(tmpdir) / "results.csv"
            with open(results_path, 'w') as f:
                f.write("effect,quantization_level,cesr_score,lpips_distance\n")
                f.write("effect_A,int8,0.5,0.2\n")
                f.write("effect_B,int4,0.6,0.3\n")
                f.write("effect_C,int8,0.7,0.4\n") # Not in ranks

            result = prepare_correlation_data(ranks_data, results_path)
            
            assert len(result) == 2 # Only effects in ranks
            effects = {r['effect'] for r in result}
            assert effects == {"effect_A", "effect_B"}
            
            # Check values
            for r in result:
                if r['effect'] == "effect_A":
                    assert r['subspace_rank'] == 20
                    assert r['cesr_score'] == 0.5
                elif r['effect'] == "effect_B":
                    assert r['subspace_rank'] == 30
                    assert r['cesr_score'] == 0.6

    def test_missing_results_file(self):
        """Test behavior when results.csv is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ranks_data = {"effect_X": 10}
            
            # Use a non-existent path for results
            non_existent_path = Path(tmpdir) / "missing.csv"
            
            result = prepare_correlation_data(ranks_data, non_existent_path)
            
            assert len(result) == 1
            assert result[0]['effect'] == "effect_X"
            assert result[0]['subspace_rank'] == 10
            assert result[0]['cesr_score'] is None

    def test_invalid_csv_values(self):
        """Test handling of non-numeric values in CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ranks_path = Path(tmpdir) / "subspace_ranks.json"
            ranks_data = {"effect_A": 20}
            with open(ranks_path, 'w') as f:
                json.dump({"ranks": ranks_data}, f)

            results_path = Path(tmpdir) / "results.csv"
            with open(results_path, 'w') as f:
                f.write("effect,cesr_score\n")
                f.write("effect_A,invalid_number\n")

            result = prepare_correlation_data(ranks_data, results_path)
            
            # Should handle conversion error gracefully (set to None or 0 depending on impl)
            # Based on implementation: float() raises error -> caught -> None
            # Wait, my implementation catches Exception in main block but here we do float() directly.
            # Let's check the implementation logic:
            # float(row.get('cesr_score', 0)) if row.get('cesr_score') else None
            # If 'invalid_number' is present, row.get returns it, then float() raises ValueError.
            # The try/except block in prepare_correlation_data catches this.
            # So it should fall back to the partial data logic or skip the row?
            # In my implementation:
            # try: ... except Exception: ... merged_data = partial
            # So if one row fails, it might return the partial list (all ranks, no metrics).
            # Let's assume the implementation handles it by returning the partial list if any error occurs.
            
            # Re-reading implementation:
            # The try block wraps the whole CSV reading. If any row fails, it goes to except.
            # In except, it returns the partial list (ranks only).
            assert len(result) == 1
            assert result[0]['cesr_score'] is None