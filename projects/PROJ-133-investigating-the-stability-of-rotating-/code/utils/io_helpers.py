"""
File-based I/O helpers for .npy and .csv files.

Provides robust loading and saving functions for simulation data,
integrating with the project's seed management for reproducibility where applicable.
"""

import os
import numpy as np
import pandas as pd
from typing import Optional, Union, Dict, Any, List
from pathlib import Path

# Import seed manager to ensure reproducibility context if needed
from utils.seed_manager import get_global_seed


def save_array(
    data: np.ndarray,
    filepath: Union[str, Path],
    overwrite: bool = False
) -> None:
    """
    Save a NumPy array to a .npy file.

    Args:
        data: The array to save.
        filepath: Path to the output .npy file.
        overwrite: If False, raises an error if the file exists.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not overwrite:
        raise FileExistsError(f"File {filepath} already exists. Set overwrite=True to replace.")

    np.save(path, data)


def load_array(filepath: Union[str, Path]) -> np.ndarray:
    """
    Load a NumPy array from a .npy file.

    Args:
        filepath: Path to the input .npy file.

    Returns:
        The loaded NumPy array.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File {filepath} not found.")

    return np.load(path)


def save_dataframe(
    df: pd.DataFrame,
    filepath: Union[str, Path],
    overwrite: bool = False,
    index: bool = False
) -> None:
    """
    Save a Pandas DataFrame to a .csv file.

    Args:
        df: The DataFrame to save.
        filepath: Path to the output .csv file.
        overwrite: If False, raises an error if the file exists.
        index: Whether to write row indices.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not overwrite:
        raise FileExistsError(f"File {filepath} already exists. Set overwrite=True to replace.")

    df.to_csv(path, index=index)


def load_dataframe(
    filepath: Union[str, Path],
    **kwargs
) -> pd.DataFrame:
    """
    Load a DataFrame from a .csv file.

    Args:
        filepath: Path to the input .csv file.
        **kwargs: Additional arguments passed to pd.read_csv.

    Returns:
        The loaded DataFrame.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File {filepath} not found.")

    return pd.read_csv(path, **kwargs)


def save_simulation_snapshot(
    density: np.ndarray,
    phase: np.ndarray,
    filepath_prefix: Union[str, Path],
    time_step: float,
    overwrite: bool = False
) -> Dict[str, str]:
    """
    Save simulation state (density and phase) to separate .npy files.

    Args:
        density: Real-valued density array.
        phase: Real-valued phase array.
        filepath_prefix: Base path (without extension) for output files.
        time_step: The simulation time step to include in the filename.
        overwrite: Whether to overwrite existing files.

    Returns:
        A dictionary mapping 'density' and 'phase' to their saved file paths.
    """
    path_prefix = Path(filepath_prefix)
    path_prefix.parent.mkdir(parents=True, exist_ok=True)

    # Construct filenames with time step
    density_path = path_prefix.parent / f"{path_prefix.name}_t{time_step:.4f}_density.npy"
    phase_path = path_prefix.parent / f"{path_prefix.name}_t{time_step:.4f}_phase.npy"

    save_array(density, density_path, overwrite=overwrite)
    save_array(phase, phase_path, overwrite=overwrite)

    return {
        "density": str(density_path),
        "phase": str(phase_path)
    }


def load_simulation_snapshot(
    filepath_prefix: Union[str, Path],
    time_step: float
) -> Dict[str, np.ndarray]:
    """
    Load simulation state (density and phase) from .npy files.

    Args:
        filepath_prefix: Base path (without extension) used during saving.
        time_step: The simulation time step to match in the filename.

    Returns:
        A dictionary with keys 'density' and 'phase' containing the arrays.
    """
    path_prefix = Path(filepath_prefix)

    # Construct expected filenames
    density_path = path_prefix.parent / f"{path_prefix.name}_t{time_step:.4f}_density.npy"
    phase_path = path_prefix.parent / f"{path_prefix.name}_t{time_step:.4f}_phase.npy"

    return {
        "density": load_array(density_path),
        "phase": load_array(phase_path)
    }


def load_multiple_csvs(
    filepaths: List[Union[str, Path]],
    concat_key: str = "source_file"
) -> pd.DataFrame:
    """
    Load multiple CSV files and concatenate them into a single DataFrame.

    Args:
        filepaths: List of paths to CSV files.
        concat_key: Column name to add indicating the source file.

    Returns:
        A single concatenated DataFrame.
    """
    dfs = []
    for fp in filepaths:
        df = load_dataframe(fp)
        df[concat_key] = str(fp)
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)
