# Technical Design Document

## Overview

This document provides the technical justification for design decisions made in the
llmXive automated science pipeline for predicting cognitive flexibility from
resting-state functional connectivity variability.

## Window Length Justification

The default short-duration window is statistically invalid for the Schaefer 200 atlas due to rank deficiency and insufficient time points for stable correlation estimation. A 60s window is mandated by FR-003 to ensure robust metric stability.

The Schaefer 200-parcel atlas requires a minimum number of time points to compute
a stable correlation matrix. With a typical TR of 0.72s (HCP data), a 30s window
yields approximately 42 time points. For 200 regions, this creates a 200x200
correlation matrix where the effective degrees of freedom are insufficient for
reliable estimation, leading to rank-deficient matrices and inflated variance in
edge-wise metrics.

FR-003 explicitly requires a 60s window to address this statistical limitation.
A 60s window provides approximately 83 time points, which significantly improves
the stability of correlation estimates and ensures that the computed variability
metrics reflect true neural dynamics rather than estimation noise.

This decision represents a justified deviation from the Constitution's Principle VII
(which suggests shorter windows for dynamic analysis), as the statistical validity
of the correlation estimates takes precedence over the theoretical benefit of
higher temporal resolution in this specific context.

## Artifact Schema Override

The Plan's definition of `final_results.csv` containing `Variability_Component_1...N`
is incorrect and superseded by the Spec's single `Variability_Metric` schema. The
authoritative output contains a single `Variability_Metric` column (mean edge SD)
as defined in the functional requirements.

## Rejection of AR-Surrogates

The Plan's suggestion to use AR-surrogates is rejected in favor of phase-shuffling
as mandated by FR-008. Phase-shuffling preserves the power spectrum and autocorrelation
structure of the original time series while destroying temporal dependencies that
would create spurious dynamic connectivity patterns. This method is more appropriate
for validating that observed variability exceeds what would be expected from linear
stochastic processes.

## Configuration Parameters

- Window length: 60 seconds (FR-003)
- Step size: 1 second
- FD threshold: 0.2 mm (motion exclusion)
- Seed: 42 (reproducibility)