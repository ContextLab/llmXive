# Implementation Plan: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

**Branch**: `001-llmxive-alayaworld-extend` | **Date**: 2026-08-21 | **Spec**: `specs/001-llmxive-follow-up-extending-alayaworld-l/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-alayaworld-l/spec.md`

## Summary

This project implements a hybrid inference pipeline to mitigate long-horizon semantic drift in video world models. The approach integrates a lightweight, deterministic, rule-based symbolic engine (tracking object HP, inventory, and existence) with a **CPU-tractable surrogate video generation model** (specifically, a quantized StyleGAN2-ADA variant at 256x256 resolution, as the original AlayaWorld is not CPU-feasible). 

The system generates interactive sequences of fixed duration using a **Within-Sequence Counterfactual Design**: for every action sequence, two parallel video streams are generated from the **identical initial latent noise** and random seed. 
- **Stream A (Baseline)**: No correction tokens injected.
- **Stream B (Hybrid)**: Correction tokens are **deterministically injected** (p=1.0) upon discrepancy detection.

The system compares the "Semantic Drift Score" of Stream B against Stream A to isolate the causal effect of the correction token. The implementation strictly adheres to CPU-only constraints (2 cores, 7 GB RAM) and validates the computer vision (CV) detection pipeline against the **Symbolic Ground Truth** to ensure the drift metric is statistically valid (≥85% detection accuracy).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU mode, default precision), `opencv-python` (headless), `scikit-learn`, `pandas`, `numpy`, `pytest`, `psutil`, `kornia` (for lightweight optical flow), `pyyaml`  
**Storage**: Local file system (`data/` for raw/processed video, `data/ground_truth/` for symbolic logs); JSON logs for state trajectories.  
**Testing**: `pytest` (unit tests for symbolic logic, integration tests for drift calculation, resource constraint benchmarks).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU cores, ~7 GB RAM, ~14 GB disk).  
**Project Type**: Computational Research / Inference Pipeline  
**Performance Goals**: 
- Wall-clock time per 60s sequence (at 15fps, 900 frames) ≤ 30 minutes.
- Peak memory usage ≤ 7 GB.
- CV detection accuracy ≥ 85% (validated against Symbolic GT).
**Constraints**: 
- NO GPU usage for inference (CPU-first).
- NO retraining of the surrogate model (frozen weights).
- Strict deterministic execution for the symbolic engine.
- Streaming data processing to avoid RAM overflow.
- **Feasibility Warning**: Generating a substantial number of frames on 2 cores is a tight budget. If generation rate drops below 0.5 fps, the pipeline will automatically skip frames (process every 3rd frame) to meet the 30-minute constraint, noting the reduced temporal resolution.
**Scale/Scope**: 
- N=10 random seeds for statistical significance (Feasibility Study).
- Short-duration sequences (approx. 900 frames at 15fps).
- Ground Truth subset: ≥50 frames (derived from Symbolic Engine state).
- **Note on Model**: The original AlayaWorld model is not CPU-tractable. This project uses a **StyleGAN2-ADA (256x256, 8-bit quantized)** surrogate to test the *methodology* of the hybrid correction. The research question is reframed to address this surrogate model. If the AlayaWorld model must be used, the project is flagged as 'Feasibility Failure'.

