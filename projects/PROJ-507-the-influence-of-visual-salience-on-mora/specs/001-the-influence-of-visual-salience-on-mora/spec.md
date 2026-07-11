# Feature Specification: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Feature Branch**: `001-visual-salience-moral-judgment`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does increasing the visual salience of non-causal elements in morally ambiguous simulated scenarios systematically shift participants' blame and responsibility judgments toward the visually highlighted party?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Salience Manipulation Pipeline (Priority: P1)

The system must load a curated, human-validated list of morally ambiguous scenarios from open visual datasets (e.g., Visual Genome, COCO), and programmatically generate variants with manipulated visual salience (low, medium, high) while preserving semantic content and perceptual realism.

**Why this priority**: This is the foundational step. Without a validated dataset of manipulated stimuli that are perceptually realistic, no survey can be deployed, and no empirical data can be collected. It directly enables the core research question.

**Independent Test**: A script can be run to process a sample of 5 images, generate 3 salience variants each, and output a manifest file linking original images to manipulated versions with verified pixel-level statistics (mean brightness, standard deviation, and SSIM) confirming the manipulation without semantic alteration or visible artifacts.

**Acceptance Scenarios**:

1. **Given** a source image from the Visual Genome dataset annotated as a "traffic accident" and included in the curated list, **When** the manipulation script runs with "high salience" parameters on a non-causal object (e.g., a red traffic cone), **Then** the output image must show increased contrast/brightness on the target object while the semantic content (vehicle positions, road layout) remains visually identical to the original, and the file is saved with a unique ID.
2. **Given** a set of [deferred] identified morally ambiguous scenarios, **When** the pipeline processes them, **Then** the system must output a CSV manifest containing the appropriate number of rows (scenarios × 3 salience levels) with columns for `scenario_id`, `salience_level`, `image_path`, and `pixel_stats`, ready for survey integration.

---

### User Story 2 - Survey Deployment and Data Collection (Priority: P2)

The system must deploy a survey interface where participants view the manipulated images and provide blame ratings on a 1-7 Likert scale, capturing the data in a structured format suitable for statistical analysis.

**Why this priority**: This enables the collection of the dependent variable (blame judgments). While the data pipeline (US-1) creates the stimuli, this story captures the human response required to test the hypothesis.

**Independent Test**: A survey link can be generated and opened in a browser; a test user can view an image, select a rating, submit, and the system must record the response in a local JSON/CSV file with the correct `scenario_id`, `salience_level`, and `user_id`.

**Acceptance Scenarios**:

1. **Given** a participant accessing the survey URL, **When** they view an image from the "medium salience" condition and select a rating of "5" on the 1-7 scale, **Then** the submission must record the response with a timestamp and link it to the specific image ID, ensuring no other data (e.g., demographic info) blocks the submission if the user chooses to remain anonymous.
2. **Given** a dataset of [deferred] completed responses, **When** the data export function is triggered, **Then** the output file must contain exactly the expected number of rows with no missing values in the `blame_rating` or `salience_level` columns, formatted for import into standard statistical libraries (e.g., pandas, R).

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system must execute a repeated-measures ANOVA to test the effect of salience on blame ratings, perform post-hoc pairwise comparisons with Bonferroni correction, and generate a report including effect sizes, confidence intervals, and power analysis.

**Why this priority**: This transforms raw data into scientific evidence. It directly answers the research question and fulfills the methodology requirements for validity and multiplicity control.

**Independent Test**: A script can be run on a synthetic dataset with known parameters (e.g., a simulated strong effect); the output must correctly identify the significant effect, report the F-statistic and p-value, and apply the Bonferroni correction to the pairwise comparisons.

**Acceptance Scenarios**:

1. **Given** a dataset of [deferred] participants with 3 salience conditions each, **When** the analysis script runs, **Then** it must output a summary table showing the F-statistic, degrees of freedom, and p-value for the main effect of salience, explicitly stating if the result is significant after Bonferroni correction.
2. **Given** a significant main effect in the ANOVA, **When** post-hoc tests are executed, **Then** the system must report pairwise comparisons (Low vs. Medium, Medium vs. High, Low vs. High) with adjusted p-values and 95% confidence intervals for the mean differences.

### Edge Cases

