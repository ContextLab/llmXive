# Implementation Plan: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

**Branch**: `001-gene-regulation` | **Date**: 2026-07-02 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a meta-analysis pipeline to investigate the correlation between structural brain connectivity (dMRI metrics like FA/MD) and individual music preferences. The system extracts effect sizes (r, t, F) and sample sizes from literature, performs a random-effects meta-analysis, assesses heterogeneity (I²) and publication bias (Egger's), and generates visualizations (forest, funnel plots). 

**Critical Methodological Update**: To address the Unit of Analysis Error (multiple tracts per study), the plan implements a **Hybrid Approach**:
1.  **Primary Analysis**: Applies **Bonferroni correction** for multiple tract comparisons (k >= 2) as mandated by FR-005 and SC-004.
2.  **Robustness Check**: Performs a **Multilevel Meta-Analysis (MLM)** to account for the clustering of tracts within studies, validating the independence assumption.
3.  **Dynamic Gate**: If fewer than a sufficient number of eligible studies are found, the system pivots to a narrative systematic review to satisfy FR-006 and SC-005.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `lme4` (via `rpy2` or equivalent Python MLM library if available, otherwise `statsmodels` mixed linear models)  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/derived`)  
**Testing**: `pytest` (unit tests for statistical calculations, integration tests for full pipeline, **specific test for N < 10 pivot**)  
**Target Platform**: Linux (GitHub Actions runner: vCPU, 7GB RAM)  
**Project Type**: CLI/Data Processing Pipeline  
**Performance Goals**: Complete analysis of 10-50 studies in <15 minutes; memory usage <4GB.  
**Constraints**: Must run on CPU only; no GPU required for statistical meta-analysis.  
**Scale/Scope**: Analysis of literature data (synthetic or real CSV inputs); output JSON and PNG reports.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The pipeline will use pinned `requirements.txt` and random seeds (`np.random.seed(42)`). All data transformations will be script-driven, ensuring re-runs produce identical outputs.
- **II. Verified Accuracy**: Citations in `research.md` and `plan.md` will be validated against the provided "Verified datasets" list (if applicable) or the defined "Literature Extraction Protocol". No fabricated URLs will be used.
- **III. Data Hygiene**: Input data will be checksummed upon ingestion. Raw data will never be modified; derived data (e.g., `study_count.json`) will be written to new files.
- **IV. Single Source of Truth**: The `data/processed/study_count.json` file is the **SINGLE** artifact for the gate logic. T009 (Data Source Adapter) calculates checksums but **does NOT** update the state file; T000-verif is the sole updater of the state file.
- **V. Versioning**: All artifacts (schemas, scripts) will carry content hashes in the state file upon completion.
- **VI. Meta-Analysis Statistical Integrity**: The implementation will strictly use `statsmodels` for random-effects models, calculate I², and perform Egger's regression only when N ≥ 20 (with a caveat for N=10-19), applying Bonferroni correction for multiple tracts as required.
- **VII. Systematic Review Fallback Protocol**: The code will explicitly check the study count (N) via `data/processed/study_count.json` before running quantitative steps. If N < 10, it will trigger the narrative synthesis mode and skip quantitative aggregation, satisfying FR-006.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
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
├── data/
│   ├── raw/             # Original CSV/JSON inputs (mock or real)
│   ├── processed/       # Intermediate stats (study_count.json)
│   └── derived/         # Final aggregated results
├── scripts/
│   ├── extract.py       # Data extraction logic (FR-001)
│   ├── real_data_validator.py # Counts studies, writes study_count.json (T009b)
│   ├── meta_analysis.py # Statistical core (FR-002, FR-003, FR-005, MLM)
│   ├── visualize.py     # Plot generation (FR-004)
│   ├── pivot_narrative.py # Fallback logic (FR-006)
│   └── generate_mock_data.py # Mock data generator for CI
├── tests/
│   ├── test_meta.py     # Unit tests for statistical logic
│   ├── test_pivot.py    # Tests for N < 10 logic (Gate Logic Test)
│   └── test_bonferroni.py # Tests for k >= 2 correction
├── utils/
│   ├── checksum.py      # Data hygiene utilities
│   └── config.py        # Configuration loading
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: Single project structure chosen to minimize overhead for a data-processing pipeline. The `code/` directory contains all logic, separated by functional responsibility (extraction, analysis, visualization).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Hybrid Bonferroni + MLM | Required to satisfy FR-005 (Bonferroni) AND address Unit of Analysis Error (MLM). | A static Bonferroni ignores clustering; a pure MLM ignores the spec's mandate for Bonferroni. |
| Dynamic Pivot Logic (N < 10) | Required by FR-006 and SC-005 to handle data scarcity. | A static pipeline would fail or produce invalid statistics on small datasets, violating "Statistical Integrity". |
| Separate Narrative Module | Required to generate structured text summaries when quantitative analysis is impossible. | Hardcoding text generation in the analysis module would violate separation of concerns and make testing difficult. |

## Statistical Rigor & Feasibility

- **Egger's Test**: The plan acknowledges that Egger's test has low power for N < 20. The gate is set to N >= 20 for reliable detection, but the system will report the result for N >= 10 with a "Low Power" warning.
- **Bonferroni**: Applied strictly to the primary pooled results per tract (k >= 2) as per FR-005.
- **MLM**: Used as a robustness check to validate the independence assumption. If MLM results diverge significantly from the Bonferroni-corrected results, the narrative report will highlight this discrepancy.
- **CPU Feasibility**: Meta-analysis of <100 studies is computationally trivial on a 2-core CPU. `statsmodels` and `scipy` are lightweight and fit well within 7GB RAM.
- **Mock Data**: Strictly for CI testing. The research question is only answerable if real data is extracted via the defined protocol.