> **Note on Data Source**: The AlayaWorld model weights and data are expected as local artifacts with a specific SHA-256 checksum recorded in `data/checksums.txt`. If the checksum does not match, the run fails. No verified URL exists for AlayaWorld. The **StyleGAN2-ADA** surrogate weights must be sourced from a verified internal manifest (see Constitution Check).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds will be pinned in `code/config.py`. Local artifacts are checksummed (SHA-256) and verified before use. All scripts runnable via `pytest` or entry points. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` are restricted to the provided "Verified datasets" block (none for AlayaWorld, so no URL cited). The **Surrogate Model** (StyleGAN2-ADA) source is verified via a `data/verified_manifest.json` which records the provenance (e.g., "Internal Team X, Date Y") and hash. Ground Truth Validation (FR-007) ensures CV accuracy is measured against the **Symbolic Engine**, not human observation of the video. |
| **III. Data Hygiene** | **PASS** | All data in `data/` will be checksummed. Raw video and annotations will be immutable; derived logs (state trajectories) will be new files. No PII expected in synthetic game data. |
| **IV. Single Source of Truth** | **PASS** | Drift scores and statistical results in the final report will be derived directly from `data/results/` JSON/CSV files generated by the code. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be computed for all artifacts. The `state/` YAML file will be updated on artifact changes. |
| **VI. Deterministic Symbolic Grounding** | **PASS** | The symbolic engine is implemented in pure Python with no stochastic elements. State transitions are strictly rule-based. The output log is hashed (SHA-256) at each timestep and at the end to prove immutability. **Verification Step**: The final hash is compared against a pre-computed canonical hash to ensure no drift occurred in the engine itself. |
| **VII. Edge-Device Inference** | **PASS** | The pipeline is designed for multi-core/7GB constraints. Memory usage will be monitored via `psutil`. No GPU-dependent libraries (e.g., `flash-attn`, `cuDNN`) will be installed. The surrogate model (StyleGAN2-ADA 8-bit) is selected for CPU feasibility. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-alayaworld-extend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (source of truth for schemas)
└── tasks.md             # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Global config, seeds, paths
├── symbolic_engine.py   # Deterministic rule-based logic (HP, inventory)
├── cv_pipeline.py       # Template matching, optical flow, drift calculation
├── hybrid_controller.py # Correction token injection logic (with safety filter)
├── surrogate_wrapper.py # Interface to frozen surrogate model (CPU)
├── metrics.py           # Drift score calculation, statistical tests
├── validation.py        # Ground Truth Validation (FR-007)
├── resource_monitor.py  # Memory/CPU logging
├── calibration.py       # CV Calibration (Systematic Bias Correction)
└── main.py              # Entry point for baseline and hybrid runs

tests/
├── unit/
│   ├── test_symbolic_engine.py
│   └── test_cv_pipeline.py
├── integration/
│   └── test_drift_calculation.py
└── benchmark/
    └── test_resource_constraints.py

data/
├── raw/                 # Local video sequences (if provided)
├── ground_truth/        # Symbolic Engine State Logs (JSON)
├── processed/           # State trajectories, drift logs, symbolic hashes
├── calibration/         # CV Calibration results (Systematic Bias Maps)
└── results/             # Final scores, statistical reports, resource logs

contracts/
├── symbolic_state.schema.yaml
├── drift_result.schema.yaml
├── cv_annotation.schema.yaml
├── hybrid_controller.schema.yaml
└── action_sequence.schema.yaml
```

**Structure Decision**: Single project structure (`code/`, `tests/`, `data/`) selected to minimize overhead and align with the computational research nature of the project. This allows direct sharing of state objects between the symbolic engine and CV pipeline without complex inter-process communication.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Hybrid Controller** | Required to inject correction tokens dynamically based on symbolic state. | A pure baseline (no correction) fails to address the core research question of *mitigating* drift. |
| **Ground Truth Validation** | Required by FR-007 to ensure CV accuracy ≥ 85%. | Skipping validation risks invalid drift scores due to CV errors, rendering the experiment inconclusive. |
| **Resource Monitor** | Required by US-3 to verify CPU-only feasibility. | Without explicit monitoring, the system might silently exceed RAM limits or run too long, failing the deployment constraint. |
| **Within-Sequence Counterfactual** | Required for causal inference (SC-004). | A simple A/B test of different seeds conflates generative variance with the intervention effect. |

## Methodology & Execution Order

### 0. Pre-Experiment: CV Calibration & Feasibility Check
- **Feasibility Check**: Verify that the **StyleGAN2-ADA surrogate** supports dynamic prompt re-conditioning (required for correction tokens). If not, abort experiment (Scientific Soundness Concern).
- **CV Calibration**: Run the CV pipeline on a **Calibration Set** (50 frames) where the Symbolic Ground Truth is known.
  - Measure systematic biases (e.g., false negatives for specific object types).
  - Compute **Bias Correction Factors** to adjust the "Safety Filter" thresholds.
  - **Gate**: If calibration accuracy < 85%, the experiment is "Inconclusive" (SC-006).

