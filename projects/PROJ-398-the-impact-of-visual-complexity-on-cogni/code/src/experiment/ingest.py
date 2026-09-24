import argparse
import sys
from pathlib import Path

import pandas as pd

# Define output location constants
OUTPUT_DIR = Path("data/measurements")
OUTPUT_FILE = OUTPUT_DIR / "human_ratings.csv"


def ensure_output_dir() -> None:
    """Create the measurements directory if it does not already exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map a loosely‑specified input CSV to the canonical schema required for
    ``human_ratings.csv``. The canonical schema is:

    - ``image_id``          – identifier of the stimulus image
    - ``participant_id``   – identifier of the participant
    - ``complexity_score``  – integer/float rating (1‑10)

    The function looks for common alternative column names and raises a
    clear ``ValueError`` if any required field cannot be resolved.
    """
    # Mapping from possible source column names to the canonical name
    column_map = {
        "image_id": "image_id",
        "image": "image_id",
        "stimulus_id": "image_id",
        "participant_id": "participant_id",
        "participant": "participant_id",
        "user_id": "participant_id",
        "complexity_score": "complexity_score",
        "rating": "complexity_score",
        "score": "complexity_score",
    }

    selected: dict[str, pd.Series] = {}
    for src_name, target_name in column_map.items():
        if src_name in df.columns:
            selected[target_name] = df[src_name]

    required = {"image_id", "participant_id", "complexity_score"}
    missing = required - set(selected.keys())
    if missing:
        raise ValueError(
            f"Input CSV is missing required columns (or recognizable aliases): {missing}"
        )

    # Preserve the order of the canonical columns
    ordered = {col: selected[col] for col in ["image_id", "participant_id", "complexity_score"]}
    return pd.DataFrame(ordered)


def ingest_csv(input_path: Path) -> None:
    """
    Read an external recruitment CSV export and write a clean
    ``human_ratings.csv`` file to ``data/measurements/``.
    """
    ensure_output_dir()
    df = pd.read_csv(input_path)
    out_df = _map_columns(df)
    out_df.to_csv(OUTPUT_FILE, index=False)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a recruitment CSV export and map it to the canonical "
            "human_ratings.csv format used by the pilot study."
        )
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to the external recruitment CSV export to ingest.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    ingest_csv(args.input_csv)


if __name__ == "__main__":
    # When executed as a script ``python ingest.py <path>``, forward the
    # arguments to ``main``.  This also allows the test suite to invoke
    # ``main`` directly after monkey‑patching ``sys.argv``.
    main()
