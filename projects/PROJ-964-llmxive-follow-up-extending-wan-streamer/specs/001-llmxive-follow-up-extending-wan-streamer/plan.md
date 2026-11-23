# Implementation Plan: llmXive follow-up: extending "Wan-Streamer v0.1"

**Branch**: `001-llmxive-streamer-optimization` | **Date**: 2026-07-12 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-llmxive-streamer-optimization/spec.md`

## Summary

This project extends the "Wan-Streamer v0.1" architecture to investigate "low-information manifolds" in audio-visual generation. The core hypothesis is that turn-taking semantics (interruptions vs. pauses) predict the magnitude of latent vector deltas, allowing a lightweight estimator to skip expensive flow-matching steps for "low-priority" frames without significant perceptual degradation. The implementation involves extracting labeled time-series data from Wan-Streamer logs (or a verified conversational fallback), training a CPU-tractable RNN/Transformer estimator, simulating a hybrid inference pipeline with randomized counterfactuals, and validating quality-latency trade-offs using **Segment-Level FID** and proxy MOS metrics under strict CPU constraints (≤7 GB RAM, ≤6 hours).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `numpy`, `faster-fid` (or equivalent CPU-optimized FID), `torchaudio`, `librosa`  
**Storage**: Local filesystem (`data/` for artifacts, `code/` for scripts), `state.yaml` for versioning  
**Testing**: `pytest` (unit/integration), `pytest-cov`  
**Target Platform**: Linux (GitHub Actions CPU runner: vCPU, 7 GB RAM, 14 GB disk)  
**Project Type**: Research/Computational Experiment  
**Performance Goals**: Training ≤ 6 hours; Inference simulation ≤ 2 hours; Peak RAM ≤ 7 GB  
**Constraints**: No GPU access for training; must use open, downloadable datasets; must implement randomized counterfactuals (FR-008) and propensity-score matching (FR-005).  
**Scale/Scope**: Sampled dataset ≤ 1 GB; Model parameters < 50M; A large-scale dataset comprising tens of thousands of frames for training and evaluation..

> **Reproducibility Note**: All datasets are fetched via `datasets.load_dataset(..., revision="pin")` with explicit revision hashes stored in `state.yaml`. Random seeds are pinned in all scripts.
> **Data Validity**: If the primary source (Wan-Streamer logs) lacks conversational structure, the project will either use a verified conversational fallback or reframe the hypothesis to 'monologue dynamics' to avoid training on noise.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `datasets.load_dataset(..., revision="pin")` and `random.seed` in all scripts. `state.yaml` tracks artifact hashes. Dataset fetch tasks (T009) verify revision hashes. |
| **II. Verified Accuracy** | **PASS** | All citations (Wan-Streamer, VoxCeleb2) reference verified URLs from the input block. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | `data/` directory structure enforces checksums. No in-place modifications; derivations use new filenames. |
| **IV. Single Source of Truth** | **PASS** | `data-model.md` defines schema; `contracts/` provides YAML validation. All metrics trace to `data/` rows. |
| **V. Versioning Discipline** | **PASS** | `code/utils/state_manager.py` (FR-020) updates `state.yaml` with content hashes. Key path `state.validation_status` is explicitly defined. |
| **VI. Latency-Quality Trade-off** | **PASS** | Plan includes **Bootstrap-based Equivalence Test** for FID (due to non-Gaussianity) and **Paired** TOST for Latency. Both are implemented as paired tests (same segment under hybrid vs. baseline) to satisfy the 'paired' constraint. |
| **VII. Validation Independence** | **PASS** | Estimator training data is partitioned from FID/MOS evaluation data via a **time-based split** (or stratified by speaker) to ensure no data leakage. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-streamer-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── extract_turn_taking.py       # FR-001, US-1 -> Outputs TurnTakingEvent records
│   ├── preprocess_latents.py        # Data cleaning
│   └── fetch_data.py                # FR-019, FR-022 (Includes revision hash verification)
├── model/
│   ├── estimator_train.py           # FR-002, US-2 (Includes FR-023 Power Limitation logging)
│   ├── estimator_inference.py       # FR-003, FR-006
│   ├── hybrid_simulate.py           # FR-003, US-3, FR-008
│   └── execute_fallback.py          # FR-009 (Explicit task module for fallback logic)
├── metrics/
│   ├── calculate_fid.py             # FR-004
│   ├── validate_proxy_mos.py        # FR-012, FR-013 (Includes FR-024 Assumption Validated logging)
│   ├── calculate_fid_stability_corr.py # FR-010, FR-011 (Explicit task module)
│   ├── analyze_latency_bias.py      # FR-005, FR-007 (Explicit task module)
│   └── statistical_tests.py         # FR-005
├── utils/
│   ├── state_manager.py             # FR-020 (Updates state.validation_status)
│   ├── sampling_utils.py            # FR-015, FR-014
│   ├── reduce_sample_size.py        # FR-014 (Explicit task module)
│   ├── validate_sampling_distribution.py # FR-015 (Explicit task module)
│   └── config_loader.py             # T012a verification
├── inference/
│   └── full_solver.py               # T060 (Explicit script for full solver)
├── main.py                          # Orchestrator
└── requirements.txt                 # Pinned dependencies

data/
├── raw/                             # Downloaded datasets (checksummed)
├── processed/                       # Extracted CSV/Parquet (checksummed)
└── artifacts/                       # Model checkpoints, logs

tests/
├── unit/
├── integration/
├── contract/                        # Validates against contracts/
└── link_check.py                    # T038b (Verifies links in quickstart.md/data-model.md)
```

