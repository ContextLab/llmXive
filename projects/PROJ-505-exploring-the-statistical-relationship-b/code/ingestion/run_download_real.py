"""
Helper script to invoke the real-data ingestion routine.

This script attempts to download the ACE, WIND, and OMNI datasets via
``code.ingestion.download_real.download_and_preserve``.  If any part of the
download fails (e.g., because the runner has no network access or the
CDAWeb service is unavailable), the exception is caught, a clear error
message is logged, and the script exits with status 0.  This behaviour
allows the overall pipeline (which defaults to the deterministic synthetic
data path) to continue without being aborted by a hard failure in the
real‑data download step.

The script is deliberately minimal and does not attempt any synthetic
fallback; the responsibility for deciding whether to use real or synthetic
data remains with the top‑level driver (``code.main``).  The only purpose
is to provide a safe entry point that can be invoked in environments where
the real download is expected to succeed, while still permitting graceful
continuation when it does not.
"""

import sys
from llmxive_toolkit import get_logger
from code.ingestion import download_real

log = get_logger(__name__)

def main() -> int:
    """Run the real‑data ingestion and handle failures gracefully."""
    try:
        # Use the default date range (2000‑01‑01 to 2020‑12‑31).
        # The underlying function validates the dates.
        summary = download_real.download_and_preserve()
        log.info("Real‑data ingestion completed successfully: %s", summary)
    except Exception as exc:  # noqa: BLE001
        # Log the exception but do not re‑raise – we want a clean exit.
        log.error(
            "Real‑data ingestion failed (this is expected in offline CI runs): %s",
            exc,
        )
        # Do NOT propagate the error; the pipeline should continue.
    # Always exit with status 0 to indicate graceful handling.
    return 0

if __name__ == "__main__":
    sys.exit(main())