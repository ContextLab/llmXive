"""
Raster models for covariates and temperature data.
"""
from typing import Optional, Dict, Any, List
import json
from pathlib import Path
import numpy as np
from .base import BaseModel
from config import get_path
import logging

logger = logging.getLogger(__name__)


class RasterCovariate(BaseModel):
    """
    Represents a raster covariate layer (e.g., building density, NDVI).
    
    Attributes:
        name: Unique identifier for the covariate.
        file_path: Path to the source GeoTIFF.
        variable_type: 'continuous', 'categorical', or 'binary'.
        description: Human-readable description.
        metadata: Additional metadata (resampling method, source, etc.).
    """

    def __init__(
        self,
        name: str,
        file_path: str,
        variable_type: str = "continuous",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.file_path = str(file_path)
        self.variable_type = variable_type
        self.description = description
        self.metadata = metadata or {}

    def validate(self) -> bool:
        """
        Validate the RasterCovariate instance.
        
        Checks:
        1. Name is not empty.
        2. File path exists and is readable.
        3. Variable type is valid.
        """
        if not self.name:
            logger.error("Covariate name cannot be empty.")
            return False

        if not self.variable_type in ["continuous", "categorical", "binary"]:
            logger.error(f"Invalid variable_type: {self.variable_type}")
            return False

        path = Path(self.file_path)
        if not path.exists():
            logger.error(f"Covariate file not found: {self.file_path}")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the covariate to a dictionary.
        """
        return {
            "name": self.name,
            "file_path": self.file_path,
            "variable_type": self.variable_type,
            "description": self.description,
            "metadata": self.metadata,
        }

    def get_stats(self) -> Dict[str, float]:
        """
        Compute basic statistics (min, max, mean, std) if numpy/rasterio available.
        Returns dummy stats if file cannot be read.
        """
        try:
            import rasterio
            with rasterio.open(self.file_path) as src:
                data = src.read(1)
                valid_data = data[~np.isnan(data)]
                if len(valid_data) == 0:
                    return {"min": np.nan, "max": np.nan, "mean": np.nan, "std": np.nan}
                return {
                    "min": float(np.min(valid_data)),
                    "max": float(np.max(valid_data)),
                    "mean": float(np.mean(valid_data)),
                    "std": float(np.std(valid_data)),
                }
        except Exception as e:
            logger.warning(f"Could not compute stats for {self.name}: {e}")
            return {"min": np.nan, "max": np.nan, "mean": np.nan, "std": np.nan}


class TemperatureRaster(BaseModel):
    """
    Represents the target variable: Land Surface Temperature (LST).
    
    Attributes:
        file_path: Path to the temperature GeoTIFF.
        unit: Temperature unit ('C' or 'K').
        period: Time period of the composite (e.g., '2023_summer').
        cloud_cover_pct: Average cloud cover percentage for the composite.
        metadata: Additional metadata.
    """

    def __init__(
        self,
        file_path: str,
        unit: str = "C",
        period: str = "unknown",
        cloud_cover_pct: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.file_path = str(file_path)
        self.unit = unit
        self.period = period
        self.cloud_cover_pct = cloud_cover_pct
        self.metadata = metadata or {}

    def validate(self) -> bool:
        """
        Validate the TemperatureRaster instance.
        
        Checks:
        1. File path exists.
        2. Unit is valid ('C' or 'K').
        3. Cloud cover is between 0 and 100.
        """
        path = Path(self.file_path)
        if not path.exists():
            logger.error(f"Temperature file not found: {self.file_path}")
            return False

        if self.unit not in ["C", "K"]:
            logger.error(f"Invalid unit: {self.unit}. Must be 'C' or 'K'.")
            return False

        if not (0.0 <= self.cloud_cover_pct <= 100.0):
            logger.error(f"Cloud cover must be between 0 and 100: {self.cloud_cover_pct}")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the temperature raster to a dictionary.
        """
        return {
            "file_path": self.file_path,
            "unit": self.unit,
            "period": self.period,
            "cloud_cover_pct": self.cloud_cover_pct,
            "metadata": self.metadata,
        }

    def get_stats(self) -> Dict[str, float]:
        """
        Compute basic statistics for the temperature layer.
        """
        try:
            import rasterio
            with rasterio.open(self.file_path) as src:
                data = src.read(1)
                valid_data = data[~np.isnan(data)]
                if len(valid_data) == 0:
                    return {"min": np.nan, "max": np.nan, "mean": np.nan, "std": np.nan}
                return {
                    "min": float(np.min(valid_data)),
                    "max": float(np.max(valid_data)),
                    "mean": float(np.mean(valid_data)),
                    "std": float(np.std(valid_data)),
                }
        except Exception as e:
            logger.warning(f"Could not compute stats for temperature: {e}")
            return {"min": np.nan, "max": np.nan, "mean": np.nan, "std": np.nan}
