"""Enforce free‑tier resource limits.

The script reads ``data/results/resource_usage.json`` (produced by
``src.utils.resource_monitor.ResourceMonitor``) and aborts with a clear
error message if any of the limits are exceeded:

- wall_time_seconds > 6 hours (21600 s)
- peak_memory_gb > 7 GB
- peak_disk_gb > 20 GB
"""

import json
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Limits as defined in the specification (FR‑011)
MAX_WALL_TIME_S = 6 * 60 * 60      # 6 hours → 21600 s
MAX_PEAK_MEMORY_GB = 7.0
MAX_PEAK_DISK_GB = 20.0

def _load_usage() -> dict:
    usage_path = paths.results("resource_usage.json")
    if not usage_path.is_file():
        raise FileNotFoundError(f"Resource usage file not found: {usage_path}")
    with usage_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def _check_limits(usage: dict) -> None:
    wall = usage.get("wall_time_seconds", 0)
    mem = usage.get("peak_memory_gb", 0)
    disk = usage.get("peak_disk_gb", 0)

    violations = []
    if wall > MAX_WALL_TIME_S:
        violations.append(f"wall time {wall:.1f}s exceeds {MAX_WALL_TIME_S}s")
    if mem > MAX_PEAK_MEMORY_GB:
        violations.append(f"peak memory {mem:.2f}GB exceeds {MAX_PEAK_MEMORY_GB}GB")
    if disk > MAX_PEAK_DISK_GB:
        violations.append(f"peak disk {disk:.2f}GB exceeds {MAX_PEAK_DISK_GB}GB")

    if violations:
        msg = "Resource limit violation(s): " + "; ".join(violations)
        raise RuntimeError(msg)

def main() -> None:
    """CLI entry point used by the test suite."""
    try:
        usage = _load_usage()
        _check_limits(usage)
        log.info("Resource usage within free‑tier limits.")
    except Exception as exc:
        log.error("Resource limit check failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
