# Implementation Plan: Neuromorphic Transformer Networks: Spiking Neural Dynamics in Language Models

**Branch**: `591-neuromorphic-transformer-spiking` | **Date**: 2026-06-24  
**Spec**: `specs/591-neuromorphic-transformer-spiking/spec.md`

## Summary

This project implements a comparative study between a standard 2-layer Transformer and a Spiking Neural Network (SNN) variant where feed-forward sub-layers are replaced by Leaky-Integrate-and-Fire (LIF) neurons. The study measures (a) temporal coding characteristics (spike timing, inter-spike intervals) and (b) the trade-off between language modeling performance (perplexity) and computational cost (energy-per-token). The implementation strictly adheres to CPU-only execution on GitHub Actions free-tier runners, utilizing `snnTorch` for SNN dynamics and `codecarbon` for energy logging, with explicit fallbacks for hardware limitations.

**Scientific Validity Note**: On CPU, SNN simulation is computationally more expensive than dense matrix multiplication. Therefore, the "energy-per-token" metric is a proxy for **computational cost**. The plan explicitly acknowledges that CPU measurements cannot validate true neuromorphic hardware efficiency claims; results will be framed as "computational cost trade-offs" rather than "energy efficiency gains."

## Technical Context

**Language/Version**: Python (compatible with `snnTorch` and `torch` CPU wheels)  
**Primary Dependencies**: `torch` (CPU-only), `snnTorch` (v0.9.x), `codecarbon`, `datasets`, `scikit-learn`, `pandas`, `numpy`  
**Storage**: Local filesystem (`data/` for datasets/logs, `code/` for scripts)  
**Testing**: `pytest` (unit tests for LIF dynamics, integration tests for training loops)  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, limited RAM, no GPU)  
**Project Type**: Computational research / Machine Learning experiment  
**Performance Goals**: Complete 10 seeds (5 baseline + 5 spiking) with 3+ epochs each within 6 hours; memory usage < 6GB.  
**Constraints**: No CUDA; no 8-bit quantization; strict CPU execution; energy metrics may be estimated if `codecarbon` fails.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Evidence |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in code; `requirements.txt` pins versions; dataset fetched from verified HuggingFace URL. |
| **II. Verified Accuracy** | **Pass** | All citations (snnTorch, codecarbon, WikiText) map to verified sources in `research.md`. |
| **III. Data Hygiene** | **Pass** | Data downloaded to `data/raw/`; checksums recorded in `state/`; no in-place modification. |
| **IV. Single Source of Truth** | **Pass** | Metrics saved to CSVs; paper figures generated programmatically from these CSVs. |
| **V. Versioning Discipline** | **Pass** | **Procedure**: Every artifact write triggers an agent-mediated update to `state/projects/PROJ-591-neuromorphic-transformer-networks-spikin.yaml`. The agent computes the SHA-256 content hash of the new artifact and updates the `updated_at` timestamp and `artifact_hashes` map. This ensures the state file is always synchronized with the latest artifact version. |
| **VI. Energy-Efficiency Transparency** | **Pass** | `codecarbon` used for all runs; fallback to wall-clock time with "estimated" flag. **CSV Compliance**: The output CSV explicitly includes columns: `model_type`, `seed`, `epoch`, `energy_per_token_kWh`, and `wall_clock_time` as required. |
| **VII. Neuromorphic Implementation Fidelity** | **Pass** | `snnTorch` LIF neurons used. **Unit Test Scope**: `code/tests/neuromorphic_fidelity_test.py` explicitly verifies: (1) Membrane potential dynamics follow the LIF update rule for a deterministic input, and (2) Surrogate-gradient learning produces non-NaN gradients on a mini-batch. |

## Project Structure

### Documentation (this feature)

```text
specs/591-neuromorphic-transformer-spiking/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-591-neuromorphic-transformer-networks-spikin/
├── code/
│   ├── __init__.py
│   ├── main.py                  # Entry point for training loops
│   ├── models/
│   │   ├── __init__.py
│   │   ├── baseline_transformer.py  # Standard -layer Transformer
│   │   └── spiking_transformer.py   # Transformer with LIF FFNs
│   ├── data/
│   │   └── dataset_loader.py      # WikiText-2 loading and preprocessing
│   ├── metrics/
│   │   ├── perplexity.py          # Perplexity calculation
│   │   ├── temporal_coding.py     # ISI, bits/spike, synchrony
│   │   └── energy_logger.py       # codecarbon wrapper + fallback
│   ├── analysis/
│   │   ├── statistical_tests.py   # Unpaired t-tests, threshold stability
│   │   └── plots.py               # Figure generation
│   └── tests/
│       ├── test_lif_dynamics.py   # Constitution Principle VII test
│       └── test_training_loop.py
├── data/
│   ├── raw/                       # Downloaded WikiText-2
│   └── processed/                 # Tokenized datasets
├── data/energy_logs/              # CSV logs from codecarbon
├── state/
│   └── projects/PROJ-591-neuromorphic-transformer-networks-spikin.yaml
└── requirements.txt
```

**Structure Decision**: Single-project structure (`code/` root) selected to minimize overhead and ensure all scripts run from a unified virtual environment. The `models/`, `data/`, and `metrics/` separation ensures modularity for testing and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **SNN Implementation** | Required to address Research Question (a) on temporal coding. | Standard ReLU/GeLU activations cannot model spike timing or inter-spike intervals. |
| **Energy Logging (codecarbon)** | Required to address Research Question (b) on computational cost. | Wall-clock time alone is insufficient for "energy" claims; codecarbon provides hardware-agnostic estimation. |
| **Multiple Seeds (Negative Count)

The specific value to remove/generalize: 'Negative Count'

Rewritten passage:
The study will investigate the research question regarding the impact of multiple seeds on system performance using the method of comparative analysis with varying seed configurations. References include [Citation].** | Required for statistical power (FR-008) and robustness. | Single run results are anecdotal and fail statistical significance testing (FR-009). |
| **Unpaired Statistical Design** | Required because Baseline and Spiking models use independent seeds. | Paired t-tests require dependent samples (same seed), which is not feasible for distinct architectures in this setup. |