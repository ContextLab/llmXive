# Implementation Plan: Decoding Internal States from Longitudinal Calcium Imaging Data

**Branch**: `001-decoding-internal-states` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-decoding-internal-states/spec.md`

## Summary
This feature implements a CPU-tractable pipeline to decode latent neural states from longitudinal calcium imaging data. The approach involves downloading a specific subset of the Allen Brain Atlas Visual Coding dataset, preprocessing fluorescence traces (dF/F normalization, detrending, deconvolution), and applying Non-negative Matrix Factorization (NMF) with temporal regularization enforced via a custom solver. The extracted latent component weights are then aligned with behavioral metadata and validated via Spearman correlation with a 1000-iteration permutation test on a held-out dataset. The entire pipeline is constrained to run within 5GB RAM and 6 hours on a free-tier GitHub Actions runner.

**Critical Data Note**: This plan is contingent on the availability of the Allen Brain Atlas dataset. If the specific subset containing both fluorescence traces and behavioral metadata is not accessible via the verified sources, the project **MUST HALT** as no valid fallback exists.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `scipy`, `requests`, `tqdm`, `nwb` (for raw data extraction if needed)  
**Storage**: Local `data/` directory (raw and processed Parquet/CSV/NPZ files)  
**Testing**: `pytest` (unit tests for preprocessing, integration tests for pipeline flow, contract tests against schema)  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7GB RAM)  
**Project Type**: Data analysis pipeline / Research tool  
**Performance Goals**: Memory ≤ 5GB, Runtime ≤ 6h, NMF convergence within 1000 iterations  
**Constraints**: No GPU/CUDA, no deep learning training, strict temporal integrity, no modification of raw data in-place.  
**Scale/Scope**: Single session subset of imaging data (thousands of ROIs, thousands of time points).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External data fetched via canonical URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Dataset URLs validated against the "Verified datasets" block in the spec. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed upon download. All transformations produce new files (e.g., `data/processed/dF_norm.npz`). |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in paper trace to specific files in `data/` and code blocks in `code/`. |
| **V. Versioning Discipline** | **PASS** | Content hashes recorded in state YAML. Artifacts updated on change. |
| **VI. Longitudinal Temporal Integrity** | **PASS** | Preprocessing (detrending) applied time-consistently. Permutation tests strictly shuffle indices for the null hypothesis only, preserving raw temporal structure. |
| **VII. Computational Efficiency** | **PASS** | Pipeline enforces 5GB limit via chunked loading and session subsetting. NMF optimized for CPU. |

## Project Structure

### Documentation (this feature)

```text
specs/001-decoding-internal-states/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── correlation_results.schema.yaml
│   └── alignment_results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download.py          # Downloads raw data from Allen Brain Atlas
│   ├── preprocess.py        # dF/F, detrend, deconvolve (OASIS)
│   ├── loader.py            # Chunked loader for memory safety
│   └── split.py             # Time-based train/test splitter (FR-008)
├── analysis/
│   ├── nmf_engine.py        # Custom NMF with temporal penalty
│   ├── alignment.py         # Time-series alignment & error calculation
│   ├── stats.py             # Spearman correlation + permutation test
│   └── null_model.py        # Time-shuffled null model generator (FR-009)
├── utils/
│   ├── logger.py
│   └── memory_monitor.py    # Enforces 5GB limit
├── tests/
│   ├── test_preprocess.py
│   ├── test_nmf.py
│   ├── test_stats.py
│   └── test_split.py
├── main.py                  # Orchestration script
└── requirements.txt
```

**Structure Decision**: Single project structure chosen to minimize overhead. Modular separation of `data`, `analysis`, and `utils` ensures testability and adherence to the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Custom NMF Solver** | Required by FR-010 to enforce temporal smoothness *during* factorization. Post-hoc smoothing is scientifically invalid for this claim. | Standard `sklearn.NMF` lacks temporal constraints. Using it would violate the scientific premise of "biologically plausible dynamics". |
| **Deconvolution (OASIS)** | Required by FR-011 to estimate spike rates before NMF. | Skipping deconvolution would violate the spec's requirement to reflect neural dynamics rather than indicator kinetics. |
| **Permutation Test (1000 iters)** | Required by FR-005 for statistical rigor. | Using analytical p-values would violate the non-parametric nature of Spearman correlation and the spec's explicit requirement. |
| **Time-Based Split** | Required by FR-008 to prevent circular validation. | Random splitting would violate temporal integrity; using the full dataset for validation would be tautological. |

## Phase Plan

### Phase 0: Research & Dataset Validation (Research Complete)
*Goal: Confirm dataset availability and variable fit.*
1.  **FR-001 / SC-001**: Verify the Allen Brain Atlas Visual Coding subset contains the required ROI fluorescence traces and behavioral metadata (running speed, stimulus).
    *   *Action*: Inspect the verified dataset URLs.
    *   *Constraint*: **Blocking Gap**: If the specific Allen subset is missing from the "Verified datasets" block, the plan **MUST HALT**. No fallback to datasets lacking behavioral metadata (e.g., `Chaymaa/roi_donut`) is permitted.
2.  **FR-002**: Validate preprocessing algorithms (dF/F, detrending, interpolation) against the "Missing Data" edge case.
3.  **FR-003 / FR-010**: Evaluate CPU-tractable NMF implementations (custom solver with temporal penalty) to ensure they fit within 6h runtime.

### Phase 1: Data Model & Contracts (Design Complete)
*Goal: Define schemas and data flow.*
1.  **FR-002 / FR-004**: Define `FluorescenceTrace`, `LatentComponent`, `ComponentWeight`, `BehavioralMetric`, and `AlignmentResult` schemas in `contracts/`.
2.  **FR-005**: Define `CorrelationResult` schema including p-values, corrected p-values, and significance flags.
3.  **FR-007**: Document memory constraints in `data-model.md`.

### Phase 2: Implementation (Implementation Complete)
*Goal: Build the pipeline.*
1.  **FR-001**: Implement `download.py` with checksumming and size validation.
2.  **FR-002 / FR-011**: Implement `preprocess.py` (dF/F, detrend, OASIS deconvolution, interpolation).
3.  **FR-003 / FR-010**: Implement `nmf_engine.py` with **custom temporal penalty solver** and CPU-only enforcement. Include multi-seed sweep for stability (SC-004).
4.  **FR-004 / SC-005**: Implement `alignment.py` for resampling, timestamp alignment, and **alignment error calculation**.
5.  **FR-008**: Implement `split.py` for **time-based train/test splitting** (80/20).
6.  **FR-005 / FR-006 / SC-003**: Implement `stats.py` (Spearman + 1000-iter permutation) with **Benjamini-Hochberg FDR correction**. Restrict testing to held-out set.
7.  **FR-009**: Implement `null_model.py` to generate **time-shuffled baseline** for comparison.

### Phase 3: Testing & Validation (Research Accepted)
*Goal: Verify against acceptance criteria.*
1.  **US-1**: Verify memory usage ≤ 5GB and NaN handling.
2.  **US-2**: Verify NMF convergence and CPU execution.
3.  **US-3**: Verify permutation test significance (p < 0.05 corrected) on **held-out set** only.
4.  **SC-004**: Run stability check (cosine similarity ≥ 0.95) across seeds.
5.  **SC-005**: Verify alignment error ≤ 1 frame.

