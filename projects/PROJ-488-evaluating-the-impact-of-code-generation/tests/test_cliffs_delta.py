import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from cliffs_delta_analysis import compute_cliffs_delta, get_effect_size_magnitude

class TestCliffsDeltaComputation:
    """Test cases for Cliff's Delta calculation logic."""

    def test_identical_groups(self):
        """If groups are identical, delta should be 0."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [1.0, 2.0, 3.0]
        delta = compute_cliffs_delta(group1, group2)
        assert abs(delta) < 1e-6, f"Expected 0 for identical groups, got {delta}"

    def test_complete_separation_higher(self):
        """If group1 is strictly higher than group2, delta should be 1."""
        group1 = [5.0, 6.0, 7.0]
        group2 = [1.0, 2.0, 3.0]
        delta = compute_cliffs_delta(group1, group2)
        assert abs(delta - 1.0) < 1e-6, f"Expected 1.0, got {delta}"

    def test_complete_separation_lower(self):
        """If group1 is strictly lower than group2, delta should be -1."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [5.0, 6.0, 7.0]
        delta = compute_cliffs_delta(group1, group2)
        assert abs(delta - (-1.0)) < 1e-6, f"Expected -1.0, got {delta}"

    def test_empty_group_raises(self):
        """Should raise ValueError if a group is empty."""
        with pytest.raises(ValueError):
            compute_cliffs_delta([], [1.0, 2.0])
        with pytest.raises(ValueError):
            compute_cliffs_delta([1.0, 2.0], [])

    def test_magnitude_small(self):
        """Test magnitude classification for small effect."""
        assert get_effect_size_magnitude(0.2) == "small"
        assert get_effect_size_magnitude(-0.2) == "small"

    def test_magnitude_medium(self):
        """Test magnitude classification for medium effect."""
        assert get_effect_size_magnitude(0.4) == "medium"
        assert get_effect_size_magnitude(-0.4) == "medium"

    def test_magnitude_large(self):
        """Test magnitude classification for large effect."""
        assert get_effect_size_magnitude(0.6) == "large"
        assert get_effect_size_magnitude(-0.6) == "large"

    def test_magnitude_negligible(self):
        """Test magnitude classification for negligible effect."""
        assert get_effect_size_magnitude(0.1) == "negligible"
        assert get_effect_size_magnitude(-0.1) == "negligible"

class TestIntegration:
    """Integration tests requiring real data files."""

    def test_data_file_exists_if_generated(self):
        """Check if the output file exists if the script has been run."""
        output_path = Path("data/metrics/cliffs_delta_results.csv")
        # This test is skipped if the file doesn't exist yet (expected in fresh env)
        if output_path.exists():
            import pandas as pd
            df = pd.read_csv(output_path)
            assert 'metric_type' in df.columns
            assert 'cliffs_delta' in df.columns
            assert 'magnitude' in df.columns
        else:
            pytest.skip("Output file not generated yet. Run code/cliffs_delta_analysis.py first.")
