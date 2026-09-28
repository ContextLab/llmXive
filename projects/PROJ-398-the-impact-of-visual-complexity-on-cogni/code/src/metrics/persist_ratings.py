"""
src.metrics.persist_ratings
---------------------------

Utility for persisting human complexity ratings collected during the pilot
study.

The function ``persist_human_ratings`` accepts an iterable of rating records
(each record being a mapping with keys ``image_id``, ``participant_id`` and
``complexity_score``) and writes them to a CSV file that conforms to the
required schema:

- ``image_id``          : identifier of the stimulus image (string)
- ``participant_id``   : identifier of the participant (string or int)
- ``complexity_score`` : numeric rating (float or int)

By default the CSV is written to ``data/measurements/human_ratings.csv``.
Callers may override the destination via the ``output_path`` argument – this
is useful for unit‑tests that write to a temporary location.

The implementation ensures that the target directory exists and that the
output file contains **only** the three required columns in the correct
order.  If the CSV already exists, new rows are appended while preserving
the header.
"""

import csv
import os
from pathlib import Path
from typing import Iterable, Mapping, Union

# Type alias for a single rating record
RatingRecord = Mapping[
    str, Union[str, int, float]
]  # expects keys: image_id, participant_id, complexity_score


def _ensure_parent_dir(path: Path) -> None:
    """Make sure the parent directory of *path* exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _validate_record(record: RatingRecord) -> None:
    """Validate that a rating record contains the required keys."""
    required_keys = {"image_id", "participant_id", "complexity_score"}
    missing = required_keys - set(record.keys())
    if missing:
        raise ValueError(f"Rating record is missing required keys: {missing}")


def persist_human_ratings(
    ratings: Iterable[RatingRecord],
    output_path: Union[str, Path] = None,
) -> Path:
    """
    Persist an iterable of rating records to a CSV file.

    Parameters
    ----------
    ratings:
        An iterable (list, generator, etc.) of mappings.  Each mapping must
        contain the keys ``image_id``, ``participant_id`` and
        ``complexity_score``.
    output_path:
        Destination CSV file.  If ``None`` the default location
        ``data/measurements/human_ratings.csv`` (relative to the project root)
        is used.

    Returns
    -------
    pathlib.Path
        The absolute path of the CSV file that was written.
    """
    if output_path is None:
        output_path = Path("data") / "measurements" / "human_ratings.csv"
    else:
        output_path = Path(output_path)

    _ensure_parent_dir(output_path)

    # Determine whether we need to write a header (file does not exist or is empty)
    write_header = not output_path.is_file() or output_path.stat().st_size == 0

    # Define the column order required by the specification
    fieldnames = ["image_id", "participant_id", "complexity_score"]

    with output_path.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        for rec in ratings:
            _validate_record(rec)
            # Cast values to appropriate types (strings for ids, float for score)
            row = {
                "image_id": str(rec["image_id"]),
                "participant_id": str(rec["participant_id"]),
                "complexity_score": float(rec["complexity_score"]),
            }
            writer.writerow(row)

    return output_path.resolve()
