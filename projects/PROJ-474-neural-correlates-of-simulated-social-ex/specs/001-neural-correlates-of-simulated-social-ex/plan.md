# Implementation Plan: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Branch**: `001-neural-correlates-social-exclusion` | **Date**: 2026-07-01 | **Spec**: `specs/001-neural-correlates-social-ex/spec.md`
**Input**: Feature specification from `/specs/001-neural-correlates-social-ex/spec.md`

## Summary

This project implements a computational pipeline to investigate how acute simulated social exclusion (Cyberball task) modulates functional connectivity dynamics within the Default Mode Network (DMN). The system ingests **preprocessed fMRI data (NIfTI format)** from **OpenNeuro ds000030**, performs rigorous motion QC (FR-002) on the raw signal, extracts BOLD time-series from PCC, mPFC, and angular gyrus (FR-003), computes condition-specific connectivity strength metrics (FR-004, FR-005), and executes a non-parametric paired permutation test (FR-006) to determine statistical significance. All findings are framed as associational unless randomization is verified (FR-007). The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners (2 CPU, 7GB RAM) using memory-mapped data processing.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `nibabel`, `nilearn` (CPU-only build, memory-mapping enabled), `scikit-learn`, `pyyaml`, `bids`  
**Storage**: Local filesystem (temporary data in `data/`, derived artifacts in `data/derived/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Neuroscience Pipeline / CLI  
**Performance Goals**: Complete pipeline run within 6 hours; memory usage < 7GB; disk usage < 14GB.  
**Constraints**: No GPU; no large model training; dataset must be sampled or processed in chunks if necessary; strict motion exclusion (>3mm).  
**Scale/Scope**: Single dataset (OpenNeuro ds000030), N subjects (target N≥10 for valid test).

### Memory Management Strategy
To satisfy the 7GB RAM constraint while processing 4D NIfTI data:
- **Memory Mapping**: The pipeline uses `nilearn.image.load_img` with `mmap=True` (or equivalent `nibabel` memory mapping) to stream data from disk rather than loading full 4D volumes into RAM.
- **Chunked Processing**: ROI extraction and correlation calculation are performed subject-by-subject or in small batches. Intermediate time-series (1D arrays) are stored in memory, but raw 4D volumes remain on disk.
- **Garbage Collection**: Explicit `gc.collect()` calls are inserted between subject iterations to reclaim memory.

### Dataset Variable Fit & Failure Logic
- **Source**: OpenNeuro ds000030 (BIDS format, NIfTI + JSON + TSV).
- **Verification**: Upon download, the system checks for the presence of `events.tsv` files containing "Inclusion" and "Exclusion" trial types.
- **Failure Handling**:
  - If `events.tsv` is missing or lacks required conditions: Halt with `ERR_DATA_UNAVAILABLE`.
  - If the number of valid subjects (after QC) is < 10: Halt with `ERR_N_INSUFFICIENT`.
  - The plan does **not** assume the dataset contains pre-extracted time-series; it extracts them dynamically.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seed setting, and fetching from canonical OpenNeuro ds000030. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the "Verified datasets" block; no invented URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming steps for raw data and derivation logging. |
| **IV. Single Source of Truth** | **PASS** | Pipeline architecture ensures all stats flow from `data/` to `results/` without manual entry. |
| **V. Versioning Discipline** | **PASS** | **Phase 5 Step 5** explicitly generates SHA-256 hashes of outputs and updates the project state YAML. |
| **VI. fMRI Motion Artifact Exclusion** | **PASS** | Explicit implementation of >3mm threshold (FR-002) and exclusion logic (FR-010). |
| **VII. State-Dependent Connectivity** | **PASS** | Metric definition (Mean Absolute Correlation) strictly follows FR-005 and SC-002. |

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-correlates-social-ex/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py            # Paths, seeds, constants (DEFAULT 3mm threshold, DMN ROIs)
├── data_ingestion.py    # OpenNeuro download, checksum, integrity check (FR-001)
├── motion_qc.py         # Displacement calculation, subject exclusion (FR-002)
├── roi_extraction.py    # BOLD time-series extraction from AAL/Harvard-Oxford (FR-003)
├── connectivity.py      # Segmentation, correlation matrices, strength metrics (FR-004, FR-005)
├── stats.py             # Permutation test, FDR correction, effect size (FR-006, FR-008, FR-011)
├── viz.py               # Visualization (null distribution, CI bars, sensitivity curve) (FR-006)
└── main.py              # Orchestration script
```

**Structure Decision**: Single project structure selected to minimize overhead. `src/` contains all logic; `tests/` mirrors structure. This aligns with the "computational pipeline" nature and simplifies dependency management for the CI runner.

## Implementation Phases

### Phase 1: Data Ingestion & QC (FR-001, FR-002, FR-009, FR-010)
1. **Download**: Fetch ds000030 from OpenNeuro. Verify checksums.
2. **QC**: Calculate motion displacement for each subject. Exclude >3mm.
3. **Validate**: Ensure `events.tsv` contains "Inclusion" and "Exclusion".
4. **Check Count**: If valid subjects < 10, halt with `ERR_N_INSUFFICIENT`.

### Phase 2: Feature Extraction (FR-003, FR-004, FR-005)
1. **Extract**: Load 4D NIfTI (memory-mapped). Extract time-series for PCC, mPFC, Angular.
2. **Segment**: Split time-series into "Inclusion" and "Exclusion" segments based on `events.tsv`.
3. **Compute**: Calculate Pearson correlation matrices for each condition.
4. **Aggregate**: Compute Mean Absolute Correlation (MAC) for each condition per subject.

### Phase 3: Statistical Analysis (FR-006, FR-008, FR-011)
1. **Global Test**: Paired permutation test on MAC values (Inclusion vs Exclusion).
2. **Edge-wise Test**: Paired permutation test for each of the 3 edges (PCC-mPFC, etc.).
3. **Correction**: Apply FDR (q ≤ 0.05) to edge-wise p-values.
4. **Framing**: Set `is_associational` flag based on metadata `randomization_verified`.

### Phase 4: Sensitivity & Visualization (SC-005)
1. **Sensitivity Curve**: Re-calculate MAC and p-values for the *fixed set of retained subjects* using alternative motion thresholds (mm, 4mm) for reporting purposes only. **Note**: This does not re-include subjects excluded by the 3mm rule.
2. **Visualize**: Generate null distribution, CI bar plots, and sensitivity curve.

### Phase 5: Reporting & Versioning (Constitution Principle V)
1. **Compile**: Generate `results.json` and markdown report.
2. **Hash**: Compute cryptographic hashes for all output artifacts..
3. **Update State**: Write hashes and `updated_at` timestamp to `state/projects/PROJ-474-neural-correlates-of-simulated-social-ex.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. The scope is strictly bounded by the spec and compute constraints. | N/A |