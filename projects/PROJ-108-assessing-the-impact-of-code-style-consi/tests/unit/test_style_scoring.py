"""
Unit tests for style scoring logic in code/01_style_scoring.py.

This module verifies:
1. Score ranges are valid (0.0 to 1.0) for all metrics and the composite score.
2. Metric aggregation logic (weighted average) produces correct results.
3. Parse errors are handled gracefully (skipping files without crashing).
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code import (
    get_pylint_score,
    get_radon_line_length_score,
    compute_style_score,
    main
)


class TestScoreRange:
    """Tests to verify that all scores fall within the 0.0 to 1.0 range."""

    def test_pylint_score_normalization(self):
        """Test that pylint scores are normalized to 0.0-1.0."""
        # Mock pylint output to return a score of 8.5/10
        mock_output = json.dumps([{"score": 8.5}])

        with patch("code.subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.stdout = mock_output
            mock_process.stderr = ""
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
                f.write(b"print('hello')\n")
                temp_path = f.name

            try:
                score = get_pylint_score(temp_path)
                assert 0.0 <= score <= 1.0, f"Score {score} is out of range [0.0, 1.0]"
            finally:
                os.unlink(temp_path)

    def test_radon_score_normalization(self):
        """Test that radon line-length scores are normalized to 0.0-1.0."""
        # Mock radon output (simplified)
        mock_output = json.dumps({"average_line_length": 40, "max_line_length": 80})

        with patch("code.subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.stdout = mock_output
            mock_process.stderr = ""
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
                f.write(b"print('hello')\n")
                temp_path = f.name

            try:
                score = get_radon_line_length_score(temp_path)
                assert 0.0 <= score <= 1.0, f"Score {score} is out of range [0.0, 1.0]"
            finally:
                os.unlink(temp_path)

    def test_compute_style_score_range(self):
        """Test that the composite style score is within 0.0-1.0."""
        # Test with various combinations of input scores
        test_cases = [
            (0.0, 0.0),  # Worst case
            (1.0, 1.0),  # Best case
            (0.5, 0.5),  # Middle
            (0.8, 0.2),  # Mixed
            (0.2, 0.8),  # Mixed
        ]

        for pylint_score, radon_score in test_cases:
            composite = compute_style_score(pylint_score, radon_score)
            assert 0.0 <= composite <= 1.0, (
                f"Composite score {composite} from inputs "
                f"(pylint={pylint_score}, radon={radon_score}) is out of range"
            )


class TestMetricAggregation:
    """Tests to verify the metric aggregation logic."""

    def test_default_weights(self):
        """Test that default weights (50/50) produce correct weighted average."""
        # With equal weights, the composite should be the arithmetic mean
        pylint_score = 0.8
        radon_score = 0.4
        expected = (0.5 * pylint_score) + (0.5 * radon_score)
        result = compute_style_score(pylint_score, radon_score)
        assert abs(result - expected) < 1e-6, (
            f"Expected {expected}, got {result} for default weights"
        )

    def test_custom_weights(self):
        """Test that custom weights are applied correctly."""
        pylint_score = 0.8
        radon_score = 0.4
        pylint_weight = 0.7
        radon_weight = 0.3
        expected = (pylint_weight * pylint_score) + (radon_weight * radon_score)
        result = compute_style_score(pylint_score, radon_score, pylint_weight, radon_weight)
        assert abs(result - expected) < 1e-6, (
            f"Expected {expected}, got {result} for custom weights"
        )

    def test_weight_normalization(self):
        """Test that weights are normalized if they don't sum to 1.0."""
        pylint_score = 0.8
        radon_score = 0.4
        # Provide weights that sum to 2.0 (should be normalized to 0.75/0.25)
        pylint_weight = 1.5
        radon_weight = 0.5
        expected = (0.75 * pylint_score) + (0.25 * radon_score)
        result = compute_style_score(pylint_score, radon_score, pylint_weight, radon_weight)
        assert abs(result - expected) < 1e-6, (
            f"Expected {expected}, got {result} for unnormalized weights"
        )


class TestParseErrorHandling:
    """Tests to verify that parse errors are handled gracefully."""

    def test_pylint_parse_error(self):
        """Test that a pylint parse error is handled without crashing."""
        with patch("code.subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.stdout = ""
            mock_process.stderr = "SyntaxError: invalid syntax"
            mock_process.returncode = 1
            mock_run.return_value = mock_process

            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
                f.write(b"invalid syntax here\n")
                temp_path = f.name

            try:
                # Should return None or a sentinel value for parse errors
                score = get_pylint_score(temp_path)
                assert score is None, "Expected None for pylint parse error"
            finally:
                os.unlink(temp_path)

    def test_radon_parse_error(self):
        """Test that a radon parse error is handled without crashing."""
        with patch("code.subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.stdout = ""
            mock_process.stderr = "RadonError: cannot parse"
            mock_process.returncode = 1
            mock_run.return_value = mock_process

            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
                f.write(b"invalid syntax here\n")
                temp_path = f.name

            try:
                # Should return None or a sentinel value for parse errors
                score = get_radon_line_length_score(temp_path)
                assert score is None, "Expected None for radon parse error"
            finally:
                os.unlink(temp_path)

    def test_compute_style_score_with_partial_errors(self):
        """Test that compute_style_score handles partial errors gracefully."""
        # One metric is valid, one is None
        composite = compute_style_score(0.8, None)
        assert composite is None, "Expected None when one metric is invalid"

        composite = compute_style_score(None, 0.4)
        assert composite is None, "Expected None when one metric is invalid"

        composite = compute_style_score(None, None)
        assert composite is None, "Expected None when both metrics are invalid"

    def test_main_skips_parse_errors(self):
        """Test that the main function skips files with parse errors without crashing."""
        # Create a temporary directory with a mix of valid and invalid files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a valid Python file
            valid_file = temp_path / "valid.py"
            valid_file.write_text("print('hello')\n")

            # Create an invalid Python file
            invalid_file = temp_path / "invalid.py"
            invalid_file.write_text("invalid syntax here\n")

            # Create output directory
            output_dir = temp_path / "output"
            output_dir.mkdir()

            # Mock the subprocess calls to simulate errors for the invalid file
            with patch("code.subprocess.run") as mock_run:
                def side_effect(cmd, *args, **kwargs):
                    mock_process = MagicMock()
                    if "invalid.py" in str(cmd):
                        mock_process.stdout = ""
                        mock_process.stderr = "SyntaxError"
                        mock_process.returncode = 1
                    else:
                        mock_process.stdout = json.dumps([{"score": 9.0}])
                        mock_process.stderr = ""
                        mock_process.returncode = 0
                    return mock_process

                mock_run.side_effect = side_effect

                # Run the main function - should not crash
                try:
                    main(
                        input_dir=str(temp_path),
                        output_file=str(output_dir / "style_scores_raw.csv")
                    )
                    # If we get here, the function handled errors gracefully
                    assert True
                except Exception as e:
                    pytest.fail(f"main() crashed with parse errors: {e}")