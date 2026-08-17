"""
Raster data models for covariates and temperature targets.
"""
from typing import Optional, Dict, Any, List, Tuple
import json
from pathlib import Path
import numpy as np
import logging

from .base import BaseModel

logger = logging.getLogger(__name__)

class RasterCovariate(BaseModel):
    """
    Represents a raster covariate layer (e.g., building density, NDVI).
    
    Attributes:
        name: Unique identifier for the covariate.
        path: Path to the GeoTIFF file.
        crs_epsg: EPSG code of the CRS.
        resolution_m: Resolution in meters.
        data_type: Data type (e.g., 'continuous', 'categorical').
        nodata_value: Value representing missing data.
        description: Human-readable description.
        created_at: ISO timestamp of creation.
    """
    REQUIRED_FIELDS = ["name", "path", "crs_epsg", "resolution_m", "data_type"]

    def __init__(
        self,
        name: str,
        path: str,
        crs_epsg: int,
        resolution_m: float,
        data_type: str,
        nodata_value: Optional[float] = None,
        description: Optional[str] = None,
        created_at: Optional[str] = None,
    ):
        data = {
            "name": name,
            "path": path,
            "crs_epsg": crs_epsg,
            "resolution_m": resolution_m,
            "data_type": data_type,
            "nodata_value": nodata_value,
            "description": description,
            "created_at": created_at,
        }
        self.validate_schema(data, self.REQUIRED_FIELDS)

        self.name = name
        self.path = Path(path)
        self.crs_epsg = crs_epsg
        self.resolution_m = resolution_m
        self.data_type = data_type
        self.nodata_value = nodata_value
        self.description = description
        self.created_at = created_at

        # Validate file existence if path is provided
        if self.path.exists():
            logger.debug(f"Raster file exists: {self.path}")
        else:
            logger.warning(f"Raster file not found: {self.path}")

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["path"] = str(self.path)
        return d

    @classmethod
    def from_raster_file(cls, path: Path, name: Optional[str] = None) -> "RasterCovariate":
        """
        Create a RasterCovariate by reading metadata from a GeoTIFF.
        
        Args:
            path: Path to the GeoTIFF.
            name: Optional name override. Defaults to filename stem.
        
        Returns:
            RasterCovariate instance.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            ImportError: If rasterio is not installed.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Raster file not found: {path}")
        
        try:
            import rasterio
        except ImportError:
            raise ImportError("rasterio is required to read raster metadata.")

        with rasterio.open(path) as src:
            crs_epsg = src.crs.to_epsg() if src.crs else 4326
            # Estimate resolution from transform
            res_x, res_y = abs(src.transform.a), abs(src.transform.e)
            resolution_m = (res_x + res_y) / 2.0
            
            nodata = src.nodata
            count = src.count
            dtype = src.dtypes[0]

            # Infer data type
            if count > 1:
                data_type = "multiband"
            elif dtype in ['float32', 'float64']:
                data_type = "continuous"
            else:
                data_type = "categorical"

            return cls(
                name=name or path.stem,
                path=str(path),
                crs_epsg=crs_epsg,
                resolution_m=resolution_m,
                data_type=data_type,
                nodata_value=nodata,
                description=f"Auto-detected from {path.name}",
            )

class TemperatureRaster(BaseModel):
    """
    Represents a temperature raster layer (LST).
    
    Attributes:
        name: Unique identifier.
        path: Path to the GeoTIFF.
        crs_epsg: EPSG code.
        resolution_m: Resolution in meters.
        acquisition_time: ISO timestamp of satellite acquisition.
        sensor: Sensor name (e.g., MODIS, Landsat).
        band_index: Band index for temperature (default 0).
        nodata_value: Missing data value.
        units: Temperature units (default 'Kelvin').
    """
    REQUIRED_FIELDS = ["name", "path", "crs_epsg", "resolution_m", "acquisition_time"]

    def __init__(
        self,
        name: str,
        path: str,
        crs_epsg: int,
        resolution_m: float,
        acquisition_time: str,
        sensor: Optional[str] = "MODIS",
        band_index: int = 0,
        nodata_value: Optional[float] = None,
        units: str = "Kelvin",
    ):
        data = {
            "name": name,
            "path": path,
            "crs_epsg": crs_epsg,
            "resolution_m": resolution_m,
            "acquisition_time": acquisition_time,
            "sensor": sensor,
            "band_index": band_index,
            "nodata_value": nodata_value,
            "units": units,
        }
        self.validate_schema(data, self.REQUIRED_FIELDS)

        self.name = name
        self.path = Path(path)
        self.crs_epsg = crs_epsg
        self.resolution_m = resolution_m
        self.acquisition_time = acquisition_time
        self.sensor = sensor
        self.band_index = band_index
        self.nodata_value = nodata_value
        self.units = units

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["path"] = str(self.path)
        return d

    @classmethod
    def from_raster_file(cls, path: Path, acquisition_time: str, name: Optional[str] = None) -> "TemperatureRaster":
        """
        Create a TemperatureRaster from a GeoTIFF file.
        
        Args:
            path: Path to the GeoTIFF.
            acquisition_time: ISO timestamp of acquisition.
            name: Optional name override.
        
        Returns:
            TemperatureRaster instance.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Temperature raster not found: {path}")
        
        try:
            import rasterio
        except ImportError:
            raise ImportError("rasterio is required to read raster metadata.")

        with rasterio.open(path) as src:
            crs_epsg = src.crs.to_epsg() if src.crs else 4326
            res_x, res_y = abs(src.transform.a), abs(src.transform.e)
            resolution_m = (res_x + res_y) / 2.0
            nodata = src.nodata

            return cls(
                name=name or path.stem,
                path=str(path),
                crs_epsg=crs_epsg,
                resolution_m=resolution_m,
                acquisition_time=acquisition_time,
                nodata_value=nodata,
            )
