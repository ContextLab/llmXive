# Implementation Plan: The Influence of Chatbot Politeness on User-Perceived Quality

**Branch**: `001-chatbot-politeness-trust` | **Date**: 2026-06-26 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-chatbot-politeness-trust/spec.md`

## Summary

This project investigates the association between linguistic politeness in chatbot responses and user-perceived quality (trust) using the **HCI_P2** dataset (YCAI3/HCI_P2) as the primary source, which explicitly contains `trust_rating` (1-5 Likert) as its outcome variable. The technical approach involves downloading this dataset, computing mean politeness scores per conversation using the `jfiedler/politeness-bert` model, and fitting a Cumulative Link Mixed-Effects Model (CLMM) to test the hypothesis `trust_rating ~ politeness + conversation_length + (1|user_id)`. Robustness checks will be performed using the `polite` library (as a fallback for the unavailable LIWC-2015) and subgroup analyses using interaction terms. The pipeline is designed to run on GitHub Actions free-tier runners (CPU-first) with a scaled-down GPU escape hatch for the BERT inference if necessary.

## Technical Context

**Language/Version**: Python 3.11 (Primary), R 4.3+ (for CLMM via `rpy2` or separate R script)  
**Primary Dependencies**: `transformers`, `datasets`, `scikit-learn`, `statsmodels`, `lme4` (via R), `ordinal` (via R), `polite` (Python), `pandas`, `pyyaml`, `ruff`, `black`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/models`), CSV/Parquet formats  
**Testing**: `pytest` (Python), `testthat` (R), Contract tests via `schema_validator.py`  
**Target Platform**: GitHub Actions free-tier (2 CPU, ~7 GB RAM, ~14 GB disk, Linux)  
**Project Type**: Data Science / Statistical Analysis Pipeline  
**Performance Goals**: Full pipeline execution ≤ 6 hours; Memory peak ≤ 6 GB; Model convergence ≥ 95%  
**Constraints**: No local GPU on CI; CPU-first execution; Fallback to scaled-down GPU on Kaggle if BERT inference fails or exceeds time limits; No unverified dataset URLs; Adherence to Constitution Principles (Reproducibility, Data Hygiene, Verified Accuracy).  
**Scale/Scope**: One primary dataset (HCI_P2); A large-scale dataset of dialogues, depending on filtering, will be collected.; A primary model, robustness model, up to 4 subgroup models (via interaction terms).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt`/`pyproject.toml` pinning, random seed fixing, and CI execution. |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset citations to the "Verified datasets" block. **HCI_P2** is verified via Hugging Face Hub. Persona-Chat is excluded if unverified. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming (`data_integrity.py`), raw data preservation, and PII scanning. |
| **IV. Single Source of Truth** | **PASS** | **`data/processed`** is explicitly designated as the Single Source of Truth (SSoT) for all statistics. All statistics trace to `data/processed` CSVs; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes; `state` file updated on change. |
| **VI. Psychometric Measurement Validity** | **PASS** | Plan explicitly names the **Trust Rating** scale used in **HCI_P2** (YCAI3/HCI_P2 dataset documentation) as the outcome variable and cites its source. |
| **VII. Linguistic Feature Extraction Consistency** | **PASS** | Plan mandates `jfiedler/politeness-bert` (version pinned) for all utterances; fallback to `polite` library documented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-chatbot-politeness-trust/
├── plan.md              # This file (Phase 0/1)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (generated in Phase 1)
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
data/
├── raw/                  # Downloaded raw datasets (HCI_P2)
├── processed/            # Cleaned, scored, and merged datasets (SSoT)
└── models/               # Serialized models (if needed) and logs

code/
├── utils/
│   ├── schema_validator.py
│   ├── data_integrity.py
│   └── r_runner.py       # Helper to run R scripts from Python
├── data/
│   ├── download_datasets.py
│   ├── validate_data.py
│   └── score_politeness.py
├── analysis/
│   ├── run_clmm.py       # Main CLMM fitting (Python/R interface)
│   ├── robustness_check.py
│   └── subgroup_analysis.py
└── main.py               # Pipeline orchestrator

tests/
├── contract/             # Schema validation tests
├── unit/                 # Unit tests for scoring, validation
└── integration/          # End-to-end pipeline tests

docs/
└── ...

state/
└── projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml
```

