# Implementation Plan: Predicting Alloy Phase Diagrams from Compositional Data

**Branch**: `001-predict-alloy-phase-diagrams` | **Date**: 2023-10-27 | **Spec**: `spec.md`

## Summary

This project implements a machine learning pipeline to predict alloy phase transition temperatures (liquidus/solidus) for simple binary systems using only compositional descriptors. The approach involves ingesting experimental phase data, generating elemental descriptors (atomic radius, electronegativity, valence electron concentration), training a Random Forest Regressor with Leave-One-System-Out (LOSO) cross-validation, and validating results against a null baseline and visual fidelity targets. The entire pipeline is constrained to run on a single CPU core with <7 GB RAM.

**Critical Constraint**: The Spec mandates data from NIST-JANAF/SGTE. If these sources are not available in the verified input block, the pipeline halts with `DATA_SOURCE_MISSING` to satisfy Verified Accuracy.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `requests`, `pyyaml`, `statsmodels`  
**Storage**: Local CSV/Parquet files in `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete pipeline < 4 hours; Memory < 7 GB  
**Constraints**: No GPU; No external thermodynamic simulation inputs; LOSO validation strictness.  
**Scale/Scope**: Binary alloy systems only (e.g., Cu-Zn, Al-Cu); a representative subset of systems depending on data availability.

## Constitution Check

*Gates determined based on `projects/PROJ-485/.../constitution.md`*

1.  **Principle I (Reproducibility)**: Plan mandates pinned `random_state` in all ML steps and deterministic data loading order. All scripts in `code/` will be runnable end-to-end.
2.  **Principle II (Verified Accuracy)**: All dataset references are restricted to the verified URLs provided in the input block. **If the Spec-mandated NIST-JANAF/SGTE sources are absent from the verified block, the pipeline halts with `DATA_SOURCE_MISSING`**. No unverified URLs will be cited.
3.  **Principle III (Data Hygiene)**: Plan includes a checksum step for raw data ingestion. Derivations (descriptors) will be written to new files. **Checksums are explicitly recorded in the project state file (`state/...yaml`)** after generation.
4.  **Principle IV (Single Source of Truth)**: The `data-model.md` defines the exact schema for inputs/outputs. The plan ensures all figures and metrics (including TCS) are generated programmatically from these files.
5.  **Principle V (Versioning)**: The plan includes a step to compute content hashes of generated artifacts and update the `state/...yaml` file immediately after generation.
6.  **Principle VI (Computational Resource Envelope)**: The plan explicitly selects CPU-tractable methods (Random Forest, no deep learning) and enforces data subsampling if necessary to fit <7 GB RAM.
7.  **Principle VII (Input Feature Scope)**: The plan strictly limits features to stoichiometry-derived descriptors, forbidding thermodynamic simulation outputs as inputs.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-alloy-phase-diagrams/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Pipeline orchestrator
├── ingest/
│   ├── __init__.py
│   └── load_data.py     # Data loading & validation
├── features/
│   ├── __init__.py
│   └── generate_descriptors.py  # Descriptor calculation
├── models/
│   ├── __init__.py
│   ├── train.py         # LOSO training & power analysis
│   └── evaluate.py      # Metrics & baseline comparison
├── viz/
│   ├── __init__.py
│   └── plot_phase_diagrams.py
├── utils/
│   ├── __init__.py
│   └── logging.py       # Error code logging
└── tests/
    ├── test_ingest.py
    ├── test_features.py
    └── test_model.py

data/
├── raw/                 # Raw downloads (checksummed)
├── processed/           # Feature-engineered data
└── artifacts/           # Checksums & hashes

requirements.txt
```

