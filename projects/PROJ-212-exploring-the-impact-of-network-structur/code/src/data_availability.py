import logging
from pathlib import Path
from typing import Dict, Any
import yaml
from llmxive_toolkit import paths, get_logger

# Set up a module‑level logger using the platform helper.
log = get_logger(__name__)

def check_data_availability(raw_dir: Path) -> int:
    """
    Count the number of network files present in ``raw_dir``.

    Parameters
    ----------
    raw_dir: Path
        Directory that should contain the downloaded raw network files.

    Returns
    -------
    int
        Number of regular files (any extension) found directly under ``raw_dir``.
    """
    if not raw_dir.is_dir():
        log.warning("Raw data directory %s does not exist.", raw_dir)
        return 0
    # Count all regular files (the loader may create .mtx, .csv, .txt, etc.).
    count = sum(1 for entry in raw_dir.iterdir() if entry.is_file())
    log.debug("Found %d raw network files in %s.", count, raw_dir)
    return count

def write_state_file(state_path: Path, data: Dict[str, Any]) -> None:
    """
    Write a small YAML state file.

    Parameters
    ----------
    state_path: Path
        Full path (including filename) where the YAML document will be written.
    data: dict
        Mapping to be serialised as YAML.
    """
    # Ensure the parent directory exists.
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    log.info("Wrote state file %s with data: %s", state_path, data)

def main() -> None:
    """
    Entry point used by the task runner.

    It counts the raw network files and writes
    ``state/data_availability.yaml`` containing a single key
    ``regression_blocked`` that is ``True`` when fewer than ten raw
    networks are present.
    """
    # Resolve the raw data directory via the toolkit helper.
    raw_dir = paths.data("raw")
    num_files = check_data_availability(raw_dir)

    # According to the specification the regression step is blocked
    # when we have fewer than ten networks.
    regression_blocked = num_files < 10

    # Write the YAML state file under the top‑level ``state`` folder.
    state_path = paths.state("data_availability.yaml")
    write_state_file(state_path, {"regression_blocked": regression_blocked})

    log.info(
        "Data availability check complete: %d files found; regression_blocked=%s",
        num_files,
        regression_blocked,
    )

if __name__ == "__main__":
    main()