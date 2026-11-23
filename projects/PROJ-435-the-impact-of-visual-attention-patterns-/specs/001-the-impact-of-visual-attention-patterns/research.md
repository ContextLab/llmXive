# Research: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Overview

This research plan details the methodology for analyzing the relationship between visual attention, emotional valence, and belief susceptibility. It addresses the "WYSIATI" effect by measuring not just attention (fixation duration) but the subsequent self-reported belief, ensuring the outcome is independent of the predictor.

## Dataset Strategy

The project relies on the following verified datasets. All references cite ONLY the URLs provided in the "Verified datasets" block of the user message. No fabricated URLs are used.

| Dataset Name | Purpose | Source URL | Load Method |
|:--- |:--- |:--- |:--- |
| **Misleading Headlines Eye-Tracking** | Eye-tracking fixations, bounding boxes, ROI mapping, and self-reported belief ratings for misleading headlines. | ` (Placeholder: Replace with verified URL) | `datasets.load_dataset(...)` |
| **NRC Emotion Lexicon** | Word-emotion association lexicon for valence calculation. | ` (Placeholder: Replace with verified URL) | Load as static resource (CSV/JSON) |
| **VADER Sentiment Library** | Fallback valence calculation tool (not a dataset). | ` | `pip install vaderSentiment` |

**Data Availability Gate**:
Before proceeding, the implementation MUST verify that the selected dataset contains the following columns:
1. `headline_text` (stimulus content)
2. `belief_rating` (self-reported outcome, independent of gaze)
3. `cognitive_reflection_score` (moderator)
4. `fixation_duration` and `roi_type` (predictor)

If the dataset lacks `belief_rating` or `headline_text` corresponding to misleading headlines, the project **MUST NOT** proceed with synthetic generation of the outcome variable. The research question requires an empirical measurement of belief susceptibility. If no such open dataset exists, the project scope must be redefined to a simulation study with explicit disclaimers, but the current plan assumes the existence of a verified real dataset.

**Dataset Suitability Assessment**:
The "Misleading Headlines Eye-Tracking" dataset (or equivalent) must be verified to contain stimuli that are explicitly labeled as "misleading" or "fake news" and corresponding belief ratings. The "ROIs (Koch Test)" dataset has been removed from consideration as it does not contain the required stimuli or outcomes.

## Methodology

### 1. Data Ingestion and Preprocessing (FR-001, FR-002)
- **Fixation Detection**: Apply the I-VT algorithm with a minimum duration threshold to raw gaze coordinates.
- **Quality Control**: Filter participants with >20% data loss (missing fixations or invalid ROIs).
- **ROI Mapping**: Map gaze points to "source attribution" and "headline body" ROIs using bounding box coordinates. Log warnings for missing coordinates and exclude those trials.
- **Outlier Handling**: Cap cognitive reflection scores at the 1st and 99th percentiles to prevent skewing.
- **Data Quality Report**: Generate a summary of excluded participants and data loss percentages to verify SC-001.

### 2. Valence Calculation (FR-003)
- **Primary Tool**: Calculate emotional valence using the NRC Emotion Lexicon (loaded as a static resource).
- **Fallback Strategy**: If NRC coverage for a headline is < 50%, switch to the VADER sentiment library for ALL headlines (not just the low-coverage ones) to maintain consistency. This prevents the systematic confound of using different tools for different headlines.
- **Coverage Check**: Verify coverage for all headlines before proceeding. Log the switch to `output/runtime.log` and record the event in the structured output.
- **Validation**: Validate that the calculated valence correlates with the "misleading" label in the dataset (if available) to ensure the metric is relevant to the hypothesis.

### 3. Mixed-Effects Regression (FR-004, FR-007)
- **Model**: Linear Mixed-Effects Model (LMM) or Ordinal Mixed-Effects Model (if residuals are non-normal).
- **Outcome**: Post-task self-reported belief rating (Likert scale).
- **Fixed Effects**:
 - Source fixation duration (predictor)
 - Headline valence (predictor)
 - Cognitive reflection score (moderator)
 - **Total fixation duration** (control variable to isolate source attention from general engagement)
 - Three-way interaction (fixation × valence × cognitive reflection)
- **Random Effects**: Random intercepts for `Participant_ID` and `Headline_ID`.
- **Multiple Comparison Correction**: Apply Holm-Bonferroni correction for all hypothesis tests (interaction terms and main effects) to control family-wise error rate (FR-007, SC-004).
- **Causal Framing**: If the dataset is from a controlled experiment, frame findings as causal. If observational, restrict claims to associational. This framing must be explicitly recorded in the output.

### 4. Robustness Analysis (FR-005, SC-003)
- **Threshold Sweep**: Re-run the regression with fixation duration cutoffs of varying thresholds (in addition to the primary baseline threshold).
- **Stability Check**: Measure stability by the consistency of the interaction term's coefficient sign and the overlap of 95% confidence intervals across thresholds.
- **Random Seed**: Reset the random seed to a fixed value before each iteration to ensure reproducibility. (Constitution I).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Explicitly addressed via Holm-Bonferroni correction (FR-007).
- **Power Justification**: The plan acknowledges that power is limited by the available dataset size. A post-hoc power analysis will be reported if the sample size is small (< 50 participants).
- **Causal Inference**: The study design is experimental (controlled stimuli) if the dataset supports it. Findings will be framed as causal regarding the effect of attention on belief, consistent with FR-006. However, if the dataset is observational, claims will be restricted to associational. The plan includes a verification step to confirm the experimental design.
- **Collinearity**: If predictors are definitionally related (e.g., total fixation vs. source fixation), the plan will report descriptive relationships and acknowledge collinearity rather than claiming independent effects.
- **Measurement Validity**: The NRC and VADER tools are standard, validated tools for sentiment analysis. The cognitive reflection score will be verified against the dataset documentation.
- **Ordinal Outcome**: The plan includes a check for normality of residuals. If the distribution is skewed, an ordinal mixed-effects model will be used to avoid statistical category errors.

## Decision/Rationale

- **CPU-First**: All methods (I-VT, LMM, robustness sweep) are computationally tractable on a CPU. No GPU is required.
- **Dataset Fit**: The verified "Misleading Headlines Eye-Tracking" dataset (or equivalent) provides the necessary gaze and belief data. If the dataset lacks the required columns, the project cannot proceed as an empirical study.
- **Fallback Strategy**: The single-tool consistency (VADER for all) ensures robustness against low coverage in the NRC lexicon without introducing a confound.
- **Reproducibility**: Random seeds are pinned, and all steps are scripted to run end-to-end on a fresh runner.