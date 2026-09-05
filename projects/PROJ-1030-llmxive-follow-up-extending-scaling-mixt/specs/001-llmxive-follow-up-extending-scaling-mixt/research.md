# Research: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

## Executive Summary

This research investigates whether the internal latent representations of video models (specifically MoE architectures, with a ViT fallback) encode physical laws governing embodied intelligence. By extracting expert activation masks and latent vectors from intermediate DiT/ViT layers and correlating them with independent ground-truth labels generated via 3D reconstruction (with kinematic checks) and physics simulation, we aim to determine if specific sub-networks are consistently predictive of physical validity (e.g., collision, gravity violation).

## Dataset Strategy

The project relies on verified, open datasets for robot manipulation. The strategy prioritizes programmatic access to ensure reproducibility on CI runners.

| Dataset Role | Source Name | Verified URL | Access Method | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Video Clips** | BridgeData V2 | `https://huggingface.co/datasets/rail-berkeley/bridgedata_v2` | `datasets.load_dataset(..., streaming=True)` | Contains diverse robot manipulation clips. Verified public access. |
| **Secondary Video Clips** | RoboNet (via Robomimic) | `https://huggingface.co/datasets/robomimic/robomimic` | `datasets.load_dataset(..., streaming=True)` | Fallback if BridgeData lacks specific physical scenarios. |
| **Model Weights (MoE)** | VideoMoE (or DiT-MoE) | `https://huggingface.co/[verified-moe-model]` | `transformers` | **Fallback**: If no public MoE model with accessible DiT layers is found, the pipeline defaults to **VideoMAE** (ViT) as a negative control. |
| **Model Weights (ViT)** | VideoMAE | `https://huggingface.co/MCG-NJU/videomae-base` | `transformers` | Used if MoE model is unavailable. |

**Dataset Fit Verification**:
The selected datasets contain video clips of robot interactions. The study requires variables: `video_frames` (for feature extraction), `action_context` (for 3D reconstruction).
- **Missing Variable Check**: The datasets provide video frames. The study *needs* 3D state estimates (positions, velocities) which are **not** in the dataset.
- **Resolution**: The plan explicitly includes a **3D Reconstruction Step** (US-2) using `monodepth2` (default) to derive these variables from the video frames. This is a computational transformation, not a missing data gap.

## Methodological Rigor

### Statistical Approach
1.  **Classification Task**: Binary classification (Valid vs. Invalid).
    -   **Model**: Shallow MLP or Random Forest (CPU-tractable).
    -   **Metrics**: F1-score, Precision, Recall (SC-001).
    -   **Baseline**: Random guessing (chance level).
2.  **Power & Sample Size (Dynamic)**:
    -   **Test**: Logistic Regression (to estimate odds ratios of expert activation).
    -   **Assumptions**: Effect size (Cohen's h) = 0.5 (medium), Power (1-β) = 0.8, α = 0.05.
    -   **Calculation**: The script calculates the minimum N required for these parameters.
    -   **Feasibility Constraint**: If the calculated N exceeds the available clips or the 6-hour runtime budget, the study **does not** fabricate data. Instead, it reports the **achieved power** and the **minimum detectable effect size (MDES)** for the available sample. This explicitly addresses the risk of underpowering.
3.  **Feature Importance**:
 - Method: **KernelSHAP** with a limited background sample (n=100) and a [deferred] sampling budget to handle sparsity and correlation in expert masks.
    -   Fallback: If KernelSHAP exceeds the 30-minute time limit, the script falls back to **Permutation Importance** with a strict time cap.
    -   Goal: Identify if specific MoE experts correlate with physical violations (SC-002).
4.  **Multiple Comparisons**:
    -   If testing individual expert contributions, apply **False Discovery Rate (FDR)** control (Benjamini-Hochberg) to the p-values.
5.  **Causal Claims**:
    -   **Strictly Associational**: As per FR-007, the study will frame results as correlations between latent states and physical validity. No causal claims will be made.

### Control Experiments & Interpretation
To distinguish "genuine physical understanding" from "spurious visual correlations":
1.  **Label Shuffling**: Train on shuffled labels. Expected F ≈ 0.5.
2.  **Visual Texture Baseline**: Train a classifier on raw image patches (no latent extraction). If MoE performance is not significantly better than this, the signal may be texture-based.
3.  **ViT Baseline**: Train on a non-MoE model (VideoMAE).
4.  **Decision Rule**: "Genuine physical understanding" is supported **only if**:
    -   MoE F1 > ViT F1 (p < 0.05 via McNemar's test).
    -   MoE F1 > Texture Baseline F1 (p < 0.05).
    -   MoE F1 > Chance Level.

### Dataset-Variable Fit & Limitations
-   **Variable**: `Expert Activation Mask`.
    -   **Source**: Extracted from Video Model intermediate layers.
    -   **Validity**: Directly measured.
-   **Variable**: `Physical Label` (Valid/Invalid).
    -   **Source**: Generated via PyBullet on reconstructed 3D states.
    -   **Risk**: Monocular depth estimation is noisy.
    -   **Mitigation**:
        1.  **Kinematic Consistency Check**: Before labeling, the reconstructed trajectory is checked for continuity and non-zero velocity. Samples failing this are labeled 'null'.
        2.  **Scale Normalization**: Relative depth is normalized to the first frame's bounding box and scaled by a heuristic average object size to ensure PyBullet compatibility.
        3.  **Confidence Filter**: Samples with reconstruction confidence < 0.9 are filtered out.

## Compute Feasibility & GPU Strategy

### CPU-First Strategy
The entire pipeline is designed for the GitHub Actions free-tier (limited vCPU, limited RAM, No GPU).
-   **Feature Extraction**: `torch.no_grad()` and chunking.
-   **Physics Simulation**: PyBullet is CPU-native.
-   **Classifier**: Scikit-learn (Random Forest/MLP).
-   **SHAP**: KernelSHAP with limited samples (n=100) to fit time budget.

### GPU Escape Hatch (Kaggle Auto-Offload)
If the depth estimation or model inference exceeds CPU limits:
-   **Trigger**: CUDA requirement or OOM.
-   **Action**: Re-run on Kaggle GPU with reduced sample size (first 50 clips).
-   **Note**: No synthetic stand-ins.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **monodepth2 (Default)** | Selected as the **only** supported default for reproducibility. MiDaS/Depth Anything are research-only alternatives. |
| **Kinematic Consistency Check** | Filters out samples where the *motion* is physically impossible due to reconstruction artifacts, addressing systematic errors in velocity. |
| **Prior Audit** | Checks for shared training data between video and depth models. If overlap > 50%, switches to SfM (COLMAP) to ensure independence. |
| **Relative to Rigid Translation** | Normalizes relative depth to a unit scale using heuristic object sizes, allowing PyBullet to run without absolute scale. |
| **KernelSHAP Approximation** | Balances the need for handling sparse/correlated features with the 30-minute CPU time limit. |

## Ethical & Safety Considerations
-   **Bias**: The dataset may be biased towards specific robot types. The study will acknowledge this.
-   **Safety**: No real-world robot control.
-   **Privacy**: Datasets are open-source.
