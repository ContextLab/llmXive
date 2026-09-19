# Implementation Plan: Statistical Evaluation of Dimensionality Reduction Techniques

**Project ID**: PROJ-168-statistical-evaluation-of-dimensionality
**Status**: Active
**Last Updated**: 2024-05-24
**Primary Author**: Research Team

## Executive Summary

This project implements a rigorous statistical evaluation pipeline for dimensionality reduction techniques (PCA, t-SNE, UMAP) applied to single-cell RNA sequencing (scRNA-seq) data. The pipeline automates data acquisition from GEO, quality control, preprocessing, embedding generation, geometric diagnostics, clustering, and statistical modeling to determine which dimensionality reduction method best preserves biological structure.

## Objectives

1. **Automate Data Acquisition**: Download and validate raw count matrices for specific GEO accessions (GSE131907, GSE111322, GSE150728).
2. **Standardize Preprocessing**: Implement deterministic QC, HVG selection, and cell sampling.
3. **Generate Embeddings**: Compute PCA, t-SNE, and UMAP embeddings with reproducible parameters.
4. **Assess Geometry**: Quantify global linearity and local continuity preservation.
5. **Evaluate Fidelity**: Cluster embeddings and compare against ground-truth labels using ARI/NMI.
6. **Statistical Modeling**: Apply Mixed-Effects Models (primary) or Fixed-Effects ANOVA (fallback) to compare methods.
7. **Sensitivity Analysis**: Sweep Leiden resolutions to assess clustering stability.

## Architecture Overview

```
projects/001-statistical-evaluation-of-dimensionality/
├── code/
│ ├── config.py # Global configuration, paths, seeds
│ ├── download.py # GEO data fetching and validation
│ ├── preprocess.py # QC, HVG, sampling
│ ├── embeddings.py # PCA, t-SNE, UMAP generation
│ ├── geometry.py # Trustworthiness, LCA metrics
│ ├── clustering.py # Leiden clustering, ARI/NMI
│ ├── stats.py # ANOVA, Mixed-Effects, Sensitivity
│ ├── utils.py # Resource monitoring, time wrappers
│ ├── validators.py # Real-data enforcement
│ ├── data_gap_resolver.py# Data availability check
│ └── main.py # Snakemake orchestration
├── data/
│ ├── raw/ # Downloaded GEO count matrices
│ └── processed/ # Preprocessed matrices, embeddings
├── results/
│ ├── monitoring.csv # Resource usage logs
│ ├── summary.json # Pipeline summary
│ └──... # Statistical reports, plots
├── tests/ # Unit and integration tests
├── Snakefile # Workflow definition
├── environment.yml # Conda dependencies
└── plan.md # This document
```

## User Stories

### US1: Data Acquisition and Preprocessing (Priority: P1)
**Goal**: Automatically download three specific public scRNA-seq datasets, apply QC, and retain top HVGs.
**Acceptance Criteria**:
- Pipeline fetches raw counts for GSE131907, GSE111322, GSE150728.
- If no data found, pipeline aborts with exit code 1.
- If 1 dataset found, pipeline switches to "Case-Study Mode" (Fixed-Effects only).
- If >1 dataset found, pipeline proceeds with Mixed-Effects (if N>3) or Fixed-Effects (if N<=3).
- Output: Preprocessed matrices in `data/processed/`.

### US2: Geometric Diagnostics and Embedding Generation (Priority: P2)
**Goal**: Compute global linearity and local density metrics, and generate PCA, t-SNE, and UMAP embeddings.
**Acceptance Criteria**:
- Embeddings generated with deterministic seeds.
- Trustworthiness and LCA computed on raw high-dimensional space (pre-log-CPM).
- Resource monitoring logs written to `results/monitoring.csv`.
- Output: Embedding matrices and geometry metrics.

### US3: Fidelity Assessment and Statistical Modeling (Priority: P3)
**Goal**: Cluster embeddings, calculate ARI/NMI, and fit the statistical model.
**Acceptance Criteria**:
- Leiden clustering with resolution optimization (maximize Silhouette).
- ARI/NMI calculated against ground-truth labels.
- **Primary Model**: Mixed-Effects Model (`fidelity ~ method + (1|dataset)`).
- **Fallback**: Fixed-Effects ANOVA if N=1 (Case-Study) or N<=3.
- **Sensitivity Analysis**: Sweep Leiden resolutions {0.1,..., 1.0} and report variance.
- Benjamini-Hochberg correction applied to all p-values.
- Abort if VIF >= 5 (multicollinearity).
- Output: `results/statistical_report.json`, `results/sensitivity_analysis.csv`.

### US4: CI Resource Constraint Compliance (Priority: P4)
**Goal**: Ensure pipeline completes within GitHub Actions free-tier limits.
**Acceptance Criteria**:
- Runtime < 6 hours, Peak RAM < 7GB.
- Automated monitoring and abort if thresholds exceeded.
- GitHub Actions workflow defined.

