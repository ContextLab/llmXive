import builtins
import sys

from utils.memory_monitor import MemoryMonitor

def test_memory_monitor_noop_methods():
    """
    Ensure that any undefined attribute access on MemoryMonitor returns a
    callable that does nothing (no exception is raised).
    """
    monitor = MemoryMonitor()
    # Call a few typical logger‑style methods that are not explicitly defined
    for method_name in ["info", "debug", "warning", "error", "critical"]:
        method = getattr(monitor, method_name)
        # Should be callable and return None regardless of arguments
        assert callable(method)
        assert method("test message") is None
        assert method(key="value") is None