**Structure Decision**: Single project structure with clear separation of `data` (raw/processed), `code` (utils/data/analysis), and `tests`. This aligns with the Constitution's requirement for reproducibility and the specific need to separate raw data from derived artifacts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| R/Python Interop (rpy2 or separate R script) | CLMM (`ordinal` package) is best implemented in R; Python's `statsmodels` lacks full CLMM support with random effects. | Pure Python implementation would require a custom MCMC or approximation, risking statistical validity and convergence. |
| GPU Escape Hatch (Kaggle) | `jfiedler/politeness-bert` inference on ~50k dialogues may exceed 6h on 2 CPU cores. | Running a synthetic stand-in for politeness scores violates the "Data Hygiene" and "Verified Accuracy" principles (fabrication). The plan uses the real model on GPU if CPU fails, enforced by `contracts/output.schema.yaml` metadata checks. |
| Fallback Classifier (`polite`) | LIWC-2015 is commercial/proprietary and not available via the verified datasets block. | Hard-failing the pipeline on LIWC acquisition contradicts the spec's fallback logic. The `polite` library is an open-source, valid substitute for lexicon-based scoring. |

## Task Ordering & Dependencies (Addressing Panel Concerns)

- **T018 (Transform) -> T019 (Merge)**: T019 explicitly lists T018 as a hard dependency. T018 produces transformed files; T019 merges them. T018 is not marked as parallelizable in the final execution flow to ensure data integrity.
- **T032a (LIWC/Polite)**: Re-scoped. The task attempts LIWC first. If LIWC fails (expected), it immediately attempts the `polite` library. It does **not** abort the pipeline. The dependency chain reflects this fallback logic.
- **T033b (Generate Metrics)**: Explicitly depends on T029 (Consolidate Results) and T033 (Re-fit CLMM). The risk of blocking is acknowledged, and T029 is strictly sequential.
- **T007b (Checksums)**: Clarified as a sequential step following T007, even if T007 is parallelizable in other contexts.
- **T012 (Gate) -> T034**: T034 explicitly states `Dependency: T012 (Gate Pass)`.

## Compute Feasibility & Escape Hatch

- **CPU-First Strategy**:
  - Data download and filtering: `pandas`/`datasets` (streaming).
  - Politeness Scoring: `jfiedler/politeness-bert` in `float32` or `int8` (if supported) on CPU. Batch size tuned to fit 6GB RAM.
  - CLMM: R `lme4`/`ordinal` (CPU optimized).
- **GPU Escape Hatch**:
  - If CPU inference of BERT exceeds a reasonable duration or OOMs, the pipeline will auto-offload to a Kaggle GPU (sufficient VRAM).
  - **Scaling**: Use `device="cuda"`, `load_in_8bit=True`, and a batch size of -64.
  - **Note**: No synthetic CPU approximation of BERT will be used; the real model runs on the GPU. The output schema (`contracts/output.schema.yaml`) will enforce metadata indicating the compute device used.

## Addressing Unresolved Panel Concerns

1.  **Dataset Validity (HCI_P2)**: The plan now uses **HCI_P2** (YCAI3/HCI_P2) as the primary dataset, which explicitly contains `trust_rating`. This resolves the construct validity issue of using EmpatheticDialogues.
2.  **Hierarchy Check**: A mandatory step verifies multiple dialogues per user. If not present, the model switches to CLM (no random effects).
3.  **Fallback Classifier**: Replaced `textstat` with `polite` library for valid politeness scoring.
4.  **Collinearity**: Explicit VIF check and centering of `conversation_length`.
5.  **Robustness Metric**: Focus on coefficient consistency, not just raw score correlation.
6.  **FR-005 (LIWC)**: Formally acknowledged as unavailable; `polite` library is the approved substitute.
7.  **FR-001 (Persona-Chat)**: Treated as secondary. Attempted download; excluded if unverified or lacking trust metrics.
8.  **SC-003/SC-004 Measurement**: Explicit tasks to generate `convergence_report.csv` and `robustness_metrics.csv`.
9.  **SSoT**: `data/processed` is explicitly designated as the Single Source of Truth.
10. **Constitution VI**: Explicitly names the Trust Rating scale from HCI_P2.

## References

- **Datasets**: HCI_P2 (YCAI3/HCI_P2) via Hugging Face Hub.
- **Models**: `jfiedler/politeness-bert` (Hugging Face Hub).
- **Statistical Methods**: Christensen, R. H. B. (2015). *ordinal - Regression Models for Ordinal Data*. R package version 2015.6-28.
- **Libraries**: `polite` (Python) for lexicon-based politeness.