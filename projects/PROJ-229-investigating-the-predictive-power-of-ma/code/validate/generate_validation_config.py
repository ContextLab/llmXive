"""
generate_validation_config.py

This script generates the validation configuration file used by the external
validation step. It reads the global configuration (config.yaml) and writes
a JSON file containing the required parameters, currently only ``top_n``.
The default value for ``top_n`` is defined in ``config.yaml`` (default: 10).
"""

import json
import logging
from pathlib import Path

# The project provides a config helper that loads the YAML configuration.
from config import get_config

logger = logging.getLogger(__name__)

def generate_validation_config(output_path: Path | str = None) -> Path:
    """
    Generate ``validation_config.json`` containing the ``top_n`` parameter.

    Parameters
    ----------
    output_path : Path | str, optional
        Destination for the JSON file. If omitted, the default location
        ``data/results/validation_config.json`` is used.

    Returns
    -------
    Path
        Path to the written JSON file.
    """
    cfg = get_config()
    top_n = cfg.get("top_n", 10)  # default to 10 if the key is missing

    # Resolve the output path
    if output_path is None:
        output_path = Path("data/results/validation_config.json")
    else:
        output_path = Path(output_path)

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {"top_n": top_n}
    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("Validation config written to %s", output_path)
    except Exception as exc:
        logger.error("Failed to write validation config: %s", exc)
        raise

    return output_path

def main() -> None:
    """
    Entry‑point for ``python -m code.validate.generate_validation_config``.
    """
    generate_validation_config()

if __name__ == "__main__":
    main()