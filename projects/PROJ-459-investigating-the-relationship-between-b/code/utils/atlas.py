"""
Atlas loading and mapping utilities.
Handles Schaefer‑400 atlas and Yeo network parcellation.
Provides functions to load the atlas image and label file,
map ROI identifiers to Yeo network IDs, and retrieve a ROI‑to‑network
dictionary for downstream analysis.
"""

from pathlib import Path
from typing import Dict, List, Tuple

import nibabel as nib
import numpy as np

# Default paths – can be overridden in tests via monkey‑patching
ATLAS_PATH = Path("data/raw/schaefer_atlas.nii.gz")
LABELS_PATH = Path("data/raw/schaefer_labels.txt")


def _name_to_yeo_id(name: str) -> int:
    """
    Convert a Yeo network name to its numeric ID.

    The mapping follows the project‑specific requirement:
        DMN (Default Mode Network) -> 7
        Auditory                -> 4
        Salience                -> 2

    For the standard seven networks the IDs are:
        1: Visual
        2: SomatoMotor
        3: Dorsal Attention
        4: Ventral Attention (used here for Auditory)
        5: Limbic
        6: Frontoparietal
        7: Default Mode

    The function is case‑insensitive and tolerant of common
    naming variations (underscores, hyphens, etc.).

    Raises:
        ValueError: If the name cannot be resolved to an ID.
    """
    # Normalise the name
    norm = name.strip().lower().replace("_", "").replace("-", "")

    mapping = {
        "visual": 1,
        "somatomotor": 2,
        "dorsalattention": 3,
        "ventralattention": 4,   # Auditory as per task spec
        "auditory": 4,           # explicit alias
        "salience": 2,           # explicit alias for Salience
        "limbic": 5,
        "frontoparietal": 6,
        "defaultmode": 7,
        "defaultmodenetwork": 7,
        "defaultmodenetwork": 7,
    }

    if norm in mapping:
        return mapping[norm]
    raise ValueError(f"Unrecognised Yeo network name: '{name}'")


def load_atlas() -> Tuple[np.ndarray, Dict[int, str]]:
    """
    Load the Schaefer‑400 atlas image and its label file.

    Returns:
        label_map (np.ndarray): 3‑D array where each voxel contains the ROI label (int).
        network_dict (Dict[int, str]): Mapping from ROI label (int) to the network name (str).

    Raises:
        RuntimeError: If either the image or the label file cannot be read.
    """
    # Load the NIfTI image
    try:
        img = nib.load(ATLAS_PATH)
        label_map = img.get_fdata().astype(int)
    except Exception as exc:
        raise RuntimeError(f"Failed to load atlas image from {ATLAS_PATH!s}: {exc}") from exc

    # Load the label file – expected format: "<id> <NetworkName>"
    network_dict: Dict[int, str] = {}
    try:
        with open(LABELS_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    continue
                roi_id_str, net_name = parts
                roi_id = int(roi_id_str)
                network_dict[roi_id] = net_name
    except Exception as exc:
        raise RuntimeError(f"Failed to load atlas labels from {LABELS_PATH!s}: {exc}") from exc

    return label_map, network_dict


def map_to_yeo(roi_ids: List[int], network_dict: Dict[int, str]) -> List[int]:
    """
    Map a list of ROI identifiers to their corresponding Yeo network IDs.

    For each ROI identifier the function looks up the network name using
    ``network_dict`` and then translates that name to a Yeo ID via
    ``_name_to_yeo_id``.  If an ROI identifier is not present in
    ``network_dict`` a ``ValueError`` is raised.

    Args:
        roi_ids: List of ROI identifiers (as integers) to be mapped.
        network_dict: Mapping from ROI identifier to network name.

    Returns:
        List[int]: Yeo network IDs corresponding to the input ROI IDs.

    Raises:
        ValueError: If any ROI identifier is missing from ``network_dict``.
    """
    yeo_ids: List[int] = []
    for rid in roi_ids:
        if rid not in network_dict:
            raise ValueError(f"ROI identifier {rid} not found in network dictionary.")
        net_name = network_dict[rid]
        try:
            yeo_id = _name_to_yeo_id(net_name)
        except ValueError:
            # If the name is not one of the custom‑mapped ones,
            # fall back to the original integer identifier.
            yeo_id = rid
        yeo_ids.append(yeo_id)
    return yeo_ids


def get_roi_networks() -> Dict[int, str]:
    """
    Return a dictionary mapping each ROI label to its Yeo network name.

    This helper loads the atlas and builds a simple ``{roi_id: network_name}``
    mapping that can be used by downstream modules (e.g., metric calculation).

    Returns:
        Dict[int, str]: Mapping from ROI label to network name.
    """
    label_map, network_dict = load_atlas()
    # Extract the unique ROI identifiers present in the volume
    unique_rois = np.unique(label_map)
    roi_to_network: Dict[int, str] = {}
    for rid in unique_rois:
        # ``network_dict`` may not contain every possible label; skip missing ones
        if rid in network_dict:
            roi_to_network[int(rid)] = network_dict[int(rid)]
    return roi_to_network

# The module's public interface
__all__ = [
    "load_atlas",
    "map_to_yeo",
    "_name_to_yeo_id",
    "get_roi_networks",
    "ATLAS_PATH",
    "LABELS_PATH",
]