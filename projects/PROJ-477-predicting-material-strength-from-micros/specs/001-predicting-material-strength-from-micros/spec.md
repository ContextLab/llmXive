# Feature Specification: Predicting Material Strength from Microstructure Images

**Feature Branch**: `001-predict-material-strength-cnn`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Material Strength from Microstructure Images with Convolutional Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download a public microstructure-strength dataset (e.g., from HuggingFace or Zenodo), preprocess the 2D EBSD images (resize to 224×224, normalize), and split them into [deferred] training, [deferred] validation, and [deferred] test sets to establish a reproducible baseline for analysis.

**Why this priority**: Without a validated, standardized dataset split and preprocessed images, no model training or evaluation can occur. This is the foundational step that determines data quality and statistical validity.

**Independent Test**: The pipeline can be fully tested by running the data loading script and verifying that the resulting train/validation/test directories contain the correct number of image files and that a corresponding CSV/JSON manifest correctly maps image filenames to yield strength values.

**Acceptance Scenarios**:

1. **Given** a valid dataset source URL and a local storage directory, **When** the preprocessing script is executed, **Then** the script downloads the data, resizes all images to 224×224 pixels, normalizes pixel values, and saves the split datasets into distinct folders with a manifest file.
2. **Given** a corrupted or missing dataset source, **When** the script is executed, **Then** the system fails gracefully with a clear error message indicating the missing resource and halts without partial data processing.
3. **Given** a dataset with mismatched image-strength pairs, **When** the validation step runs, **Then** the system identifies and reports the count of invalid pairs (missing metadata or NaN values) and aborts processing if the invalid ratio exceeds 1%.

---

### User Story 2 - Lightweight CNN Model Training and Evaluation (Priority: P2)

The researcher MUST be able to train a lightweight CNN (e.g., MobileNetV2 or ResNet-18 with frozen ImageNet weights) on the preprocessed dataset using CPU-only resources, applying data augmentation, and evaluate the model's predictive performance (MSE, R²) against a naive statistical baseline.

**Why this priority**: This is the core research activity. It tests the hypothesis that microstructure images contain sufficient signal for strength prediction. It must run within the 6-hour CPU constraint to be feasible.

**Independent Test**: The model training and evaluation can be tested independently by executing the training script with a fixed random seed and verifying that it completes within the time limit, produces a model artifact, and outputs a report containing MSE and R² metrics for both the CNN and the baseline mean predictor.

**Acceptance Scenarios**:

1. **Given** the preprocessed train/validation split and a CPU-only environment, **When** the training script is executed with the specified architecture and hyperparameters, **Then** the model trains for a maximum of 50 epochs or until early stopping triggers (patience=5), saves the best checkpoint based on validation loss, and generates a performance report comparing the CNN against the mean predictor.
2. **Given** a model that fails to converge (validation loss increases for consecutive epochs), **When** the early stopping mechanism triggers, **Then** the training halts, the best checkpoint is retained, and the report indicates the early stopping reason.
3. **Given** the test set, **When** the final evaluation is run, **Then** the system calculates and logs the Mean Squared Error (MSE) and Coefficient of Determination (R²) for the CNN and the baseline, and performs a single-sample t-test (α=0.05) to determine if the CNN error is significantly lower than the baseline error.

---

### User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

The researcher MUST be able to generate visual explanations (Grad-CAM or SHAP) to identify which microstructure features drive predictions and perform a sensitivity analysis on the prediction threshold to understand model robustness.

**Why this priority**: While not strictly required for the primary R² metric, interpretability is essential for scientific validity (proving the model learned morphology, not artifacts) and the sensitivity analysis addresses the methodological requirement for threshold justification.

**Independent Test**: The interpretability and sensitivity features can be tested by running the analysis script on the test set, verifying that heatmaps are generated for sample images, and confirming that the sensitivity report shows performance variation across the defined threshold sweep.

**Acceptance Scenarios**:

1. **Given** a trained model and a set of test images, **When** the interpretability script is executed, **Then** the system generates Grad-CAM heatmaps overlaid on the original microstructure images, highlighting regions contributing most to the strength prediction.
2. **Given** a defined decision threshold for classifying "high strength" materials (defined as the median predicted strength of the test set), **When** the sensitivity analysis is run, **Then** the system sweeps the threshold across a set of low relative values (relative to the median) and reports the variation in false-positive and false-negative rates.
3. **Given** a model prediction with high uncertainty, **When** the user requests an explanation, **Then** the system provides a confidence interval alongside the prediction value.

