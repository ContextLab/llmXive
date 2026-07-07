# Feature Specification: Machine Learning Prediction of Fracture Toughness from Microstructure Images

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Machine Learning Prediction of Fracture Toughness from Microstructure Images"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

A materials researcher uploads a dataset of metallic alloy micrographs (SEM/TEM) and corresponding fracture toughness (K_IC) values. The system automatically converts images to 8-bit grayscale, resizes them to 128x128 pixels, normalizes intensities, and splits the data into [deferred] training, [deferred] validation, and [deferred] test sets, stratified by alloy family (steel, Al, Ti).

**Why this priority**: This is the foundational step; without a clean, stratified, and reproducible dataset split, no model training or evaluation is valid. It ensures data integrity and prevents leakage between training and testing.

**Independent Test**: Can be fully tested by running the preprocessing script on a dummy dataset and verifying the output directory structure, file counts per split, and that the alloy family distribution matches the input distribution via stratified sampling (proportional representation as close as mathematically possible given integer constraints).

**Acceptance Scenarios**:

1. **Given** a CSV file with image paths and K_IC values and a folder of images, **When** the preprocessing script is executed, **Then** the output folder contains three subdirectories (`train`, `val`, `test`) with images resized to 128x128 and a `split_metadata.csv` recording the alloy family distribution.
2. **Given** a dataset containing only "steel" and "Al" alloys, **When** the script runs, **Then** the test set contains at least one sample from each alloy family present in the input.

### User Story 2 - Lightweight CNN Model Training and Baseline Comparison (Priority: P2)

A researcher trains a lightweight 3-block CNN on the training set and compares its performance against linear regression and Random Forest baselines trained on handcrafted texture features. The system performs 5 independent training runs with different random seeds, outputs R², MAE, and RMSE for all models, and performs a Wilcoxon signed-rank test to determine statistical significance.

**Why this priority**: This delivers the core scientific value: determining if imaging data alone explains variance in toughness and if deep learning outperforms traditional methods, while accounting for variance introduced by random initialization.

**Independent Test**: Can be tested by running the training script on a small subset of data (e.g., 50 images) for 5 seeds and verifying that the output log contains the R² and MAE metrics for all three models and a p-value from the Wilcoxon test.

**Acceptance Scenarios**:

1. **Given** a preprocessed training set of ≥ 50 images, **When** the training script is executed with 5 different random seeds, **Then** the output log reports R² and MAE for the CNN, Linear Regression, and Random Forest models across all 5 runs, and a p-value from the Wilcoxon signed-rank test comparing the distribution of MAE differences.
2. **Given** a test set, **When** the evaluation script runs, **Then** the system outputs a JSON file containing the mean absolute error for each model and the result of the Wilcoxon signed-rank test (statistic and p-value).

### User Story 3 - Feature Attribution and Stability Reporting (Priority: P3)

A researcher generates Grad-CAM heatmaps for a random subset of test images to visualize which microstructural regions influenced the model's predictions. The system validates the stability of these attributions by computing the Intersection-over-Union (IoU) of the heatmaps across 5 augmented views of the same image.

**Why this priority**: This addresses the "mechanistic understanding" goal of the research question by ensuring the model's attention is stable against input perturbations, rather than relying on potentially circular correlations with derived metrics.

**Independent Test**: Can be tested by running the attribution script on a single test image with 5 augmentations and verifying that a heatmap image is generated, and that an IoU score is calculated and printed.

**Acceptance Scenarios**:

1. **Given** a test image and a trained CNN model, **When** the Grad-CAM script is executed with 5 augmentations, **Then** heatmap images are generated for each view, and an IoU score is calculated between the heatmaps.
2. **Given** a set of 10 test images and their corresponding heatmap IoU scores, **When** the stability script runs, **Then** the system outputs the mean IoU score and confirms if it meets the stability threshold.

### Edge Cases

