# Feature Specification: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

**Feature Branch**: `001-cognitive-mechanisms-moral-judgments`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Research question: How does the visual salience of avatars’ emotional expressions in immersive virtual environments modulate the activation of specific moral foundations and shape intuitive moral judgments? Methodology: Bayesian decision modeling on VR experiment data. Primary data sources: MFQ dataset (OSF) and Moral Stories dataset (HuggingFace)."

## User Scenarios & Testing

### User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1)

The system MUST ingest raw data from the Open Science Framework (MFQ dataset) and the HuggingFace "Moral Stories" dataset, construct the experimental VR conditions by mapping text stories to VR scenes with controlled blend-shape parameters (low vs. high salience), and ingest actual VR interaction logs (response times, gaze tracking, in-VR judgment inputs). This is the foundational step; without clean, aligned, and experimentally constructed data, no modeling or analysis can occur.

**Why this priority**: This is the critical path for any empirical study. If data cannot be loaded, cleaned, experimentally constructed, or matched to VR conditions, the research question cannot be addressed.

**Independent Test**: The pipeline can be tested by running the ingestion and construction scripts against a small, static sample of the MFQ and Moral Stories datasets and verifying that the output CSV contains correctly merged rows with valid salience labels (constructed via blend-shape mapping), VR interaction logs, and no missing values for key predictors.

**Acceptance Scenarios**:

1. **Given** the raw MFQ and Moral Stories datasets are available in the local cache, **When** the ingestion script is executed, **Then** a unified CSV file is generated with columns for `participant_id`, `salience_level`, `foundation_scores`, `judgment_rating`, `response_time`, and `gaze_metrics` with no null values in required fields.
2. **Given** a participant record with mismatched IDs between the MFQ and judgment logs, **When** the preprocessing step runs, **Then** the record is flagged and excluded from the final analysis dataset, logging the exclusion reason.
3. **Given** the Unity VR scene metadata (salience levels), **When** mapped to the Moral Stories dataset, **Then** each story is correctly tagged with its corresponding `salience_level` (low or high) based on the experimental design, ensuring the text-to-VR transformation is explicitly defined.

---

### User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

The system MUST execute a Bayesian decision model on the preprocessed data to estimate the effect of visual salience on moral foundation activation. The model must treat foundation scores as covariates (moderators) and salience as a fixed-effect predictor on the mean. It must compare this model against a baseline (no salience) using AIC/WAIC to determine if salience provides strong evidence of improvement (ΔAIC > 10).

**Why this priority**: This addresses the core hypothesis. The research question hinges on whether the salience-augmented model outperforms the baseline and if salience modulates activation independent of pre-existing traits.

**Independent Test**: The model execution can be tested by running the PyMC3 script on a subset of data (e.g., 50 participants) and verifying that the model converges, produces posterior distributions, and calculates a ΔAIC value that is comparable to the full run.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset with 200 participants, **When** the Bayesian model is fitted on a CPU-only environment, **Then** the model converges (R-hat < 1.05) within 4 hours and outputs posterior distributions for the salience coefficient.
2. **Given** the fitted salience-augmented model and the baseline model, **When** model comparison metrics are calculated, **Then** the system reports the ΔAIC and ΔWAIC values, explicitly indicating if ΔAIC > 10 (strong evidence).
3. **Given** the posterior distributions, **When** posterior predictive checks (PPC) are performed, **Then** the generated data visually matches the observed data distribution for moral judgment ratings.

---

### User Story 3 - Statistical Validation and Reporting (Priority: P3)

The system MUST perform hierarchical mixed-effects regression to test the interaction between salience level and foundation-specific scores (moderation analysis), applying Bonferroni correction for multiple comparisons, and generate a final report summarizing the findings.

**Why this priority**: This provides the statistical rigor required to validate the interaction effect and ensures the results are not artifacts of multiple testing.

**Independent Test**: The validation step can be tested by running the regression on the full dataset and verifying that the p-values for the interaction terms are correctly adjusted and that the final report includes a sensitivity analysis of the decision threshold.

**Acceptance Scenarios**:

1. **Given** the model coefficients, **When** the mixed-effects regression is run, **Then** the interaction term (salience × foundation) is reported with a Bonferroni-corrected p-value.
2. **Given** a decision threshold for "strong evidence" (e.g., ΔAIC > 10), **When** the sensitivity analysis is run, **Then** the system reports the model selection stability across thresholds {2, 10, 20} as required by methodological soundness.
3. **Given** the final results, **When** the report is generated, **Then** it includes a clear statement of the findings, citing the specific statistical metrics (ΔAIC, p-value) and whether the evidence supports the hypothesis.

