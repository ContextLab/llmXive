# Feature Specification: Investigating the Role of Microglial Morphology in Age-Related Cognitive Decline

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Investigate the specific aspects of microglial morphological remodeling in the hippocampus vs. prefrontal cortex that predict age-related cognitive decline, distinguishing between normal aging and early Alzheimer's pathology."

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Morphological Feature Extraction (Priority: P1)

The researcher must be able to ingest high-resolution confocal microscopy images from the Allen Brain Atlas and AD Knowledge Portal, preprocess them to remove noise, and automatically extract quantitative morphological metrics (branch points, total length, soma area, Sholl intersections) for microglia in specific brain regions (Hippocampus or Prefrontal Cortex).

**Why this priority**: Without accurate, automated extraction of continuous morphological metrics tagged by brain region, the core research question cannot be addressed. This is the foundational data generation step.

**Independent Test**: Can be fully tested by running the pipeline on a small, labeled subset of images (e.g., 10 images from the Allen Brain Atlas) and verifying that the output CSV contains non-null, physically plausible values for branch points and soma area, matching manual counts within a 10% tolerance, and that every row includes a valid `brain_region` tag.

**Acceptance Scenarios**:

1. **Given** a set of raw confocal microscopy images from the hippocampus, **When** the preprocessing and extraction module is executed, **Then** the system outputs a structured dataset where every image has a corresponding row of morphological metrics (branch points, process length, soma area, Sholl counts) and a `brain_region` tag without crashing.
2. **Given** an image with known microglial branch count (verified by manual annotation), **When** the automated extraction runs, **Then** the reported branch point count deviates by no more than 10% from the manual ground truth.
3. **Given** an image lacking a valid `brain_region` tag in metadata, **When** ingestion runs, **Then** the system logs a warning and excludes the image from the output dataset.

---

### User Story 2 - Multivariate Regression Analysis with Interaction Effects (Priority: P2)

The researcher must be able to run a multiple linear regression model that predicts **Cognitive Status Score** (e.g., Morris Water Maze latency at a single timepoint) using orthogonal morphological features as predictors, explicitly including interaction terms between "Pathology Status" (Normal vs. Early AD) AND "Brain Region" (Hippocampus vs. Prefrontal Cortex) to identify region-specific predictive signatures.

**Why this priority**: This directly addresses the research question's core hypothesis: distinguishing predictors between normal aging and pathology, and comparing regions. It transforms raw data into the specific statistical evidence required.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset with known interaction effects (where a specific morphological feature predicts status only in the "AD" group AND only in the "Hippocampus") and verifying the model correctly identifies the significant interaction term with a p-value < 0.05.

**Acceptance Scenarios**:

1. **Given** a merged dataset of morphological metrics, cognitive scores, and region/pathology tags, **When** the regression model is executed, **Then** the output includes coefficients and p-values for interaction terms (e.g., `PC1_Morphology * PathologyStatus` and `PC1_Morphology * BrainRegion`) indicating whether the predictive power differs by group or region.
2. **Given** a stratified analysis request (e.g., "Analyze Hippocampus only"), **When** the model runs, **Then** the output is restricted to the specified brain region and the interaction terms are recalculated based solely on that subset.
3. **Given** a dataset where Pathology Status is missing, **When** the model runs, **Then** the system dynamically classifies 'Early AD' based on amyloid-beta load > 75th percentile of the control group (or calculated threshold) and proceeds with the analysis, logging the classification method used.

---

### User Story 3 - Model Validation and Sensitivity Analysis of Thresholds (Priority: P3)

The researcher must be able to validate the model's generalizability using k-fold cross-validation and perform a sensitivity analysis on any decision thresholds (e.g., Sholl radius steps) to ensure findings are robust and not artifacts of arbitrary parameter choices.

**Why this priority**: Ensures the scientific validity and reproducibility of the results, preventing overfitting and addressing methodological concerns about arbitrary parameter selection.

**Independent Test**: Can be fully tested by running the cross-validation loop and the sensitivity sweep (varying a parameter across a defined set) and verifying that the reported performance metrics (R², RMSE) remain stable (variation < 5% of mean) across folds and parameter variations.

**Acceptance Scenarios**:

1. **Given** a trained regression model, **When** k-fold cross-validation (k=5) is executed, **Then** the system outputs the mean and standard deviation of the R² score across all folds, confirming the model is not overfitting to a single data split.
2. **Given** a Sholl analysis radius step of 5µm, **When** the sensitivity analysis is run sweeping the step size to {2µm, 5µm, 10µm}, **Then** the system reports the variation in the primary interaction effect p-value across these settings, confirming the result is not an artifact of the specific radius choice.

---

### Edge Cases

