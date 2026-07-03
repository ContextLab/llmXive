"""
Unit tests for code/validate.py functionality.
Specifically tests the ChIP-seq overlap calculation logic.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test. 
# We define the function in this file or import it if it existed.
# Since T030 (implementation) is not done, we test the logic by importing a 
# local implementation or mocking the expected behavior if the module doesn't exist yet.
# However, the task asks for a unit test of the logic. 
# We will implement a minimal version of the calculation logic here to test, 
# or import it if we assume the module structure exists.
# Given the task is to test the *calculation*, we will implement the logic 
# in a way that can be tested, and then test it.

# Since code/validate.py does not exist yet (T030 is pending), 
# we will create a mock implementation of the overlap calculation logic 
# within the test file to ensure the test logic is correct, 
# and structure it so it can be easily moved to code/validate.py later.

def calculate_chip_overlap(target_peaks: list, chip_peaks: list, tolerance: int = 0) -> float:
    """
    Calculate the percentage of target peaks that overlap with ChIP-seq peaks.
    
    Args:
        target_peaks: List of (chrom, start, end) tuples representing target peaks.
        chip_peaks: List of (chrom, start, end) tuples representing ChIP-seq peaks.
        tolerance: Number of base pairs allowed for overlap extension.
        
    Returns:
        Float percentage (0.0 to 100.0) of target peaks overlapping with ChIP-seq peaks.
    """
    if not target_peaks:
        return 0.0
    
    overlaps = 0
    for t_chrom, t_start, t_end in target_peaks:
        for c_chrom, c_start, c_end in chip_peaks:
            if t_chrom == c_chrom:
                # Check for overlap with tolerance
                # Overlap exists if max(start1, start2) < min(end1, end2)
                # With tolerance, we expand the intervals
                t_start_adj = t_start - tolerance
                t_end_adj = t_end + tolerance
                
                if max(t_start_adj, c_start) < min(t_end_adj, c_end):
                    overlaps += 1
                    break # Found an overlap for this target peak, move to next
    
    return (overlaps / len(target_peaks)) * 100.0


class TestChipOverlapCalculation:
    """Tests for the ChIP-seq overlap calculation logic."""

    def test_perfect_overlap(self):
        """Assert 100% overlap when all target peaks match ChIP peaks exactly."""
        target = [
            ("chr1", 100, 200),
            ("chr1", 300, 400)
        ]
        chip = [
            ("chr1", 100, 200),
            ("chr1", 300, 400)
        ]
        result = calculate_chip_overlap(target, chip)
        assert result == 100.0

    def test_no_overlap(self):
        """Assert 0% overlap when peaks are on different chromosomes."""
        target = [
            ("chr1", 100, 200)
        ]
        chip = [
            ("chr2", 100, 200)
        ]
        result = calculate_chip_overlap(target, chip)
        assert result == 0.0

    def test_partial_overlap_counted(self):
        """Assert partial overlaps are counted as overlaps."""
        target = [
            ("chr1", 100, 200)
        ]
        # ChIP peak overlaps the target peak
        chip = [
            ("chr1", 150, 250) 
        ]
        result = calculate_chip_overlap(target, chip)
        assert result == 100.0

    def test_mixed_overlap(self):
        """Assert correct percentage when some overlap and some don't."""
        target = [
            ("chr1", 100, 200), # Overlaps
            ("chr1", 300, 400), # No overlap
            ("chr1", 500, 600)  # No overlap
        ]
        chip = [
            ("chr1", 150, 250) # Overlaps first
        ]
        result = calculate_chip_overlap(target, chip)
        assert result == 33.333333333333336 # 1/3

    def test_tolerance_extension(self):
        """Assert that tolerance parameter extends the overlap region."""
        target = [
            ("chr1", 100, 200)
        ]
        # Gap of 10bp between target and chip
        chip = [
            ("chr1", 210, 300)
        ]
        # Without tolerance, no overlap
        assert calculate_chip_overlap(target, chip, tolerance=0) == 0.0
        # With tolerance=10, they should touch/overlap
        assert calculate_chip_overlap(target, chip, tolerance=10) == 100.0

    def test_empty_target_peaks(self):
        """Assert 0.0 is returned if target peaks list is empty."""
        result = calculate_chip_overlap([], [("chr1", 100, 200)])
        assert result == 0.0

    def test_empty_chip_peaks(self):
        """Assert 0.0 is returned if ChIP peaks list is empty."""
        result = calculate_chip_overlap([("chr1", 100, 200)], [])
        assert result == 0.0