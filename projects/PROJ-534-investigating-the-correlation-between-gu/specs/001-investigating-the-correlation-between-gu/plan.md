# Implementation Plan: Pipeline Validation Study: Gut Microbiome & Cognitive Flexibility Analysis

**Branch**: `001-gut-microbiome-cognitive-flexibility` | **Date**: 2024-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-gut-microbiome-cognitive-flexibility/spec.md`
**Status**: **Amended Scope** (Pipeline Validation Study)

## Summary

**Critical Scope Note**: The original spec assumed the availability of UK Biobank 16S rRNA and cognitive data. **Research has confirmed no verified source exists for this specific linked dataset.** Consequently, this project has been amended to a **Pipeline Validation Study**. The objective is no longer to investigate the biological correlation (which requires real data), but to **validate the statistical pipeline** using a synthetic dataset generated under a **Null Hypothesis** (zero correlation). This ensures the code correctly handles data ingestion, diversity calculation, and statistical testing (returning non-significant results when no effect exists) before real data becomes available.

The approach involves ingesting synthetic 16S rRNA sequencing data and cognitive assessment data, filtering for the target demographic (age >= 65), calculating diversity metrics, and performing correlation/regression analysis. The pipeline is designed to run on CPU-only CI with strict memory constraints.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `statsmodels`, `biom-format`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`
**Storage**: Local CSV/Parquet files in `data/` (derived from **synthetic generator output**)
**Testing**: `pytest` (unit tests for data filtering, statistical assertions, null hypothesis validation)
**Target Platform**: Linux (GitHub Actions free-tier runner: standard CPU allocation, 7GB RAM)
**Project Type**: Data analysis pipeline / Scientific computing library (Validation Mode)
**Performance Goals**: Complete full analysis pipeline within 6 hours on CPU-only runner; memory usage < 7GB.
**Constraints**: No GPU usage; no deep learning models; dataset must be sampled if raw size exceeds RAM; all statistical tests must handle zero-variance cases gracefully.
**Scale/Scope**: Cohort size ranging from moderate to large (synthetic); S features a synthetic community with a moderate to high diversity of OTUs/ASVs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**: The plan mandates pinned `requirements.txt` and fixed random seeds in all scripts. The **Synthetic Generator Script + Seed** acts as the canonical source for this validation phase to ensure re-generability.
2.  **Verified Accuracy**: All citations in `research.md` are validated. **No fabricated URLs** are used. The plan explicitly acknowledges the *absence* of a verified real-world dataset for the specific linked modality, adhering to the principle by not inventing one.
3.  **Data Hygiene**: The plan includes steps for checksumming the synthetic generator output and writing derived data to new files with documented derivation steps. PII scanning is enforced via the `contracts/` schema.
4.  **Single Source of Truth**: The **Synthetic Generator + Seed** is the Single Source of Truth for this validation phase. All statistical outputs are generated programmatically from this source. The Spec's assumption of UK Biobank data is formally flagged as false and requires amendment.
5.  **Versioning Discipline**: The plan structure supports content hashing of `code/` and `data/` artifacts.
6.  **Microbiome Pipeline Integrity**: The plan specifies the use of standard, CPU-tractable diversity calculation methods (Shannon, Simpson, Bray-Curtis) and requires preserving the synthetic feature tables to ensure alpha/beta diversity calculations are reproducible.
7.  **Covariate Transparency**: The linear regression model explicitly includes age, sex, BMI, dietary fiber, and antibiotic use as covariates, with sensitivity analysis steps planned to test confounding robustness.

## Project Structure

### Documentation (this feature)

```text
specs/001-gut-microbiome-cognitive-flexibility/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml       # Enforced by Ingestion Task
│   └── analysis_output.schema.yaml # Enforced by Analysis Task
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── ingestion.py       # FR-001 (Modified: Synthetic Gen), FR-002
│   ├── filtering.py       # FR-002
│   └── synthetic_gen.py   # New: Null Hypothesis Data Generator
├── analysis/
│   ├── diversity.py       # FR-003 (Alpha & Beta)
│   ├── correlation.py     # FR-004, FR-005 (Alpha Correlation, Regression)
│   └── beta_diversity.py  # FR-005 (PERMANOVA/db-RDA)
├── viz/
│   └── plots.py           # FR-006
├── power/
│   └── estimation.py      # FR-007 (A priori)
├── sensitivity/
│   └── confounding.py     # New: E-value / Negative Control
├── utils/
│   └── config.py          # Random seeds, paths
└── main.py                # Orchestration

tests/
├── unit/
│   ├── test_filtering.py
│   ├── test_diversity.py
│   └── test_null_hypothesis.py # Validates pipeline returns p > 0.05
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py    # Validates dataset.schema.yaml & analysis_output.schema.yaml

data/
├── raw/                   # Synthetic generator output (checksummed)
├── processed/             # Filtered, merged datasets
└── results/               # Statistical outputs, plots

requirements.txt
```