- What happens if the input dataset contains images with resolution significantly larger than 128x128 (e.g., 4000x3000)? The system must downsample without aspect ratio distortion and log a warning for each image processed.
- How does the system handle an input CSV where the K_IC value is missing for a specific image? The system must exclude that row from all splits and log the count of excluded samples.
- What happens if the stratification results in a test set with only one alloy family (due to extreme class imbalance)? The system must raise a fatal error and suggest increasing the minimum sample size per family or adjusting the split ratio.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST convert all input images to 8-bit grayscale and resize them to exactly 128x128 pixels before training. (See US-1)
- **FR-002**: The system MUST split the dataset into training, validation, and test sets, stratified by alloy family, using a fixed random seed to ensure reproducibility. (See US-1)
- **FR-003**: The system MUST implement a multi-block CNN architecture (Conv-ReLU-BatchNorm-MaxPool) followed by two fully connected layers (256 → 64 → 1) for regression. (See US-2)
- **FR-004**: The system MUST train baseline models (Linear Regression and RandomForestRegressor with a standard ensemble configuration) on handcrafted texture features (GLCM, band-pass filtered power spectra) extracted from the same images. (See US-2)
- **FR-005**: The system MUST perform 5 independent training runs with different random seeds and execute a Wilcoxon signed-rank test (α = 0.05) on the distribution of MAE differences between the CNN and each baseline model. (See US-2)
- **FR-006**: The system MUST generate Grad-CAM heatmaps for a random subset of at least 10 test images to visualize predictive features. (See US-3)
- **FR-007**: The system MUST calculate the Intersection-over-Union (IoU) of Grad-CAM heatmaps across multiple augmented views of the same image and report the mean IoU score. (See US-3)
- **FR-008**: The system MUST operate entirely on CPU-only hardware to ensure compatibility with standard CI runners. (See Assumptions)

### Key Entities

- **MicrostructureImage**: Represents a single micrograph, containing attributes for file path, alloy family, pixel dimensions, and normalized intensity array.
- **FractureToughnessRecord**: Represents a data point linking a MicrostructureImage to a scalar K_IC value (fracture toughness).
- **ModelEvaluationResult**: Represents the output of a model run, containing attributes for R², MAE, RMSE, and the specific model type used.
- **AttributionMap**: Represents a Grad-CAM heatmap, linking a specific image to a 2D array of activation values and the corresponding overlay image.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The explanatory power of imaging data is measured against the performance of the baseline models to determine if the CNN demonstrates a statistically significant improvement. (See US-2)
- **SC-002**: The predictive superiority of the CNN is measured against the baseline models using a Wilcoxon signed-rank test with α = 0.05 on the distribution of MAE differences across 5 runs. (See US-2)
- **SC-003**: The validity of feature attribution is measured by the consistency of Grad-CAM heatmaps across 5 augmented views of the same image (IoU score). (See US-3)
- **SC-004**: The computational feasibility is measured against the constraint of completing the full training and evaluation pipeline within 6 hours on a 2-core CPU-only runner. (See Assumptions)
- **SC-005**: The robustness of the model is measured by calculating the standard deviation of R² across multiple runs with different seeds. (See Assumptions)

## Assumptions

- The "Metallurgical Microstructure–Fracture Toughness" dataset from the Materials Data Facility contains all necessary variables (images and K_IC values) for the specified alloy families (steel, Al, Ti).
- The dataset size is sufficient to train a lightweight CNN without overfitting after augmentation, targeting an effective sample size of ≥ 500 images.
- The free-tier GitHub Actions runner (2 CPU cores, ~7 GB RAM) is sufficient to train the specified 3-block CNN on 128x128 images within the 6-hour time limit.
- The imaging resolution of the source micrographs is sufficient to resolve grain boundaries and precipitates after resizing to 128x128 pixels.
- The K_IC values provided in the dataset are ground truth measurements obtained via standard mechanical testing protocols, ensuring valid labels for supervised learning.
- The statistical power of the Wilcoxon test is sufficient to detect a meaningful difference in MAE between the CNN and baselines given the expected sample size and number of runs.