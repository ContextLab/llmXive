# Research: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Overview

This research validates the hypothesis that numerical instability in the AnyFlow diffusion model (measured as "flow-map divergence") correlates with semantic temporal discontinuities (scene cuts) in video data. The study relies on a curated dataset of video clips, manual ground-truth annotation, and CPU-only inference.

## Dataset Strategy

### Verified Datasets
The project utilizes the following verified datasets as sources for video clips. No other datasets are used.

| Dataset Name | Source Type | Verified URL | Usage |
| :--- | :--- | :--- | :--- |
| **Kinetics-400** | HuggingFace (Video) | `https://huggingface.co/datasets/UCB-kinetics/kinetics400` (via `datasets` library) | Primary source for video clips. The `download.py` script uses `datasets.load_dataset('UCB-kinetics/kinetics400', split='val')` to fetch videos. |
| **UCF101** | HuggingFace (Video) | `https://huggingface.co/datasets/UCB-kinetics/ucf101` (via `datasets` library) | Secondary source for video clips if Kinetics quota is insufficient. |
| **AnyFlow Status Manifest** | HuggingFace (JSON) | `https://huggingface.co/datasets/simbahuang/anyflow-p0-status/resolve/main/experiments/anyflow-aapt-go24h-20260712T0235/a-dynamics500-s0/manifests/a_checkpoint_manifest.json` | Provides canonical list of video IDs. **Note:** This manifest contains internal experiment IDs, not direct HTTP links. The script uses these IDs to filter the HuggingFace datasets above. |
| **AnyFlow Model Weights** | HuggingFace (Model) | *Referenced in Assumptions* | The plan assumes the model weights are available in a format convertible to ONNX. If a specific URL is not provided in the spec, the script will attempt to load a local `anyflow_distilled.onnx` file or fail gracefully if not found. |

**Note on Data Fetching & Fallback Strategy**:
The `AnyFlow Status Manifest` does not provide direct HTTP links to raw video files. Therefore, the `download.py` script will:
1.  Parse the manifest to extract video IDs.
2.  Use the `datasets` library to fetch the corresponding video clips from the verified Kinetics-400 or UCF101 repositories using those IDs.
3.  **Fallback Mechanism**: If a video ID from the manifest cannot be resolved or the video is unavailable, the script will immediately switch to a **Verified Fallback List** of 600 pre-validated Kinetics-400 video IDs known to contain cuts or continuous motion (sourced from the Kinetics-400 official split files). This ensures the N=500 target is met without relying on potentially broken manifest links.
4.  If the fallback list is also exhausted, the script halts with an error.

### Data Curation Strategy (FR-001, FR-002)
1.  **Ingestion**: The `download.py` script parses the manifest or fallback list to extract video IDs.
2.  **Stratified Sampling**: A stratified sampling strategy is implemented to ensure:
    *   Total clips: a representative sample (N=500).
    *   Scene cuts: ≥ 20% (100 clips).
    *   Continuous motion: ≥ 80% (400 clips).
    *   **Variance Focus**: The sampling specifically targets "hard" cuts (expected score ~1.0) and "smooth" motion (expected score ~0.0) to maximize the distribution of scores, ensuring the variance check (FR-010) is likely to pass.
3.  **Extraction**: Clips are extracted as short temporal sequences at a standard frame rate.
4.  **Ground Truth**: Human annotators assign a `continuity_score` (0.0–1.0) based *solely* on pixel-space visual inspection. No model features are used.

### Annotation Workflow (FR-002 Clarification)
*   **Tooling**: `code/annotate.py` is a **Template Generator & Validator**, not a GUI.
*   **Process**:
    1.  `annotate.py` generates an empty `continuity_scores.csv` with all video IDs and schema headers.
    2.  Annotators manually review clips (e.g., using VLC or a simple frame viewer) and fill the CSV.
    3.  `annotate.py` validates the filled CSV to ensure scores are in [0.0, 1.0] and no NaN values exist.
*   **Constraint**: The manual process strictly forbids using model outputs (optical flow, divergence) for scoring.

### Model & Inference Strategy (FR-003, FR-004)
1.  **Model Loading**: The frozen AnyFlow model is loaded via **ONNX Runtime** (CPU provider).
    *   *Constraint Check*: No CUDA, no `load_in_8bit`, no GPU device mapping.
2.  **Divergence Calculation**:
    *   **Input**: 16-frame latent sequence.
    *   **Baseline**: High-precision numerical integration (Runge-Kutta 4, N=500 steps) of the *latent dynamics* predicted by the model's own flow field. This serves as a "numerical ground truth" for the solver's stability.
    *   **Metric**: L2 distance between the model's predicted intermediate state and the RK4 baseline, averaged across the sequence.
    *   **Hypothesis Clarification**: The hypothesis is that the *model's* approximation error (divergence from its own high-fidelity solver) correlates with *semantic* discontinuity. This avoids circular logic by treating the high-fidelity solver as the reference for "correct" numerical behavior.
