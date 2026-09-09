# Feature Specification: Predicting Material Strength from Microstructure Images

**Feature Branch**: `001-predict-material-strength-cnn`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Material Strength from Microstructure Images with Convolutional Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion, Validation, and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download a public microstructure-strength dataset, validate the integrity of image-strength pairs, preprocess the 2D EBSD images (resize to 224×224, normalize), and split them into training, validation, and test sets using a 5-fold cross-validation strategy to establish a reproducible baseline for analysis.

**Why this priority**: Without a validated, standardized dataset split and preprocessed images, no model training or evaluation can occur. This step ensures data quality and prevents the introduction of invalid samples that would invalidate statistical conclusions. 5-fold cross-validation is used to reduce variance in metric estimation for small-sample regimes.

**Independent Test**: The pipeline can be fully tested by running the data loading and validation scripts and verifying that the resulting `results/validation_report.json` contains the count of valid/invalid pairs, that the `results/metrics.json` file is initialized with a valid schema, and that the split directories contain the correct number of image files.

**Acceptance Scenarios**:

1. **Given** a valid dataset source URL and a local storage directory, **When** the preprocessing script is executed, **Then** the script downloads the data, resizes all images to 224×224 pixels, normalizes pixel values, and saves the split datasets into distinct folders with a manifest file.
2. **Given** a corrupted or missing dataset source, **When** the script is executed, **Then** the system fails gracefully with a clear error message indicating the missing resource and halts without partial data processing.
3. **Given** a dataset with mismatched image-strength pairs, **When** the validation step runs, **Then** the system identifies and reports the count of invalid pairs (missing metadata or NaN values) in `results/validation_report.json`, and aborts processing if the invalid ratio exceeds [DEFERRED: invalid_ratio_threshold] (configurable parameter, default 0.01).

---

### User Story 2 - Lightweight CNN Model Training and Evaluation (Priority: P2)

The researcher MUST be able to train a lightweight CNN (e.g., MobileNetV2 or ResNet-18 with frozen ImageNet weights) on the preprocessed dataset using CPU-only resources, applying data augmentation, and evaluate the model's predictive performance (MSE, R²) against BOTH a naive statistical baseline (constant training set mean) AND a physics-based baseline (linear regression on hand-crafted grain size features) using 5-fold cross-validation.

**Why this priority**: This is the core research activity. It tests the hypothesis that microstructure images contain sufficient signal for strength prediction compared to both a trivial baseline and a physics-based one. It must run within a feasible CPU time constraint to be feasible.

**Independent Test**: The model training and evaluation can be tested independently by executing the training script with a fixed random seed and verifying that it completes within the time limit, produces a model artifact, and outputs a report containing MSE and R² metrics for the CNN, the naive baseline, and the physics-based baseline.

**Acceptance Scenarios**:

1. **Given** the preprocessed train/validation split and a CPU-only environment, **When** the training script is executed with the specified architecture and hyperparameters, **Then** the model trains for a maximum of 50 epochs or until early stopping triggers (patience=5), saves the best checkpoint based on validation loss, and generates a performance report comparing the CNN against both the naive and physics-based baselines.
2. **Given** a model that fails to converge (validation loss increases for consecutive epochs), **When** the early stopping mechanism triggers, **Then** the training halts, the best checkpoint is retained, and the report indicates the early stopping reason.
3. **Given** the test set, **When** the final evaluation is run, **Then** the system calculates and logs the Mean Squared Error (MSE) and Coefficient of Determination (R²) for the CNN and both baselines using **actual** forward pass predictions, and performs a one-sample t-test (α=0.05) on the error differences for the naive baseline (testing against zero) and a paired t-test (α=0.05) for the physics-based baseline to determine if the CNN error is significantly lower. The paired t-test is chosen because residuals on the same test set are correlated and typically normal for N≥100.
4. **Given** the training configuration, **When** an ablation study is requested, **Then** the system retrains the model without data augmentation to assess the impact of augmentation on performance.

---

### User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

The researcher MUST be able to generate visual explanations (Grad-CAM or SHAP) to identify which microstructure features drive predictions and perform a sensitivity analysis on the prediction threshold to understand model robustness.

**Why this priority**: While not strictly required for the primary R² metric, interpretability is essential for scientific validity (proving the model learned morphology, not artifacts) and the sensitivity analysis addresses the methodological requirement for threshold justification.

**Independent Test**: The interpretability and sensitivity features can be tested by running the analysis script on the test set, verifying that heatmaps are generated for sample images, confirming that the sensitivity report shows performance variation across the defined threshold sweep, and verifying that the expert review procedure is executed with ≥3 independent reviewers.

**Acceptance Scenarios**:

1. **Given** a trained model and a set of test images, **When** the interpretability script is executed, **Then** the system generates Grad-CAM heatmaps overlaid on the original microstructure images, highlighting regions contributing most to the strength prediction.
2. **Given** a defined decision threshold for classifying "high strength" materials (defined as the median ground-truth strength of the training set), **When** the sensitivity analysis is run, **Then** the system sweeps the threshold across a set of relative values (±10% relative to the median in 5 steps) and reports the variation in false-positive and false-negative rates.
3. **Given** a model prediction with high uncertainty, **When** the user requests an explanation, **Then** the system provides a confidence interval alongside the prediction value.

### Edge Cases

