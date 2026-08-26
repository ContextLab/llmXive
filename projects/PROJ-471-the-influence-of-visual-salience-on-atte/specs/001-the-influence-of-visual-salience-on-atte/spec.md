# Feature Specification: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Feature Branch**: `001-influence-of-visual-salience`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "The Influence of Visual Salience on Attentional Bias in Moral Judgements"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Salience Map Generation (Priority: P1)

The researcher downloads the "Moral Foundations Eye-Tracking Dataset" (OpenNeuro dsXXXX), extracts the 200 stimulus images, and generates pixel-wise computational salience maps using the DeepGaze II model for every image.

**Why this priority**: This is the foundational data preparation step. Without successfully computing salience maps that align with the stimulus images, no correlation analysis with eye-tracking data can occur. It establishes the predictor variable required for the entire study.

**Independent Test**: The system can be tested by running the ingestion pipeline on a small subset of images and verifying that a salience map file (e.g., `.npy` or `.png`) is generated for each image with spatial resolution matching the original stimulus, and that the DeepGaze II model loads without requiring GPU resources.

**Acceptance Scenarios**:
1. **Given** the OpenNeuro dataset is downloaded locally, **When** the ingestion script processes the first 5 stimulus images, **Then** 5 salience map files are generated with spatial resolution (height/width) matching the source images.
2. **Given** a standard GitHub Actions free-tier runner (CPU-only), **When** the DeepGaze II model is initialized and run, **Then** the process completes without CUDA errors and consumes less than 7 GB of RAM.

### User Story 2 - Attention Metric Extraction and Alignment (Priority: P2)

The researcher parses the raw eye-tracking data to extract fixation metrics (first-fixation probability, dwell time, latency) for predefined morally relevant regions (faces, weapons) and aligns these metrics with the corresponding salience scores for each trial.

**Why this priority**: This step constructs the outcome variable. It transforms raw gaze coordinates into the specific dependent variables (attention allocation) required to test the hypothesis against the salience predictor.

**Independent Test**: The system can be tested by processing a single trial's eye-tracking data and verifying that the output includes a row in the analysis dataframe containing the trial ID, the calculated dwell time on the target region, and the mean salience score for that same region.

**Acceptance Scenarios**:
1. **Given** a raw eye-tracking file for one participant, **When** the preprocessing script runs, **Then** it outputs a structured CSV containing fixation metrics (onset, duration, location) filtered to the defined "morally relevant regions."
2. **Given** a specific stimulus image, **When** the alignment script runs, **Then** it correctly merges the computed salience score for the target region with the eye-tracking metrics for that specific image, ensuring no trial ID mismatches.

### User Story 3 - Statistical Modeling and Robustness Verification (Priority: P3)

The researcher fits linear mixed-effects models to test the predictive relationship between salience and attention, applies multiple-comparison corrections, and performs a sensitivity analysis on the model specification.

**Why this priority**: This delivers the core scientific finding. It answers the research question by quantifying the relationship while controlling for confounds and validating the robustness of the statistical inference.

**Independent Test**: The system can be tested by running the analysis script on the prepared dataset and verifying that a regression summary is produced with p-values for the salience predictor, and that a sensitivity analysis plot is generated showing result stability across model variations.

**Acceptance Scenarios**:
1. **Given** the aligned dataset of 200 images, **When** the mixed-effects model is fitted, **Then** the output includes a fixed-effect estimate for salience with a p-value, and random intercepts for participants and items.
2. **Given** the primary regression result, **When** the sensitivity analysis runs, **Then** it reports the change in the headline association rate across the comparison of Model A (random intercepts only) and Model B (random intercepts and slopes for salience).

### Edge Cases

