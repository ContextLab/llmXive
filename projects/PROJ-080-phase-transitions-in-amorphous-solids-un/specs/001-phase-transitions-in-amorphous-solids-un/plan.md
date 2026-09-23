# Implementation Plan: Phase Transitions in Amorphous Solids Under Shear Stress

**Branch**: `001-phase-transitions-amorphous-solids` | **Date**: 2024-05-21 | **Spec**: `specs/001-phase-transitions-in-amorphous-solids/spec.md`
**Input**: Feature specification from `specs/001-phase-transitions-in-amorphous-solids/spec.md`

## Summary

This project implements a computational pipeline to detect structural precursors to macroscopic yielding in amorphous solids under shear stress. The primary technical approach involves ingesting molecular dynamics (MD) trajectory data, computing the non-affine displacement metric ($D^2_{min}$) and local shear strain for every particle, and identifying the yielding onset via stress-drop detection. The system then performs statistical correlation analysis (Permutation Test, as a methodological correction to the spec-mandated KS-test due to clustered data dependencies) between brittle and ductile regimes and validates a predictive threshold model for time-to-failure. The predictive threshold is a heuristic derived from associational data, not a causal mechanism. The implementation strictly adheres to CPU-first constraints (7GB RAM) and ensures full reproducibility via pinned seeds and checksummed data.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `h5py`, `scikit-learn`, `matplotlib`, `datasets` (Hugging Face), `tqdm`
**Storage**: Local filesystem (`data/raw/`, `data/processed/`) in HDF5/Parquet/CSV formats; no external database.
**Testing**: `pytest` (unit tests for $D^2_{min}$ calculation, integration tests for pipeline flow).
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-only, 2 cores, 7GB RAM).
**Project Type**: Scientific computation pipeline / CLI tool.
**Performance Goals**: Process ≤100k particle trajectories within 6 hours; memory footprint <7GB.
**Constraints**: Max [deferred] particles per trajectory (FR-006); no GPU usage for core logic; strict adherence to spec-defined stress drop thresholds.
**Scale/Scope**: Single feature branch processing a batch of pre-downloaded MD trajectories.

