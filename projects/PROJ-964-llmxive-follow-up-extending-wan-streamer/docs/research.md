# Research Documentation: llmXive Follow-up

## Project Overview

**Project ID**: PROJ-964-llmxive-follow-up-extending-wan-streamer
**Goal**: Extend the "Wan-Streamer v0.1" pipeline to support hybrid inference, reducing latency while maintaining quality in turn-taking scenarios.
**Constitution Principles**:
- **I**: Data Integrity (Real data only, no synthetic inputs)
- **V**: Reproducibility (State tracking via `state.yaml`)
- **VI**: Statistical Rigor (Power analysis, TOST, Uncertainty calibration)

## User Stories & Methodology

### US1: Data Extraction and Preprocessing
**Objective**: Extract time-series latent vectors and turn-taking labels from real logs.
**Methodology**:
1. **Source Selection**: Prefer Wan-Streamer logs; fallback to VoxCeleb2 if missing (FR-019).
2. **Event Detection**: Use binary search on `audio_energy_threshold` to detect ≥500 interruption/pause events (FR-018).
3. **Statistical Power**: Perform 'a priori' power analysis on `latent_delta_magnitude` variance to determine minimum sample size (FR-016, SC-008).
4. **Stratified Sampling**: Reduce dataset to ≤1GB while preserving event distribution (FR-015).
**Artifacts**:
- `data/processed/raw_extract.parquet`
- `data/processed/sampled_dataset.parquet`
- `data/metrics/power_analysis.json`

### US2: Lightweight Estimator Training
**Objective**: Train a CPU-tractable GRU model to predict latent delta magnitude and uncertainty.
**Methodology**:
1. **Architecture**: Lightweight GRU with CPU-optimized operations (T025).
2. **Training**: Memory-constrained training loop (≤7GB RAM) with timeout monitoring (FR-014).
3. **Uncertainty Calibration**: Ensure correlation (r ≥ 0.7) between `UncertaintyScore` and actual prediction error (SC-006).
4. **Baseline Comparison**: Verify MSE improvement over zero-delta predictor (T020).
**Artifacts**:
- `data/models/estimator_checkpoint_final.pt`
- `data/metrics/baseline_comparison.json`

### US3: Hybrid Inference Simulation
**Objective**: Simulate hybrid inference with randomized counterfactual interventions.
**Methodology**:
1. **Counterfactual Generation**: Create `counterfactual_indices` (≥5% of frames) using fixed seed (FR-008).
2. **Fallback Logic**: Enforce full solver for high uncertainty/delta magnitude, with precedence for randomized subset (FR-017).
3. **Quality-Latency Trade-off**:
 - **Latency**: Validate ≥20% reduction via bootstrap with propensity-score matching (FR-005).
 - **Quality**: Validate FID degradation ≤5% via TOST equivalence tests (Δ=0.05) (FR-004).
4. **Proxy MOS**: Validate correlation (r ≥ 0.8) between proxy MOS and human ratings (if available) (SC-007).
**Artifacts**:
- `data/processed/hybrid_output.parquet`
- `data/metrics/latency_bootstrap_results.csv`
- `data/metrics/tost_results.csv`
- `data/metrics/fid_stability_corr.json`

## Data Flow & Schema

### Input Data
- **Wan-Streamer Logs**: JSON/Parquet logs containing latent vectors and audio features.
- **VoxCeleb2**: Standardized speech dataset (fallback).

### Processing Pipeline
1. `extract_latents.py` → `raw_extract.parquet`
2. `preprocess.py` → `sampled_dataset.parquet`
3. `trainer.py` → `estimator_checkpoint_pending.pt` → `estimator_checkpoint_final.pt`
4. `hybrid_sim.py` → `hybrid_output.parquet`

### Output Metrics
- **Power Analysis**: `min_sample_size`, `expected_variance`, `effect_size`.
- **Model Performance**: MSE, Uncertainty Correlation (r).
- **Simulation**: Latency reduction %, FID degradation %, TOST p-values.

## Verification & State Management

All artifacts are tracked in `state.yaml`:
- **Hashes**: SHA256 checksums of all data and model files.
- **Status**: `power_analysis_status`, `calibration_status`, `validation_status`.
- **Dependencies**: Explicit links between tasks (e.g., T013 → T014).

## Limitations & Assumptions

- **CPU-Only**: All models and simulations run on CPU; no GPU acceleration.
- **Data Availability**: If Wan-Streamer logs are missing, VoxCeleb2 is used (verified real source).
- **Human Ratings**: Proxy MOS validation assumes no human ratings are available unless `data/raw/human_ratings.json` exists.
- **Power Constraints**: Pipeline fails gracefully with "Power Limitation" error if sample size cannot be reduced further (FR-023).

## References
- Constitution Principles (FR-019, FR-020, etc.)
- User Stories (US1, US2, US3)
- Statistical Methods: TOST, Bootstrap, Propensity Score Matching.