### Edge Cases

- What happens if the dataset contains images with extreme aspect ratios or non-standard pixel depths (e.g., 16-bit vs 8-bit)? The preprocessing pipeline MUST normalize these to the standard 224×224 8-bit format or reject them with a log entry.
- How does the system handle a scenario where the naive statistical baseline outperforms the CNN on the test set? The system MUST still report the metrics and the statistical significance test result, even if the null hypothesis is not rejected.
- What happens if the CPU memory limit is exceeded during data augmentation? The system MUST implement a batch loading strategy that prevents memory overflow, ensuring the job does not crash.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess the public microstructure-strength dataset, resizing images to 224×224 and normalizing pixel values, to ensure consistent input for the model (See US-1).
- **FR-002**: System MUST implement a lightweight CNN architecture (e.g., MobileNetV or ResNet variants) with frozen backbone weights; only the final classification head is trained to respect the 7GB RAM and CPU-only constraints (See US-2).
- **FR-003**: System MUST apply data augmentation techniques (random rotation, flip, brightness adjustment) during training to increase effective dataset size and improve generalization (See US-2).
- **FR-004**: System MUST evaluate model performance using Mean Squared Error (MSE) and R² on a held-out test set and compare these metrics against a naive statistical baseline (constant training set mean) (See US-2).
- **FR-005**: System MUST perform a single-sample t-test (α=0.05) to statistically validate whether the CNN mean squared error is significantly lower than the baseline mean squared error, and report the outcome (significant/not significant) (See US-2).
- **FR-006**: System MUST generate Grad-CAM or SHAP visualizations to interpret which image regions drive predictions, ensuring the model relies on morphological features rather than artifacts (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis on the prediction threshold (defined as the median predicted strength of the test set) by sweeping it over a representative set of low absolute difference values. and reporting the variation in false-positive/false-negative rates (See US-3).
- **FR-008**: System MUST calculate and output a confidence interval for each individual prediction to quantify uncertainty (See US-3).
- **FR-009**: System MUST extract grain size features for every image in the test set to ensure any comparative analysis uses the exact same instances for both models (See US-2).

### Key Entities

- **MicrostructureImage**: Represents a 2D EBSD map of a polycrystalline material, containing pixel data and metadata (grain size, orientation if available).
- **YieldStrengthValue**: The macroscopic mechanical property (scalar) associated with a specific microstructure image, measured in MPa.
- **PredictionResult**: The output of the model containing the predicted strength, confidence interval, and associated visualization data.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model prediction accuracy (R²) is measured against the naive statistical baseline (mean predictor) performance to determine if image-based features provide superior signal (See FR-004).
- **SC-002**: Statistical significance of the performance difference is measured against the α=0.05 threshold using a single-sample t-test comparing CNN error to baseline error (See FR-005).
- **SC-003**: Model robustness is measured against the sensitivity analysis results across the defined threshold sweep to assess stability of classification rates (See FR-007).
- **SC-004**: Computational feasibility is measured against a bounded CPU runtime limit and a constrained RAM capacity. to ensure the analysis is reproducible on free-tier CI (See FR-002).
- **SC-005**: Interpretability validity is measured by computing Intersection-over-Union (IoU) between Grad-CAM heatmaps and manually annotated grain boundaries on a small-sample subset, requiring IoU ≥ 0.4, OR via expert review report (See FR-006).

## Assumptions

- The public dataset (e.g., from HuggingFace or Zenodo) contains paired EBSD images and corresponding yield strength values with sufficient sample size (N ≥ 100) to support training a lightweight CNN without severe overfitting.
- The microstructure images are 2D representations (e.g., EBSD maps) that capture sufficient morphological information (grain size, boundary orientation) to predict yield strength without 3D volumetric data.
- The "naive statistical baseline" (constant mean predictor) is a valid reference point for comparison, representing the null hypothesis that no image features improve prediction.
- The free-tier GitHub Actions runner (2 CPU, ~7GB RAM) is sufficient for training a frozen-weight MobileNetV2/ResNet-18 on a sampled dataset (e.g., <5000 images) within 6 hours.
- The dataset does not require GPU-accelerated quantization (8-bit/4-bit) or CUDA-specific libraries, allowing execution in standard PyTorch CPU mode.
- The yield strength values in the dataset are measured under consistent conditions (e.g., room temperature, standard strain rate) to ensure comparability across samples.