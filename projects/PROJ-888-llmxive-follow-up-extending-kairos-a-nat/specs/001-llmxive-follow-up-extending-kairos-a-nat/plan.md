# Implementation Plan: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Branch**: `001-llmxive-kairos-discrete-scaling` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-follow-up-extending-kairos-a-nat/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-kairos-a-nat/spec.md`

## Summary

This project investigates the scaling of minimum information density required for stable long-horizon forecasting in embodied agents as input modality shifts from continuous visual streams to sparse, discrete sensor streams. The technical approach involves converting the continuous LIBERO benchmark dataset into discrete, quantized JSON state vectors (4-bit, 8-bit, 16-bit), injecting controlled noise to simulate sensor instability, and evaluating the stability of the "Kairos" Hybrid Linear Temporal Attention mechanism under these constraints. The entire pipeline is engineered to run on a CPU-only GitHub Actions free-tier runner (limited cores, constrained RAM, time-constrained environment)., ensuring the results are directly applicable to resource-constrained edge deployment scenarios.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `numpy`, `pandas`, `datasets` (HuggingFace), `scikit-learn`, `pyyaml`, `pytest`, `h5py`, `arviz` (for Bayesian analysis)  
**Storage**: Local file system (JSON for discrete vectors, HDF5 for raw data caching), GitHub Actions ephemeral storage  
**Testing**: `pytest` (unit tests for quantization logic, integration tests for pipeline execution, contract tests against YAML schemas)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free tier), CPU-only execution  
**Project Type**: Research pipeline / Data processing & Modeling  
**Performance Goals**: Training loop convergence within 4 hours (graceful exit at 6h), inference latency ≤ 2s/step, peak RAM < 7GB.  
**Constraints**: No GPU/CUDA usage, no 8-bit/4-bit quantization libraries requiring CUDA (e.g., `bitsandbytes`), strict adherence to 7GB RAM limit via data chunking.  
**Scale/Scope**: LIBERO dataset subset (sampled to fit RAM), 10 independent runs with varying noise seeds, 3 quantization levels (4, 8, 16-bit).  
**Prediction Horizons**: 100, 500, and 1000 steps (per Constitution Principle VII).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Plan / Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External datasets fetched from verified HuggingFace URLs (LIBERO) on every run. `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | **PASS** | All citations to LIBERO and Kairos architecture will be validated against primary sources. No fabricated dataset URLs; only verified sources used. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed before processing. Quantized outputs written to new files with derivation logs. No in-place modification of raw HDF5 files. PII scan configured. |
| **IV. Single Source of Truth** | **PASS** | All error metrics (MSE, p-values/credible intervals) will be generated programmatically and stored in `data/` as CSV/JSON. Paper figures will be generated directly from these files. |
| **V. Versioning Discipline** | **PASS** | Content hashes for all artifacts in `data/` and `code/` will be tracked in `state/`. `updated_at` timestamps managed by the Advancement-Evaluator. |
| **VI. Resource-Constrained Stability** | **PASS** | Pipeline explicitly designed for a minimal multi-core/low-memory configuration. Training loop includes memory monitoring and graceful exit at 6h. Quantization parameters (4/8/16-bit) explicitly logged. |
| **VII. Discrete Modality Error** | **PASS** | MSE normalized by state space dimensionality. Cumulative error growth calculated over 100, 500, and 1000 steps. Bayesian Hierarchical Modeling (BHM) used for multiple independent runs to ensure statistical power. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-kairos-discrete-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/
├── code/
│   ├── __init__.py
│   ├── config.py                # Configuration for seeds, paths, quantization levels
│   ├── data/
│   │   ├── download_libero.py   # Fetches from verified HuggingFace URLs (HDF5)
│   │   ├── quantize.py          # Converts HDF5/Parquet to JSON discrete vectors
│   │   └── noise.py             # Injects Gaussian noise with clamping
│   ├── models/
│   │   ├── __init__.py
│   │   ├── kairos_adapter.py    # Loads pre-trained weights, replaces visual encoder
│   │   └── training_loop.py     # CPU-only training (two-stage: encoder pre-train, then freeze)
│   ├── analysis/
│   │   ├── metrics.py           # MSE, cumulative error growth calculation
│   │   └── stats.py             # Bayesian Hierarchical Modeling (BHM)
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded HDF5/Parquet files (checksummed)
│   ├── processed/               # Quantized JSON vectors
│   └── results/                 # MSE logs, stats outputs
├── tests/
│   ├── contract/                # Schema validation tests (validates training_loop.py output)
│   ├── integration/             # End-to-end pipeline tests
│   └── unit/                    # Quantization logic tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (`projects/.../code/`) selected to align with the research pipeline nature of the work. The separation of `data`, `models`, and `analysis` ensures modularity while maintaining a clear data flow from raw ingestion to statistical reporting. This structure supports the "Single Source of Truth" principle by keeping all intermediate artifacts within the project tree. The `tests/contract/` suite explicitly validates the output of `training_loop.py` against `contracts/error_metric.schema.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Two-Stage Training** | Standard libraries do not support the specific "discrete sensor simulation" with Gaussian noise injection and bin clamping required by US-1. | Using pre-binned datasets would not allow the controlled sweep of quantization levels (4/8/16-bit) and noise parameters (0.1-0.5 std dev) needed for the scaling law analysis. |
| **CPU-Only Training Adapter** | The Kairos model is typically trained on GPU; a custom adapter is needed to replace the visual encoder with a fixed discrete projection without triggering CUDA errors. | Attempting to run the original GPU-optimized code on CPU would result in "CUDA device" errors or OOM, failing US-2. |
| **Statistical Rigor (BHM)** | To satisfy FR-005 and SC-004 with N=10 runs, a Bayesian Hierarchical Model is required to handle low-N high-variance data and avoid Type II errors. | A frequentist t-test with N=10 lacks the power to detect subtle scaling effects, risking a false negative conclusion. |
| **HDF5 Parsing** | The LIBERO benchmark distributes data as HDF5 files, not Parquet. | Assuming Parquet format would result in data loading failures and invalid state extraction. |