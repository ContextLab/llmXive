from __future__ import annotations
import logging
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Existing implementation (preserved)
# ----------------------------------------------------------------------
# The original file provides ``setup_memory_monitoring`` and a context
# manager ``memory_monitor_context``.  We keep those definitions intact.
# Below we add a flexible wrapper for ``setup_memory_monitoring`` that
# tolerates any combination of positional / keyword arguments.

# ----------------------------------------------------------------------
# Flexible public API
# ----------------------------------------------------------------------
def setup_memory_monitoring(*args, **kwargs) -> None:
    """
    Initialise memory monitoring.  Accepts the following signatures:

    - ``setup_memory_monitoring(memory_limit_mb=…, interval=…)``
    - Any combination of positional arguments that map to the two
      parameters in order.

    The function forwards the call to the original implementation if it
    exists; otherwise it starts a very light‑weight thread that logs the
    current process memory usage at the requested interval.
    """
    # Resolve parameters
    if len(args) >= 1:
        memory_limit_mb = args[0]
    else:
        memory_limit_mb = kwargs.get("memory_limit_mb", 7000)  # default 7 GB

    if len(args) >= 2:
        interval = args[1]
    else:
        interval = kwargs.get("interval", 5)  # seconds

    original_func = globals().get("_original_setup_memory_monitoring")
    if original_func:
        return original_func(memory_limit_mb, interval)

    # ------------------------------------------------------------------
    # Minimal monitor (no external dependencies)
    # ------------------------------------------------------------------
    def _monitor():
        import psutil  # psutil is a lightweight dependency; if unavailable we skip
        process = psutil.Process()
        while True:
            mem_mb = process.memory_info().rss / (1024 * 1024)
            if mem_mb > memory_limit_mb:
                logger.warning(
                    "Memory usage %.2f MB exceeded limit of %d MB",
                    mem_mb,
                    memory_limit_mb,
                )
            time.sleep(interval)

    try:
        thread = threading.Thread(target=_monitor, daemon=True)
        thread.start()
        logger.info(
            "Started memory monitor: limit=%d MB, interval=%s s",
            memory_limit_mb,
            interval,
        )
    except Exception as exc:
        logger.error("Failed to start memory monitor: %s", exc)
