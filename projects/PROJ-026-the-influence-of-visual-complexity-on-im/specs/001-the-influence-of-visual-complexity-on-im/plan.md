# Implementation Plan: The Influence of Visual Complexity on Implicit Bias

**Branch**: `001-the-influence-of-visual-complexity-on-im` | **Date**: 2026-06-29 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-the-influence-of-visual-complexity-on-im/spec.md`

## Summary

This project implements a computational pipeline to test the hypothesis that increasing the visual complexity of background stimuli during an Implicit Association Test (IAT) reduces implicit bias scores (D-scores). The technical approach involves three phases: (1) quantifying visual complexity of image stimuli using edge density, entropy, and fractal dimension; (2) aggregating raw IAT response times into D-scores (Greenwald et al.) for two counterbalanced sessions; and (3) performing a **Permutation Test** (with Leave-One-Image-Out sensitivity analysis) to test the hypothesis while controlling for stimulus-set confounds. The pipeline is designed to run entirely on CPU within GitHub Actions free-tier constraints (≤7 GB RAM, ≤6h runtime).

**Constitution Compliance Note**: The final scientific conclusion MUST rely on **real data** collected with pre-manipulated stimuli (Constitution Principle VI). Synthetic data is used **ONLY** for unit/integration testing of the D-score aggregation and statistical logic (e.g., verifying the pipeline handles null results correctly). The production analysis pipeline is designed to ingest real, pre-collected data where complexity was manipulated *before* data collection. The `code/data/load.py` module includes a `--null-effect` flag specifically for CI testing to ensure the pipeline does not tautologically confirm the hypothesis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `scipy`, `numpy`, `pandas`, `pillow`, `opencv-python-headless`, `matplotlib`, `seaborn`, `statsmodels`  
**Storage**: Local file system (CSV/JSON/Parquet) under `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete entire analysis (image processing + D-score aggregation + Permutation Test + plotting) within 6 hours on 2-core CPU, <7 GB RAM.  
**Constraints**: No GPU; no deep learning models; no external API calls during execution; strict adherence to Greenwald D2 algorithm; sensitivity analysis must handle edge cases (n < 15).  
**Scale/Scope**: A set of images for stimulus quantification; A sufficient number of participants (synthetic or collected) for analysis; sessions per participant.

> **Note**: The spec assumes new data collection. The plan implements the *analysis* of such data. For the purpose of this implementation plan and to ensure CI feasibility, the pipeline will support loading synthetic data or a provided dataset file. The statistical logic (Permutation Test, Sensitivity) is the core deliverable.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, random seed setting in code, and local data storage. No external API calls for core logic. |
| **II. Verified Accuracy** | PASS | Citations (Greenwald et al., year) will be validated against primary sources. No invented URLs. |
| **III. Data Hygiene** | PASS | Plan requires checksums for `data/` artifacts; raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | PASS | Figures/stats in paper will trace to `data/` rows and `code/` blocks. No hand-typed stats. |
| **V. Versioning Discipline** | PASS | Content hashes for artifacts; `updated_at` timestamp updates on change. |
| **VI. Stimulus Manipulation Integrity** | PASS | **Enforcement Mechanism**: `code/stimuli/metrics.py` computes metrics *before* any condition assignment. `code/data/process.py` aggregates D-scores only after metrics are finalized. Synthetic data is strictly for CI testing (Null Mode); real data requires pre-manipulated stimuli. |
| **VII. Quantified Stimulus Metrics** | PASS | Plan includes FR-001: Edge density, entropy, fractal dimension computed for every image. PCA/Dimensionality check ensures valid construct usage. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-influence-of-visual-complexity-on-im/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── main.py              # Orchestration script
├── data/
│   ├── __init__.py
│   ├── load.py          # Synthetic data generation / loading (conforms to data-model.md)
│   └── process.py       # D-score aggregation
├── stimuli/
│   ├── __init__.py
│   ├── metrics.py       # Edge density, entropy, fractal dimension
│   └── validate.py      # Image integrity checks
├── analysis/
│   ├── __init__.py
│   ├── permutation.py   # Permutation Test & LOIO sensitivity
│   └── pca.py           # PCA dimensionality check
├── viz/
│   ├── __init__.py
│   └── plot.py          # Publication-quality plots
└── tests/
    ├── test_stimuli.py
    ├── test_data.py
    └── test_analysis.py

data/
├── raw/
│   ├── stimuli/         # Original images (or synthetic placeholders)
│   └── responses/       # Raw IAT logs
├── processed/
│   ├── complexity_scores.csv
│   └── aggregated_d_scores.csv
└── results/
    ├── permutation_results.json
    └── sensitivity_results.json
```

**Structure Decision**: Single-project structure (`code/`) is chosen to minimize overhead and ensure easy dependency management for a research pipeline. All modules are Python packages to support testing and modularity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Permutation Test Module** | Required to handle the confound between 'Stimulus Set' and 'Complexity Level' (Methodology Concern 5878fce0). | ANOVA/LMM fails because 'Stimulus Set' is perfectly confounded with the fixed effect. Permutation tests the null distribution without assuming independence. |
| **PCA Dimensionality Check** | Required to avoid 'cherry-picking' a single metric (Methodology Concern 07f04f81). | Selecting one metric post-hoc introduces researcher degrees of freedom. PCA/Multivariate test ensures construct validity. |
| **Leave-One-Image-Out (LOIO)** | Required to ensure effect is not driven by a single outlier image (Methodology Concern 1ea5d194). | Simple threshold sweeping does not address stimulus-specific variance. LOIO validates robustness against specific image content. |
| **Synthetic Data Null Mode** | Required to avoid tautological validation (Scientific Soundness Concern 9d7b59a3). | Hard-coding the effect size guarantees a positive result. Null mode ensures the pipeline can detect no effect. |


## FR-SC Mapping

| ID | Requirement | Plan Element |
|----|-------------|--------------|
| FR-001 | Compute 3 complexity metrics | `code/stimuli/metrics.py` computes Edge, Entropy, Fractal. |
| FR-002 | Aggregate D-scores (Greenwald) | `code/data/process.py` implements the D algorithm. |
| FR-003 | Test hypothesis (Complexity vs D-score) | `code/analysis/permutation.py` runs Permutation Test. |
| FR-004 | Report effect sizes | `code/analysis/permutation.py` calculates Cohen's d and Permutation p-value. |
| FR-005 | Generate plot | `code/viz/plot.py` generates D-score comparison and LOIO plots. |
| FR-006 | Exclude <10 valid trials | `code/data/process.py` flags/excludes participants. |
| FR-007 | Sensitivity analysis (threshold + LOIO) | `code/analysis/permutation.py` runs threshold sweep AND LOIO. |
| SC-001 | Measure D-score difference | Permutation Test mean difference. |
| SC-002 | Measure significance (p < 0.05) | Permutation p-value. |
| SC-003 | Measure robustness | LOIO and threshold sweep results. |
| SC-004 | Power analysis | Conducted on real data (or realistic sim) in `research.md`. |
| SC-005 | Compute feasibility | CPU-only, <7GB RAM, <6h runtime. |

