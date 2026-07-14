import time
from pathlib import Path

from utils.memory_monitor import MemoryMonitor


def test_memory_monitor_writes_log(tmp_path: Path):
    """
    The monitor should create a JSON‑lines file containing at least one
    measurement record and a summary line with ``peak_memory_mb`` and
    ``duration_seconds`` fields.
    """
    log_file = tmp_path / "mem.log"

    monitor = MemoryMonitor(log_path=log_file, interval=0.1)
    monitor.start()
    # Let it collect a few samples.
    time.sleep(0.35)
    monitor.stop()

    # The file must exist and be non‑empty.
    assert log_file.is_file()
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) >= 2  # at least one sample + summary

    # The last line should be the summary.
    import json

    summary = json.loads(lines[-1])
    assert summary.get("summary") is True
    assert isinstance(summary.get("peak_memory_mb"), (int, float))
    assert isinstance(summary.get("duration_seconds"), (int, float))

# The permissive fallback should never raise an AttributeError.
def test_memory_monitor_fallback_methods():
    monitor = MemoryMonitor()
    # Call a handful of typical logger methods that do not exist.
    for method in ["info", "debug", "warning", "error", "log"]:
        getattr(monitor, method)("test message")  # should be a no‑op, no exception.