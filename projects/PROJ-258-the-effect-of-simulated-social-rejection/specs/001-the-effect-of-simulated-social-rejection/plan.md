# Implementation Plan: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

**Branch**: `001-social-rejection-reward` | **Date**: 2024-05-21 | **Spec**: `specs/001-social-rejection-reward/spec.md`
**Input**: Feature specification from `specs/001-social-rejection-reward/spec.md`

## Summary

This project performs a secondary analysis of existing behavioral datasets to investigate how simulated social rejection (Cyberball) modulates subsequent behavioral responses to positive feedback (reaction times, mood ratings). 

**Critical Design Constraint**: The analysis relies on a **Single-Cohort Dataset Strategy**. A Within-Subjects design (Mixed ANOVA) is **ONLY** possible if a SINGLE dataset is identified where the same participants completed both the Cyberball rejection task and the positive feedback task. 

**Fallback Strategy**: If no such single-cohort dataset is found (the likely scenario for public datasets like ds000208 and ds003392 which are distinct studies), the system will **NOT** attempt to merge them. Instead, it will:
1.  Report that the "modulation" hypothesis (requiring within-subject interaction) is **untestable** with the available data.
2.  Optionally, perform a Between-Subjects comparison (One-Way ANOVA) to test for *group differences* between rejection and control groups, **explicitly dropping the claim of "modulation"** and framing results as "associational group differences".
3.  If no valid dataset is found, the pipeline halts with a "Data Unavailable" state.

All statistical methods (ANOVA, Benjamini-Hochberg FDR) are CPU-tractable and designed to run within GitHub Actions free-tier constraints (limited CPU, 7 GB RAM, 6h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `requests`  
**Storage**: 
- **Raw Data**: Preserved in `data/raw/` with checksums (Constitution Principle III). Never deleted.
- **Intermediate/Processed**: Stored in `data/interim/` and `data/processed/`.
- **RAM**: Temporary processing in RAM must stay ≤ 7 GB.
**Testing**: `pytest` (unit tests for data validation, integration tests for statistical pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Analysis / Research Pipeline  
**Performance Goals**: Complete ingestion, preprocessing, and analysis within 6 hours for N ≤ 500. Memory usage ≤ 7 GB.  
**Constraints**: No GPU. No heavy deep learning models. Must handle missing variables by switching design or halting. No merging of distinct studies for Within-Subjects analysis.  
**Scale/Scope**: N ≤ 500 participants. Single-cohort datasets only for Within-Subjects.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

1.  **I. Reproducibility**: **PASS**. Plan mandates pinned `requirements.txt`, random seed setting in `code/`, and fetching from canonical sources.
2.  **II. Verified Accuracy**: **PASS with Caveat**. Plan restricts dataset citations to the provided "# Verified datasets" block. **Mock data is explicitly excluded from research results** and used only for CI logic validation. If no real data is found, the research result is marked "Inconclusive".
3.  **III. Data Hygiene**: **PASS**. Plan includes checksumming of raw data and preservation of raw files. "Temporary processing" refers to RAM usage, not deletion of raw data.
4.  **IV. Single Source of Truth**: **PASS**. All statistics trace to `data/` artifacts; no hand-typed numbers in reports.
5.  **V. Versioning Discipline**: **PASS**. Plan includes content hashing of artifacts and **explicitly mandates updating `state/projects/PROJ-258...yaml`** with these hashes after generation.
6.  **VI. Behavioral Proxy Transparency**: **PASS**. The plan explicitly states that "neural response" claims are derived from behavioral proxies (RT, Mood) and will use the phrase "associational" in limitations. **Additionally, if the design falls back to Between-Subjects, the "modulation" claim is dropped.**
7.  **VII. Paradigm Validity**: **PASS**. Plan strictly adheres to Cyberball and positive feedback paradigms. If data is missing or distinct, it does not modify the paradigm but reports the limitation.

## Plan ↔ Data Model Link

The adaptive logic in the plan is explicitly driven by the `design_type` field in the `PreprocessedRecord` (see `data-model.md`):
- If `design_type` == "Within-Subjects" (requires single-cohort dataset), `analysis.py` runs a 2×2 Mixed ANOVA.
- If `design_type` == "Between-Subjects" (distinct datasets or no matching), `analysis.py` runs a One-Way ANOVA and **flags the inability to test modulation**.
- If `design_type` == "Unavailable" (no valid data), the pipeline halts.

## Project Structure

### Documentation (this feature)

```text
specs/001-social-rejection-reward/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, thresholds
├── ingest.py            # Data download and validation (US-1)
├── preprocess.py        # Cleaning, outlier removal, feature extraction (US-2)
├── analysis.py          # ANOVA selection, FDR, sensitivity, power analysis (US-3)
├── report.py            # Report generation with "associational" constraint
├── requirements.txt
└── main.py              # Orchestration script

data/
├── raw/                 # Downloaded datasets (checksummed, preserved)
├── interim/             # Preprocessed data
└── processed/           # Final analysis-ready CSVs

tests/
├── test_ingest.py
├── test_preprocess.py
└── test_analysis.py
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to minimize overhead and fit the CPU-only, single-runner constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Adaptive Design (Within vs. Between) | Dataset variable mismatch or ID mismatch is a high-probability risk. | A static design would fail if the dataset lacks the required single-cohort structure. |
| Single-Cohort Requirement | Merging distinct studies (ds000208 + ds003392) is scientifically invalid for Mixed ANOVA. | A "composite" strategy would lead to Type I errors and invalid claims of modulation. |
| Power Analysis | Required to assess feasibility of detecting interaction effects. | Proceeding without power analysis risks reporting underpowered results as significant. |
| Sensitivity Sweep | Required by FR-006 to test robustness of results across α levels. | Reporting only α=0.05 is insufficient for rigorous secondary analysis. |

