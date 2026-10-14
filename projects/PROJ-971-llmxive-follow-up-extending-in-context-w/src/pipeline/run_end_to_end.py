"""
Minimal end‑to‑end driver for the Auto‑ICWM pipeline.

This placeholder implementation creates:
- 50 dummy ``.npz`` files under ``data/raw/`` (empty archives)
- An empty ``descriptors_subset.csv`` with the required column headers

Later tasks will replace the dummy generation and descriptor extraction
with real implementations.
"""
import argparse
import numpy as np
from pathlib import Path
import pandas as pd

def create_dummy_clips(num_clips: int, out_dir: Path) -> None:
    """Create ``num_clips`` empty ``.npz`` files as placeholders."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(num_clips):
        clip_path = out_dir / f"clip_{i:04d}.npz"
        # Store empty arrays with the expected keys so downstream code can load them.
        np.savez(clip_path, states=np.array([]), actions=np.array([]), observations=np.array([]))

def write_placeholder_descriptors(csv_path: Path) -> None:
    """Write a CSV with the required descriptor columns but no rows."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(columns=[
        "clip_id",
        "variance",
        "autocorr_lag1",
        "spectral_density"
    ])
    df.to_csv(csv_path, index=False)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run minimal Auto‑ICWM pipeline.")
    parser.add_argument(
        "--subset",
        type=int,
        default=50,
        help="Number of interaction clips to generate and process."
    )
    args = parser.parse_args()

    raw_dir = Path("data/raw")
    descriptors_path = Path("data/descriptors_subset.csv")

    print(f"Generating {args.subset} dummy clips in {raw_dir} …")
    create_dummy_clips(args.subset, raw_dir)

    print(f"Writing placeholder descriptor CSV to {descriptors_path} …")
    write_placeholder_descriptors(descriptors_path)

    print("Minimal pipeline completed. Summary:")
    print(f"  - Clips created: {args.subset}")
    print(f"  - Descriptor file: {descriptors_path}")

if __name__ == "__main__":
    main()
