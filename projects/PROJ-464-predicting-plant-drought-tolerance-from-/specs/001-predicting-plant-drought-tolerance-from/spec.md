# Feature Specification: Predicting Plant Drought Tolerance from RSA Data

**Feature Branch**: `001-predict-drought-tolerance`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Plant Drought Tolerance from Publicly Available Root System Architecture Data"

## User Scenarios & Testing

### User Story 1 - Extract and Aggregate Root System Architecture Metrics (Priority: P1)

A researcher needs to convert raw root images from public datasets (NPPN) into quantitative architectural metrics (depth, branching density, surface area) to enable downstream statistical analysis.

**Why this priority**: This is the foundational data ingestion step. Without quantified RSA metrics, no correlation analysis or prediction can occur. It is the primary bottleneck for the entire research pipeline.

**Independent Test**: The pipeline can be tested by running the image analysis module on a small, fixed set of known root images and verifying that the output CSV contains non-null, positive numerical values for all defined RSA traits.

**Acceptance Scenarios**:

1. **Given** a directory of 10 root system images in supported formats (PNG/JPG), **When** the image analysis script is executed on CPU, **Then** a CSV file is generated containing exactly 10 rows with columns for root depth, branching complexity, and surface area, and no rows contain missing values.
2. **Given** an image with invalid formatting or corrupted data, **When** the analysis script attempts processing, **Then** the script logs a specific error for that file and continues processing the remaining valid images without crashing.
3. **Given** a dataset of 1000 root images, **When** the analysis is run on a CPU-only environment with ≤7 GB RAM, **Then** the processing of the 1000 images completes within 60 minutes and the output file size is consistent with the input count.

---

### User Story 2 - Correlate RSA Metrics with Drought Physiology (Priority: P2)

A plant biologist needs to statistically validate whether deeper or more branched root systems associate with higher stomatal conductance and photosynthetic rates under water stress using the aggregated data.

**Why this priority**: This addresses the core research question. It transforms the processed data into the primary scientific insight (the association) required to justify the hypothesis.

**Independent Test**: The analysis can be tested by running the regression module on a synthetic dataset with a known positive correlation between a "depth" variable and a "conductance" variable, verifying that the calculated correlation coefficient matches the expected value within a 5% margin of error.

**Acceptance Scenarios**:

1. **Given** a merged dataset of RSA metrics and physiological traits for ≥50 species, **When** the regression analysis is performed using Spearman rank correlation and listwise deletion for missing data, **Then** the output includes a correlation matrix and p-values for the relationship between RSA traits and drought tolerance metrics.
2. **Given** an observational dataset where no randomization exists, **When** the results are generated, **Then** the report explicitly frames findings as "associational" and avoids causal language (e.g., "causes," "leads to").
3. **Given** multiple hypothesis tests (e.g., testing depth, branching, and surface area separately), **When** the analysis completes, **Then** a multiple-comparison correction (e.g., Bonferroni or FDR) is applied, and the adjusted p-values are reported.

---

### User Story 3 - Validate Predictive Robustness via Sensitivity Analysis (Priority: P3)

A peer reviewer needs to confirm that the predictive thresholds used in the classification model (a core requirement for testing the 'predict' hypothesis) are not arbitrary and that the results are robust to small variations in decision boundaries.

**Why this priority**: This ensures methodological soundness and defensibility of the results. It addresses the requirement for threshold justification and sensitivity, preventing the rejection of the spec due to arbitrary cutoffs.

**Independent Test**: The sensitivity module can be tested by running the model with a primary threshold and then sweeping that threshold across a defined range (e.g., ±0.05), verifying that the output includes a plot or table showing how the false-positive/false-negative rates change.

**Acceptance Scenarios**:

1. **Given** a classification model with a decision threshold (e.g., for high vs. low drought tolerance), **When** the sensitivity analysis is triggered, **Then** the system runs the model with thresholds at {0.01, 0.05, 0.1} deviations from the baseline (defined as the optimal F1 threshold or 0.5) and reports the resulting variation in accuracy.
2. **Given** a threshold derived from community standards, **When** the report is generated, **Then** the document includes a one-line justification citing the standard or rationale for that specific value.
3. **Given** a scenario where no explicit threshold is used (pure regression), **When** the report is generated, **Then** the sensitivity analysis section is skipped or explicitly states "N/A" with a note that regression coefficients were analyzed for stability instead.

### Edge Cases

