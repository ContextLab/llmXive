# Research: The Relationship Between Sleep Chronotype and Moral Judgement

## Research Question
Do individuals with later sleep chronotypes (evening types) exhibit systematically different patterns of moral judgement compared to earlier chronotypes (morning types), independent of acute sleep deprivation?

## Literature & Context
Current literature suggests that circadian rhythms influence cognitive processing and emotional regulation, which may extend to moral reasoning. However, few studies have controlled for acute sleep deprivation (a confounder that affects both chronotype expression and moral judgment). This study aims to isolate the trait-like effect of chronotype on the five Moral Foundations (Care, Fairness, Loyalty, Authority, Sanctity).

## Dataset Strategy

### Data Sources
The analysis requires a **single, pre-merged** dataset containing the following variables for the *same* participants:
1. **Chronotype**: MEQ scores.
2. **Moral Judgment**: MFQ subscale scores.
3. **Covariates**: PSQI (chronic sleep quality), Acute Sleepiness, Age, Sex.

**Verified Sources (per spec constraints):**
* **MFQ Data**: Available via `lukebruhns/identity-refusal-mfq2` (HuggingFace).
 * *URL*: `
 * *Content Check*: Contains MFQ subscale scores. **Lacks** MEQ, PSQI, Acute Sleepiness.
* **MEQ Data**: Available via `lighteval/me_q_sum` (HuggingFace).
 * *URL*: `
 * *Content Check*: This dataset is an NLP benchmark for summarization tasks (MEQ-Sum) and **does not** contain the standard Morningness-Eveningness Questionnaire (MEQ) scores required for chronotype classification (FR-002) or the associated demographic/sleep covariates.
* **PSQI/Acute Sleepiness Data**: No verified source found in the provided block.

**Dataset Fit Analysis:**
* **MEQ**: No verified source containing the full psychometric MEQ scores and required covariates.
* **MFQ**: Present in `lukebruhns/identity-refusal-mfq2`.
* **PSQI/Acute Sleepiness**: **NOT** present in any verified source.
* **Merge Feasibility**: Merging the verified MFQ and MEQ sources is **methodologically invalid** because they lack a common `participant_id` and contain different subjects. Creating artificial rows by merging disjoint datasets destroys individual-level variance and invalidates the ANCOVA.

**Resolution:**
Per the spec's "Assumptions" section and the requirement to control for acute sleep deprivation (FR-007), the pipeline **MUST** require a single, pre-merged dataset containing all required variables.
* **Strategy**: The pipeline will **ABORT** if the input data does not contain all required columns.
* **Simulation**: **No simulation** of missing covariates is permitted. Synthetic data cannot test the relationship between real chronotype and moral judgment and would invalidate the research question.
* **Data Collection**: The researcher must provide a merged dataset (e.g., from primary data collection via Prolific) or a specific merged file. The pipeline is designed to validate the presence of this data, not to create it.

## Statistical Methodology

### 1. Chronotype Classification (FR-002)
* **Method**: Threshold-based classification of `MEQ_score`.
 * `MEQ >= 59`: "morning"
 * `MEQ <= 41`: "evening"
 * `41 < MEQ < 59`: "intermediate"
* **Handling Missing**: Rows with `NA` or non-numeric `MEQ_score` are flagged and excluded from group analysis (FR-006).

### 2. ANCOVA (FR-003)
* **Model**: Separate linear models for each of the MFQ subscales.
 * `MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex`
* **Correction**: Bonferroni correction applied to the resulting p-values.
 * Adjusted alpha = 0.05 / 5 = 0.01.
* **Covariates**: `PSQI` (chronic quality), `acute_sleepiness` (to control for deprivation), `age`, `sex`.
* **Collinearity Check**: Variance Inflation Factors (VIF) calculated; if VIF > 2, a warning is issued (Assumption: Collinearity is low).

### 3. Effect Sizes (FR-004)
* **Metric**: Cohen's *d* for significant contrasts (e.g., Evening vs. Morning).
* **Confidence Interval**: 95% CI calculated for Cohen's *d*.

### 4. Power Analysis (FR-005)
* **Method**: Post-hoc power calculation using `pwr` package.
* **Parameters**: Effect size *f* = 0.25, alpha = 0.05, power = 0.80 (target n=159).
* **Sensitivity**: Report power at observed effect sizes.

### 5. Sensitivity Analysis (FR-005, SC-004)
* **Sweep**: Re-evaluate significance for alpha_corrected values: {, 0.0125, 0.015}.
* **Output**: Table showing significance status for each MFQ subscale at each threshold.

## Statistical Rigor & Limitations
* **Multiple Comparisons**: Bonferroni correction is strictly applied (α=0.01).
* **Sample Size**: The pipeline assumes a sample size meeting the n=159 threshold. If the provided data is smaller, the power analysis will reflect this limitation explicitly.
* **Causal Inference**: The study is **observational**. Claims will be framed as "associational." No causal claims regarding chronotype causing moral differences will be made.
* **Measurement Validity**: MEQ and MFQ are standard instruments. Internal consistency (Cronbach's α) will be reported.
* **Collinearity**: The plan acknowledges that if `acute_sleepiness` and `PSQI` are highly correlated, VIF will detect it. The plan does *not* claim independent effects if predictors are definitionally related.
* **Data Limitation**: The study cannot proceed without a real merged dataset containing MEQ, MFQ, PSQI, and acute sleepiness. The pipeline will abort if such data is not provided.

## Compute Feasibility
* **Environment**: CPU-only GitHub Actions runner.
* **Method**: Linear models (ANOVA/ANCOVA) are computationally trivial for N < 10,000.
* **Memory**: Data will be loaded into RAM; no large model inference required.
* **Runtime**: Estimated < 5 minutes for full pipeline.