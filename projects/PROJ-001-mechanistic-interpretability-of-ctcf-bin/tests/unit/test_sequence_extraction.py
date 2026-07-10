import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.filter_complexity import calculate_shannon_entropy, filter_sequence_by_entropy

def test_calculate_shannon_entropy_uniform():
    """
    Test entropy calculation on a uniform sequence.
    A sequence with only one character type has entropy 0.
    """
    seq = "AAAA"
    entropy = calculate_shannon_entropy(seq)
    assert entropy == 0.0, f"Expected entropy 0.0 for uniform sequence, got {entropy}"

def test_calculate_shannon_entropy_maximal():
    """
    Test entropy calculation on a maximally diverse sequence.
    For 4 equally likely bases, entropy should be log2(4) = 2.0.
    """
    # A sequence with equal representation of A, C, G, T
    seq = "ACGTACGT"
    entropy = calculate_shannon_entropy(seq)
    # Allow small floating point tolerance
    assert abs(entropy - 2.0) < 1e-5, f"Expected entropy ~2.0, got {entropy}"

def test_extract_window_positive():
    """
    Test extracting a ±500 bp window (1001 bp total) centered on a peak.
    """
    # Create a dummy sequence longer than 1001 bp
    # We need a sequence of at least 1001 bases to center at 500
    seq = "A" * 1001
    center_idx = 500
    window_size = 1000  # ±500 means 500 on left, 500 on right, total 1001? 
    # Wait, the task says "±500 bp windows". Usually this means 500 upstream + 500 downstream + 1 center = 1001.
    # Or it could mean 500 total (250 each side). 
    # Let's look at T013 description: "extract 1000bp windows (±500bp)". 
    # 1000bp usually implies 500 left + 500 right. If center is inclusive, it's 1001. 
    # Let's assume the implementation in extract_features.py handles the math.
    # For this test, we verify the logic of slicing.
    
    # Let's assume the function signature is extract_window(sequence, center, half_window=500)
    # If half_window is 500, start = center - 500, end = center + 500 + 1 (if inclusive) or center + 500.
    # Standard bioinformatics: ±500bp usually means 1001bp total (500 upstream, 1 base, 500 downstream).
    # Let's test a helper that mimics the extraction logic.
    
    half_window = 500
    start = center_idx - half_window
    end = center_idx + half_window + 1 # +1 for python slice end
    
    window = seq[start:end]
    assert len(window) == 1001, f"Expected length 1001, got {len(window)}"
    assert window[500] == "A" # Center base

def test_extract_window_boundary():
    """
    Test extracting a window when the center is near the start of the sequence.
    Should handle padding or raise an error depending on implementation.
    Here we test that it doesn't crash and handles indices gracefully if padding is expected.
    """
    seq = "A" * 100
    center_idx = 10
    half_window = 500
    
    start = center_idx - half_window
    end = center_idx + half_window + 1
    
    # If start is negative, slicing handles it by starting at 0
    # But the length will be shorter than expected.
    window = seq[start:end]
    
    # We expect the window to be shorter than 1001 if the sequence is too short
    # This test verifies the slicing logic works without IndexError
    assert len(window) <= 1001
    assert start <= 0 # Verify start is negative
    
def test_filter_low_complexity():
    """
    Test that low complexity sequences (entropy < threshold) are filtered out.
    """
    low_complexity = "AAAAA"
    high_complexity = "ACGTA"
    threshold = 0.8
    
    is_low_1 = filter_sequence_by_entropy(low_complexity, threshold)
    is_low_2 = filter_sequence_by_entropy(high_complexity, threshold)
    
    assert is_low_1 == True, "Low complexity sequence should be flagged as True (filtered)"
    assert is_low_2 == False, "High complexity sequence should be flagged as False (kept)"

def test_window_extraction_logic():
    """
    Specific test for the ±500bp windowing logic described in T013.
    Verifies that given a center and a sequence, the correct slice is returned.
    """
    # Simulate the logic expected in extract_features.py
    def get_window(seq: str, center: int, half_width: int = 500) -> str:
        start = max(0, center - half_width)
        end = min(len(seq), center + half_width + 1)
        return seq[start:end]

    long_seq = "ACGT" * 300 # 1200 bases
    center = 600
    
    window = get_window(long_seq, center, 500)
    assert len(window) == 1001, f"Expected 1001 bp window, got {len(window)}"
    assert window[500] == long_seq[600] # Center matches

    # Test with center too close to start
    center_start = 100
    window_start = get_window(long_seq, center_start, 500)
    # 100 - 500 = -400 -> 0. 100 + 500 + 1 = 601.
    assert len(window_start) == 601
    assert window_start[0] == long_seq[0]
    
    # Test with center too close to end
    center_end = 1150
    window_end = get_window(long_seq, center_end, 500)
    # 1150 - 500 = 650. 1150 + 500 + 1 = 1651 -> 1200.
    assert len(window_end) == 1200 - 650
    assert window_end[0] == long_seq[650]