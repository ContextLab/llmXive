# Implementation Plan: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Branch**: `001-visual-priming-implicit-attitudes` | **Date**: 2024-05-24 | **Spec**: `specs/001-the-influence-of-visual-priming-on-impli/spec.md`

## Summary

This feature implements a computational pipeline to analyze the influence of visual priming on Implicit Association Test (IAT) response times using secondary data. The approach involves ingesting public IAT datasets containing **visual stimuli** (faces), deriving missing prime valence scores via CPU-optimized **Valence-Arousal-Dominance (VAD) regression models**, and fitting linear mixed-effects models (LMM) to test for associational effects. 

**Critical Design Changes**: 
1. **Visual Data Requirement**: The pipeline strictly requires a dataset containing actual image files. Text-only datasets are rejected.
2. **Ambiguity Derivation**: Ambiguity is NO longer derived from model confidence or synthetic generation. It requires **human-rated data** from a verified external source. If unavailable, the analysis is scoped to "valence only" or halted to preserve construct validity.
3. **Statistical Identifiability**: The analysis unit is **aggregated to the Stimulus level** (mean response time per stimulus per participant) to ensure within-stimulus variance exists for fixed effects, or the model is specified as `mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)`. The `stimulus_id` is NOT included as a random effect to avoid collinearity with stimulus-level predictors.
4. **Confounding Check**: A dedicated step verifies that the "prime" variable is not confounded with trial order or block structure before modeling.
5. **Valence Model Specificity**: The plan explicitly requires VAD-specific regression models, rejecting discrete emotion classifiers to avoid arbitrary mapping errors.

The pipeline strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and the distinction between prime and target stimuli, while operating within the constraints of a CPU-only GitHub Actions runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels` (for LMM), `scikit-learn` (for preprocessing), `torch` (CPU-only backend, pinned via `--index-url https://download.pytorch.org/whl/cpu`), `requests`, `pyyaml`, `pillow`.  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `data/primes/`, `data/targets/`, `state/`).  
**Testing**: `pytest` (unit tests for data ingestion logic, integration tests for model fitting on sample data).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Complete data ingestion and preprocessing within 30 minutes; model fitting on full dataset within 4 hours.  
**Constraints**: CPU-only (no CUDA); RAM ≤ 7GB (requires data chunking or sampling if dataset exceeds limits); disk ≤ 14GB; no PII in outputs.  
**Scale/Scope**: Analysis of public IAT datasets (estimated N trials ~kk); generation of one PDF report and one set of interaction plots.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/`; `requirements.txt` pins versions (including CPU-only torch); data fetched from canonical HF/OSF URLs; `code/` runs end-to-end in isolated venv. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` and `paper/` will be validated against primary sources; dataset URLs strictly limited to the "Verified datasets" block (real, reachable URLs only). |
| **III. Data Hygiene** | **Pass** | Checksums recorded in `state/`; raw data preserved; derivations written to new files; PII scan integrated into CI. |
| **IV. Single Source of Truth** | **Pass** | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in reports. `data/processed/stimulus_metadata.csv` is the single source for derived metrics. |
| **V. Versioning Discipline** | **Pass** | `state/projects/<PROJ-ID>/state.yaml` maintained with content hashes and timestamps. Pipeline updates this file on every artifact write. The `state/` directory is explicitly defined in the project structure. |
| **VI. Distinct Stimulus Set Integrity** | **Pass** | Pipeline explicitly separates `data/primes/` and `data/targets/`; no merging prior to final modeling step. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-influence-of-visual-priming-on-impli/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (schemas)
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point
├── config.py            # Paths, seeds, constants
├── data/
│   ├── __init__.py
│   ├── ingest.py        # Data ingestion (US-1) + Confounding Check
│   ├── preprocess.py    # Derivation of valence (FR-002) only
│   └── integrity.py     # Distinct set validation (Principle VI)
├── models/
│   ├── __init__.py
│   ├── lmm.py           # Linear Mixed-Effects modeling (US-2)
│   └── metrics.py       # VIF, effect sizes, sensitivity analysis (FR-005, FR-006)
├── viz/
│   ├── __init__.py
│   └── plots.py         # Interaction plots, coefficient tables (US-3)
└── reports/
    └── generate_report.py # PDF generation (US-3)

tests/
├── unit/
│   ├── test_ingest.py
│   └── test_preprocess.py
└── integration/
    └── test_modeling.py

data/
├── raw/                 # Downloaded datasets (checksummed)
├── processed/           # Cleaned, linked CSVs
│   ├── linked_trials.csv
│   └── stimulus_metadata.csv  # Single source for derived metrics
├── primes/              # Prime stimulus images (if available)
└── targets/             # Target stimulus images (if available)

state/
└── projects/
    └── PROJ-345-the-influence-of-visual-priming-on-impli/
        └── state.yaml   # Versioning and checksums (Principle V)
```

**Structure Decision**: Single project structure chosen to maintain tight coupling between data processing, modeling, and reporting. The `state/` directory is explicitly defined to satisfy Constitution Principle V. The `data/processed/stimulus_metadata.csv` is the single source for derived metrics (Principle IV). The separation of `data/primes/` and `data/targets/` directories explicitly enforces Principle VI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **CPU-only VAD Model** | Required for FR-002 (derive valence) in a CPU environment, specifically using VAD regression to avoid discrete mapping errors. | GPU-accelerated models or discrete emotion classifiers (e.g., ResNet18 on FER-2013) are excluded due to CI constraints or construct validity failures (arbitrary mapping). |
| **LMM without Stimulus Random Effect** | Required to avoid perfect collinearity between derived stimulus predictors (valence/ambiguity) and random intercepts. | Including `stimulus_id` as a random effect would make fixed effects unidentifiable. |
| **Human-Rated Ambiguity Requirement** | Required for construct validity (rejecting model-confidence proxy and synthetic generation). | Using model confidence or synthetic generation as ambiguity is a construct validity failure (low confidence != ambiguity; synthetic = circular). |
| **Confounding Check** | Required to ensure "prime" is not confounded with trial order/block. | Ignoring confounding would lead to spurious "priming" effects driven by practice effects. |
| **Stimulus-Level Aggregation** | Required to ensure within-stimulus variance for fixed effects estimation. | Using trial-level data with stimulus-level predictors without aggregation leads to unidentifiable fixed effects. |
