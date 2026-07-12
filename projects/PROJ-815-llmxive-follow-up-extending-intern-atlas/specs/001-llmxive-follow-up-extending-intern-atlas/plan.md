# Implementation Plan: llmXive follow-up: extending "Intern-Atlas"

**Branch**: `001-methodological-evolution-fragility` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-intern-atlas/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-intern-atlas/spec.md`

## Summary

This feature implements a computational study to determine if topological features of methodological evolution graphs (specifically `bottleneck_resolution_ratio` and `branching_entropy`) predict the long-term reproducibility (proxied by retraction status) of methodological lineages. The approach involves extracting a subgraph from the Intern-Atlas snapshot, computing graph metrics, merging with external retraction databases (Retraction Watch/Replication Index), and training a logistic regression model. The implementation strictly adheres to CPU-only constraints for GitHub Actions free-tier runners.

**Critical Data Constraint & Synthetic Fallback**: The Intern-Atlas graph and Retraction Watch Database MUST be fetched from verified canonical sources. As per the "Verified datasets" block, **no verified URL exists** for these specific resources. Therefore, the pipeline is designed with a **Synthetic Fallback Protocol**:
1. If `data/raw/intern-atlas-snapshot.graphml` and `data/raw/retraction-watch-dump.csv` are present, the pipeline proceeds with **Scientific Analysis**.
2. If missing, the pipeline **automatically generates** a synthetic graph and labels with known properties to validate the code pipeline (Code Validation Mode).
3. **Scientific Discovery** is explicitly marked as "Infeasible" in the absence of real data, ensuring reproducibility (Constitution Principle I) without requiring manual user intervention.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `networkx`, `requests`, `pyyaml`, `seaborn`, `matplotlib`, `Levenshtein`  
**Storage**: Local CSV/Parquet files within `data/` (no external database server)  
**Testing**: `pytest` (unit tests for feature extraction, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Total runtime < 6 hours; Memory usage < 6GB during peak processing.  
**Constraints**: No GPU; no LLM inference for edge typing; strict separation of training features and target labels (Constitution Principle VI); **Strict Abort** for scientific discovery if real data missing (fallback to synthetic for code validation).  
**Scale/Scope**: Subgraph of Intern-Atlas (-2018); A variable number of nodes (sampled if necessary to fit memory).

> **Dataset Note**: The Intern-Atlas graph snapshot is the primary data source. As per the "Verified datasets" block, **no verified URL exists** for this graph. The pipeline requires the file `data/raw/intern-atlas-snapshot.graphml`. If missing, the pipeline **triggers the Synthetic Fallback Protocol** to generate a reproducible synthetic dataset for code validation. Scientific analysis (real data) is aborted. Similarly, the Retraction Watch Database must be present at `data/raw/retraction-watch-dump.csv`. If missing, the pipeline triggers the Synthetic Fallback for labels.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Action Required |
|-----------|-------------------|-----------------|
| **I. Reproducibility** | **Pass** | All scripts pin versions. Random seeds set to 42. **Automatic Synthetic Fallback** ensures reproducibility on fresh runners even if real data is missing. |
| **II. Verified Accuracy** | **Pass** | All citations to retraction databases validated against primary sources. Synthetic data used only for validation. |
| **III. Data Hygiene** | **Pass** | Raw data checksummed. Derivations written to new files. Synthetic data is checksummed and logged. |
| **IV. Single Source of Truth** | **Pass** | All metrics generated from `code/` output. |
| **V. Versioning Discipline** | **Pass** | Content hashes recorded in `state/`. |
| **VI. Graph-Topology Non-Circularity** | **Pass** | Features strictly separated from labels. **Edge Type Validation** and **Circularity Audit** steps added to exclude 'retraction-outcome' types. |
| **VII. Interpretability** | **Pass** | Logistic Regression used. Structural coupling acknowledged and handled via re-run logic. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-intern-atlas/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── model.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── extract_intern_atlas.py      # Includes Edge Type Validation & Fuzzy Matching
│   │   ├── merge_retractions.py         # Includes Levenshtein fallback
│   │   ├── compute_features.py
│   │   └── synthetic_data_generator.py  # New: Generates synthetic graph/labels
│   ├── models/
│   │   ├── train_baseline.py
│   │   ├── train_topological.py
│   │   └── evaluate.py
│   ├── analysis/
│   │   ├── robustness_tests.py          # Includes Stratified Permutation (n=1000)
│   │   └── sensitivity_analysis.py
│   └── utils/
│       ├── graph_utils.py
│       └── constants.py
├── data/
│   ├── raw/
│   │   ├── intern-atlas-snapshot.graphml (Optional - triggers synthetic if missing)
│   │   └── retraction-watch-dump.csv (Optional - triggers synthetic if missing)
│   └── processed/
│       ├── features_2010_2018.csv
│       └── model_results.json
├── tests/
│   ├── unit/
│   │   ├── test_feature_extraction.py
│   │   └── test_graph_utils.py
│   └── integration/
│       └── test_pipeline.py
└── requirements.txt
```

**Structure Decision**: Single project structure with modular `code/` subdirectories for data extraction, modeling, and analysis. This ensures a linear pipeline execution order (Extract -> Merge -> Feature -> Train -> Evaluate) required by the spec.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is limited to graph metrics and logistic regression, which fits within the 7GB RAM/2 CPU constraint. | N/A |

