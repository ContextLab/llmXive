# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Branch**: `001-gut-microbiome-sleep-architecture` | **Date**: 2026-06-27 | **Spec**: `specs/001-gut-microbiome-sleep-architecture/spec.md`
**Input**: Feature specification from `/specs/001-gut-microbiome-sleep-architecture/spec.md`

## Summary

This project implements a robust, reproducible statistical pipeline to investigate the associational correlation between gut microbiome composition (metagenomic counts) and sleep architecture (polysomnography metrics). The system ingests data, validates variable completeness, selects appropriate statistical models based on rigorous distribution and compositional tests, applies robust multiple-comparison corrections (Benjamini-Hochberg), and performs sensitivity, collinearity, and power analyses. The pipeline is designed to run entirely on a CPU-only GitHub Actions runner (2 cores, 7GB RAM) within 6 hours. **No GPU fallback is permitted** to ensure full reproducibility on the standard CI runner. The project is scoped to **Pipeline Validation** due to the absence of a verified public dataset containing both modalities.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `pyyaml`, `datasets` (HuggingFace), `spiecEasi` (or `SparCC`), `qvalue`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`)  
**Testing**: `pytest`  
**Target Platform**: `ubuntu-latest` (GitHub Actions). **CPU-only execution**.  
**Project Type**: Data analysis pipeline / CLI tool  
**Performance Goals**: Complete full pipeline (ingestion to reporting) within 6 hours on 2-core CPU.  
**Constraints**: <7 GB RAM usage, no PII, strict reproducibility (random seeds), no causal language in output.  
**Scale/Scope**: N < 1000 subjects, < 500 taxa (Assumption-001).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt`, random seed fixation, and deterministic data fetching. **No GPU fallback**; all runs must be reproducible on a fresh GitHub Actions runner.
- **II. Verified Accuracy**: A 'Verified Accuracy Gate' task (T006) runs a script to validate all citations. **The implementation will fail immediately if citations are unverified.**
- **III. Data Hygiene**: Plan includes checksumming (`md5sum`/`sha256`) of all raw data downloads and versioning of derived files.
- **IV. Single Source of Truth**: All figures/stats in the final report will be generated programmatically from `data/processed/` artifacts; no manual entry.
- **V. Versioning Discipline**: Artifacts will be hashed; `state/` files will be updated on change.
- **VI. Biological Sample Integrity**: **If real data is used, a `chain_of_custody_log.json` must be present and validated.** For synthetic data, this field is explicitly null.
- **VII. Sleep Metric Standardization**: The plan includes a validation step to ensure sleep metrics (REM, SWS) follow consistent definitions as per the dataset schema.

## Project Structure

### Documentation (this feature)

```text
specs/001-gut-microbiome-sleep-architecture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── correlation_result.schema.yaml
│   └── ...
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point / CLI
├── ingestion/
│   ├── loader.py        # Data loading & validation (FR-001)
│   └── validator.py     # Variable completeness check
├── analysis/
│   ├── distribution.py  # Shapiro-Wilk, Zero-inflation check (FR-002)
│   ├── correlation.py   # SparCC, ZINB, Spearman, Pearson logic (FR-002)
│   ├── correction.py    # Benjamini-Hochberg (FR-003)
│   ├── diagnostics.py   # VIF, Collinearity, Power (FR-006, US-3)
│   └── sensitivity.py   # Threshold sweep (FR-005)
├── reporting/
│   └── generator.py     # Report generation, causal language filter (FR-004)
├── utils/
│   ├── logger.py
│   └── checksum.py
└── tests/
    ├── unit/
    └── integration/

data/
├── raw/                 # Downloaded datasets (checksummed)
├── processed/           # Cleaned, validated data
└── results/             # Output artifacts (JSON, CSV, PDF)

requirements.txt
.gitignore
```

