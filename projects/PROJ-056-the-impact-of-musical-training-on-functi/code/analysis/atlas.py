"""
Atlas utilities for the functional connectivity pipeline.

The Schaefer‑200 atlas CSV is expected to have the following columns:
    - roi_id: integer identifier of the ROI (starting at 0 or 1)
    - x, y, z: voxel coordinates (in voxel space) of the ROI centre
    - network: name of the functional network the ROI belongs to
The file may contain additional columns which are ignored.

The helper functions below load the CSV into a pandas DataFrame and
provide convenient look‑ups for the three target networks:
    * auditory
    * motor
    * executive
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict

__all__ = [
    "load_atlas",
    "get_network_roi_indices",
    "TARGET_NETWORKS",
]


# The three networks required by the analysis.  Names must match exactly
# the values used in the bundled atlas CSV.
TARGET_NETWORKS = ["auditory", "motor", "executive"]


def load_atlas(atlas_path: Path) -> pd.DataFrame:
    """
    Load the Schaefer‑200 atlas CSV.

    Parameters
    ----------
    atlas_path: Path
        Path to the CSV file containing the atlas definition.

    Returns
    -------
    pandas.DataFrame
        DataFrame with at least the columns ``roi_id``, ``x``, ``y``, ``z``,
        and ``network``.  The ``roi_id`` column is converted to ``int`` and
        used as a zero‑based index.
    """
    if not atlas_path.is_file():
        raise FileNotFoundError(f"Atlas file not found at {atlas_path}")

    df = pd.read_csv(atlas_path)

    required = {"roi_id", "x", "y", "z", "network"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Atlas CSV is missing required columns: {missing}")

    # Ensure roi_id is integer and zero‑based
    df["roi_id"] = df["roi_id"].astype(int)
    if df["roi_id"].min() != 0:
        # Convert to zero‑based indexing if necessary
        df["roi_id"] = df["roi_id"] - df["roi_id"].min()

    return df


def get_network_roi_indices(atlas_df: pd.DataFrame, network_name: str) -> List[int]:
    """
    Return a list of ROI indices belonging to ``network_name``.

    Parameters
    ----------
    atlas_df: pd.DataFrame
        Atlas DataFrame as returned by ``load_atlas``.
    network_name: str
        Name of the target network (must be one of ``TARGET_NETWORKS``).

    Returns
    -------
    List[int]
        Zero‑based ROI indices that belong to the requested network.
    """
    if network_name not in TARGET_NETWORKS:
        raise ValueError(f"Network '{network_name}' is not a recognized target. "
                         f"Valid targets are: {TARGET_NETWORKS}")

    indices = atlas_df.loc[atlas_df["network"] == network_name, "roi_id"].tolist()
    if not indices:
        raise ValueError(f"No ROIs found for network '{network_name}' in the atlas.")
    return indices