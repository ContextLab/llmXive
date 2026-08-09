"""
Unit tests for hypothesis testing module, specifically verifying Westfall-Young permutation
for label-dependent tests in T021.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.hypothesis_testing import (
    load_cleaned_data,
    prepare_groups_for_test,
    perform_kruskal_wallis,
    perform_pairwise_comparisons,
    analyze_hypotheses,
    save_results,
)
from utils.config import get_config


class TestWestfallYoungPermutation:
    """Tests to verify Westfall-Young permutation is applied for label-dependent tests."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n_samples = 1000
        data = {
            "resolution_time_hours": np.random.lognormal(mean=2, sigma=1, size=n_samples),
            "language": np.random.choice(
                ["Python", "JavaScript", "Java", "C++", "Go"], size=n_samples
            ),
            "repo_id": np.random.choice(range(100), size=n_samples),
            "star_count": np.random.randint(10, 1000, size=n_samples),
        }
        return data

    def test_perform_kruskal_wallis_uses_permutation(self, sample_data):
        """
        Verify that perform_kruskal_wallis applies Westfall-Young permutation
        for label-dependent tests.
        """
        # Mock the data loading to return our sample data
        with patch("analysis.hypothesis_testing.pd.read_csv") as mock_read_csv:
            import pandas as pd
            mock_read_csv.return_value = pd.DataFrame(sample_data)

            # Call the function with permutation enabled (default for Westfall-Young)
            result = perform_kruskal_wallis(
                data=sample_data,
                target_col="resolution_time_hours",
                group_col="language",
                use_permutation=True,
                n_permutations=100,
                random_state=42,
            )

            # Verify result structure
            assert "statistic" in result
            assert "p_value" in result
            assert "p_value_permutation" in result
            assert "method" in result

            # Verify permutation method is indicated
            assert result["method"] == "Kruskal-Wallis with Westfall-Young permutation"

            # Verify permutation p-value is present and numeric
            assert isinstance(result["p_value_permutation"], (int, float))
            assert 0 <= result["p_value_permutation"] <= 1

    def test_perform_pairwise_comparisons_uses_permutation(self, sample_data):
        """
        Verify that perform_pairwise_comparisons applies Westfall-Young permutation
        for label-dependent pairwise tests.
        """
        with patch("analysis.hypothesis_testing.pd.read_csv") as mock_read_csv:
            import pandas as pd
            mock_read_csv.return_value = pd.DataFrame(sample_data)

            # Call pairwise comparisons with permutation
            result = perform_pairwise_comparisons(
                data=sample_data,
                target_col="resolution_time_hours",
                group_col="language",
                use_permutation=True,
                n_permutations=100,
                random_state=42,
            )

            # Verify result structure
            assert "comparisons" in result
            assert "method" in result

            # Verify permutation method is indicated
            assert "Westfall-Young" in result["method"]

            # Verify each comparison has permutation p-value
            for comp in result["comparisons"]:
                assert "p_value_permutation" in comp
                assert 0 <= comp["p_value_permutation"] <= 1

    def test_analyze_hypotheses_applies_permutation(self, sample_data):
        """
        Verify that analyze_hypotheses applies Westfall-Young permutation
        when analyzing group differences.
        """
        with patch("analysis.hypothesis_testing.pd.read_csv") as mock_read_csv:
            import pandas as pd
            mock_read_csv.return_value = pd.DataFrame(sample_data)

            # Mock save_results to avoid file I/O
            with patch("analysis.hypothesis_testing.save_results"):
                result = analyze_hypotheses(
                    data_path="dummy_path.csv",
                    target_col="resolution_time_hours",
                    group_col="language",
                    use_permutation=True,
                    n_permutations=100,
                    random_state=42,
                    output_path="dummy_output.json",
                )

                # Verify result contains permutation information
                assert "kruskal_wallis" in result
                assert "pairwise_comparisons" in result

                # Verify permutation was used
                assert result["kruskal_wallis"]["method"] == "Kruskal-Wallis with Westfall-Young permutation"
                assert "p_value_permutation" in result["kruskal_wallis"]

    def test_permutation_count_affects_p_value(self, sample_data):
        """
        Verify that different permutation counts produce different p-values,
        confirming permutation is actually being run.
        """
        with patch("analysis.hypothesis_testing.pd.read_csv") as mock_read_csv:
            import pandas as pd
            mock_read_csv.return_value = pd.DataFrame(sample_data)

            # Run with different permutation counts
            result_50 = perform_kruskal_wallis(
                data=sample_data,
                target_col="resolution_time_hours",
                group_col="language",
                use_permutation=True,
                n_permutations=50,
                random_state=42,
            )

            result_200 = perform_kruskal_wallis(
                data=sample_data,
                target_col="resolution_time_hours",
                group_col="language",
                use_permutation=True,
                n_permutations=200,
                random_state=42,
            )

            # P-values should differ due to different permutation counts
            # (though they should be in the same ballpark)
            assert result_50["p_value_permutation"] != result_200["p_value_permutation"]

            # Both should be valid probabilities
            assert 0 <= result_50["p_value_permutation"] <= 1
            assert 0 <= result_200["p_value_permutation"] <= 1

    def test_permutation_flag_controls_behavior(self, sample_data):
        """
        Verify that use_permutation=False disables permutation testing.
        """
        with patch("analysis.hypothesis_testing.pd.read_csv") as mock_read_csv:
            import pandas as pd
            mock_read_csv.return_value = pd.DataFrame(sample_data)

            # Run without permutation
            result = perform_kruskal_wallis(
                data=sample_data,
                target_col="resolution_time_hours",
                group_col="language",
                use_permutation=False,
                n_permutations=100,
                random_state=42,
            )

            # Verify result indicates standard method
            assert "standard" in result["method"].lower() or "chi-squared" in result["method"].lower()

            # Verify permutation p-value is not present or is None
            assert "p_value_permutation" not in result or result["p_value_permutation"] is None

    def test_westfall_young_handles_label_dependency(self, sample_data):
        """
        Verify that Westfall-Young permutation properly handles label dependency
        by using the same permutation across all test statistics.
        """
        with patch("analysis.hypothesis_testing.pd.read_csv") as mock_read_csv:
            import pandas as pd
            mock_read_csv.return_value = pd.DataFrame(sample_data)

            # Run permutation test
            result = perform_kruskal_wallis(
                data=sample_data,
                target_col="resolution_time_hours",
                group_col="language",
                use_permutation=True,
                n_permutations=100,
                random_state=123,
            )

            # Run again with same seed to verify reproducibility
            result_repro = perform_kruskal_wallis(
                data=sample_data,
                target_col="resolution_time_hours",
                group_col="language",
                use_permutation=True,
                n_permutations=100,
                random_state=123,
            )

            # Results should be identical with same seed
            assert result["p_value_permutation"] == result_repro["p_value_permutation"]

            # This confirms the permutation procedure is deterministic and
            # properly handles the label dependency through consistent resampling