**Structure Decision**: A modular, single-project structure (`code/`) is selected to minimize overhead and ensure tight coupling between ingestion, analysis, and reporting, facilitating the 6-hour execution constraint on a limited CI runner. **Modules validate against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`**.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| SparCC / SpiecEasi | Required for compositional data to avoid closure problem. | Standard Pearson/Spearman on raw/CLR data yields spurious correlations. |
| Zero-Inflated Models (ZINB) | Required by FR-002 for >30% zeros in raw counts. | Standard methods yield biased estimates for sparse microbiome data. |
| Dynamic Method Selection | Required by FR-002 to adapt to data distribution. | Hard-coding a single method risks statistical invalidity. |
| Multi-Phase Validation | Required by FR-001 and US-1 to halt on missing variables. | Running analysis on incomplete data would produce meaningless results. |
| Hierarchical Pre-screening | Required to reduce multiple testing burden (2000 tests -> manageable). | Standard BH on 2000 tests with N<1000 is statistically unsound for discovery. |

## Task Dependencies & Execution Order

The following task ordering ensures data flows correctly and dependencies are met:

- **T090 (Synthetic Data Generator)** must complete before **T006d_init** (Initialize Checksum State) to ensure the generator script checksum is recorded.
- **T014b (Pre-screening)** and **T022 (Compositionality Check)** must complete **before** **T021f_algo (Implement Dynamic Collinearity Detection)**. The collinearity detection requires pre-screened, compositionally-aware data.
- **T021f_algo (Collinearity Detection)** must complete **before** **T021 (Implement Correlation Method Selection)**. The method selection logic must account for collinearity flags.
- **T021f_io (Write Collinearity Output)** depends on T021f_algo. T021f_algo is in Phase 4. T021f_io is in Phase 4. The dependency is correct, but ensure T021f_algo completes before T021f_io starts.
- **T021 (Implement Correlation Method Selection)** depends on T020, T020a, T022a, T021f_io. T020, T020a, T022a, T021f_io are in Phase 4. T021 is in Phase 4.
- **T025 (FDR Correction)** must complete before **T078 (Sensitivity)**, **T080 (Power)**, and **T087 (Report)**.
- **T013 (Validation Halt)** must complete before **T015 (Orchestration)**.
- **T016 (Timeout Enforcement)** must actively halt the pipeline if the 6-hour limit is exceeded (using `signal`/`subprocess`).
- **T013b (Success Artifact)** must generate `validation_success_report.json` if ingestion succeeds, including variable counts.
- **T080 (Power Analysis)** MUST generate `power_analysis_report.json` containing the full calculation trace (effect size, alpha, power, required N, observed N) to satisfy SC-005 verification.
- **T087 (Report Generation)** MUST include a regex-based scan of all logs and reports for causal language and generate `causal_scan_report.json`. If violations are found, the pipeline must halt.
- **T047b (Method Log)** must write `data/metadata/method_selection_log.json` with `zero_inflation_warning` flag and reason.
- **T079 (VIF Calculation)** must internally perform the matrix rank check (T021f_algo logic) and exclude dependent pairs before calculating VIF, ensuring a single source of truth.
- **T021 (Method Selection)** must perform distribution tests on `abundance_count` and `value` attributes defined in `data-model.md`.

## Plan Completeness & Methodological Rigor

- **FR-001 (Ingestion)**: Validated by T013.
- **FR-002 (Method Selection)**: Validated by T021, with explicit checks for ZINB, Spearman, Pearson.
- **FR-003 (FDR)**: Validated by T025 using Benjamini-Hochberg.
- **FR-004 (Associational)**: Validated by T087 causal scan.
- **FR-005 (Sensitivity)**: Validated by T078.
- **FR-006 (Collinearity)**: Validated by T079 and T021f_algo.
- **FR-007 (Time)**: Validated by T016.
- **SC-001**: Validated by T013b.
- **SC-002**: Validated by T078.
- **SC-003**: Validated by T079.
- **SC-004**: Validated by T016.
- **SC-005**: Validated by T080 and `power_analysis_report.json`.

## Compute Feasibility

- **CPU-First**: The entire pipeline (ZINB, SparCC, VIF, Power) is designed to run on a standard multi-core CPU with sufficient RAM.
- **Reproducibility**: **No GPU fallback is permitted**. All runs must be reproducible on a fresh GitHub Actions runner.
- **Data Streaming**: If the dataset exceeds memory, `datasets.load_dataset(..., streaming=True)` will be used to process data in chunks.
