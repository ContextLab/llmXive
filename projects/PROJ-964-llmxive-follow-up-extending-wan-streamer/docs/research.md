# Research Documentation: llmXive Follow-up (Wan-Streamer Extension)

## Overview

This document details the research methodology, data flow, and statistical validation procedures for the llmXive automated science pipeline extension of Wan-Streamer v0.1.

## Table of Contents

1. [Research Goals](#research-goals)
2. [Data Sources](#data-sources)
3. [Methodology](#methodology)
4. [Statistical Validation](#statistical-validation)
5. [Model Architecture](#model-architecture)
6. [Hybrid Inference Strategy](#hybrid-inference-strategy)
7. [Quality-Latency Trade-off Analysis](#quality-latency-trade-off-analysis)
8. [Reproducibility Protocol](#reproducibility-protocol)
9. [References](#references)

## Research Goals

### Primary Objectives
1. **Data Extraction**: Extract time-series latent vectors and turn-taking labels from Wan-Streamer v0.1 logs or VoxCeleb2 dataset
2. **Lightweight Estimator**: Train a CPU-tractable GRU model to predict latent delta magnitude and uncertainty scores
3. **Hybrid Inference**: Simulate hybrid inference with randomized counterfactual interventions to validate latency reduction while maintaining quality

### Success Criteria
- Latency reduction ≥ 20%
- FID degradation ≤ 5%
- TOST equivalence test p-value < 0.05 (Δ=0.05)
- Uncertainty correlation r ≥ 0.7
- FID stability correlation r ≥ 0.7

## Data Sources

### Primary Data Source: Wan-Streamer v0.1 Logs
- **Location**: `data/raw/wan-streamer-logs/`
- **Format**: JSON/Parquet logs with timestamp, latent vectors, and turn-taking annotations
- **Fallback**: VoxCeleb2 dataset via HuggingFace datasets

### Data Validation
The pipeline implements a strict data source validation protocol:
1. Check for existing Wan-Streamer logs
2. If missing, check for cached VoxCeleb2
3. If both missing, fetch VoxCeleb2 via `datasets.load_dataset()`
4. Compute checksums and register in `state.yaml`

**Constitution Principle I**: Dataset revision pinning via `code/config.py`

## Methodology

### Phase 1: Data Extraction and Preprocessing

#### 1.1 Latent Vector Extraction
```python
from data.extract_latents import parse_wan_streamer_logs, fetch_and_process_voxceleb2
```
- Parse raw logs or fetch VoxCeleb2
- Extract latent vectors at frame-level granularity
- Detect interruption/pause events using configured thresholds

#### 1.2 Event Detection Thresholds
Configured in `code/config/detection_thresholds.yaml`:
- `audio_energy_threshold: 20` (default 20dB)
- Customizable per experiment

#### 1.3 Stratified Sampling
- Reduce dataset to ≤ 1GB while preserving distribution
- Parameters from `data/metrics/power_analysis.json`
- Preserve interruption/pause event distribution

### Phase 2: Lightweight Estimator Training

#### 2.1 GRU Architecture
```python
from models.gru_estimator import GRUEstimator
```
- Input: Latent vectors (time-series)
- Output: [delta_magnitude, uncertainty_score]
- CPU-optimized operations
- Memory constraint: ≤ 7GB RAM

#### 2.2 Training Protocol
- Wall-clock timeout: 6 hours
- Memory monitoring with automatic sample size reduction
- Uncertainty calibration on validation set

#### 2.3 Uncertainty Calibration
```python
from metrics.uncertainty_calibration import compute_uncertainty_correlation
```
- Correlation between predicted uncertainty and actual error
- Threshold: r ≥ 0.7
- Finalize checkpoint only if threshold met

### Phase 3: Hybrid Inference Simulation

#### 3.1 Counterfactual Intervention
```python
from inference.generate_counterfactual_indices import generate_counterfactual_indices
```
- Randomized subset: ≥ 5% of total frames
- Fixed seed: SEED=42
- Forced skip intervention for validation

#### 3.2 Fallback Handler
```python
from inference.fallback_handler import apply_fallback_logic
```
- Trigger full solver when:
 - Uncertainty > 0.8
 - Delta magnitude is high
- **Precedence Rule**: Randomized counterfactual overrides deterministic fallback

#### 3.3 Hybrid Inference Execution
```python
from inference.hybrid_sim import run_hybrid_inference
```
- Consume GRU estimator
- Apply fallback logic
- Generate hybrid output for quality metrics

## Statistical Validation

### Power Analysis
```python
from data.power_analysis import run_power_analysis
```
- A priori power analysis with conservative heuristics
- Output: `data/metrics/power_analysis.json`
- Updated with literature-derived estimates when available

### Latency Bias Analysis
```python
from inference.analyze_latency_bias import run_latency_bias_analysis
```
- Stratified bootstrap with propensity-score matching
- Independent covariates: frame timestamp, audio energy
- Excludes estimator predictions to avoid bias
- Output: `data/metrics/latency_bootstrap_results.csv`

### Equivalence Testing (TOST)
```python
from metrics.tost_equivalence import run_tost_equivalence_tests
```
- Two One-Sided Tests for quality metrics
- Equivalence margin: Δ=0.05
- Significance level: α=0.05
- Output: `data/metrics/tost_results.csv`

### FID Stability Correlation
```python
from metrics.fid_stability_corr import calculate_fid_stability_corr
```
- Correlation between predicted delta magnitude and FID stability
- Threshold: r ≥ 0.7
- Validation status recorded in `state.yaml`

### Proxy MOS Validation
```python
from metrics.validate_proxy_mos import validate_proxy_mos
```
- Pearson correlation between proxy MOS and human ratings
- Fallback: "Assumption Validated" if human ratings missing

## Model Architecture

### GRU Estimator Details
- **Type**: Gated Recurrent Unit
- **Input Shape**: [batch, sequence_length, feature_dim]
- **Output Shape**: [batch, 2]
 - Column 0: Predicted delta magnitude
 - Column 1: Uncertainty score (0.0-1.0)
- **CPU Optimization**: No CUDA, no 8-bit quantization
- **Memory Constraint**: ≤ 7GB RAM during training

### Training Loss
- Combined MSE for delta magnitude prediction
- Uncertainty calibration loss
- Regularization to prevent overfitting

## Hybrid Inference Strategy

### Decision Logic
1. **Estimator Prediction**: Compute delta magnitude and uncertainty
2. **Fallback Trigger**:
 - If uncertainty > 0.8 → Full solver
 - If delta magnitude > threshold → Full solver
 - If in randomized counterfactual set → Forced skip (for validation)
3. **Precedence**: Counterfactual intervention overrides deterministic fallback

### Quality-Latency Trade-off
- **Latency Reduction**: Measure time savings from skipped frames
- **Quality Preservation**: Monitor FID degradation
- **Equivalence Testing**: Validate that quality loss is within acceptable bounds

## Reproducibility Protocol

### Seed Pinning
```python
from utils.config import set_seed
```
- All random operations use fixed seeds
- Seeds recorded in `state.yaml`

### Artifact Hashing
```python
from utils.update_state_yaml import compute_file_hash
```
- All output files hashed and registered
- `state.yaml` tracks validation status

### Data Flow Verification
- Contract tests for schema validation
- Integration tests for end-to-end pipeline
- Unit tests for edge cases

### State Management
- `state.yaml` contains:
 - Artifact hashes
 - Validation status
 - Configuration snapshots
 - Execution metadata

## Configuration Files

### `code/config.py`
- Dataset revision pinning
- Data source selection
- Global configuration

### `code/config/detection_thresholds.yaml`
- Event detection thresholds
- Audio energy thresholds
- Turn-taking classification parameters

### `data/metrics/power_analysis.json`
- Sample size calculations
- Variance estimates
- Effect size parameters

## Error Handling

### Power Limitation
- Triggered when 6-hour training limit approached
- Calls `code/tasks/reduce_sample_size.py`
- Fails gracefully if minimum sample size reached
- Logs "Power Limitation" error

### Data Source Unavailable
- Fails loudly if real data source unreachable
- No synthetic fallback
- Clear error message for remediation

### Uncertainty Calibration Failure
- Raises error if correlation < 0.7
- Prevents checkpoint finalization
- Updates `state.yaml` with invalid status

## Validation Checklist

### Pre-Execution
- [ ] All directories created (`code/`, `data/`, `state/`, `docs/`)
- [ ] Dependencies installed (`requirements.txt`)
- [ ] Data source validated (`validate_logs.py`)
- [ ] Power analysis completed (`power_analysis.json`)

### Post-Execution
- [ ] All artifacts generated (`.parquet`, `.pt`, `.json`, `.csv`)
- [ ] State file updated (`state.yaml`)
- [ ] All tests passing (`pytest tests/`)
- [ ] Validation thresholds met (TOST, correlation, etc.)

## References

1. Wan-Streamer v0.1 Technical Report
2. VoxCeleb2 Dataset Documentation (HuggingFace)
3. GRU Architecture: Cho et al. (2014)
4. TOST Equivalence Testing: Schuirmann (1987)
5. FID Metric: Heusel et al. (2017)
6. Propensity Score Matching: Rosenbaum & Rubin (1983)

## Appendix: Artifact Locations

### Data Artifacts
- `data/raw/wan-streamer-logs/` - Raw logs
- `data/raw/voxceleb2/` - Fallback dataset
- `data/processed/sampled_dataset.parquet` - Preprocessed data
- `data/processed/counterfactual_indices.parquet` - Intervention indices
- `data/processed/hybrid_output.parquet` - Simulation output

### Model Artifacts
- `data/models/estimator_checkpoint_pending.pt` - Pending checkpoint
- `data/models/estimator_checkpoint_final.pt` - Validated checkpoint

### Metrics Artifacts
- `data/metrics/power_analysis.json` - Power analysis results
- `data/metrics/baseline_comparison.json` - Baseline MSE comparison
- `data/metrics/latency_bootstrap_results.csv` - Latency bias analysis
- `data/metrics/tost_results.csv` - Equivalence test results

### State Artifacts
- `state.yaml` - Project state and validation status
- `state/logs/` - Execution logs