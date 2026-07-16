# Implementation Plan: Assessing Statistical Significance of Observed Correlations in Public Databases

**Branch**: `001-assess-correlation-significance` | **Date**: 2026-07-05 | **Spec**: `specs/001-assess-correlation-significance/spec.md`
**Input**: Feature specification from `/specs/001-assess-correlation-significance/spec.md`

## Summary

This feature implements a permutation-based statistical engine to assess the significance of network statistics (mean absolute correlation, edge density, max correlation, clustering coefficient) derived from multivariate datasets. The system will generate empirical null distributions by permuting data columns, calculate two-sided p-values, apply Benjamini-Yekutieli (BY) correction for multiple testing, and perform threshold sensitivity analysis. The implementation strictly adheres to CPU-only constraints for GitHub Actions free-tier execution.

**Critical Governance Note**: This plan proposes an amendment to Constitution Principle VII to replace the Benjamini-Hochberg (BH) procedure with the Benjamini-Yekutieli (BY) procedure. Execution of the primary analysis is **blocked** until this amendment is formally ratified by the Advancement-Evaluator Agent, as the current Constitution mandates BH, which is scientifically unsound for dependent network statistics.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `networkx`, `matplotlib`, `seaborn`
**Storage**: Local filesystem (`data/`, `code/`, `output/`)
**Testing**: `pytest` (unit tests for permutation logic, integration tests for pipeline)
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, no GPU)
**Project Type**: Data analysis CLI / Research pipeline
**Performance Goals**: Complete full pipeline (3+ valid datasets, 1,000 permutations) within 6 hours.
**Constraints**: No GPU usage; memory footprint < 7GB; strict handling of missing data (drop rows); no causal language in output.
**Scale/Scope**: Multiple valid datasets (from fallback list if primary fails), a set of network statistics, correlation thresholds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check & Amendment Record

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Amendment Proposal**:
Constitution Principle VII currently mandates the Benjamini-Hochberg (BH) procedure. However, the Functional Requirements (FR-004) and the statistical nature of network statistics (arbitrary dependence) require the Benjamini-Yekutieli (BY) procedure. BH assumes independence or positive dependence; BY is robust to arbitrary dependence.
**Proposed Amendment Text**: Replace "Benjamini-Hochberg procedure" with "Benjamini-Yekutieli procedure" in Constitution Principle VII.
**Rationale**: Network statistics (density, clustering) are highly correlated. Using BH would fail to control the False Discovery Rate (FDR) at the nominal level, leading to inflated false positives. This is a scientific necessity, not a preference.
**Status**: **PENDING RATIFICATION**. The plan will not proceed to Phase 1 until the Advancement-Evaluator ratifies this amendment.

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Plan mandates pinned `requirements.txt`, random seeds, and raw data checksums. |
| II. Verified Accuracy | PASS | Research.md cites ONLY verified URLs provided in the prompt block or standard UCI archive links. |
| III. Data Hygiene | PASS | Plan includes checksumming step; raw data preserved; derivations in new files. |
| IV. Single Source of Truth | PASS | All figures/stats trace to `data/` and `code/`. Amendment proposal ensures SSoT is updated. |
| V. Versioning Discipline | PASS | Artifacts will carry content hashes; state file updated on change. |
| VI. Permutation-Based Null Validation | PASS | Core engine implements a sufficient number of permutations per dataset (amended from an originally higher count for feasibility) as required. |
| VII. Multiple Testing Correction Discipline | **CONFLICTING** | **AMENDMENT PROPOSED**: Constitution mandates BH; Plan requires BY for scientific validity. Execution blocked until ratified. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-correlation-significance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-297-assessing-statistical-significance-of-ob/
├── data/
│   ├── raw/             # Downloaded CSVs (checksummed)
│   └── processed/       # Cleaned dataframes (dropped missing)
├── code/
│   ├── __init__.py
│   ├── config.py        # Paths, seeds, thresholds
│   ├── loaders.py       # Dataset ingestion
│   ├── stats_engine.py  # Permutation, correlation, network stats
│   ├── correction.py    # BY procedure
│   ├── viz.py           # Heatmaps, histograms
│   └── main.py          # Orchestration script
├── tests/
│   ├── unit/
│   │   ├── test_stats_engine.py
│   │   └── test_correction.py
│   └── integration/
│       └── test_pipeline.py
├── output/
│   ├── results/         # CSVs of p-values, q-values
│   ├── plots/           # PNGs of null distributions
│   └── reports/         # Final summary tables
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure (`code/`) chosen for simplicity. No frontend/backend split required; this is a batch processing research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Benjamini-Yekutieli (BY) vs. Benjamini-Hochberg (BH) | Spec requires control of FDR under *dependence*. BH assumes independence or positive dependence; BY is robust to arbitrary dependence. Constitution Principle VII requires amendment. | BH is simpler but violates FR-004 and leads to scientific invalidity. |
| 1,000 Permutations | Required by FR-003 (amended from [deferred]) for stable empirical p-values while ensuring runtime < 6h on CPU. Resolution is 0.001, sufficient for α=0.05. | A large number of permutations risks timeout on a 2-CPU runner for clustering coefficient. A limited number of permutations may be insufficient for accuracy. |
| Threshold Sensitivity Sweep | Required by US-3 and FR-005 to assess robustness of findings to arbitrary cutoffs. | Single threshold analysis would fail to demonstrate robustness, a key research question. |
| Fallback Dataset Strategy | Primary 6 UCI datasets may have <20 variables. Fallback ensures multiple valid datasets are found. | Relying solely on the primary list risks a null result due to data unavailability. |

