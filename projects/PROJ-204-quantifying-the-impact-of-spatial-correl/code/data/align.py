import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
from scipy.ndimage import zoom
from scipy.interpolate import RectBivariateSpline

__all__ = [
    "calculate_target_grid_shape",
    "resample_map",
    "align_maps",
    "validate_alignment",
    "create_aligned_dataset",
]

def calculate_target_grid_shape(
    reference_shape: Tuple[int, int],
    target_shape: Tuple[int, int],
    scale_factor: Optional[float] = None,
) -> Tuple[int, int]:
    """
    Determine the target grid shape for resampling.

    If ``scale_factor`` is provided, the target shape is multiplied by that
    factor; otherwise the reference shape is used.

    Parameters
    ----------
    reference_shape: Tuple[int, int]
        Shape of the reference map (height, width).
    target_shape: Tuple[int, int]
        Original shape of the map to be resampled.
    scale_factor: float, optional
        Scaling factor.

    Returns
    -------
    Tuple[int, int]
        Desired shape after resampling.
    """
    if scale_factor is not None:
        return (
            int(reference_shape[0] * scale_factor),
            int(reference_shape[1] * scale_factor),
        )
    return reference_shape

def resample_map(
    map_array: np.ndarray,
    target_shape: Tuple[int, int],
    order: int = 1,
) -> np.ndarray:
    """
    Resample an image to a new shape using spline interpolation.

    Parameters
    ----------
    map_array: np.ndarray
        Input image.
    target_shape: Tuple[int, int]
        Desired output shape (height, width).
    order: int, optional
        Interpolation order (default 1 – linear).

    Returns
    -------
    np.ndarray
        Resampled image.
    """
    zoom_factors = (
        target_shape[0] / map_array.shape[0],
        target_shape[1] / map_array.shape[1],
    )
    logging.debug("Resampling with factors %s", zoom_factors)
    return zoom(map_array, zoom_factors, order=order)

def align_maps(
    maps: Dict[str, np.ndarray],
    reference_key: str = "Pb",
) -> Dict[str, np.ndarray]:
    """
    Align a dictionary of elemental maps to the reference map.

    Parameters
    ----------
    maps: Dict[str, np.ndarray]
        Mapping from element name to its image array.
    reference_key: str, optional
        Key of the map to use as spatial reference.

    Returns
    -------
    Dict[str, np.ndarray]
        Aligned maps with identical shapes.
    """
    reference = maps[reference_key]
    target_shape = reference.shape
    aligned = {}
    for key, arr in maps.items():
        if arr.shape != target_shape:
            aligned[key] = resample_map(arr, target_shape)
        else:
            aligned[key] = arr
    return aligned

def validate_alignment(
    aligned_maps: Dict[str, np.ndarray],
    tolerance: float = 1e-3,
) -> bool:
    """
    Verify that all aligned maps share the same shape.

    Parameters
    ----------
    aligned_maps: Dict[str, np.ndarray]
        Aligned maps.
    tolerance: float, optional
        Not used for shape check; kept for API compatibility.

    Returns
    -------
    bool
        ``True`` if all shapes match, ``False`` otherwise.
    """
    shapes = {arr.shape for arr in aligned_maps.values()}
    return len(shapes) == 1

def create_aligned_dataset(
    raw_dir: Path,
    element_files: List[str],
    reference_key: str = "Pb",
) -> Dict[str, np.ndarray]:
    """
    Load elemental map files from ``raw_dir`` and return an aligned dataset.

    Parameters
    ----------
    raw_dir: Path
        Directory containing raw ``.npy`` map files.
    element_files: List[str]
        Filenames (relative to ``raw_dir``) for each element.
    reference_key: str, optional
        Which element to treat as spatial reference.

    Returns
    -------
    Dict[str, np.ndarray]
        Mapping from element name (derived from filename) to aligned array.
    """
    maps = {}
    for fname in element_files:
        path = raw_dir / fname
        element = Path(fname).stem.split("_")[0]  # e.g. "Pb_map.npy" -> "Pb"
        maps[element] = np.load(path)
    aligned = align_maps(maps, reference_key)
    if not validate_alignment(aligned):
        raise ValueError("Alignment validation failed")
    return aligned
