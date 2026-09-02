# Data Model: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Overview

This document defines the data structures used throughout the pipeline, ensuring alignment with the `Key Entities` in the specification and the `Granular Energy Component Isolation` principle.

## Entity Definitions

### 1. ParticleState
Represents a single particle at a single time step.
-   **particle_id**: `int` (Unique identifier)
-   **timestamp**: `float` (Seconds, synchronized with driving signal)
-   **x**: `float` (Position)
-   **y**: `float` (Position)
-   **z**: `float` (Position)
-   **theta**: `float` (Orientation in radians)
-   **mass**: `float` (kg, derived from material)
-   **radius**: `float` (m, derived from material)
-   **material**: `str` (e.g., "steel", "polymer")

### 2. EnergySample
Derived from `ParticleState`. Represents raw energy values.
-   **particle_id**: `int`
-   **timestamp**: `float`
-   **E_trans**: `float` (Joules)
-   **E_rot**: `float` (Joules)
-   **E_pot**: `float` (Joules)
-   **E_vib**: `float` (Joules, **Diagnostic only**, calculated via PSD)
-   **frequency_bin**: `str` (e.g., "10Hz")

### 3. EnergyDistribution
Aggregated statistics for a group.
-   **group_label**: `str` (e.g., "Steel_10Hz")
-   **material**: `str`
-   **frequency**: `float`
-   **mean_E_trans**: `float`
-   **mean_E_rot**: `float`
-   **mean_E_pot**: `float`
-   **variance_E_trans**: `float`
-   **sample_size**: `int`
-   **equipartition_ratio**: `float` (Calculated as $\langle E_{trans} \rangle / \langle E_{rot} \rangle$)
-   **deviation_metric**: `float` (Calculated as $|\langle E_{trans} \rangle - \langle E_{rot} \rangle| / \langle E_{total} \rangle$)

### 4. StatisticalResult
Outcome of a hypothesis test.
-   **test_type**: `str` ("KS", "ChiSquare", "Regression", "PairedT")
-   **group_label**: `str`
-   **statistic_value**: `float`
-   **p_value**: `float`
-   **is_significant**: `bool`
-   **corrected_p_value**: `float` (after FDR)
-   **threshold**: `float` (alpha used)
-   **slope**: `float` (For Regression)
-   **intercept**: `float` (For Regression)
-   **r_squared**: `float` (For Regression)
-   **slope_p_value**: `float` (For Regression)
-   **t_statistic**: `float` (For Regression)

### 5. RegressionResult
Outcome of linear regression.
-   **predictor**: `str` (e.g., "frequency")
-   **slope**: `float`
-   **intercept**: `float`
-   **r_squared**: `float`
-   **slope_p_value**: `float`
-   **model_fit_quality**: `str` ("Good", "Poor")

## Data Flow

1.  **Input**: Raw CSVs (Particle Tracking) + Driving Log.
2.  **Sync**: `ParticleState` (aligned timestamps).
3.  **Compute**: `EnergySample` (finite differences + formulas). **E_vib is calculated as a separate diagnostic.**
4.  **Aggregate**: `EnergyDistribution` (group by material/frequency). **Equipartition Ratio calculated excluding E_vib.**
5.  **Test**: `StatisticalResult` (KS, Chi-squared, FDR correction, Regression).
6.  **Model**: `RegressionResult` (Deviation vs. Frequency/Roughness).

## Storage Format

-   **Intermediate**: Parquet files (efficient for columnar data, supports streaming).
-   **Final**: CSV/JSON for reporting.
-   **Configuration**: YAML for seeds and thresholds.

## Clarification on E_vib and Residuals

-   **E_vib**: Calculated via PSD integration. It is a **diagnostic component** representing energy in the driven mode. It is **NOT** added to $E_{trans}$ or $E_{rot}$ for the purpose of the equipartition ratio check.
-   **E_vib_residual**: Defined as $E_{total\_measured} - (E_{trans} + E_{rot} + E_{pot})$. This residual captures the energy balance error. It is **NOT** calculated as $Total - (E_{trans} + E_{rot} + E_{pot} + E_{vib})$. This avoids double-counting E_vib in the energy balance if E_vib is already part of the measured total motion.
-   **SSoT**: `energy_output.schema.yaml` is the Single Source of Truth for the primary output artifacts.
