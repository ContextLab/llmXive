"""
download_atlas.py
-----------------
Fetches the Schaefer 400‑parcel atlas using Nilearn, writes a CSV with
ROI coordinates and network labels, and records a SHA‑256 checksum.
"""

import hashlib
from pathlib import Path
import pandas as pd
from nilearn import datasets

ATLAS_ROI_COUNT = 400
ATLAS_OUTPUT_PATH = Path('data/atlas/schaefer_400.csv')
CHECKSUM_FILE = Path('data/checksums.txt')


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with file_path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def main() -> None:
    """
    Fetch the Schaefer 400‑parcel atlas, write a CSV with columns:
    ``roi_id, x, y, z, network`` and store a checksum.
    """
    # Ensure the target directory exists
    ATLAS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Fetch the atlas (this returns a dict with 'labels' pointing to a CSV)
    atlas = datasets.fetch_atlas_schaefer_2018(n_rois=ATLAS_ROI_COUNT, yeo_networks=7, resolution_mm=1,
                                              verbose=0)

    # Load the labels CSV supplied by Nilearn
    labels_path = Path(atlas['labels'])
    labels_df = pd.read_csv(labels_path)

    # Expected columns in Nilearn's labels file:
    #   ['index', 'label', 'center_x', 'center_y', 'center_z', 'network']
    # We'll rename/reorder to match the required specification.
    processed = labels_df.rename(columns={
        'index': 'roi_id',
        'center_x': 'x',
        'center_y': 'y',
        'center_z': 'z'
    })[['roi_id', 'x', 'y', 'z', 'network']]

    # Write the CSV
    processed.to_csv(ATLAS_OUTPUT_PATH, index=False)

    # Compute checksum and write to checksums.txt
    checksum = _compute_sha256(ATLAS_OUTPUT_PATH)
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CHECKSUM_FILE.open('w') as f:
        f.write(f"schaefer_400.csv {checksum}\\n")

    print(f"Atlas written to {ATLAS_OUTPUT_PATH}")
    print(f"Checksum recorded in {CHECKSUM_FILE}")


if __name__ == '__main__':
    main()
