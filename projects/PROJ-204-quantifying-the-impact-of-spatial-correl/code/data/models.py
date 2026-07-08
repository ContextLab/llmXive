from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator
import numpy as np

__all__ = [
    "ElementalMap",
    "DevicePerformance",
    "SpatialMetric",
    "AnalysisResult",
    "create_sample_dataset",
    "create_sample_performance",
]

class ElementalMap(BaseModel):
    """
    Representation of a single elemental map.

    Attributes
    ----------
    sample_id: str
        Identifier of the sample.
    element: str
        Chemical element (e.g., ``'Pb'``).
    map_path: Path
        Path to the ``.npy`` file storing the map.
    """

    sample_id: str
    element: str
    map_path: Path

    @field_validator("map_path", mode="before")
    def ensure_path(cls, v):
        return Path(v)

    @model_validator(mode="after")
    def check_file_exists(cls, values):
        if not values.map_path.is_file():
            raise ValueError(f"Map file does not exist: {values.map_path}")
        return values

class DevicePerformance(BaseModel):
    """
    Performance metrics for a perovskite solar cell device.

    Attributes
    ----------
    sample_id: str
        Identifier linking to ``ElementalMap``.
    PCE: float
        Power conversion efficiency (percentage).
    J_sc: float
        Short‑circuit current density (mA·cm⁻²).
    V_oc: float
        Open‑circuit voltage (V).
    """

    sample_id: str
    PCE: float = Field(..., ge=0, le=100)
    J_sc: float = Field(..., ge=0)
    V_oc: float = Field(..., ge=0)

class SpatialMetric(BaseModel):
    """
    Spatial correlation metrics derived from elemental maps.

    Attributes
    ----------
    sample_id: str
    element: str
    correlation_length: Optional[float]
    model_type: Optional[str]
    AIC: Optional[float]
    low_freq_power: Optional[float]
    """

    sample_id: str
    element: str
    correlation_length: Optional[float] = None
    model_type: Optional[str] = None
    AIC: Optional[float] = None
    low_freq_power: Optional[float] = None

class AnalysisResult(BaseModel):
    """
    Container for the final analysis results for a sample.

    Attributes
    ----------
    sample_id: str
    correlation_coefficient: float
    p_value: float
    model: str
    """

    sample_id: str
    correlation_coefficient: float
    p_value: float
    model: str

def create_sample_dataset(
    num_samples: int = 10, elements: List[str] = ["Pb", "I", "MA"]
) -> List[ElementalMap]:
    """
    Generate a list of synthetic ``ElementalMap`` objects for testing.

    The function creates temporary ``.npy`` files with random data under a
    temporary directory and returns the corresponding model objects.

    Parameters
    ----------
    num_samples: int, optional
        Number of samples to generate (default 10).
    elements: List[str], optional
        Elements for which maps are created.

    Returns
    -------
    List[ElementalMap]
        List of populated ``ElementalMap`` instances.
    """
    import tempfile
    import os

    base_dir = Path(tempfile.mkdtemp())
    maps = []
    for i in range(num_samples):
        sample_id = f"sample_{i:03d}"
        for elem in elements:
            arr = np.random.rand(100, 100)
            fname = base_dir / f"{sample_id}_{elem}.npy"
            np.save(fname, arr)
            maps.append(
                ElementalMap(
                    sample_id=sample_id,
                    element=elem,
                    map_path=fname,
                )
            )
    return maps

def create_sample_performance(
    sample_ids: List[str],
) -> List[DevicePerformance]:
    """
    Generate synthetic performance records for a list of ``sample_ids``.

    Parameters
    ----------
    sample_ids: List[str]
        Sample identifiers.

    Returns
    -------
    List[DevicePerformance]
        Performance objects with random but plausible values.
    """
    performances = []
    for sid in sample_ids:
        performances.append(
            DevicePerformance(
                sample_id=sid,
                PCE=np.random.uniform(10, 20),
                J_sc=np.random.uniform(15, 25),
                V_oc=np.random.uniform(0.9, 1.2),
            )
        )
    return performances
