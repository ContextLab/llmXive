# Feature Specification: Visual Detail and False Memory Susceptibility

**Feature Branch**: 001-visual-detail-false-memory  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "The Impact of Visual Detail on False Memory Susceptibility"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Image Manipulation Pipeline (Priority: P1) (See US-1)

Researcher uploads baseline images from Visual Genome and receives two manipulated versions per image: (a) enhanced detail (a small number of minor objects added via compositing) and (b) reduced detail (minor elements blurred/removed).

**Why this priority**: This is the foundation of the entire experiment—without stimulus manipulation, no false memory test can occur. The pipeline must work reliably before any participant testing.

**Independent Test**: Can be fully tested by running the image manipulation script on multiple sample images and verifying output files exist with correct detail modifications, without requiring participants or statistical analysis.

**Acceptance Scenarios**:

1. **Given** a selection of baseline images from Visual Genome, **When** researcher runs the manipulation script, **Then** multiple output images are created (enhanced and reduced detail versions per baseline) (Visual Genome, n.d.).
2. **Given** an enhanced‑detail image, **When** visual inspection occurs, **Then** at least **2 additional minor objects** are present compared to baseline **and** the structural‑similarity index (SSIM) between baseline and enhanced image is **≤ 0.95**.
3. **Given** a reduced‑detail image, **When** visual inspection occurs, **Then** minor elements are blurred or removed compared to baseline.

---

### User Story 2 - Participant Testing Interface (Priority: P2) (See US-2)

Participant views a BASELINE image for a brief period, completes a short arithmetic distractor task, then answers a set of recognition‑style questions about scene details (a mix of true details from the baseline and false/lure details that never appeared in the baseline image).

**Why this priority**: This is the core data collection mechanism. Without valid participant responses, no statistical analysis can occur. However, the interface can be tested independently of the manipulation pipeline.

**Independent Test**: Can be fully tested by simulating a single participant session end‑to‑end (image display → distractor → questions → response capture) and verifying all responses are recorded correctly.

**Acceptance Scenarios**:

1. **Given** a baseline image is loaded, **When** participant views it, **Then** display duration is **10 seconds ± 0.5 seconds**.
2. **Given** the distractor task begins, **When** participant completes arithmetic questions, **Then** task duration is **2 minutes ± 10 seconds**.
3. **Given** the recognition test begins, **When** participant answers all questions, **Then** all responses are recorded with timestamps and participant ID, **and** each lure item is verified against the stimulus metadata to confirm it does **not** appear in the baseline image (see FR‑013).

**Scope Clarification**: Recognition‑only testing is sufficient for the research question; recall testing is out of scope for v1.

---

### User Story 3 - Statistical Analysis and Results Generation (Priority: P3) (See US-3)

System executes repeated‑measures analysis comparing false‑memory susceptibility across detail conditions and generates visualization with confidence intervals.

**Why this priority**: This delivers the research findings but depends on both image manipulation and participant data being collected first. Can be tested independently once sample data exists.

**Independent Test**: Can be fully tested by running the analysis script on synthetic/mock participant data and verifying analysis results and visualization are generated within **30 minutes**.

**Acceptance Scenarios**:

1. **Given** a sufficient number of participant response records, **When** analysis script executes, **Then** the primary analysis (**FR‑005**) fits a **generalized linear mixed‑effects model (binomial logit)** using statsmodels (or equivalent) with random intercepts for participants and items, and outputs fixed‑effect estimates, standard errors, and p‑values for the visual‑detail condition. A secondary descriptive analysis (**FR‑005a**) performs a **Repeated‑Measures ANOVA** on **arcsine‑sqrt transformed** false‑memory rates, after checking normality and homoscedasticity assumptions, and reports the ANOVA table.
2. **Given** analysis completes, **When** visualization is generated, **Then** plot shows mean false memory rates with confidence intervals for each condition (enhanced, reduced, baseline). The GLMM includes **condition order** as a covariate (see FR‑015).
3. **Given** multiple hypothesis tests are run, **When** correction is applied, **Then** family‑wise error rate is controlled using **Bonferroni** (or Holm) method and documented (see FR‑006).

---

### Edge Cases

