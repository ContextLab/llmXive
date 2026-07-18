# Implementation Plan: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Branch**: `001-llmxive-discrete-scaling` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-llmxive-discrete-scaling/spec.md`

## Summary

This project implements a CPU-tractable study to determine how the minimum information density required for stable long-horizon forecasting in embodied agents scales as input modality shifts from continuous visual streams to sparse, discrete sensor streams. The approach involves: (1) converting the continuous LIBERO benchmark dataset into discrete, quantized JSON state vectors (4/8/12/16-bit) with simulated sparsity (temporal subsampling); (2) adapting the pre-trained Kairos Hybrid Linear Temporal Attention model to accept these discrete inputs via a fixed projection layer (or training from scratch if weights are missing); (3) training and evaluating the model on a CPU-only environment (-core/7GB RAM) to simulate edge constraints; and (4) performing statistical validation (paired t-tests/Wilcoxon) to identify the stability threshold where error accumulation exceeds baseline visual-modality performance.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `datasets` (HuggingFace), `numpy`, `pandas`, `scipy` (for statistical tests), `json`, `h5py` (for LIBERO HDF5 parsing), `tqdm`, `psutil` (RAM monitoring)  
**Storage**: Local `data/` directory (raw HDF5/Parquet, processed JSON), `data/processed/` (quantized streams), `data/results/` (MSE logs, checkpoints)  
**Testing**: `pytest` (unit tests for quantization logic, integration tests for training loop), `pytest-timeout` (enforce 6h limit)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, Substantial disk storage capacity.)  
**Project Type**: Research Pipeline / Data Processing / Model Training  
**Performance Goals**: Training time ≤ 4 hours (graceful exit at h), Peak RAM < 7GB, Inference latency ≤ 2s/step  
**Constraints**: No GPU/CUDA; strict adherence to FR-004 (100, 250, 500 step horizons) and FR-005 (t-test/Wilcoxon only); quantization sweep in fixed-bit increments  
**Scale/Scope**: LIBERO dataset subset (N=50 episodes, A fixed number of steps per episode.); Multiple independent runs per quantization level; 3 quantization levels (4, 8, 12, 16-bit)

> **Note on Dataset**: The plan uses the verified LIBERO HDF source. As no "JSON-serialized" dataset exists in the verified list, the pipeline *must* generate this artifact from the raw HDF5 source (Addressing Assumption about data).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Requirement | Plan Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned; canonical sources. | `code/config.py` defines `SEED=42`. `datasets.load_dataset` uses verified URLs. Checksums recorded in `data/`. Untrained runs are recorded but excluded from final stats. |
| **II. Verified Accuracy** | Citations verified. | All dataset URLs match the `# Verified datasets` block. No external papers cited without verification. |
| **III. Data Hygiene** | Checksummed; no in-place mods. | Raw HDF5 downloaded to `data/raw/`. Quantized JSON written to `data/processed/`. Checksums generated post-conversion. |
| **IV. Single Source of Truth** | Figures trace to `data/`. | `code/analysis.py` reads *only* from `data/results/` to generate plots. No hand-typed numbers. |
| **V. Versioning** | Content hashes. | `state/...yaml` updated on artifact change. `requirements.txt` pinned. |
| **VI. Resource-Constrained** | CPU-only (2-core/7GB/6h). | Model uses `device="cpu"`. Training loop includes `timeout` check. RAM monitored via `psutil`. Sweep values: **[4, 8, 12, 16]**. |
| **VII. Discrete Modality** | MSE normalized; horizons /250/500; t-test/Wilcoxon; **No BHM**. | `code/metrics.py` implements horizons **[100, 250, 500]**. `code/stats.py` uses `scipy.stats.ttest_rel` or `wilcoxon`. **No Bayesian Hierarchical Models**. |

**Addressing Unresolved Panel Concerns**:
1.  **Stats Method**: `code/stats.py` will **only** implement `paired t-test` and `Wilcoxon signed-rank` as primary methods. Bayesian Hierarchical Models are **excluded** to comply with FR-005 and Principle VII.
2.  **Horizon Steps**: `code/metrics.py` will calculate error growth strictly for horizons **[100, 250, and 500]**. The 1000-step horizon is **removed** to align with FR-004.
    *   *Constitution Note*: While Principle VII mentions 1000 steps, FR-004 and SC-001 explicitly mandate [100, 250, 500]. The plan follows the specific functional requirement (FR-004) over the generic principle text.
3.  **Weight Fallback**: If pre-trained Kairos weights are unavailable, the system will **train a model from scratch** for 5 epochs on the continuous baseline to learn temporal dependencies before testing discrete stability. This ensures the mechanism is tested, not random noise. Runs are flagged as "Untrained" and excluded from final stats but recorded for reproducibility.
4.  **Sensitivity Sweep**: `code/experiments.py` will explicitly sweep quantization levels **[4, 8, 12, 16]** bits. The terms "low/medium/high" are **replaced** with these specific integer values.
5. **Sample Size**: A fixed number of episodes per run, with 200 steps/episode (Total [deferred] steps). This provides sufficient power for the paired tests on the defined horizons.
6.  **Sparsity**: Simulated via **temporal subsampling** (stride=2) and **random dropout** (20% rate) to simulate low-bandwidth transmission.
7.  **Ground Truth**: Evaluation uses **Clean Ground Truth** (noise removed) to separate model error from sensor noise.
8.  **Statistical Validity**: Levene's test for equal variance is performed before t-test; if unequal, Wilcoxon is used. Pairing is by **Episode ID**.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-discrete-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/code/
├── config.py            # Seeds, paths, hyperparameters (10 runs, horizons, N=50)
├── download.py          # LIBERO fetch, Schema Verification, Weight fetch (with fallback)
├── quantize.py          # HDF5 -> JSON (4/8/12/16-bit) with noise injection and sparsity
├── model.py             # Kairos adapter (fixed projection layer or train-from-scratch)
├── train.py             # CPU training loop with checkpointing
├── metrics.py           # MSE, cumulative error (100, 250, 500), Entropy Check
├── stats.py             # Levene's test, Paired t-test, Wilcoxon, significance reporting
├── experiments.py       # Sweep loop (4, 8, 12, 16-bit)
└── utils.py             # Logging, RAM monitoring, timeout handling

tests/
├── unit/
│   ├── test_quantize.py
│   └── test_metrics.py
└── integration/
    └── test_training_loop.py
```

**Structure Decision**: Single project structure. All data processing and modeling occur in `code/` under the project ID. This ensures tight coupling between data hygiene and analysis, satisfying the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Custom Quantization Pipeline** | No verified JSON source exists; must transform HDF5 to discrete vectors. | Using a pre-processed dataset would require trusting an external, unverified source, violating Principle III (Data Hygiene). |
| **Fallback Weight Strategy** | Hard dependency on external weights risks total pipeline failure. | A hard fail would violate Reproducibility (Principle I) if the external source is temporarily down. The "Train-from-scratch" fallback allows the *mechanism* to be tested. |
| **Statistical Rigor (10 runs, N=50)** | Required for FR-005 to detect significant differences in error accumulation. | Single-run analysis is insufficient for statistical significance (p < 0.05) and violates Principle VII. |
| **Sparsity Simulation** | Quantization alone does not simulate "sparse streams". | Using only quantization would fail to answer the core research question about modality shift to sparse streams. |
| **Clean Ground Truth Evaluation** | Noise injection conflates sensor noise with model error. | Evaluating against noisy ground truth would penalize accurate models for predicting the underlying state. |