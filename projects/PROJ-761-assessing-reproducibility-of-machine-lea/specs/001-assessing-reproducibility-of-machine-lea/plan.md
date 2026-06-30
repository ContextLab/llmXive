# Implementation Plan: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

**Branch**: `PROJ-761-01-reproducibility` | **Date**: 2026-06-25 | **Spec**: `spec.md`

## Summary

This project implements a reproducible pipeline to audit the performance claims of machine-learned reaction yield models found in scientific literature. The system ingests a manifest of target papers, retrieves their datasets (prioritizing direct links from supplementary materials if verified datasets lack covariates), and re-implements the models in a strictly controlled CPU-only environment (Python 3.x, PyTorch, scikit-learn (latest stable release)). The pipeline computes a normalized **Deviation Index** (per FR-009) for ranking and performs a **Fixed-Effects Meta-Analysis (FEMA)** with inverse-variance weighting (derived from seed sweeps) to assess systematic bias. Reproducibility is tested via **Equivalence Testing (TOST)** against a pre-defined tolerance margin, rather than simple difference testing.

## Technical Context

**Language/Version**: Python 3.x
**Primary Dependencies**: `torch` (CPU wheel), `scikit-learn` 1.5, `pandas`, `numpy`, `rdkit`, `statsmodels`, `matplotlib`, `pyyaml`, `requests`, `equivalence` (for TOST).
**Storage**: Local filesystem (`data/`, `artifacts/`) with checksums; no external database.
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline phases).
**Target Platform**: Linux (GitHub Actions free-tier: CPU, GB RAM, no GPU).
**Project Type**: Computational research pipeline.
**Performance Goals**: Complete per-paper re-implementation within 30 minutes; full meta-analysis within 6 hours.
**Constraints**: No GPU usage; models limited to ≤1M parameters or classical ML; strict dependency pinning; all code must run in a Docker container.
**Scale/Scope**: Processing a manifest of target papers (variable count, but designed for batch processing of ≤20 papers per run).

## Constitution Check

| Principle | Status | Action / Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates Docker container, pinned seeds (default value), and exact dataset versions. Random seed sweep (FR-010) included. |
| **II. Verified Accuracy** | PASS | Phase 0 explicitly includes a "Reference Validation" step invoking the Reference-Validator agent for DOI/URL reachability and title overlap (≥0.7). |
| **III. Data Hygiene** | PASS | All raw data downloads will be checksummed; transformations create new files; no in-place modification. |
| **IV. Single Source of Truth** | PASS | All metrics derived from code output JSONs; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Docker image hash recorded in state; artifact hashes tracked in `state.yaml`. |
| **VI. Dataset Version Fidelity** | PASS | Plan explicitly requires identifying dataset by name AND version (e.g., USPTO-Extract v1.0) and archiving prior versions if updated. |
| **VII. Env Consistency** | PASS | Dockerfile constructed in Phase 0; all experiments run inside this container. |

## Project Structure

### Documentation (this feature)

```text
specs/[PROJ-761-01-reproducibility]/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (JSON Schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-761-assessing-reproducibility-of-machine-lea/
├── data/
│   ├── manifest.yaml          # Input list of papers (must include direct data URLs)
│   ├── raw/                   # Downloaded datasets (checksummed)
│   ├── processed/             # Preprocessed splits
│   └── checksums.json         # Data integrity logs
├── code/
│   ├── __init__.py
│   ├── main.py                # Orchestration entry point
│   ├── ingest.py              # Manifest validation & data fetch (incl. supp. materials)
│   ├── model_runner.py        # Model training & evaluation (CPU)
│   ├── metrics.py             # MAE, R², Spearman, Deviation Index
│   ├── stats.py               # TOST, FEMA, Bland-Altman
│   ├── guidelines.py          # Checklist generation
│   └── requirements.txt       # Pinned dependencies
├── tests/
│   ├── unit/
│   │   ├── test_metrics.py
│   │   └── test_stats.py
│   └── integration/
│       └── test_pipeline.py
├── artifacts/
│   ├── logs/                  # Execution logs, environment details
│   ├── plots/                 # Bland-Altman PNGs
│   └── reports/               # Final JSON summaries and Markdown checklist
├── Dockerfile                 # Reproducible environment
└── state/
    └── projects/PROJ-761-assessing-reproducibility-of-machine-lea.yaml
```

**Structure Decision**: Single project layout (`code/`, `data/`, `tests/`) is selected to minimize overhead for a research pipeline. The separation of `ingest`, `model_runner`, and `stats` ensures modularity while maintaining a linear execution flow required for reproducibility.

## Phase Plan