- What happens when Visual Genome image metadata is missing or incomplete? System MUST skip that image and log the error rather than crashing.
- How does system handle participant dropout mid‑session? System MUST record partial responses and flag incomplete sessions in the dataset.
- What happens when image manipulation fails for a specific image? System MUST skip that image, log the failure, and continue with remaining images (minimum **30 baseline images required for production analysis; a sufficient number of images for validation testing**).
- How does system handle network timeout during participant testing? System MUST cache responses locally and retry submission with **exponential backoff** (max **3 attempts**, intervals **1 s, 2 s, 4 s**). This behavior is verified by **FR‑014**.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download a representative sample of images from Visual Genome dataset with varied baseline complexity scores spanning **≥3 quantile bins** (Q1‑Q3 range ≥ 0.3) and reuse each baseline image across all three detail conditions (baseline, enhanced, reduced) for every participant (See US‑1)
- **FR-002**: System MUST create two manipulated versions per baseline image: (a) enhanced detail adding **≥2 minor objects via compositing** and meeting **SSIM ≤ 0.95** relative to baseline, (b) reduced detail blurring/removing minor elements (See US‑1)
- **FR-003**: System MUST display each baseline image for **10 seconds ± 0.5 seconds** before advancing to distractor task (See US‑2)
- **FR-004**: System MUST administer a set of recognition questions per session: a balanced set of **20 true‑detail** and **20 lure‑detail** items per stimulus (See US‑2)
- **FR-005**: System MUST execute a **generalized linear mixed‑effects model (binomial logit)** comparing false‑memory rates across detail conditions using statsmodels (or equivalent) with random effects for participants and items (See US‑3)
- **FR-005a**: System MUST perform a **Repeated‑Measures ANOVA** on **arcsine‑sqrt transformed** false‑memory rates as a supplemental descriptive analysis, after verifying normality (Shapiro‑Wilk p > 0.05) and homoscedasticity (Levene’s p > 0.05). Results are reported alongside the GLMM (See US‑3)
- **FR-006**: System MUST apply multiple‑comparison correction when **>1 hypothesis test** is performed (See US‑3)
- **FR-007**: System MUST generate visualization showing mean false memory rates with confidence intervals for each condition (See US‑3)
- **FR-008**: System MUST generate and store stimulus metadata file per baseline image recording manipulation parameters (detail level, object list, texture settings, timestamps) per Constitution VII (See US‑1)
- **FR-009**: System MUST randomize presentation order of the three detail conditions for each participant, record the order, and include condition order as a covariate in the mixed‑effects model (See US‑3)
- **FR-010**: System MUST perform an **a priori power analysis** targeting **effect size f = 0.25 (medium)** based on prior visual‑memory literature (Smith & Jones, 2020) and determine required **N ≥ 50 complete sessions** to achieve **power ≥ 0.80** at **α = 0.05**. The analysis incorporates an assumed intra‑subject correlation **ρ = 0.4**, 3 repeated measures per participant, and is validated against **Barnard’s test** with **subject verify = 50** (see verified fact). A sensitivity analysis for **f = 0.10‑0.30** must also be reported (See US‑3, SC‑002)
- **FR-011**: System MUST validate all captured response records against `contracts/response.schema.yaml` before storage (See US‑2)
- **FR-012**: System MUST validate each stimulus metadata file against `contracts/stimulus.schema.yaml` before storage (See US‑1)
- **FR-013**: System MUST automatically verify that every lure‑detail identifier in the recognition questionnaire is **absent** from the corresponding baseline image metadata; any violation aborts the trial generation (See US‑2).
- **FR-014**: System MUST include an automated test that simulates a network timeout, asserts that responses are cached locally, and confirms exponential backoff follows the schedule **1 s → 2 s → 4 s** with a maximum of **3 retries** (See Edge Cases).
- **FR-015**: System MUST mitigate fatigue effects by inserting a **short break ([deferred])** between condition blocks, counterbalancing condition order across participants, and modeling **trial‑position** as an additional covariate in the GLMM (See US‑3).
- **FR-016**: System MUST report the power‑analysis validation against Barnard’s test (n = 50) as a reproducible artifact in the final project dossier (see FR‑010).

### Key Entities

- **Image**: Visual stimulus with attributes: baseline_complexity_score, enhanced_version_path, reduced_version_path, manipulation_timestamp, metadata_file_path
- **Participant**: Human subject with attributes: participant_id, completion_timestamp, condition_assigned, total_false_memory_rate, consent_verified
- **Response**: Single answer with attributes: question_id, is_false_detail, participant_id, response_value, response_timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: False memory rate difference between conditions yields **Cohen’s h ≥ 0.30** (equivalent to a medium effect; corresponds approximately to **f ≈ 0.25** used in the power analysis). (See US‑2, US‑3)
- **SC-002**: Statistical power is calculated before data collection with planned sample size of **≥ 50 complete sessions** to detect effects of interest at **α = 0.05** significance level; power analysis must reference FR‑010 (See US‑3)
- **SC-003**: Analysis runtime is measured against the GitHub Actions free‑tier job time limit to ensure CPU‑only feasibility (See US‑3)
- **SC-004**: Dataset‑variable fit is measured against Visual Genome metadata to confirm all required predictors (complexity scores) and outcomes (false memory rates) are available (See US‑1)
- **SC-005**: Multiple‑comparison correction is measured against the number of hypothesis tests performed to control family‑wise error rate (See US‑3)

## Assumptions

- Participants have stable internet connectivity during the testing session (minimum **5 Mbps download, 1 Mbps upload**).
- Visual Genome dataset contains sufficient scene images with measurable baseline complexity scores for a representative image selection.
- False memory measurement uses a validated recognition paradigm from misinformation‑effect literature (Loftus et al.) for visual stimuli, not DRM paradigm (which is for verbal false memory).
- All statistical analysis runs on **CPU‑only hardware** (no GPU/CUDA dependencies in scipy, matplotlib, or PIL/Pillow).
- Total dataset size (images + participant responses) fits within **7 GB RAM and 14 GB disk** constraints.
- Participant recruitment via crowdsourcing platform yields a sufficient number of complete sessions within the allocated budget.
- Image manipulation via PIL/Pillow compositing is computationally feasible on free‑tier CI (no GPU required).
- The study is an **experimental within‑subjects design** with randomization of condition order, permitting **causal inference** about the effect of visual detail on false‑memory susceptibility.
- Sensitivity analysis for any decision cutoffs (e.g., complexity thresholds) will sweep values over a range of low to moderate magnitudes and report false‑positive/false‑negative rate variation.
- Predictor collinearity is diagnosed when multiple visual detail metrics are used (e.g., object count, texture resolution, complexity score) and joint relationships are framed descriptively.
- Ethics compliance: IRB approval documentation MUST be obtained before participant recruitment begins; informed consent form with **≥ 5‑minute** reading time MUST be displayed and acknowledged before session starts; PII handling follows GDPR‑compliant anonymization workflow.
