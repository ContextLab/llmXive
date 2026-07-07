# Implementation Plan: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Branch**: `001-impact-of-incidental-music` | **Date**: 2026-06-28 | **Spec**: `specs/001-impact-of-incidental-music-on-autobiographical-memory-retrieval/spec.md`

## Summary

This feature implements a computational pipeline to test the "Adolescent Advantage" hypothesis in autobiographical memory. The system ingests listening logs (MSD) and memory cues (AMT), computes a **Residualized Adolescent Exposure Score** (to disentangle timing from popularity), matches memory cues to tracks via fuzzy string matching, and fits a linear mixed-effects model. 

**Critical Methodological Update**: The unit of analysis is changed from "individual memory instance" to **"User-Track Pair"**. Data is aggregated to one row per unique user-track combination (mean vividness/valence per pair). This resolves the collinearity issue where a track-level predictor (exposure score) would be identical for multiple rows of the same user, and ensures the random intercept (User) can be estimated correctly.

The pipeline is designed to run entirely on CPU within GitHub Actions free-tier constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `python-Levenshtein`, `pyyaml`, `tqdm`, `scipy`  
**Storage**: Local CSV/Parquet files (no external DB); data processed in-memory with chunking if necessary.  
**Testing**: `pytest` (unit tests for ingestion/matching logic; integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Data Science / Research Pipeline.  
**Performance Goals**: Complete ingestion, matching, and modeling within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU; no heavy LLM inference; strict adherence to verified dataset URLs; fuzzy matching threshold ≤ 4.  
**Scale/Scope**: Limited to the scale of verified datasets (likely <100k users). Power analysis adjusted accordingly.

> **Note on Datasets**: The plan relies on the verified URLs provided in the research phase. If the verified MSD subset lacks `birth_year`, the plan falls back to the "Global Exposure" metric as per FR-008. If no human-collected AMT data is verified, the pipeline runs in "Simulation Mode" for code validation only.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | All random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched from canonical verified URLs. |
| **II. Verified Accuracy** | ✅ Pass | Citations limited to verified URLs; no invented dataset sources; validation logic included. |
| **III. Data Hygiene** | ✅ Pass | Raw data preserved; derivations written to new files with checksums; PII scan configured. |
| **IV. Single Source of Truth** | ✅ Pass | All statistics traced to specific data rows and code blocks; no hand-typed numbers. |
| **V. Versioning Discipline** | ✅ Pass | **Mechanism**: Every derived file in `data/processed/` and `data/final/` is checksummed via `sha256sum`. The `state.yaml` file is updated by the Advancement-Evaluator Agent with these hashes upon successful pipeline completion. Any change to source data invalidates the state, triggering a re-run. |
| **VI. Psychometric Instrument Integrity** | ✅ Pass | AMT protocol followed; deviations documented; vividness/valence scales validated against literature. **Blocker**: If only LLM-generated data is verified, the study is flagged as non-valid for human psychology claims. |
| **VII. Developmental Period Definition** | ✅ Pass | Adolescence strictly defined as ages -18; boundary cases excluded or analyzed separately. |

## Project Structure

### Documentation (this feature)

```text
specs/001-impact-of-incidental-music/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-200-the-impact-of-incidental-music-on-autobi/
├── code/
│   ├── __init__.py
│   ├── config.py                 # Paths, thresholds, seeds, min_listen_threshold
│   ├── data_ingestion.py         # FR-001, FR-002, FR-008, Minimum Listen Filter
│   ├── cue_matching.py           # FR-003
│   ├── aggregation.py            # FR-004 (User-Track Level Aggregation)
│   ├── modeling.py               # FR-005, FR-006, FR-007
│   └── main.py                   # Pipeline orchestration
├── data/
│   ├── raw/                      # Downloaded datasets (checksummed)
│   ├── processed/                # Intermediate CSVs/Parquets (User-Track pairs)
│   └── final/                    # Aggregated analysis dataset
├── tests/
│   ├── unit/
│   │   ├── test_ingestion.py
│   │   └── test_matching.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The workflow is linear (Ingest → Match → Aggregate → Model), making a monolithic `code/` directory with modular scripts the most efficient approach for a research pipeline. No separate frontend/backend is required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Fuzzy Matching** | Track titles in AMT cues are free-text and often misspelled or abbreviated. | Exact string matching would result in <10% match rate, violating SC-004 (≥80% match). |
| **Mixed-Effects Model (User-Track)** | Data is hierarchical (memories nested within users, nested within tracks). | Ordinary Least Squares (OLS) would violate independence assumptions; aggregating to global track level would lose the user random effect. |
| **Residualized Exposure** | Raw ratio (Adolescent/Total) is correlated with Total (Popularity). | Simple covariate adjustment may not fully remove spurious correlation; residualization is more robust. |
| **Minimum Listen Threshold** | Low-frequency tracks have unstable exposure scores (e.g., 1/1 = 100%). | Including them introduces noise and potential spurious correlations with vividness. |

## Phase Plan

### Phase 0: Research & Data Validation
- **Goal**: Verify dataset contents against spec requirements.
- **Tasks**:
  1. Inspect verified MSD URLs to confirm presence of `user_id`, `track_id`, `timestamp`, and `birth_year`.
  2. Inspect verified AMT URLs to confirm presence of `cue_text`, `vividness`, `valence`, and `user_id`. **Critical**: Verify these are human-collected, not LLM-synthesized.
  3. **Critical Check**: If MSD lacks `birth_year`, the **pipeline code** will trigger FR-008 fallback logic (Global Exposure) and log a warning.
  4. Estimate dataset size to ensure CPU feasibility (sampling strategy if necessary).

### Phase 1: Data Engineering & Modeling Design
- **Goal**: Define schemas and implement ingestion/matching logic.
- **Tasks**:
  1. Implement `data_ingestion.py` with `birth_year` filtering, **Minimum Listen Threshold (N >= 10)**, and `residualized_exposure_score` calculation.
  2. Implement `cue_matching.py` with Levenshtein distance ≤ 4.
  3. Design `User-Track AggregatedMetric` schema in `contracts/dataset.schema.yaml`.
  4. Implement `aggregation.py` to compute **mean vividness/valence per User-Track pair**.

### Phase 2: Statistical Analysis & Sensitivity
- **Goal**: Fit models and run sensitivity/permutation tests.
- **Tasks**:
  1. Implement `modeling.py` with `statsmodels` mixed-effects (`MixedLM`) on **User-Track pairs**.
     - Model: `mean_vividness ~ residualized_exposure + popularity + (1|user_id)`
  2. Implement sensitivity analysis (varying thresholds).
  3. Implement permutation test: **Shuffle `residualized_exposure_score` values across tracks** (preserving track IDs and memory counts) 1000 times.
  4. Generate regression summary tables and diagnostic plots (VIF, residual checks).

### Phase 3: Validation & Reporting
- **Goal**: Ensure all FRs and SCs are met.
- **Tasks**:
  1. Run full pipeline on a small synthetic subset for unit testing.
  2. Execute full pipeline on verified datasets.
  3. Verify SC-001 (p-value), SC-002 (stability), SC-003 (permutation), SC-004 (match rate), SC-005 (runtime).
  4. Generate final artifacts and checksums.