### Edge Cases

- What happens if the MFQ dataset is missing specific foundation scores for a participant? (System excludes the participant from foundation-weighted analysis but retains them for general judgment analysis if possible).
- How does the system handle a scenario where the Bayesian model fails to converge within the 4-hour CPU limit? (System logs the failure, reports the maximum likelihood estimate as a fallback, and flags the run as "inconclusive" for that participant).
- What if the Unity VR scene fails to render the high-salience expression correctly? (The system logs the error and excludes the corresponding vignette from the analysis, ensuring data integrity).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and merge the MFQ dataset and Moral Stories dataset, ensuring alignment of participant IDs and experimental conditions (See US-1).
- **FR-002**: System MUST implement a Bayesian decision model in PyMC3 that uses a Gaussian likelihood, Normal priors for coefficients, and treats participant-specific foundation scores as covariates (moderators) while using salience level as a fixed-effect predictor on the mean. The decision rule must be based on the posterior probability of the salience effect being greater than 0 (See US-2).
- **FR-003**: System MUST calculate model comparison metrics (AIC, WAIC) to compare the salience-augmented model against a baseline model (See US-2).
- **FR-004**: System MUST perform hierarchical mixed-effects regression to test the interaction between salience level and foundation scores (moderation analysis), applying Bonferroni correction for multiple comparisons (See US-3).
- **FR-005**: System MUST conduct a sensitivity analysis sweeping the decision threshold (ΔAIC) over {2, 10, 20} and report the model selection stability (See US-3).
- **FR-006**: System MUST capture and process actual VR interaction data, including response times, gaze tracking, and in-VR judgment inputs, and construct the experimental salience variable by mapping text stories to VR scenes with controlled blend-shape parameters (low vs. high salience) (See US-1).

### Key Entities

- **Participant**: Represents an individual user, containing attributes for MFQ scores, salience condition, moral judgment ratings, response times, and gaze metrics.
- **Vignette**: Represents a moral scenario mapped to a VR scene, containing attributes for story ID, salience level (low/high), associated foundation activation, and blend-shape parameters.
- **ModelResult**: Represents the output of the Bayesian inference, containing posterior distributions, AIC/WAIC scores, and convergence diagnostics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Model convergence rate is measured against the standard Bayesian inference benchmark (R-hat < 1.05) for the PyMC3 implementation (See US-2).
- **SC-002**: Model fit improvement (ΔAIC) is measured against the baseline model to determine if the salience-augmented model provides strong evidence of improvement (ΔAIC > 10) (See US-2).
- **SC-003**: Interaction significance is measured by the correct computation and reporting of the Bonferroni-corrected p-value (See US-3).
- **SC-004**: Sensitivity analysis coverage is measured against the required threshold set {2, 10, 20} to ensure robustness of the decision boundary (See US-3).

## Assumptions

- The Open Science Framework (OSF) dataset for the Moral Foundations Questionnaire (MFQ) will be accessible and contain the necessary variables (foundation scores) for all recruited participants.
- The "Moral Stories" dataset on HuggingFace will be compatible with the Unity VR vignette mapping, requiring the system to explicitly construct the salience variable via text-to-VR transformation (mapping text to specific VR scenes with controlled blend-shapes).
- The GitHub Actions free-tier runner (multi-core CPU, adequate RAM) is sufficient to run the PyMC Bayesian model on a sample of 200 participants within the 6-hour limit., assuming no GPU acceleration is required.
- The Unity Asset Store VR scene ("VR Classroom") will provide the necessary blend-shape parameters to manipulate avatar expressions between "low" and "high" salience without requiring custom 3D asset creation.
- Participants recruited via Prolific will have access to WebXR-compatible browsers and the necessary hardware (VR headset or compatible display) to experience the vignettes as intended.
- The Bayesian model will use default precision (float64) and will not require 8-bit or 4-bit quantization, which would necessitate CUDA hardware not available on the free-tier runner.
- The "Moral Stories" dataset will contain enough distinct scenarios to support the experimental design without requiring data augmentation or synthetic generation.
- The Bonferroni correction will be applied to the specific set of hypothesis tests defined in the methodology (interaction tests for each moral foundation), and the number of tests will not exceed the computational capacity of the free-tier runner.
- The sensitivity analysis thresholds {2, 10, 20} are sufficient to demonstrate the robustness of the decision boundary, as per community standards for Bayesian model comparison.
- The Unity VR scene will be downloadable and runnable on the GitHub Actions runner or a local machine for testing, with no licensing restrictions preventing automated access.
- The VR client and data collection pipeline are part of the system scope and will be constructed to capture the necessary interaction data.