- What happens when an image contains no detectable microglia (e.g., empty field of view)? The system must skip the image and log a warning, rather than crashing or outputting nulls that corrupt the regression.
- How does the system handle missing cognitive scores for a subject? The subject must be excluded from the regression analysis for that specific outcome variable, with a log entry recording the exclusion.
- What if the "Pathology Status" label is missing for a subject? The system must calculate the threshold dynamically using the control group distribution and apply the classification, logging the action.
- What if the input data lacks brain region metadata? The system must exclude the subject from region-specific analysis and log the exclusion.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest high-resolution confocal microscopy images from the Allen Brain Atlas and AD Knowledge Portal, supporting standard formats (e.g., TIFF), extracting metadata for brain region (Hippocampus, Prefrontal Cortex) and pathology status, and **tagging every record with its specific brain region**, filtering out untagged data (See US-1).
- **FR-002**: System MUST apply standardized denoising and background subtraction to all input images to ensure consistent segmentation across datasets (See US-1).
- **FR-003**: System MUST extract quantitative morphological features including branch point count, total process length, soma area, and Sholl analysis intersection counts at defined radii (See US-1).
- **FR-004**: System MUST perform multiple linear regression with **Cognitive Status Score** as the dependent variable, **orthogonal morphological components** (derived via PCA) as independent predictors, and explicit interaction terms for "Pathology Status" AND "Brain Region". The system MUST calculate Variance Inflation Factor (VIF) for all predictors; if any VIF > 5.0, the system MUST apply PCA or feature selection to reduce collinearity before reporting coefficients (See US-2).
- **FR-005**: System MUST execute k-fold cross-validation (k=5) to validate model generalizability and prevent overfitting given sample size constraints (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the Sholl radius step size across the set {2µm, 5µm, 10µm} and report the variation in the interaction effect p-value (See US-3).
- **FR-007**: System MUST output a structured report where the `causality_warning` flag is set to `true` and a standardized disclaimer string ("Associational findings only; causality not inferred") is appended to all text outputs unless the input metadata explicitly flags randomization (See US-2).
- **FR-008**: System MUST validate data availability by checking for the existence of matched subject IDs in the metadata of both the microglial image repository and the cognitive score repository before ingestion. If a subject ID lacks a corresponding entry in either dataset, that subject is excluded from the analysis with a log entry (See US-1).
- **FR-009**: System MUST apply Z-score normalization to all cognitive scores (e.g., Morris Water Maze latency) within each distinct study cohort before merging datasets. This transformation converts raw scores into standard deviations from the cohort mean, enabling direct comparison across heterogeneous study protocols. The normalization parameters (mean, std) are calculated per cohort and applied to all subjects in that cohort (See US-2).
- **FR-010**: System MUST classify 'Early AD' pathology based on amyloid-beta load exceeding the 75th percentile of the control group distribution OR the presence of specific tau pathology markers as defined in the source dataset metadata. If the source dataset lacks explicit labels, the system MUST calculate this threshold dynamically during the preprocessing phase using the control group's distribution. The specific threshold used (e.g., p75) is logged in the output report (See US-2).
- **FR-011**: System MUST perform Principal Component Analysis (PCA) on highly correlated morphological features (e.g., branch points vs. total length) to generate orthogonal predictors before regression, ensuring VIF < 5.0 for all inputs to the regression model (See US-2).

### Key Entities

- **MicroglialImage**: Represents a single microscopy image, containing attributes for brain region (hippocampus, prefrontal cortex), pathology status (Normal, Early AD), and raw pixel data.
- **MorphologicalMetrics**: A structured record containing derived quantitative features (branch points, soma area, Sholl counts) linked to a specific MicroglialImage.
- **CognitiveScore**: Represents a behavioral metric (e.g., Morris Water Maze latency) linked to a subject ID, used as the target variable for regression.
- **RegressionModel**: The statistical model object containing coefficients, p-values, and interaction terms derived from the merged dataset.
- **PathologyClassification**: Represents the dynamic logic for classifying 'Early AD' status based on amyloid-beta thresholds, storing the calculated threshold and the resulting binary label.
- **NormalizedCognitiveScore**: Represents the Z-score transformed cognitive metric, storing the original value, cohort mean, cohort std, and the resulting normalized score.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The extraction accuracy (branch point count deviation from manual ground truth) is measured against the manually annotated subset of images to ensure <10% error (See US-1).
- **SC-002**: The model's generalizability (R² standard deviation across 5 folds) is measured against the threshold of **5% of the mean R²** to confirm no overfitting (See US-3).
- **SC-003**: The robustness of the interaction effect (p-value variation) is measured against the sensitivity analysis sweep of Sholl radius steps {2µm, 5µm, 10µm} to ensure stability (See US-3).
- **SC-004**: The collinearity diagnostic (Variance Inflation Factor) is measured against a standard threshold. to confirm that definitionally related predictors (e.g., branch count vs. total length) do not inflate coefficient estimates (See US-2).
- **SC-005**: The statistical framing of results is measured against the requirement that the `causality_warning` flag is set to `true` and the standard disclaimer is present in all outputs (unless randomization is flagged), verified by a text scan of the output report (See US-2).
- **SC-006**: The data integrity check (subject exclusion log) is measured against the count of missing subject IDs in the input metadata; the number of logged exclusions must match the number of missing IDs (See US-1).

## Methodological Decisions

- **Pathology Thresholding**: The analysis will dichotomize continuous pathology scores using the top [deferred] (upper quartile) of the control group distribution as the threshold for 'Early AD'. This is a required protocol step to handle datasets lacking explicit labels, ensuring a consistent definition of pathology across heterogeneous sources.
- **Cross-Sectional Proxy**: The study uses 'Cognitive Status Score' (single timepoint) as a proxy for cognitive decline due to the cross-sectional nature of the available public datasets. Longitudinal decline rates are not modeled.
- **Dimensionality Reduction**: PCA is mandated for morphological features to resolve inherent multicollinearity (e.g., branch points vs. total length) before regression, ensuring statistical validity of interaction terms.

## Assumptions

- The Allen Brain Atlas Mouse Aging project and AD Knowledge Portal datasets contain the necessary matched variables: high-resolution microglial images, cognitive scores (e.g., Morris Water Maze), and pathology status labels for the same subjects.
- The analysis will be conducted on a CPU-only environment (GitHub Actions free tier: limited cores, constrained RAM) using Python libraries (scikit-learn, statsmodels) without GPU acceleration.
- The Sholl analysis radius step is used as the default., based on standard protocols in microglial morphology literature, with sensitivity analysis performed as a fallback.
- The sample size of the public datasets is sufficient to detect an interaction effect with adequate power given the number of predictors., though exact power calculations are deferred to the implementation phase.