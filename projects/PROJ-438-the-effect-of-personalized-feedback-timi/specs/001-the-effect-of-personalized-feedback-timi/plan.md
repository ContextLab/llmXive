# Implementation Plan: The Effect of Personalized Feedback Timing on Skill Acquisition

**Branch**: `001-feedback-timing-analysis` | **Date**: 2025-01-15 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-feedback-timing-analysis/spec.md`

## Summary

This feature implements an observational analysis of the Open University Learning Analytics Dataset (OULAD) to quantify the association between feedback timing (Immediate vs. Delayed vs. Variable) and learner outcomes (final grade, completion status). The technical approach involves downloading and caching OULAD, filtering for courses with assessment/forum events, computing inter-event intervals (using forum reply time as a proxy if explicit feedback timestamps are missing), binning learners, and performing Cluster-Robust Ordinary Least Squares (OLS) regression to handle course-level clustering. The implementation is constrained to CPU-only execution (GitHub Actions free tier) and prioritizes statistical rigor (clustered standard errors, sensitivity analysis) and reproducibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels` (for OLS with clustered SE), `pyyaml`, `requests`, `tqdm`, `scipy` (for spline checks)  
**Storage**: Local filesystem (`data/` for raw/derived CSVs, `data/` for checksums)  
**Testing**: `pytest` (unit tests for interval calculation, binning logic; integration test for full pipeline on sample)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data analysis pipeline / Statistical research  
**Performance Goals**: Full pipeline execution ≤ 6 hours on 2 CPU cores; RAM usage < 7 GB (via chunked processing or sampling if necessary)  
**Constraints**: No GPU/CUDA; no deep learning; strict adherence to OULAD schema; observational framing (no causal claims); sensitivity analysis required (FR-007); explicit handling of missing response timestamps.  
**Scale/Scope**: Target ≥10,000 learner records; exclude courses with <50 learners; handle missing timestamps gracefully.  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (Principle I)**: The plan mandates pinning random seeds in `code/`, caching OULAD locally with checksums, and ensuring `code/` runs end-to-end on a fresh runner. *Status: Compliant.*
2.  **Verified Accuracy (Principle II)**: The plan requires citing only verified dataset URLs and validating the "final grade" proxy for skill acquisition via literature (FR-008). **Crucially, the plan explicitly confirms adherence to the automated Reference-Validator Agent verification gate**, ensuring all citations meet the `CITATION_TITLE_OVERLAP_THRESHOLD` (≥0.7) before contributing to review points. *Status: Compliant.*
3.  **Data Hygiene (Principle III)**: The plan enforces checksumming raw data, creating new files for derivations, and excluding PII (OULAD is anonymized). *Status: Compliant.*
4.  **Single Source of Truth (Principle IV)**: All figures/stats will trace to `data/` rows and `code/` blocks; no hand-typed numbers in reports. *Status: Compliant.*
5.  **Versioning Discipline (Principle V)**: The plan explicitly states that every artifact under this project carries a content hash. **The Advancement-Evaluator Agent will detect changes by comparing the content hash of the artifact against the `artifact_hashes` map in the project's `state/...yaml` file. Any change triggers an update to the `updated_at` timestamp in that state file.** *Status: Compliant.*
6.  **Construct Validity (Principle VI)**: The plan explicitly addresses the validation of "final grade" as a proxy for skill acquisition (FR-008) and uses established metrics (Cohen's d, p-values). It includes a fallback limitation statement if validation fails. *Status: Compliant.*
7.  **Temporal Data Integrity (Principle VII)**: The plan mandates computing intervals from consistent timestamps (UTC) and preserving ordering. *Status: Compliant.*

## Project Structure

### Documentation (this feature)

```text
specs/001-feedback-timing-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Drafted here, finalized in Phase 1)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

**Structure Decision**: Single project structure selected for a data analysis pipeline. The `code/` directory contains modular scripts for each functional requirement (download, preprocess, compute, model, report), ensuring separation of concerns and testability. `data/` is strictly for storage, with `raw/` immutable and `processed/` for derived artifacts. **The `contracts/` directory contains the source of truth for data shapes; the plan assumes these contracts are drafted here to ensure consistency with the implementation code.**

### Source Code (repository root)

```text
projects/PROJ-438-the-effect-of-personalized-feedback-timi/
├── code/
│   ├── __init__.py
│   ├── download_data.py          # FR-001: Download OULAD
│   ├── preprocess.py             # FR-002, US-1: Filter, extract, handle missing
│   ├── compute_intervals.py      # FR-003, US-2: Calculate intervals, binning
│   ├── models.py                 # FR-005, US-3: Cluster-Robust OLS fitting
│   ├── sensitivity.py            # FR-007: Boundary sweep analysis
│   ├── report.py                 # FR-008, SC-001-004: Generate metrics/reports
│   └── main.py                   # Orchestration
├── data/
│   ├── raw/                      # Cached OULAD JSON/CSV
│   ├── processed/                # Derived CSVs (intervals, binned groups)
│   └── checksums.txt             # SHA256 hashes
├── tests/
│   ├── test_intervals.py         # US-2 tests
│   ├── test_binning.py           # US-2 tests
│   └── test_ols.py               # US-3 tests
├── requirements.txt
└── README.md
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Cluster-Robust OLS (instead of LMM) | Required because the predictor (feedback group) is aggregated per student, making a student-level random effect singular. Clustering by course handles the non-independence of learners within the same course. | Standard OLS would inflate Type I error by ignoring course-level variance. LMM with student random effects is statistically invalid for this predictor structure. |
| Sensitivity Analysis (FR-007) | Required to test robustness of the 2h/48h cutoffs (SC-003) and alternative window definitions. | Single-point analysis is insufficient for establishing the stability of the finding. |
| Tukey HSD (or equivalent) | Required to control family-wise error rate across ≥3 comparisons (FR-006, SC-002). | Uncorrected t-tests would inflate false positive rates. |