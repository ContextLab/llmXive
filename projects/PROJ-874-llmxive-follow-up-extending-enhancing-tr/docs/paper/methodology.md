# Methodology: Enhancing Train-Free Infinite-Frame Generation for Consistent Long Video

## Abstract

This document outlines the methodology for the llmXive follow-up study, which extends the "Train-Free Infinite-Frame Generation" approach to address temporal inconsistency and 3D drift in long-form video synthesis. We propose a two-stage pipeline: (1) a baseline generation phase utilizing a Large Language Model (LLM) for frame prediction with and without self-reflection, and (2) a deterministic flow-based correction phase using RAFT-Small optical flow to enforce temporal coherence without additional training.

## 1. Introduction

Generating consistent long-form videos from text prompts remains a challenge for diffusion and autoregressive models, often suffering from temporal flickering and object drift. Existing train-free methods attempt to mitigate this via prompt engineering and self-reflection loops. This study evaluates the efficacy of such methods and introduces a post-hoc correction mechanism based on classical computer vision (optical flow) to further stabilize the output.

Our approach is strictly train-free, relying on pre-trained LLMs for generation and pre-trained optical flow models for correction, ensuring reproducibility on CPU-only infrastructure.

## 2. Dataset and Experimental Setup

### 2.1 Datasets
We utilize two benchmark datasets for evaluation:
- **NarrLV**: A dataset of narrated long-form video clips used for generating consistent sequences.
- **VBench**: A comprehensive benchmark suite for evaluating video generation quality, used here for metric computation.

Data is downloaded programmatically via the HuggingFace `datasets` library. All downloads are validated via checksums to ensure integrity.

### 2.2 Hardware Constraints
Experiments are conducted under strict CPU-only constraints to ensure accessibility and reproducibility:
- **Compute**: 2-core CPU limit.
- **Memory**: Peak RAM usage constrained to < 6GB.
- **Precision**: Optical flow inference defaults to FP32 if FP16 causes OOM, as determined by a pre-flight benchmark.

## 3. Methodology

The pipeline consists of three primary stages: Baseline Generation, Flow-Based Correction, and Quantitative Analysis.

### 3.1 Stage 1: Baseline Generation

We generate initial video sequences using a pre-trained LLM in two distinct modes to establish a performance baseline:

1. **Naive Baseline (`--mode baseline-naive`)**: The LLM generates frames sequentially based solely on the text prompt and previous frame context, without explicit consistency checks.
2. **Full Self-Reflection (`--mode baseline-full`)**: The LLM employs a self-reflection loop where generated frames are critiqued against the prompt and temporal consistency criteria before finalization.

**Implementation Details**:
- Frame generation is handled by `code/generate.py`.
- Wall-clock time is recorded for each video to measure efficiency overhead introduced by self-reflection.
- A pilot study (`code/pilot_study.py`) is conducted on N=5 samples to estimate variance for subsequent power analysis.

### 3.2 Stage 2: Deterministic Flow-Based Correction

To address temporal inconsistencies and 3D drift observed in the naive baseline, we apply a non-differentiable correction pipeline. This stage does not update model weights but uses classical warping techniques.

**Algorithm**:
1. **Flow Estimation**: We compute optical flow fields between consecutive frames of the baseline video using the RAFT-Small model (`code/utils/flow.py`).
 - *Precision Handling*: A benchmark (`code/utils/flow_benchmark.py`) determines if FP16 inference is feasible on the target CPU. If not, the system falls back to FP32.
 - *Fallback*: For frames with invalid flow (e.g., severe motion blur), a nearest-neighbor interpolation of flow vectors is applied.
2. **Warping and Smoothing**: The estimated flow fields are used to warp frames to a common reference time, smoothing temporal transitions.
3. **Artifact Detection**: A scan for tearing artifacts (`code/utils/artifact_detector.py`) flags frames with severe 3D drift for manual review.

**Implementation**:
- Executed via `code/correct.py`.
- Outputs: Warped videos and flow field visualizations.

### 3.3 Stage 3: Evaluation and Statistical Analysis

We evaluate the generated videos using a suite of metrics and perform rigorous statistical testing.

**Metrics**:
- **VBench Score**: Overall video quality assessment.
- **FVD (Fréchet Video Distance)**: Distributional similarity to real video data.
- **Object Permanence**: A custom metric tracking object consistency across frames.

**Statistical Protocol**:
1. **Power Analysis**: Using the pilot variance from Stage 1, we calculate the statistical power for N=50 samples. If power < 0.8, the study is flagged as underpowered, and subsequent parametric tests are aborted or flagged as invalid (`code/analyze.py`).
2. **Normality Test**: Shapiro-Wilk test is performed on the difference metrics (Corrected vs. Naive).
 - *Null Hypothesis*: Data is normally distributed.
 - *Decision*: p < 0.05 implies non-normality.
3. **Adaptive Testing**:
 - If normality is rejected (p < 0.05): Wilcoxon signed-rank test is used.
 - If normality is not rejected: Paired t-test is used.
4. **Failure Case Identification**: Videos where Object Permanence drops ≥5% or VBench score drops ≥0.1 compared to the baseline are flagged as failure cases.

## 4. Results and Reporting

All results are aggregated into a single CSV report (`results/metrics_report.csv`) containing:
- Video ID and Condition (Naive vs. Corrected)
- Metric scores (VBench, FVD, Object Permanence)
- Statistical results (p-value, test type)
- Power sufficiency flag

Failure cases are logged in `results/failure_cases.json` with explicit notes that these are 2D perceptual proxies and do not guarantee 3D geometric correctness.

## 5. Reproducibility

To reproduce this study:
1. Ensure the environment meets CPU and RAM constraints.
2. Run `code/download.py` to fetch NarrLV and VBench datasets.
3. Execute `code/generate.py` for baselines.
4. Run `code/correct.py` for flow correction.
5. Execute `code/analyze.py` for statistical validation.

All code is modular, with strict API contracts defined in `contracts/` and configuration managed via `code/config.py`.

## 6. Conclusion

This methodology provides a rigorous, train-free framework for enhancing long-form video consistency. By combining LLM-based self-reflection with deterministic optical flow correction, we aim to significantly reduce temporal artifacts while maintaining computational feasibility on standard CPU hardware.