**Structure Decision**: Single-project structure with clear separation of `data`, `model`, and `metrics` modules to enforce the validation independence required by Constitution Principle VII. Explicit task modules (FR-007, FR-009, FR-011, FR-014, FR-015) are mapped to specific script files.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Randomized Counterfactuals (FR-008) | Required to distinguish "easy to skip" from "easy to generate" and establish causal effect. | Observational data alone (propensity matching) cannot rule out confounding variables in the latent trajectory. |
| Hybrid Inference Simulation | Essential to measure the *actual* FID degradation of skipping steps. | A purely theoretical model of latency/quality trade-off lacks empirical validity for the 5% threshold claim. |
| Two-Stage Validation (Estimator vs. FID) | Prevents circular validation (Principle VII). | Using the same data/model for training and evaluation would inflate performance metrics. |
| Segment-Level FID | Required for construct validity in video generation. | Frame-level FID fails to capture temporal artifacts (jitter, flicker) introduced by skipping steps. |

## Methodology

### 1. Data Extraction & Preprocessing (US-1, FR-001)
*   **Input**: Raw video/audio (Wan-Streamer logs or verified conversational fallback).
*   **Process**:
    *   **Label Validity Check**: Verify that the dataset contains actual conversational turn-taking (interruptions/pauses). If only monologues are present, reframe hypothesis to 'monologue dynamics' or fail.
    *   Extract latent trajectories using a frozen encoder.
    *   Compute `latent_delta_magnitude` between consecutive frames.
    *   Apply heuristic thresholds (FR-018) to label frames as "interruption", "pause", or "normal".
    *   Filter for events: Target ≥500 interruptions and ≥500 pauses (US-1 AS-2). If fewer exist, log actual count and proceed.
*   **Output**: `data/processed/turn_taking_dataset.parquet` (Schema: `timestamp`, `semantic_feature`, `prosodic_feature`, `latent_delta_magnitude`, `turn_label`).
*   **Verification**: T009 verifies dataset revision hash; T012a verifies config file existence.

### 2. Lightweight Estimator Training (US-2, FR-002)
*   **Model**: 2-layer LSTM or shallow Transformer (CPU-optimized).
*   **Task**: Predict `latent_delta_magnitude` and `uncertainty_score` (0.0-1.0) from history of semantic/prosodic features.
*   **Constraints**:
    *   Max RAM: 7 GB.
    *   Max Runtime: 6 hours.
    *   **Power Limitation (FR-023)**: If training exceeds limits, `reduce_sample_size.py` reduces sample size. If minimum sample size (calculated in Power Analysis) is reached, log "Power Limitation: Insufficient Sample" and exit with non-zero code.
*   **Validation**:
    *   MSE vs. Zero-Delta Baseline (Target: >10% improvement).
    *   **Two-Stage Validation**: (1) Train on Subset A. (2) Run FULL solver on Subset B (held-out) to generate Ground Truth FID Stability. (3) Correlate predictions with Ground Truth.
    *   Uncertainty calibration (SC-006).

