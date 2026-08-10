# Implementation Plan: Statistical Analysis of GitHub Issue Resolution Times

**Branch**: `001-github-issue-resolution` | **Date**: 2024-01-15 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-github-issue-resolution/spec.md`

## Summary

This feature implements a statistical analysis pipeline for GitHub issue resolution times. The approach prioritizes **data availability** by utilizing the verified HuggingFace dataset `akhousker/github-issues` as the primary source, with a fully implemented **GitHub API fallback** (Phase 0.5) for cases where the HF dataset is unavailable or fails schema validation. The pipeline performs data ingestion, cleaning (excluding invalid timestamps, MAD-based outlier detection), distribution fitting (Log-normal/Weibull), hypothesis testing (Kruskal-Wallis with Westfall-Young permutation for label dependency), and mixed-effects modeling (Linear Mixed-Effects with LME-design-matrix VIF) entirely on CPU-tractable methods within GitHub Actions constraints (≤6h, 7GB RAM). Cross-Validation (SC-004) is performed via 5-fold stratification by repository size.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `datasets`, `numpy`, `matplotlib`, `seaborn`, `requests`  
**Storage**: Local CSV/Parquet files (`data/raw/`, `data/processed/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Data Analysis Pipeline / CLI  
**Performance Goals**: Complete end-to-end analysis (ingest 7k+ rows, fit models, generate plots) in ≤6 hours.  
**Constraints**: CPU-only (no GPU/CUDA), memory ≤7GB, strict adherence to observational/causal disclaimers.  
**Scale/Scope**: [deferred] issues across multiple repositories (based on verified dataset size).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Plan mandates `random_state` pinning in all statistical functions. Data source is a static HF dataset or GitHub API (with fixed pagination). `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | ✅ Pass | Dataset source `akhousker/github-issues` is verified via **Reference-Validator Agent** in Phase 0. All statistical methods (KS, VIF, LME) use standard, well-documented libraries (`scipy`, `statsmodels`). |
| **III. Data Hygiene** | ✅ Pass | Plan specifies checksumming of raw data files. Raw data is never modified; `data/processed/` contains derived artifacts only. |
| **IV. Single Source of Truth** | ✅ Pass | All figures and stats in reports will be generated programmatically from `data/processed/`. No manual typing of numbers. Contract schemas in `contracts/` are consolidated to avoid redundancy. |
| **V. Versioning Discipline** | ✅ Pass | All scripts will include a `__version__` or hash reference. Artifact hashes will be recorded in `state/` upon completion. |
| **VI. Temporal Data Integrity** | ✅ Pass | Timestamps (`created_at`, `closed_at`) will be parsed directly from the dataset/API without post-hoc alteration. Timezone normalization will be deterministic. |
| **VII. Reproducible Feature Engineering** | ✅ Pass | Label extraction, language inference (via API), and feature engineering scripts will be version-controlled and deterministic. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-of-publicly-availab/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Consolidated Schemas)
│   ├── dataset.schema.yaml
│   ├── analysis_output.schema.yaml
│   ├── collinearity.schema.yaml
│   └── sensitivity.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── __init__.py
│   ├── loader.py           # Loads from akhousker/github-issues
│   ├── loader_api.py       # Collects from GitHub API (Fallback)
│   └── cleaner.py          # Filters invalid times, computes resolution_time, MAD outlier flag
├── analysis/
│   ├── __init__.py
│   ├── distribution.py     # ECDF, Log-normal, Weibull fitting
│   ├── hypothesis.py       # Kruskal-Wallis, Westfall-Young, Holm-Bonferroni
│   ├── modeling.py         # LME, VIF (LME-design-matrix), Cross-validation
│   └── viz.py              # Plotting utilities
├── main.py                 # Orchestration script
├── requirements.txt
└── tests/
    ├── test_loader.py
    ├── test_cleaner.py
    ├── test_distribution.py
    └── test_hypothesis.py

data/
├── raw/
│   └── github_issues_raw.parquet
└── processed/
    ├── cleaned_issues.csv
    ├── analysis_results.json
    ├── collinearity_report.json
    └── sensitivity_report.json
```

**Structure Decision**: Single-project structure chosen for simplicity. Separation of `data/` (loading/cleaning) and `analysis/` (statistical logic) ensures modularity and testability. `contracts/` contains the single canonical schema for each artifact type to satisfy Constitution Principle I.

## Complexity Tracking

No complexity violations identified. The plan uses standard CPU-tractable statistical libraries and a verified, small-scale dataset (<100MB) that fits comfortably within the 7GB RAM constraint.

## Phase Breakdown