- What happens when the TRY database does not contain physiological data for a specific species present in the NPPN image dataset? (System must exclude the species or impute with a documented method, not crash).
- How does the system handle images where root segmentation fails (e.g., high background noise)? (System must flag these as "unusable" and exclude them from the final count, logging the exclusion rate).
- What if the collinearity between "root depth" and "total root length" is too high (VIF > 5)? (System must detect this, report the VIF score, and avoid claiming independent predictive effects for both; PCA is performed unconditionally to handle this).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse root images from the NPPN Plant Phenome Pipeline and trait data from the TRY database for matching species. (See US-1)
- **FR-002**: System MUST extract RSA traits (depth, branching density, surface area) using CPU-optimized image analysis (OpenCV/scikit-image) without requiring GPU acceleration. (See US-1)
- **FR-003**: System MUST perform Multiple Linear Regression and Random Forest Regression to predict stomatal conductance and photosynthetic rate from RSA features (using PCA-transformed inputs), ensuring all operations fit within 7 GB RAM. Evaluation MUST use R² for regression, with 5-fold cross-validation and regularization to prevent overfitting. (See US-2)
- **FR-004**: System MUST apply multiple-comparison correction (e.g., Bonferroni or FDR) when testing >1 hypothesis and explicitly frame results as associational, not causal. (See US-2)
- **FR-005**: System MUST execute a sensitivity analysis sweeping decision thresholds by at least ±0.05 and report the impact on error rates IF a classification model is used; if only regression is performed, the system MUST report N/A with a justification. (See US-3)
- **FR-006**: System MUST detect and report high predictor collinearity (VIF > 5) and refrain from claiming independent effects for definitionally related variables. (See US-2)
- **FR-007**: System MUST binarize continuous physiological metrics (stomatal conductance/photosynthesis) into high/low classes using the median value as the threshold for classification tasks. (See US-3)
- **FR-008**: System MUST perform Random Forest Classification to predict the binary drought tolerance class (high/low) derived from FR-007, ensuring evaluation uses F1-score and 5-fold cross-validation. (See US-3)
- **FR-009**: System MUST explicitly frame the study as predicting "physiological state" (gs/A) unless an independent tolerance proxy (e.g., survival rate) is available; if available, the system MUST include it as a validation target. (See US-2)
- **FR-010**: System MUST perform Principal Component Analysis (PCA) on RSA traits prior to modeling to handle the "root economics spectrum" collinearity and MUST apply Phylogenetic Generalized Least Squares (PGLS) or equivalent phylogenetic correction to account for species non-independence. (See US-2)

### Key Entities

- **RootImage**: Raw image file from NPPN, associated with a species identifier.
- **RSAMetrics**: Derived quantitative features (depth, branching, surface area) linked to a RootImage.
- **PhysioTrait**: Measured physiological values (stomatal conductance, photosynthetic rate) linked to a species.
- **ModelResult**: Statistical output (coefficients, p-values, R², F1-score) linking RSAMetrics to PhysioTrait.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of root images successfully processed into valid RSA metrics is measured against the total number of images in the NPPN subset. (See FR-002)
- **SC-002**: The statistical significance (p-value) of the association between RSA metrics and drought tolerance is measured against the corrected alpha level (e.g., 0.05 / number of tests). (See FR-004)
- **SC-003**: The variation in model performance (R² or accuracy) across the sensitivity sweep (threshold ±0.05) is measured against the baseline performance to assess robustness. (See FR-005)
- **SC-004**: The Variance Inflation Factor (VIF) for correlated predictors is measured against the threshold of 5 to confirm collinearity handling. (See FR-006)
- **SC-005**: The total runtime of the end-to-end pipeline for the full NPPN subset (up to 10,000 images) is measured against the 6-hour limit for a GitHub Actions free-tier runner. (See FR-003)

## Assumptions

- The NPPN and TRY databases provide sufficient data overlap (same species) to enable a merged dataset of at least 30 distinct species for statistical power.
- The image analysis pipeline can process root images using standard CPU resources (OpenCV/scikit-image) without requiring 8-bit quantization or CUDA acceleration.
- The physiological data available in the TRY database or linked literature represents "water stress" conditions (stressed) rather than only optimal conditions, allowing for drought tolerance assessment.
- The dataset size (images + trait tables) will fit within the memory and disk constraints of the CI runner after sampling if necessary.
- Any missing values in the merged dataset are handled via listwise deletion or simple mean imputation, as the sample size is expected to be small (<1000 rows).
- Phylogenetic trees for the species in the dataset are available or can be constructed to enable PGLS analysis.