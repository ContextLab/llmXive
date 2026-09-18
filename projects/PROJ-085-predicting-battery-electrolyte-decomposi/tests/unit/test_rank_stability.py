"""
Unit tests for the rank stability check implementation (T032).

These tests verify that the rank stability logic correctly identifies
when top 3 descriptors change by more than 1 position across thresholds.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.rank_stability import (
    get_top_features_by_threshold,
    calculate_rank_shift,
    verify_rank_stability,
    generate_stability_report,
    run_rank_stability_check,
    SWEEP_THRESHOLDS,
    TOP_N,
    MAX_RANK_SHIFT
)


class TestGetTopFeaturesByThreshold:
    """Tests for get_top_features_by_threshold function."""

    def test_extract_top_features_success(self):
        """Test successful extraction of top features."""
        mock_results = {
            "0.45": {
                "feature_importance": {
                    "all": {
                        "feature_a": 0.9,
                        "feature_b": 0.8,
                        "feature_c": 0.7,
                        "feature_d": 0.6
                    }
                }
            }
        }

        result = get_top_features_by_threshold(mock_results, 0.45, "all")

        assert len(result) == TOP_N
        assert result == ["feature_a", "feature_b", "feature_c"]

    def test_threshold_not_found(self):
        """Test error when threshold is not in results."""
        mock_results = {
            "0.45": {
                "feature_importance": {
                    "all": {"feature_a": 0.9}
                }
            }
        }

        with pytest.raises(KeyError, match="Threshold 0.50 not found"):
            get_top_features_by_threshold(mock_results, 0.50, "all")

    def test_bin_type_not_found(self):
        """Test error when bin type is not in results."""
        mock_results = {
            "0.45": {
                "feature_importance": {
                    "low": {"feature_a": 0.9}
                }
            }
        }

        with pytest.raises(KeyError, match="Bin type 'high' not found"):
            get_top_features_by_threshold(mock_results, 0.45, "high")


class TestCalculateRankShift:
    """Tests for calculate_rank_shift function."""

    def test_no_shift(self):
        """Test when ranks are identical."""
        features_1 = ["a", "b", "c"]
        features_2 = ["a", "b", "c"]

        shifts = calculate_rank_shift(features_1, features_2)

        assert shifts["a"] == 0
        assert shifts["b"] == 0
        assert shifts["c"] == 0

    def test_single_position_shift(self):
        """Test when one feature shifts by 1 position."""
        features_1 = ["a", "b", "c"]
        features_2 = ["b", "a", "c"]

        shifts = calculate_rank_shift(features_1, features_2)

        assert shifts["a"] == 1
        assert shifts["b"] == 1
        assert shifts["c"] == 0

    def test_large_shift(self):
        """Test when a feature shifts by more than 1 position."""
        features_1 = ["a", "b", "c"]
        features_2 = ["c", "b", "a"]

        shifts = calculate_rank_shift(features_1, features_2)

        assert shifts["a"] == 2
        assert shifts["b"] == 0
        assert shifts["c"] == 2

    def test_feature_only_in_one_set(self):
        """Test when a feature is only present in one set."""
        features_1 = ["a", "b", "c"]
        features_2 = ["d", "b", "c"]

        shifts = calculate_rank_shift(features_1, features_2)

        # 'a' is missing in set 2, so it gets rank 4 (TOP_N + 1)
        assert shifts["a"] == abs(1 - 4)  # 3
        # 'd' is missing in set 1, so it gets rank 4 (TOP_N + 1)
        assert shifts["d"] == abs(4 - 1)  # 3
        assert shifts["b"] == 0
        assert shifts["c"] == 0


class TestVerifyRankStability:
    """Tests for verify_rank_stability function."""

    def test_all_stable(self):
        """Test when all shifts are within the limit."""
        mock_results = {
            "0.45": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
                }
            },
            "0.50": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
                }
            },
            "0.55": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
                }
            }
        }

        is_stable, all_shifts, stable_features = verify_rank_stability(mock_results)

        assert is_stable is True
        assert "a" in stable_features
        assert "b" in stable_features
        assert "c" in stable_features

    def test_unstable_shift(self):
        """Test when a shift exceeds the limit."""
        mock_results = {
            "0.45": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
                }
            },
            "0.50": {
                "feature_importance": {
                    "all": {"c": 0.9, "b": 0.8, "a": 0.7, "d": 0.6}
                }
            },
            "0.55": {
                "feature_importance": {
                    "all": {"c": 0.9, "b": 0.8, "a": 0.7, "d": 0.6}
                }
            }
        }

        is_stable, all_shifts, stable_features = verify_rank_stability(mock_results)

        # 'a' shifts from 1 to 3 (shift=2), 'c' shifts from 3 to 1 (shift=2)
        assert is_stable is False
        assert "a" not in stable_features
        assert "c" not in stable_features
        assert "b" in stable_features

    def test_partial_stability(self):
        """Test when some features are stable and others are not."""
        mock_results = {
            "0.45": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
                }
            },
            "0.50": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
                }
            },
            "0.55": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.7, "c": 0.8, "d": 0.6}
                }
            }
        }

        is_stable, all_shifts, stable_features = verify_rank_stability(mock_results)

        # First comparison (0.45->0.50): all stable
        # Second comparison (0.50->0.55): b and c swap (shift=1), so still stable
        assert is_stable is True
        assert len(stable_features) >= 2


class TestGenerateStabilityReport:
    """Tests for generate_stability_report function."""

    def test_report_generation(self):
        """Test that a report is generated correctly."""
        mock_results = {
            "0.45": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7}
                }
            },
            "0.50": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7}
                }
            },
            "0.55": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7}
                }
            }
        }

        stability_result = verify_rank_stability(mock_results)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp_path = Path(tmp.name)

        report_content = generate_stability_report(stability_result, tmp_path)

        assert "RANK STABILITY ANALYSIS REPORT" in report_content
        assert "STABILITY RESULT" in report_content
        assert "Is Stable" in report_content
        assert tmp_path.exists()

        # Clean up
        tmp_path.unlink()

    def test_report_without_output_path(self):
        """Test report generation without saving to file."""
        mock_results = {
            "0.45": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7}
                }
            },
            "0.50": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7}
                }
            },
            "0.55": {
                "feature_importance": {
                    "all": {"a": 0.9, "b": 0.8, "c": 0.7}
                }
            }
        }

        stability_result = verify_rank_stability(mock_results)
        report_content = generate_stability_report(stability_result)

        assert "RANK STABILITY ANALYSIS REPORT" in report_content
        assert len(report_content) > 0


class TestRunRankStabilityCheck:
    """Tests for the main entry point run_rank_stability_check."""

    @patch('models.rank_stability.load_sensitivity_results')
    @patch('models.rank_stability.verify_rank_stability')
    @patch('models.rank_stability.generate_stability_report')
    @patch('builtins.open')
    @patch('pathlib.Path.exists', return_value=True)
    def test_successful_run(
        self,
        mock_exists,
        mock_open,
        mock_generate_report,
        mock_verify,
        mock_load
    ):
        """Test successful execution of the rank stability check."""
        mock_load.return_value = {"0.45": {}, "0.50": {}, "0.55": {}}
        mock_verify.return_value = (True, {}, ["a", "b"])
        mock_generate_report.return_value = "Report content"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "results.json"

            results = run_rank_stability_check(
                sensitivity_results_path=tmp_path,
                output_report_path=tmp_path.with_suffix('.txt')
            )

            assert results["is_stable"] is True
            assert "report_path" in results
            assert "report_content" in results