"""
Flag source script for data ingestion.

This script determines whether the dataset in ``data/raw/dataset.csv`` was
obtained from a real source (as indicated by a ``Dataset URL:`` line in
``plan.md``) or generated synthetically. It writes the result to
``data/data_source_flag.json`` with the structure ``{ "source": "<type>" }``.
"""

import json
from pathlib import Path
from utils.config import get_project_root
from utils.logging import get_logger, log_info, log_error

logger = get_logger()


def _determine_source(root: Path) -> str:
    """
    Determine the data source type.

    Parameters
    ----------
    root : Path
        Project root directory.

    Returns
    -------
    str
        ``"real"`` if a real dataset was fetched, otherwise ``"synthetic"``.
    """
    raw_dir = root / "data" / "raw"
    dataset_path = raw_dir / "dataset.csv"
    plan_path = root / "plan.md"

    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset file not found at {dataset_path}")

    # If ``plan.md`` contains a non‑empty ``Dataset URL:`` line we treat the
    # dataset as real.  Absence of the line (or an empty URL) means the
    # dataset was created synthetically.
    if plan_path.is_file():
        for line in plan_path.read_text().splitlines():
            if line.startswith("Dataset URL:"):
                url = line.split(":", 1)[1].strip()
                if url:
                    return "real"
    return "synthetic"


def main() -> None:
    """
    Entry point: write ``data/data_source_flag.json`` with the detected source.
    """
    try:
        root = get_project_root()
        source = _determine_source(root)

        flag_path = root / "data" / "data_source_flag.json"
        flag_path.parent.mkdir(parents=True, exist_ok=True)

        with flag_path.open("w", encoding="utf-8") as f:
            json.dump({"source": source}, f, indent=2)

        log_info(logger, f"Data source flag written: {source}")
    except Exception as exc:  # pragma: no cover – any error is logged and re‑raised
        log_error(logger, f"Failed to set data source flag: {exc}")
        raise


if __name__ == "__main__":
    main()
