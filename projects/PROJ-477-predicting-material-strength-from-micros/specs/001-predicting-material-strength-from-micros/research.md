# Research: Predicting Material Strength from Microstructure Images

## Overview

This research investigates whether 2D Electron Backscatter Diffraction (EBSD) microstructure images contain sufficient morphological signal to predict macroscopic yield strength using a lightweight Convolutional Neural Network (CNN). The study compares a MobileNetV2-based model against a naive statistical baseline (mean predictor) to determine if image features provide superior predictive power.

## Dataset Strategy

### Primary Dataset
*   **Name**: Synthetic EBSD Microstructures
*   **Source**: HuggingFace `Rxzh/ebsd-synthetic`
*   **URL**: `https://huggingface.co/datasets/Rxzh/ebsd-synthetic/resolve/main/data_synth_ebsd.zip`
*   **Verification**: This URL is explicitly listed in the project's "Verified datasets" block. It is a direct download (zip) suitable for unattended CI execution.
*   **Content**: Paired 2D EBSD images and corresponding yield strength values.
*   **Size**: Approximately 2,697 images (verified source: arXiv:2506.09162).
*   **Fit**: The dataset contains the required variables: `image` (2D map) and `yield_strength` (scalar). No variable mismatch detected.

### Data Processing Strategy
1.  **Download & Integrity**: Fetch via `requests` or `wget`. Verify checksum against the hash recorded in `state/...yaml`.
2. **Streaming**: Due to the [deferred] image count, the full dataset fits in RAM. No streaming is strictly required, but the loader will use `torch.utils.data.Dataset` with on-the-fly loading to minimize peak memory.
3. **Splitting**: Stratified split ([deferred] train, [deferred] val, [deferred] test) based on yield strength bins to ensure distributional parity.
4.  **Preprocessing**:
    *   Resize: 224x224 pixels (FR-001).
    *   Normalization: Mean/Std of ImageNet (standard for transfer learning).
    *   Format: Convert to 8-bit if necessary; reject non-standard formats.

### Dataset Feasibility Check
*   **Constraint**: GitHub Actions free tier (7GB RAM).
* **Assessment**: [deferred] images at 224x224x3 (float32) [deferred] * 150KB ≈ 405MB. Even with augmentation buffers, this is well within the 7GB limit.
*   **Conclusion**: Dataset is fully feasible for CPU-only execution.

## Methodology & Statistical Rigor

### Model Architecture
*   **Backbone**: MobileNetV2 (pre-trained on ImageNet).
*   **Freezing**: All backbone layers frozen; only the final classification head (replaced with a linear regression layer) is trainable.
*   **Rationale**: Reduces trainable parameters significantly, preventing overfitting on a small dataset and enabling CPU training.
*   **Alternative**: ResNet-18 considered, but MobileNetV2 is more parameter-efficient for this scale.

### Baseline Comparison
*   **Null Hypothesis**: Image features provide no predictive signal beyond the global mean.
*   **Baseline Model**: Constant predictor returning the mean yield strength of the training set.
*   **Metric**: MSE and R².

### Statistical Testing
*   **Test**: Single-sample t-test.
*   **Variable**: Squared errors of the CNN model vs. squared errors of the baseline.
*   **Hypothesis**: $H_1$: Mean squared error (CNN) < Mean squared error (Baseline).
*   **Significance Level**: α = 0.05.
*   **Correction**: No multiple comparison correction needed for the primary hypothesis (single test).

### Interpretability & Sensitivity
*   **Method**: Grad-CAM (Gradient-weighted Class Activation Mapping).
*   **Goal**: Visualize regions of the microstructure (grain boundaries, phases) driving the prediction.
*   **Validation**: IoU calculation against manual annotations (if available) or expert review (SC-005).
*   **Sensitivity**: Threshold sweep around the median predicted strength to assess classification robustness (FR-007).

## Compute Feasibility & Escape Hatch

### CPU-First Strategy
*   **Model**: MobileNetV2 (frozen) + 1-layer head.
*   **Batch Size**: 16 (tuned to fit 7GB RAM).
*   **Epochs**: Max 50.
*   **Time Estimate**: ~2-3 hours on 2 vCPU.
*   **Decision**: This method is fully CPU-tractable. No GPU escape hatch is required.

### GPU Escape Hatch (Not Needed)
*   **Condition**: If the dataset size were >100k images or if a larger model (e.g., ResNet-50 full fine-tune) were required.
*   **Plan**: If triggered, offload to Kaggle GPU (16GB VRAM) with a smaller batch size or quantization.
*   **Current Status**: Not applicable.

## Addressing Unresolved Concerns

1.  **T042 (Validation Report)**: The `code/utils/validation.py` script will be implemented to explicitly write `results/validation_report.json` containing the count of valid/invalid pairs and the invalid ratio. The script will exit with code 1 if the ratio > 1%.
2.  **T030 (Annotation Fallback)**: The interpretability pipeline will check for manual annotations. If missing, it will proceed to generate Grad-CAM heatmaps and output a "Expert Review Required" flag in the report, rather than raising a fatal error, satisfying SC-005's fallback path.
3.  **T032 (Confidence Intervals)**: Confidence intervals will be calculated using the residual distribution from the **validation set** (not test set) to avoid data leakage, applied as a post-hoc correction to test set predictions.
4.  **T005 (Batch Loading)**: A custom `BatchLoader` class will be implemented in `code/data/loader.py` to handle on-the-fly augmentation and memory management, preventing OOM errors.
5.  **Fabricated Metrics**: All metrics (MSE, R², t-stat) will be computed dynamically from the actual model outputs. No hardcoded values will be used.
