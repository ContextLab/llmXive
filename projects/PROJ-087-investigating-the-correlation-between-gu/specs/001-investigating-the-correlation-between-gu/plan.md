# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

**Branch**: `001-gene-regulation` | **Date**: 2026-06-26 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `specs/001-gene-regulation/spec.md`
**Status**: **BLOCKED** (Data Availability Gap)

## Summary

This plan implements a statistical pipeline to investigate the correlation between gut microbiome alpha-diversity indices and sleep quality metrics. **CRITICAL STATUS**: The project is currently **BLOCKED** because the provided "# Verified datasets" block contains NO dataset that includes both 16S rRNA OTU data AND sleep quality metrics (efficiency, duration). The American Gut Project (AGP) is assumed in the spec, but no verified URL for AGP with sleep metadata exists in the provided list.

The pipeline is designed to **fail fast** if a valid source is not found, preventing any attempt to run on mismatched or missing data. The implementation includes a mandatory "Data Feasibility Check" that must pass before any analysis code is executed.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-bio`, `scipy`, `matplotlib`, `seaborn`, `requests`  
**Storage**: Local CSV/Parquet files (no external DB)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Data analysis pipeline  
**Performance Goals**: Complete analysis within 6 hours, memory usage < 7 GB (if data were available)  
**Constraints**: No GPU, no heavy LLM inference, **must halt if data source is missing**  
**Scale/Scope**: Public dataset processing (currently unfeasible due to missing data)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned dependencies (`requirements.txt`), random seed setting, and fetching from canonical sources (if available).
- **II. Verified Accuracy**: **FAILED**. The required dataset (AGP with sleep metadata) is NOT in the "# Verified datasets" block. The plan explicitly halts due to this failure.
- **III. Data Hygiene**: The plan includes checksumming of downloaded files and strict separation of raw vs. derived data.
- **IV. Single Source of Truth**: All statistics in the final report will be generated programmatically from the `data/` artifacts, ensuring traceability.
- **V. Versioning Discipline**: The plan includes content hashing for output artifacts to detect staleness.
- **VI. Statistical Rigor**: The plan explicitly includes Benjamini-Hochberg correction for multiple comparisons and uses non-parametric Spearman correlation as required.
- **VII. Cross-Source Metadata Harmonization**: The plan defines a strict exclusion rule for samples lacking compatible sleep metadata, avoiding imputation.

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
projects/PROJ-087-investigating-the-correlation-between-gu/code/
├── data/
│   ├── raw/             # Downloaded raw files
│   └── processed/       # Cleaned analysis-ready files
├── src/
│   ├── ingestion.py     # Data download and filtering (with feasibility check)
│   ├── diversity.py     # Alpha-diversity computation (with rarefaction)
│   ├── correlation.py   # Statistical tests
│   ├── viz.py           # Plot generation
│   └── main.py          # Pipeline orchestrator
├── tests/
│   ├── test_ingestion.py
│   ├── test_correlation.py
│   └── test_viz.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Selected a modular single-project structure (`src/`, `data/`, `tests/`) suitable for a data analysis pipeline. This keeps the codebase simple and focused on the specific statistical workflow without unnecessary abstraction layers.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Data Availability Block | The required dataset (OTU + Sleep) is not in the verified list. | No alternative dataset in the verified list contains both modalities. |
| Spec Assumption Gap | The spec assumes AGP has sleep metrics, but this is unverified. | The plan cannot proceed without a verified source. |

## Phase Execution Order

1. **Phase 0: Research & Data Strategy** (`research.md`)
   - Identify and verify data sources (American Gut Project).
   - **CRITICAL**: Confirm variable availability (sleep metrics, OTU counts) in verified sources.
   - **BLOCKING CHECK**: If no verified source contains both OTU and sleep data, the pipeline halts.

2. **Phase 1: Data Model & Contracts** (`data-model.md`, `quickstart.md`, `contracts/`)
   - Define input/output schemas.
   - Set up project structure and dependencies.
   - Create validation contracts.

3. **Phase 2: Implementation** (Code generation by Implementer)
   - **Step 0: Data Feasibility Check**: Verify source existence and column presence.
   - Ingestion script (download, filter).
   - Diversity computation (with rarefaction).
   - Correlation analysis with FDR correction.
   - Visualization generation.

4. **Phase 3: Testing & Validation**
   - Run unit tests on synthetic data.
   - Validate end-to-end pipeline on GitHub Actions.
   - Verify reproducibility (hash comparison).

## Risk Mitigation

- **Dataset Unavailability**: The ingestion script will implement exponential backoff with a limited number of retries and fail gracefully with a clear error message if the source is unreachable. **If the source is not in the verified list, the pipeline halts immediately.**
- **Memory Constraints**: The pipeline will process data in chunks if the dataset exceeds available RAM, ensuring the memory limit is not breached.
- **No Significant Results**: The report generation will explicitly state "No significant associations found" if no correlations survive FDR correction, preventing silent failures.
- **Collinearity**: The plan acknowledges that diversity indices are correlated and reports them descriptively without claiming independent causal effects.
- **Sequencing Depth**: The plan includes a rarefaction/normalization step to prevent sequencing depth artifacts from biasing diversity indices.

## Success Criteria Alignment

- **SC-001**: Exclusion rates will be logged and reported against the initial sample size. **If no dataset is found, SC-001 is marked as 'Unmeasurable'.**
- **SC-002**: Correlation strength and significance will be measured against the biological benchmark (|r| > 0.3). **If no dataset is found, SC-002 is marked as 'Blocked'.**
- **SC-003**: FDR control will be verified by checking adjusted p-values.
- **SC-004**: Resource usage will be monitored and reported to ensure compliance with GitHub Actions limits.
- **SC-005**: Reproducibility will be validated via SHA-256 hash comparison of outputs on clean runs.

## Functional Requirements (Conditional)

- **FR-001**: System MUST attempt to download and parse pre-processed 16S rRNA OTU count tables and metadata from the American Gut Project public repository **IF a verified URL is found in the '# Verified datasets' block**. If no verified URL exists, the system MUST halt with a clear error message. (See US-1).
- **FR-002**: System MUST filter samples to exclude those where the `antibiotic_use_last_3m` field is true and those lacking valid `sleep_efficiency` or `sleep_duration_hours`. **If these columns are missing from the source, the system MUST halt with a clear error message.** (See US-1).
- **FR-003**: System MUST compute alpha-diversity indices (Shannon, Simpson, Observed OTUs) using `scikit-bio` or `vegan` on the filtered count tables, **including a rarefaction step to normalize sequencing depth**, ensuring the computation completes within 6 hours on a 2-core runner. (See US-2).
- **FR-004**: System MUST perform Spearman rank correlation tests between each alpha-diversity index and sleep variables. Additionally, the system MUST flag any correlation with |r| > 0.3 as a "moderate correlation" for reporting purposes, while noting that Spearman detects only monotonic trends. (See US-2).
- **FR-005**: System MUST apply Benjamini-Hochberg correction to p-values to control for false discovery rate across the set of alpha-diversity vs. sleep metric comparisons. (See US-2).
- **FR-006**: System MUST generate scatterplots with regression lines and boxplots by sleep quality quartile for significant findings. (See US-3).
- **FR-007**: System MUST execute the entire analysis pipeline within 7 GB RAM and 6 hours on a GitHub Actions ubuntu-latest runner (2 vCPUs). (See US-2).