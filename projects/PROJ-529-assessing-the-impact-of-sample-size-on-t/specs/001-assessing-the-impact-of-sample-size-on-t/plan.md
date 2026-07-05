# Implementation Plan: Assessing the Impact of Sample Size on Meta-Analytic Reliability

**Branch**: `001-meta-analytic-sample-size` | **Date**: 2026-06-27 | **Spec**: `specs/001-meta-analytic-sample-size/spec.md`
**Input**: Feature specification from `/specs/001-meta-analytic-sample-size/spec.md`

## Summary

This project assesses the reliability of meta-analytic effect sizes as a function of the number of component studies (sample size `k`). The technical approach involves:
1.  **Data Acquisition**: Attempting to acquire a corpus of multiple real-world meta-analyses from public repositories (Cochrane/Campbell). **If no verified machine-readable source is found**, the system defaults to a **Parameterized Simulation** mode using distributions derived from meta-epidemiological literature.
2.  **Subsampling**: Generating bootstrap subsamples (k=3 to N) for each meta-analysis (or simulation instance), logging the specific `k` and random `seed` for every iteration.
3.  **Modeling**: Computing pooled effect sizes using Fixed Effects (FE) and Random Effects (RE) models. **REML is used for k<10, DL for k≥10**, with a parallel sensitivity run using REML across all `k` to check for estimator boundary artifacts.
4.  **Metrics**: Deriving **Reference Agreement Rates** (proportion of subsample CIs containing the full-sample estimate) and **True Coverage Rates** (if simulation mode allows access to the ground truth).
5.  **Threshold Detection**: Fitting a **Parametric 1/sqrt(k) model** (primary) and a Generalized Additive Model (GAM) (secondary) to identify the "diminishing returns" threshold. The final threshold is selected based on model fit (AIC) and derivative stability.
6.  **Validation**: Validating results against the project constitution, ensuring reproducibility, data hygiene, and computational feasibility on CPU-only CI.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `pygam`, `scikit-learn`, `requests`, `tqdm`, `pyyaml`.  
**Storage**: Local filesystem (`data/`, `output/`); CSV/Parquet intermediate formats.  
**Testing**: `pytest` (unit tests for subsampling logic, integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, ~7GB RAM, no GPU).  
**Project Type**: Research Pipeline / Data Analysis Script  
**Performance Goals**: Complete full bootstrap analysis for 50 meta-analyses (or simulation equivalents) within 6 hours on CI.  
**Constraints**: No GPU; memory usage <7GB; strict adherence to `k`-specific RE methods (REML vs DL) with boundary sensitivity check; handling of zero-variance studies.  
**Scale/Scope**: A set of meta-analyses (or simulation instances), up to 100 subsamples per `k`, ~100 `k` values per instance.

> **Critical Feasibility Note**: The spec assumes a set of real-world meta-analyses. If no verified dataset is found (high probability), the project executes in **Simulation Mode**. The research question is then reframed as "Assessing estimator reliability under realistic simulation parameters," and SC-001 is measured against the simulation count, not a real-world corpus.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**:
    *   *Action*: All random seeds will be pinned in `code/` (e.g., `np.random.seed(42)`).
    *   *Action*: External datasets will be fetched via `requests` from canonical URLs; checksums recorded in `state/`.
    *   *Action*: `requirements.txt` will pin exact versions.
    *   *Action*: **Per-iteration seeds** will be logged in `subsample_data.parquet` to ensure every bootstrap sample is reproducible.
2.  **II. Verified Accuracy**:
    *   *Action*: All citations in `research.md` and `paper/` will be validated against primary sources.
    *   *Action*: **For Synthetic Data**: The parameters used to generate synthetic data (heterogeneity, bias) MUST be cited from verified literature (e.g., Ioannidis et al.). The "Verified Accuracy" gate applies to these citations, ensuring the simulation reflects real-world conditions defined by those sources.
3.  **III. Data Hygiene**:
    *   *Action*: Raw data checksummed; derivations written to new files (e.g., `raw_meta.csv` → `subsampled_meta_k3.csv`).
    *   *Action*: PII scan integrated into CI.
4.  **IV. Single Source of Truth**:
    *   *Action*: All figures/statistics in the final report will be generated directly from `data/` artifacts via `code/`.
5.  **V. Versioning Discipline**:
    *   *Action*: Content hashes for artifacts tracked in `state/`.
6.  **VI. Simulation & Subsampling Rigor**:
    *   *Action*: Bootstrap iterations will log `k`, `seed`, and `estimator_type` for every sample.
    *   *Action*: Non-linear stability relationship will be empirically verified via Parametric Fit (1/sqrt(k)) and GAM comparison.
7.  **VII. Model Selection Justification**:
    *   *Action*: Heterogeneity statistics (I², Q) calculated on full datasets to justify FE vs RE.
    *   *Action*: Results presented for both models where heterogeneity is significant.
    *   *Action*: **Estimator Continuity Check**: A parallel analysis using REML for all `k` will be run to ensure the k=10 boundary does not create artificial thresholds.

## Project Structure

### Documentation (this feature)

```text
specs/001-meta-analytic-sample-size/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── subsample.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-529-assessing-the-impact-of-sample-size-on-t/
├── data/
│   ├── raw/                 # Downloaded meta-analysis data (checksummed) or synthetic seed
│   ├── processed/           # Subsampled data, aggregated metrics
│   └── output/              # Plots, final summary CSVs
├── code/
│   ├── __init__.py
│   ├── download.py          # FR-001: Data acquisition (or synthetic generator)
│   ├── subsample.py         # FR-002: Bootstrap generation
│   ├── models.py            # FR-003: FE/RE model fitting (with REML/DL logic)
│   ├── metrics.py           # FR-004, FR-005, FR-009: Stability & Coverage
│   ├── analysis.py          # FR-006, FR-007: Parametric/GAM fitting & threshold detection
│   ├── viz.py               # FR-008: Plot generation
│   └── main.py              # Orchestration script
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to minimize I/O overhead and simplify dependency management for a research pipeline. This aligns with the "Reproducibility" principle by keeping all logic and data paths explicit.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual RE Methods (REML vs DL)** | Spec requires REML for k<10 and DL for k≥10 to ensure stability. | Using a single method (e.g., DL) for all k would violate FR-003 and introduce bias in small-sample stability estimates. |
| **Estimator Continuity Check** | To detect artifacts at the k=10 boundary. | Ignoring the boundary could lead to false threshold detection. |
| **GAM + Parametric Fit** | Spec requires non-linear threshold detection. | A parametric fit (1/sqrt(k)) is statistically more robust for theoretical SE decay; GAM is added as a non-parametric validation. |
| **Chunked Processing** | Memory limit (7GB) vs potential large corpus. | Loading all 50+ meta-analyses with 100 subsamples each into RAM simultaneously would cause OOM errors. |