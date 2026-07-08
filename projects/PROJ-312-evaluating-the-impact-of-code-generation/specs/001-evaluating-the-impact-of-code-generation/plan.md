# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Turnaround Time

**Branch**: `001-evaluating-the-impact-of-code-generation` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary

This feature implements a data-driven research study to evaluate the association between **explicitly flagged AI-assisted code contributions** and code review turnaround times. The system will fetch pull request (PR) metadata from a representative set of top Python and JavaScript repositories on GitHub., classify PRs based on commit messages and labels, calculate turnaround times, and perform **stratified statistical analysis** to control for confounding variables (e.g., PR size, author activity). The implementation adheres to strict data hygiene, reproducibility, and computational feasibility constraints (CPU-only, free-tier GitHub Actions).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `pandas`, `scipy`, `matplotlib`, `pyyaml`, `tqdm`, `statsmodels`  
**Storage**: Local CSV/Parquet files in `data/` directory; artifacts in `artifacts/`  
**Testing**: `pytest` for unit and integration tests; contract validation via local YAML schemas (`contracts/`).  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research Data Pipeline & Statistical Analysis  
**Performance Goals**: Complete data acquisition, cleaning, analysis, and reporting within 6 hours on 2 CPU cores, ~7 GB RAM.  
**Constraints**: No GPU usage; exponential backoff for API rate limits; **robust statistical testing** (no pre-test outlier removal); manual spot-check for false-negative estimation.  
**Scale/Scope**: Top repositories by stars; expected a substantial volume of PRs (filtered to available data); output: 1 report, 1 plot, 1 statistical summary.  
**Validation**: Local schema files (`contracts/pull_request.schema.yaml`, `contracts/repo_metadata.schema.yaml`, `contracts/statistical_result.schema.yaml`) are validated against generated data. No external bibliographic citations are used, so the `Reference-Validator` gate is bypassed; instead, a `Schema-Validator` checks local contracts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence/Action |
|-----------|-------------------|-----------------|
| **I. Reproducibility** | ✅ Compliant | `requirements.txt` will pin versions; random seeds set in `code/`; data fetched from canonical GitHub API. |
| **II. Verified Accuracy** | ✅ Compliant | No external bibliographic citations are used (live API data + local schemas). The `Reference-Validator` is bypassed; a `Schema-Validator` ensures local contract integrity. |
| **III. Data Hygiene** | ✅ Compliant | Raw data saved to `data/raw/`; derived data to `data/processed/`; checksums recorded in `state/`; no in-place modifications. |
| **IV. Single Source of Truth** | ✅ Compliant | All statistics in the final report will be derived from `data/processed/` via scripts in `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | ✅ Compliant | Artifacts will be hashed; `state/projects/PROJ-312-.../state.yaml` updated with `artifact_hashes` and `updated_at` timestamp upon completion. |
| **VI. GitHub API Data Integrity** | ✅ Compliant | API responses logged with rate-limit headers; timestamps recorded for consistency. |
| **VII. AI-Label Heuristic Transparency** | ✅ Compliant | Classification logic (keywords/labels) versioned in `code/` and documented in `technical-design/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-code-generation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Local schemas)
└── tasks.md             # Phase 2 output (Created AFTER plan approval)
```

### Source Code (repository root)

```text
projects/PROJ-312-evaluating-the-impact-of-code-generation/
├── code/
│   ├── __init__.py
│   ├── fetch_data.py          # GitHub API acquisition + metadata collection
│   ├── validate_spot_check.py # Manual spot-check execution (FR-011)
│   ├── analyze.py             # Descriptive stats, Stratified MWU, Sensitivity Analysis
│   ├── visualize.py           # Boxplot generation (IQR for whiskers only)
│   ├── report.py              # Final report assembly (with FR-012 conditional logic)
│   └── utils.py               # Backoff, logging, checksums, schema validation
├── data/
│   ├── raw/                   # Raw API JSON/CSV dumps
│   ├── processed/             # Cleaned, labeled, covariate-enriched CSVs
│   └── spot_check/            # Manual validation results
├── artifacts/
│   └── boxplot.png            # Final visualization
├── tests/
│   ├── unit/                  # Unit tests for logic
│   ├── integration/           # End-to-end pipeline tests
│   └── contract/              # Schema validation tests
├── contracts/                 # Local schema definitions
│   ├── pull_request.schema.yaml
│   ├── repo_metadata.schema.yaml
│   └── statistical_result.schema.yaml
├── requirements.txt           # Pinned dependencies
└── README.md                  # Project overview
```

**Structure Decision**: Single project structure with modular scripts in `code/` to ensure clarity and maintainability. Data is separated into `raw/` and `processed/` to enforce hygiene. `tasks.md` is generated in Phase 2, post-plan approval.

## Complexity Tracking

> No violations detected. Complexity is managed via modular scripts, stratified analysis, and strict adherence to CPU-only constraints.

## Implementation Phases

### Phase 0: Data Acquisition & Preprocessing (FR-001, FR-009, FR-010)
- **Goal**: Fetch PR metadata, commits, and repo details.
- **Actions**:
  1. Fetch a representative set of top Python/JS repositories.
  2. Fetch PRs and commits with exponential backoff.
  3. Classify PRs (AI vs. Non-AI) based on heuristics.
  4. Calculate turnaround times and collect covariates (PR size, author activity).
  5. Save raw and processed data; validate against `pull_request.schema.yaml`.

### Phase 0.5: Validation (FR-011)
- **Goal**: Estimate false-negative rate of the AI classification heuristic.
- **Actions**:
  1. Stratified random sample of non-AI-labeled PRs.
  2. Manual review (human-in-the-loop) to determine true AI status.
  3. Calculate false-negative rate.
  4. Save results to `data/spot_check/validation_report.csv`.

### Phase 1: Statistical Analysis (FR-004, FR-005, FR-006, FR-013)
- **Goal**: Perform robust statistical testing with confounding control.
- **Actions**:
  1. **Descriptive Stats**: Calculate mean, median, SD, quartiles for both groups.
  2. **Repo Metrics**: Calculate median star count and median contributors (FR-013).
  3. **Outlier Handling**: Use **full dataset** for hypothesis testing (robustness). Use IQR bounds only for visualization whiskers and sensitivity checks.
  4. **Hypothesis Testing**: Perform **Stratified Mann-Whitney U Test** (controlling for PR size and author activity) to address confounding.
  5. **Power Check**: If AI group < 30 after cleaning, abort primary test and report limitation.
  6. **Sensitivity Analysis**: Apply bias-correction using spot-check error rates.

### Phase 2: Visualization & Reporting (FR-007, FR-008, FR-012)
- **Goal**: Generate publication-quality plot and final report.
- **Actions**:
  1. Generate boxplot (≥300 DPI) using IQR bounds for whiskers.
  2. Assemble final report.
  3. **Conditional Logic (FR-012)**: If false-negative rate > 10%, inject limitation statement into report.
  4. Save artifacts; update `state/` with hashes and timestamp.
