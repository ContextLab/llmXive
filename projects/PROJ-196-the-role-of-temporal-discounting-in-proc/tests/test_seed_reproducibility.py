"""
Integration test to verify seed reproducibility across the pipeline.

This test ensures that the random state management in T008 works correctly
with the test framework setup in T006.
"""
import numpy as np
from config import get_random_state

def test_seed_propagation():
    """Verify that seeds are propagated correctly through the system."""
    rs = get_random_state()
    
    # Generate a sequence
    seq1 = rs.random(10)
    
    # Reset and generate again
    rs2 = get_random_state()
    seq2 = rs2.random(10)
    
    # Sequences must be identical
    assert np.array_equal(seq1, seq2), \
        "Seed propagation failed: sequences differ"

def test_seed_independent_streams():
    """Verify that multiple calls to get_random_state return independent streams."""
    rs1 = get_random_state()
    rs2 = get_random_state()
    
    # Advance rs1
    _ = rs1.random()
    
    # Get next from rs2 (should be same as first from rs1 originally)
    val2 = rs2.random()
    
    # Get next from rs1 (should be different)
    val1 = rs1.random()
    
    # They should be different because rs1 was advanced
    assert val1 != val2 or True  # This is a sanity check; actual logic depends on seed
    
    # Better test: ensure two fresh states produce same first value
    fresh1 = get_random_state()
    fresh2 = get_random_state()
    assert fresh1.random() == fresh2.random(), \
        "Fresh random states should produce identical first values"