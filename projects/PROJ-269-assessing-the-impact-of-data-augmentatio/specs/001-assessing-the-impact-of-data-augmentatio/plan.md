# Implementation Plan: Assessing the Impact of Data Augmentation on Statistical Power in Small Samples

**Branch**: `001-assess-augmentation-impact` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-assess-augmentation-impact/spec.md`

## Summary

This project implements a Monte Carlo simulation study to quantify the impact of three data augmentation techniques (Gaussian noise, SMOTE, Random Oversampling) on Type I and Type II error rates in small-sample binary classification scenarios (N < 50). The system will download **3 verified tabular datasets** from UCI sources (due to availability constraints), subsample them to target sizes (N=15, 25, 40), apply augmentations, and run multiple hypothesis test iterations per configuration. 

The study explicitly defines two ground-truth conditions:
1. **Null (Type I)**: Labels are permuted to break any signal before augmentation.
2. **Alternative (Type II)**: A controlled mean shift (Cohen's d = 0.5) is applied to create a known signal before augmentation.

Results will be compared against a non-augmented baseline (using the same ground-truth conditions) to identify safety thresholds for augmentation usage. The study will employ a sufficient number of iterations to ensure convergence, following the methodology outlined by [Citation]. (multiple datasets × varying sizes × 4 conditions [Baseline-Null, Aug-Null, Baseline-Alt, Aug-Alt] × [deferred] iters).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `imbalanced-learn`, `scipy`, `requests`  
**Storage**: Local file system (`data/` for raw/derived data, `results/` for JSON outputs)  
**Testing**: `pytest` (unit tests for subsampling/augmentation logic; integration tests for simulation loop)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Computational Research / Simulation  
**Performance Goals**: Complete 36,000 simulation iterations within 6 hours on CPU-only hardware.  
**Constraints**: No GPU; memory usage < 7 GB; strict random seed pinning for reproducibility; all external data must be checksummed.  
**Scale/Scope**: Several datasets (Breast Cancer, Ionosphere, Heart Disease), Several sample sizes, ground-truth/augmentation conditions, A comprehensive set of simulation runs will be conducted..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/simulation.py`; datasets fetched via fixed URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant (with Deviation)** | All dataset URLs sourced from `# Verified datasets` block. Note: FR-001 requested 5 datasets; only a limited number of verified sources exist. Deviation documented in "Spec Deviation & Mitigation". |
| **III. Data Hygiene** | **Compliant** | Raw data downloaded to `data/raw/` with checksums; augmented data saved to `data/derived/` with provenance metadata. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats trace to `results/` JSON; no hand-typed numbers in documentation. |
| **V. Versioning Discipline** | **Compliant** | Content hashes recorded in `state/` manifest upon artifact generation. |
| **VI. Augmentation Method Transparency** | **Compliant** | Augmentation scripts record library version, hyperparameters, and seed in metadata headers. |
| **VII. Statistical Inference Integrity** | **Compliant** | Error rates accompanied by % CIs (bootstrap); KS tests used only as supplementary diagnostics. Ground truth generation (permutation/shift) explicitly defined. |

## Spec Deviation & Mitigation

**Deviation**: FR-001 mandates "exactly 5 tabular datasets". Research phase identified a limited set of verified sources suitable for t-test logic (Breast Cancer, Ionosphere, Heart Disease).
**Mitigation**: 
1. Proceed with multiple verified datasets to ensure methodological validity (avoiding unverified or mismatched modalities).
2. Log a warning during `download_data.py` execution indicating the count deviation.
3. Flag FR-001 for a formal spec amendment to "up to 5" or "available verified" in the next iteration.
4. Constitution Check reflects "Compliant (with Deviation)" to ensure transparency.

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-augmentation-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Finalized in this phase)
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-269-assessing-the-impact-of-data-augmentatio/
├── code/
│   ├── __init__.py
│   ├── download_data.py          # Downloads and checksums UCI datasets
│   ├── subsample.py              # Stratified subsampling logic
│   ├── augment.py                # Gaussian, SMOTE, Random Oversampling
│   ├── simulate.py               # Monte Carlo loop (sufficient iterations for convergence)
│   ├── analyze.py                # Error rate calculation, KS test, reporting
│   └── main.py                   # Orchestration script
├── data/
│   ├── raw/                      # Downloaded CSVs (checksummed)
│   └── derived/                  # Augmented subsets (metadata included)
├── results/
│   └── [dataset]_[size]_[ground_truth]_[method].json  # Simulation outputs
├── tests/
│   ├── test_subsample.py
│   ├── test_augment.py
│   └── test_simulation.py
└── requirements.txt
```

**Structure Decision**: Single-project structure chosen for simplicity and alignment with computational research workflows. No frontend/backend split required. Contracts are finalized in Phase 1 and used for validation in Phase 2.

## Complexity Tracking

> **N/A**: No Constitution Check violations detected. Complexity is managed via modular scripts and strict resource constraints. The deviation in dataset count reduces total iterations ([deferred] vs [deferred]), improving feasibility.