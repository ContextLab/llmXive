# Implementation Plan: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Branch**: `001-statistical-analysis-of-recipe-data` | **Date**: 2026-07-05 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-statistical-analysis-of-recipe-data/spec.md`

## Summary

This project implements a statistical pipeline to predict culinary compatibility for ingredient substitution. **CRITICAL REFRAME**: Due to the unavailability of verified independent datasets (FlavorDB, Counterfactual Recipe Generation) as required by the original spec, the study is explicitly reframed from a "Causal Independence Test" to a **"Correlational Analysis of Corpus Bias"**. The pipeline ingests the verified Recipe1M corpus, uses its visual/text embeddings as a proxy for "semantic similarity" (replacing FlavorDB chemical vectors), and uses Recipe1M ratings as the outcome variable (replacing independent sensory scores). The methodology acknowledges the inherent circularity (same source for predictor and outcome) and employs partial correlation and data leakage audits to quantify these limitations. The goal is to quantify the associative strength of semantic similarity and functional role *within the corpus*, not to claim causal independence.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyarrow`, `datasets` (Hugging Face), `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `pymc>=5.0.0`.  
**Storage**: Local filesystem (`data/`, `code/`, `docs/`). No external DB.  
**Testing**: `pytest` (unit tests for data processing, integration tests for pipeline phases).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Data Analysis / Statistical Research Pipeline (Correlational).  
**Performance Goals**: Pipeline execution ≤ 6 hours; RAM usage ≤ 7 GB; Bayesian model sample size ≤ 50,000 pairs.  
**Constraints**: No authentication for datasets; streaming required for large files; no synthetic data; **strict acknowledgment of data source circularity**.  
**Scale/Scope**: A large-scale corpus of recipes (streamed/downsampled); A substantial number of unique ingredients; A large-scale dataset of pairs for Bayesian modeling..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates `requirements.txt` pinning, random seed setting (`np.random.seed`, `random.seed`), and checksumming of all raw data files in `data/`.
2.  **II. Verified Accuracy**: All dataset URLs in `research.md` are restricted to the verified list provided in the prompt. The plan explicitly documents the use of **proxies** (Recipe1M embeddings/ratings) for the original required datasets (FlavorDB/Counterfactual) and includes a "Verified Proxy Validation" step to ensure these proxies are the only available verified sources.
3.  **III. Data Hygiene**: Raw data is preserved in `data/raw/`. Derived data is written to `data/processed/` with checksums recorded. No in-place modification.
4.  **IV. Single Source of Truth**: All statistics in the final report trace to `data/processed/` CSVs and `code/` scripts.
5.  **V. Versioning**: Content hashes for artifacts will be recorded in `state/...yaml`.
6.  **VI. Statistical Independence**: **CONSTITUTION EXCEPTION**: The plan explicitly acknowledges that Constitution Principle VI (Statistical Independence) **cannot be satisfied** with the available verified data sources. The study is reframed as a correlational analysis to avoid false causal claims. A "Data Leakage Audit" is included to quantify the shared variance.
7.  **VII. Mechanism-Focused Rigor**: The plan includes a null model (frequency-only) and a model comparison (AIC/BIC) to test if semantic similarity adds predictive value *within the corpus*. A null result is treated as a valid scientific outcome.

## Spec Amendment Proposal

The original Spec (FR-001, FR-004, FR-006, FR-008, SC-001, SC-002) requires datasets (FlavorDB, Counterfactual) that are **not available** in the verified sources list. To proceed, the following amendments are proposed and **implemented in the updated spec.md**:
- **FR-001-AMEND**: Replace "FlavorDB chemical matrix" and "Counterfactual Recipe Generation dataset" with "Recipe1M visual/text embeddings" and "Recipe1M ratings".
- **FR-004-AMEND**: Replace "chemical vectors" with "visual/text embeddings".
- **FR-006-AMEND**: Replace "independent sensory scores" with "Recipe1M ratings", acknowledging circularity.
- **FR-008-AMEND**: Replace "likelihood-ratio test for independent explanatory power" with "partial correlation analysis and leakage-adjusted model comparison (AIC/BIC)".
- **SC-001-AMEND**: Measure "associative strength" (partial correlation) rather than "independent explanatory power".
- **SC-002-AMEND**: Measure "cross-validation performance within the corpus" rather than "generalization to an independent dataset".
- **Assumptions-AMEND**: Remove the assumption that Counterfactual data provides independent scores; explicitly state the use of Recipe1M proxies.

*Implementation will not proceed until these amendments are ratified.*

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-of-recipe-data/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-175-statistical-analysis-of-publicly-availab/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py           # Atomic download scripts (download_recipe1m.py, etc.)
│   │   ├── preprocess.py         # Normalization, co-occurrence, similarity, role derivation
│   │   ├── split.py              # Train/test split with power analysis integration
│   │   └── utils.py              # Helpers (checksum, logging)
│   ├── models/
│   │   ├── logistic.py           # Logistic Regression fitting & model comparison
│   │   ├── bayesian.py           # Hierarchical Bayesian model (PyMC)
│   │   └── diagnostics.py        # VIF, convergence checks, data leakage audit
│   ├── evaluation/
│   │   └── report.py             # Metrics, calibration, final report generation
│   └── run_full_pipeline.py      # Orchestration script
├── data/
│   ├── raw/                      # Downloaded raw files (checksummed)
│   ├── processed/                # Normalized datasets, feature matrices
│   └── logs/                     # Execution logs (pipeline, model, evaluation)
├── docs/
│   ├── draft_final_report.md     # Draft report
│   └── final_report.md           # Final report
├── tests/
│   ├── test_preprocess.py
│   ├── test_models.py
│   └── test_evaluation.py
├── requirements.txt
└── README.md
```

**Structure Decision**: The single-project structure is chosen to minimize complexity for a data analysis pipeline. The separation of `data/`, `models/`, and `evaluation/` ensures modularity while keeping the orchestration simple via `run_full_pipeline.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | The current structure is minimal and sufficient for the statistical pipeline. |

## Task Traceability

- **Phase 1 (Data)**: Tasks T013-T018 (Download, Normalize, Co-occurrence, Similarity, Role) produce `data/processed/ingredient_pairs.csv`.
- **Phase 2 (Model)**: Tasks T022-T025 (Logistic, Bayesian, Diagnostics) produce `data/logs/model_output.json`.
- **Phase 3 (Eval)**: Tasks T029-T032 (Evaluation, Report) produce `docs/final_report.md`.
- **Task Dependencies**: `tasks.md` (Phase 2) will explicitly link these phases to the implementation scripts.