# Implementation Plan: Multi-Property Trade-Offs in Alloy Design

**Branch**: `786-multi-property-trade-offs-in-alloy-desig` | **Date**: 2026-07-08 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/786-multi-property-trade-offs-in-alloy-desig/spec.md`

## Summary

This project identifies alloy compositions optimizing the trade-off between Bulk Modulus (K) and Shear Modulus (G) using high-throughput DFT data from OQMD. The approach involves ingesting compositional data, encoding it via isometric log-ratio (ilr) transforms with periodic descriptors, training Gradient Boosting surrogates under strict Leave-One-System-Out (LOSO-CV) constraints, and generating a Pareto frontier via NSGA-II. A critical physics check (FR-000) determines whether to analyze "decoupling" via correlation deviation or Poisson's ratio anomalies. The methodology has been revised to use density-based clustering on residuals to ensure clusters represent physical decoupling phenomena, and statistical validation now employs local permutation tests and bootstrap resampling.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `datasets` (HuggingFace), `scikit-learn`, `hdbscan`, `xgboost` (CPU), `pymoo` (NSGA-II), `pandas`, `numpy`, `scipy`, `pyyaml`
**Storage**: Local filesystem (`data/processed/`, `data/raw/`); CSV and JSON artifacts.
**Testing**: `pytest` (unit, integration, contract tests).
**Target Platform**: Linux (GitHub Actions CPU runner: 2 cores, ~7GB RAM).
**Project Type**: Computational research pipeline / CLI.
**Performance Goals**: Complete full pipeline (ingestion -> modeling -> optimization -> analysis) within 6 hours. R² > 0.6 on LOSO-CV.
**Constraints**:
- CPU-only execution (no GPU for model training; NSGA-II must be efficient).
- Strict data locality: All data must be streamed or sampled to fit within available RAM.
- No extrapolation beyond convex hull of training data.
- Reproducibility: Fixed random seeds for all stochastic processes.
**Scale/Scope**: A substantial number of valid alloy entries from OQMD.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | All scripts in `code/` use fixed seeds to ensure reproducibility. Data fetched via canonical HF URLs. |
| **II. Verified Accuracy** | ✅ PASS | Citations in `research.md` limited to verified OQMD URLs. No fabricated sources. |
| **III. Data Hygiene** | ✅ PASS | Raw data saved to `data/raw/` with checksums. `data/processed/` contains derived artifacts (CSV/JSON) only. |
| **IV. Single Source of Truth** | ✅ PASS | All metrics (R², hull radius, robustness_score) derived strictly from `code/` output files. |
| **V. Versioning Discipline** | ✅ PASS | `requirements.txt` pins versions. Artifacts tracked in `state/` via content hash. |
| **VI. Computational Surrogate Validity** | ✅ PASS | Model validation includes LOSO-CV variance (`uncertainty_variance`) to flag unreliable regions. |
| **VII. Convex Hull Constraint on Exploration** | ✅ PASS | NSGA-II search space is strictly bounded by the convex hull of training data in ilr-space, with projection to simplex for physical validity. |

## Project Structure

### Documentation (this feature)

```text
specs/786-multi-property-trade-offs-in-alloy-desig/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── alloy_entry.schema.yaml
    ├── dataset.schema.yaml
    ├── decoupled_region.schema.yaml
    ├── decoupling_validation.schema.yaml
    ├── encoded_schema.schema.yaml
    ├── ingest_schema.schema.yaml
    ├── ingested_alloy.schema.yaml
    ├── model_output.schema.yaml
    ├── model_validation.schema.yaml
    ├── pareto_frontier.schema.yaml
    ├── sensitivity_analysis.schema.yaml
    ├── sensitivity_schema.schema.yaml
    └── validation_report.schema.yaml
```

### Source Code (repository root)

```text
code/
├── ingestion/
│   ├── __init__.py
│   ├── load_oqmd.py       # Downloads and filters OQMD data (with schema verification)
│   └── encode_composition.py # ILR transform + periodic descriptors
├── modeling/
│   ├── __init__.py
│   ├── loso_cv.py         # LOSO-CV logic with System definition (unique element sets)
│   ├── train_surrogates.py # XGBoost training for K and G
│   └── pareto_optimize.py  # NSGA-II generation within convex hull (with projection)
├── analysis/
│   ├── __init__.py
│   ├── feasibility_check.py # FR-000: Correlation/Poisson check
│   ├── clustering.py        # HDBSCAN on residuals + Decoupling logic
│   └── sensitivity.py       # FR-006: Threshold sweep + Jaccard + Bootstrap
├── utils/
│   ├── __init__.py
│   ├── constants.py         # Periodic table data, physics constants
│   └── io_utils.py          # Checksum, JSON/CSV writers
├── main.py                  # Orchestration script
└── requirements.txt

tests/
├── unit/
│   ├── test_encoding.py
│   └── test_physics.py
├── integration/
│   └── test_ingestion_pipeline.py # Verifies encoded_alloys.csv creation
└── contract/
    └── test_contracts.py    # Validates output against YAML schemas