### 3. Hybrid Inference Simulation (US-3, FR-003)
*   **Pipeline**:
    *   For each frame: Estimator predicts delta and uncertainty.
    *   **Skip Mechanism**: "Estimated (Skip)" is defined as **reusing the previous frame or linear interpolation** (explicitly defined to avoid ambiguity).
    *   **Decision Logic**:
        *   If `uncertainty > 0.8` (Threshold [deferred]): Use Full Solver.
        *   If `uncertainty ≤ 0.8` AND **not** in randomized subset: Use Estimated (Skip).
        *   **Randomized Counterfactual (FR-008)**: Force skip on ≥5% of frames regardless of prediction to establish causal effect.
        *   **Precedence (FR-017)**: Randomized intervention overrides deterministic fallback.
*   **Metrics**:
    *   **Latency**: Inference time per frame.
    *   **Quality**: **Segment-Level FID** (computed over sliding windows of 10-20 frames) and Proxy MOS.
    *   **Statistical Tests**:
        *   **Bootstrap-based Equivalence Test** for FID (due to non-Gaussianity).
        *   Paired TOST for Latency.
        *   Propensity-score matched paired test for latency validation.

## Statistical Rigor & Power Analysis

*   **Multiple Comparisons**: If multiple metrics (FID, MOS, Latency) are tested, apply Bonferroni or Benjamini-Hochberg correction.
*   **Power Analysis (FR-016)**:
    *   **Pre-Execution Calculation**: The system MUST calculate the required N to detect a statistically significant FID degradation

The research question is: What sample size is needed to detect a meaningful change in model performance?
The method is: Power analysis based on expected effect sizes.
References: Cohen (); Faul et al. (). with [deferred] power (e.g., 0.8) BEFORE data extraction.
    *   **Fail-Fast**: If the available sample (after sampling) is < required N, the system logs "Power Limitation: Insufficient Sample" and exits with a non-zero code. **It does not proceed with an underpowered sample.**
*   **Causal Inference**:
    *   **Observational**: Propensity-score matching (FR-005) controls for covariates (e.g., speaker identity, frame complexity) to validate latency reduction.
    *   **Causal**: Randomized counterfactuals (FR-008) isolate the effect of the "skip" action from the "easy frame" property.

## Compute Feasibility Strategy

*   **CPU-First**: All training and inference simulations are designed for CPU.
    *   Use `torch.no_grad()` for inference.
    *   Use small batch sizes (e.g., 8-16) to stay within 7 GB RAM.
    *   Use streaming datasets to avoid loading full data into memory.
*   **GPU Escape Hatch**: Not applicable for this specific plan as the estimator and simulation are designed to be CPU-tractable. If a future iteration requires a large-scale flow-matching solver that exceeds CPU capabilities, the plan would need to be revised to use the Kaggle GPU offload mechanism (scaled down).

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Dataset Mismatch**: VoxCeleb2 lacks explicit turn-taking labels. | **Dataset Validity Gate**: If Wan-Streamer logs are missing, the system checks for a verified conversational fallback. If none exists, it reframes the hypothesis to 'monologue dynamics' (removing 'interruption' labels) or fails. |
| **Power Limitation**: Dataset too large for 7 GB RAM. | Stream data; reduce sample size (FR-014); **Fail** if minimum sample size reached (FR-023). |
| **No Human Data**: Proxy MOS cannot be validated against human ratings. | Log "Assumption Validated (No Human Data Available)" (FR-012, SC-007) and skip correlation test. |
| **Wan-Streamer Logs Missing**: Primary source unavailable. | Automatically fallback to verified conversational dataset (FR-019) or reframe hypothesis. |

## Validation & Verification Tasks

*   **T009 (Data Source Check)**: Fetch data; **verify revision hash** matches pinned config.
*   **T012a (Config Check)**: Create config; **verify file exists and is valid YAML**.
*   **T037 (Quickstart Validation)**: Execute `quickstart.md` dry-run; generate **Quickstart Validation Report** with logs.
*   **T038b (Link Verification)**: Run `tests/link_check.py` to verify all links in `quickstart.md` and `data-model.md` exist.
*   **T043 (State Update)**: Update `state.yaml` key `state.validation_status`.
*   **T060 (Full Solver)**: Run `python code/inference/full_solver.py --input <segment> --output <path>`.