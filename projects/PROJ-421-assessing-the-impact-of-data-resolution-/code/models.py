"""
Base data models for the resolution impact study.

This module defines core data structures for representing raster data at
different resolutions and binary indicator maps derived from land cover data.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class ResolutionRaster:
    """
    Represents a raster dataset at a specific spatial resolution.

    Attributes:
        resolution: The spatial resolution in meters (e.g., 30, 60, 120).
        path: Absolute or relative path to the raster file on disk.
        values: A 2D numpy array containing the raster pixel values.
    """
    resolution: int
    path: str
    values: np.ndarray

    def __post_init__(self):
        if not isinstance(self.values, np.ndarray):
            raise TypeError("values must be a numpy array")
        if self.values.ndim != 2:
            raise ValueError("values must be a 2D array")
        if self.resolution <= 0:
            raise ValueError("resolution must be a positive integer")

    @property
    def shape(self) -> tuple:
        """Returns the shape (rows, cols) of the raster."""
        return self.values.shape

    @property
    def unique_values(self) -> np.ndarray:
        """Returns the unique values present in the raster."""
        return np.unique(self.values)


@dataclass
class BinaryIndicatorMap:
    """
    Represents a binary transformation of a land cover raster.

    This map converts categorical land cover classes into a binary
    indicator (0 or 1) based on a specific class of interest (e.g., Forest).

    Attributes:
        class_id: The original land cover class ID being tracked (e.g., 41 for deciduous forest).
        binary_values: A 2D numpy array of 0s and 1s indicating presence/absence.
        source_path: Optional path to the source raster this map was derived from.
    """
    class_id: int
    binary_values: np.ndarray
    source_path: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.binary_values, np.ndarray):
            raise TypeError("binary_values must be a numpy array")
        if self.binary_values.ndim != 2:
            raise ValueError("binary_values must be a 2D array")
        if not np.array_equal(np.unique(self.binary_values), [0, 1]) and not np.array_equal(np.unique(self.binary_values), [0]):
            # Allow all zeros case, but generally expect 0 and 1
            if not np.all(np.isin(self.binary_values, [0, 1])):
                raise ValueError("binary_values must contain only 0s and 1s")
        if self.class_id < 0:
            raise ValueError("class_id must be non-negative")

    @property
    def shape(self) -> tuple:
        """Returns the shape (rows, cols) of the binary map."""
        return self.binary_values.shape

    @property
    def prevalence(self) -> float:
        """Returns the proportion of cells where the indicator is 1."""
        return float(np.mean(self.binary_values))