data/
├── raw/
│   └── oqmd_targets.csv.gz  # (Downloaded, checksummed)
└── processed/
    ├── encoded_alloys.csv
    ├── feasibility_report.json
    ├── model_validation_report.json
    ├── cluster_analysis.json
    ├── sensitivity_analysis.csv
    └── pareto_frontier.csv
```

**Structure Decision**: Single monolithic `code/` directory with modular sub-packages (`ingestion`, `modeling`, `analysis`) to facilitate isolated testing and clear data flow. This structure supports the CPU-first constraint by keeping dependencies localized and avoiding complex build systems.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **LOSO-CV over K-Fold** | Essential to prevent elemental leakage. Standard K-Fold would allow the same elements in train/test, inflating R² artificially. | K-Fold is simpler but violates the "System" definition required for true out-of-distribution generalization in materials science. |
| **ILR Transform** | Required for compositional data (sum-to-one constraint). Euclidean distance on raw fractions is mathematically invalid. | Standard scaling/normalization ignores the simplex geometry of composition data, leading to spurious correlations. |
| **NSGA-II within Convex Hull** | Ensures physical feasibility. Extrapolation to unknown regions is unreliable without DFT validation. | Global search (unconstrained) would generate non-physical alloys outside the data distribution, violating Constitution Principle VII. |
| **HDBSCAN on Residuals** | Ensures clusters are formed based on the 'decoupling' phenomenon (deviation from the trend) rather than arbitrary Euclidean distance in feature space. | K-Means on features partitions space based on geometry, not property correlation, risking false positives. |

## Phase Implementation Details

### Phase 0: Data Ingestion & Feasibility (FR-000, FR-001, FR-001.1)
- **Action**: Download OQMD elastic data via verified URL.
- **Validation**: Verify schema contains `bulk_modulus` and `shear_modulus` columns.
- **Filtering**: Keep only entries with positive, non-null moduli.
- **Check**: If valid entries < 500, **exit with error code 1** and log "Insufficient data for research validity; minimum 500 entries required."
- **Feasibility**: Calculate global Pearson correlation $r$.
  - If $r < 0.95$: Set `analysis_mode` = "standard".
  - If $r \ge 0.95$: Set `analysis_mode` = "poisson_anomaly".
- **Output**: `data/processed/feasibility_report.json` (fields: `global_correlation`, `analysis_mode`).

### Phase 1: Encoding & Modeling (FR-002, FR-003, FR-004)
- **Encoding**: Apply ilr transform to elemental fractions. Append weighted periodic descriptors.
- **System Definition**: A "System" is defined as the **unique set of constituent elements** (e.g., {Fe, Ni} vs {Fe, Ni, Cr}).
- **Modeling**: Train XGBoost for K and G using LOSO-CV based on System definition.
- **Uncertainty**: Store per-split predictions to calculate `uncertainty_variance` for each point.
- **Optimization**: NSGA-II in ilr-space.
  - **Constraint**: Map candidates back to simplex; reject or project if invalid (negative fractions, sum != 1).
  - **Validation**: Compare frontier against Voigt-Reuss-Hill bounds.

### Phase 2: Decoupling & Sensitivity (FR-005, FR-006)
- **Clustering**: Apply HDBSCAN on **residuals** from the global K-G correlation (or Poisson line).
- **Decoupling**: Identify clusters with high residual density.
- **Permutation Test**: For identified clusters, shuffle **composition assignments within the cluster** (local permutation) to generate null distribution for correlation. Verify p < 0.05.
- **Sensitivity**: Sweep threshold [lower bound, upper bound] (step size). Calculate Jaccard Index and **bootstrap confidence intervals** for correlation stability.
- **Output**: `data/processed/cluster_analysis.json`, `data/processed/sensitivity_analysis.csv`.

## Traceability Matrix

| Requirement | Plan Element | Status |
| :--- | :--- | :--- |
| **FR-000** | Phase 0 Feasibility Check (Case A/B logic) | Addressed |
| **FR-001** | Phase 0 Data Ingestion | Addressed |
| **FR-001.1** | Phase 0 Exit Condition (error code 1) | Addressed |
| **FR-002** | Phase 1 Encoding (ilr + descriptors) | Addressed |
| **FR-003** | Phase 1 Modeling (LOSO-CV, unique element sets) | Addressed |
| **FR-004** | Phase 1 Optimization (NSGA-II + projection + uncertainty) | Addressed |
| **FR-005** | Phase 2 Clustering (HDBSCAN on residuals) | Addressed |
| **FR-006** | Phase 2 Sensitivity (Sweep [0.1, 0.9], Jaccard, Bootstrap) | Addressed |
| **SC-001** | Phase 1 Validation (R² > 0.6) | Addressed |
| **SC-002** | Phase 2 Permutation Test (Local shuffle) | Addressed |
| **SC-003** | Phase 1 Optimization (Coverage + Bounds) | Addressed |