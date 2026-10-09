"""
Utility to enforce a global runtime timeout for the research pipeline.

The timeout defaults to 6 hours (the maximum allowed runtime per the
specification).  When the timeout expires a warning is written to
``logs/timeout.log`` and the process terminates with exit code **143**,
which is the conventional code for a timeout/termination signal.

The implementation is deliberately lightweight – it uses a daemon thread
that sleeps for the requested number of seconds and then calls
``os._exit(143)``.  Because the thread is a daemon it does not prevent the
interpreter from exiting normally if the main work finishes before the
timeout.

Example usage::

    from src.utils.timeout_wrapper import start_timeout

    # enforce a 10‑second timeout for this run (useful in tests)
    start_timeout(seconds=10)

    # ... long‑running work ...

The function is safe to call multiple times; each call starts an
independent timer.
"""

import os
import threading
import time
from pathlib import Path
from typing import Optional

# Default timeout is 6 hours expressed in seconds.
DEFAULT_TIMEOUT_SECONDS = 6 * 60 * 60  # 21600 seconds


def _timeout_thread(seconds: int) -> None:
    """
    Sleep for *seconds* and then terminate the process.

    The function writes a warning to ``logs/timeout.log`` before exiting.
    """
    time.sleep(seconds)

    # Ensure the logs directory exists.
    log_path = Path("logs") / "timeout.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Record the timeout event.
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} - WARNING - Global timeout of {seconds} seconds reached. Exiting with code 143.\n")

    # Exit the whole interpreter with the required code.
    os._exit(143)


def start_timeout(seconds: Optional[int] = None) -> None:
    """
    Start a watchdog thread that will terminate the process after *seconds*.

    Parameters
    ----------
    seconds : int, optional
        Number of seconds before the timeout fires.  If ``None`` the
        default 6 hour timeout is used.

    The function returns immediately; the watchdog runs in the background.
    """
    timeout_seconds = seconds if seconds is not None else DEFAULT_TIMEOUT_SECONDS

    # Create a daemon thread so that it does not block interpreter shutdown.
    thread = threading.Thread(target=_timeout_thread, args=(timeout_seconds,), daemon=True)
    thread.start()
