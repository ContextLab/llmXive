"""
Unit tests for point filtering logic in code/data/preprocess.py.

This module validates the confidence index filtering and sample rejection
logic as specified in User Story 1 (US1).
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path for imports if running standalone
if "code" not in sys.modules:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.preprocess import filter_by_confidence, process_ebsd_dataset
from code.data.models import EbsdSample, TextureDescriptor


class TestFilterPointsBelowConfidence:
    """Tests for filtering individual data points with low confidence."""

    def test_filter_points_below_confidence(self):
        """
        Verify that filter_by_confidence removes points with confidence < 0.1
        while keeping the sample object valid.
        """
        # Create a mock sample with mixed confidence values
        # Using dummy orientation data (Euler angles) and confidence indices
        num_points = 100
        eulers = np.random.rand(num_points, 3) * 180.0  # Random Euler angles
        confidences = np.random.rand(num_points)  # Random confidence [0, 1]

        # Ensure we have some points below 0.1 and some above
        confidences[0:10] = 0.05  # Low confidence
        confidences[10:20] = 0.95  # High confidence
        confidences[20:] = 0.5  # Medium confidence

        # Create a mock EbsdSample
        # Note: EbsdSample expects specific fields based on model definition
        sample = EbsdSample(
            material="Al",
            reduction=20,
            eulers=eulers,
            confidence_indices=confidences,
            sample_id="test_sample_001"
        )

        # Apply the filter
        filtered_sample = filter_by_confidence(sample, threshold=0.1)

        # Assertions
        assert filtered_sample is not None, "Filtered sample should not be None"
        assert filtered_sample.sample_id == sample.sample_id, "Sample ID should be preserved"
        assert filtered_sample.material == sample.material, "Material should be preserved"
        assert filtered_sample.reduction == sample.reduction, "Reduction should be preserved"

        # Check that all remaining confidences are >= 0.1
        assert np.all(filtered_sample.confidence_indices >= 0.1), \
            "All remaining points should have confidence >= 0.1"

        # Check that the number of points is reduced
        assert len(filtered_sample.confidence_indices) < len(sample.confidence_indices), \
            "Filtered sample should have fewer points than original"

        # Specifically check that we removed the low confidence points
        expected_remaining = num_points - 10  # We set 10 points to 0.05
        assert len(filtered_sample.confidence_indices) == expected_remaining, \
            f"Expected {expected_remaining} points, got {len(filtered_sample.confidence_indices)}"

        # Verify the orientations array shape matches the confidence array
        assert filtered_sample.eulers.shape[0] == len(filtered_sample.confidence_indices), \
            "Eulers array should match confidence array length"

    def test_filter_all_points_below_threshold(self):
        """
        Verify behavior when ALL points are below the confidence threshold.
        The sample should be returned but with zero points, or None depending on implementation.
        Based on T014 logic, if >50% are filtered, it's flagged as low reliability.
        """
        num_points = 50
        eulers = np.random.rand(num_points, 3) * 180.0
        confidences = np.full(num_points, 0.05)  # All below 0.1

        sample = EbsdSample(
            material="Cu",
            reduction=40,
            eulers=eulers,
            confidence_indices=confidences,
            sample_id="test_sample_002"
        )

        filtered_sample = filter_by_confidence(sample, threshold=0.1)

        # If implementation returns None for empty samples:
        if filtered_sample is None:
            pass  # Valid behavior
        else:
            # If it returns a sample with 0 points:
            assert len(filtered_sample.confidence_indices) == 0, \
                "Sample should have 0 points if all are filtered out"
            assert filtered_sample.eulers.shape[0] == 0, \
                "Eulers array should be empty"

    def test_filter_no_points_below_threshold(self):
        """
        Verify behavior when NO points are below the confidence threshold.
        The sample should be returned unchanged (or with identical data).
        """
        num_points = 50
        eulers = np.random.rand(num_points, 3) * 180.0
        confidences = np.full(num_points, 0.9)  # All above 0.1

        sample = EbsdSample(
            material="Ni",
            reduction=60,
            eulers=eulers,
            confidence_indices=confidences,
            sample_id="test_sample_003"
        )

        filtered_sample = filter_by_confidence(sample, threshold=0.1)

        assert filtered_sample is not None
        assert len(filtered_sample.confidence_indices) == num_points, \
            "All points should be retained"
        assert np.allclose(filtered_sample.confidence_indices, confidences), \
            "Confidence values should be unchanged"


class TestSampleRejectionNotTriggered:
    """Tests for sample-level rejection logic."""

    def test_sample_rejection_not_triggered(self):
        """
        Verify that a sample with mixed confidence values (some < 0.1, some >= 0.1)
        is NOT rejected entirely, but processed with the valid points only.
        This tests US-1 Scenario 2 and FR-002.
        """
        # Create a sample where 40% of points are below threshold
        # This is < 50%, so the sample should NOT be rejected
        num_points = 100
        eulers = np.random.rand(num_points, 3) * 180.0
        confidences = np.random.rand(num_points)

        # Set 40 points to low confidence (40%)
        confidences[0:40] = 0.05
        # Set 60 points to high confidence (60%)
        confidences[40:100] = 0.9

        sample = EbsdSample(
            material="Al",
            reduction=20,
            eulers=eulers,
            confidence_indices=confidences,
            sample_id="test_sample_004"
        )

        # Process the dataset (which includes filtering and potential rejection)
        # We mock the logging to capture warnings if any
        with patch('code.data.preprocess.logging') as mock_logging:
            result = process_ebsd_dataset([sample], confidence_threshold=0.1)

        # Assertions
        assert result is not None, "Result should not be None"
        assert len(result) > 0, "Result should contain samples"

        # The sample should be in the result (not rejected)
        # It might be the only sample or one of several
        found_sample = False
        for res_sample in result:
            if res_sample.sample_id == sample.sample_id:
                found_sample = True
                # Verify it has filtered points
                assert len(res_sample.confidence_indices) == 60, \
                    "Sample should have 60 valid points (100 - 40 low confidence)"
                assert np.all(res_sample.confidence_indices >= 0.1), \
                    "All remaining points should have confidence >= 0.1"
                break

        assert found_sample, "Original sample should be in the result (not rejected)"

    def test_sample_rejection_triggered_when_over_50_percent_filtered(self):
        """
        Verify that a sample where >50% of points are filtered IS rejected/excluded.
        This tests the edge case mentioned in T014.
        """
        # Create a sample where 60% of points are below threshold
        num_points = 100
        eulers = np.random.rand(num_points, 3) * 180.0
        confidences = np.random.rand(num_points)

        # Set 60 points to low confidence (60% > 50%)
        confidences[0:60] = 0.05
        # Set 40 points to high confidence (40%)
        confidences[60:100] = 0.9

        sample = EbsdSample(
            material="Cu",
            reduction=40,
            eulers=eulers,
            confidence_indices=confidences,
            sample_id="test_sample_005"
        )

        # Process the dataset
        with patch('code.data.preprocess.logging') as mock_logging:
            result = process_ebsd_dataset([sample], confidence_threshold=0.1)

        # The sample should NOT be in the result (rejected due to >50% low reliability)
        found_sample = False
        for res_sample in result:
            if res_sample.sample_id == sample.sample_id:
                found_sample = True
                break

        assert not found_sample, \
            "Sample should be excluded from result when >50% of points are filtered"

    def test_mixed_samples_processing(self):
        """
        Verify that a dataset with multiple samples is processed correctly:
        - Some samples retained (mixed confidence, <50% filtered)
        - Some samples rejected (>50% filtered)
        """
        samples = []

        # Sample 1: 30% low confidence -> should be retained
        num_points = 100
        eulers1 = np.random.rand(num_points, 3) * 180.0
        confidences1 = np.random.rand(num_points)
        confidences1[0:30] = 0.05
        samples.append(EbsdSample(
            material="Al", reduction=20, eulers=eulers1,
            confidence_indices=confidences1, sample_id="sample_retain_1"
        ))

        # Sample 2: 70% low confidence -> should be rejected
        eulers2 = np.random.rand(num_points, 3) * 180.0
        confidences2 = np.random.rand(num_points)
        confidences2[0:70] = 0.05
        samples.append(EbsdSample(
            material="Cu", reduction=40, eulers=eulers2,
            confidence_indices=confidences2, sample_id="sample_reject_1"
        ))

        # Sample 3: 10% low confidence -> should be retained
        eulers3 = np.random.rand(num_points, 3) * 180.0
        confidences3 = np.random.rand(num_points)
        confidences3[0:10] = 0.05
        samples.append(EbsdSample(
            material="Ni", reduction=60, eulers=eulers3,
            confidence_indices=confidences3, sample_id="sample_retain_2"
        ))

        # Process
        with patch('code.data.preprocess.logging') as mock_logging:
            result = process_ebsd_dataset(samples, confidence_threshold=0.1)

        # Verify results
        result_ids = [s.sample_id for s in result]

        assert "sample_retain_1" in result_ids, "Sample 1 should be retained"
        assert "sample_reject_1" not in result_ids, "Sample 2 should be rejected"
        assert "sample_retain_2" in result_ids, "Sample 3 should be retained"

        assert len(result) == 2, "Exactly 2 samples should be in the result"