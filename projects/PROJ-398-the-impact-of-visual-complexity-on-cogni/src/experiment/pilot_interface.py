import csv
import os
from pathlib import Path
from typing import List, Dict, Union

from src.metrics.persist_ratings import persist_human_ratings

__all__ = [
    "ensure_output_dir",
    "list_stimuli_images",
    "load_existing_ratings",
    "append_rating",
    "main",
]


def ensure_output_dir() -> Path:
    """
    Ensure that the directory for storing human rating CSVs exists.

    Returns
    -------
    Path
        The path to the ``data/measurements`` directory.
    """
    measurements_dir = Path("data/measurements")
    measurements_dir.mkdir(parents=True, exist_ok=True)
    return measurements_dir


def list_stimuli_images() -> List[Path]:
    """
    List image files available for the pilot study.

    The function looks for image files (PNG/JPG/JPEG) in the stimuli directory.
    The directory can be overridden by the ``STIMULI_DIR`` environment variable;
    otherwise it defaults to ``data/stimuli``.

    Returns
    -------
    List[Path]
        Sorted list of image file paths.
    """
    stimuli_dir = Path(os.getenv("STIMULI_DIR", "data/stimuli"))
    if not stimuli_dir.is_dir():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")

    image_extensions = {".png", ".jpg", ".jpeg"}
    images = [
        p
        for p in stimuli_dir.iterdir()
        if p.is_file() and p.suffix.lower() in image_extensions
    ]
    images.sort()
    return images


def load_existing_ratings() -> List[Dict[str, Union[str, int, float]]]:
    """
    Load already‑persisted human ratings from the CSV file.

    Returns
    -------
    List[Dict[str, Union[str, int, float]]]
        List of rating records; empty list if the CSV does not exist.
    """
    csv_path = Path("data/measurements/human_ratings.csv")
    if not csv_path.is_file():
        return []

    ratings: List[Dict[str, Union[str, int, float]]] = []
    with csv_path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields to appropriate types
            rating = {
                "image_id": row["image_id"],
                "participant_id": row["participant_id"],
                "complexity_score": float(row["complexity_score"]),
            }
            ratings.append(rating)
    return ratings


def append_rating(
    image_id: str,
    participant_id: Union[str, int],
    complexity_score: Union[int, float],
) -> None:
    """
    Append a single rating to the persisted CSV file.

    The function loads any existing ratings, adds the new record, and writes
    the full collection back to disk using :func:`persist_human_ratings`.

    Parameters
    ----------
    image_id:
        Identifier of the stimulus image.
    participant_id:
        Identifier of the participant providing the rating.
    complexity_score:
        The perceived visual complexity score (e.g., 1‑5 Likert).
    """
    # Load current ratings, add the new one, and persist.
    ratings = load_existing_ratings()
    new_rating = {
        "image_id": image_id,
        "participant_id": str(participant_id),
        "complexity_score": float(complexity_score),
    }
    ratings.append(new_rating)
    persist_human_ratings(ratings)


def main() -> None:
    """
    Minimal command‑line interface for manual testing.

    Usage example:
        python -m src.experiment.pilot_interface append <image_id> <participant_id> <score>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Pilot interface rating helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    append_parser = subparsers.add_parser("append", help="Append a rating")
    append_parser.add_argument("image_id", type=str)
    append_parser.add_argument("participant_id", type=str)
    append_parser.add_argument("complexity_score", type=float)

    args = parser.parse_args()

    if args.command == "append":
        ensure_output_dir()
        append_rating(args.image_id, args.participant_id, args.complexity_score)
        print(f"Appended rating for image {args.image_id}")

if __name__ == "__main__":
    main()