# Research: llmXive Follow-up: Extending "Enhancing Train-Free Infinite-Frame Generation for Consistent Long Vid"

## Research Question

To what extent can a deterministic 2D optical flow correction (Condition C) *mitigate* temporal inconsistency in train-free infinite-frame generation compared to the naive baseline (Condition B), and what are the specific boundaries (e.g., 3D rotation, depth changes) where 2D priors fail to hide structural drift?

**Note on Causality**: This is an experimental design (manipulating the algorithm on the same prompts). The analysis will support causal claims about the *method's* effect (Condition C vs B), while explicitly acknowledging that the metrics are 2D proxies for 3D truth.

## Dataset Strategy

The project utilizes the **VBench** benchmark suite, accessed via the canonical HuggingFace repository `kmhh/vbench`. The MIGA pipeline is a *method* applied to this standard benchmark data. The data strategy involves downloading a sampled subset of video prompts and ground-truth sequences to ensure computational feasibility within the 6-hour CI window.

**Within-Subjects Design**: The same N=50 prompts are used for Conditions A, B, and C to ensure a paired comparison and eliminate content difficulty as a confound.

| Dataset | Source (Verified URL) | Usage in Project | Loading Strategy |
|---------|-----------------------|------------------|------------------|
| **VBench (VideoCrafter-1)** | `https://huggingface.co/datasets/kmhh/vbench` (Subset: `videocrafter-1`) | Prompts and ground-truth sequences for Condition A/B generation. | `datasets.load_dataset("kmhh/vbench", "videocrafter-1")` with checksum verification. |
| **VBench (CausVid)** | `https://huggingface.co/datasets/kmhh/vbench` (Subset: `causvid`) | Additional test cases for temporal consistency evaluation. | `datasets.load_dataset("kmhh/vbench", "causvid")`. |
| **VBench (MMR)** | `https://huggingface.co/datasets/kmhh/vbench` (Subset: `mmr`) | Metadata and prompt alignment for evaluation. | `datasets.load_dataset("kmhh/vbench", "mmr")`. |