**Structure Decision**: Single Python package structure (`code/`) chosen for simplicity and ease of testing on CI. The separation of `ingest`, `features`, `models`, and `viz` ensures modularity and adherence to the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| LOSO Cross-Validation | Required by FR-003 to test generalization to unseen systems. | K-fold CV would leak system-level information, failing the "new system" test. |
| Power Analysis (FR-011) | Required to prevent false positives on small datasets. | Skipping this risks publishing results that are statistically underpowered. |
| Error Code Logging (FR-008) | Required for traceability of data quality issues. | Simple logging lacks the structured traceability needed for automated review. |
| Topological Consistency Score (TCS) | Required to validate visual fidelity beyond point-wise MAE. | MAE alone cannot detect phase topology errors (e.g., swapped solidus/liquidus). |

## Methodology & Technical Decisions

### 1. Data Ingestion & Verification
- **Source Check**: The pipeline first checks if the verified input block contains NIST-JANAF or SGTE URLs.
  - **If Missing**: Halt with `DATA_SOURCE_MISSING`. (Satisfies Spec FR-001 and Constitution Principle II).
  - **If Present**: Load data.
- **Schema Validation**: Verify presence of `temperature`, `composition`, `element_a`, `element_b`.
- **Filtering**: Keep only binary systems with valid temperatures. Exclude metastable phases (e.g., Fe-C) if identifiable.

### 2. Descriptor Generation
- **Features**: Mean Atomic Radius, Electronegativity Variance, VEC, Hume-Rothery Concentration.
- **Constants**: Loaded from a versioned `data/raw/elemental_properties.csv`.
- **Validation**: Check derived values against known constants (≤ 1% deviation).

### 3. Model Training & Validation (LOSO)
- **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Validation Strategy**: **Leave-One-System-Out (LOSO)**.
  - **Logic Correction**: In binary alloys, LOSO implies the test set contains elements *not* in the training set.
  - **FR-010 Compliance**: The "New Element" check is redefined as **Property Range Extrapolation**.
    - *Check*: Calculate the convex hull of elemental properties (radius, EN) in the training set.
    - *Action*: If the test set's elements fall *outside* this convex hull (extrapolation), the fold is skipped. If they are *inside* but the system is new, the fold proceeds (interpolation).
- **Power Analysis**:
  - **Metric**: Number of *Systems* (K), not data points.
  - **Effect Size**: Target R² improvement over Null Model (Cohen's f² indicating a small-to-moderate effect size).
  - **Variance**: Estimated from a pilot run of the Null Model.
  - **Action**: If Power < 0.8, halt with `INSUFFICIENT_POWER`.

### 4. Evaluation Metrics
- **Pointwise Accuracy**: Mean Absolute Error (MAE), R².
- **Visual Fidelity**: **Topological Consistency Score (TCS)**.
  - **Algorithm**: For each system, sort predicted temperatures and experimental temperatures at fixed composition slices. TCS = 1.0 if `sorted(predicted) == sorted(experimental)`, else 0.0 (or partial match ratio).
  - **Target**: TCS ≥ 0.8.
- **Baseline Comparison**:
  - **Null Model**: Trained on the *training fold* (predicting mean of training fold).
  - **Significance**: **Permutation Test** on fold-level MAE differences (not paired t-test).
- **Data Density Check (FR-013, SC-009)**:
  - **Step**: Explicitly aggregate prediction errors by `system_id`.
  - **Calculation**: Compute standard deviation of errors per system.
  - **Trigger**: If SD > 50K or N < 5, flag `LOW_DATA_DENSITY`.

### 5. Data Hygiene & Versioning
- **Checksums**: After every raw data load, compute SHA-256.
- **State Update**: Immediately write `artifact_hashes` to `state/PROJ-485/...yaml`.
- **Derivations**: All processed files are new; raw data is immutable.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Data Source Missing** | If NIST/SGTE not in verified block, halt with `DATA_SOURCE_MISSING`. |
| **Property Extrapolation** | Skip folds where test elements are outside training convex hull. |
| **Low Data Density** | Trigger `LOW_DATA_DENSITY` error if SD > 50K. |
| **Insufficient Power** | Halt with `INSUFFICIENT_POWER` if K < required for MDE=0.10. |
| **Memory Overflow** | Stream processing or subsampling; monitor memory usage. |