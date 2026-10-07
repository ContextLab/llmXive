# Feature Specification: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Feature Branch**: `001-visual-complexity-cognitive-load`
**Created**: 2023-10-27
**Status**: Draft
**Input**: User description: "How does the visual complexity of video meeting backgrounds affect cognitive load during remote work, and does this relationship persist when controlling for task difficulty and participant familiarity with the meeting content?"

## User Scenarios & Testing *(mandatory)*

### User Story 0 - Conduct Human Pilot Study for Metric Validation (Priority: P0)

The system must facilitate the recruitment of a small cohort of human participants (n=20) to rate a set of background images for perceived visual complexity. This data serves as the ground truth for validating the automated metrics.

**Why this priority**: Without empirical validation against human perception, the automated metrics (entropy, variance) are unproven proxies for cognitive load. This is a prerequisite for the main study.

**Independent Test**: Can be fully tested by running the pilot study interface, collecting 20 human ratings, and verifying that the resulting dataset meets the validation criteria described in FR-006.

**Acceptance Scenarios**:

1. **Given** a set of 50 background images, **When** 20 participants rate them for visual complexity on a 1-10 scale, **Then** the system stores the ratings linked to the image IDs.
2. **Given** the collected human ratings, **When** the system computes the automated metrics (entropy, variance, object count) and performs an exploratory factor analysis, **Then** it reports (a) a Pearson correlation coefficient **r ≥ 0.7** between the human scores and the aggregated automated metric, **b** the lower bound of the 95 % confidence interval for *r* is **≥ 0.6**, and **c** the factor analysis yields a single dominant factor (eigenvalue > 1) explaining ≥ 50 % of variance.
3. **Given** the validation results, **When** the Pearson *r* is below 0.7 **or** the confidence‑interval lower bound is below 0.6 **or** the factor analysis does not reveal a single dominant factor, **Then** the system flags the metric extraction pipeline for review before proceeding to the main study.
4. **Given** the pilot data, **When** the system generates a validation report, **Then** it includes the scatter plot of human scores vs. automated scores, the correlation statistics, the confidence interval, and the factor‑analysis summary.

---

### User Story 1 - Compute Visual Complexity Metrics (Priority: P1)

The system must process video meeting background frames to extract quantitative visual complexity metrics (image entropy, color variance, and object detection counts) to serve as the independent variable for the study.

**Why this priority**: Without accurate, automated measurement of the predictor variable (visual complexity), no correlation with cognitive load can be established. This is the foundational data generation step.

**Independent Test**: Can be fully tested by running the metric extraction script on a static set of diverse background images and verifying that the output JSON contains valid numerical values for entropy, variance, and object counts without errors.

**Acceptance Scenarios**:

1. **Given** a set of 50 simulated meeting background images with varying complexity, **When** the system processes them via the CPU‑compatible pipeline, **Then** it outputs a structured dataset containing entropy, color variance, and object detection counts for each image.
2. **Given** an image with a blank white background, **When** processed, **Then** the system reports near‑zero entropy and object count, validating the metric sensitivity to low‑complexity stimuli.
3. **Given** a CPU‑only environment (no GPU) and 10 input images at 1080p (1920x1080), H.264 encoded, **When** the YOLOv8n model runs inference on this batch, **Then** the process meets the performance constraints defined in NFR-001.
4. **Given** the pilot study dataset (US‑0), **When** the system ingests human‑rated complexity scores, **Then** it computes the correlation between human scores and automated metrics and reports the result.

---

### User Story 2 - Administer Cognitive Load Assessment (Priority: P2)

The system must present meeting clips to participants and capture their cognitive load response via the NASA‑TLX self‑report scale and a post‑task reaction‑time task. Additionally, the system must collect a **familiarity rating** (1 = not familiar, 5 = very familiar) for the meeting content before each clip.

**Why this priority**: This captures the dependent variables (subjective and objective cognitive load) required to test the hypothesis while controlling for participant familiarity.

**Independent Test**: Can be fully tested by simulating a participant session where a clip is shown, the familiarity rating, NASA‑TLX form, and the reaction‑time task are completed, verifying that the resulting data record links the participant ID, clip ID, familiarity rating, and response metrics correctly.

