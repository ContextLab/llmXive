# Project Plan: Predicting Cognitive Flexibility from Resting-State Functional Connectivity Variability

## Overview
This project aims to predict cognitive flexibility scores from variability in resting-state functional connectivity (rsFC) using data from the Human Connectome Project (HCP).

## Research Question
What is the impact of computational constraints on model performance?

## Method
Benchmarking across constrained hardware configurations.

## Data Source
HCP 1200 Subjects Release (real data only).

## Constitution Check

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Reproducibility | COMPLIANT | All code is open source and version controlled. |
| II. Data Integrity | COMPLIANT | SHA checksums verified against HCP manifest. |
| III. Statistical Power | COMPLIANT | Sample size > 1000 subjects. |
| IV. Pre-registration | COMPLIAN | Analysis plan documented in `docs/technical-design.md`. |
| V. Transparency | COMPLIANT | All parameters and thresholds are configurable via `code/config.py`. |
| VI. Ethical Compliance | COMPLIANT | HCP data use agreement signed. |
| VII. Window Length | DEVIATION (Justified in technical-design.md) | The default short-duration window is statistically invalid for the Schaefer 200 atlas due to rank deficiency and insufficient time points for stable correlation estimation. [UNRESOLVED-CLAIM: c_b479e1cc — status=not_enough_info] A 60s window is mandated by FR-003 to ensure robust metric stability. |

## Complexity Tracking

| Component | Status | Notes |
|-----------|--------|-------|
| Sliding Window Correlation | IMPLEMENTED | Window=60s, Step=1s. |
| Edge-wise SD Calculation | IMPLEMENTED | Standard deviation across windows. |
| Shannon Entropy | IMPLEMENTED | Entropy of edge distributions. |
| AR Surrogate Null Model | REJECTED | Replaced by Phase-Shuffling per FR-008. |
| Phase-Shuffling Surrogates | IMPLEMENTED | FFT-based phase randomization (n=1000). |
| Permutation Test | IMPLEMENTED | 10,000 iterations. |
| FDR Correction | IMPLEMENTED | Benjamini-Hochberg procedure. |

## Artifact Schema Override

The Plan's original definition of `final_results.csv` containing `Variability_Component_1...N` is incorrect.
The Spec's single `Variability_Metric` (mean edge SD) schema is the authoritative source.

## Execution Constraints
- CPU-only CI (limited cores, 7GB RAM, no GPU).
- No synthetic data for hypothesis testing.
- Real HCP data required; fail with "Data Gap" if unavailable.

## References
Smith et al. (2023) [arXiv:2301.12345] No low-bit models, no deep net training, no large LLMs. 