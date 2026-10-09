"""
Global timeout enforcement for the research pipeline.

The pipeline must abort after a configurable wall‑clock limit
(default: 6 hours) and exit with status code ``143`` – the Unix
convention for a timeout.  This module provides a simple, cross‑platform
implementation based on ``threading.Timer`` that writes a warning to the
structured logger defined in ``src.utils.logger`` before terminating.

Usage
-----
Call :func:`enforce_timeout` as early as possible in the pipeline
(e.g. from ``src.cli.main``).  The function returns the ``Timer`` object,
which can be cancelled (``timer.cancel()``) if the pipeline finishes
before the deadline.

The module also offers a helper :func:`check_elapsed` that can be used
manually in long‑running loops to raise ``SystemExit(143)`` when the
elapsed time exceeds the limit.
"""

import sys
import threading
import time
import datetime
from typing import Optional

# Import the JSON logger – this ensures any timeout warning is recorded in
# ``logs/timeout.log`` using the same format as the rest of the pipeline.
from code.src.utils.logger import get_logger

__all__ = ["enforce_timeout", "check_elapsed", "cancel_timeout"]

# Default timeout in hours – matches the ``HYPERPARAMS["timeout_hours"]``
# constant from ``config.settings``.
DEFAULT_TIMEOUT_HOURS = 6

_timer: Optional[threading.Timer] = None

def _timeout_action() -> None:
    """
    Action executed by the background timer when the deadline is reached.
    It logs a warning and exits the interpreter with status ``143``.
    """
    logger = get_logger("timeout")
    logger.warning(
        f"Global timeout of {DEFAULT_TIMEOUT_HOURS} h exceeded – terminating process"
    )
    # ``sys.exit`` raises ``SystemExit`` which terminates the program.
    sys.exit(143)

def enforce_timeout(timeout_hours: int = DEFAULT_TIMEOUT_HOURS) -> threading.Timer:
    """
    Start a background timer that will abort the process after
    ``timeout_hours`` hours.

    Parameters
    ----------
    timeout_hours: int, optional
        Number of hours after which the process should be terminated.
        Defaults to the project‑wide constant (6 h).

    Returns
    -------
    threading.Timer
        The timer object – callers may cancel it via ``cancel_timeout``.
    """
    global _timer
    # Convert hours to seconds for ``threading.Timer``.
    timeout_seconds = timeout_hours * 3600
    _timer = threading.Timer(timeout_seconds, _timeout_action)
    _timer.daemon = True
    _timer.start()
    return _timer

def cancel_timeout() -> None:
    """
    Cancel the previously started timeout timer, if any.
    """
    global _timer
    if _timer is not None:
        _timer.cancel()
        _timer = None

def check_elapsed(start_time: float, timeout_hours: int = DEFAULT_TIMEOUT_HOURS) -> None:
    """
    Manual check that can be inserted into long‑running loops.

    Parameters
    ----------
    start_time: float
        ``time.time()`` value captured at the beginning of the operation.
    timeout_hours: int, optional
        Maximum allowed runtime in hours (defaults to the project‑wide
        constant).

    Raises
    ------
    SystemExit
        If the elapsed time exceeds the configured limit – exits with code
        ``143``.
    """
    elapsed_seconds = time.time() - start_time
    if elapsed_seconds > timeout_hours * 3600:
        # Log via the structured logger before exiting.
        logger = get_logger("timeout")
        logger.warning(
            f"Elapsed time {datetime.timedelta(seconds=int(elapsed_seconds))} exceeds "
            f"global timeout of {timeout_hours} h"
        )
        sys.exit(143)