## Phase Plan

### Phase 0: Data Acquisition, Validation & Synthetic Fallback (Research)
- **Goal**: Verify availability of Intern-Atlas graph and Retraction Watch data. **If missing, trigger Synthetic Fallback Protocol.**
- **Steps**:
    1. Check for `data/raw/intern-atlas-snapshot.graphml` and `data/raw/retraction-watch-dump.csv`.
    2. **If Missing**: Trigger `code/data/synthetic_data_generator.py` to create a reproducible synthetic graph and labels (Code Validation Mode). **Scientific Discovery is aborted.**
    3. **If Present**: Proceed with **Circularity Audit**. Inspect edge type metadata. Exclude any edge types semantically linked to retraction (e.g., 'retracted', 'invalidated') to prevent label leakage. **Audit a sample of 'improves'/'replaces' edges to ensure they are not defined by retraction outcomes.**
    4. Validate edge types (human-annotated vs. LLM inferred). **Exclude LLM-inferred edges.**
- **FR Mapping**: FR-001, FR-002, FR-010, FR-011.
- **SC Mapping**: N/A (Pre-analysis).

### Phase 1: Feature Engineering Pipeline
- **Goal**: Compute `bottleneck_resolution_ratio` and `branching_entropy` for 2010-2018 nodes.
- **Steps**:
    1. Load graph (real or synthetic), filter nodes by year.
    2. **Edge Type Validation**: Exclude LLM-inferred and 'retraction-outcome' edges. **Explicitly filter based on metadata flags.**
    3. Compute outgoing edge stats (excluding untyped edges).
    4. Handle edge cases (nodes with no outgoing edges -> 0.0).
    5. **Fuzzy Matching**: Merge with retraction labels. First attempt exact DOI match. **If DOI fails, use Levenshtein ratio >= 0.85 on title/author** in `code/data/merge_retractions.py`.
    6. Save processed dataset.
- **FR Mapping**: FR-002, FR-003, FR-004, FR-010, FR-011.
- **SC Mapping**: N/A (Data prep).

### Phase 2: Model Training & Baseline Comparison
- **Goal**: Train Topological vs. Citation models.
- **Steps**:
    1. **Stratified Time-Based Split**: Train on 2010-2015, Validate on 2016-2018. **Ensure minimum 10 positive cases (retractions) in validation set** via stratification or oversampling (SMOTE) if necessary.
    2. Train Logistic Regression (Topological features).
    3. Train Logistic Regression (Citation features).
    4. Compute AUC-ROC, Precision, Recall.
    5. **Check**: If validation set has < 10 positive cases after stratification, abort or report limitation.
- **FR Mapping**: FR-005, FR-006.
- **SC Mapping**: SC-001.

### Phase 3: Robustness & Sensitivity Analysis
- **Goal**: Validate statistical significance and threshold stability.
- **Steps**:
  1. **Stratified Permutation Test**: Shuffle labels **n=1000** times, stratified by `field_of_study` and `publication_venue` to control for confounding. Check if Observed AUC > Mean(Permuted) + 2*Std(Permuted). **Note**: Stratified permutation tests the null hypothesis conditional on field/venue.
  2. Run Threshold Sweep (variable thresholds).
  3. Calculate VIF and MI for collinearity.
  4. **Structural Coupling Diagnostic**: If BRR and BE are highly correlated (VIF > 5), **re-run model using only 'branching_entropy' or a composite metric** and report as sensitivity analysis.
  5. **Covariate Adjustment**: Run logistic regression with `field_of_study` and `publication_venue` as covariates as a confirmatory step.
- **FR Mapping**: FR-007, FR-008, FR-009, FR-012.
- **SC Mapping**: SC-002, SC-003, SC-004.

### Phase 4: Reporting & Artifact Generation
- **Goal**: Generate final results and update `research.md`.
- **Steps**:
    1. Aggregate metrics.
    2. Generate plots (PR curve, Permutation distribution).
    3. Write final report.
- **FR Mapping**: All.
- **SC Mapping**: All.

## Compute Feasibility Check
- **Memory**: Graph processing with `networkx` on a ~k node graph fits in 7GB RAM.
- **CPU**: Logistic regression and permutation tests (n=1,000) are CPU-tractable.
- **Disk**: CSV/Parquet outputs will be < 1GB.
- **Time**: Estimated runtime is expected to be moderate on 2 CPU cores.

## Risk Mitigation
- **Risk**: Intern-Atlas graph not available in verified list.
  - **Mitigation**: Pipeline triggers **Synthetic Fallback Protocol** for code validation. Scientific analysis aborted.
- **Risk**: Edge types are LLM-inferred (violating FR-002).
  - **Mitigation**: Script checks metadata flags; if "LLM-inferred" is present, those edges are excluded.
- **Risk**: Dataset too large for RAM.
  - **Mitigation**: Implement chunked processing or random sampling (as per Assumption).
- **Risk**: Class imbalance in validation set.
  - **Mitigation**: Use **Stratified Time-Based Split** to ensure positive cases accumulate in later years.
- **Risk**: Structural coupling of BRR and BE.
  - **Mitigation**: **Structural Coupling Diagnostic** in Phase 3; re-run model with single predictor if VIF > 5.