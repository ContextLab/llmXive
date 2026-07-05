# Implementation Plan: Predicting the Glass Forming Region of Metallic Glass Alloys via Machine Learning

**Branch**: `001-glass-forming-region` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-glass-forming-region/spec.md`

## Summary
This feature implements a computational pipeline to predict the Glass Forming Ability (GFA) of metallic alloys using machine learning. The system ingests composition data, computes thermodynamic descriptors (ΔHmix, δ, VEC, Δχ), trains Random Forest and Gradient Boosting classifiers, and performs rigorous cross-system validation and methodological diagnostics. The implementation adheres to strict CPU-only constraints (≤7 GB RAM) and ensures all findings are framed as associational.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pyyaml`, `requests`
**Storage**: Local CSV/Parquet files in `data/` (raw and processed), JSON reports in `results/`
**Testing**: `pytest` with `pytest-cov`
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: computational research pipeline
**Performance Goals**: Process ≤7 GB RAM, ≤6h runtime, no GPU
**Constraints**: CPU-only execution, chunked processing for large datasets, strict reproducibility via pinned seeds
**Scale/Scope**: Medium-scale alloy dataset (hundreds to thousands of samples)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Reference in Plan |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; data fetched from canonical sources; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | BLOCKED (Pending Verified Source) | No verified dataset URL currently available. Placeholder data is for development only. Final results require verified source. |
| **III. Data Hygiene** | PASS | Raw data preserved; checksums recorded; transformations produce new files; PII scan enforced. |
| **IV. Single Source of Truth** | PASS | All figures/stats in paper trace to `data/` rows and `code/` blocks; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in state YAML; artifact changes update `updated_at` timestamps. |
| **VI. Thermodynamic Descriptor Integrity** (Project Extension) | PASS | Descriptors computed from standardized elemental tables; source recorded in metadata. |
| **VII. Cross‑System Generalization Validation** (Project Extension) | BLOCKED (Pending Sufficient Data) | Requires N>=150 total and N>=20 per family. If not met, marked 'Not Applicable'. |

## Project Structure

### Documentation (this feature)

```text
specs/001-glass-forming-region/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── dataset.schema.yaml
│ └── output.schema.yaml
└── tasks.md # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-396-predicting-the-glass-forming-region-of-m/
├── data/
│ ├── raw/ # Raw downloads (checksummed)
│ ├── processed/ # Descriptor-computed datasets
│ └── metadata/ # Descriptor source logs
├── code/
│ ├── __init__.py
│ ├── data_ingestion.py # FR-001, FR-002, FR-009
│ ├── descriptor_computation.py # FR-001, VI
│ ├── model_training.py # FR-003, FR-004, FR-005
│ ├── validation.py # FR-006, FR-007, FR-008
│ └── utils.py # Logging, chunking helpers
├── results/
│ ├── models/ # Pickled model artifacts
│ ├── reports/ # JSON/CSV performance reports
│ └── validation/ # VIF, sensitivity analysis outputs
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure with clear separation of `data/`, `code/`, `results/`, and `tests/` directories to support reproducibility and hygiene.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Constitution Check passed all principles (with BLOCKED status for missing data). | N/A |

## Implementation Phases

### Phase 0: Data Ingestion & Validation (FR-001, FR-002, FR-009)

1. **Source Verification**:
 - Attempt to load from Zenodo GFA-DB () and Materials Project API.
 - If no verified URL is available, the pipeline **halts with ERROR: DATA_SOURCE_MISSING** and generates a **Synthetic Fallback** dataset (Inoue's rules) for code testing only.
 - **Action**: Log source status. If synthetic, flag all subsequent results as `SYNTHETIC`.

2. **Chunked Processing**:
 - Implement `read_csv(..., chunksize=1000)`.
 - **Memory Estimation**: Process first 1000 samples to estimate RAM usage. If >7 GB projected, reduce `chunksize` dynamically.
 - **Fallback**: If total N is unknown, process in batches of a fixed size until EOF.

3. **Schema Validation**:
 - Verify presence of `composition` and `gfa_label` (or `critical_cooling_rate`).
 - **Fallback**: If binary label missing but `critical_cooling_rate` exists, apply threshold `Rc < 100 K/s`.
 - **Fallback**: If neither exists, generate Synthetic Fallback.

### Phase 1: Descriptor Computation (FR-001, VI)

1. **Thermodynamic Descriptors**:
 - Compute ΔHmix, δ, VEC, Δχ using standardized elemental property tables.
 - **Validation**: Log any missing elemental data; exclude sample and log.

2. **Collinearity Check**:
 - Compute Variance Inflation Factor (VIF) for all predictors.
 - **Fallback**: If VIF > 10, apply PCA to reduce dimensionality before training. Log this action.

### Phase 2: Model Training & Validation (FR-003, FR-004, FR-005)

1. **Split Strategy**:
 - **Primary**: Cross-system split (train on Fe-based, test on Zr-based).
 - **Grouping Logic**: Assign family based on the element with the highest atomic fraction (Fe, Zr, Mg, Cu, Ti).
 - **Validation**: Ensure N >= 20 per family. If not, fall back to **Stratified Random Split** (80/20) and report limitation.

2. **Training**:
 - Train Random Forest and Gradient Boosting with stratified cross-validation..
 - **Power Analysis**: If total N < 150, report results as 'Exploratory' (underpowered).

3. **Permutation Test**:
 - Run multiple permutations of labels. to ensure model performance is not due to chance or family identity alone.
 - **Requirement**: Model AUC must be significantly better than permuted baseline (p < 0.05).

### Phase 3: Methodological Validation (FR-006, FR-007, FR-008)

1. **Threshold Sensitivity**:
 - Sweep classification cutoffs including a range of values below 0.5.
 - **Fallback**: If data is synthetic, flag results as 'Synthetic Baseline'.

2. **Provenance Verification**:
 - Check source URL and checksums.
 - **Framing**: If source is synthetic or unverified, append 'Data Provenance: Synthetic/Unverified - Findings are associational but limited to the specific dataset distribution.' to the report.

3. **Reporting**:
 - Generate JSON/CSV reports with explicit associational language.
 - **Success Criteria**: Empirical measurement of transferability (not a hard AUC >= 0.70 gate).

## Success Criteria

- **SC-001**: Classification accuracy measured against held-out test set.
- **SC-002**: Cross-system transferability measured via AUC on external family; if no external family exists, report 'Not Applicable' and fallback to random split metrics.
- **SC-003**: Threshold sensitivity measured by FPR variation across a range of thresholds.
- **SC-004**: Computational feasibility measured by peak RAM usage ≤7 GB.
- **SC-005**: Predictor collinearity measured by max VIF; if VIF > 5, flag and apply PCA if VIF > 10.