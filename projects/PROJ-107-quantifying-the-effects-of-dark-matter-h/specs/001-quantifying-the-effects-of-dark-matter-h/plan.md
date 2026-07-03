# Implementation Plan: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

**Branch**: `001-quantifying-the-effects-of-dark-matter-h` | **Date**: 2026-06-25 | **Spec**: `specs/001-quantifying-the-effects-of-dark-matter-h/spec.md`
**Input**: Feature specification from `/specs/001-quantifying-the-effects-of-dark-matter-h/spec.md`

## Summary

This project implements a computational pipeline to quantify **associational trends** between dark matter halo shapes (triaxiality) and galaxy formation properties (Star Formation Rate, effective radius) using cosmological simulation data. The technical approach involves ingesting the IllustrisTNG-100 dataset (primary) and attempting to ingest Millennium-II (conditional), computing reduced inertia tensors for halo shape metrics, performing mass-controlled statistical comparisons (Kruskal-Wallis, Mann-Whitney U, KS tests), and conducting sensitivity analyses on binning thresholds. **All analysis is strictly framed as associational evidence; no causal claims are made.** The pipeline is constrained to CPU-only execution on GitHub Actions free-tier runners (limited CPU and constrained RAM) via chunked processing and sampling.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scipy`, `scikit-learn`, `h5py`, `requests`, `pyyaml`  
**Note on `pyyaml`**: Used specifically for loading contract schemas and configuration files.  
**Storage**: Local file system (parquet/csv/hdf5) for intermediate and final artifacts; no external database.  
**Testing**: `pytest` for unit tests on tensor calculations and statistical logic; integration tests for pipeline end-to-end on sampled data.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Complete full pipeline on sampled dataset within 6 hours; memory usage < 6 GB peak.  
**Constraints**: NO GPU/CUDA; NO large-LLM inference; Data must be processed in chunks to fit available RAM.; all statistical tests must include Bonferroni correction for multiple comparisons.  
**Scale/Scope**: Processing a substantial number of haloes (sampled/chunked) from TNG-100. Millennium-II is conditional.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `random.seed(42)` pinned in all scripts; `requirements.txt` pins exact versions; data fetched from canonical URLs only. |
| **II. Verified Accuracy** | **PASS (with Caveat)** | All citations restricted to verified dataset URLs. Millennium-II is unverified; the plan explicitly excludes it from the active analysis scope if no URL is found, preventing unverified data from contributing to results. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` with checksums recorded in `data/metadata.yaml`; derived data written to new files with provenance headers. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` generated via `code/` scripts reading from `data/`; no manual entry of numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for all data artifacts tracked in `state/`. The `Advancement-Evaluator` agent is explicitly responsible for updating `state/` artifact hashes and `updated_at` timestamps upon data change. |
| **VI. Simulation Data Integrity** | **PASS** | TNG-100 downloaded from official portals; version IDs recorded in `data/metadata.yaml`; derived quantities link back to raw snapshot files. |
| **VII. Statistical Rigor** | **PASS** | Pre-registered tests implemented with Bonferroni correction (family-wise error rate controlled); p-value thresholds and confidence intervals explicitly coded; Null Simulation Control added to distinguish artifacts from physical correlations. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-the-effects-of-dark-matter-h/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point for pipeline orchestration
├── ingestion/
│   ├── __init__.py
│   ├── tng_loader.py    # TNG-100 data fetcher and parser
│   └── millennium_loader.py # Millennium-II data fetcher (conditional)
├── processing/
│   ├── __init__.py
│   ├── inertia_tensor.py # Reduced inertia tensor calculation
│   ├── shape_metrics.py  # Axial ratios, triaxiality, binning
│   └── alignment.py      # Spin vector and misalignment angle calc
├── analysis/
│   ├── __init__.py
│   ├── stats.py          # Kruskal-Wallis, MWU, KS, Regression
│   ├── sensitivity.py    # Threshold sweep logic
│   └── null_control.py   # Null simulation (shuffling) logic
├── utils/
│   ├── __init__.py
│   ├── io.py             # CSV/Parquet I/O with checksums
│   └── config.py         # Seed and path configuration
└── tests/
    ├── test_inertia.py
    ├── test_stats.py
    └── test_pipeline.py

data/
├── raw/
│   ├── tng100/           # Raw simulation data (chunked)
│   └── millennium/       # Raw simulation data (chunked, if available)
├── processed/
│   ├── halo_shapes.csv
│   ├── galaxy_properties.csv
│   └── alignment_angles.csv
└── metadata.yaml         # Checksums and version IDs

outputs/
├── figures/
└── reports/
```

**Structure Decision**: Single Python package structure (`code/`) with modular separation of concerns (ingestion, processing, analysis). This minimizes overhead and simplifies dependency management for CPU-only execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Chunked Processing** | The The TNG full catalog requires substantial RAM resources exceeding typical single-node memory capacities.. | Loading full dataset into memory would crash the runner; chunked streaming is required for feasibility. |
| **Regression-First Mass Control** | Mass is a strong confounder; binning causes selection bias. | Simple binning without mass stratification would conflate mass effects with shape effects, violating FR-012. Multivariate regression is the primary estimator to preserve statistical power. |
| **Sensitivity Sweep (Effect Size)** | Thresholds (0.5, 0.8) are phenomenological. | Fixed thresholds without validation would fail FR-006. The metric is now effect size stability (coefficient/CI), not arbitrary p-value variance. |
| **Null Simulation Control** | Risk of simulation artifacts. | Without shuffling halo-galaxy pairings, a significant p-value only proves the simulation code links them, not a robust physical law. |
| **Data Gap Protocol** | Millennium-II URL unverified. | Attempting to fetch an unverified URL risks runtime failure. The protocol explicitly skips the step if no verified source exists, logging the gap. |

## Success Criteria Adjustments

*   **SC-004 (Reproducibility)**: If Millennium-II is unavailable (no verified URL), this criterion is marked as **"Not Measurable"** with a mandatory explanation in the final report. The project does not fail if the data is genuinely inaccessible, provided the protocol is followed.

## Risk Register

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Millennium-II Data Unavailable** | Cannot satisfy FR-007 (Cross-validation). | **Data Gap Protocol**: If no verified URL exists, the pipeline skips cross-validation, logs the gap, and proceeds with TNG-100 only. SC-004 is marked "Not Measurable". |
| **Memory Overflow** | Pipeline crash on 7GB limit. | Strict chunking; discard intermediate arrays immediately; use `dtype=float32` where precision allows. |
| **Inertia Tensor Singularities** | Numerical errors for low-N haloes. | Exclude haloes with $N < 10,000$ (FR-002); add small regularization term if necessary. |
| **False Positives** | Spurious correlations due to multiple testing. | Strict Bonferroni correction (FR-005) across the defined family of tests; Null Simulation Control. |
| **Binning Bias** | Discretizing continuous variables reduces power. | Primary analysis uses multivariate regression; binning is secondary for visualization only. |