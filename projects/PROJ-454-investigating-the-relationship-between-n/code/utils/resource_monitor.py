"""
Resource monitor for the neural-entropy pipeline (Task T004).

Logs RAM and disk usage to ``logs/resource_usage.log`` and aborts
(raises :class:`ResourceLimitExceeded`) when the process exceeds the
CI budget of 7 GB RAM or 14 GB disk.

Public API (used across the pipeline):
  - get_memory_usage_gb()
  - get_disk_usage_gb()
  - check_resource_limits()
  - enforce_limits()          (raises on violation)
  - log_resource_snapshot()   (accepts optional logger / label)
  - log_resource_usage()      (logger, label, ram_gb=None)
  - record()                  (snapshot + enforce, per T017)

Running ``python code/utils/resource_monitor.py --self-check``
writes one snapshot entry to ``logs/resource_usage.log`` so the
verification criterion ("log entry appears during any script run")
can be checked even without a full pipeline run.
"""
from __future__ import annotations

import argparse
import logging
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

try:
    from llmxive_toolkit import paths

    PROJECT_ROOT = Path(paths.root)
except Exception:  # pragma: no cover - fallback if toolkit unavailable
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "resource_usage.log"

RAM_LIMIT_GB = 7.0
DISK_LIMIT_GB = 14.0

_GB = 1024.0 ** 3


class ResourceLimitExceeded(RuntimeError):
    """Raised when RAM or disk usage exceeds the CI budget."""


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _get_module_logger() -> logging.Logger:
    logger = logging.getLogger("resource_monitor")
    if not logger.handlers:
        _ensure_log_dir()
        handler = logging.FileHandler(LOG_FILE)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def get_memory_usage_gb() -> float:
    """Return this process's current RAM usage in GB (RSS)."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / _GB


def get_disk_usage_gb(path: Optional[str] = None) -> float:
    """Return disk usage (in GB) attributable to the project tree.

    If ``path`` is None, the size of the project directory is measured
    (this is what counts against the 14 GB disk budget). If the tree
    cannot be walked, falls back to free-space accounting on the
    device containing the project.
    """
    target = Path(path) if path else PROJECT_ROOT
    if not target.exists():
        return 0.0
    total = 0
    for dirpath, _dirnames, filenames in os.walk(target):
        for fname in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, fname))
            except OSError:
                continue
    return total / _GB


def _snapshot(label: str = "snapshot") -> Dict[str, Any]:
    return {
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ram_gb": round(get_memory_usage_gb(), 4),
        "disk_gb": round(get_disk_usage_gb(), 4),
        "ram_limit_gb": RAM_LIMIT_GB,
        "disk_limit_gb": DISK_LIMIT_GB,
        "host": platform.node(),
    }


def check_resource_limits(
    ram_limit_gb: float = RAM_LIMIT_GB,
    disk_limit_gb: float = DISK_LIMIT_GB,
) -> bool:
    """Return True if current usage is within limits, False otherwise."""
    ram = get_memory_usage_gb()
    disk = get_disk_usage_gb()
    return ram <= ram_limit_gb and disk <= disk_limit_gb


def enforce_limits(
    ram_limit_gb: float = RAM_LIMIT_GB,
    disk_limit_gb: float = DISK_LIMIT_GB,
) -> None:
    """Abort (raise) if RAM or disk usage exceeds the limits."""
    ram = get_memory_usage_gb()
    disk = get_disk_usage_gb()
    if ram > ram_limit_gb:
        raise ResourceLimitExceeded(
            f"RAM usage {ram:.2f} GB exceeds limit {ram_limit_gb} GB"
        )
    if disk > disk_limit_gb:
        raise ResourceLimitExceeded(
            f"Disk usage {disk:.2f} GB exceeds limit {disk_limit_gb} GB"
        )


def log_resource_snapshot(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Write a RAM/disk snapshot to ``logs/resource_usage.log``.

    Flexible signature for backwards compatibility with existing
    call sites: accepts an optional logger as first positional
    argument and an optional label (positional or keyword).
    """
    logger = None
    label = "snapshot"
    for arg in args:
        if isinstance(arg, logging.Logger):
            logger = arg
        elif isinstance(arg, str):
            label = arg
    label = kwargs.get("label", label)
    logger = kwargs.get("logger", logger)

    snap = _snapshot(label)
    line = (
        f"[{label}] ram={snap['ram_gb']:.3f}GB "
        f"disk={snap['disk_gb']:.3f}GB "
        f"(limits: ram={snap['ram_limit_gb']}GB disk={snap['disk_limit_gb']}GB)"
    )
    if logger is not None:
        logger.info(line)
    _get_module_logger().info(line)
    return snap


def log_resource_usage(logger: Any, label: str, ram_gb: Optional[float] = None) -> Dict[str, Any]:
    """Log a resource-usage step entry (used by compute_entropy)."""
    snap = _snapshot(label)
    if ram_gb is not None:
        snap["ram_gb"] = round(float(ram_gb), 4)
    line = (
        f"[{label}] ram={snap['ram_gb']:.3f}GB disk={snap['disk_gb']:.3f}GB"
    )
    if isinstance(logger, logging.Logger):
        logger.info(line)
    _get_module_logger().info(line)
    return snap


def record(label: str = "record") -> Dict[str, Any]:
    """Take a snapshot, log it, and abort if limits are exceeded (T017)."""
    snap = log_resource_snapshot(label=label)
    if snap["ram_gb"] > RAM_LIMIT_GB:
        raise ResourceLimitExceeded(
            f"RAM usage {snap['ram_gb']:.2f} GB exceeds limit {RAM_LIMIT_GB} GB"
        )
    if snap["disk_gb"] > DISK_LIMIT_GB:
        raise ResourceLimitExceeded(
            f"Disk usage {snap['disk_gb']:.2f} GB exceeds limit {DISK_LIMIT_GB} GB"
        )
    return snap


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline resource monitor")
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Record one snapshot and verify limits (writes logs/resource_usage.log)",
    )
    parser.add_argument("--label", default="self_check")
    parser.add_argument("--watch", type=float, default=0.0,
                        help="Poll every N seconds until interrupted")
    args = parser.parse_args(argv)

    if args.watch > 0:
        try:
            while True:
                record(label="watch")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            return 0

    snap = record(label=args.label)
    print(
        f"resource_monitor: ram={snap['ram_gb']:.3f}GB "
        f"disk={snap['disk_gb']:.3f}GB log={LOG_FILE}"
    )
    if not check_resource_limits():
        print("Resource limits EXCEEDED", flush=True)
        return 1
    print("Resource limits OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
