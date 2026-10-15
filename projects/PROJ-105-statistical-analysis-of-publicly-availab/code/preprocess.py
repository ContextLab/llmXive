"""
Preprocess script for Task T002.

This script extracts the BTS data archive (ZIP or CSV), streams the CSV
in chunks, computes the total delay, filters records, and writes the
cleaned dataset to ``data/processed/cleaned_delays.csv`` with the
required columns:

  - flight_id
  - total_delay_minutes
  - carrier
  - origin
  - destination
  - is_anomaly
  - is_data_error
  - is_zero

It re‑uses the robust implementation from ``code/preprocessing.py`` to
avoid code duplication and to keep the preprocessing logic in a single
place.
"""

import argparse
from pathlib import Path

# Re‑use the core preprocessing function defined in the library module.
from preprocessing import preprocess_flight_delays

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Task T002: Extract BTS ZIP/CSV, clean data, and write the cleaned CSV."
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the raw BTS CSV file or the ZIP archive containing it."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(
            Path("data")
            / "processed"
            / "cleaned_delays.csv"
        ),
        help="Path where the cleaned CSV will be written."
    )

    args = parser.parse_args()

    # Perform preprocessing
    cleaned_df = preprocess_flight_delays(args.input_path)

    # Ensure the output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the cleaned dataset
    cleaned_df.to_csv(output_path, index=False)
    print(f"Cleaned data written to {output_path}")

if __name__ == "__main__":
    main()
