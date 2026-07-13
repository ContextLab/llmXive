# Research: The Impact of Social Comparison on Self-Perception on AI-Generated Image Platforms

## Research Question

Do upward social comparisons with AI-generated idealized body images on image-sharing platforms produce stronger negative effects on body image self-perception than comparisons with human-generated idealized images, after controlling for platform usage frequency and baseline comparison orientation?

## Methodology Overview

### Design
- **Type**: Within-subjects experimental design.
- **Stimuli**: 40 images per participant (20 AI-generated, 20 Human-generated), matched on pose, lighting, and body type.
- **Procedure**: Randomized presentation of images. Immediate post-stimulus rating using the Body Image States Scale (BISS).
- **Covariates**: Iowa-Netherlands Comparison Orientation Measure (INCOM) and Platform Usage Frequency (hours/week), collected prior to stimulus exposure.

### Statistical Analysis Plan

The primary analysis employs a **Linear Mixed Effects (LME)** model to account for the nested structure of the data (responses nested within participants).

**Model Specification**:
$$ BISS_{ij} = \beta_0 + \beta_1(\text{ImageType}_{ij}) + \beta_2(\text{INCOM}_i^c) + \beta_3(\text{UsageFreq}_i^c) + \beta_4(\text{ImageType}_{ij} \times \text{INCOM}_i^c) + u_{0i} + u_{1i}(\text{ImageType}_{ij}) + \epsilon_{ij} $$

Where:
- $i$ = Participant, $j$ = Image trial.
- $\text{ImageType}$: Categorical (AI vs. Human).
- $\text{INCOM}_i^c$, $\text{UsageFreq}_i^c$: Covariates **mean-centered** to ensure $\beta_1$ represents the effect at the average level of the covariate.
- $u_{0i}$: Random intercept for Participant ID.
- $u_{1i}$: Random slope for Image Type by Participant (captures individual variation in response to AI vs. Human images).
- $\epsilon_{ij}$: Residual error.

*Note: If the model with random slopes fails to converge, a random intercept-only model will be used, and this limitation will be reported.*

**Hypothesis Testing**:
- **H1**: $\beta_1 < 0$ (AI images lead to lower BISS scores than Human images).
- **H2**: Interaction effects ($\beta_4$) indicate moderation by comparison orientation.

**Multiple Comparison Correction**:
- The "family" of tests for Bonferroni correction is explicitly defined as:
  1. Main Effect of Image Type.
  2. Interaction Effect (Image Type × INCOM).
  3. Main Effect of INCOM.
  4. Main Effect of Usage Frequency.
- Exploratory tests (e.g., simple slopes) will be reported with uncorrected p-values or a separate correction factor.
- Correction applied to control Family-W Error Rate (FWER) at $\alpha = 0.05$.

**Missing Data Strategy**:
- **Retain Partial Data**: Unlike the initial draft, this plan utilizes the LME model's ability to handle unbalanced data (Missing At Random - MAR). Participants with incomplete sequences (< 40 images) will be **retained** in the analysis. This maximizes statistical power and reduces selection bias associated with excluding participants who may have dropped out due to distress (a non-random process).
- **Exclusion Criteria**: Only participants with **zero** valid responses (e.g., failed consent, no data) will be excluded.

### Outlier & Sensitivity Analysis
- **Outlier Detection**: Extreme INCOM scores (e.g., > 3 SD from mean) will be flagged.
- **Sensitivity**: A secondary analysis will be run excluding these flagged participants to ensure the main effect is robust. Results will be reported in `data/analysis_results.json`.

## Dataset Strategy

### Stimuli (Primary Data Source)
The study relies on two pre-validated sets of images:
1.  **AI-Generated Set**: 20 images generated using stable diffusion models with specific prompts targeting "idealized body types."
2.  **Human-Generated Set**: 20 images sourced from public domain or licensed stock photography, matched to the AI set by metadata (pose, lighting, body type).

*Note: The spec assumes these sets are pre-validated (FR-008, FR-009). The implementation will load these from `data/stimuli/`.*