## Statistical Modeling Strategy (Revised)

To resolve the "Plan Inconsistency" noted in previous iterations:

1. **Primary Model**: **Linear Mixed-Effects Model (LMM)**.
 - Formula: `fidelity_metric ~ method + (1 | dataset)`
 - Used when N > 3 datasets are available.
 - Accounts for dataset-specific variance.
 - Implementation: `statsmodels` `MixedLM`.

2. **Fallback Model**: **Fixed-Effects ANOVA** (or Kruskal-Wallis).
 - Formula: `fidelity_metric ~ method`
 - Used when N <= 3 datasets (including Case-Study mode where N=1).
 - If N=1, results are descriptive only (Case-Study Mode).
 - Implementation: `statsmodels` `ols` + `anova_lm`.

3. **Sensitivity Analysis**:
 - **Requirement**: Sweep Leiden resolutions across {0.1, 0.2,..., 1.0}.
 - **Metric**: Variance in ARI/NMI across resolutions.
 - **Implementation**: Script `code/stats.py` function `run_sensitivity_analysis()`.
 - **Output**: `results/sensitivity_analysis.csv` and plot.
 - **Note**: This supersedes the previous "Silhouette Threshold Sweep" (FR-007) to focus on clustering stability rather than arbitrary thresholds.

4. **Multicollinearity Check**:
 - Calculate VIF for predictors.
 - **Abort** if VIF >= 5.

## Data Management

### Sources
- **Primary**: GEO (Gene Expression Omnibus) via `requests` (no R/GEOquery).
- **Accessions**: GSE131907, GSE111322, GSE150728.
- **Constraint**: **Real Data Only**. No synthetic data generation. If data is missing, pipeline aborts or switches to Case-Study mode.

### Validation
- Checksums validated against GEO metadata.
- Ground-truth labels validated for integrity.
- `code/validators.py` enforces "Real Data Only" constraint.

### Handling Missing Data
- **0 datasets**: Abort (Exit Code 1), log "No Data".
- **1 dataset**: Case-Study Mode (Fixed-Effects, descriptive only).
- **2-3 datasets**: Fixed-Effects ANOVA.
- **>3 datasets**: Mixed-Effects Model.

## Resource Constraints

- **RAM Limit**: 7 GB (Abort if exceeded).
- **Runtime Limit**: 6 hours (Target).
- **CPU**: CPU-only (no GPU dependencies).
- **Monitoring**: `code/utils.py` wraps scripts with `/usr/bin/time -v` and logs to `results/monitoring.csv`.

## Implementation Phases

### Phase 0: Data Gap Resolution (Critical Blocker)
- Verify raw count availability.
- Implement fallback logic (Case-Study vs. Full).
- **Tasks**: T039, T040, T041, T044.

### Phase 1: Setup
- Project structure, environment, config.
- **Tasks**: T001, T002, T004, T003.

### Phase 2: Foundational
- Core infrastructure (download, preprocess, embeddings, geometry).
- **Tasks**: T005, T006, T008a, T008b, T007, T010, T011, T020, T029.

### Phase 3: User Story 1 (Data Acquisition)
- Snakemake rules for download and preprocess.
- **Tasks**: T012, T013, T014, T015, T016.

### Phase 4: User Story 2 (Geometry & Embeddings)
- Snakemake rules for embeddings and geometry.
- **Tasks**: T017, T018, T019, T021.

### Phase 5: User Story 3 (Statistics & Fidelity)
- Clustering, fidelity, statistical modeling, sensitivity analysis.
- **Tasks**: T022, T023, T023.5, T024, T026, T027.5, T028, T044.

### Phase 6: User Story 4 (CI Compliance)
- Resource monitoring, GitHub Actions.
- **Tasks**: T028, T030, T031, T032.

### Phase 7: Revision (Consistency & Sensitivity)
- **T049**: Update plan to reflect Mixed-Effects adoption and Silhouette/Resolution sweep.
- **T050-T054**: Data gap resolution refinements.

## Risk Mitigation

- **Data Unavailability**: Phase 0 handles this explicitly.
- **Resource Exhaustion**: T029 and T021 enforce hard limits.
- **Model Convergence**: `stats.py` includes error handling and simplified model fallbacks.
- **Fabrication**: `validators.py` and strict "Real Data Only" policy.

## Success Metrics

1. Pipeline runs end-to-end on at least one real dataset.
2. Statistical model converges and produces valid p-values.
3. Sensitivity analysis demonstrates clustering stability.
4. Resource usage stays within 7GB RAM and 6h runtime.
5. All unit and integration tests pass.

## Future Work

- Extend to additional GEO accessions.
- Explore non-linear mixed-effects models.
- Integrate interactive visualization (Plotly/Dash).
- Publish results to preprint server.