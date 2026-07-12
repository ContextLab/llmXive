# Implementation Plan: llmXive follow-up: extending "Wan-Streamer v0.1: End-to-end Real-time Interactive Foundation Models"

**Branch**: `001-llmxive-streamer-optimization` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-streamer-optimization/spec.md`

## Summary

This project investigates the existence of "low-information manifolds" in audio-visual generation by training a lightweight CPU-tractable estimator to predict latent vector deltas based on turn-taking semantics. The core approach involves extracting time-series latent data and turn-taking labels from Wan-Streamer v0.1 logs (or VoxCeleb2 fallback), training a shallow RNN/Transformer to predict delta magnitude and uncertainty, and simulating a hybrid inference pipeline that skips flow-matching steps for predicted "low-priority" frames.

**Scope Limitation**: The primary research claim ("Extending Wan-Streamer") is contingent on the availability of Wan-Streamer v0.1 training logs. 
- **If logs are available**: The project performs full Hybrid Inference Simulation against the Wan-Streamer baseline, measuring FID degradation and latency reduction as per SC-001/SC-002.
- **If logs are missing**: The project falls back to VoxCeleb2 for *methodological validation* only. The results are framed as a "Proof-of-Concept for the Pipeline" rather than "Wan-Streamer Optimization". The Hybrid Simulation in this mode uses a linear interpolation baseline, and FID degradation metrics are reported as "Proxy Simulation Results" with explicit disclaimers.

Success is measured by a ≥20% latency reduction with ≤5% FID degradation (if logs available), validated via paired statistical tests (TOST, bootstrap) and a randomized counterfactual intervention to establish causal efficacy.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU wheel), `scikit-learn`, `pandas`, `pyyaml`, `datasets` (HuggingFace), `numpy`, `scipy` (for TOST/bootstrap), `torchmetrics` (for FID), `opencv-python`.  
**Storage**: Local filesystem (Parquet/CSV) for intermediate data; GitHub Actions ephemeral storage.  
**Testing**: `pytest` (unit/contract), shell scripts for integration (data extraction, training, simulation).  
**Target Platform**: Linux (GitHub Actions Free Tier: limited CPU resources, ~7 GB RAM, no GPU).  
**Project Type**: Research/Computational Experiment.  
**Performance Goals**: Training ≤ 6h; Peak RAM ≤ 7 GB; Inference simulation latency reduction ≥ 20%.  
**Constraints**: No GPU/CUDA; No quantization libraries requiring CUDA; Strict memory limits; Reproducibility via pinned seeds.  
**Scale/Scope**: Sampled dataset ≤ 1 GB (target 10k+ frames); 1 lightweight model; 1 simulation pipeline.

**Dataset Version Pinning**: To satisfy Constitution Principle I (Reproducibility), the `code/config.py` file will pin the exact HuggingFace dataset revision for VoxCeleb2 (e.g., `revision: 'main'` or a specific commit hash) to ensure the canonical source is fetched on every run.

## Constitution Check

| Principle | Status | Compliance Strategy |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; Data fetched from verified URLs (VoxCeleb2) or checksummed local logs (treated as canonical artifacts); `requirements.txt` pinned. Local logs are only for dev; reproducible runs use canonical source. |
| **II. Verified Accuracy** | PASS | Citations restricted to verified dataset URLs provided in spec; No external claims without source. |
| **III. Data Hygiene** | PASS | Raw data checksummed; Derivations (latents, labels) written to new files; PII scan passed (VoxCeleb2 is public). |
| **IV. Single Source of Truth** | PASS | All metrics (FID, Latency) computed by `code/` and logged to `data/`; No hand-typed numbers in `plan.md`. |
| **V. Versioning Discipline** | PASS | Artifact hashes recorded in `state.yaml` via `update_state_yaml` task module. |
| **VI. Latency-Quality Trade-off** | PASS | Plan mandates paired statistical tests (TOST is a paired test; compares Hybrid vs. Baseline on same frames) and randomized counterfactuals to validate claims. |
| **VII. Validation Independence** | PASS | Estimator trained on latent/turn data; FID/MOS computed by separate, frozen pre-trained models (not used in training). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-streamer-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   ├── dataset_schema.schema.yaml
│   ├── estimator_predictions.schema.yaml
│   ├── evaluation_metrics.schema.yaml
│   ├── hybrid_metrics.schema.yaml
│   ├── latents.schema.yaml
│   ├── metrics.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py                # Dataset version pinning
│   ├── data/
│   │   ├── extract_latents.py       # FR-001, US-1
│   │   ├── preprocess.py            # US-1
│   │   └── validate_sampling.py     # FR-015
│   ├── models/
│   │   ├── estimator.py             # FR-002, US-2 (RNN/Transformer)
│   │   └── trainer.py               # US-2
│   ├── inference/
│   │   ├── hybrid_sim.py            # FR-003, US-3
│   │   ├── fallback_handler.py      # FR-006, FR-009
│   │   └── randomized_intervention.py # FR-008
│   ├── metrics/
│   │   ├── fid_stability.py         # FR-010, FR-011
│   │   ├── mos_validation.py        # FR-012, FR-013
│   │   └── stats_tests.py           # FR-005, FR-007, FR-016
│   └── utils/
│       ├── state_manager.py         # FR-020
│       └── config.py
├── data/
│   ├── raw/                         # Downloaded datasets
│   ├── processed/                   # Extracted latents, labels
│   └── artifacts/                   # Model checkpoints, logs
├── tests/
│   ├── contract/                    # Schema validation tests
│   ├── integration/                 # End-to-end pipeline tests
│   └── unit/                        # Model logic tests
└── state.yaml
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`data`, `models`, `inference`, `metrics`) to isolate responsibilities and facilitate independent testing of the estimator vs. the evaluation metrics (Constitution Principle VII).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Randomized Counterfactual (FR-008)** | Required to distinguish "easy to skip" from "easy to generate" and establish causal effect (US-3, Edge Cases). | Observational propensity matching alone (FR-005) is insufficient for causal claims; it only adjusts for confounders, does not prove intervention efficacy. |
| **Fallback Logic (FR-006, FR-009)** | Ensures quality safety when uncertainty is high; prevents degradation on non-smooth trajectories. | Blind skipping based on prediction alone risks >5% FID degradation on ambiguous frames. |
| **Hybrid Simulation (FR-003)** | Necessary to measure the *actual* trade-off of the proposed skipping strategy. | Running only the estimator does not measure the system-level latency/quality impact. |
| **Segment-Level FID** | FID is a batch metric; per-frame FID is mathematically invalid. | Using per-frame FID would yield degenerate results. We compute FID over segments (windows) to maintain validity while approximating frame-level granularity. |