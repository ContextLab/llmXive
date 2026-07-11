# Feature Specification: llmXive follow-up: extending "Edit-Compass & EditReward-Compass: A Unified Benchmark for Image Editing"

**Feature Branch**: `001-llmxive-followup-correlation-study`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "Does the human preference score for complex image edits correlate more strongly with the semantic logic consistency of the edit than with the pixel-level fidelity?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Filtering (Priority: P1)

The system MUST download the Edit-Compass dataset (up to 2,388 instances) and filter it to retain only instances labeled under "World Knowledge Reasoning" and "Visual Reasoning" categories.

**Why this priority**: This is the foundational step; without the specific subset of data relevant to the hypothesis, no analysis can be performed. It delivers the raw material required for the entire study.

**Independent Test**: Can be fully tested by executing the download and filter script and verifying that the output directory contains only images and metadata matching the "World Knowledge" or "Visual Reasoning" labels, with a count > 0.

**Acceptance Scenarios**:

1. **Given** the GitHub Actions runner has network access, **When** the download script executes, **Then** the `edit-compass` dataset files are present in the working directory.
2. **Given** the full dataset is downloaded, **When** the filtering logic runs, **Then** the output subset contains only instances where the `category` field matches "World Knowledge Reasoning" or "Visual Reasoning".
3. **Given** the filtered subset is generated, **When** the system reports the count, **Then** the count is a positive integer representing the valid samples for analysis.

---

### User Story 2 - Automated Scoring Generation (Priority: P2)

The system MUST compute two distinct scores for each filtered instance: a **Logic Consistency Score** (using a CPU-optimized Vision-Language Model) and a **Fidelity Score** (using SSIM and LPIPS metrics).

**Why this priority**: This implements the core measurement mechanism of the study. It transforms raw images and text into the quantitative variables required for the regression analysis.

**Independent Test**: Can be fully tested by processing a small batch of known images and verifying that the output JSON contains valid numeric values (between 0 and 1 or -1 and 1) for both logic and fidelity scores, with no nulls.

**Acceptance Scenarios**:

1. **Given** a filtered instance with a source image, edited image, and instruction, **When** the scoring module runs, **Then** a **Logic Consistency Score** is generated via cosine similarity between the embedding of the *intended instruction* and the embedding of the *VLM-generated description of the actual edit*.
2. **Given** a filtered instance with source and edited images, **When** the fidelity module runs, **Then** a **Fidelity Score** is generated as a weighted average (0.5/0.5) of SSIM and (1 - LPIPS), measuring background preservation.
3. **Given** the batch processing completes, **When** the system logs the output, **Then** every instance in the batch has both scores recorded, and the total memory usage remains within the 7 GB limit.

---

### User Story 3 - Statistical Correlation Analysis (Priority: P3)

The system MUST perform a preliminary independence check, followed by a multiple linear regression analysis to determine the correlation strength between the Human Judgment Score (target) and the two predictors (Logic Consistency Score and Fidelity Score), including multiplicity correction.

**Why this priority**: This delivers the final scientific insight. It synthesizes the computed scores and the ground truth to answer the research question regarding which factor drives human preference, while validating the independence of the metrics.

**Independent Test**: Can be fully tested by running the analysis script on the generated scores and verifying that a regression summary is produced with standardized beta coefficients, p-values, and a corrected significance level, preceded by an independence check report.

**Acceptance Scenarios**:

1. **Given** the dataset with Human Judgment, Logic, and Fidelity scores, **When** the preliminary check runs, **Then** the system reports the correlation between Human Score and Logic Score to verify independence.
2. **Given** the independence check passes, **When** the regression model runs, **Then** the output includes standardized beta coefficients for both predictors.
3. **Given** multiple hypothesis tests are performed (e.g., testing both predictors), **When** the analysis completes, **Then** a Benjamini-Hochberg (FDR ≤ 0.05) correction is applied to the p-values.
4. **Given** the final results, **When** the report is generated, **Then** it explicitly states which predictor has the stronger independent effect on human preference based on the partial correlation values.

---

### Edge Cases