### Phase 0: Data Strategy & Feasibility (Research)
- **Action**: Confirm `akhousker/github-issues` schema matches requirements (FR-001).
- **Action**: **Reference-Validator Agent** runs to verify dataset citation against primary source (Constitution Principle II).
- **Action**: Verify `created_at`, `closed_at`, `labels`, `assignee`, `comments_count` are present.
- **Action**: Design the log-transformation and MAD-based outlier detection logic (FR-002, US-2).
- **Action**: Design 'Repository Metadata Enrichment' via GitHub API to fetch `language` for repositories in the dataset (to address missing predictor).
- **Deliverable**: `research.md`

### Phase 0.5: GitHub API Fallback Collection (Triggered if HF fails)
- **Action**: Implement `loader_api.py` to collect closed issues from GitHub REST API (`state=closed`, `since=2020-01-01`) for a fixed set of repositories.
- **Action**: Implement rate limit handling (exponential backoff, 60s wait).
- **Action**: Merge API data with HF schema if needed.
- **Trigger**: HF dataset unavailable, schema mismatch, or <1000 issues.
- **Deliverable**: `data/raw/github_issues_raw_api.parquet`

### Phase 1: Data Model & Contracts
- **Action**: Define the `Issue` entity schema.
- **Action**: Define the `AnalysisResult` schema for statistical outputs.
- **Action**: Create YAML contracts for input/output validation (including MAD-based outlier flag).
- **Action**: Consolidate multiple schema drafts into single canonical files in `contracts/` to ensure Single Source of Truth.
- **Deliverable**: `data-model.md`, `contracts/*.schema.yaml`

### Phase 2: Implementation & Execution
- **Action**: Implement `loader.py` to fetch from HF OR `loader_api.py` (if triggered).
- **Action**: Implement `cleaner.py` to filter `resolution_time <= 0`, log invalid entries, and flag outliers via **MAD on log-scale** (US-1, FR-003).
- **Action**: Implement 'Repository Metadata Enrichment' to fetch `language` via GitHub API.
- **Action**: Implement `distribution.py` for ECDF and parametric fitting (US-2, FR-002).
- **Action**: Implement `hypothesis.py` for Kruskal-Wallis with **Westfall-Young permutation** for label dependency and Holm-Bonferroni for independent tests (US-3, FR-004).
- **Action**: Implement `modeling.py` for LME, **VIF on LME design matrix**, and **5-fold Stratified CV by repository size** (US-3, FR-005, FR-006, FR-007, SC-004).
- **Action**: Generate visualizations and final report.
- **Deliverable**: Executable code, `data/processed/` artifacts.

## FR/SC Coverage Matrix

| ID | Requirement | Plan Element |
| :--- | :--- | :--- |
| **FR-001** | Collect from HF or API | `code/data/loader.py` (HF) + `code/data/loader_api.py` (API Fallback). Trigger: HF failure. |
| **FR-002** | Compute resolution time, log-transform | `code/data/cleaner.py` computes `closed - created`, logs, and filters `<=0`. |
| **FR-003** | Exclude invalid timestamps | `code/data/cleaner.py` excludes `closed_at < created_at` or missing. |
| **FR-004** | Holm-Bonferroni correction | `code/analysis/hypothesis.py` applies `statsmodels.stats.multitest.multipletests` (for independent tests) and Westfall-Young (for dependent labels). |
| **FR-005** | Linear Mixed-Effects Model | `code/analysis/modeling.py` uses `statsmodels` `MixedLM` with random intercepts. |
| **FR-006** | VIF & Collinearity | `code/analysis/modeling.py` calculates VIF from **LME fixed effects design matrix**, flags `>=5`, reports descriptive joint relationships. Includes **Dimensionality Reduction** (label grouping <5%). |
| **FR-007** | Sensitivity Analysis | `code/analysis/modeling.py` sweeps thresholds {, 0.05, 0.1} with **Parametric Bootstrap**, reports **Bootstrap Stability Index**. |
| **FR-008** | "Associational" language | All result generation functions append "associational" or "correlational" to text. |
| **FR-009** | ≤6h runtime | CPU-tractable methods on <10k rows ensure execution <1h. |
| **FR-010** | CPU-only | No CUDA/GPU libraries used. |
| **SC-001** | Dataset completeness | `research.md` verifies schema coverage; `cleaner.py` logs completeness %. |
| **SC-002** | Goodness-of-fit (KS) | `distribution.py` reports KS statistic and p-value. |
| **SC-003** | Validity (Adjusted p) | `hypothesis.py` reports adjusted p-values (Westfall-Young/Holm-Bonferroni). |
| **SC-004** | Predictive performance (MAE/R²) | `modeling.py` performs **5-fold Stratified CV by repository size** and reports MAE/R². |
| **SC-005** | Compute feasibility | Verified via `research.md` and runtime logs. |