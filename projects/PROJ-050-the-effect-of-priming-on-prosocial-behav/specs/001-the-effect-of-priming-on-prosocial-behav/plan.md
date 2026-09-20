# Implementation Plan: The Effect of Priming on Prosocial Behavior (Association Study)

**Branch**: `050-priming-prosocial-behavior` | **Date**: 2026-06-25 | **Spec**: `specs/050-priming-prosocial-behavior/spec.md`
**Input**: Feature specification from `specs/050-priming-prosocial-behavior/spec.md`

## Summary

This project implements a computational study to test the **association** between "priming" (exposure to prosocial keywords in thread titles) and the prosocial language used in Reddit comments. The technical approach involves:
1.  **Ingestion**: Fetching historical Reddit data from the verified HuggingFace dataset `jplu/tf-reddit-comments-2020` for specific subreddits (r/AskReddit, r/science, r/relationships) between 2020-2023.
2.  **Anonymization**: Hashing user IDs and removing raw timestamps (keeping only derived `user_tenure`) to comply with Constitution Principle VII (Privacy).
3.  **Scoring**: Computing VADER sentiment and counting prosocial keywords to generate the dependent variable.
4.  **Validation**: Comparing automated scores against a simulated dual-blind human annotation sample (N=200) to report Cohen's Kappa.
5.  **Analysis**: Fitting a **Generalized Linear Mixed Model (GLMM)** with a Poisson/Negative Binomial link to test the hypothesis, verifying convergence, and exporting results.

*Note on Causal Language*: This is an observational study. We test for an **association**, not a causal "effect". The "priming" is inferred from the title, not experimentally assigned. Selection bias (users who choose 'Prime' threads may already be prosocial) is acknowledged as a limitation.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels` (for GLMM), `nltk` (for VADER), `requests`, `datasets` (HuggingFace), `pyyaml`, `pytest`.
**Storage**: Local CSV/JSON files in `data/` (raw, processed, annotated).
**Testing**: `pytest` with unit tests for classification logic, anonymization, and data integrity.
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7GB RAM).
**Project Type**: Data analysis pipeline / Research script.
**Performance Goals**: Process ~100k+ comments within 6 hours on CPU; GLMM convergence within reasonable iterations.
**Constraints**: No local GPU; data must be streamed or sampled to fit 7GB RAM; strict PII removal.
**Scale/Scope**: Target N >= 4,000 comments per group (Prime/Control); total dataset size depends on API availability.

> **Dataset Source**: The plan utilizes the verified HuggingFace dataset `jplu/tf-reddit-comments-2020` (or the most recent verified equivalent containing `link_title`) to ensure CI reproducibility (Constitution Principle I). If the dataset lacks `author_created_utc`, a proxy (first comment date) will be used with explicit limitation reporting.

## Constitution Check

*Gates determined based on `constitution.md`*

- [x] **I. Reproducibility**: Plan defines pinned `requirements.txt`, fixed random seeds, and deterministic data fetching from `jplu/tf-reddit-comments-2020`.
- [x] **II. Verified Accuracy**: All dataset URLs and method citations in `research.md` will be drawn *only* from the verified sources list.
- [x] **III. Data Hygiene**: Plan includes checksumming of raw data (`data/raw/`) and ensures no in-place modification; derivations go to `data/processed/`.
- [x] **IV. Single Source of Truth**: Output JSON/PNG will be generated programmatically from the final dataframe; no hand-typed numbers.
- [x] **V. Versioning Discipline**: Plan includes content hashing logic for artifacts.
- [x] **VI. Measurement Validity**: Plan includes a specific validation phase (US2) computing Cohen's Kappa against human annotations (simulated for CI, manual for real) and storing results in `code/validation/`.
- [x] **VII. Participant Privacy**: Plan explicitly includes SHA-256 hashing of `user_id` and removal of raw `created_utc` timestamps before writing to `data/processed/` (only derived `user_tenure` is kept).

## Project Structure

### Documentation (this feature)

```text
specs/050-priming-prosocial-behavior/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/
├── code/
│   ├── 01_ingest.py             # Fetch, filter, hash, save raw/processed
│   ├── 02_score.py              # VADER, keyword count, validation logic
│   ├── 03_analyze.py            # GLMM fitting, convergence check, export
│   └── validation/
│       └── 01_human_annotation.py # Script to generate/compare human sample
├── data/
│   ├── raw/                     # Downloaded dataset shards (checksummed)
│   ├── processed/
│   │   ├── anonymized.csv       # Cleaned, hashed data
│   │   ├── scored.csv           # Data with VADER/Keyword counts
│   │   └── raw_counts.json      # N counts per group
│   └── annotations/             # Human annotation sample (N=200)
├── tests/
│   ├── unit/
│   │   ├── test_classification.py # T011: Regex and classification logic
│   │   ├── test_anonymization.py  # T012: Hashing and PII removal
│   │   └── test_feasibility.py    # T015b: CPU feasibility check
│   └── integration/
│       └── test_pipeline.py       # End-to-end check
├── artifacts/
│   ├── results.json             # Final model stats
│   └── figures/
│       └── glmm_plot.png         # Visualization
└── requirements.txt
```

**Structure Decision**: Single-project structure selected. All data processing and analysis scripts reside in `code/` to ensure a linear, reproducible pipeline. Unit tests are isolated in `tests/unit/` to satisfy T011, T012, and T015b requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| GLMM (Mixed Effects) | Required by FR-003 to account for nested data (comments within users/subreddits) and to handle count data (Poisson/Negative Binomial) correctly. | Standard LMM assumes Gaussian residuals, which is invalid for count data with many zeros. |
| Dual-Blind Validation | Required by US2 and Constitution Principle VI for measurement validity. | Automated scoring alone is insufficient for psychological research; human ground truth is needed for Kappa. |
| SHA-256 Hashing | Required by Constitution Principle VII for privacy. | Simple obfuscation (e.g., truncation) is reversible or insufficient for anonymization standards. |