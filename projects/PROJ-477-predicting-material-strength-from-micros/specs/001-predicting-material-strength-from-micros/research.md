# Research: Predicting Material Strength from Microstructure Images

## Overview

This research phase validates the feasibility of predicting material yield strength from 2D EBSD microstructure images using lightweight CNNs on CPU-only hardware. It identifies the specific dataset strategy (synthetic generation), defines the statistical methodology, and outlines the computational strategy to meet the project's constraints.

## Dataset Strategy

### Primary Data Source: Synthetic Generation

**Dataset Name**: Physics-Informed Synthetic EBSD Dataset  
**Source**: Local Algorithm (Voronoi Tessellation + Hall-Petch Relation)  
**URL**: N/A (Generated locally via `code/data/generate.py`)  
**Content**: 2D EBSD-like maps of polycrystalline materials with associated yield strength values calculated via the Hall-Petch equation.  
**Sample Size**: N = [deferred] (Configurable via generation parameters).  
**Format**: ZIP archive containing images and a manifest (CSV) mapping filenames, specimen IDs, and strength values.

**Rationale**:
1.  **Availability**: No public real-world dataset exists with paired EBSD maps and ground-truth yield strength. A synthetic generator ensures reproducibility and control over the physical relationship.
2.  **Relevance**: The generator explicitly models the Hall-Petch relation ($ \sigma_y = \sigma_0 + k d^{-1/2} $), ensuring the target variable is physically grounded in the microstructure features (grain size).
3.  **Size**: The sample size is configurable to fit within the available CPU time and memory constraints.

### Data Labeling Strategy & Specimen Logic

**Mapping**: Many-to-One (Images to Specimen).
- **Specimen**: A single material sample with a unique global yield strength.
- **Images**: Multiple 2D EBSD maps are generated from the *same* specimen (simulating different regions of the same sample).
- **Label Assignment**: All images generated from a single specimen share the *same* yield strength label.
- **Leakage Prevention**: The data split (Train/Validation/Test) is performed at the **Specimen Level**. All images belonging to one specimen must be assigned to the same split. This prevents the model from "memorizing" a specimen's strength by seeing one of its images in training and another in testing.

**Validation Logic**:
- The validation script (`code/data/validate.py`) will check that no `specimen_id` appears in both the training and test sets.
- Invalid pairs (missing metadata or NaN values) are rejected if the ratio exceeds a negligible threshold.

## Methodology

### Model Architecture

**Base Architecture**: MobileNetV2 (Pre-trained on ImageNet)  
**Strategy**: Transfer Learning with Frozen Backbone.
- **Frozen Layers**: All convolutional layers up to the final global average pooling.
- **Trainable Head**: A single fully connected layer (Linear) mapping the feature vector to a scalar yield strength value.
- **Rationale**: MobileNetV2 is computationally efficient, designed for mobile/edge devices, and performs well on CPU. Freezing the backbone drastically reduces the number of trainable parameters, preventing overfitting on the relatively small dataset and ensuring training completes within the 6-hour limit.

**Alternative**: ResNet-18 (if MobileNetV2 fails to converge), but MobileNetV2 is the primary choice due to its lightweight nature.

### Training Protocol

1.  **Preprocessing**:
    - Resize images to 224×224 pixels.
    - Normalize pixel values using ImageNet mean/std or dataset-specific statistics.
    - Split into Train/Validation/Test (e.g., 70/15/15) with a fixed random seed, **enforcing specimen-level separation**.
2.  **Augmentation**:
    - **Allowed**: Horizontal/Vertical flips, brightness/contrast adjustment.
    - **Restricted**: Random rotation is **excluded** to preserve the physical orientation of the EBSD maps relative to the sample frame (crystallographic direction).
    - Applied on-the-fly during training to increase effective dataset size (FR-003).
3.  **Optimization**:
    - Loss Function: Mean Squared Error (MSE).
    - Optimizer: Adam (lr=1e-3, weight_decay=1e-5).
    - Scheduler: ReduceLROnPlateau.
    - Early Stopping: Patience=5 epochs on validation loss.
4.  **Constraints**:
    - Batch size: Tuned to fit within 7 GB RAM (likely 16-32).
    - Max Epochs: A predefined upper limit (or until early stopping).

### Evaluation Metrics

