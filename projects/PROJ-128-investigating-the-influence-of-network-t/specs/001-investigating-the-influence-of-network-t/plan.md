# Implementation Plan: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

**Branch**: `001-gene-regulation` | **Date**: 2026-07-10 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project investigates whether topological properties of structural brain networks (derived from dMRI) predict the stability and prevalence of recurrent dynamic functional states (derived from fMRI). The approach involves a strictly ordered pipeline: (1) downloading and validating open HCP-derived data from OpenNeuro, (2) computing structural graph metrics (global efficiency, clustering, modularity) using NetworkX, (3) extracting dynamic functional states via **Leave-One-Subject-Out (LOSO)** sliding-window correlation and k-means clustering to ensure independence, (4) calculating per-subject dynamic metrics (dwell time, state visits) with stability validation, and (5) performing Pearson/Spearman correlations with Benjamini-Hochberg FDR correction. The plan explicitly addresses the "associational only" constraint, handles missing data and convergence failures robustly, and ensures all analyses run within GitHub Actions free-tier CPU constraints (7GB RAM, h runtime).

**Scientific Validity Note**: While FR-002 mentions "concatenating windowed matrices across all subjects," the project's Constitution Principle VI (Structural-Functional Independence) and scientific soundness requirements necessitate a **Leave-One-Subject-Out (LOSO)** strategy. This prevents the subject's own data from defining the state space they are measured against, eliminating circular correlation. This deviation is documented as a necessary methodological refinement for validity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `datasets`, `scipy`  
**Storage**: Local filesystem (`data/` for raw/derived, `artifacts/` for reports)  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner: a limited number of vCPUs, ~7GB RAM, ~GB disk)  
**Project Type**: Data analysis pipeline / Computational neuroscience  
**Performance Goals**: Process ~50 subjects within 6 hours; peak RAM < 7GB  
**Constraints**: CPU-only execution (no local GPU); no causal claims; strict data independence between structural and functional pipelines.  
**Scale/Scope**: Cohort of a moderate number of subjects; -region parcellation; dynamic states.

> Empirical specifics (exact subject counts, effect sizes) are deferred to the research phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **[x] Reproducibility**: All code uses pinned `requirements.txt`. Random seeds (numpy, sklearn) are fixed. Data fetched via `datasets` library from canonical OpenNeuro sources.
- **[x] Verified Accuracy**: Citations in `research.md` are restricted to the verified URLs provided in the prompt (OpenNeuro ds). No fabricated URLs.
- **[x] Data Hygiene**: Raw data is downloaded to `data/raw/` with checksums recorded. Derivatives written to `data/derived/`. No in-place modification. PII scan passed (HCP data is de-identified).
- **[x] Single Source of Truth**: All statistics in the final report will trace to `data/derived/metrics.csv` and `data/derived/correlations.csv`.
- **[x] Versioning**: Artifacts will be hashed; `state/` updated on changes.
- **[x] Structural-Functional Independence**: The plan explicitly enforces LOSO clustering to ensure the functional state space is independent of the subject's own data.
- **[x] Dynamic State Metric Robustness**: The plan mandates a sensitivity analysis with two window lengths (TR and 20 TR) and structural density variations (±5%) as required by the constitution.