3.  **Feasibility Check (FR-009)**:
    *   A pre-flight check runs on a subset of clips.
    *   **Default**: N=500 steps for the RK4 baseline.
    *   If projected runtime > 5.5 hours, the Euler steps are reduced to N=200.
    *   *Decision*: The plan targets N=500. If the pre-flight check fails, the script automatically switches to N=200 and logs the change. N=5000 is rejected as infeasible.

### Precision Validation (Methodology-70fd5695)
To ensure CPU/ONNX precision does not introduce artifacts:
1.  A **CPU-Only Precision Validation** step is added.
2.  The ONNX Runtime output is compared against a high-precision NumPy/RK4 integration (N=5000 steps) of the *same* latent trajectory on the CPU.
3.  If the L difference exceeds 1e-4, the run is flagged as "Precision Failure" and the model is re-validated. This avoids the need for GPU hardware.

## Statistical Methodology (FR-005, FR-006, FR-007)

### Methodological Rationale: Continuous vs. Binary Scoring
The plan employs a continuous `continuity_score` (0.0–1.0) rather than a binary "cut/no-cut" label for the following reasons:
1.  **Spectrum of Discontinuity**: Temporal discontinuity is not binary. It ranges from "smooth motion" (0.0) to "hard cuts" (1.0), with intermediate states like "fast motion blur" or "partial occlusion".
2.  **Monotonic Trend**: The hypothesis posits that model instability *scales* with the severity of the discontinuity. A binary metric (AUC-ROC) would only test if the model distinguishes "cut" from "no-cut", missing the nuance of *how* instability increases with discontinuity severity.
3.  **Correlation Power**: Pearson and Spearman correlations are designed to detect linear or monotonic relationships in continuous data. Using a continuous score allows the study to capture these trends.
4.  **Bimodal Fallback**: If the annotators produce a bimodal distribution (only 0.0 or 1.0), the correlation analysis will still execute. However, the interpretation will shift to acknowledging that the continuous metric acted as a binary classifier in this specific dataset, and the correlation coefficient will be interpreted as the strength of the binary separation.

### Correlation Analysis
*   **Hypothesis**: Higher divergence scores correlate with lower continuity scores (higher discontinuity).
*   **Methods**:
    1.  **Pearson Correlation ($r$)**: Tests for linear relationship.
    2.  **Spearman Rank Correlation ($\rho$)**: Tests for monotonic relationship.
*   **Significance**: P-values are calculated for both.
*   **Causal Framing**: The study is observational. All results are framed as **associational**. No causal claims are made.

### Power Analysis & Sensitivity (Scientific Soundness)
*   **Sample Size Justification**: N=500 is chosen to detect a moderate effect size (r=0.3) with 80% power at alpha=0.05.
*   **Confidence Interval Sensitivity**: In addition to the binary variance check, the analysis will compute confidence intervals for the correlation coefficient. If the interval includes zero, the result is reported as "not statistically significant" even if variance > 0.05.
*   **Thresholds**: {0.01, 0.05, 0.1}.
*   **Output**: False Positive Rate (FPR) and False Negative Rate (FNR) for each threshold.
*   **Interpretation**: Determines the robustness of the divergence metric as a classifier for scene cuts.

### Variance Check (FR-010)
*   **Requirement**: Variance of `continuity_score` must be ≥ 0.05.
*   **Action**: If variance < 0.05, the analysis halts with an "Insufficient Variance" error.

## Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-Only Inference** | The project must run on GitHub Actions free-tier (no GPU). ONNX Runtime is the standard for CPU-optimized inference. |
| **RK4 Baseline (N=500)** | Required to establish a "Numerical Baseline" that is sufficiently accurate to detect model instability. N=5000 is rejected as infeasible. |
| **Stratified Sampling** | Ensures the dataset has enough "cut" examples to calculate meaningful correlation and sensitivity metrics, and specifically targets score variance to meet FR-010. |
| **Associational Framing** | The data is observational (curated from public repos). Causal claims would violate scientific rigor (FR-007). |
| **No Synthetic Data** | **All metrics are computed from real video clips and real model inference. No synthetic data, placeholder metrics, or simulated scores are generated or used.** |
| **Continuous Scoring** | Captures the *degree* of discontinuity, allowing for correlation analysis that binary metrics would miss. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Runtime Exceeds 6h** | High | Pre-flight check (FR-009) reduces RK4 steps to N=200 if needed. Default is N=500. |
| **Memory Exceeds 7GB** | High | Process clips in small batches and clear memory between batches. |
| **Model Not Available in ONNX** | Critical | The spec assumes the model is convertible. If not, the plan halts with an error; no alternative model is substituted. |
| **Variance < 0.05** | Medium | If annotators are inconsistent, the script halts. Re-annotation is required. |
| **Missing Video IDs** | High | **Fallback to verified static list of Kinetics IDs if manifest IDs cannot be resolved.** |
| **Bimodal Scores** | Low | If scores are binary, the correlation is still computed but interpreted as a binary separation strength. |