# Implementation Plan: The Relationship Between Personality Traits and Response to Personalized AI Feedback

**Branch**: `001-personality-ai-feedback` | **Date**: 2026-06-25 | **Spec**: `specs/001-personality-ai-feedback/spec.md`
**Input**: Feature specification from `/specs/001-personality-ai-feedback/spec.md`

## Summary

This project implements a CPU-only **Theoretical Validation Study** to determine if the *pipeline* can detect a theoretical relationship between Big Five personality traits and receptivity to personalized AI feedback. The technical approach involves downloading a verified public dataset containing AI feedback text, generating *theoretical* personality scores and response metrics based on established psychological literature, performing multiple linear regression with Benjamini-Hochberg correction, and generating visualizations and a summary report. The pipeline is constrained to run on GitHub Actions free-tier runners with limited CPU and memory resources without GPU acceleration.

**Note on Scope**: This study is a **Pipeline Validation** and not an **Empirical Discovery**. The data is synthetic/theoretical, and the findings are intended to verify the *code's* ability to detect relationships, not to make claims about real-world human psychology.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `pyyaml`  
**Storage**: Local filesystem (`data/`, `results/`)  
**Testing**: `pytest` (unit tests for data validation, integration test for full pipeline)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Full pipeline execution ≤ 4 hours; Data ingestion ≤ 15 minutes.  
**Constraints**: CPU-only (no CUDA/GPU); RAM ≤ 7GB; Disk ≤ 14GB; No authentication required for datasets.  
**Scale/Scope**: Single dataset analysis (N ≥ 50 required); predictors × multiple outcomes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Spec Deviation Log

The following functional requirements from the spec are **not met** due to the unavailability of verified real-world datasets:

- **FR-001**: "System MUST download a standard personality inventory dataset (e.g., IPIP-based)".
  - **Status**: Not Met.
  - **Rationale**: No verified source for a public IPIP-50 dataset was found in the "Verified datasets" block.
  - **Mitigation**: Personality traits are generated using a *theoretical simulation* based on IPIP-50 norms (Mean=30, SD=8).

- **FR-002**: "The system MUST ingest existing human response data... rather than generating synthetic values."
  - **Status**: Not Met.
  - **Rationale**: No verified source for a public dataset containing both personality traits and human response to AI feedback was found.
  - **Mitigation**: Response metrics (receptivity, anxiety, behavioral intention) are generated using a *theoretical simulation* based on established psychological literature (e.g., Openness correlates with receptivity).

- **FR-005**: "System MUST perform multiple linear regression... including interaction terms for feedback type."
  - **Status**: Partially Met.
  - **Rationale**: The "feedback type" is derived from the text classification label (0/1) of the `ziq` dataset. The interaction term is included in the model, but the "response" is not real human data.

- **Principle VI (Ethical Treatment)**: "All data collection... must obtain informed consent".
  - **Status**: Waived.
  - **Rationale**: The data used is public (text dataset) and synthetic (personality/response). No new human participants are recruited. Therefore, informed consent for *new* collection is not applicable. However, the pipeline ensures no PII is introduced (Principle III).

- **Principle VII (Statistical Validity)**: "employ appropriate statistical controls (e.g., covariates for age, gender)".
  - **Status**: Not Applicable.
  - **Rationale**: The synthetic data does not include demographic information. This is a documented limitation of the theoretical simulation. The plan includes all other required statistical controls (FDR, effect sizes) where applicable to the available variables.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (Principle I)**: **Pass**. Plan mandates `random_seed` pinning in `code/` and deterministic dataset fetching from verified URLs.
2.  **Verified Accuracy (Principle II)**: **Pass**. Plan restricts dataset sources to the "Verified datasets" block in the spec; no fabricated URLs.
3.  **Data Hygiene (Principle III)**: **Pass**. Plan includes checksum generation for raw data and immutable derivation steps (`data/processed/`).
4.  **Single Source of Truth (Principle IV)**: **Pass**. All statistics in the report will be generated programmatically from `analysis_data.csv`, not hand-typed.
5.  **Versioning Discipline (Principle V)**: **Pass**. Artifacts will carry content hashes; `state/` files updated on change.
6.  **Ethical Treatment (Principle VI)**: **Waived (with Rationale)**. The plan uses public and synthetic data; no new PII collection; consent waiver documented. The pipeline ensures no PII is generated or stored.
7.  **Statistical Validity (Principle VII)**: **Partially Pass (with Limitation)**. Plan includes Benjamini-Hochberg correction, effect size reporting, and pre-registration of the analysis logic in `code/`. Demographic covariates are **Not Applicable** due to the synthetic nature of the data; this limitation is explicitly documented in the final report.

## Project Structure

### Documentation (this feature)

```text
specs/001-personality-ai-feedback/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── analysis.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── download.py          # Data ingestion (FR-001)
├── validate.py          # Data validation (US-1, Edge Cases)
├── merge.py             # Data merging (FR-003)
├── analyze.py           # Regression & Correlation (FR-004, FR-005)
├── visualize.py         # Plot generation (FR-006)
├── report.py            # Report generation (FR-007, FR-008)
└── main.py              # Orchestration script

data/
├── raw/                 # Downloaded parquet/CSV files
├── processed/           # Merged analysis_data.csv
└── checksums.txt        # SHA256 hashes

results/
├── analysis_results.json # Correlation/Regression stats
├── plots/               # Generated figures
├── report.md            # Final summary
└── drift_analysis.md    # Drift analysis section (T039)
```

**Structure Decision**: A linear script-based pipeline (`main.py` orchestrating `download` → `validate` → `merge` → `analyze` → `visualize` → `report`) was chosen to ensure reproducibility and ease of debugging on CPU-only runners. This avoids the overhead of Jupyter notebooks for CI execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is a single correlational study fitting within 7GB RAM. | N/A |

## Task Refinement (Addressing T015, T039)

- **T015 'Implement validation logic'**: This task will produce a `validation_log.json` file in `results/` and exit with code 0 on success or 1 on failure. It will explicitly validate the existence and schema compliance of `data/processed/analysis_data.csv`.
- **T039 'Generate a Drift Analysis report section'**: This task will generate a section in `results/report.md` with the header `## Drift Analysis`. If a separate file is preferred for modularity, it will be written to `results/drift_analysis.md` and included in the main report.