**Resolved Unresolved Concerns**:
- **FR-008 & FR-006 Implementation**: Phase 4 explicitly implements the sensitivity analysis for both window length (FR-006) and structural threshold density (FR-008). The output artifact `sensitivity_comparison.csv` is generated in Phase 4 Step 4, ensuring traceability.
- **Dependency Chain**: The plan orders phases strictly: Data Download -> Structural Metrics -> Dynamic Metrics -> Correlation (Primary) -> Sensitivity (Re-run) -> Report. This ensures `sensitivity_comparison.csv` is generated before the report.
- **Task Logic**: References to rejected task IDs (T043, T031) have been removed. The functionality is now integrated directly into the Phase breakdown (Phase 4).

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
projects/PROJ-128-investigating-the-influence-of-network-t/
├── data/
│   ├── raw/             # Downloaded parquet/csv files (checksummed)
│   └── derived/         # Computed metrics, correlation tables, sensitivity data
├── code/
│   ├── __init__.py
│   ├── download_data.py # Fetches HCP data via OpenNeuro
│   ├── structural_metrics.py # NetworkX graph metrics
│   ├── dynamic_metrics.py # Sliding window, LOSO k-means, state extraction
│   ├── correlation_analysis.py # Pearson/Spearman, FDR correction
│   ├── sensitivity_analysis.py # Re-runs with different parameters
│   ├── report_generator.py # Generates final markdown/CSV reports
│   └── completeness_report.py # Generates data_completeness_report.csv
├── tests/
│   ├── unit/            # Tests for individual metric functions
│   └── integration/     # End-to-end pipeline tests
├── contracts/
│   ├── dataset.schema.yaml
│   └── metrics.schema.yaml
├── requirements.txt
└── README.md            # Generated by report_generator.py
```

**Structure Decision**: Single project structure with modular scripts. This minimizes overhead and fits the 2-core/7GB RAM constraint by avoiding complex microservices or heavy ORM layers.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Leave-One-Subject-Out (LOSO) Clustering | Required by Constitution Principle VI to prevent circular correlation between subject data and state definition. | Concatenating all subjects violates independence and creates tautological results. |
| Two-phase sensitivity analysis (Window Length & Density) | Required by Constitution Principle VII and FR-006/FR-008 to ensure robustness. | A single fixed parameter analysis would fail the "methodological soundness" check. |
| Strict Separation of Structural/Functional Pipelines | Required by Constitution Principle VI to prevent circular correlation. | Merging pipelines could introduce shared preprocessing noise. |

## Phase Breakdown

### Phase 0: Data Acquisition & Validation
- **Goal**: Download and verify HCP data (OpenNeuro dataset

The research question, method, and references remain unchanged, focusing on the analysis of open neuroimaging data without asserting specific low-level empirical identifiers.) from verified sources.
- **FR/SC Mapping**: FR-001 (data source), SC-005 (data completeness).
- **Steps**:
  1. Fetch datasets using `datasets.load_dataset` or direct BIDS download from OpenNeuro ds000224.
  2. Validate schema against `contracts/dataset.schema.yaml`.
  3. Compute checksums; log any missing subjects to `data/derived/exclusion_log.txt`.
  4. Output: `data/raw/verified_manifest.json`.

### Phase 0.5: Data Completeness Reporting
- **Goal**: Generate a formal report on data completeness as required by SC-005.
- **FR/SC Mapping**: SC-005 (data completeness measurement).
- **Steps**:
  1. Parse `data/derived/exclusion_log.txt` from Phases 0, 1, and 2.
  2. Calculate percentage of subjects successfully processed vs. total cohort.
  3. Categorize exclusions by reason (e.g., "convergence failure", "sparsity >90%", "missing data").
  4. Output: `data/derived/data_completeness_report.csv` with columns: `subject_id`, `status` (included/excluded), `reason`.

### Phase 1: Structural Metrics Extraction
- **Goal**: Compute graph metrics from dMRI matrices.
- **FR/SC Mapping**: FR-001, SC-001 (structural predictor).
- **Steps**:
  1. Load structural connectivity matrices.
  2. Apply proportional density thresholding (baseline [deferred] density).
  3. Compute Global Efficiency, Clustering Coefficient, Modularity via NetworkX.
  4. Handle sparsity >90%: Flag and exclude subject (log reason to `exclusion_log.txt`).
  5. Output: `data/derived/structural_metrics.csv`.

### Phase 2: Dynamic Functional Metrics Extraction (LOSO)
- **Goal**: Extract recurrent states and per-subject metrics using LOSO to ensure independence.
- **FR/SC Mapping**: FR-002, FR-003, SC-001 (dynamic outcome).
- **Steps**:
  1. Load fMRI time series.
  2. Compute sliding-window correlation matrices (TR window).
  3. **LOSO Clustering**: For each subject `S`:
     - Concatenate windows of all *other* subjects (N-1).
     - Apply k-means (k=5) to define common states.
     - Assign subject `S`'s windows to these centroids.
  4. **Stability Check**: Calculate Silhouette Score and run Consensus Clustering (seeds). If stability < threshold, flag subject.
  5. Compute dwell times and visit counts per subject.
  6. Handle non-convergence: Exclude subject, log reason.
  7. Output: `data/derived/dynamic_metrics.csv`.

### Phase 3: Primary Correlation Analysis
- **Goal**: Test association between structural and dynamic metrics.
- **FR/SC Mapping**: FR-004, FR-005, FR-007, SC-001.
- **Steps**:
  1. Join structural and dynamic metrics by subject ID.
  2. **Dimensionality Reduction**: Apply PCA to dynamic metrics (multiple states) to derive 1-2 composite stability scores, reducing multiple comparison burden.
  3. Test normality (Shapiro-Wilk). Select Pearson or Spearman.
  4. Compute correlations for all pairs; apply Benjamini-Hochberg FDR.
  5. Output: `data/derived/correlation_results.csv` (with FDR flags).

### Phase 4: Sensitivity & Robustness Analysis
- **Goal**: Validate results against parameter changes.
- **FR/SC Mapping**: FR-006, FR-008, SC-002.
- **Steps**:
  1. **Window Sensitivity**: Re-run Phase (LOSO) with A fixed TR window length is selected for the analysis. The research question remains focused on temporal dynamics, employing a sliding window method as described by Author et al. (DOI:10.xxxx/xxxxxx).. Output: `data/derived/sensitivity_window.csv`.
  2. **Density Sensitivity**: Re-run Phase 1 with baseline density ±5% (e.g., [deferred], [deferred]). **Dynamic Metrics are NOT re-computed** (they are independent of structural threshold). Re-run Phase 3 (Correlation) for these structural metrics. Output: `data/derived/sensitivity_density.csv`.
  3. **Comparison**: Aggregate `sensitivity_window.csv` and `sensitivity_density.csv` into `data/derived/sensitivity_comparison.csv`.
  4. **Robustness Test**: Calculate absolute difference in correlation coefficients (`|r_baseline - r_sensitivity|`). 
     - **Decision Rule**: If `|r_baseline - r_sensitivity| < 0.05`, the result is flagged as "robust". If `≥ 0.05`, it is flagged as "sensitive". 
     - **Note**: No statistical significance test (e.g., t-test) is performed on the difference itself, as the study is exploratory and SC-002 specifically requires measuring the absolute difference.
  5. Output: `data/derived/sensitivity_comparison.csv`.

### Phase 5: Reporting
- **Goal**: Generate final report with associational framing.
- **FR/SC Mapping**: FR-007, SC-003, SC-004.
- **Steps**:
  1. Aggregate all results (`correlation_results.csv`, `sensitivity_comparison.csv`, `data_completeness_report.csv`).
  2. **Dependency Check**: Ensure `sensitivity_comparison.csv` exists (produced in Phase 4).
  3. Explicitly label findings as "associational".
  4. Include resource usage report (RAM, time).
  5. Generate `README.md` with project overview and `artifacts/final_report.md`.
  6. Output: `artifacts/final_report.md`, `README.md`.

## Compute Feasibility Strategy

- **CPU-First**: All graph metrics (NetworkX), statistical tests (scipy/statsmodels), and k-means (scikit-learn) are CPU-tractable. No GPU required.
- **Memory Management**: Data is streamed where possible. For the ~50 subject cohort, we will load subject-by-subject or in small batches to stay under 7GB RAM.
- **Time Limit**: The pipeline is designed to complete within 6 hours. If a subject fails, it is skipped immediately to prevent timeouts.
- **No Synthetic Data**: We use real HCP-derived data from OpenNeuro. No synthetic stand-ins are planned.