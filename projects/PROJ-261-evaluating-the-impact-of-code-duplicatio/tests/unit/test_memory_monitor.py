"""
Unit test for the memory‑monitor helper – it should start a thread and
return a ``MemoryMonitor`` instance without raising.
"""
import time

from memory_monitor import setup_memory_monitoring

def test_memory_monitor_starts_and_stops():
    monitor = setup_memory_monitoring(interval_seconds=0.1)
    # Let the thread run a couple of cycles.
    time.sleep(0.3)
    monitor.stop()
    # After stop the thread should be marked as not alive.
    assert not monitor._thread.is_alive()
