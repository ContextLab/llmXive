# Feature Specification: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

**Feature Branch**: `001-perspective-taking-outrage`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "Does prompting individuals to adopt the perspective of a disagreeing online poster reduce their self‑reported moral outrage toward the post, and is this effect independent of the initial emotional intensity of the stimulus?"

## User Scenarios & Testing

### User Story 1 - Stimulus Curation and Stratified Randomization (Priority: P1)

The system must ingest the "Against the Others!" Twitter dataset, filter for posts on controversial topics (e.g., climate, immigration), and stratify the stimulus pool by initial automated sentiment scores (computed via VADER if not present) to ensure a mix of moderate and high intensity. It must then generate randomized experimental stimuli (perspective-taking vs. control instructions) for participant delivery.

**Why this priority**: Without a curated, balanced, and stratified set of stimuli, the core experimental manipulation cannot occur. This ensures the study tests the intervention across the full range of emotional intensity, addressing the research question's second clause regarding independence from initial intensity.

**Independent Test**: The system can be tested by executing the data pipeline script and verifying that the output JSON contains a set of unique posts distributed across the specified topics, each paired with two distinct instruction sets. The test must confirm that the selection was a random sample from a pool of ≥60 posts and that the distribution of automated sentiment scores is balanced across the two instruction conditions.

**Acceptance Scenarios**:

1. **Given** the raw "Against the Others!" dataset is available and contains posts on controversial topics, **When** the system filters and stratifies by automated sentiment, **Then** the output contains a balanced set of posts (approximately equal per topic) selected via random sampling, ensuring representation of both moderate and high intensity.
2. **Given** the 60 selected posts, **When** the system generates instructions, **Then** each post has exactly two versions: one "Perspective-taking" prompt ("Explain... why the author might hold this view") and one "Control summarization" prompt ("Summarize... in one sentence").
3. **Given** the stimulus generation is complete, **When** the system checks the sentiment distribution, **Then** the system verifies that the stratification logic was applied and reports the resulting difference in mean automated sentiment scores between the perspective-taking group and the control group.

---

### User Story 2 - Participant Response Collection and Data Cleaning (Priority: P2)

The system MUST process uploaded raw data from actual participants. Synthetic data generation is permitted ONLY for unit testing the pipeline logic, not for the primary study execution. The system must enforce attention checks (failing >1 item) and detect straight-lining (zero variance across 7 items), then calculate the mean moral outrage score per participant.

**Why this priority**: This user story defines the data ingestion and cleaning logic required to transform raw survey responses into the analysis-ready dataset. It ensures data validity before statistical testing, adhering to the stricter exclusion criteria (>1 failed check) defined in the methodology.

**Independent Test**: The system can be tested by feeding a synthetic CSV of responses (including some failed attention checks and straight-liners) and verifying that the output dataset excludes the failed participants and contains the calculated mean scores for the remaining valid set.

**Acceptance Scenarios**:

1. **Given** a raw response file with a cohort of participants, **When** the system runs the attention check filter, **Then** any participant failing >1 attention check item OR exhibiting zero variance (straight-lining) across all 7 scale items is excluded from the final dataset.
2. **Given** a valid participant's responses to 5 posts, **When** the system calculates the mean, **Then** the output includes a single `mean_outrage_score` column derived from the 7-item Moral Outrage Scale.
3. **Given** the cleaned dataset, **When** the system groups by condition, **Then** the system calculates the number of participants per condition and reports a warning if the total N is less than 240 (120 per condition).

---

### User Story 3 - Statistical Analysis and Robustness Verification (Priority: P3)

