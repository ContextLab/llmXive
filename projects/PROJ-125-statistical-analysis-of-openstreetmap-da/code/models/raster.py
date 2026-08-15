"""
Raster data models for covariates and temperature data.
"""
from typing import Optional, Dict, Any, List
import json
from pathlib import Path
import numpy as np
from .base import BaseModel
from config import get_path


class RasterCovariate(BaseModel):
    """
    Represents a raster covariate (e.g., NDVI, building density, road density).
    """

    def __init__(
        self,
        name: str,
        path: Path,
        description: str = "",
        crs: str = "EPSG:3857",
        resolution: float = 30.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.path = Path(path)
        self.description = description
        self.crs = crs
        self.resolution = resolution
        self.metadata = metadata or {}

        # Validate path exists
        if not self.path.exists():
            raise FileNotFoundError(f"Covariate file not found: {self.path}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "crs": self.crs,
            "resolution": self.resolution,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RasterCovariate":
        return cls(
            name=data["name"],
            path=Path(data["path"]),
            description=data.get("description", ""),
            crs=data.get("crs", "EPSG:3857"),
            resolution=data.get("resolution", 30.0),
            metadata=data.get("metadata", {}),
        )

    def validate(self) -> bool:
        """
        Validate the RasterCovariate instance.
        Checks: path exists, name is valid, resolution is positive.
        """
        if not self.name:
            raise ValueError("Raster name cannot be empty")

        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

        if self.resolution <= 0:
            raise ValueError("Resolution must be positive")

        return True


class TemperatureRaster(BaseModel):
    """
    Represents a temperature raster (LST) derived from satellite imagery.
    """

    def __init__(
        self,
        path: Path,
        crs: str = "EPSG:3857",
        resolution: float = 30.0,
        source_dataset: str = "",
        acquisition_date: Optional[str] = None,
        cloud_cover: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.path = Path(path)
        self.crs = crs
        self.resolution = resolution
        self.source_dataset = source_dataset
        self.acquisition_date = acquisition_date
        self.cloud_cover = cloud_cover
        self.metadata = metadata or {}

        if not self.path.exists():
            raise FileNotFoundError(f"Temperature raster file not found: {self.path}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "crs": self.crs,
            "resolution": self.resolution,
            "source_dataset": self.source_dataset,
            "acquisition_date": self.acquisition_date,
            "cloud_cover": self.cloud_cover,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemperatureRaster":
        return cls(
            path=Path(data["path"]),
            crs=data.get("crs", "EPSG:3857"),
            resolution=data.get("resolution", 30.0),
            source_dataset=data.get("source_dataset", ""),
            acquisition_date=data.get("acquisition_date"),
            cloud_cover=data.get("cloud_cover"),
            metadata=data.get("metadata", {}),
        )

    def validate(self) -> bool:
        """
        Validate the TemperatureRaster instance.
        Checks: path exists, resolution is positive, cloud cover (if present) is valid.
        """
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

        if self.resolution <= 0:
            raise ValueError("Resolution must be positive")

        if self.cloud_cover is not None and not (0 <= self.cloud_cover <= 100):
            raise ValueError("Cloud cover must be between 0 and 100")

        return True