**Sampling Strategy**: To fit the 7GB RAM and 6-hour runtime constraints, the project will sample **N=50** video prompts from the combined dataset sources. This sample size is targeted for statistical power analysis (SC-006) to detect a medium effect size (Cohen's d = 0.5), *after* a pilot study estimates empirical variance.

**Dataset Fit Verification**:
- **Predictors**: Prompt text, frame count, resolution. (Present in Parquet sources).
- **Outcomes**: Temporal consistency (VBench), Object Permanence, FVD. (Calculated by evaluation models).
- **Covariates**: Motion magnitude (estimated via flow magnitude), scene complexity.
- **Gap Check**: The datasets provide video sequences and prompts. The project does **not** require 3D ground truth (e.g., depth maps) for the primary evaluation, as the hypothesis is about 2D perceptual proxies. The "3D drift" analysis (US-3, SC-003) is performed via **failure mode detection** (object permanence drop) and qualitative review, acknowledging that 2D metrics cannot prove 3D geometric correctness.

## Methodology & Technical Approach

### Phase 0: Pilot Study (Power Analysis)
1.  **Execute**: Run a small pilot (N=5) for Conditions A, B, and C.
2.  **Estimate Variance**: Calculate the empirical variance of FVD and VBench scores on the CPU pipeline.
3.  **Power Check**: Use `statsmodels.stats.power` to confirm if N=50 provides power ≥ 0.8 for the observed effect size. If power < 0.8, the final report will explicitly state this limitation.

### Phase 1: Baseline Generation (Conditions A & B)
1.  **Data Loading**: Fetch and verify checksums for the sampled N=50 prompts from the verified HuggingFace sources.
2.  **MIGA Execution**:
    -   **Condition A (Baseline-Full)**: Run MIGA with `--mode baseline-full` (self-reflection enabled). Record wall-clock time.
    -   **Condition B (Baseline-Naive)**: Run MIGA with `--mode baseline-naive` (self-reflection disabled). Record wall-clock time.
    -   **Constraint**: Ensure `torch` is loaded in CPU mode; no CUDA device assignment.

### Phase 2: Flow-Based Correction (Condition C)
1.  **Optical Flow Estimation**:
    -   Load **RAFT-Small** model (pre-trained weights, FP16 precision).
    -   Compute flow fields between consecutive frames of Condition B videos.
    -   **CPU Feasibility**: RAFT-Small is selected for its lightweight architecture. FP16 precision is used to reduce memory footprint.
    -   **Fallback**: If flow estimation fails (e.g., extreme blur), fallback to nearest-neighbor interpolation of flow vectors (Edge Case 1).
2.  **Warping & Smoothing**:
    -   **Target**: Warp Condition B frames *forward* to align with the *previous* frame's position (temporal back-projection) to enforce consistency. The first frame serves as the anchor.
    -   **Operation**: Apply non-differentiable warping and temporal smoothing.
    -   **Conceptual Limitation**: This is a 2D smoothing operation. It cannot reconstruct missing 3D data (e.g., an object that has rotated out of view). It aims to *mitigate* perceptual flicker, not *correct* 3D geometry.
    -   **Artifact Detection**: Flag frames with invalid pixel artifacts (tearing) for manual review (Edge Case 2).

### Phase 3: Evaluation & Statistical Analysis
1.  **Metric Calculation**:
    -   Compute **VBench Temporal Consistency**, **Object Permanence**, and **FVD** for all three conditions (A, B, C).
    -   Use pre-trained evaluation models (independent of the generator).
2.  **Statistical Testing**:
    -   **Normality Check**: Perform Shapiro-Wilk test on the differences (A-C) and (B-C).
    -   **Significance Test**:
        -   If normality accepted (p ≥ 0.05): Paired t-test.
        -   If normality rejected (p < 0.05): Wilcoxon signed-rank test.
    -   **Threshold**: p < 0.05 for significance (Bonferroni corrected for multiple comparisons).
3.  **Failure Analysis**:
    -   Identify videos where Object Permanence drops ≥ 5% or VBench consistency drops ≥ 0.1 (Condition C vs B).
    -   **Qualitative 3D Review**: For failure cases, perform a qualitative review to identify "3D geometric collapse" (e.g., object flattening) that the 2D proxy failed to hide. Log these as "2D Flow Failure Cases" (FR-007).

## Statistical Rigor & Power Analysis

-   **Multiple Comparisons**: As we are comparing three conditions, we will apply a **Bonferroni correction** to the significance threshold (α = 0.05 / 3 ≈ 0.017) for pairwise comparisons to control family-wise error rate.
-   **Power Analysis**:
    -   **Target**: N=50 samples (subject to pilot validation).
    -   **Effect Size**: Medium (Cohen's d = 0.5).
    -   **Variance**: Estimated empirically from the Phase 0 pilot study to ensure accuracy.
    -   **Limitation**: If the calculated power is < 0.8, the final report will explicitly state this as a limitation of the study rather than claiming definitive significance.
-   **Causal Inference**: This is an **experimental** design (paired comparison of algorithmic conditions). Claims will be framed as "causal effects of the method" (Condition C vs B), with the caveat that the metrics are 2D proxies for 3D truth.
-   **Collinearity**: The predictors (motion magnitude, scene complexity) may be correlated. The analysis will report descriptive statistics of these correlations and acknowledge that independent effects cannot be fully disentangled without a designed experiment.

## Decision Rationale & Constraints

-   **Why RAFT-Small?** It is the smallest viable variant of the RAFT family, balancing accuracy and CPU inference time. Larger variants (RAFT-Large) would likely exceed the 6-hour runtime on 2 cores.
- **Why FP16?** Reduces model memory footprint by [deferred], crucial for the 7GB RAM limit on the CI runner.
-   **Why N=50?** A balance between statistical power and the strict 6-hour runtime limit. Generating 50 videos with full self-reflection (Condition A) is computationally expensive; increasing N would risk timeout.
-   **Why 2D Proxies for 3D Drift?** Direct 3D ground truth is not available in the verified datasets. The project uses **Object Permanence** and **Temporal Consistency** as proxies, with explicit caveats (FR-007) that they do not guarantee 3D geometric correctness. The "3D drift" analysis is a failure mode detection task, not a 3D reconstruction task.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Runtime Exceeds 6 Hours** | High | Use N=50 (validated by pilot); optimize loop logic; use `--mode baseline-naive` for Condition C generation (faster than A). |
| **RAM Overflow (7GB)** | High | Process videos in batches; unload models between steps; use FP16; limit `torch` threads. |
| **Flow Estimation Failure** | Medium | Implement nearest-neighbor fallback (Edge Case 1); log errors without crashing. |
| **Dataset Download Failure** | High | Abort with clear error message listing missing files (Edge Case 3); verify checksums immediately. |
| **Statistical Power < 0.8** | Medium | Use Phase 0 pilot to estimate variance; report power limitation explicitly if N=50 is insufficient. |
| **2D Flow Cannot Fix 3D** | Medium | Explicitly frame hypothesis as "mitigation of flicker" not "correction of drift"; qualitative review of 3D collapse. |