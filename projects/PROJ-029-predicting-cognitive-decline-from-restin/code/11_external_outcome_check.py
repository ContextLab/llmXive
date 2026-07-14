"""External outcome check – thin wrapper around shared logger utilities."""
from __future__ import annotations

# Re‑export the fully tolerant logger implementation
from utils.logger import LogEntry, ReproducibilityLogger, get_logger, log_operation

def check_mci_conversion() -> bool:
    """Placeholder: check for MCI conversion data; not implemented."""
    get_logger().info("check_mci_conversion called")
    return False

def write_limitation(message: str) -> None:
    """Write a limitation note to ``data/artifacts/limitations.txt``."""
    from pathlib import Path

    out_path = Path("data/artifacts/limitations.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(message)

def main() -> None:
    """Entry point used by the run‑book."""
    logger = get_logger("external_outcome")
    logger.info("Running external outcome check")
    if not check_mci_conversion():
        write_limitation("MCI conversion data not available.")
    # Example of a direct logging call
    log_operation("external_outcome_check", status="completed")
