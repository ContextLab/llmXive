# Implementation Plan: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Branch**: `001-self-compassion-feedback` | **Date**: 2026-06-28 | **Spec**: `specs/001-self-compassion-feedback/spec.md`

## Summary

This project implements a statistically rigorous analysis to test whether self-compassion (SCS) moderates the adverse psychological impact of negative feedback on anxiety, rumination, and self-efficacy. The approach involves downloading a verified OSF dataset, performing data cleaning and validation, fitting three ANCOVA models (one per outcome) with interaction terms, applying Holm-Bonferroni correction for multiple comparisons, generating simple-slope visualizations, and producing a comprehensive HTML report. All methods are constrained to run on CPU-only CI (GitHub Actions free tier) using `statsmodels` and `pandas`. The analysis strictly computes all statistics from the raw data; no simulated or hard-coded results are permitted.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `seaborn`, `matplotlib`, `requests`, `jinja2`, `pyyaml`, `scipy`  
**Storage**: Local filesystem (CSV/Parquet input, PNG/HTML output)  
**Testing**: `pytest` (contract tests for schema validation)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)  
**Project Type**: Data Analysis Pipeline / Statistical Study  
**Performance Goals**: Complete analysis and report generation within 6 hours on CPU-only hardware.  
**Constraints**: No GPU; no heavy model training; strict adherence to OSF dataset schema; robust error handling for missing data/columns.  
**Scale/Scope**: Single dataset (~10k rows max), 3 primary models, 3 robustness checks.

## Constitution Check

*Gates determined based on `projects/PROJ-167-the-impact-of-self-compassion-on-resilie/.specify/memory/constitution.md`*

1.  **I. Reproducibility**: **PASS**. Plan mandates `random_seed=42` for all stochastic operations (bootstrap, shuffling) and requires fetching data from a fixed OSF URL. `requirements.txt` will pin versions.
2.  **II. Verified Accuracy**: **PASS**. The plan explicitly includes a step to run the **Reference-Validator Agent** against the OSF URL (`https://osf.io/3k9r2/`) and instrument citations (SCS, STAI, etc.) before analysis begins. This ensures all citations are verified against primary sources as required by the constitution's gate.
3.  **III. Data Hygiene**: **PASS**. Plan includes FR-016: SHA-256 checksum of the raw dataset immediately after download, stored in `state/projects/...yaml`. No in-place modification of raw data; derivations go to new files.
4.  **IV. Single Source of Truth**: **PASS**. All statistics in the report are computed by the code from the `data/` directory. No hand-typed numbers.
5.  **V. Versioning Discipline**: **PASS**. Artifacts (data, report, plots) will be hashed. The `state` file tracks `updated_at`.
6.  **VI. Validated Instruments**: **PASS**. The plan explicitly relies on SCS (Neff), STAI (Spielberger), RRS (Nolen-Hoeksema), and GSES (Schwarzer), all established scales.
7.  **VII. Participant Well‑Being**: **PASS**. The plan adds a specific step to create `code/protocol.md` documenting ethical procedures (pre-screening, debriefing, resource access). The data cleaning phase will verify a 'debriefing_complete' flag or metadata note. If missing, a 'Protocol Verification Warning' is added to the report.

## Project Structure

### Documentation (this feature)

```text
specs/001-self-compassion-feedback/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── analysis_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-167-the-impact-of-self-compassion-on-resilie/
├── data/
│   ├── raw/
│   │   └── feedback_self_compassion.csv (downloaded)
│   └── processed/
│       └── clean_data.csv
├── code/
│   ├── __init__.py
│   ├── download.py          # Downloads dataset, computes SHA-256
│   ├── clean.py             # Listwise deletion, encoding, z-scoring
│   ├── models.py            # ANCOVA fitting, VIF, Bootstrap, Johnson-Neyman
│   ├── viz.py               # Simple slope plots
│   ├── report.py            # HTML generation (Jinja2)
│   └── main.py              # Orchestrator
├── tests/
│   ├── test_contracts.py    # Validates CSV/JSON against dataset.schema.yaml, analysis_result.schema.yaml, output.schema.yaml
│   └── test_pipeline.py     # End-to-end smoke test
├── state/
│   └── projects/PROJ-167-the-impact-of-self-compassion-on-resilie.yaml
└── reports/
    └── report.html
```

**Structure Decision**: Single project structure. The analysis is linear (Download -> Clean -> Model -> Viz -> Report). No complex microservices or frontend/backend split is needed for a statistical study.

## Compute Feasibility & Methodological Rigor

- **Dataset Fit**: The plan explicitly checks for required columns (`stai_post`, `rrs_post`, `gse_post`, `scf_total`, `feedback_cond`) per FR-001. If missing, the pipeline aborts with a specific error, preventing "fatal dataset mismatch" flaws.
- **Statistical Rigor**:
    - **Multiple Comparisons**: Holm-Bonferroni correction applied across the 3 primary outcomes (FR-011) and 3 robustness outcomes (FR-011b).
    - **Power & MDES**: Power analysis target (N≥92) is checked. If N<92, the pipeline **calculates the Minimum Detectable Effect Size (MDES)** for the observed N and reports this specific value. The report will frame findings as "exploratory" if power < 0.80 for the target f²=0.02.
    - **Causal Claims**: The plan checks for randomization metadata (FR-017). If absent, claims are restricted to "associational."
    - **Collinearity**: VIF computed; >5 triggers a flag (FR-013).
    - **Robustness**: HC3 standard errors (FR-009) and Bootstrap (FR-008) included.
    - **Homogeneity of Slopes**: **Prerequisite Gate**. If the interaction between Covariate and Feedback is significant (p < 0.10), the primary ANCOVA interaction is flagged as biased. The pipeline **automatically runs a Johnson-Neyman technique** to identify the specific range of the moderator where the effect is significant, and these results take precedence for the main conclusion.
    - **Simple Slopes Direction**: The plan explicitly computes the simple slopes of the *feedback condition* at low, mean, and high SCS to confirm the *direction* of the buffering effect (flatter slope for high SCS), not just the interaction significance.
    - **Bootstrap Strategy**: Explicitly uses **Case Resampling** (stratified by feedback condition) to preserve experimental design structure.
- **CPU Feasibility**:
    - **No GPU**: All operations use `statsmodels` (CPU-native) and `pandas`.
    - **Memory**: Data is processed in chunks or fully loaded (assuming <100k rows, well within 7GB RAM).
    - **Runtime**: Bootstrap (5k resamples) and 3 models are computationally light on 2 cores; estimated runtime < 30 mins.

## Testing Strategy

- **Contract Tests**: `tests/test_contracts.py` will validate the raw CSV against `contracts/dataset.schema.yaml` and the analysis output against `contracts/analysis_result.schema.yaml` and `contracts/output.schema.yaml`.
- **Pipeline Tests**: `tests/test_pipeline.py` ensures the end-to-end flow (Download -> Clean -> Model -> Report) completes without error and produces non-empty artifacts.
- **No Hard-Coded Results**: All tests verify that values in the output are derived from the `data/` directory via the specified statistical methods. No simulated or placeholder numbers are allowed.