### 1. Baseline Semantic Drift Quantification (US-1)
- **Symbolic Engine**: A deterministic Python class that tracks object states (HP, existence, position) based on a sequence of discrete user actions (e.g., "hit", "summon").
  - **Immutability Verification**: The symbolic state log is hashed at the end of the run. This hash is compared against a pre-computed "canonical hash" (derived from the action sequence and seed) to prove no drift occurred in the engine itself.
- **Visual Analysis**: 
  - *Static Objects*: Template matching (OpenCV `matchTemplate`) to detect object presence.
  - *Motion*: Optical flow (OpenCV `calcOpticalFlowPyrLK`) to track movement.
- **Drift Score**: Calculated as the normalized difference between the symbolic state vector and the visual state vector over time.
  - **Deconvolution Formula**: $D_{intrinsic} = (D_{total} - \text{Expected Noise}) / (1 - \text{Noise Bias})$, where Expected Noise is calculated from the CV confusion matrix (TP, FP, FN rates) measured against the **Symbolic Ground Truth** (not human observation). This correctly scales the noise component.
- **Validation**: Ground Truth Validation (FR-007) ensures the visual analysis accuracy is ≥85% before calculating the final score. The Ground Truth is derived from the **Symbolic Engine's state log**, ensuring independence from the video generation.

### 2. Hybrid Correction Mechanism (US-2) - **Within-Sequence Counterfactual**
- **Experimental Design**: For every action sequence (Seed $S$), generate **two** video streams:
  - **Stream A (Baseline)**: Identical latent noise as Stream B, but **NO** correction tokens injected.
  - **Stream B (Hybrid)**: Identical latent noise as Stream A, but **deterministic** correction token injection (p=1.0) upon discrepancy detection.
- **Correction Logic**:
  - If CV detects a discrepancy (Visual State != Symbolic State) AND **Bias-Corrected Confidence** > Threshold, inject the correction token into Stream B.
  - **Safety Filter**: Uses bias-corrected confidence from Phase 0 to avoid amplifying systematic CV errors.
- **Statistical Test**: A **Paired T-Test** compares the drift scores of Stream A vs. Stream B for each seed.
  - Null Hypothesis ($H_0$): Mean difference (Drift_B - Drift_A) = 0.
  - Alternative Hypothesis ($H_1$): Mean difference < 0 (Hybrid reduces drift).
  - Significance Level: $\alpha = 0.05$.
  - **FR-006 Compliance**: Explicitly perform this test and report the p-value.
  - **SC-004 Compliance**: Success is defined as p < 0.05.

### 3. Resource Constraint Verification (US-3)
- **Monitoring**: `psutil` will log peak RAM and wall-clock time for each sequence (both Stream A and B).
- **Thresholds**: 
  - Time ≤ 30 minutes (total for both streams).
  - RAM ≤ 7 GB.
- **Failure Mode**: If constraints are exceeded, the run is aborted and flagged as "Non-Compliant."
- **FR-005 Compliance**: Resource logs are generated per-sequence in JSON format at `data/results/resource_logs/{seed}_stream_{A,B}.json`.

### 4. Ground Truth Validation (FR-007)
- **Process**: The **Symbolic Engine** generates the "Ground Truth" state log for ≥50 frames. The CV pipeline is then run on the corresponding video frames.
- **Validation Logic**: Calculate CV accuracy (TP, FP, FN) against the **Symbolic Engine's state** (not human observation of the video).
- **Invalidation**: If accuracy < 85%, the drift score for that sequence is flagged as invalid, and the *entire experiment* is deemed "inconclusive" (SC-006). No statistical comparison is performed.
- **SC-006 Compliance**: Explicitly define the "inconclusive" outcome and its handling.

