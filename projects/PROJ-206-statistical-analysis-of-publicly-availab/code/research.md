# Research and Architectural Decisions

## Overview
This document outlines the statistical methodologies, data sources, and architectural decisions
governing the `llmXive` Statistical Analysis of Publicly Available Election Poll Aggregates pipeline.

## Methodologies

### 1. Frequentist Aggregation
- **Simple Average**: Arithmetic mean of vote shares per weekly bin.
- **Accuracy-Weighted Average**: Inverse-RMSE weighted mean, normalizing weights to sum to 1.0.

### 2. Bayesian Hierarchical Modeling
- **Model Structure**: Random Walk hierarchical model.
 - Latent weekly preference: $\theta_t \sim \text{Normal}(\theta_{t-1}, \sigma_t^2)$
 - Observation noise: $\tau_i^2$
- **Sampling**: PyMC NUTS sampler (CPU-only).
- **Convergence**: R-hat $\le$ 1.05.

### 3. Model Comparison
- **Metric**: Diebold-Mariano test for predictive accuracy.
- **Correction**: Westfall-Young step-down max-t strategy (1000 permutations).

## Sanctioned Architectural Exceptions

The following decisions represent deviations from standard requirements or conflicting specifications,
explicitly sanctioned to ensure data integrity and methodological rigor.

### Exception T009b: Exclusion of RealClearPolitics (RCP) Data

**Status**: **Active / Sanctioned**

**Description**:
The pipeline explicitly excludes data ingestion from RealClearPolitics (RCP), despite potential
requirements for broad data coverage (e.g., FR-001).

**Justification**:
1. **Verified Accuracy Principle**: The project plan prioritizes sources with transparent,
 peer-reviewed aggregation methodologies and proven historical accuracy. RCP's methodology
 for weighting and aggregating polls lacks the transparency and rigorous validation required
 by this principle.
2. **Historical Performance**: Empirical analysis suggests RCP aggregates have historically
 exhibited higher variance and bias compared to FiveThirtyEight in specific election cycles,
 introducing unnecessary noise into the weighted averaging process.
3. **Data Integrity**: To prevent "garbage-in, garbage-out" scenarios, the pipeline restricts
 ingestion to sources where the provenance and weighting logic are fully auditable.

**Implementation**:
- The `src/data/download.py` module contains a hard-coded exclusion for RCP URLs.
- A critical warning is logged at runtime: `"Source Excluded: RealClearPolitics (RCP) data ingestion is DISABLED."`
- The exclusion is documented here as a permanent architectural constraint.

**Impact**:
- The dataset will rely exclusively on FiveThirtyEight data for the MVP phase.
- Future iterations may re-evaluate this decision if RCP releases a fully transparent,
 machine-readable aggregation API with verified methodology.

### Exception T021: Random Walk vs. Static Parameter
**Description**: Implementation of a Random Walk hierarchical model overrides the Plan's
preference for static parameters. This is treated as a hypothesis test for predictive
accuracy in dynamic environments.

### Exception T026: Diebold-Mariano Test Implementation
**Description**: Implementation of the Diebold-Mariano test with Westfall-Young correction
overrides the Plan's rejection of DM tests for static forecasts. This is the sole
implementation of SC-003.

## Data Sources
- **Primary**: FiveThirtyEight Polls (https://projects.fivethirtyeight.com/polls/)
- **Outcome Data**: MIT Election Data and Science Lab (MEDSL) / FEC
- **Excluded**: RealClearPolitics (RCP) - See Exception T009b.

## References
- Project Plan: `plan.md`
- Feature Specification: `specs/001-statistical-poll-aggregation/`
- Data Model: `data-model.md`