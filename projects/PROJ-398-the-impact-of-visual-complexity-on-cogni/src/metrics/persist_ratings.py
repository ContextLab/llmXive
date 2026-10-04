import csv
from pathlib import Path
from typing import Iterable, Mapping, Union

__all__ = ["persist_human_ratings"]


def persist_human_ratings(
    ratings: Iterable[Mapping[str, Union[str, int, float]]],
    csv_path: Path = Path("data/measurements/human_ratings.csv"),
) -> None:
    """
    Persist a collection of human rating records to a CSV file.

    Each rating mapping must contain the keys:
        - ``image_id`` (str)
        - ``participant_id`` (str or int)
        - ``complexity_score`` (float or int)

    The CSV is written with a header row and will be overwritten if it already
    exists. The parent directory is created if it does not already exist.

    Parameters
    ----------
    ratings:
        An iterable of mappings (e.g., list of dicts) representing the rating
        records.
    csv_path:
        Destination path for the CSV file. Defaults to
        ``data/measurements/human_ratings.csv`` relative to the project root.
    """
    # Ensure the output directory exists
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["image_id", "participant_id", "complexity_score"]

    with csv_path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rating in ratings:
            # Minimal validation – let KeyError surface if required keys missing
            writer.writerow(
                {
                    "image_id": rating["image_id"],
                    "participant_id": rating["participant_id"],
                    "complexity_score": rating["complexity_score"],
                }
            )
