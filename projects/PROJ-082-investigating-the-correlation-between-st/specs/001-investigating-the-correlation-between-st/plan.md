# Implementation Plan: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

**Branch**: `001-gene-regulation` | **Date**: 2024-05-22 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a systematic review and meta-analysis pipeline to investigate the correlation between structural brain connectivity (dMRI metrics like FA/MD) and individual music preferences. The primary technical approach is a Python-based statistical pipeline using `statsmodels` and `scipy` to extract effect sizes from a **manually curated dataset**, perform random-effects meta-analysis, assess heterogeneity (I²) and publication bias (Egger's test), and generate visualizations (forest/funnel plots). 

**Critical Distinction**: This pipeline is a **statistical engine**. It does not perform the literature search or data extraction itself (as no verified dataset contains the required (tract, r, n) tuples). Instead, it ingests a user-provided `studies_extracted.csv` (the result of a manual literature review) and performs the aggregation. The pipeline distinguishes between:
1.  **Unit Testing**: Using synthetic data to verify mathematical correctness (e.g., Egger's test detection logic).
2.  **Scientific Execution**: Processing manually curated data to generate empirical findings.

All computations are designed to run on CPU-only GitHub Actions runners (2 vCPU, 7GB RAM) within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: 
- `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `requests`
- `datasets`: Used **only** to fetch verified metadata (titles/abstracts) from PubMed for literature discovery, NOT for effect size extraction.
- `sklearn`: For power analysis calculations.

**Storage**: Local file system (`data/`, `code/`, `specs/`) with JSON/CSV artifacts; no external database.  
**Testing**: `pytest` for unit tests on statistical logic; `pytest` for integration tests on file I/O and plot generation.  
**Target Platform**: Linux (GitHub Actions default runner: 2 vCPU, ~7 GB RAM).  
**Project Type**: Research Data Pipeline / Statistical Analysis Library.  
**Performance Goals**: Process 10+ studies and generate all plots in < 15 minutes on CI.  
**Constraints**: CPU-only (no GPU); memory usage < 6 GB; no external API calls for data extraction (static CSV/JSON inputs assumed for the pipeline logic); strict adherence to the "Narrative Fallback" if N < 10.  
**Scale/Scope**: Processing a dataset of up to ~50 studies (simulated or extracted); generating 3-5 static PNG figures.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (Principle I)**: The plan mandates pinning `requirements.txt` and using `random.seed` in all statistical sampling. Data derivation steps will produce new files, preserving raw inputs.
2.  **Verified Accuracy (Principle II)**: The `research.md` will only cite URLs from the "Verified datasets" block. The `contracts/` schemas will enforce strict data types for extracted effect sizes.
3.  **Data Hygiene (Principle III)**: The pipeline will implement checksums for input data files. No in-place modification of raw data; all transformations write to `data/derived/`.
4.  **Single Source of Truth (Principle IV)**: All plots and statistics in the final report will be generated directly from the `MetaAnalysisResult` JSON, ensuring no hand-typed numbers.
5.  **Versioning Discipline (Principle V)**: Artifacts will carry content hashes; the plan includes a script to update the `state.yaml` timestamp upon successful run.
6.  **Meta-Analysis Statistical Integrity (Principle VI)**: The plan explicitly implements `statsmodels` random-effects models, I² calculation, Egger's regression (conditional on N≥10), and Bonferroni correction. It also addresses non-independence via Robust Variance Estimation (RVE) logic where applicable.
7.  **Systematic Review Fallback Protocol (Principle VII)**: The `data_model.md` and `plan.md` define a strict gate: if `unique_studies < 10`, the quantitative aggregation steps are skipped, and a narrative synthesis mode is triggered. **See `data-model.md` section "Data Flow" for the specific logic.**

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── study_record.schema.yaml
│   └── meta_analysis_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-082-investigating-the-correlation-between-st/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── main.py                 # Entry point: Orchestrates data loading, tract harmonization, statistical analysis, and plot generation.
│   ├── extraction/
│   │   ├── __init__.py
│   │   └── parser.py           # Logic to parse CSV/JSON inputs for r, n, tract
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── meta_analysis.py    # Random-effects model, I², Egger's test, Power Analysis
│   │   ├── correction.py       # Bonferroni logic, RVE for non-independence
│   │   └── narrative.py        # Narrative synthesis generator
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── plots.py            # Forest, funnel, and correlation plots
│   └── utils/
│       ├── __init__.py
│       ├── checksum.py         # Data hygiene utilities
│       └── config.py           # Seed pinning and config loading
├── data/
│   ├── raw/                    # Input datasets (manual CSV, verified metadata)
│   └── derived/                # Processed JSON/CSV outputs
├── tests/
│   ├── unit/                   # Test extraction and statistical logic
│   └── integration/            # End-to-end pipeline test
└── docs/
    └── paper_draft.md          # Output report
```

**Structure Decision**: Single-project structure (`code/` at root of project folder) is selected to maintain simplicity for a data-science pipeline. Separation of concerns is achieved via sub-packages (`extraction`, `analysis`, `visualization`). This aligns with the "Research Data Pipeline" project type and facilitates unit testing of statistical logic in isolation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Tract Harmonization** | Studies use varying definitions for tracts (e.g., "Arcuate" vs "AF"). | Simple string matching is insufficient; requires mapping to a standard ontology (JHU Atlas) to ensure construct validity. |
| **Non-Independence Handling** | Multiple tracts from one study share participants. | Standard Bonferroni assumes independence. We implement Robust Variance Estimation (RVE) or study-level grouping to avoid Type I errors. |
| **Power Analysis** | N=10 is low power for small effects. | A simple N<10 gate ignores statistical power. We add a specific warning for N<20 when detecting small effects (r<0.3). |
| **Model Convergence** | Random-effects models may fail on small N. | Fixed-effects fallback is necessary to ensure the pipeline produces a result (with a warning) rather than crashing. |

## Data Provenance & Validation

- **Input Data**: The pipeline expects `data/raw/studies_extracted.csv` as a **user-provided artifact**. This file represents the output of a manual literature review. The pipeline does **not** attempt to scrape or auto-extract effect sizes from raw literature (PubMed abstracts) because they lack statistical tables.
- **Verified Datasets**: Used **only** for literature discovery (titles/abstracts) to validate the existence of relevant studies. They are **not** used for the statistical aggregation.
- **Unit Testing**: Synthetic data is used **only** to verify the mathematical correctness of the statistical engines (e.g., "Does the code correctly calculate I²?"). These tests do not validate the scientific claim, only the code logic.
- **Scientific Execution**: When run with manually curated data, the pipeline generates empirical findings. The validity of these findings depends on the quality of the manual curation, which is outside the scope of the code but documented in the `research.md`.

## Statistical Methodology Addendum

- **Tract Harmonization**: All `tract_name` strings are mapped to a standard ontology (e.g., JHU White Matter Tractography Atlas) before aggregation. Studies using non-standard names are flagged.
- **Non-Independence**: If a study reports multiple tracts, they are treated as distinct comparisons for Bonferroni correction **only if** the study reports them as independent analyses. Otherwise, the study is treated as a single unit for the primary aggregation, with a note on the potential for within-study correlation.
- **Power Analysis**: A post-hoc power analysis is performed. If N < 20 and the expected effect size is small (r < 0.3), a `power_warning` is included in the output.

## Feasibility Assessment (Compute)
- **Memory**: The analysis of < 100 studies requires negligible RAM (< 500MB).
- **CPU**: Statistical calculations (I², Egger's) are $O(N)$ and will complete in seconds.
- **Time**: Total runtime on GitHub Actions (2 vCPU) estimated at < 5 minutes.
- **Constraints**: No GPU required. All libraries (`statsmodels`, `scipy`) have CPU wheels available.

## Risks & Mitigations
- **Risk**: Insufficient studies ($N < 10$) for quantitative analysis.
  - **Mitigation**: The pipeline is explicitly designed to detect this and switch to Narrative Mode (FR-006). This is an acceptable outcome per the spec.
- **Risk**: Missing effect sizes (only p-values reported).
  - **Mitigation**: The extraction module will attempt conversion using standard formulas (p-value to z-score to r) or flag the study for exclusion with a log entry.
- **Risk**: Model convergence failure.
  - **Mitigation**: Fallback to Fixed-Effects model if Random-Effects fails to converge, with a warning log.
- **Risk**: Tract definition heterogeneity.
  - **Mitigation**: Mapping to a standard ontology and flagging non-standard entries.