- What happens if the OpenNeuro dataset contains missing fixation data for a specific trial? (System must exclude the trial from the analysis and log a warning).
- How does the system handle images where the "morally relevant region" mask is empty or invalid? (System must skip the salience aggregation for that region and flag the image for manual review).
- What if the DeepGaze II model fails to converge on a specific high-contrast image? (System must fall back to a simpler heuristic salience calculation or exclude the image, ensuring the pipeline does not crash).

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute pixel-wise salience maps for all 200 stimulus images using the DeepGaze II model in CPU-only mode (See US-1).
- **FR-002**: System MUST parse raw eye-tracking data to extract first-fixation probability, dwell time, and fixation latency for predefined morally relevant regions (See US-2).
- **FR-003**: System MUST align the computed salience scores with the extracted eye-tracking metrics on a per-trial basis using unique trial identifiers (See US-2).
- **FR-004**: System MUST fit a linear mixed-effects model with salience as a fixed predictor and random intercepts for participants and items (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis by comparing Model A (random intercepts only) and Model B (random intercepts and slopes for salience) and reporting the variation in effect significance (See US-3).
- **FR-006**: System MUST apply False Discovery Rate (FDR) correction to all reported p-values (See US-3).
- **FR-007**: System MUST append a disclaimer block containing the phrase "correlational only" to all machine-readable output artifacts (JSON, CSV) containing p-values < 0.05 (See US-3).
- **FR-008**: System MUST generate semantic masks for "faces" and "weapons" using an ensemble of YOLOv8 (for faces) and Detectron2 (for weapons) if pre-segmented masks are not provided in the dataset (See US-2).
- **FR-009**: System MUST include low-level visual features (luminance, contrast, edge density) as covariates in the linear mixed-effects model to control for confounding visual properties (See US-3).

### Key Entities

- **StimulusImage**: Represents one of the 200 moral-scenario images; attributes include ID, file path, and computed salience map.
- **FixationTrial**: Represents a single viewing event; attributes include ParticipantID, StimulusID, RegionOfInterest, DwellTime, and FirstFixation.
- **AnalysisResult**: Represents the output of the statistical model; attributes include FixedEffectEstimate, PValue, ConfidenceInterval, and SensitivitySweepData.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of successfully generated salience maps is measured against the total number of stimulus images (200) (See FR-001, US-1).
- **SC-002**: The computational resource usage (RAM and CPU time) for the salience generation step is measured against the GitHub Actions free-tier limits (7 GB RAM, 6 hours) (See FR-001, US-1).
- **SC-003**: The statistical significance of the salience predictor in the mixed-effects model is measured against the adjusted alpha level (after FDR correction) AND the study power must be ≥ 0.8; if power < 0.8, the study is deemed "Invalid for inference" regardless of p-value (See FR-006, US-3).
- **SC-004**: The stability of the headline association rate is measured across the comparison of Model A and Model B to ensure robustness (See FR-005, US-3).
- **SC-005**: The proportion of trials successfully aligned is measured against the total available trials (target: [deferred]) (See FR-003, US-2).
- **SC-006**: The collinearity diagnostic (Variance Inflation Factor) for predictors is measured against established standard thresholds to ensure independent predictive effects are not claimed (See Methodological Soundness).

## Assumptions

- The "Moral Foundations Eye-Tracking Dataset" (OpenNeuro ds003123) contains the specific variables required for the analysis (predictor: image properties; outcome: eye-tracking fixation; covariates: stimulus complexity) without missing critical data fields.
- The DeepGaze II model can be executed on a CPU-only runner with a maximum of 2 cores and 7 GB RAM within the 6-hour job limit, potentially requiring data sampling or model simplification if full-batch inference exceeds these bounds.
- The predefined "morally relevant regions" (e.g., faces, weapons) can be reliably segmented using the specified ensemble of YOLOv8 and Detectron2 without manual annotation.
- The study design is observational; therefore, any significant relationship found will be interpreted as an association between visual salience and attentional allocation, not a causal effect of salience on moral judgment.
- The sample size provides sufficient statistical power (≥ 0.8) to detect a moderate effect size in a mixed-effects model; if power is calculated to be < 0.8, the study is considered invalid for inference.