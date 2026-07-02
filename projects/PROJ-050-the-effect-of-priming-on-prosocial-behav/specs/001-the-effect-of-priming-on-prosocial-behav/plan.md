# Implementation Plan: The Effect of Priming on Prosocial Behavior in Online Communities

**Branch**: `001-the-effect-of-priming-on-prosocial-behav` | **Date**: 2026-06-25 | **Spec**: `spec.md`

## Summary

This project investigates the correlational effect of prosocial priming (presence of keywords like "help", "support", "charity" in thread titles) on subsequent prosocial language in Reddit replies. The implementation involves a three-phase pipeline: (1) Ingesting and filtering a verified multi-subreddit HuggingFace Reddit dataset (`pushshift/reddit`) for target subreddits, classifying threads into Prime/Control groups while handling negation logic, and anonymizing PII; (2) Computing VADER sentiment scores and a custom prosocial action lexicon count (excluding prime keywords to avoid tautology) on a CPU-tractable sample; (3) Performing Linear Mixed-Effects Modeling (LMM) to account for clustered data, followed by visualization and sensitivity analysis. The entire pipeline is designed to run within GitHub Actions free-tier limits (2 CPU, 7 GB RAM, <6h).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `vaderSentiment`, `statsmodels`, `matplotlib`, `seaborn`, `datasets` (HuggingFace), `pyyaml`, `linearmodels` (for Mixed-Effects), `pytest`
**Storage**: Local CSV/Parquet files in `data/` (derived from HuggingFace)
**Testing**: `pytest` (unit tests for lexicon logic, integration tests for pipeline flow)
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-only)
**Project Type**: Data Science / Statistical Analysis Pipeline
**Performance Goals**: Process ~10k-20k comments within 4 hours on 2 CPU cores; memory usage < 6 GB peak.
**Constraints**: No GPU; no large language model inference; strict PII anonymization; dataset must be verified via HuggingFace URLs provided.
**Scale/Scope**: Target ~+ comments (several thousand per group), limited by available data density in verified subreddits.
**Dependency Usage Note**: `pyyaml` is explicitly used in `code/data/preprocess.py` to load and validate the dataset schema against `contracts/dataset.schema.yaml` before processing begins, ensuring data integrity.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Action Required |
|-----------|-------------------|-----------------|
| I. Reproducibility | **Compliant** | Random seeds will be pinned in `code/`. Dependencies pinned in `requirements.txt`. |
| II. Verified Accuracy | **Compliant** | Dataset URLs cited only from the "Verified datasets" block. No fabricated URLs. |
| III. Data Hygiene | **Compliant** | Raw data downloaded to `data/raw/` with checksums. Derived data in `data/processed/`. No in-place edits. |
| IV. Single Source of Truth | **Compliant** | All stats in the final report will be generated programmatically from `data/processed/`. |
| V. Versioning Discipline | **Compliant** | **Procedure Added**: Artifact hashes are computed via `sha256sum` after each phase. The `state/projects/...yaml` file is updated programmatically by `code/utils/versioning.py` to reflect the new `updated_at` timestamp and artifact hashes, invalidating stale reviews. |
| VI. Measurement Validity | **Compliant** | VADER and prosocial lexicon will be validated on a stratified sample via **independent human annotation** (manual coding) with Cohen's Kappa reporting. |
| VII. Participant Privacy | **Compliant** | Usernames hashed (SHA-256); timestamps stripped before `data/` storage. |

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
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)
```text
projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/
├── code/
│   ├── __init__.py
│   ├── config.py          # Paths, seeds, constants
│   ├── utils/
│   │   └── versioning.py  # Manages artifact hashes and state file updates
│   ├── data/
│   │   ├── download.py    # HuggingFace fetcher (schema validation included)
│   │   ├── preprocess.py  # Classification, negation logic, anonymization, schema enforcement
│   │   └── score.py       # VADER, lexicon scoring
│   ├── analysis/
│   │   ├── stats.py       # LMM, sensitivity analysis
│   │   └── viz.py         # Boxplot generation
│   └── validation/
│       └── kappa.py       # Inter-rater reliability script (requires manual annotations)
├── data/
│   ├── raw/               # Downloaded parquet (gitignored or checksummed)
│   └── processed/         # Cleaned, anonymized CSV/Parquet
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Single project structure (`code/` and `data/` at root of feature) is selected for simplicity, matching the data science workflow. No frontend/backend split is needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| LMM vs T-Test | Data is clustered (comments within threads). | Simple t-test violates independence assumption, inflating Type I errors. |
| Manual Annotation | Construct validity requires human ground truth. | Heuristic/simulated validation is circular and invalid for measuring prosocial behavior. |
| Multi-Subreddit Dataset | Study requires specific subreddits. | AskReddit-only datasets cannot support the cross-community comparison. |

## Versioning Discipline Procedure

To satisfy Constitution Principle V:
1. **Hashing**: After `download.py` and `preprocess.py` complete, `code/utils/versioning.py` computes SHA-256 hashes for all files in `data/raw/` and `data/processed/`.
2. **State Update**: The script updates `state/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav.yaml` with:
   - `artifact_hashes`: Mapping of file paths to their content hashes.
   - `updated_at`: ISO 8601 timestamp of the update.
3. **Invalidation**: If any hash changes, the Advancement-Evaluator Agent invalidates any `research_review` records dependent on the old hash.