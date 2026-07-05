# Implementation Plan: Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence

**Branch**: `001-quantify-resolution-impact` | **Date**: 2023-10-27 | **Spec**: `specs/001-quantifying-resolution-impact/spec.md`
**Input**: Feature specification from `specs/001-quantifying-resolution-impact/spec.md`

## Summary

This project quantifies the systematic bias introduced by spatial resolution limits in isotropic turbulence simulations. The technical approach involves downloading high-resolution velocity fields from the Johns Hopkins Turbulence Database (JHTDB), synthetically generating lower-resolution variants via Fourier-mode truncation, and computing comparative statistics (energy spectra $E(k)$ and structure functions $S_p(r)$). The analysis strictly adheres to CPU-only constraints (cores, 7 GB RAM) by processing data in spatial slices and utilizing optimized FFT libraries. The output includes bias curves, scaling exponent deviations, and Confidence intervals derived from bootstrap resampling across multiple snapshots.

**Critical Note on Data Integrity**: This project strictly prohibits the use of simulated, placeholder, or hardcoded metrics. All reported bias values, scaling exponents, and confidence intervals MUST be derived from the actual execution of the pipeline against real JHTDB data. Any task that cannot be executed due to data constraints must be flagged as "Skipped" rather than simulated.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `h5py`, `scikit-learn`, `matplotlib`, `pandas` (all CPU-optimized wheels)  
**Storage**: Local HDF5 for intermediate derivatives; raw data streamed from JHTDB mirrors.  
**Testing**: `pytest` (unit tests for spectral computation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7 GB RAM, no GPU).  
**Project Type**: Scientific Computing / Data Analysis Library  
**Performance Goals**: Full pipeline (5 snapshots, 4 resolutions) ≤ 6 hours; Peak RAM ≤ 7 GB.  
**Constraints**: No GPU/CUDA; no full 2048³ load into memory; strict memory accounting via RSS.  
**Scale/Scope**: Multiple independent JHTDB snapshots (1024³); downsampling factors (, 4, 8, 16).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (Principle I)**: The plan mandates pinned `requirements.txt`, random seed initialization in all stochastic steps (bootstrap), and deterministic JHTDB fetching via checksum verification scripts.
2.  **Verified Accuracy (Principle II)**: All citations to JHTDB datasets will reference the verified URLs in `research.md`. The plan explicitly rejects hardcoded metrics; all bias values are computed from real data.
3.  **Data Hygiene (Principle III)**: The plan includes a `checksums.json` artifact. Raw data is read-only; all downsampled derivatives are written to new files with resolution tags (e.g., `snapshot_001_res2.hdf5`).
4.  **Single Source of Truth (Principle IV)**: Figures and tables in the final report will be generated programmatically from the `data/` directory. No manual data entry is permitted in the paper.
5.  **Versioning Discipline (Principle V)**: The plan requires content hashes for all generated artifacts. Any change to the downsampling algorithm or statistical method invalidates previous hashes.
6.  **Numerical Resolution & Bias Quantification (Principle VI)**: The core of the plan is the explicit calculation of bias against the highest available resolution ground truth, with resolution limits reported for every statistic.

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-resolution-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (Input to Implementation)
```

### Source Code (repository root)

```text
projects/PROJ-535-quantifying-the-impact-of-data-resolutio/
├── code/
│   ├── __init__.py
│   ├── download.py          # JHTDB fetcher with checksum verification
│   ├── downsample.py        # Fourier truncation logic
│   ├── stats.py             # E(k) and S_p(r) computation
│   ├── analysis.py          # Bias calculation, fitting, bootstrap
│   └── main.py              # Orchestration script
├── data/
│   ├── raw/                 # Downloaded JHTDB snapshots (symbolic links or staged)
│   ├── processed/           # Downsampled variants and computed stats
│   └── checksums.json       # Integrity manifest
├── tests/
│   ├── unit/                # Test spectral math, memory limits
│   └── integration/         # End-to-end pipeline test
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected to minimize I/O overhead and simplify memory management on the constrained runner. All analysis logic is modularized in `code/` to allow unit testing of individual mathematical operations (e.g., FFT truncation) without requiring full dataset downloads.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project adheres to a single, linear pipeline: Download -> Downsample -> Compute -> Analyze. | No complex microservices or multi-stage orchestration required for this specific scientific computation. |

## Phase Breakdown

### Phase 0: Research & Dataset Strategy
*   **FR-001, US-1**: Verify JHTDB dataset availability and memory footprint. Select 5 snapshots with sufficient Reynolds number to ensure an inertial subrange.
*   **FR-002, US-1**: Validate Fourier truncation logic on a synthetic Kolmogorov field.
*   **FR-003, US-2**: Confirm FFT libraries (`scipy.fftpack` or `numpy.fft`) run within 2-core limits for 1024³ data.
*   **FR-006, US-3**: Estimate bootstrap runtime (A sufficient number of iterations) on 5 snapshots to ensure ≤ 6h total runtime. *Note: Acknowledges statistical power limitations of N=5.*

### Phase 1: Data Model & Contracts
*   Define schemas for input velocity fields and output bias metrics.
*   Establish data hygiene protocols (checksums, naming conventions).

### Phase 2: Design & Task Definition
*   **Output**: `tasks.md` (Implementation Task List).
*   Define the specific algorithmic steps for FFT-based structure function computation (to avoid O(N^6) complexity).
*   Define the "Valid Fitting Range" logic to exclude Gibbs-affected scales.
*   Define the fallback parametric uncertainty method if N=5 bootstrap is too sparse.

### Phase 3: Implementation
*   **FR-001**: Implement `download.py` with slice-by-slice reading to stay under 7 GB RAM.
*   **FR-002**: Implement `downsample.py` with strict anti-aliasing (zeroing high-k modes).
*   **FR-003, FR-004**: Implement `stats.py` for $E(k)$ and $S_p(r)$ (FFT-based) and bias calculation.
*   **FR-005, FR-006**: Implement `analysis.py` for power-law fitting and bootstrap CI.
*   **FR-007**: Add memory monitoring hooks to abort if RSS > 7 GB.
*   **Execution**: Run the full pipeline on 5 snapshots. **No simulated results.**

### Phase 4: Validation & Reporting
*   Execute full pipeline on 5 snapshots.
*   Generate figures and tables.
*   Verify all results are real measurements (no fabrication).

## Statistical Rigor & Limitations

- **Bootstrap Power**: The plan uses N=5 independent snapshots. We acknowledge that 95% confidence intervals derived from this sample size will have low statistical power. Results will be presented as "Descriptive Bounds" with explicit warnings about the uncertainty of the interval width.
- **Computational Feasibility**: Structure functions will be computed via FFT-based convolution (Wiener-Khinchin) for $S_2$ and sparse sampling for $S_3$ to ensure runtime fits within 6 hours on 2 cores.
- **Ground Truth**: The "ground truth" is defined as the 1024³ dataset. We explicitly acknowledge that this dataset itself contains finite-Reynolds-number effects. The analysis measures "Relative Bias against the Best Available Proxy," not absolute physical truth.