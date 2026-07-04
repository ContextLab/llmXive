# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

**Branch**: `001-gene-regulation` | **Date**: 2023-10-27 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a reproducible, CPU-tractable statistical pipeline to investigate the correlational relationship between gut microbiome composition (alpha-diversity and taxon-level abundance) and sleep quality metrics. The pipeline ingests 16S rRNA OTU count tables and metadata, filters for antibiotic use and missing data, computes diversity indices, performs Spearman rank correlations with Benjamini-Hochberg correction, adjusts for confounders using permutation-based partial correlation, and generates visualizations. The implementation strictly adheres to the project constitution regarding reproducibility, data hygiene, and statistical rigor, ensuring all steps run within the constraints of a free-tier GitHub Actions runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-bio`, `scipy`, `seaborn`, `matplotlib`, `requests`, `numpy`, `pyyaml`, `pingouin`  
**Storage**: Local CSV/Parquet files (no external database); data stored in `data/` and processed in memory with chunking where necessary.  
**Testing**: `pytest` (unit tests for data filtering, correlation logic, proxy fallback, and file generation).  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Data analysis pipeline / CLI.  
**Performance Goals**: Complete end-to-end analysis in < 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU; no heavy model training; strict adherence to `scikit-bio` for diversity; Benjamini-Hochberg for FDR control; `pingouin` for partial correlation.  
**Scale/Scope**: Processing of public microbiome datasets (American Gut Project style); expected sample size > 30 after filtering.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. `requirements.txt` pins all versions. Data fetched from canonical sources only. |
| **II. Verified Accuracy** | **PENDING DATA (HALT IF UNVERIFIED)** | All dataset URLs in `research.md` will be validated against the "Verified datasets" block. If the required variables (sleep, antibiotic) are missing from the verified block, the pipeline halts. No simulation of data. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations written to new files. Checksums recorded in state. No PII committed. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` will trace to exactly one row in `data/` and one block in `code/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. `updated_at` timestamps managed by the system. |
| **VI. Statistical Rigor** | **PASS** | Benjamini-Hochberg correction mandatory for all multiple tests. Non-parametric (Spearman) tests used by default. **Mandatory**: `pingouin` for Permutation-based Partial Correlation (no custom fallback). |
| **VII. Cross-Source Harmonization** | **PASS** | `data/data_mapping_table.yaml` generated in Phase 0. Samples lacking compatible sleep metadata excluded (not imputed). |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Path config, seed management
├── ingestion.py         # FR-001, FR-009: Download, filter, merge, proxy logic
├── diversity.py         # FR-002, FR-003: Alpha-diversity calc
├── correlation.py       # FR-004, FR-007: Spearman, FDR
├── confounder_adjustment.py # FR-008: Permutation-based partial correlation (pingouin)
├── visualization.py     # FR-005: Plots
├── sensitivity.py       # SC-004: Sensitivity analysis
├── main.py              # Orchestration script
└── utils.py             # Helpers

data/
├── raw/                 # Downloaded raw files (checksummed)
├── processed/           # Filtered/merged CSVs
├── data_mapping_table.yaml # Generated mapping table (Principle VII)
└── checksums.json       # Artifact hashes

results/
├── correlation_results.csv
├── adjusted_correlation_results.csv
├── sensitivity_analysis.csv
├── scatter_shannon_sleep.png
└── boxplot_diversity_sleep_quartile.png

tests/
├── test_ingestion.py        # Includes test for proxy fallback (FR-009)
├── test_correlation.py
├── test_confounder_adjustment.py
└── test_visualization.py

requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead for a data analysis pipeline. All scripts reside in `code/` with clear separation of concerns (ingestion, analysis, viz). This aligns with the requirement for a single-source-of-truth pipeline and simplifies the reproducibility test on GitHub Actions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

*No complexity violations detected. The design is minimal and directly maps to the spec requirements.*

## Implementation Phases

### Phase 0: Data Ingestion & Feasibility Check (FR-001, FR-009, SC-002)
1.  **Load & Validate**: Load raw data from verified sources.
    *   **Check**: Verify `sleep_efficiency` OR `sleep_quality` (proxy) and `antibiotic_use_last_3mo` exist.
    *   **Action**: If neither exists, **HALT** with "Data Unavailable" error. If only proxy exists, log "Scope Narrowed: Using Self-Reported Sleep Quality".
2.  **Filter**: Remove samples with `antibiotic_use_last_3mo == True` or missing sleep data.
3.  **Mapping**: Generate `data/data_mapping_table.yaml` documenting sample ID alignment.
4.  **Test**: Run `tests/test_ingestion.py` including a specific test case for the proxy fallback logic (mocking missing primary variables).
5.  **Output**: `data/processed/analysis_data.csv`.

### Phase 0.5: Power & Sample Size Check (FR-008, SC-004)
1. **Calculate**: Compute effective N and Minimum Detectable Effect Size (MDES) for r=0.3 at [deferred] power.
2.  **Decision**: If N < 30 OR MDES > 0.3, **HALT** with "Insufficient Power" warning.
3.  **Output**: Log of power analysis.

### Phase 1: Diversity Calculation (FR-002, FR-003)
1.  **Compute**: Calculate Shannon and Simpson indices using `scikit-bio`.
2.  **Filter**: Exclude samples with zero OTU counts.
3.  **Contract**: Validate output against `contracts/diversity_metrics.schema.yaml`.
4.  **Output**: Append diversity columns to `analysis_data.csv`.

### Phase 2: Alpha-Diversity Correlation (FR-004)
1.  **Correlate**: Compute Spearman correlations between diversity indices and sleep metrics.
2.  **Correct**: Apply Benjamini-Hochberg correction.
3.  **Output**: `results/correlation_results.csv`.

### Phase 3: Taxon-Level Correlation (FR-007, SC-001)
1.  **Transform**: Apply Centered Log-Ratio (CLR) transformation to OTU counts.
2.  **Correlate**: Compute Spearman correlations between CLR-transformed taxa and sleep metrics.
3.  **Correct**: Apply Benjamini-Hochberg correction (thousands of tests).
4.  **Risk Note**: Explicitly acknowledge in logs that spurious correlations may persist despite CLR.
5.  **Output**: Append taxon-level results to `results/correlation_results.csv`.

### Phase 4: Confounder Adjustment (FR-008)
1.  **Adjust**: Perform Permutation-based Partial Correlation (using `pingouin.partial_corr(..., method='spearman', permutation=1000)`) adjusting for age, BMI, diet, medication.
2.  **Fallback**: If N < 20 globally, attempt **Stratified Partial Correlation** (within BMI/Diet strata) and aggregate.
3.  **Fail-Stop**: If `pingouin` is unavailable or permutation test fails, **HALT** with "Confounder Adjustment Failed" error. **No custom fallback allowed.**
4.  **Contract**: Validate output against `contracts/adjusted_correlation_results.schema.yaml`.
5.  **Output**: `results/adjusted_correlation_results.csv`.

### Phase 5: Sensitivity Analysis (SC-004)
1.  **Sweep**: Re-calculate significance counts for p < {, 0.05, 0.1}.
2.  **Output**: `results/sensitivity_analysis.csv`.
3.  **Gate**: If results show high variance (e.g., sign flips across cutoffs), flag study as "Inconclusive" in the final report.

### Phase 6: Visualization & Reporting (FR-005)
1.  **Plot**: Generate scatter plots and boxplots.
2.  **Output**: Save PNGs to `results/`.
3.  **Report**: Generate summary table including power analysis, sensitivity results, and confounder-adjusted findings.

## Assumptions

- The study assumes the availability of **Self-Reported Sleep Quality** as the primary target, acknowledging that 'Sleep Efficiency' (clinical) is likely unavailable in public datasets.
- The relationship between gut microbiome diversity and sleep quality is observational; therefore, findings will be framed as associational rather than causal.
- The `pingouin` library is available and stable on the GitHub Actions runner for permutation-based partial correlation.
- CLR transformation reduces but does not eliminate the risk of spurious correlations in taxon-level analysis.