**Acceptance Scenarios**:

1. **Given** a participant viewing a specific meeting clip, **When** the clip ends, **Then** the system immediately presents the familiarity rating prompt, records the rating, then presents the NASA‑TLX questionnaire and records the score.
2. **Given** a participant performing a reaction‑time task *after* the clip, **When** the task completes, **Then** the system records the mean reaction time and accuracy percentage for that specific trial.
3. **Given** a participant with missing data on a specific trial, **When** the data is aggregated, **Then** the system flags the record for exclusion rather than imputing a default value.
4. **Given** a set of clips with varying complexity, **When** presented to a participant, **Then** the order of clips is counterbalanced to control for order effects.
5. **Given** a participant at the start of the session, **When** the session begins, **Then** the system administers a baseline reaction‑time task (low‑complexity or neutral stimulus) to establish a reference point for that participant.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system must execute linear mixed‑effects models to correlate visual complexity metrics with cognitive load outcomes, controlling for task difficulty, participant familiarity, and participant ID, while applying multiple‑comparison corrections and checking for multicollinearity. **Crucially, this stage distinguishes between 'Pipeline Validation' (using synthetic data to verify code correctness) and 'Primary Hypothesis Testing' (using real human data to answer the research question).**

**Why this priority**: This synthesizes the data to answer the research question, providing the final evidence for the gap analysis.

**Independent Test**:
1. **Pipeline Validation**: Can be tested by running the analysis script on a pre‑generated synthetic dataset with known correlations to verify the code executes correctly and reproduces expected parameters.
2. **Hypothesis Testing**: Can be tested by running the analysis script on the actual collected participant data (NASA‑TLX/reaction time) to produce the final inference on the research question.

**Acceptance Scenarios**:

1. **Given** the real human dataset collected in US‑2 (containing actual NASA‑TLX scores, reaction times, and familiarity ratings), **When** the linear mixed‑effects model is run, **Then** the output includes a fixed‑effect estimate for visual complexity with a 95 % confidence interval, a random intercept for participant ID, a random slope for visual complexity, and a random effect for trial order.
2. **Given** multiple hypothesis tests (e.g., testing entropy, variance, and object count separately), **When** the analysis completes, **Then** the system applies a Benjamini‑Hochberg correction and reports the adjusted p‑values.
3. **Given** the model results, **When** the report is generated, **Then** it explicitly states the effect size (Cohen’s d) and the direction of the association (positive/negative).
4. **Given** the set of predictors, **When** the model is prepared, **Then** the system calculates Variance Inflation Factors (VIF) for each; if any VIF > 5, the system either combines predictors via PCA or flags the instability in the report.
5. **Given** a synthetic dataset generated with a true null effect size (for pipeline validation only), **When** the system runs a null‑simulation, **Then** it calculates and reports the observed family‑wise error rate (FWER) to verify the code's ability to control Type I errors (target α = 0.05, see verified fact).
6. **Given** the sensitivity analysis sweep (alpha thresholds {a low significance level, 0.05, 0.1}), **When** the report is generated, **Then** it explicitly lists the count of significant predictors for each threshold and the standard deviation of the effect sizes.
7. **Scientific Validation**: **Given** the actual collected human data (NASA‑TLX scores, reaction times, familiarity), **When** the LMM is executed, **Then** the system outputs the final statistical inference regarding the *association* between visual complexity and cognitive load, distinguishing this from the synthetic pipeline validation.

---

### User Story 4 - Conduct Main Study with Real Human Participants (Priority: P3)

The system must orchestrate the collection of real human data to test the hypothesis, ensuring that the final analysis is based on empirical observations (NASA‑TLX, reaction time, familiarity) rather than synthetic simulations.

**Why this priority**: Synthetic data can validate code, but only real human data can answer the research question about cognitive load. This story ensures the study is scientifically valid.

**Independent Test**: Can be tested by recruiting a cohort of real participants, collecting their NASA‑TLX, reaction‑time, and familiarity data, and verifying that the final analysis report is generated from this real dataset, not a synthetic one.

**Acceptance Scenarios**:

