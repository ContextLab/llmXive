"""
Flag source script for the diffusion dataset pipeline.

This script inspects the `data/raw` directory to determine whether the
dataset was obtained from a real external source or generated synthetically.
It then writes a JSON artifact `data/data_source_flag.json` with the
structure:

    {"source": "real"}        # when a real dataset is present
    {"source": "synthetic"}   # when only a synthetic dataset is present

The presence of a real dataset is inferred from the existence and non‑zero
size of `data/raw/dataset.csv`.  If that file is missing or empty, the
script looks for `data/raw/synthetic_dataset.csv`.  If neither file is
found, a `FileNotFoundError` is raised so that downstream tasks can fail
fast and surface the problem.

The script is intended to be run as a standalone module:

    python code/ingestion/flag_source.py

It writes the flag file under the project root's `data/` directory.
"""

import json
from pathlib import Path

from utils.config import get_project_root


def _determine_source() -> str:
    """
    Determine the origin of the dataset.

    Returns
    -------
    str
        Either ``"real"`` or ``"synthetic"``.
    """
    raw_dir: Path = get_project_root() / "data" / "raw"

    real_path = raw_dir / "dataset.csv"
    synthetic_path = raw_dir / "synthetic_dataset.csv"

    # Prefer the explicit real dataset file.
    if real_path.is_file() and real_path.stat().st_size > 0:
        return "real"

    # Fall back to the synthetic dataset file.
    if synthetic_path.is_file() and synthetic_path.stat().st_size > 0:
        return "synthetic"

    # As a last‑resort heuristic, inspect any CSV present.
    csv_files = list(raw_dir.glob("*.csv"))
    if len(csv_files) == 1:
        # If the only CSV is not the recognised real name, treat as synthetic.
        return "synthetic"

    raise FileNotFoundError(
        f"Unable to determine dataset source in '{raw_dir}'. "
        "Expected 'dataset.csv' (real) or 'synthetic_dataset.csv' (synthetic)."
    )


def _write_flag(source: str) -> None:
    """
    Write the source flag JSON artifact.

    Parameters
    ----------
    source : str
        The source identifier, ``"real"`` or ``"synthetic"``.
    """
    flag_path: Path = get_project_root() / "data" / "data_source_flag.json"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    with flag_path.open("w", encoding="utf-8") as f:
        json.dump({"source": source}, f, indent=2)
    # Ensure the file is flushed to disk.
    f.flush()


def main() -> None:
    """
    Entry point for the script.
    """
    source = _determine_source()
    _write_flag(source)
    print(f"Data source flag written to 'data/data_source_flag.json': {source}")


if __name__ == "__main__":
    main()