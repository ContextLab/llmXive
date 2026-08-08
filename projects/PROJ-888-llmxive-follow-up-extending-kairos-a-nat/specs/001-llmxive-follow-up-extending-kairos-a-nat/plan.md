# Implementation Plan: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Branch**: `001-llmxive-discrete-scaling` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-discrete-scaling/spec.md`
**Input**: Feature specification from `specs/001-llmxive-discrete-scaling/spec.md`

## Summary

This project implements a CPU-tractable investigation into the stability of long-horizon forecasting in embodied agents under modality shift from continuous visual streams to sparse, discrete sensor streams. The technical approach involves: (1) converting the continuous LIBERO dataset into quantized JSON state vectors (4/8/16-bit) with derived velocities (from continuous data, then quantized) and controlled noise; (2) adapting the pre-trained Kairos Hybrid Linear Temporal Attention model by replacing visual embeddings with a trainable discrete projection layer; (3) executing training and inference on a CPU-only environment (GitHub Actions Free Tier); and (4) performing rigorous statistical analysis to identify the minimum information density threshold where model error exceeds a predefined acceptable margin above the continuous baseline.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `datasets` (Hugging Face), `numpy`, `pandas`, `scipy` (for statistical tests), `json`, `zstandard` (for compression), `pytest`, `psutil` (for resource profiling)  
**Storage**: Local filesystem (`data/` for raw/processed, `data/processed/quantized/` for JSON artifacts)  
**Testing**: `pytest` (unit tests for quantization logic, integration tests for training loop, contract tests for schema validation)  
**Target Platform**: Linux (GitHub Actions Free Tier: vCPU, 7GB RAM, 6h runtime)  
**Project Type**: Computational Research / Machine Learning Pipeline  
**Performance Goals**: Training convergence within 4 hours on sampled data; inference latency ≤ 2s/step; peak RAM < 7GB  
**Constraints**: No CUDA/GPU access; no external API calls during execution; strict adherence to a predefined runtime limit with checkpointing; statistical power ≥ 0.8 (N≥10 runs)  
**Scale/Scope**: LIBERO dataset subset (a subset of episodes for training); Multiple quantization levels (e.g., 8, 16-bit); independent noise seeds; Multiple prediction horizons (100, 250, 500, 1000 steps)

> **Dataset Note**: The LIBERO benchmark is used as the source. Per the "Verified datasets" block, direct parquet URLs are available. The plan assumes a programmatic fetch via `datasets.load_dataset` or direct download of the verified parquet shards.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds in `config.py`, and explicit dataset source URLs from the verified block. |
| **II. Verified Accuracy** | **PASS** | All dataset references restricted to the "Verified datasets" block. No external citations invented. |
| **III. Data Hygiene** | **PASS** | Plan specifies checksumming raw data, creating new files for derived data (quantized JSON), and no in-place modification. Explicit 1-bit collapse halt logic (FR-010) ensures data integrity. |
| **IV. Single Source of Truth** | **PASS** | All error metrics and stability claims will be generated programmatically and stored in `results/` before being referenced in reports. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes will be recorded in `state/...yaml` upon generation. |
| **VI. Resource-Constrained Stability** | **PASS** | The entire pipeline is designed for CPU-only execution (2-core/7GB RAM). Stability claims are explicitly framed against this constraint. Explicit resource validation step (SC-003) produces pass/fail artifacts. |
| **VII. Discrete Modality Error Characterization** | **PASS** | Plan mandates MSE normalization, cumulative error growth analysis over horizons of 100, 250, 500, **and 1000** steps, and Mixed-Effects Models for statistical validation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-discrete-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── config.schema.yaml
│   ├── discrete_state_vector.schema.yaml
│   ├── error_metric.schema.yaml
│   └── stats.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/
├── data/
│   ├── raw/               # Downloaded LIBERO parquet shards
│   ├── processed/
│   │   └── quantized/     # JSON-serialized discrete state vectors
│   └── checksums.json     # SHA256 hashes of raw data
├── code/
│   ├── __init__.py
│   ├── config.py          # Hyperparameters, seeds, paths
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py      # HuggingFace dataset loading
│   │   ├── quantize.py    # Quantization, velocity derivation, noise injection
│   │   └── validator.py   # 1-bit collapse detection, bin clamping
│   ├── models/
│   │   ├── __init__.py
│   │   ├── kairos_adapter.py # Discrete projection layer replacement
│   │   └── training.py    # CPU training loop, checkpointing
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py     # MSE, noise floor separation (reporting), cumulative growth
│   │   └── stats.py       # Mixed-effects models, stability threshold mapping
│   ├── utils/
│   │   ├── logging.py     # Resource profiling (CPU/RAM)
│   │   └── seeds.py       # Seed management
│   └── main.py            # Orchestration script
├── tests/
│   ├── __init__.py
│   ├── test_quantize.py   # Unit tests for FR-001, FR-010
│   ├── test_model.py      # Unit tests for FR-002
│   └── test_stats.py      # Unit tests for FR-005
├── results/
│   ├── runs/              # Per-seed output artifacts
│   └── aggregate/         # Final stability report
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure (`projects/.../code/`) selected to align with the research nature of the project, ensuring all data processing, modeling, and analysis are tightly coupled and reproducible within a single virtual environment. This avoids the overhead of microservices for a batch-processing research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Statistical Power (N=10)** | Required to achieve power ≥ 0.8 for detecting error accumulation differences (FR-009, SC-004). | A single run or N=3 would yield unreliable p-values and fail to characterize the stability threshold robustly. |
| **Custom Quantization Pipeline** | LIBERO does not provide discrete states; velocities are not natively available. | Using raw continuous data would fail to answer the "modality shift" research question. Pre-made discrete datasets are not available (NO verified source). |
| **CPU-Only Optimization** | Mandatory for the "resource-constrained" hypothesis (FR-003, Assumption about target hardware). | GPU acceleration would invalidate the study's core premise regarding edge deployment stability and violates the compute constraint. |
| **Run-Level Pairing** | Required to ensure valid statistical comparison between discrete and continuous modalities. | Static baseline comparison would fail to account for data stochasticity and noise injection effects. |
| **1000-Step Horizon** | Required by Constitution Principle VII to characterize long-horizon stability. | Shorter horizons (100, 250) may not reveal the cumulative error growth rate required for the stability threshold. |
| **Mixed-Effects Models** | Required to account for temporal autocorrelation in autoregressive predictions (Scientific Soundness). | Simple paired t-tests would inflate Type I error rates due to serial correlation. |