- What happens if the dataset contains images with extreme aspect ratios or non-standard pixel depths (e.g., 16-bit vs 8-bit)? The preprocessing pipeline MUST normalize these to the standard 224×224 8-bit format or reject them with a log entry.
- How does the system handle a scenario where the naive statistical baseline outperforms the CNN on the test set? The system MUST still report the metrics and the statistical significance test result, even if the null hypothesis is not rejected.
- What happens if the CPU memory limit is exceeded during data augmentation? The system MUST implement a batch loading strategy that prevents memory overflow, ensuring the job does not crash.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess the public microstructure-strength dataset, resizing images to 224×224 and normalizing pixel values, to ensure consistent input for the model. The system MUST initialize a logger that writes to `results/metrics.log` and `results/metrics.json` (with a JSON schema including timestamp, metric_name, and value), generate a `results/validation_report.json` with the count of valid/invalid pairs, and exit with code 0 on success or 1 on failure (See US-1).
- **FR-002**: System MUST implement a lightweight CNN architecture (e.g., MobileNetV2 or ResNet variants) with frozen backbone weights; only the final classification head is trained to respect the 7GB RAM and CPU-only constraints (See US-2).
- **FR-003**: System MUST apply data augmentation techniques (random rotation, flip, brightness adjustment) during training to increase effective dataset size and improve generalization (See US-2).
- **FR-004**: System MUST evaluate model performance using Mean Squared Error (MSE) and R² on a held-out test set (via 5-fold cross-validation) and compare these metrics against BOTH a naive statistical baseline (constant training set mean) AND a physics-based baseline (linear regression on grain size features). All metrics MUST be computed from actual forward passes on the test set (See US-2).
- **FR-005**: System MUST perform a one-sample t-test (α=0.05) against zero on the error differences (CNN error - naive error) for the naive baseline, and a paired t-test (α=0.05) on the error differences for the physics-based baseline, to statistically validate whether the CNN mean squared error is significantly lower than the baseline mean squared errors, and report the outcome (significant/not significant) (See US-2).
- **FR-006**: System MUST generate Grad-CAM or SHAP visualizations to interpret which image regions drive predictions, ensuring the model relies on morphological features rather than artifacts (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis on the prediction threshold (defined as the median ground-truth strength of the training set) by sweeping it across a range of ±10% relative to the median in 5 steps, and reporting the variation in false-positive/false-negative rates (See US-3).
- **FR-008**: System MUST calculate and output a confidence interval for each individual prediction using Monte Carlo dropout with 50 forward passes at a 95% confidence level to quantify uncertainty. The final head MUST be configured for stochastic inference (dropout enabled) while the backbone remains frozen. The output format MUST be mean ± 1.96 * standard deviation (See US-3).
- **FR-009**: System MUST extract grain size features for every image in the test set to ensure the comparative analysis uses the exact same instances for both models (See US-2).

### Key Entities

- **MicrostructureImage**: Represents a 2D EBSD map of a polycrystalline material, containing pixel data and metadata (grain size, orientation if available).
- **YieldStrengthValue**: The macroscopic mechanical property (scalar) associated with a specific microstructure image, measured in MPa.
- **PredictionResult**: The output of the model containing the predicted strength, confidence interval, and associated visualization data.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model prediction accuracy (R²) is measured against the naive statistical baseline (mean predictor) and physics-based baseline (linear regression on grain size) performance to determine if image-based features provide superior signal (See FR-004).
- **SC-002**: Statistical significance of the performance difference is measured against the α=0.05 threshold using a one-sample t-test (naive) or paired t-test (physics) comparing CNN error to baseline errors (See FR-005).
- **SC-003**: Model robustness is measured against the sensitivity analysis results across the defined threshold sweep to assess stability of classification rates (See FR-007).
- **SC-004**: Computational feasibility is measured against a bounded CPU runtime limit and a constrained RAM capacity to ensure the analysis is reproducible on free-tier CI (See FR-002).
- **SC-005**: Interpretability validity is measured by consensus of ≥3 independent expert reviewers using a defined rubric focused on "morphological relevance" (e.g., grain boundaries, twins) on a random subset of 50 images. Consensus is defined as majority vote (≥2 of 3) on a 5-point Likert scale (See FR-006).

## Assumptions

- The public dataset (e.g., from HuggingFace or Zenodo) contains paired EBSD images and corresponding yield strength values with sufficient sample size (N ≥ 100) to support training a lightweight CNN without severe overfitting.
- The microstructure images are 2D representations (e.g., EBSD maps) that capture sufficient morphological information (grain size, boundary orientation) to predict yield strength without 3D volumetric data.
- The "naive statistical baseline" (constant mean predictor) and "physics-based baseline" (linear regression on grain size) are valid reference points for comparison, representing the null hypothesis and the physics-informed hypothesis respectively.
- The free-tier GitHub Actions runner (2 CPU, ~7GB RAM) is sufficient for training a frozen-weight MobileNetV2/ResNet-18 on a sampled dataset (e.g., <5000 images) within 6 hours.
- The dataset does not require GPU-accelerated quantization (8-bit/4-bit) or CUDA-specific libraries, allowing execution in standard PyTorch CPU mode.
- The yield strength values in the dataset are measured under consistent conditions (e.g., room temperature, standard strain rate) to ensure comparability across samples.
- All metrics and results are computed from REAL measurements of actual model outputs; no hardcoded values or simulated results are used.
- The 5-fold cross-validation strategy is a standard convention in the field for small-sample material science datasets to ensure robust metric estimation.
- The dataset contains at least 2,697 images after preprocessing, as reported in recent literature on microstructure analysis (Source: Recent literature on microstructure analysis, e.g., arXiv preprints 2023-2024).