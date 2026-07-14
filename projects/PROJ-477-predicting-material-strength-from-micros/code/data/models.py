from __future__ import annotations
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
import uuid
import hashlib
import os

# Constants for validation
MIN_YIELD_STRENGTH_MPA = 0.0
MAX_YIELD_STRENGTH_MPA = 5000.0
MIN_GRAIN_SIZE_UM = 0.0
MAX_GRAIN_SIZE_UM = 10000.0
MIN_IMAGE_SIZE_PIXELS = 10
MAX_IMAGE_SIZE_PIXELS = 8192
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
SUPPORTED_MICROSCOPY_TYPES = {"SEM", "EBSD", "TEM", "OM", "AFM"}

def generate_image_id(filename: str, source_path: Optional[Path] = None) -> str:
    """
    Generate a deterministic unique ID for an image based on its filename and path.
    If source_path is provided, includes it in the hash for extra uniqueness across directories.
    """
    if source_path:
        content = f"{source_path}:{filename}"
    else:
        content = filename
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


class MicrostructureImage(BaseModel):
    """
    Represents a single microstructure image with its metadata.
    Corresponds to the 'MicrostructureImage' entity in data-model.md.
    """
    image_id: str = Field(
        ...,
        description="Unique identifier for the image, generated from filename and path",
        min_length=1,
        max_length=64
    )
    filename: str = Field(
        ...,
        description="Original filename of the image",
        min_length=1
    )
    filepath: Path = Field(
        ...,
        description="Absolute path to the image file on disk"
    )
    width_pixels: int = Field(
        ...,
        description="Width of the image in pixels",
        ge=MIN_IMAGE_SIZE_PIXELS,
        le=MAX_IMAGE_SIZE_PIXELS
    )
    height_pixels: int = Field(
        ...,
        description="Height of the image in pixels",
        ge=MIN_IMAGE_SIZE_PIXELS,
        le=MAX_IMAGE_SIZE_PIXELS
    )
    channels: int = Field(
        ...,
        description="Number of color channels (1 for grayscale, 3 for RGB)",
        ge=1,
        le=4
    )
    microscopy_type: str = Field(
        ...,
        description="Type of microscopy used to capture the image",
        pattern=f"^(?:{'|'.join(SUPPORTED_MICROSCOPY_TYPES)})$"
    )
    magnification: Optional[float] = Field(
        None,
        description="Magnification factor if available",
        ge=0.0
    )
    pixel_size_um: Optional[float] = Field(
        None,
        description="Physical size of one pixel in micrometers",
        ge=0.0
    )
    acquisition_date: Optional[datetime] = Field(
        None,
        description="Date and time when the image was acquired"
    )
    source_dataset: Optional[str] = Field(
        None,
        description="Name of the source dataset this image came from"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata fields not explicitly defined"
    )

    @field_validator('filepath')
    @classmethod
    def validate_filepath(cls, v: Path) -> Path:
        if not v.is_absolute():
            raise ValueError("filepath must be an absolute path")
        if not v.exists():
            raise ValueError(f"File does not exist: {v}")
        if v.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(f"Unsupported image extension: {v.suffix}")
        return v

    @field_validator('microscopy_type')
    @classmethod
    def validate_microscopy_type(cls, v: str) -> str:
        if v not in SUPPORTED_MICROSCOPY_TYPES:
            raise ValueError(f"Microscopy type must be one of: {SUPPORTED_MICROSCOPY_TYPES}")
        return v

    @computed_field
    @property
    def pixel_count(self) -> int:
        """Total number of pixels in the image."""
        return self.width_pixels * self.height_pixels

    @computed_field
    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio of the image (width / height)."""
        return self.width_pixels / self.height_pixels

    @model_validator(mode='after')
    def generate_id_if_missing(self) -> 'MicrostructureImage':
        if not self.image_id:
            self.image_id = generate_image_id(self.filename, self.filepath.parent)
        return self


class YieldStrengthValue(BaseModel):
    """
    Represents a yield strength measurement for a material sample.
    Corresponds to the 'YieldStrengthValue' entity in data-model.md.
    """
    value_mpa: float = Field(
        ...,
        description="Yield strength value in Megapascals (MPa)",
        ge=MIN_YIELD_STRENGTH_MPA,
        le=MAX_YIELD_STRENGTH_MPA
    )
    image_id: str = Field(
        ...,
        description="Reference to the MicrostructureImage this value corresponds to",
        min_length=1
    )
    measurement_method: str = Field(
        ...,
        description="Method used to determine yield strength",
        pattern="^(?:tensile_test|compression_test|microhardness|hall_petch_estimation|cnn_prediction)$"
    )
    confidence_score: Optional[float] = Field(
        None,
        description="Confidence score of the measurement (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    uncertainty_mpa: Optional[float] = Field(
        None,
        description="Uncertainty margin in MPa",
        ge=0.0
    )
    measurement_date: Optional[datetime] = Field(
        None,
        description="Date and time when the measurement was taken"
    )
    temperature_celsius: Optional[float] = Field(
        None,
        description="Temperature at which measurement was taken"
    )
    strain_rate_s_inv: Optional[float] = Field(
        None,
        description="Strain rate during measurement in s^-1",
        ge=0.0
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes about the measurement"
    )

    @field_validator('value_mpa')
    @classmethod
    def validate_strength_range(cls, v: float) -> float:
        if v < MIN_YIELD_STRENGTH_MPA or v > MAX_YIELD_STRENGTH_MPA:
            raise ValueError(
                f"Yield strength must be between {MIN_YIELD_STRENGTH_MPA} and "
                f"{MAX_YIELD_STRENGTH_MPA} MPa"
            )
        return v

    @field_validator('confidence_score')
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v

    @model_validator(mode='after')
    def validate_uncertainty_consistency(self) -> 'YieldStrengthValue':
        # If uncertainty is provided, confidence should ideally also be provided
        if self.uncertainty_mpa is not None and self.confidence_score is None:
            # We don't raise an error, just a warning-like behavior by setting a default
            # In a real system, this might trigger a log warning
            pass
        return self

    @computed_field
    @property
    def is_estimated(self) -> bool:
        """True if the value was estimated rather than directly measured."""
        return self.measurement_method in ["hall_petch_estimation", "cnn_prediction"]

    @computed_field
    @property
    def relative_uncertainty(self) -> Optional[float]:
        """Relative uncertainty as a fraction of the value."""
        if self.uncertainty_mpa is not None and self.value_mpa > 0:
            return self.uncertainty_mpa / self.value_mpa
        return None