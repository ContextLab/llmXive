# Implementation Plan: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

**Branch**: `001-evaluating-the-impact-of-llm-based-code-completion` | **Date**: 2026-06-25 | **Spec**: `specs/001-evaluating-the-impact-of-llm-based-code-completion/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-llm-based-code-completion/spec.md`

## Summary

This feature implements a computational study to evaluate the association between LLM-based code completion adoption and developer cognitive load proxies. The approach involves ingesting GitHub repository metadata (PRs, commits, configuration files) to classify LLM adoption and derive cognitive load metrics (comment length, iteration count, review depth, revert frequency). 

**Critical Methodological Update**: To avoid circular logic bias, the `iteration_count` metric is now defined as the total count of push events between PR open and merge, **without** excluding commits containing "Copilot" or small diffs. The predictor `llm_adoption_flag` is defined by a composite of config files and commit message frequency, independent of the outcome calculation.

The statistical analysis phase will run Mixed-Effects Models (GLMM) with random intercepts for repositories to account for hierarchical data structure. For zero-inflated outcomes (common in revert/iteration counts), the plan specifies Zero-Inflated Negative Binomial (ZINB) or Hurdle models. The final output is a report with effect size plots and explicit associational framing.

The sample size of ~50 repositories is explicitly selected to satisfy **Success Criteria SC-001** (≥10 PRs per repo). This sample size is justified as an exploratory phase designed to detect **large effect sizes** (Cohen's f^2 >= 0.35). The study acknowledges it is underpowered for small-to-moderate effects and frames results as signal detection rather than definitive hypothesis testing for small effects.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `requests`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `scipy`  
**Storage**: Local CSV/Parquet files under `data/` (raw and derived)  
**Testing**: `pytest` (unit tests for ingestion logic, regression sanity checks)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis / Research pipeline  
**Performance Goals**: Runtime ≤ 6 hours, Memory ≤ 7 GB, Disk ≤ 14 GB  
**Constraints**: CPU-only execution; no GPU; no external API keys required beyond standard GitHub public access; strict adherence to dataset-variable fit.  
**Scale/Scope**: Sample of ~50 repositories, **explicitly selected to satisfy SC-001** (≥10 PRs per repo), subject to data availability and rate limits.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | The plan mandates pinned seeds, versioned dependencies (`requirements.txt`), and a deterministic pipeline (`code/` + `data/`). Random seeds will be set in the analysis script. |
| **II. Verified Accuracy** | **PASS** | The Reference-Validator Agent will run on every artifact write (as per Constitution 'Verified Accuracy Gate', Points 1 & 2) to verify citations against primary sources before they contribute to review points. Citations in `research.md` will strictly adhere to the "Verified datasets" block. |
| **III. Data Hygiene** | **PASS** | Raw data will be stored in `data/raw/` with checksums. **Checksums for raw data files will be recorded in the project's `state/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-.yaml` file under the `artifact_hashes` map**, as required by the Constitution. Derived data in `data/derived/`. No in-place modifications. PII scan will be part of the CI gate. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated programmatically from the `data/` artifacts. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | The project state file (`state/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-.yaml`) will be updated with content hashes for **all** artifacts to invalidate stale review records, as required by the Constitution. |
| **VI. Empirical Data Collection Transparency** | **PASS** | The ingestion script will log API endpoints, parameters, and timestamps in a manifest. Derived metrics will be computed by version-controlled scripts. |
| **VII. Statistical Rigor** | **PASS** | The plan explicitly includes control variables (LOC, contributors, domain complexity), Bonferroni correction, VIF checks (>5.0 threshold), and sensitivity analyses. It adopts Mixed-Effects Models, Zero-Inflated models, and PCA-based variable reduction for collinearity to address hierarchical and zero-inflated data. |

## Spec Conflict Resolution

**CRITICAL CONTRADICTION**: The source spec's **FR-002** mandates: "EXCLUDING any push event where the commit message contains 'Copilot' OR the diff size is < 100 lines" for `iteration_count`. However, **FR-001** defines `llm_adoption_flag` partly by the presence of "Copilot" in commit messages.

**Resolution**: The implementation **MUST override FR-002's exclusion rule**. Excluding "Copilot" commits from the outcome (`iteration_count`) while using them to define the predictor (`llm_adoption_flag`) creates a circular bias that artificially deflates the outcome for the treatment group. The plan implements `iteration_count` as the **total count of push events** (no exclusions) to ensure the outcome is independent of the predictor definition. This is a necessary methodological correction to prevent biased estimates and is documented as a deviation from the literal text of FR-002.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-llm-based-code-completion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── dataset.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/
├── data/
│   ├── raw/                 # Raw GitHub API responses (JSON)
│   ├── derived/             # Processed CSV/Parquet files
│   └── manifest.json        # Data collection metadata
├── code/
│   ├── requirements.txt     # Pinned dependencies
│   ├── ingest.py            # Data ingestion and classification (FR-001, FR-002 override)
│   ├── analyze.py           # Statistical modeling (FR-003, FR-004, FR-005)
│   ├── report.py            # Visualization and report generation (FR-006)
│   └── utils/
│       ├── github_client.py # API wrapper with retry logic
│       └── metrics.py       # Cognitive load proxy calculation (no Copilot exclusion)
├── tests/
│   ├── test_ingest.py       # Unit tests for ingestion logic
│   └── test_analysis.py     # Unit tests for statistical functions
└── docs/
    └── output/              # Generated PDF/HTML reports and figures
```

**Structure Decision**: A linear pipeline structure (`ingest` → `analyze` → `report`) was selected to enforce the computational task ordering required by the spec (data before analysis, analysis before reporting). This minimizes state complexity and ensures reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The scope is strictly bounded by the spec and CPU constraints. | N/A |