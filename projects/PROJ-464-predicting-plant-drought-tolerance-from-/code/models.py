from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, validator, ValidationError
import logging

logger = logging.getLogger(__name__)

# --- Data‑Model Classes (Pydantic) ---

class RootImage(BaseModel):
    """
    Represents a raw root image file from the NPPN dataset.

    Attributes
    ----------
    id: str
        Unique identifier for the image (e.g., hash or filename without extension).
    path: str
        Relative or absolute filesystem path to the image file.
    species: str
        Scientific name of the species the image belongs to.
    """
    id: str
    path: str
    species: str

    @validator('id', 'path', 'species')
    def must_be_nonempty(cls, v: str, field):
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"{field.name} must be a non‑empty string")
        return v

class RSAMetrics(BaseModel):
    """
    Quantitative root system architecture metrics derived from a RootImage.

    Attributes
    ----------
    species_id: str
        Species identifier (matches the ``species`` field in ``RootImage``).
    depth: float
        Maximum root depth (pixels or mm). Must be > 0.
    branching_density: float
        Number of branch points per unit length. Must be > 0.
    surface_area: float
        Projected root surface area. Must be > 0.
    """
    species_id: str
    depth: float
    branching_density: float
    surface_area: float

    @validator('species_id')
    def species_must_be_nonempty(cls, v: str):
        if not v.strip():
            raise ValueError("species_id must be a non‑empty string")
        return v

    @validator('depth', 'branching_density', 'surface_area')
    def must_be_positive(cls, v: float, field):
        if v <= 0:
            raise ValueError(f"{field.name} must be positive, got {v}")
        return v

class PhysioTrait(BaseModel):
    """
    Physiological traits obtained from the TRY database.

    Attributes
    ----------
    species: str
        Species scientific name (must match ``species_id`` in ``RSAMetrics``).
    conductance: float
        Stomatal conductance (mmol m⁻² s⁻¹). Must be non‑negative.
    photosynthesis: float
        Photosynthetic rate (µmol m⁻² s⁻¹). Must be non‑negative.
    survival_rate: Optional[float]
        Optional independent drought‑tolerance proxy (0‑1). If provided, must be between 0 and 1.
    """
    species: str
    conductance: float
    photosynthesis: float
    survival_rate: Optional[float] = None

    @validator('species')
    def species_must_be_nonempty(cls, v: str):
        if not v.strip():
            raise ValueError("species must be a non‑empty string")
        return v

    @validator('conductance', 'photosynthesis')
    def non_negative(cls, v: float, field):
        if v < 0:
            raise ValueError(f"{field.name} must be non‑negative, got {v}")
        return v

    @validator('survival_rate')
    def survival_rate_bounds(cls, v: Optional[float]):
        if v is None:
            return v
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"survival_rate must be between 0 and 1, got {v}")
        return v

# The module also provides a small helper for logging when run directly.
if __name__ == "__main__":
    import json
    example = {
        "RootImage": {"id": "img_001", "path": "data/raw/nppn_images/img1.png", "species": "Quercus robur"},
        "RSAMetrics": {"species_id": "Quercus robur", "depth": 120.5, "branching_density": 0.8, "surface_area": 350.2},
        "PhysioTrait": {"species": "Quercus robur", "conductance": 250.0, "photosynthesis": 15.2}
    }
    print(json.dumps(example, indent=2))
