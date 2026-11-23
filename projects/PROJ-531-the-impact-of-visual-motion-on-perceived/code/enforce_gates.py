"""
T016b – Enforce modeling gates before any modeling step.

This script reads ``data/processed/modeling_config.json`` and checks the
``abort_flag`` field.  If the flag is ``true`` the pipeline is aborted with a
clear, user‑friendly error message and a non‑zero exit status.  When the flag
is ``false`` the script exits with status ``0`` so that downstream modeling
tasks may run.

The script is deliberately lightweight – it does not produce any output
files – but it is a required gate in the pipeline and must be invoked
(e.g. from ``run_pipeline.sh``) before any model‑fitting scripts.
"""

import json
import sys
from pathlib import Path
import logging

# Use the project's standard logger if available; fall back to a basic logger.
try:
    from utils.logging_config import get_logger
    log = get_logger(__name__)
except Exception:  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("data/processed/modeling_config.json")


def load_config(config_path: Path) -> dict:
    """Load the JSON modelling configuration.

    Args:
        config_path: Path to ``modeling_config.json``.

    Returns:
        Parsed JSON as a dict.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not config_path.is_file():
        log.error(f"Modeling config not found at {config_path}")
        raise FileNotFoundError(f"Missing modeling config: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def enforce_gates(config_path: Path = DEFAULT_CONFIG_PATH) -> bool:
    """Check the ``abort_flag`` and abort the pipeline if needed.

    Args:
        config_path: Path to the modelling configuration JSON.

    Returns:
        ``True`` if the gate passes (``abort_flag`` is ``False``),
        ``False`` otherwise.
    """
    try:
        cfg = load_config(config_path)
    except Exception as e:
        log.error(str(e))
        # Propagate the error – the pipeline should stop.
        raise

    abort_flag = cfg.get("abort_flag", False)
    if abort_flag:
        # The abort flag indicates that the sample size is insufficient for
        # reliable modelling (e.g., N < 80).  We exit with a non‑zero status
        # and a clear message.
        log.error(
            "ABORTING PIPELINE: insufficient sample size detected (abort_flag=True). "
            "Refer to data/processed/modeling_config.json for details."
        )
        return False
    else:
        log.info("Gate check passed – abort_flag is False.")
        return True


def main() -> int:
    """Entry point used by the pipeline runner.

    Returns:
        Exit code: ``0`` if the gate passes, ``1`` otherwise.
    """
    passed = enforce_gates()
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
