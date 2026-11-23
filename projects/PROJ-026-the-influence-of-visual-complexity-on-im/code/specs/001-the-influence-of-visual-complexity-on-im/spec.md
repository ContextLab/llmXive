# Specification: The Influence of Visual Complexity on Implicit Bias

**Project ID**: PROJ-026
**Version**: 1.1 (Amended)
**Status**: Active

## 1. Overview

This project investigates the relationship between the visual complexity of background stimuli and implicit bias scores (D-scores) measured via an Implicit Association Test (IAT).

## 2. Functional Requirements

### FR-001: Stimulus Processing
The system shall compute visual complexity metrics (Edge Density, Entropy, Fractal Dimension) for a set of background images.

### FR-002: Data Collection
The system shall aggregate raw IAT response times into D-scores per session using the Greenwald D2 algorithm.

### FR-003: Statistical Analysis [AMENDED]
**Original**: Perform a Repeated-Measures ANOVA on the D-scores.
**Amended**: Perform a **Permutation Test** to assess the significance of the difference in D-scores between Low and High complexity conditions.
**Reference**: See `amendment-001.md` for full details.

### FR-004: Sensitivity Analysis
The system shall perform a sensitivity analysis including threshold sweeps and Leave-One-Image-Out (LOIO) validation.

### FR-005: Visualization
The system shall generate publication-quality boxplots comparing D-scores across complexity conditions.

## 3. Data Model

- **ImageStimulus**: `path`, `edge_density`, `entropy`, `fractal_dim`, `complexity_category`
- **ParticipantResponse**: `participant_id`, `session_id`, `reaction_time`, `is_correct`, `timestamp`
- **AggregatedScore**: `participant_id`, `session_id`, `d_score`, `n_trials_valid`, `status`

## 4. Constraints

- **Data Integrity**: No synthetic data shall be used for final analysis. Real data must be loaded from `data/raw/`.
- **Reproducibility**: All random operations must use seed 42.
- **Performance**: The pipeline must complete within the allocated compute budget (approx. 7GB RAM).

## 5. Amendments

- **Amendment 001**: Replacement of FR-003 (ANOVA) with Permutation Test. Ratified on 2023-10-27.