- What happens if the Edit-Compass dataset download fails or the file structure differs from the expected format? (System must exit with a clear error code and log the specific missing file).
- How does the system handle instances where the VLM fails to generate a description due to timeout or memory constraints? (Instance must be skipped, logged, and excluded from the final regression to prevent data corruption).
- How does the system handle cases where the Human Judgment Score is missing for a specific instance? (Instance must be excluded from the analysis, and the exclusion count must be reported).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the Edit-Compass dataset (up to 2,388 instances) and associated model outputs from the official repository using `wget` or `curl`. (See US-1)
- **FR-002**: System MUST filter the dataset to retain only instances labeled under "World Knowledge Reasoning" and "Visual Reasoning" categories. (See US-1)
- **FR-003**: System MUST compute a **Logic Consistency Score** for each instance by extracting the edit instruction, generating a description of the actual edit via a CPU-optimized Vision-Language Model (e.g., `phi-3-mini`), and calculating cosine similarity between the embedding of the *intended instruction* and the embedding of the *VLM-generated description of the actual edit* using the `all-MiniLM-L6-v2` model with L2-normalized vectors. (See US-2)
- **FR-004**: System MUST compute a **Fidelity Score** for each instance by calculating SSIM and LPIPS between the source and edited images, inverting LPIPS (1 - LPIPS) to align directionality, and aggregating them into a normalized weighted average (0.5 × SSIM + 0.5 × (1 - LPIPS)) to measure background preservation. (See US-2)
- **FR-005**: System MUST perform a preliminary independence check by calculating the Pearson correlation coefficient between the Human Judgment Score and the Logic Consistency Score; if |r| ≥ 0.5, the system MUST flag a potential circular validation risk and halt the main regression. (See US-3)
- **FR-006**: System MUST perform a multiple linear regression where the dependent variable is the Human Judgment Score and independent variables are the Logic Consistency Score and Fidelity Score. (See US-3)
- **FR-007**: System MUST apply the Benjamini-Hochberg (FDR ≤ 0.05) method to the p-values derived from the regression analysis to control the false discovery rate. (See US-3)
- **FR-008**: System MUST process data in batches to ensure total memory usage does not exceed 7 GB RAM during execution. (See US-2)

### Key Entities

- **EditInstance**: Represents a single data point containing the source image, edited image, edit instruction, category label, and human judgment score.
- **ScoreRecord**: Represents the computed metrics for an instance, including the Logic Consistency Score, Fidelity Score, and the derived statistical significance values.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation coefficient between Human Preference and Logic Consistency Score must exceed the correlation between Human Preference and Fidelity Score by at least 0.1, with a p-value < 0.05 for the difference, to confirm Logic is the stronger predictor. (See FR-006)
- **SC-002**: The statistical significance of the predictors is measured against a corrected alpha threshold (FDR ≤ 0.05 via Benjamini-Hochberg) to ensure findings are not due to chance. (See FR-007)
- **SC-003**: The analysis runtime is measured against the explicit time limit of 6 hours to ensure feasibility on the GitHub Actions free-tier runner. (See FR-008)
- **SC-004**: The memory consumption is measured against a predefined RAM limit of 7 GB during the peak of the VLM inference batch to ensure stability. (See FR-008)
- **SC-005**: The dataset variable fit is measured by verifying that the Edit-Compass dataset contains all required variables (instruction, source image, edited image, human score, category) for the analysis; if any are missing, the system MUST report a specific error and halt. (See FR-001)

## Assumptions

- **Assumption about Data Availability**: The official Edit-Compass repository contains the full [deferred] instances with the "World Knowledge Reasoning" and "Visual Reasoning" labels intact and accessible via public URL.
- **Assumption about Compute Resources**: The GitHub Actions free-tier runner (standard CPU allocation, 7 GB RAM) is sufficient to run the `phi-3-mini` (or similar distilled) VLM in CPU mode for the maximum expected instance count ([deferred]) in batches without exceeding the 6-hour time limit.
- **Assumption about Methodology**: The "Human Judgment Score" provided in the Edit-Compass benchmark is mathematically independent of the automated metrics (SSIM/LPIPS) and VLM embeddings generated by this script, ensuring no circular validation (verified by FR-005).
- **Assumption about Inference Framing**: Since the study uses an observational dataset (no random assignment of edits), all findings regarding correlation will be framed as associational, not causal, in the final report.
- **Assumption about Threshold Justification**: No arbitrary decision cutoffs (e.g., for "high" vs "low" logic) are introduced in the analysis; the regression approach treats scores as continuous variables, avoiding the need for sensitivity analysis on binary thresholds.
- **Assumption about Predictor Collinearity**: While Logic and Fidelity are conceptually distinct, if a high correlation is found between the two predictors themselves, the regression output will report Variance Inflation Factors (VIF) to diagnose collinearity, and the interpretation will be adjusted to reflect joint effects rather than independent causality.