"""Create a reproducible 10 k random subset of the QM9 dataset.

The script reads the raw parquet produced by ``download_qm9.py``,
samples 10 000 molecules using a fixed random seed, and writes the
subset to ``data/processed/molecules_10k.parquet``.
"""
import os
import argparse
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a 10k random subset of the QM9 dataset."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=os.path.join("data", "raw"),
        help="Directory containing the raw QM9 parquet file.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join("data", "processed"),
        help="Directory where the subset parquet will be written.",
    )
    args = parser.parse_args()

    raw_path = os.path.join(args.raw_dir, "qm9.parquet")
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw QM9 parquet not found at {raw_path}")

    os.makedirs(args.output_dir, exist_ok=True)
    subset_path = os.path.join(args.output_dir, "molecules_10k.parquet")

    print(f"Loading raw data from {raw_path} ...")
    df = pd.read_parquet(raw_path)

    print("Sampling 10,000 molecules with seed", args.seed)
    subset_df = df.sample(n=10_000, random_state=args.seed)

    print(f"Writing subset to {subset_path} ...")
    subset_df.to_parquet(subset_path, index=False)
    print("Subset creation complete.")


if __name__ == "__main__":
    main()