1. **Given** a recruitment pool of real participants, **When** they complete the study, **Then** the system stores their real NASA‑TLX scores, reaction times, and familiarity ratings linked to the specific background complexity metrics.
2. **Given** the real dataset, **When** the statistical analysis (US‑3) is run, **Then** the output explicitly identifies the data source as “Real Human Data” and not “Synthetic Simulation”.
3. **Given** the real data, **When** the hypothesis test is concluded, **Then** the system outputs a definitive statement on whether an *association* between visual complexity and cognitive load was detected.

---

### Edge Cases

- **Scenario**: A video frame contains no detectable objects (e.g., a solid color wall).
- **Scenario**: A participant fails the attention check or submits incomplete NASA‑TLX responses.
- **Scenario**: The visual complexity metric distribution is highly skewed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute image entropy, color variance, and object detection counts for every background frame using a CPU‑compatible pipeline (See US‑1).
- **FR-002**: System MUST present meeting clips in a counterbalanced order and capture NASA‑TLX scores, post‑task reaction‑time metrics, and a pre‑clip familiarity rating for each participant (See US‑2).
- **FR-002b**: System MUST administer a baseline reaction‑time task (low‑complexity control condition) to every participant before the experimental trials to establish a reference point (See US‑2).
- **FR-002c**: System MUST generate a counterbalanced presentation order for the stimuli to control for order effects (See US‑2).
- **FR-003**: System MUST execute linear mixed‑effects models with background complexity as the predictor and cognitive load as the outcome, controlling for participant ID (random intercept), random slope for visual complexity, random effect for trial order, and participant familiarity as a fixed covariate; it MUST compute Variance Inflation Factors (VIF) to detect multicollinearity (See US‑3).
- **FR-004**: System MUST apply a multiple‑comparison correction (Benjamini‑Hochberg) when reporting significance for >1 hypothesis test (See US‑3).
- **FR-005**: System MUST perform a sensitivity analysis sweeping the p‑value significance threshold (α) over the set {0.01, 0.05, 0.1} and report the variation in the count of significant predictors (See US‑3).
- **FR-005b**: System MUST define ‘stability’ in the sensitivity analysis as the suite of results including both the count of significant predictors AND the standard deviation of the effect sizes across the swept thresholds (See US‑3).
- **FR-006**: System MUST ingest human‑rated complexity scores from the pilot study and compute (a) Pearson r ≥ 0.7, (b) 95 % CI lower bound ≥ 0.6, and (c) a single‑factor solution from exploratory factor analysis to validate the automated metrics (See US‑0, FR‑006).
- **FR-007**: System MUST run a null‑simulation (where the true effect size is 0) generated in‑pipeline by randomly drawing visual‑complexity metrics and TLX/RT outcomes; it then calculates and reports the observed family‑wise error rate (FWER) and compares it to the nominal α = 0.05 (See US‑3, FR‑007).
- **FR-008**: System MUST process ACTUAL collected participant data (NASA‑TLX scores, reaction times, familiarity) to produce the final hypothesis‑test inference, distinguishing this from synthetic validation (See US‑3, US‑4).
- **FR-009**: System MUST validate `data/derived/analysis_results.json` against the `analysis_result.schema.yaml` contract using automated schema tests (e.g., `pytest -m test_schemas.py`).
- **FR-010**: System MUST collect a participant familiarity rating (1–5) for each meeting content prior to clip presentation and store it with the trial record (See US‑2).
- **FR-011**: System MUST compute required sample size using a repeated‑measures F‑test power analysis (`statsmodels.stats.power.FTestPower`) targeting effect size d = 0.5, α = 0.05, power = 0.80, resulting in a minimum of **N = 60** participants (See Assumptions).

### Non‑Functional Requirements

- **NFR-001**: The visual complexity metric extraction pipeline MUST complete processing of 10 input images at 1080p (1920×1080) within 30 seconds and consume less than a modest amount of RAM on a CPU‑only environment.

## Key Entities *(include if the feature involves data)*

- **BackgroundFrame**: Represents a single frame from a meeting video.
 - **JSON Schema**:
 ```json
 {
 "type": "object",
 "properties": {
 "frame_id": { "type": "string" },
 "entropy": { "type": "number" },
 "color_variance": { "type": "number" },
 "object_count": { "type": "integer" }
 },
 "required": ["frame_id", "entropy", "color_variance", "object_count"]
 }
 ```