- What happens if the image manipulation algorithm fails to alter the pixel statistics significantly (e.g., target object is already pure white)? The system must flag the image as "invalid manipulation" and exclude it from the survey pool.
- How does the system handle participants who fail attention checks (e.g., selecting random ratings or failing a "select the red cone" check)? The system must automatically exclude these participants from the final analysis dataset.
- What happens if the dataset contains images where the "non-causal" element is actually ambiguous (e.g., a cone that blocks a lane)? The system must log these as "excluded due to semantic ambiguity" based on a pre-defined rule set.
- What happens if the manipulation creates visible artifacts (e.g., haloing, unnatural lighting)? The system must flag the image as "failed realism check" and exclude it from the survey pool.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse metadata from open visual datasets (e.g., Visual Genome, COCO) to load a curated, human-validated list of [deferred] morally ambiguous scenarios, explicitly citing the source dataset for each image (See US-1).
- **FR-002**: System MUST apply image processing algorithms (PIL/OpenCV) to enhance contrast/brightness of target non-causal objects across three distinct levels (low, medium, high) while maintaining a pixel-level similarity score of [deferred] for non-target regions and ensuring no visible artifacts are introduced (See US-1).
- **FR-003**: System MUST deploy a survey interface that presents images in a randomized order using a Latin Square counterbalancing design and captures blame ratings on a 1-7 Likert scale for each manipulated variant (See US-2).
- **FR-004**: System MUST store collected survey responses in a structured format (CSV/JSON) linking `user_id`, `scenario_id`, `salience_level`, and `blame_rating` without storing personally identifiable information (See US-2).
- **FR-005**: System MUST execute a repeated-measures ANOVA to test the main effect of salience on blame ratings, followed by post-hoc pairwise comparisons with Bonferroni correction for multiple comparisons (See US-3).
- **FR-006**: System MUST calculate and report post-hoc statistical power using a simulation-based method and 95% confidence intervals for partial eta-squared (ηp²) effect sizes, ensuring the analysis is interpretable even if the null hypothesis is not rejected (See US-3).
- **FR-007**: System MUST include a validation step to assess perceptual realism of manipulated images (e.g., via a pre-test panel or artifact detection metric) and exclude any stimuli that appear unnatural or "photoshopped" (See US-1).

### Key Entities

- **Scenario**: A morally ambiguous visual event (e.g., traffic accident) identified from a public dataset, characterized by `scenario_id` and `semantic_annotations`.
- **Stimulus**: A specific image variant generated from a Scenario, characterized by `stimulus_id`, `scenario_id`, `salience_level` (low/medium/high), and `pixel_statistics`.
- **Response**: A single data point representing a participant's judgment, characterized by `response_id`, `stimulus_id`, `user_id`, `blame_rating`, and `timestamp`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The effect of visual salience on blame ratings is measured against the null hypothesis of no difference across salience levels using repeated-measures ANOVA (See US-3).
- **SC-002**: The false-positive rate for pairwise comparisons is measured against the Bonferroni-corrected alpha level (0.05 / number of comparisons) to ensure family-wise error control (See US-3).
- **SC-003**: The statistical power of the study is measured against the planned sample size to ensure achieved power ≥ 0.80 for detecting the expected effect size (See US-3).
- **SC-004**: The validity of the visual manipulation is measured against the pixel-level similarity score ([deferred] for non-target regions) and the absence of visible artifacts to ensure semantic content remains constant (See US-1).

## Assumptions

- The open visual datasets (Visual Genome, COCO) contain sufficient annotations to identify a set of morally ambiguous scenarios suitable for manipulation, which will be curated by human annotators.
- The "non-causal" elements in the identified scenarios can be isolated and manipulated without altering the semantic interpretation of the event (e.g., a red cone can be brightened without changing the perception of the accident), subject to the perceptual realism check.
- The survey platform (Qualtrics free tier or Google Forms) supports the required randomization and data export features without cost or technical barriers.
- The statistical analysis can be performed on a CPU-only environment (GitHub Actions free tier) using standard Python libraries (scipy, statsmodels) without requiring GPU acceleration.
- The sample size of [deferred] participants is estimated to be sufficient to achieve a statistical power of ≥ 0.80 for a medium effect size (Cohen's f ≈ 0.25), assuming a within-subject design.
- The Bonferroni correction is appropriate for controlling the family-wise error rate given the small number of pairwise comparisons (3 comparisons).
- A Latin Square counterbalancing design effectively controls for order effects in the repeated-measures survey.