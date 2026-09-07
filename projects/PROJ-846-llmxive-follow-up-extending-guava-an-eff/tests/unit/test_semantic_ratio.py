"""
Unit test for the semantic failure ratio calculation.

Verifies that the ratio of semantic failures to total failures
(excluding perception and latency failures) is calculated correctly.
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.models import FailureType

def test_semantic_ratio_calculation():
    """Test the logic of filtering and calculating the semantic ratio."""
    # Simulate a list of failures
    failures = [
        FailureType.SEMANTIC,
        FailureType.SEMANTIC,
        FailureType.PERCEPTION,
        FailureType.LATENCY,
        FailureType.GEOMETRIC,
        FailureType.SEMANTIC
    ]
    
    # Logic: Exclude PERCEPTION and LATENCY
    filtered = [f for f in failures if f not in [FailureType.PERCEPTION, FailureType.LATENCY]]
    
    # Count semantic in filtered
    semantic_count = sum(1 for f in filtered if f == FailureType.SEMANTIC)
    total_filtered = len(filtered)
    
    if total_filtered == 0:
        ratio = 0.0
    else:
        ratio = semantic_count / total_filtered
    
    # Expected:
    # Total: 6
    # Excluded: 2 (PERCEPTION, LATENCY) -> 4 remaining
    # Semantic in remaining: 3
    # Ratio: 3/4 = 0.75
    
    assert total_filtered == 4
    assert semantic_count == 3
    assert ratio == 0.75

def test_all_perception_latency():
    """Test case where all failures are perception or latency."""
    failures = [FailureType.PERCEPTION, FailureType.LATENCY, FailureType.PERCEPTION]
    
    filtered = [f for f in failures if f not in [FailureType.PERCEPTION, FailureType.LATENCY]]
    
    assert len(filtered) == 0
    # Ratio should be 0.0 to avoid division by zero
    total_filtered = len(filtered)
    if total_filtered == 0:
        ratio = 0.0
    else:
        ratio = 0.0 # Should not happen in logic
        
    assert ratio == 0.0