**Structure Decision**: Single project structure selected to minimize overhead and simplify data passing between modules. The `src/` directory isolates logic, `data/` separates raw and processed artifacts, and `tests/` ensures contract compliance. This aligns with the CPU-only constraint by keeping the codebase lean and avoiding complex service orchestration.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly bounded by the spec (correlation/regression) but adapted for validation. | A full Bayesian pipeline or causal inference framework would exceed CPU/RAM limits and is not required for pipeline validation. |

## Task Breakdown

### Phase 0: Spec Amendment & Data Strategy
- **Task 0.1**: Formalize Spec Amendment. Document that FR-001 (UK Biobank ingestion) is unmet and replaced by Synthetic Generation.
- **Task 0.2**: Define Synthetic Data Generation Logic. Ensure `cognitive_flexibility_score` and `shannon_diversity` are **independent** (Null Hypothesis) to validate pipeline detection of no effect.

### Phase 1: Data Ingestion & Filtering
- **Task 1.1**: Implement `src/data/synthetic_gen.py`. Generate data adhering to `contracts/dataset.schema.yaml`.
- **Task 1.2**: Implement `src/data/ingestion.py`. Load synthetic data.
- **Task 1.3**: Implement `src/data/filtering.py`. Filter for age >= 65 and non-null values (FR-002). Validate output against `contracts/dataset.schema.yaml`.

### Phase 2: Diversity & Statistical Analysis
- **Task 2.1**: Implement `src/analysis/diversity.py`. Calculate Alpha (Shannon, Simpson, Chao1) and Beta (Bray-Curtis, UniFrac) metrics (FR-003).
- **Task 2.2**: Implement `src/analysis/correlation.py`. Perform Pearson/Spearman correlation (FR-004) and Linear Regression (FR-005) with covariates. Apply Benjamini-Hochberg correction.
- **Task 2.3**: Implement `src/analysis/beta_diversity.py`. Perform PERMANOVA or db-RDA using **continuous** cognitive scores (FR-005), avoiding arbitrary quartile binning.
- **Task 2.4**: Implement `src/power/estimation.py`. Perform **A priori** power analysis based on literature-derived effect sizes for simulation design (FR-007).

### Phase 3: Sensitivity & Validation
- **Task 3.1**: Implement `src/sensitivity/confounding.py`. Calculate E-values or perform negative control tests by injecting known confounders to test model robustness (Methodology Concern).
- **Task 3.2**: Run Null Hypothesis Validation. Verify that the pipeline returns p > 0.05 for the independent variables.
- **Task 3.3**: Generate Visualizations (FR-006).

### Phase 4: Reporting
- **Task 4.1**: Aggregate results into `data/results/statistical_results.json` (valid against `contracts/analysis_output.schema.yaml`).
- **Task 4.2**: Generate final validation report.

## Contract Enforcement

- **Ingestion Task**: Must validate output against `contracts/dataset.schema.yaml`.
- **Analysis Task**: Must validate output against `contracts/analysis_output.schema.yaml`.
- **Test Suite**: `tests/unit/test_null_hypothesis.py` ensures the pipeline correctly identifies no correlation when data is independent.

## Constitution Check (Re-verified)

- **Reproducibility**: Seeds pinned in `synthetic_gen.py`.
- **Verified Accuracy**: No fabricated URLs; synthetic data acknowledged as the source.
- **Data Hygiene**: Synthetic output checksummed.
- **SSoT**: Synthetic Generator is the SSoT for this phase; Spec assumption flagged for amendment.
- **Microbiome Integrity**: Standard metrics used.
- **Covariate Transparency**: All covariates included; sensitivity analysis added.