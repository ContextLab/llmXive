"""
Simple sanity test for the memory‑monitor utility.
"""

from code.utils.memory_monitor import get_available_memory, estimate_memory_usage, calculate_batch_size

def test_memory_functions():
    avail = get_available_memory()
    assert avail > 0
    usage = estimate_memory_usage(1000, 8)
    assert usage > 0
    batch = calculate_batch_size(1000, 8, 7 * 1024 ** 3)
    assert batch > 0