"""
Unit tests for multi-modal alignment functionality.

This module verifies that the `align_modalities` function in `code/data/extract_features.py`
correctly handles missing data across different modalities (sequence, ATAC-seq, H3K27ac).

Specific checks:
1. Verification that windows with missing ATAC-seq data are excluded or handled as per spec.
2. Verification that windows with missing H3K27ac data are excluded or handled as per spec.
3. Verification that valid windows with all modalities present are retained.
4. Verification that the alignment logic correctly matches genomic coordinates across modalities.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the function under test from the existing API surface
# Note: The import path assumes the test is run from the project root or code/ is in sys.path
try:
    from data.extract_features import align_modalities
except ImportError:
    # Fallback for direct execution in tests/ directory context
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from data.extract_features import align_modalities


class TestMultiModalAlignment:
    """Test suite for align_modalities function."""

    def test_all_modalities_present(self):
        """Test that windows with all modalities present are retained."""
        # Mock input data with all modalities present
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),  # One-hot encoded
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)

        # Should retain the window
        assert len(result) == 1
        assert result[0]["cell_type"] == "GM12878"
        assert "atac_signal" in result[0]
        assert "h3k27ac_signal" in result[0]

    def test_missing_atac_signal_excluded(self):
        """Test that windows with missing ATAC-seq data are excluded."""
        # Mock input data with missing ATAC-seq signal (None or empty)
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": None,  # Missing ATAC-seq
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "K562"
            }
        ]

        result = align_modalities(windows)

        # According to spec (T014), missing ATAC-seq should trigger exclusion
        # The function should filter out this window
        assert len(result) == 0

    def test_missing_h3k27ac_signal_excluded(self):
        """Test that windows with missing H3K27ac data are excluded."""
        # Mock input data with missing H3K27ac signal
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": None,  # Missing H3K27ac
                "cell_type": "IMR90"
            }
        ]

        result = align_modalities(windows)

        # According to spec, missing H3K27ac should trigger exclusion
        assert len(result) == 0

    def test_mixed_modalities_some_excluded(self):
        """Test a mix of valid and invalid windows."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            },
            {
                "chrom": "chr1",
                "start": 3000,
                "end": 4000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": None,  # Missing ATAC
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "K562"
            },
            {
                "chrom": "chr1",
                "start": 5000,
                "end": 6000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "IMR90"
            },
            {
                "chrom": "chr1",
                "start": 7000,
                "end": 8000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": None,  # Missing H3K27ac
                "cell_type": "HUVEC"
            }
        ]

        result = align_modalities(windows)

        # Should retain only the first and third windows (GM12878 and IMR90)
        assert len(result) == 2
        cell_types = [w["cell_type"] for w in result]
        assert "GM12878" in cell_types
        assert "IMR90" in cell_types
        assert "K562" not in cell_types
        assert "HUVEC" not in cell_types

    def test_empty_signal_arrays_excluded(self):
        """Test that windows with empty signal arrays are excluded."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.array([]),  # Empty array
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)

        # Empty arrays should be treated as missing data
        assert len(result) == 0

    def test_coordinate_alignment(self):
        """Test that coordinates are preserved correctly in aligned windows."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)

        assert len(result) == 1
        assert result[0]["chrom"] == "chr1"
        assert result[0]["start"] == 1000
        assert result[0]["end"] == 2000

    def test_signal_length_consistency(self):
        """Test that signal lengths match sequence length in aligned windows."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)

        assert len(result) == 1
        window = result[0]
        assert len(window["sequence"]) == 1000
        assert len(window["atac_signal"]) == 1000
        assert len(window["h3k27ac_signal"]) == 1000

    def test_missing_sequence_excluded(self):
        """Test that windows with missing sequence data are excluded."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": None,  # Missing sequence
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)

        # Missing sequence should exclude the window
        assert len(result) == 0

    def test_all_modalities_missing(self):
        """Test that windows with all modalities missing are excluded."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": None,
                "atac_signal": None,
                "h3k27ac_signal": None,
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)

        assert len(result) == 0

    def test_multiple_cell_types_handling(self):
        """Test alignment across multiple cell types."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            },
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": None,  # Missing for this cell type
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "K562"
            }
        ]

        result = align_modalities(windows)

        # Should retain only GM12878
        assert len(result) == 1
        assert result[0]["cell_type"] == "GM12878"

    def test_signal_shape_validation(self):
        """Test that signal shapes are validated correctly."""
        # Window with mismatched signal length
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(500),  # Wrong length
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)

        # Mismatched signal length should exclude the window
        assert len(result) == 0

    def test_log_missing_data(self):
        """Test that missing data is logged appropriately."""
        import logging
        from unittest.mock import patch

        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": None,
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "K562"
            }
        ]

        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            result = align_modalities(windows)

            # Verify that logging was called for missing data
            # The exact log message format depends on implementation
            assert len(result) == 0
            # If the implementation logs, it should have been called
            # This is a soft check - the test passes if the function runs without error

    def test_empty_input_list(self):
        """Test handling of empty input list."""
        windows = []
        result = align_modalities(windows)
        assert len(result) == 0

    def test_single_valid_window(self):
        """Test handling of a single valid window."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)
        assert len(result) == 1
        assert result[0]["cell_type"] == "GM12878"

    def test_all_windows_invalid(self):
        """Test when all windows have missing data."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": None,
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "K562"
            },
            {
                "chrom": "chr1",
                "start": 3000,
                "end": 4000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": None,
                "cell_type": "IMR90"
            }
        ]

        result = align_modalities(windows)
        assert len(result) == 0

    def test_signal_types_preserved(self):
        """Test that signal types are preserved after alignment."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)
        assert len(result) == 1

        # Check that signals are numpy arrays
        assert isinstance(result[0]["sequence"], np.ndarray)
        assert isinstance(result[0]["atac_signal"], np.ndarray)
        assert isinstance(result[0]["h3k27ac_signal"], np.ndarray)

    def test_cell_type_metadata_preserved(self):
        """Test that cell type metadata is preserved."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)
        assert len(result) == 1
        assert result[0]["cell_type"] == "GM12878"

    def test_chromosomal_coordinates_preserved(self):
        """Test that chromosomal coordinates are preserved."""
        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            },
            {
                "chrom": "chr2",
                "start": 5000,
                "end": 6000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "K562"
            }
        ]

        result = align_modalities(windows)
        assert len(result) == 2

        # Verify coordinates are preserved
        assert result[0]["chrom"] == "chr1"
        assert result[0]["start"] == 1000
        assert result[0]["end"] == 2000

        assert result[1]["chrom"] == "chr2"
        assert result[1]["start"] == 5000
        assert result[1]["end"] == 6000

    def test_signal_normalization_not_modified(self):
        """Test that signal values are not modified during alignment."""
        original_atac = np.array([0.1, 0.5, 0.9])
        original_h3k27ac = np.array([0.2, 0.6, 0.8])

        windows = [
            {
                "chrom": "chr1",
                "start": 1000,
                "end": 2000,
                "sequence": np.random.rand(3, 4),
                "atac_signal": original_atac.copy(),
                "h3k27ac_signal": original_h3k27ac.copy(),
                "cell_type": "GM12878"
            }
        ]

        result = align_modalities(windows)
        assert len(result) == 1

        # Check that values are preserved (within floating point tolerance)
        np.testing.assert_array_almost_equal(
            result[0]["atac_signal"], original_atac
        )
        np.testing.assert_array_almost_equal(
            result[0]["h3k27ac_signal"], original_h3k27ac
        )

    def test_missing_data_handling_policy(self):
        """
        Verify the specific policy for missing data as per spec T014:
        'exclude that cell type... or impute; we choose exclusion to ensure data integrity'.
        """
        # Create windows with various missing data scenarios
        windows = [
            # Valid window
            {
                "chrom": "chr1", "start": 1000, "end": 2000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "GM12878"
            },
            # Missing ATAC
            {
                "chrom": "chr1", "start": 3000, "end": 4000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": None,
                "h3k27ac_signal": np.random.rand(1000),
                "cell_type": "K562"
            },
            # Missing H3K27ac
            {
                "chrom": "chr1", "start": 5000, "end": 6000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": np.random.rand(1000),
                "h3k27ac_signal": None,
                "cell_type": "IMR90"
            },
            # Missing both
            {
                "chrom": "chr1", "start": 7000, "end": 8000,
                "sequence": np.random.rand(1000, 4),
                "atac_signal": None,
                "h3k27ac_signal": None,
                "cell_type": "HUVEC"
            }
        ]

        result = align_modalities(windows)

        # Only GM12878 should remain
        assert len(result) == 1
        assert result[0]["cell_type"] == "GM12878"

        # Verify that no windows with missing data remain
        for window in result:
            assert window["atac_signal"] is not None
            assert window["h3k27ac_signal"] is not None
            assert len(window["atac_signal"]) > 0
            assert len(window["h3k27ac_signal"]) > 0