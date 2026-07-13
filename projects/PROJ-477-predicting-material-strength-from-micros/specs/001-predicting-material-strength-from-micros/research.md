# Research: Predicting Material Strength from Microstructure Images

## 1. Dataset Strategy

### 1.1 Verified Source Selection
The project utilizes the **EBSD Synthetic** dataset, which contains paired 2D EBSD images and material properties. This is the only dataset in the verified list that matches the domain (microstructure images) and format (image + metadata).

* **Source Name**: EBSD Synthetic
* **Verified URL**: `
* **Format**: ZIP archive containing images and a manifest (CSV/JSON).
* **Rationale**: Directly provides the "MicrostructureImage" entity required by the spec.

### 1.2 Dataset Variable Fit Verification & Label Generation
* **Required Variables**:
 * **Predictor**: 2D EBSD Image (pixel data).
 * **Outcome**: Yield Strength (scalar, MPa).
 * **Covariates**: Grain size, orientation.
* **Fit Confirmation**: The `data_synth_ebsd.zip` contains synthetic EBSD maps.
* **Critical Gap & Resolution**:
 * *Gap*: The dataset does **not** contain a "Yield Strength" column in its manifest. It provides crystallographic orientation and grain boundaries, but not mechanical properties.
 * *Resolution*: The plan implements a **Physics-Based Label Generation** step.
 1. **Extract Grain Size**: For every image, grain size ($d$) is extracted via image segmentation (OpenCV) to measure equivalent circular diameter. **This satisfies FR-009.**
 2. **Generate Label**: Yield Strength ($\\sigma_y$) is computed using the Hall-Petch relationship: $\\sigma_y = \\sigma_0 + k d^{-1/2}$.
 3. **Constants**: $\\sigma_0$ and $k$ are set to standard values for the simulated material (e.g., Aluminum or Steel) as defined in the `config.py` defaults, ensuring physical consistency.
 * *Usage of Grain Size Features*:
 1. **Label Generation**: Used to create the ground truth target.
 2. **Baseline Model**: Used to train a physics-based baseline predictor (Hall-Petch directly).
 3. **Interpretability Proxy**: Used to validate the CNN's attention maps (correlation analysis).
 * *Action*: This derived variable serves as the ground truth for the regression task. The model is trained to predict this physically derived value from the image, validating that the image contains the morphological signal required by the physics.

### 1.3 Data Preprocessing & Splitting
* **Resizing**: All images resized to 224×224 (FR-001).
* **Normalization**: Pixel values normalized to a standard range or using ImageNet statistics..
* **Splitting**: Random split into Train/Validation/Test (e.g., majority/minority/minority).
* **Handling Edge Cases**:
 * *Aspect Ratio*: Images resized via center-crop + resize to 224×224.
 * *Bit Depth*: Converted to 8-bit or normalized float32.
 * *Corruption*: Script checks for NaN values and missing pairs; aborts if invalid ratio > 1% (US-1).

## 2. Model Strategy

### 2.1 Architecture Selection
* **Candidate**: MobileNetV2 (or ResNet-18).
* **Rationale**:
 * **CPU Feasibility**: MobileNetV is designed for mobile/edge devices, making it the most viable option for a multi-core CPU runner with limited RAM..
 * **Transfer Learning**: Backbone weights are frozen (loaded from ImageNet). Only the final regression head is trained.
 * **Constraint Adherence**: Avoids GPU/CUDA requirements (FR-002).
* **Decision**: Primary: MobileNetV2. Fallback: ResNet-18.

### 2.2 Training Strategy
* **Optimizer**: SGD or AdamW.
* **Loss Function**: Mean Squared Error (MSE).
* **Augmentation**: Random rotation (±15°), horizontal/vertical flip, brightness adjustment (US-2, FR-003). Applied *only* to training set.
* **Ablation Mechanism**: Training run with `--no-augmentation` flag to disable augmentation for the ablation study (Constitution Principle VII).
* **Early Stopping**: Patience=5 epochs on validation loss.
* **Batch Size**: Dynamically determined to fit within 7GB RAM (likely 8-16).
* **Epochs**: Max 50, or until early stopping.

### 2.3 Baseline Strategy
* **Naive Predictor**: Predicts the mean of the training set yield strength for all test samples.
* **Physics-Based Baseline**: Predicts yield strength using the extracted grain size and the Hall-Petch equation directly (without CNN). This serves as a stronger, physically grounded comparator than the naive mean.

## 3. Evaluation & Statistical Rigor

### 3.1 Metrics
* **Primary**: MSE (Mean Squared Error), R² (Coefficient of Determination).
* **Reference**: Measured on the held-out test set (SC-001).
* **Null Threshold**: R² < 0.2 indicates insufficient signal (Constitution Principle VI).

### 3.2 Statistical Significance
* **Test**: **Paired t-test** on the per-sample squared errors.
 * *Hypothesis*: H0: Mean(CNN_error_i - Baseline_error_i) = 0.
 * *Method*: Calculate $e_{cnn, i} = (y_i - \\hat{y}_{cnn, i})^2$ and $e_{base, i} = (y_i - \\hat{y}_{base, i})^2$. Test the mean of the difference $d_i = e_{cnn, i} - e_{base, i}$.
 * *Rationale*: A single-sample t-test is invalid here because the baseline error is a constant scalar for all samples, but the *difference* in errors forms a distribution. A paired test correctly accounts for the correlation between errors on the same sample.
* **Alpha**: 0.05 (FR-005).
* **Multiple Comparisons**: If multiple architectures are tested, Bonferroni correction applied.

### 3.3 Power & Sample Size
* **Pre-Study Calculation**: Before splitting, calculate the minimum N required to detect an effect size (R² improvement from 0 to 0.2) with Power=0.8 at α=0.05.
* **Protocol**:
 * If N < Required: The study is labeled "Exploratory". The hypothesis test is performed but interpreted with the explicit caveat that low power may lead to Type II errors.
 * If N ≥ Required: Standard interpretation.
* **Mitigation**: Use of transfer learning and data augmentation to maximize effective sample size.

### 3.4 Interpretability (FR-006, SC-005)
* **Method**: Grad-CAM (Gradient-weighted Class Activation Mapping).
* **Validation (Proxy for IoU)**:
 * Since manual annotations are not available, we use a **Quantitative Proxy**.
 * **Metric**: Pearson Correlation Coefficient between the mean Grad-CAM activation intensity (in the region of interest) and the extracted grain size feature.
 * **Hypothesis**: If the model learns morphology, regions with high activation should correlate with grain boundary density/size.
 * **Threshold**: Correlation > 0.3 (or p < 0.05) is considered evidence of morphological reliance.
 * **Artifact**: `results/interpretability_report.json` containing correlation scores and sample heatmaps.
* **Collinearity**: Grain size is extracted from the image, so the CNN and the physics baseline are not independent in a causal sense, but the comparison validates if the CNN captures the same signal as the physics model.

### 3.5 Sensitivity Analysis (FR-007, SC-003)
* **Threshold Definition**: Median of the **Ground Truth** (generated) yield strength values in the test set. (NOT the predicted median).
* **Binarization**: Samples with $y_{true} > Median$ are "High Strength", others "Low".
* **Sweep**: Thresholds at {0.01, 0.05, 0.1} relative to the median.
* **Output**: False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold.
* **Robustness**: If performance degrades sharply with small threshold changes, the model is deemed unstable.

## 4. Computational Feasibility

* **Hardware**: GitHub Actions Free Tier (multiple CPU cores, ample RAM).
* **Software**: PyTorch CPU build (`torch==2.x+cpu`). No CUDA.
* **Memory Management**:
 * Dataset loaded via `DataLoader` with `batch_size` tuned to fit RAM.
 * Intermediate tensors cleaned explicitly.
 * No large model loading (frozen backbone is ~-15MB).
* **Runtime**:
 * Data Preprocessing & Feature Extraction: < 30 mins.
 * Training (multiple epochs, small batch): several hours.
 * Evaluation & Interpretability: < 1 hour.
 * Total: < 6 hours.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Mismatch** | Fatal | Preprocessing script validates column names. If Yield Strength missing, Hall-Petch generation is triggered. |
| **OOM on CPU** | High | Dynamic batch size; `pin_memory=False`; use of `torch.no_grad()` during eval. |
| **Model Convergence Failure** | Medium | Early stopping; fallback to simpler ResNet-18 if MobileNetV2 fails. |
| **No Signal (R² < 0.2)** | Expected Outcome | Documented as a valid scientific result (null hypothesis accepted) via specific protocol. |
| **Low Statistical Power** | Medium | Pre-study power calculation; "Exploratory" label if N is insufficient. |