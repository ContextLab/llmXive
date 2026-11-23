import json
import csv
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.detect_threshold import (
    load_raw_annotated_data,
    load_binned_accuracy_data,
    detect_threshold,
    save_results,
    MIN_BIN_SIZE
)

def test_t021_merge_logic():
    """
    Test that T021 correctly merges bins when 3+ is small but 2+3+ is large enough.
    """
    # Mock data: 1-hop (50), 2-hop (40), 3+ (5) -> Total 3+ is 5 (<50)
    # Merged 2+3+ = 45 (Still < 50 in this specific mock? Let's adjust)
    # Let's make 2-hop (45), 3+ (10) -> Total 55. This should trigger merge.
    
    mock_records = []
    # 1-hop
    for i in range(50):
        mock_records.append({'id': str(i), 'chain_length': 1, 'correctness': True})
    # 2-hop
    for i in range(50, 95):
        mock_records.append({'id': str(i), 'chain_length': 2, 'correctness': False})
    # 3+ (10 records)
    for i in range(95, 105):
        mock_records.append({'id': str(i), 'chain_length': 3, 'correctness': False})

    bin_stats = load_binned_accuracy_data(mock_records)
    
    # Verify bin counts
    assert bin_stats['1']['count'] == 50
    assert bin_stats['2']['count'] == 45
    assert bin_stats['3+']['count'] == 10
    
    # Run detect_threshold logic
    results = detect_threshold(mock_records, bin_stats)
    
    # Verify T021 logic:
    # 1. Status should be completed (since merged >= 50)
    assert results['status'] == 'completed', f"Expected completed, got {results['status']}"
    # 2. Bin status should be merged
    assert results['bin_status'] == 'merged', f"Expected merged, got {results['bin_status']}"
    # 3. Merged definition should be correct
    assert results['merged_bin_definition'] == ['2', '3+']
    # 4. Conclusion should be set
    assert results['conclusion'] in ['PASS', 'FAIL']

def test_t021_defer_logic():
    """
    Test that T021 correctly defers when even the merged bin is too small.
    """
    mock_records = []
    # 1-hop (50)
    for i in range(50):
        mock_records.append({'id': str(i), 'chain_length': 1, 'correctness': True})
    # 2-hop (10)
    for i in range(50, 60):
        mock_records.append({'id': str(i), 'chain_length': 2, 'correctness': False})
    # 3+ (5)
    for i in range(60, 65):
        mock_records.append({'id': str(i), 'chain_length': 3, 'correctness': False})

    bin_stats = load_binned_accuracy_data(mock_records)
    
    assert bin_stats['2']['count'] == 10
    assert bin_stats['3+']['count'] == 5
    # Merged = 15 < 50
    
    results = detect_threshold(mock_records, bin_stats)
    
    assert results['status'] == 'deferred'
    assert results['bin_status'] == 'deferred'
    assert results['reason'] == 'insufficient_power'
    assert results['conclusion'] == 'DEFERRED'

if __name__ == "__main__":
    test_t021_merge_logic()
    print("Test 1 passed: Merge logic works.")
    test_t021_defer_logic()
    print("Test 2 passed: Defer logic works.")
    print("All T021 tests passed.")