from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = ["compute_clone_density_batch"]


def _calculate_clone_density(rows: list[list[str]]) -> float:
    """
    Very simple clone‑density estimator used for the MVP.

    The function treats the *second* column of each row (or the first column if
    there is only one) as the source code snippet.  It counts how many snippets
    appear more than once and divides that by the total number of snippets.
    """
    if not rows:
        return 0.0

    seen = set()
    duplicate = 0
    for row in rows:
        # The dataset we write in ``data_loader.download_and_save_sample`` stores
        # an ``id`` column followed by a ``content`` column.
        code = row[1] if len(row) > 1 else row[0]
        if code in seen:
            duplicate += 1
        else:
            seen.add(code)

    return duplicate / len(rows)


def compute_clone_density_batch(input_path: Optional[Path] = None) -> None:
    """
    Compute clone density for a batch of source files and write the result to
    ``data/processed/clone_metrics.csv``.

    The function is deliberately tolerant to how it is called:

    * ``compute_clone_density_batch()`` – uses the default path derived from
      the configuration.
    * ``compute_clone_density_batch(path)`` – positional argument.
    * ``compute_clone_density_batch(input_path=path)`` – keyword argument.
    * ``compute_clone_density_batch(input_path=None)`` – falls back to the
      default.

    Parameters
    ----------
    input_path: pathlib.Path | None
        Path to the CSV file containing the raw code samples.  If omitted,
        ``code.config.get_dataset_name`` is consulted to construct a default
        location of the form ``data/raw/<dataset>-sample.csv``.
    """
    from code.config import get_dataset_name

    if input_path is None:
        dataset_name = get_dataset_name().replace("/", "-")
        input_path = Path("data/raw") / f"{dataset_name}-sample.csv"

    if not Path(input_path).exists():
        logger.error("Input file for clone density does not exist: %s", input_path)
        raise FileNotFoundError(input_path)

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    density = _calculate_clone_density(rows)

    out_path = Path("data/processed/clone_metrics.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["clone_density"])
        writer.writerow([density])

    logger.info(
        "Clone‑density computation finished – density: %.6f written to %s",
        density,
        out_path,
    )
