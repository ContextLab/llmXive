# Data Model: Testing the Equivalence Principle with Satellite Laser Ranging

## Overview

This document defines the data structures used in the pipeline. All entities are implemented as Python dataclasses in `code/models/entities.py` and validated against YAML schemas in `contracts/`.

## Core Entities

### NormalPoint

Represents a single SLR observation.

- **timestamp**: `datetime` (ISO 8601)
- **range**: `float` (meters)
- **satellite_id**: `str` (e.g., "LAGEOS-1")
- **station_id**: `str` (e.g., "7110")
- **quality_flag**: `float` (residual in cm; used for filtering)

### SatelliteMetadata

**New Entity**: Represents the physical properties of a satellite required to calculate expected non-gravitational forces.

- **satellite_id**: `str`
- **mass**: `float` (kg)
- **cross_section_area**: `float` (m^2)
- **optical_properties**: `dict` (reflectivity, absorption coefficients)
- **source**: `str` (e.g., "ILRS Mission Specs")

### OrbitSolution

Represents a fitted dynamical model.

- **satellite_id**: `str`
- **orbital_elements**: `dict` (a, e, i, Omega, omega, M)
- **non_gravitational_acceleration**: `dict` (drag, srP, etc.)
- **covariance_matrix**: `list[list[float]]`
- **chi_squared**: `float`
- **residuals**: `list[float]` (post-fit)
- **converged**: `bool`

### EotvosResult

Represents the final test outcome.

- **satellite_pair**: `tuple[str, str]`
- **eta_value**: `float`
- **confidence_interval**: `tuple[float, float]`
- **p_value**: `float`
- **sensitivity_sweep_data**: `list[dict]` (Z-scores per geopotential model)
- **geopotential_model**: `str`
- **significance_flag**: `str` ("Significant", "Not Significant", "Unreliable")
- **precision_status**: `str` ("Within Target", "Below Target")
- **robustness_score**: `float` (std dev of Z-scores)

## Data Flow

1. **Ingestion**: Raw SLR data (CSV) -> `NormalPoint` objects -> Filtered CSV.
2. **Metadata Load**: Satellite metadata (CSV/JSON) -> `SatelliteMetadata` objects.
3. **Dynamics**: Filtered CSV + Metadata -> `OrbitSolution` objects.
4. **Analysis**: `OrbitSolution` pairs + Metadata -> `EotvosResult`.
5. **Output**: `EotvosResult` -> CSV/JSON report.

## Validation Rules

- **NormalPoint**: `range` must be > 0; `quality_flag` < 2.0 (cm).
- **SatelliteMetadata**: `mass` and `cross_section_area` must be > 0. **Hard Requirement**: If metadata is missing for a satellite, it is excluded from the differential analysis.
- **OrbitSolution**: `converged` must be `True` for valid results.
- **EotvosResult**: `p_value` must be in [0, 1]; `confidence_interval` must be ordered.