### 5. Success Criteria Mapping
- **SC-001**: Mean Semantic Drift Score for hybrid must be at least 30% lower than baseline.
- **SC-002**: Wall-clock time ≤ 30 minutes.
- **SC-003**: Peak memory ≤ 7 GB.
- **SC-004**: p-value < 0.05 (Paired T-Test on Stream A vs B).
- **SC-005**: Reduction in permanence violations ≥ 25%. This metric is explicitly calculated and reported.
- **SC-006**: Ground Truth Validation accuracy ≥ 85%.

### Dependencies & Execution Order
1. **T008**: Generate Ground Truth Subset (Symbolic Engine state logs for 50 frames). **[S]**
2. **T014**: Implement Ground Truth Validation Logic (Calculate accuracy from Symbolic GT). **[S]**
3. **T015**: Run Ground Truth Validation (Check if accuracy ≥ 85%). **[S]**
   - *Gate*: If T015 fails, stop and report "Inconclusive".
4. **T009 (New)**: Run CV Calibration (Measure systematic biases). **[S]**
5. **T010 (New)**: Verify Surrogate Architecture (Check prompt re-conditioning support). **[S]**
   - *Gate*: If T010 fails, stop and report "Infeasible".
6. **T016**: Calculate Drift Score (Baseline and Hybrid). **[S]**
7. **T017**: Run Baseline Stream A (Deterministic, p=0). **[S]**
8. **T022**: Run Hybrid Stream B (Deterministic, p=1, same seed as A). **[S]**
9. **T023**: Statistical Analysis (Paired T-Test on T017 and T022 results). **[S]**
   - *Dependencies*: T017, T022.

## Power Analysis & Sensitivity

- **Sample Size**: N=10 seeds (Feasibility Study).
- **Effect Size**: Assuming a **Large Effect Size** (d=0.8) as per SC-001 ([deferred] reduction).
- **Sensitivity Analysis**: With N=10, the study has [deferred] power to detect an effect size of d ≈ 0.85. If the actual drift reduction is smaller (e.g., 10-15%), the study is **underpowered**. The plan explicitly acknowledges this limitation and will report the result as "inconclusive" if the effect size is not detected, rather than claiming a negative result.
- **Null Result Hypothesis**: The plan explicitly acknowledges that the frozen surrogate model may ignore the correction tokens. A null result is a valid finding (the method does not work for frozen models).

## Compute Feasibility (CPU-First)

- **Model**: A CPU-tractable surrogate model (StyleGAN2-ADA 256x256, 8-bit quantized) is used for generation. The original AlayaWorld is not CPU-tractable.
- **CV Primitives**: OpenCV operations are highly optimized for CPU and will run efficiently within the 7 GB RAM limit.
- **GPU Escape Hatch**: Not applicable. The research question explicitly targets CPU-tractable solutions.

## Decision/Rationale

- **Method Choice**: Classical computer vision (template matching, optical flow) is chosen over deep learning-based object detection to ensure CPU feasibility.
- **Dataset Strategy**: AlayaWorld data is expected as local artifacts with SHA-256 checksums. If unavailable, the project is paused (not substituted). The **StyleGAN2-ADA** surrogate is the verified model for this study.
- **Statistical Approach**: **Within-Sequence Counterfactual Design** (Stream A vs Stream B) with Paired T-Test is chosen to isolate the causal effect of the correction token. This resolves the causal inference contradiction by controlling for generative variance.
- **Ground Truth Independence**: Ground Truth is derived from the **Symbolic Engine's state**, not human observation of the video, to ensure the CV pipeline measures the video's content independently of the video's drift.
- **Theoretical Distinction**: "Semantic Drift" is defined as the deviation of the visual output from the *logical* ground truth (Symbolic Engine). "Model Hallucination" is a subset of this where the model generates states not supported by the input actions. This distinction prevents conflation of 'training recall failure' with 'logic failure'.
- **CV Calibration**: Systematic CV biases are measured and corrected before the main experiment to prevent the correction mechanism from amplifying noise.