**Input Data Contract**:
- **Dataset**: `amorphous-silicon-shear-trajectories` (HuggingFace).
- **Verified URL**: ` (Must be verified in `research.md` before execution).
- **Required Fields**: `positions` (x,y,z), `box_vectors`, `stress_tensor` at every timestep.
- **Fallback**: If no verified URL is found, the pipeline halts with a fatal error.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned random seeds in all clustering and statistical steps (FR-003, FR-005) and requires a `requirements.txt` for isolated execution.
- **II. Verified Accuracy**: All dataset references in `research.md` will be restricted to the verified URLs provided in the spec input block. No fabricated URLs will be used.
- **III. Data Hygiene**: The plan enforces a strict separation between `data/raw/` (immutable) and `data/processed/` (derived metrics), with checksums recorded in the project state.
- **IV. Single Source of Truth**: All statistical outputs (p-values, FPR/FNR) will be generated programmatically and stored in structured artifacts, preventing hand-typed values in reports.
- **V. Versioning**: Content hashes for all input trajectories and output artifacts will be tracked.
- **VI. Simulation Trajectory Integrity**: Raw particle coordinates will be preserved; $D^2_{min}$ and strain calculations will be written to new files, ensuring auditability.
- **VII. Numerical Determinism**: Fixed seeds will be applied to the k-means clustering (for shear band identification) and the yielding detection algorithm to ensure identical results across runs. The `code/utils.py` module defines `SEED = 42` as the sole source of truth; all downstream functions must import this constant.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-transitions-in-amorphous-solids/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── trajectory.schema.yaml
│ ├── precursor_metrics.schema.yaml
│ └── analysis_results.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-080-phase-transitions-in-amorphous-solids-un/
├── data/
│ ├── raw/ # Immutable MD trajectory files (HDF5/XYZ)
│ └── processed/ # Derived CSVs (D2_min, stress curves), JSON reports
├── code/
│ ├── __init__.py
│ ├── utils.py # Global SEED constant, streaming helpers
│ ├── preprocess.py # FR-001, FR-002: D2_min calculation, yield detection
│ ├── analysis.py # FR-003, FR-005: Permutation Test, Bonferroni correction
│ ├── predict.py # FR-004: Threshold validation, sensitivity sweep
│ └── metrics.py # SC-004, SC-005: Runtime and memory instrumentation
├── tests/
│ ├── unit/
│ │ ├── test_preprocess.py
│ │ └── test_analysis.py
│ └── integration/
│ └── test_full_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Selected **Option 1: Single project** structure. The project is a linear scientific pipeline (Ingest -> Compute -> Analyze -> Validate) that does not require a web frontend, mobile app, or microservices. All logic resides in `code/` with data separated into `data/raw/` and `data/processed/` to satisfy Constitution Principle VI.

## Complexity Tracking

No violations identified. The complexity is managed by:
1. **Streaming**: Using `h5py`/`datasets` streaming to handle large trajectories without loading full arrays into RAM.
2. **Aggregation**: Reducing spatial autocorrelation by aggregating to shear bands before statistical testing (FR-003), reducing the N for tests.
3. **Thresholding**: Enforcing the 100k particle limit (FR-006) to guarantee memory safety.
4. **Statistical Validity**: Using Permutation Tests instead of KS-tests to handle non-independence of clustered data.

## Implementation Phases

### Phase 0: Data Verification & Ingestion
- **Task 0.1**: Verify the existence and accessibility of the `amorphous-silicon-shear-trajectories` dataset at the verified URL.
- **Task 0.2**: Download and checksum raw trajectory files to `data/raw/`.
- **Task 0.3**: Validate particle count (≤100k) and data integrity (no missing frames).

### Phase 1: Preprocessing (FR-001, FR-002)
- **Task 1.1**: Compute $D^2_{min}$ for every particle using the Falk-Langer algorithm (CPU-optimized).
- **Task 1.2**: Identify yielding onset by detecting the first significant stress drop (>5%).
- **Task 1.3**: Flag indeterminate trajectories and log warnings.
- **Output**: `data/processed/precursor_metrics.csv`, `data/processed/yield_flags.json`.

### Phase 2: Statistical Analysis (FR-003, Methodological Correction)
- **Task 2.1**: Aggregate $D^2_{min}$ values to shear bands (clusters of high-displacement particles) using k-means (seed=42 from `utils.py`).
- **Task 2.2**: Perform a **Permutation Test** (instead of KS-test) to compare distributions between brittle and ductile groups.
 - *Rationale*: The KS-test assumes independent samples, but shear bands are clustered within trajectories. A Permutation Test accounts for this dependency.
 - *Deviation Note*: This deviates from FR-003 (KS-test) to ensure statistical validity.
- **Task 2.3**: Check sample size (number of trajectories ≥ 30). If < 30, flag "Power Limitation".
- **Output**: `data/processed/permutation_p_value.json`, `data/processed/histograms.png`.

### Phase 3: Predictive Validation (FR-004)
- **Task 3.1**: Define 'time-to-failure' as an independent ground truth (total strain at catastrophic failure, NOT derived from $D^_{min}$).
- **Task 3.2**: Sweep the $D^2_{min}$ threshold and calculate FPR/FNR.
- **Task 3.3**: Generate sensitivity analysis table.
- **Output**: `data/processed/prediction_results.json`, `data/processed/sensitivity_table.csv`.

### Phase 4: Multiple Comparison Correction (FR-005)
- **Task 4.1**: Apply Bonferroni correction to all p-values generated in Phase 2 (across strain rates/temperatures).
- **Task 4.2**: Update results with corrected p-values and family-wise error rate.
- **Output**: `data/processed/corrected_results.json`.

### Phase 5: Performance Validation (SC-004, SC-005)
- **Task 5.1**: Instrument and measure total computational runtime. Compare against 6-hour limit.
- **Task 5.2**: Instrument and measure peak memory footprint. Compare against 7GB limit.
- **Task 5.3**: Generate performance report.
- **Output**: `data/processed/performance_report.json`.

## Risk Assessment

1. **Data Availability**: The biggest risk is the lack of a verified, open MD dataset with per-particle coordinates. If the `amorphous-silicon-shear-trajectories` dataset is not in the verified block, the project cannot run.
2. **Memory**: Processing 100k particles with full neighbor lists can exceed 7GB RAM if not streamed. Mitigation: Use chunked processing and `h5py` streaming.
3. **Numerical Stability**: $D^2_{min}$ calculation can be sensitive to floating-point errors. Mitigation: Use double precision (`float64`) throughout.
4. **Statistical Validity**: Using Permutation Tests instead of KS-tests is a necessary deviation to handle clustered data. This is documented and justified.