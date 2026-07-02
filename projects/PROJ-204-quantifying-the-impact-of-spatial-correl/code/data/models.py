"""
Data model definitions for the Spatial Correlation Analysis Pipeline.

This module defines Pydantic models for:
- ElementalMap: Raw and processed EDS elemental map data
- DevicePerformance: Device performance metrics (PCE, Jsc, Voc)
- SpatialMetric: Computed spatial correlation metrics
- AnalysisResult: Final analysis results and statistics
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator
import numpy as np


class ElementalMap(BaseModel):
    """
    Represents an elemental map from Energy Dispersive X-ray Spectroscopy (EDS).

    Attributes:
        sample_id: Unique identifier for the sample
        element: Element symbol (e.g., 'Pb', 'I', 'MA')
        map_path: Path to the raw map file
        processed_path: Path to the processed/masked map file
        pixel_size_nm: Physical size of a pixel in nanometers
        width_px: Width of the map in pixels
        height_px: Height of the map in pixels
        depth_um: Depth of the EDS analysis in micrometers
        metadata: Additional metadata as a dictionary
        validation_flag: Flag indicating data quality (e.g., 'valid', 'defective', 'missing')
        depth_flag: Flag indicating depth resolution concerns
    """
    sample_id: str = Field(..., description="Unique sample identifier")
    element: str = Field(..., description="Element symbol (Pb, I, MA, etc.)")
    map_path: str = Field(..., description="Path to the raw map file")
    processed_path: Optional[str] = Field(None, description="Path to the processed map file")
    pixel_size_nm: float = Field(..., ge=0.0, description="Pixel size in nanometers")
    width_px: int = Field(..., gt=0, description="Map width in pixels")
    height_px: int = Field(..., gt=0, description="Map height in pixels")
    depth_um: Optional[float] = Field(None, ge=0.0, description="Analysis depth in micrometers")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    validation_flag: str = Field("valid", description="Data quality flag")
    depth_flag: str = Field("valid", description="Depth resolution flag")

    @field_validator('map_path')
    @classmethod
    def validate_map_path(cls, v: str) -> str:
        if not Path(v).exists():
            raise ValueError(f"Map file does not exist: {v}")
        return v

    def get_array(self) -> Optional[np.ndarray]:
        """Load the elemental map as a numpy array."""
        import tifffile
        if self.processed_path and Path(self.processed_path).exists():
            return tifffile.imread(self.processed_path)
        elif Path(self.map_path).exists():
            return tifffile.imread(self.map_path)
        return None


class DevicePerformance(BaseModel):
    """
    Represents device performance metrics for a perovskite solar cell.

    Attributes:
        sample_id: Unique identifier for the sample (links to ElementalMap)
        device_id: Device identifier (for co-location validation)
        pce: Power Conversion Efficiency (%)
        j_sc: Short-circuit current density (mA/cm²)
        v_oc: Open-circuit voltage (V)
        ff: Fill Factor (%)
        measurement_date: Date of the performance measurement
        metadata: Additional metadata
    """
    sample_id: str = Field(..., description="Unique sample identifier")
    device_id: str = Field(..., description="Device identifier for co-location")
    pce: float = Field(..., gt=0.0, description="Power Conversion Efficiency (%)")
    j_sc: float = Field(..., gt=0.0, description="Short-circuit current density (mA/cm²)")
    v_oc: float = Field(..., gt=0.0, description="Open-circuit voltage (V)")
    ff: Optional[float] = Field(None, ge=0.0, le=100.0, description="Fill Factor (%)")
    measurement_date: Optional[datetime] = Field(None, description="Measurement date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode='after')
    def validate_performance(self) -> 'DevicePerformance':
        if self.pce <= 0:
            raise ValueError("PCE must be positive")
        if self.j_sc <= 0:
            raise ValueError("J_sc must be positive")
        if self.v_oc <= 0:
            raise ValueError("V_oc must be positive")
        return self


class SpatialMetric(BaseModel):
    """
    Represents computed spatial correlation metrics for an elemental map.

    Attributes:
        sample_id: Unique sample identifier
        element: Element symbol
        correlation_length: Fitted correlation length (nm)
        model_type: Type of decay model used ('exponential', 'gaussian', 'power-law')
        aic: Akaike Information Criterion for model selection
        r_squared: R² value of the fit
        spectral_power_low_freq: Integrated low-frequency spectral power
        correlation_function_path: Path to the saved correlation function data
        is_undefined: Flag indicating if correlation length is undefined (decay outside bounds)
        lower_bound_nm: Lower bound for undefined correlation lengths
    """
    sample_id: str = Field(..., description="Unique sample identifier")
    element: str = Field(..., description="Element symbol")
    correlation_length: Optional[float] = Field(None, ge=0.0, description="Correlation length in nm")
    model_type: Optional[str] = Field(None, description="Best-fit decay model type")
    aic: Optional[float] = Field(None, description="AIC value")
    r_squared: Optional[float] = Field(None, ge=0.0, le=1.0, description="R² of the fit")
    spectral_power_low_freq: Optional[float] = Field(None, ge=0.0, description="Low-freq spectral power")
    correlation_function_path: Optional[str] = Field(None, description="Path to correlation function data")
    is_undefined: bool = Field(False, description="Flag for undefined correlation length")
    lower_bound_nm: Optional[float] = Field(None, ge=0.0, description="Lower bound for undefined lengths")

    @model_validator(mode='after')
    def validate_metric(self) -> 'SpatialMetric':
        if self.is_undefined and self.correlation_length is not None:
            raise ValueError("Correlation length should be None if is_undefined is True")
        if self.is_undefined and self.lower_bound_nm is None:
            raise ValueError("Lower bound must be provided for undefined correlation lengths")
        return self


class AnalysisResult(BaseModel):
    """
    Represents the final analysis results from the correlation study.

    Attributes:
        analysis_id: Unique identifier for the analysis run
        timestamp: Timestamp of the analysis
        sample_count: Number of samples in the analysis
        correlation_results: List of correlation results (Pearson/Spearman)
        gam_results: Results from Generalized Additive Model fits
        robustness_results: Leave-one-out cross-validation results
        sensitivity_delta_r: Delta r from sensitivity analysis (T031c)
        ingestion_success_rate: Success rate from data ingestion (T010b)
        flags: Summary flags (e.g., 'non-definitive' if N < min_sample_count)
        raw_metrics_path: Path to the raw spatial metrics CSV
        summary_path: Path to the summary report CSV
    """
    analysis_id: str = Field(..., description="Unique analysis identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    sample_count: int = Field(..., gt=0, description="Number of samples analyzed")
    correlation_results: List[Dict[str, Any]] = Field(default_factory=list, description="Correlation results")
    gam_results: List[Dict[str, Any]] = Field(default_factory=list, description="GAM results")
    robustness_results: List[Dict[str, Any]] = Field(default_factory=list, description="Robustness results")
    sensitivity_delta_r: Optional[float] = Field(None, description="Delta r from sensitivity analysis")
    ingestion_success_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Ingestion success rate")
    flags: List[str] = Field(default_factory=list, description="Analysis flags")
    raw_metrics_path: Optional[str] = Field(None, description="Path to raw metrics CSV")
    summary_path: Optional[str] = Field(None, description="Path to summary report")

    def add_correlation_result(
        self,
        metric_name: str,
        performance_metric: str,
        pearson_r: float,
        pearson_p: float,
        spearman_r: float,
        spearman_p: float,
        adjusted_p: Optional[float] = None
    ) -> None:
        """Add a correlation result to the analysis."""
        self.correlation_results.append({
            "metric_name": metric_name,
            "performance_metric": performance_metric,
            "pearson_r": pearson_r,
            "pearson_p": pearson_p,
            "spearman_r": spearman_r,
            "spearman_p": spearman_p,
            "adjusted_p": adjusted_p
        })

    def add_gam_result(
        self,
        metric_name: str,
        performance_metric: str,
        deviance_explained: float,
        p_value: float,
        is_nonlinear: bool
    ) -> None:
        """Add a GAM result to the analysis."""
        self.gam_results.append({
            "metric_name": metric_name,
            "performance_metric": performance_metric,
            "deviance_explained": deviance_explained,
            "p_value": p_value,
            "is_nonlinear": is_nonlinear
        })

    def add_robustness_result(
        self,
        sample_id: str,
        delta_r: float,
        is_outlier: bool
    ) -> None:
        """Add a robustness check result."""
        self.robustness_results.append({
            "sample_id": sample_id,
            "delta_r": delta_r,
            "is_outlier": is_outlier
        })


def create_sample_dataset(
    sample_ids: List[str],
    elements: List[str] = ['Pb', 'I', 'MA']
) -> List[ElementalMap]:
    """
    Helper function to create a list of ElementalMap objects for testing.
    Note: This is for testing only. Real data must be loaded from actual files.

    Args:
        sample_ids: List of sample IDs to create
        elements: List of elements to include

    Returns:
        List of ElementalMap objects
    """
    maps = []
    for sample_id in sample_ids:
        for element in elements:
            # In a real scenario, these paths would point to actual files
            # For testing, we create placeholder paths
            map_path = f"data/raw/{sample_id}_{element}_map.tif"
            maps.append(
                ElementalMap(
                    sample_id=sample_id,
                    element=element,
                    map_path=map_path,
                    pixel_size_nm=10.0,
                    width_px=256,
                    height_px=256,
                    depth_um=1.0,
                    metadata={"source": "test"}
                )
            )
    return maps


def create_sample_performance(
    sample_ids: List[str],
    device_ids: Optional[List[str]] = None
) -> List[DevicePerformance]:
    """
    Helper function to create a list of DevicePerformance objects for testing.

    Args:
        sample_ids: List of sample IDs
        device_ids: Optional list of device IDs (defaults to sample_ids)

    Returns:
        List of DevicePerformance objects
    """
    if device_ids is None:
        device_ids = sample_ids

    performances = []
    for sample_id, device_id in zip(sample_ids, device_ids):
        performances.append(
            DevicePerformance(
                sample_id=sample_id,
                device_id=device_id,
                pce=15.0 + np.random.uniform(-2, 2),
                j_sc=20.0 + np.random.uniform(-1, 1),
                v_oc=1.0 + np.random.uniform(-0.05, 0.05),
                ff=75.0 + np.random.uniform(-3, 3)
            )
        )
    return performances