### Phase 0: Environment, Validation & Data Strategy (Research)
- **Goal**: Validate dataset availability, reference accuracy, and construct the reproducible Docker environment.
- **Steps**:
  1.  **Reference Validation**: Invoke the Reference-Validator agent to check DOI/URL reachability and citation title overlap (≥0.7) for all entries in `data/manifest.yaml`. Fail if validation fails (Constitution Principle II).
  2.  **Dataset Verification**: Confirm dataset contents match required variables (reactant/product SMILES, yield, and covariates).
      -   *Critical*: If the verified dataset (e.g., MAESTRO) lacks required covariates, the system attempts to extract data from the paper's supplementary materials (CSV/Parquet) or GitHub repository as specified in the manifest.
      -   *Exclusion*: If covariates are missing and cannot be retrieved, the paper is flagged as "Data Unavailable" and **excluded** from the quantitative reproducibility score calculation to avoid false negatives.
  3.  **Build Dockerfile**: Construct with Python 3.11, CPU-only PyTorch, scikit-learn (latest version), RDKit (FR-002).
  4.  **Download & Checksum**: Download raw data; verify integrity (Constitution Principle III).

### Phase 1: Data Model & Contracts (JSON Schemas)
- **Goal**: Define strict schemas for inputs and outputs.
- **Steps**:
  1.  Define `PaperManifest` schema (DOI, URL, dataset, reported metrics, direct data URL).
  2.  Define `ReproResult` schema (reproduced metrics, deviations, deviation index, flags, **metric_std**).
  3.  Define `StatSummary` schema (TOST results, FEMA weights, Bland-Altman summaries).
  4.  Generate **JSON Schema** files for validation in `contracts/`.

### Phase 2: Implementation (Re-implementation & Metrics)
- **Goal**: Execute the re-implementation pipeline.
- **Steps**:
  1.  **Model Execution**: Implement `model_runner.py`: Load data, apply preprocessing, train model with pinned seed (default a standard baseline value), evaluate (FR-004, FR-005).
      -   *Substitution Rule*: If a paper's model exceeds 1M parameters or requires unavailable covariates, it is **excluded** from the quantitative analysis and logged as a "Model Substitution/Unavailable" failure mode.
  2.  **Compute Metrics**: Calculate MAE, R², Spearman ρ. Compute the **Deviation Index** (S) as defined in FR-009 (normalized absolute deviations). Note: S is a descriptive ranking metric, not a statistical test.
  3.  **Sensitivity Analysis**: Run seed sweep {, a small set of values, [seed count]} to compute the **maximum standard deviation** (`metric_std`) for each metric. This `metric_std` serves as the variance estimate for the meta-analysis weights (FR-010).
  4.  **Log Environment**: Record Python version, library versions, OS, Docker image hash (FR-012).

### Phase 3: Statistical Meta-Analysis
- **Goal**: Aggregate results and test for systematic bias using appropriate statistical methods.
- **Steps**:
  1.  **Aggregate Results**: Collect `ReproResult` objects for all included papers.
  2.  **Normality Check**: Perform Shapiro-Wilk test on metric differences. If p < 0.05, use non-parametric bootstrap for equivalence testing.
  3.  **Equivalence Testing (TOST)**: Perform Two One-Sided Tests (TOST) for each metric against a pre-defined tolerance margin (delta). The null hypothesis is "non-equivalence". Report p-values and confidence intervals (FR-006).
  4.  **Fixed-Effects Meta-Analysis (FEMA)**:
      -   Calculate inverse-variance weights using `metric_std` from the seed sweep.
      -   Compute pooled effect size (mean deviation) and heterogeneity (I² statistic).
      -   *Note*: Do not model "preprocessing version" or "library version" as fixed effects; the environment is constant. Do not model "seed" as a fixed effect; its variance is captured in the weights.
  5.  **Bland-Altman Plots**: Generate plots for each metric (FR-007).
  6.  **Qualitative Failure Log**: Compile a log of excluded papers (model substitution, data gaps) for the guideline synthesis.

### Phase 4: Guideline Synthesis & Reporting
- **Goal**: Generate actionable community guidelines.
- **Steps**:
  1.  Analyze failure modes (missing seeds, version mismatches, data gaps).
  2.  Synthesize checklist with citations to guidelines and failure logs (FR-011).
  3.  Compile final report including Deviation Index rankings and Equivalence Test results.

## Compute Feasibility
- **Hardware**: Runs on GitHub Actions free tier (multi-core CPU, 7GB RAM).
- **Strategy**:
  - No GPU training.
  - Models restricted to ≤1M parameters or classical ML (Random Forest, Gradient Boosting, shallow NN).
  - Data subset to fit memory; if a paper's model is too large, it is excluded from quantitative analysis (not substituted).
  - Total runtime target: <6 hours.

## Statistical Rigor & Methodology
- **Equivalence Testing**: Uses TOST with pre-defined tolerance (delta) to test if deviation is within acceptable bounds, avoiding the circularity of treating reported values as fixed constants.
- **Multiple Comparisons**: Bonferroni correction applied to TOST p-values (FR-006).
- **Power**: Sample size (n papers) determined by available literature; power limitation acknowledged if n < 30.
- **Causal Inference**: Observational study; claims framed as associational. No causal claims about model superiority.
- **Collinearity**: If predictors are definitionally related, descriptive reporting only; no independent effect claims.
- **Measurement Validity**: Instruments (MAE, R²) are standard; validation relies on standard library implementations.
- **Variance Estimation**: Per-paper variance is estimated via the seed sweep (standard deviation) and used for inverse-variance weighting in the meta-analysis.