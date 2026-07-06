# Data Model: Solvent Effects on Photo-Fries Rearrangement Kinetics

## Overview

This document defines the data structures, relationships, and schemas for the project. All data is stored in `data/` (raw, compute, processed) and validated against `contracts/`.

## Entities

### 1. Solvent Condition
Represents a specific experimental environment.
*   **Attributes**:
    *   `solvent_id`: Unique identifier (e.g., "C6H12", "CH3OH").
    *   `dielectric_constant`: Float (e.g., 2.0, 33.0).
    *   `temperature`: Float (Target: 25.0°C, Tolerance: ±0.5°C).
    *   `humidity`: Float (Target: 50%, Tolerance: ±2% RH).
    *   `pressure`: Float (Barometric pressure in hPa).
    *   `manufacturer`: String.
    *   `lot_number`: String.
    *   `purity`: Float (e.g., 0.99).
    *   `lookup_match_status`: Enum ("match", "mismatch", "unverified").

### 2. Kinetic Trace
Raw or processed transient-absorption data.
*   **Attributes**:
    *   `trace_id`: Unique identifier.
    *   `solvent_id`: Foreign key to `Solvent Condition`.
    *   `wavelength_nm`: Float (e.g., 350.0).
    *   `time_ns`: Array of floats (Time points).
    *   `absorbance`: Array of floats (Signal).
    *   `calibration_id`: Foreign key to `Calibration Record`.
    *   `status`: Enum ("valid", "flagged_humidity", "flagged_temp", "failed_fit").

### 3. Reaction Metric
Derived lifetime and statistics.
*   **Attributes**:
    *   `metric_id`: Unique identifier.
    *   `trace_id`: Foreign key to `Kinetic Trace`.
    *   `lifetime_ns`: Float (Fitted $\tau$).
    *   `confidence_interval_lower`: Float.
    *   `confidence_interval_upper`: Float.
    *   `replicate_group`: String (e.g., "C6H12_rep1").
    *   `mean_lifetime_ns`: Float (Aggregated per solvent).
    *   `std_lifetime_ns`: Float.
    *   `power_analysis_id`: Foreign key to `Power Analysis`.

### 4. Solvation Energy
Computed DFT data.
*   **Attributes**:
    *   `solv_id`: Unique identifier.
    *   `solvent_id`: Foreign key to `Solvent Condition`.
    *   `delta_g_solv_kcal_mol`: Float.
    *   `method`: Enum ("SMD", "PCM", "Explicit").
    *   `basis_set`: String (e.g., "6-31G*").
    *   `functional`: String (e.g., "B3LYP").

### 5. Calibration Record
Instrument validation data.
*   **Attributes**:
    *   `calib_id`: Unique identifier.
    *   `date`: ISO-8601 Date.
    *   `detector_response`: Float.
    *   `wavelength_offset`: Float.
    *   `baseline_drift`: Float.

### 6. Power Analysis
Documented power analysis for the sample size.
*   **Attributes**:
    *   `analysis_id`: Unique identifier.
    *   `sample_size`: Integer (n per solvent).
    *   `detectable_effect_size`: Float.
    *   `power`: Float.
    *   `limitations`: String.

### 7. Sensitivity Analysis
Results of sensitivity analysis on decision cutoffs.
*   **Attributes**:
    *   `analysis_id`: Unique identifier.
    *   `cutoff_value`: Float.
    *   `false_positive_rate`: Float.
    *   `false_negative_rate`: Float.

## Relationships

*   **Solvent Condition** (1) -- (N) **Kinetic Trace**
*   **Solvent Condition** (1) -- (N) **Solvation Energy**
*   **Kinetic Trace** (1) -- (1) **Reaction Metric**
*   **Calibration Record** (1) -- (N) **Kinetic Trace**
*   **Reaction Metric** (N) -- (1) **Power Analysis**
*   **Sensitivity Analysis** (1) -- (N) **Reaction Metric** (via cutoff)

## Data Flow

1.  **Ingest**: Raw traces (simulated) and DFT results loaded into `data/raw/` and `data/compute/`.
2.  **Validate**: Check against `contracts/`. Flag out-of-tolerance environmental conditions. **SC-010**: Validate dielectric constants against lookup table.
3.  **Process**: Fit kinetic models -> Generate `Reaction Metric`.
4.  **Aggregate**: Calculate mean/std per solvent.
5.  **Analyze**: Correlate `Reaction Metric` with `Solvation Energy`. **SC-007**: Document power analysis.
6.  **Sensitivity**: Vary cutoffs -> Generate `Sensitivity Analysis`. **SC-008**: Report error rates.

## Schema References

*   Input Schema: `contracts/dataset.schema.yaml`
*   Output Schema: `contracts/output.schema.yaml`
*   Entity Schemas: `contracts/solvent.schema.yaml`, `contracts/kinetic_trace.schema.yaml`, `contracts/reaction_metric.schema.yaml`