- **ParticipantSession**: Represents one participant's interaction with the study; attributes include NASA‑TLX score, reaction time, accuracy, baseline reaction time, familiarity rating, and associated background frames.
- **AnalysisResult**: Represents the output of the statistical model; attributes include fixed‑effect estimates, adjusted p‑values, confidence intervals, effect sizes, VIF scores, and FWER.
- **HumanRating**: Represents a human rating for a background image; attributes include image_id, participant_id, and complexity_score (1‑10).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Visual complexity metrics (entropy, variance, object count) are measured against human‑rated complexity scores from a pilot study (n = 20) and must achieve **Pearson r ≥ 0.7**, a **95 % CI lower bound ≥ 0.6**, and a **single‑factor solution** from factor analysis (See US‑0, FR‑006).
- **SC-002**: The system outputs a p‑value for the correlation between visual complexity and NASA‑TLX scores; the study concludes whether an *association* between visual complexity and cognitive load exists based on this data (See US‑3, US‑4).
- **SC-003**: The reaction‑time difference between high‑complexity and low‑complexity conditions is measured against the baseline reaction time (defined as the mean reaction time during the baseline condition for the same participant) to quantify the cognitive load impact (See US‑2, FR‑002b).
- **SC-004**: The system MUST apply a multiple‑comparison correction (Benjamini‑Hochberg) and report adjusted p‑values, ensuring the procedure controls the family‑wise error rate at the nominal **α = 0.05** as verified by the null‑simulation in FR‑007 (See US‑3, FR‑007, verified fact: α = 0.05 from arXiv 1505.06549).
- **SC-005**: The stability of the effect size is measured across the sensitivity analysis sweep (alpha thresholds {0.01, 0.05, 0.1}) by calculating the standard deviation of effect sizes to confirm robustness of the finding (See US‑3, FR‑005b).

## Assumptions

- The public dataset or synthetic generation method provides a sufficient number of distinct background clips with enough variance in visual complexity to support statistical power.
- Participants recruited via public platforms (e.g., Prolific) will have stable internet connectivity and can complete the post‑task cognitive task without technical interruption.
- The relationship between visual complexity and cognitive load is **associational** (observational study); no causal claims will be made without random assignment.
- The NASA‑TLX scale is a validated instrument for measuring cognitive load in this context (Hart & Staveland, 1988) and the self‑report data will be treated as the primary subjective metric.
- A power analysis using a repeated‑measures F‑test (`statsmodels.stats.power.FTestPower`) indicates that **N = 60** participants are required to detect an effect size **d > 0.5** with **power ≥ 0.80** at **α = 0.05**.
- Any decision cutoffs introduced during analysis (e.g., for outlier removal) will be justified by community standards and subjected to the required sensitivity analysis.
- The study requires real human participants for the main data collection; no synthetic data will be used for the primary outcome variables (NASA‑TLX, reaction time) in the final hypothesis test.

## Bibliography

- Benjamini, Y., & Hochberg, Y. (1995). *Controlling the false discovery rate: a practical and powerful approach to multiple testing*. Journal of the Royal Statistical Society: Series B (Methodological), 57(1), 289‑300. DOI: 10.1111/j.2517-6161.1995.tb02031.x
- Hart, S. G., & Staveland, L. E. (1988). *Development of NASA‑TLX (Task Load Index): Results of empirical and theoretical research*. In P. A. Hancock & N. Meshkati (Eds.), *Human mental workload* (pp. 139‑183). Amsterdam: North‑York Publishers.
- Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). *G*Power 3: A flexible statistical power analysis program for the social, behavioral, and biomedical sciences*. Behavior Research Methods, 39(2), 175‑191. DOI: 10.3758/BF03193146
- Benjamini, Y., & Hochberg, Y. (1995). *Controlling the false discovery rate: a practical and powerful approach to multiple testing*. Journal of the Royal Statistical Society. Series B (Methodological), 57(1), 289‑300. DOI:10.1111/j.2517-6161.1995.tb02031.x
- **Family‑wise error rate control reference**: 1505.06549, *“A simple and effective approach to control the family‑wise error rate”*, arXiv, https://arxiv.org/abs/1505.06549 (α = 0.05).
