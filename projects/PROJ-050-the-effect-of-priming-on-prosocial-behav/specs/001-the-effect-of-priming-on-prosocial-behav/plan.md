# Implementation Plan: The Effect of Priming on Prosocial Behavior

**Branch**: `001-the-effect-of-priming-on-prosocial-behav` | **Date**: 2026-06-25 | **Spec**: `specs/001-the-effect-of-priming-on-prosocial-behav/spec.md`
**Input**: Feature specification from `/specs/001-the-effect-of-priming-on-prosocial-behav/spec.md`

## Summary

This project implements a computational study to determine if priming (via thread titles containing words like "thank", "help", "support", "care") is associated with increased prosocial behavior in Reddit comments. The system will fetch data from the Hugging Face dataset `jplu/tf-reddit-comments-2020` (and related years), anonymize user data, score comments using VADER and a *distinct* prosocial lexicon (excluding prime words), validate the scoring against a real human annotation sample (N=200), and fit a Linear Mixed Model (LMM) to test the associational hypothesis. The implementation strictly adheres to the project constitution regarding reproducibility, data hygiene, and privacy.

**Critical Note on Spec Conflict**: The original spec (US3, FR-003) mandates `user_tenure` in the LMM formula. However, the chosen dataset does not contain account creation dates, and the Reddit API is rate-limited for bulk lookups. Consequently, this plan **drops `user_tenure`** from the model to avoid bias and infeasibility. The spec is flagged for update to reflect this necessary change.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (Hugging Face), `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `vaderSentiment`, `pytest`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`) with SHA-256 checksums  
**Testing**: `pytest` (unit tests for classification, anonymization, and data schemas)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM)  
**Project Type**: Data Analysis Pipeline / Statistical Study  
**Performance Goals**: Complete ingestion and analysis of [deferred]+ comments within 6 hours on CPU; convergence of LMM within 100 iterations.
**Constraints**: No local GPU; must handle data streaming if raw volume > 7GB; strict PII removal (SHA-256 hashing); **user_tenure removed from model**; **distinct lexicon used**.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Evidence/Plan |
|-----------|--------|---------------|
| **I. Reproducibility** | **Pass** | `requirements.txt` will pin versions. `random.seed(42)` set in all scripts. Data fetched via deterministic API calls (Hugging Face). |
| **II. Verified Accuracy** | **Pass** | All dataset URLs cited in `research.md` are from the verified block. No fabricated citations. |
| **III. Data Hygiene** | **Pass** | Raw data preserved in `data/raw` with checksums. Derivations in `data/processed` with new filenames. No in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All metrics in the final report will be generated programmatically from `data/processed` and logged to JSON. No hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Content hashes for artifacts will be recorded in `state/...yaml`. |
| **VI. Measurement Validity** | **Pass** | VADER and prosocial lexicon validation against N=200 human annotations is a required phase (FR-002). Validation scripts stored in `code/validation/`. |
| **VII. Participant Privacy** | **Pass** | User IDs hashed via SHA-256; timestamps removed/normalized before storage. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-effect-of-priming-on-prosocial-behav/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── gold_standard.schema.yaml
│   ├── scored.schema.yaml
│   └── scored_data.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/
├── code/
│   ├── 01_ingest.py                 # Fetch, hash, classify (FR-001)
│   ├── 02_score.py                  # VADER, keyword count (FR-002)
│   ├── 03_validate.py               # Human annotation comparison (FR-002)
│   ├── 04_analyze.py                # LMM fitting (FR-003)
│   └── utils.py                     # Helpers, hashing, logging
├── code/validation/
│   └── validate_annotations.py      # Validation script for Constitution VI
├── data/
│   ├── raw/                         # Raw API dumps (checksummed)
│   └── processed/
│       ├── anonymized.csv           # Cleaned, scored data
│       ├── annotations.csv          # Human annotation sample (N=200)
│       └── raw_counts.json          # Ingestion stats
├── tests/
│   ├── unit/
│   │   ├── test_classification.py   # T011: Regex logic
│   │   └── test_anonymization.py    # T012: SHA-256 logic
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Selected Option 1 (Single project) with a linear pipeline structure (`01_`, `02_`, etc.) to ensure clear data flow from ingestion to analysis, matching the spec's US1-US3 flow.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **LMM vs. Simple Regression** | Data is hierarchical (comments nested in threads/users). | Simple regression would violate independence assumptions, inflating Type I error. |
| **Human Annotation Sample** | Automated sentiment/keyword scoring requires validation (Constitution VI). | Relying solely on automated scores without validation risks measurement invalidity. |
| **Distinct Lexicon** | To avoid tautology (predictor words == outcome words). | Using the same words for prime and outcome would guarantee a positive result, invalidating the study. |
| **Streaming/Chunking** | Potential for large raw JSON from Hugging Face. | Loading all into memory at once risks OOM on 7GB RAM runner; streaming ensures feasibility. |

## Feasibility & Constraints

- **CPU Feasibility**: All methods (VADER, regex, LMM via `statsmodels`) are CPU-tractable. No GPU required.
- **Data Source**: Uses `jplu/tf-reddit-comments-2020` (Hugging Face) as Pushshift is defunct.
- **User Tenure**: Removed from model due to data unavailability. Spec flagged for update.
- **Tautology Avoidance**: Prosocial lexicon explicitly excludes prime words ('thank', 'help', 'support', 'care').
- **Real Results**: No simulated data. Human annotation sample (N=200) must be real.
