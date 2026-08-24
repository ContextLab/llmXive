# Project Plan: Predicting Cognitive Flexibility from Resting-State FC Variability

## Overview
This project investigates the relationship between dynamic functional connectivity variability and cognitive flexibility using HCP resting-state fMRI data.

## Research Question
What is the impact of computational constraints on model performance?

## Method
Benchmarking across constrained hardware configurations.

## Constitution Check
| Principle | Status | Justification |
|-----------|--------|---------------|
| Short-duration windows (30s) | DEVIATION (Justified in technical-design.md) | The default short-duration window is statistically invalid for the Schaefer 200 atlas due to rank deficiency and insufficient time points for stable correlation estimation. A 60s window is mandated by FR-003 to ensure robust metric stability. |
| AR Surrogate Null Model | REJECTED | Replaced by Phase-Shuffling per FR-008 |

## Complexity Tracking
| Component | Status | Notes |
|-----------|--------|-------|
| AR Surrogate Null Model | REJECTED | Replaced by Phase-Shuffling per FR-008 |
| Sliding Window Correlation | ACTIVE | Window=60s, Step=1s |
| Phase-Shuffling | ACTIVE | 1000 surrogates per subject |

## Data Sources
- HCP 1200 Subjects Release
- NIH Toolbox Cognitive Scores

## Constraints
- CPU-only CI (7GB RAM)
- No GPU
- Real data only (no synthetic)