## Implementation Phases

### Phase 0: Synthetic Validation & Data Availability Gate (Blocking)

**Goal**: Validate the null model and ensure data availability before main analysis.

1.  **Synthetic Dataset Generation (FR-009)**:
    *   Generate a synthetic dataset with known independence (identity covariance matrix, N=500, V=20).
    *   Run the permutation engine (N=1,000) on this synthetic data.
 * **Success Criterion**: The observed statistics must fall within the central [deferred] of the null distribution (p > 0.05) for at least 95% of the runs.
    *   **Gate**: If this fails, the pipeline halts with an error. The null model is invalid.

2.  **Data Availability Gate (with Fallback)**:
    *   Download the target datasets (Wine, Abalone, Breast Cancer, Student Performance, Air Quality, Concrete) from verified UCI sources.
    *   For each dataset:
        *   Drop rows with missing values.
        *   Drop constant variables.
        *   Count remaining continuous variables.
    *   **Fallback Strategy**: If a dataset has < 20 continuous variables, it is excluded. If the primary list yields < 3 valid datasets, the pipeline automatically queries the UCI repository for the next available multivariate datasets with >=20 continuous variables (e.g., 'Parkinsons', 'Libras', 'Isolet') until 3 valid datasets are found.
    *   **Gate**: If an insufficient number of valid datasets remain after fallback, the pipeline halts with an error. The study cannot proceed with insufficient data.

### Phase 1: Primary Analysis (Pearson Correlation)

**Goal**: Compute observed statistics, generate null distributions, and calculate significance.

1.  **Correlation & Graph Construction**:
    *   Compute Pearson correlation matrix for each valid dataset.
    *   Construct an undirected weighted graph by thresholding absolute Pearson correlations at |r| > 0.3.
    *   Compute observed statistics: Mean Absolute Correlation, Edge Density, Max Absolute Correlation, Average Clustering Coefficient.
    *   *Note*: Spearman matrices are computed and stored (FR-002) but **excluded** from this phase.

2.  **Permutation Engine**:
    *   For each dataset, perform a substantial number of random permutations of the data columns (preserving marginals).
    *   For each permutation, compute the four network statistics.
    *   *Optimization*: If a dataset has >50 variables, reduce permutation count for clustering coefficient to 500 to ensure runtime, while other statistics use 1000.
    *   Store null distributions.

3.  **Significance Testing**:
    *   Calculate two-sided empirical p-values using a standard permutation-based estimator that accounts for the observed statistic relative to the permuted distribution.
    *   Apply Benjamini-Yekutieli (BY) procedure across all tests (valid datasets × 4 statistics).
    *   Flag significant findings (q < 0.05).

### Phase 2: Exploratory Analysis (Spearman Correlation)

**Goal**: Compute Spearman correlations for exploratory comparison (FR-002).

1.  **Spearman Computation**:
    *   Compute Spearman correlation matrices for each valid dataset.
    *   Store matrices in `output/exploratory/`.
    *   **Note**: Spearman results are NOT included in the primary significance testing or BY correction. They are for descriptive comparison only.

### Phase 3: Sensitivity Analysis & Visualization

**Goal**: Assess robustness to threshold choice and generate visualizations.

1.  **Threshold Sweep**:
    *   Re-run the primary analysis (Phases of primary analysis) for thresholds |r| ∈ {low, moderate, specific}, beginning with a low-magnitude baseline.
    *   Record the variation in significant counts and density metrics.

2.  **Visualization**:
    *   Generate heatmaps of observed vs. null correlation matrices.
    *   Generate histograms of null distributions with observed values overlaid.
    *   Generate sensitivity plots.

### Phase 4: Reporting

**Goal**: Generate final summary tables and reports.

1.  **Summary Table**:
    *   Output a CSV with dataset_id, statistic_name, threshold, observed_value, p_value, q_value, is_significant.
    *   Explicitly state that significant results indicate "non-random association" (FR-007).

2.  **Sensitivity Report**:
    *   Output a table showing significant counts for each threshold.

## Data Flow & Dependencies

1.  **Phase 0** (Synthetic Validation) MUST pass before **Phase 0** (Data Gate).
2.  **Phase 0** (Data Gate) MUST pass before **Phase 1** (Primary Analysis).
3.  **Phase 1** (Primary Analysis) MUST complete before **Phase 2** (Exploratory) and **Phase 3** (Sensitivity).
4.  **Phase 3** (Sensitivity) MUST complete before **Phase 4** (Reporting).
5.  All phases MUST complete within 6 hours on the target runner.
6.  **Constitutional Gate**: Phase 1 execution is blocked until Constitution Principle VII is amended to mandate BY.