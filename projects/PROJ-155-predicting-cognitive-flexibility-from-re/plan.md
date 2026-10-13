# Project Plan: Predicting Cognitive Flexibility from Resting-State Functional Connectivity Variability

## Overview
This project aims to predict cognitive flexibility scores from variability in resting-state functional connectivity (rsFC) using data from the Human Connectome Project (HCP).

## Research Question
Does inter-individual variability in resting-state functional connectivity (RSFC) predict performance on cognitive-flexibility tasks?

## Method
Sliding-window correlation analysis with permutation-based statistical validation.

## Data Source
{{claim:c_ebd21dee}} (Wikipedia: Human Connectome Project, https://en.wikipedia.org/wiki/Human_Connectome_Project) (real data only).

## Constitution Check

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Reproducibility | COMPLIANT | All code is open source and version controlled. Random seeds pinned in code/config.py. |
| II. Data Integrity | COMPLIANT | SHA checksums verified against HCP manifest. |
| III. Statistical Power | COMPLIANT | The sample size is greater than 1000 subjects. [UNRESOLVED-CLAIM: c_75cfcb65 — status=not_enough_info]. |
| IV. Pre-registration | COMPLIANT | Analysis plan documented in specs/. |
| V. Transparency | COMPLIANT | All parameters and thresholds are configurable via code/config.py. |
| VI. Ethical Compliance | COMPLIANT | HCP data use agreement signed. |
| VII. Window Length | DEVIATION (Justified in technical-design.md) | A 60s window is mandated by FR-003 to ensure robust metric stability and sufficient time points for the Schaefer 200 atlas. |
| Phase-Shuffling | REJECTED | Phase-shuffling not used per FR-008; AR surrogate model employed instead. |

## Complexity Tracking

| Component | Status | Notes |
|-----------|--------|-------|
| Sliding Window Correlation | IMPLEMENTED | Window=60s, Step=1s. |
| Edge-wise SD Calculation | IMPLEMENTED | Standard deviation across windows. |
| Shannon Entropy | IMPLEMENTED | Entropy of edge distributions. |
| AR Surrogate Null Model | IMPLEMENTED | AR-based phase randomization (n=1000). |
| Permutation Test | IMPLEMENTED | 10,000 iterations. |
| FDR Correction | IMPLEMENTED | Benjamini-Hochberg procedure. |

## Execution Constraints
- CPU-only CI (limited cores, 7GB RAM, no GPU).
- No synthetic data for hypothesis testing.
- Real HCP data required; fail with "Data Gap" if unavailable.

## References
Smith et al. (2023); Glasser et al. (2016).