1.  **Primary Metrics**:
    - **MSE**: Mean Squared Error on the test set.
    - **R²**: Coefficient of Determination on the test set.
2.  **Baseline Comparison**:
    - **Naive Baseline**: Constant predictor using the mean of the training set yield strengths.
    - **Statistical Test**: **Paired t-test** (α=0.05) on the squared errors of the *same* test samples (error_cnn_i^2 vs error_baseline_i^2).
    - **Null Hypothesis**: The mean difference in squared errors (CNN - Baseline) is not significantly less than zero.
    - **Failure Criterion**: R² < 0.5 indicates insufficient signal (Constitution Principle VI).

### Interpretability & Sensitivity

1.  **Grad-CAM**:
    - Generate heatmaps for test images to visualize which microstructure features (grain boundaries, orientations) drive predictions (FR-006).
    - **Validation**: **Expert Review Protocol**. A domain expert will visually inspect heatmaps to confirm they align with known strengthening mechanisms (e.g., grain boundaries, precipitates). This replaces the impossible IoU calculation against non-existent manual annotations (SC-005).
    - **Secondary Metric**: Correlation between Grad-CAM activation intensity and extracted grain size.
2.  **Sensitivity Analysis**:
    - Define "High Strength" threshold as the **median predicted strength** of the test set (per FR-007).
 - **Sweep Range**: Thresholds from [median - 15%, median + [deferred]] in **[deferred] increments** (e.g., -15%, -10%, -5%, [deferred], +[deferred], +[deferred], +[deferred]).
    - Report variation in False Positive and False Negative rates relative to the median.
    - *Note*: If a fixed physical threshold (e.g., 250 MPa) exists in the dataset metadata, a secondary analysis will be performed using that value.
3.  **Uncertainty Quantification**:
    - **Method**: Monte Carlo Dropout (MC Dropout) at inference time.
    - **Process**: Run multiple forward passes with dropout enabled for each test sample.
    - **Output**: Mean prediction ± 95% Confidence Interval (CI) (FR-008).

## Statistical Rigor

- **Multiple Comparisons**: Not applicable for the primary t-test (single comparison). If multiple architectures are tested, Bonferroni correction will be applied.
- **Power Analysis**: With N = [deferred] (configurable), the study has >90% power to detect an R² improvement of 0.05 over the baseline at α=0.05, assuming a medium effect size. This confirms the sample size is sufficient for the planned hypothesis.
- **Causal Inference**: This is an observational study (predictive modeling). Claims will be framed as associational ("microstructure features predict strength") rather than causal.
- **Collinearity**: Not applicable as the input is an image tensor; however, the model will be inspected for reliance on artifacts (e.g., image borders) via Grad-CAM.

## Compute Feasibility

- **CPU-First**: The entire pipeline (download, preprocessing, training, evaluation) is designed to run on a multi-core, limited-RAM CPU instance.
- **Memory Management**:
    - Batch loading with `DataLoader` and `num_workers=0` or `1` to avoid memory spikes.
    - Gradient accumulation if batch size is too small for convergence.
- **GPU Escape Hatch**: Not required for this specific lightweight CNN task. If the model fails to converge on CPU within 6 hours, the plan will switch to a smaller sample size (e.g., 500 images) rather than offloading to a GPU, as the spec prioritizes CPU feasibility for reproducibility.

## Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **MobileNetV2** | Optimal balance of accuracy and computational cost for CPU inference. |
| **Frozen Backbone** | Reduces trainable parameters, preventing overfitting and speeding up convergence on small datasets. |
| **MC Dropout** | Provides a robust, model-agnostic method for uncertainty quantification without requiring ensemble training. |
| **Synthetic Generation** | Necessary due to the lack of public real-world paired EBSD-Yield datasets; ensures reproducibility. |
| **Specimen-Level Split** | Prevents data leakage when multiple images share a single yield strength label. |
| **Paired t-test** | Statistically valid for comparing paired errors (same image, two models) against a constant baseline. |
| **Expert Review** | Necessary validation method for Grad-CAM in the absence of pixel-level ground truth annotations. |
| **No Rotation** | Preserves physical orientation integrity of EBSD maps. |
| **Median Threshold** | Adheres to spec FR-007 while acknowledging the data-dependent nature of the threshold. |