The system must execute the primary independent-samples t-test, calculate effect sizes (Cohen's d) and 95% confidence intervals, and perform the non-parametric Mann-Whitney U robustness check. The analysis must explicitly report results as associational if the design were observational, but here frame them as causal effects of the randomized intervention.

**Why this priority**: This delivers the final scientific output. It validates the hypothesis and ensures the results are robust to distributional assumptions, fulfilling the core research question while maintaining methodological rigor regarding inference framing.

**Independent Test**: The system can be tested by running the analysis script on the cleaned dataset and verifying that the output report contains the t-statistic, p-value, Cohen's d, confidence interval, and the Mann-Whitney U p-value.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset with two groups, **When** the t-test is executed, **Then** the output reports the p-value, Cohen's d effect size, and the 95% confidence interval for the mean difference.
2. **Given** the same dataset, **When** the Mann-Whitney U test is executed, **Then** the output reports a p-value to confirm robustness against non-normality.
3. **Given** the analysis is complete, **When** the system generates the report, **Then** the report explicitly states whether the result is significant at p < 0.05 and frames the finding as the causal effect of the intervention.

---

### User Story 4 - Computational Feasibility and Resource Constraints (Priority: P2)

The system must ensure all analysis operations complete within the constraints of free-tier CI runners (CPU-only, ≤7 GB RAM, ≤6 hours runtime) to guarantee reproducibility and accessibility.

**Why this priority**: This ensures the study can be run by researchers with limited resources and prevents the analysis from failing due to hardware limitations, which is critical for open science.

**Independent Test**: The system can be tested by running the full pipeline on a constrained environment (e.g., GitHub Actions free runner) and verifying that the process exits successfully with exit code 0 without exceeding memory or time limits.

**Acceptance Scenarios**:

1. **Given** the analysis script is executed on a standard CPU-only runner, **When** the script runs, **Then** the peak memory usage remains within ≤7 GB RAM.
2. **Given** the analysis script is executed, **When** the script completes, **Then** the total runtime does not exceed 6 hours.
3. **Given** the script attempts to use GPU acceleration or 8-bit quantization, **When** the script runs, **Then** it raises a configuration error immediately.

---

### Edge Cases

- What happens if the raw Twitter dataset contains fewer than 60 unique posts on the target topics after filtering for sentiment stratification? If the available pool for any topic is < 60 posts, the system MUST raise a `DATASET_INSUFFICIENT` error (code 400) and halt execution before stimulus generation. This ensures a random sample of sufficient size can be drawn without selection bias.
- How does the system handle participants who provide identical responses to all items on the Moral Outrage Scale (indicating straight-lining)? The system MUST exclude participants exhibiting zero variance (straight-lining), irrespective of their performance on attention checks, as defined in FR-003.
- How does the system handle the scenario where the t-test assumptions (normality, homogeneity of variance) are severely violated? The system MUST rely on the Mann-Whitney U test results as the primary interpretation for that specific run, as defined in the robustness protocol.
- What if the automated sentiment scores used for stratification are unavailable for a specific post? The system MUST compute the score using VADER (or equivalent standard library) and exclude the post only if computation fails, to maintain the integrity of the stratification logic.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the "Against the Others!" Twitter dataset, filtering for posts on controversial topics and stratifying the pool by automated sentiment scores (computed via VADER if not pre-computed) to ensure a mix of moderate and high intensity (See US-1).
- **FR-002**: System MUST generate a sufficient set of unique stimuli (≥60 posts), ensuring a balanced distribution of posts per topic and two distinct instruction sets (perspective-taking vs. control) per post (See US-1).
- **FR-003**: System MUST implement an attention check filter that excludes any participant who fails >1 item OR exhibits zero variance (straight-lining) across all 7 scale items, ensuring data validity (See US-2).
- **FR-004**: System MUST calculate the mean moral outrage score for each valid participant across their presented posts using the Moral Outrage Scale (See US-2).
- **FR-005**: System MUST perform an independent-samples t-test comparing mean outrage scores between the perspective-taking and control conditions, reporting p-values, Cohen's d, and 95% confidence intervals (See US-3).
- **FR-006**: System MUST execute a Mann-Whitney U test as a non-parametric robustness check to verify results against distributional assumptions (See US-3).
- **FR-007**: System MUST ensure all statistical computations are performed using CPU-only methods compatible with free-tier CI runners (≤7 GB RAM, no GPU, no 8-bit quantization) (See US-4).
- **FR-008**: System MUST verify that the raw 'Against the Others!' dataset contains at least 60 unique posts on the target topics after sentiment filtering. If the available pool is < 60 posts, the system MUST raise a `DATASET_INSUFFICIENT` error (code 400) and halt execution (See US-1).
- **FR-009**: System MUST frame the primary findings as the causal effect of the randomized intervention (perspective-taking instruction) on moral outrage, not as an observational association (See US-3).
- **FR-010**: System MUST support the ingestion of real participant data (e.g., via CSV upload or API) and handle the specific data formats required for the Moral Outrage Scale, distinguishing this from synthetic data used for unit testing (See US-2).
- **FR-011**: System MUST justify the aggregation of repeated measures (5 posts per participant) by calculating and reporting the intra-class correlation (ICC) or confirming the independence assumption, ensuring the validity of the t-test on means (See US-3).

### Key Entities

- **Stimulus**: Represents a specific Twitter post paired with an instruction set (Perspective-taking or Control), containing the post text, topic tag, automated sentiment score, and instruction prompt.
- **Participant**: Represents an experimental subject, containing demographics, condition assignment, individual post responses, attention check results, and the calculated mean outrage score.
- **Result**: Represents the statistical output of the analysis, containing the t-statistic, p-value, effect size, confidence intervals, and robustness check results.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The statistical significance of the difference in mean outrage scores is measured against the null hypothesis (p < 0.05) as defined in the research question (See US-3).
- **SC-002**: The precision of the effect size estimate (Cohen's d) is measured by the calculation and reporting of the 95% confidence interval width, with the target for study design (Power ≥ 0.80) documented in the Assumptions section (See US-3).
- **SC-003**: The robustness of the findings is measured against the non-parametric Mann-Whitney U test results to confirm consistency of the direction and significance (See US-3).
- **SC-004**: The data integrity is measured against the attention check failure rate, ensuring the final analysis includes only participants who failed ≤1 attention item and exhibited non-zero variance (See US-2).
- **SC-005**: The computational feasibility is measured against the free-tier CI constraints (≤6 hours runtime, ≤7 GB RAM) to ensure the analysis completes without hardware errors (See US-4).
- **SC-006**: The stratification validity is measured by the application of the stratification logic and the reporting of the resulting difference in mean automated sentiment scores between the two experimental conditions (See US-1).

## Assumptions

- The "Against the Others!" dataset contains sufficient unique posts on controversial topics (climate, immigration) to allow for a stratified random sample of 60 posts after filtering by automated sentiment.
- The automated sentiment scores available in the dataset or derived via VADER (or equivalent standard library) are sufficiently correlated with human-perceived emotional intensity to serve as a valid surrogate for stratification, acknowledging this as a methodological approximation subject to validity checks.
- The Moral Outrage Scale (Smith et al.) is available as a standard 7-item Likert instrument. and can be administered digitally with high fidelity to the paper version.
- The experimental design utilizes random assignment to conditions; therefore, findings are framed as the causal effect of the prompt on outrage, not as an observational association.
- The sample size of 240 participants (120 per condition) provides sufficient statistical power (≥0.80) to detect a medium effect size (Cohen's d ≈ 0.5) with α = 0.05, based on standard power calculations for independent t-tests.
- All analysis code (pandas, scipy, statsmodels) runs efficiently on a standard CPU without requiring GPU acceleration, 8-bit quantization, or large memory footprints.
- The randomization process effectively balances unobserved confounders between the two conditions, allowing for causal inference of the intervention effect.
- The "high-outrage" tag in the dataset is an independent metadata label derived from a separate annotation process and is not calculated from the Moral Outrage Scale items used as the outcome, mitigating ceiling effect concerns.
- The aggregation of repeated measures per participant into a single mean score is a valid approximation. for the independent t-test, provided the intra-class correlation is low or the analysis accounts for it as per FR-011.