### Response Data
- **Source**: Generated via the data collection interface (simulated for CI/testing).
- **Variables**: `participant_id`, `stimulus_id`, `image_type`, `biss_score`, `timestamp`.
- **Covariates**: `incom_score`, `usage_frequency`.

### Verified Datasets
Per the project constraints, the following verified sources are available for reference or simulation of covariate distributions if needed for power analysis or mock data generation:

| Variable | Source / Description | Verified URL |
| :--- | :--- | :--- |
| **INCOM** | Simulation based on standard psychometric distributions (bounded ranges, Normal) described in the original literature (Hodson & Olson). No specific dataset URL exists for INCOM in the verified block; we do not fabricate one. | N/A (Literature-based simulation) |
| **Usage Frequency** | Simulation based on reported population means from Pew Research Center regarding social media usage. No specific dataset URL exists for this variable in the verified block; we do not fabricate one. | N/A (Literature-based simulation) |
| **BISS** | Simulation based on standard psychometric distributions described in the original literature (Cash et al., 2004). | N/A (Literature-based simulation) |

*Clarification*: The "Verified datasets" block provided in the prompt contains URLs for "adult" census data, which are **not** appropriate for simulating psychometric variables like INCOM or Usage Frequency. We strictly adhere to the rule: **Do NOT invent or guess a dataset URL**. Instead, we simulate data based on the known statistical properties (mean, SD, range) reported in the primary psychometric literature for these scales.

## Feasibility & Compute Constraints

- **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
- **Method**: LME models using `statsmodels` (Python) are CPU-tractable for N=150 participants × 40 trials = 6,000 rows.
- **Runtime**: Expected < 30 seconds for model fitting and correction.
- **Memory**: < 500MB for data loading and model fitting.
- **Dependencies**: `statsmodels`, `pandas`, `numpy`, `scipy`. All available via PyPI and installable on CPU-only runners.

## Limitations & Assumptions

- **Dataset-Variable Fit**: The plan assumes the pre-generated stimuli sets (AI/Human) are perfectly matched on all confounding variables (pose, lighting) as per FR-008. If the metadata validation fails, the study launch is blocked.
- **Power**: N=150 is a target based on standard assumptions for a medium effect size (f=0.25). However, the effective sample size in a within-subjects design is heavily influenced by the Intraclass Correlation (ICC). A sensitivity analysis will be performed to report the power given the observed ICC. If power is lower than 0.80, this will be acknowledged as a limitation.
- **Generalizability**: Results are specific to the selected stimulus set and the demographic of the participants (assumed university students/volunteers).
- **Causal Inference**: While the within-subjects design controls for individual differences, the "Image Type" effect is causal regarding the *stimulus origin* only if the matching is perfect.
- **Visual Indistinguishability (FR-009)**: The "blind pre-test" validates that the **visual quality** (aesthetics, symmetry) is matched between AI and Human sets. It does **not** require that participants cannot *perceive* the origin (AI vs. Human). The study hypothesis relies on the *knowledge* of origin or the *perception* of "synthetic perfection" (which may differ even if visual quality is matched). If the pre-test shows a difference in *quality* (p < 0.05), the study is blocked to ensure the only systematic difference is the origin label.

## Decision Rationale

**Why LME?**
The data structure is hierarchical (trials within participants). Standard ANOVA requires complete data and assumes sphericity, which may be violated. LME handles unbalanced data (retaining partial participants) and provides more robust estimates of fixed effects with random intercepts and slopes.

**Why CPU-only?**
The statistical model (LME) does not require matrix operations large enough to necessitate GPU acceleration. The stimuli are static images, not real-time generation tasks.

**Why Retain Partial Data?**
Excluding partial participants (Per-Protocol) introduces selection bias if dropout correlates with the outcome (e.g., distress). LME models are specifically designed to handle Missing At Random (MAR) data, preserving power and validity.

**Why Center Covariates?**
Centering INCOM and Usage Frequency ensures that the main effect of Image Type ($\beta_1$) is interpretable as the effect at the *average* level of the covariate, rather than at a value of 0 (which is outside the valid range of the scales).

**Why Random Slopes?**
Participants may vary in their sensitivity to AI vs. Human images. Including a random slope for Image Type accounts for this variation, reducing Type I error rates.