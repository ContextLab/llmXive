# Research: The Influence of Visual Aesthetics on Perceived Credibility of Online Information

## 1. Research Question & Hypothesis

**Primary Question**: Do visual-aesthetic qualities of a webpage (color scheme, typography, image quality, layout simplicity) systematically affect users' perceived credibility of the information presented, when the textual content is held constant?

**Hypothesis**: Participants will rate webpages with "Professional" and "Modern Minimalist" aesthetics significantly higher on perceived credibility and professionalism scales compared to "Low-Quality" and "Neutral" aesthetics, controlling for presentation order.

**Null Hypothesis ($H_0$)**: There is no difference in mean credibility ratings across the four visual aesthetic conditions.

## 2. Dataset Strategy

The study requires a dataset containing participant ratings for 4 distinct visual conditions, along with demographic covariates (age, education).

**Data Collection Strategy**:
1.  **Instrument**: 7-point Likert scales (1=Very Low, 7=Very High) for Credibility and Professionalism.
2.  **Stimuli**: 4 HTML/CSS pages (Professional, Minimalist, Low-Quality, Neutral) with identical text.
3.  **Design**: Within-subjects randomized experiment using Latin Square randomization (4 sequences) to control order effects.
4.  **Demographics**: Age (continuous), Education (ordinal: HS, Bachelor's, Master's, PhD).
5.  **Target Sample**: N=250 participants.

**Power Analysis Justification**:
The target sample size of N=250 is derived from a G*Power calculation for a repeated-measures ANOVA (within-subjects factor, 4 levels). Parameters: Effect size $f=0.25$ (medium), $\alpha=0.05$, Power ($1-\beta$) = 0.80, Correlation among repeated measures assumed = 0.5 (conservative estimate for within-subject ratings). This calculation yields a required sample of sufficient size to achieve adequate statistical power. The target of 250 accounts for an estimated 10-15% attrition rate common in web-based surveys and ensures robustness for the mixed-effects models.

**Data Source Verification**:
-   **Primary Data**: Generated via the `survey/app.py` Streamlit application. No external raw dataset exists for this specific stimulus set.
-   **Verified Datasets**: None applicable for raw participant data. The previously cited HuggingFace URL (`P2SAMAPA/p2-etf-functional-anova-results`) contained aggregated statistical results from a different study and does not provide the raw participant-level ratings required for this primary analysis. Therefore, it is excluded from the data strategy to maintain accuracy.

**Data Fit Verification**:
-   **Required Variables**: `participant_id`, `stimulus_condition`, `credibility_rating`, `professionalism_rating`, `age`, `education`, `timestamp`, `order_sequence`.
-   **Resolution**: The survey application will generate `data/raw/participants.csv` containing all required variables.

## 3. Statistical Methodology

### 3.1 Primary Analysis (US-2)
**Method**: Repeated-Measures ANOVA.
-   **Within-Subject Factor**: Design Condition (4 levels: Professional, Minimalist, Low-Quality, Neutral).
-   **Dependent Variable**: Credibility Rating (7-point Likert).
-   **Assumption Checks & Decision Rules (Pre-Registered)**:
    1.  **Normality**: Shapiro-Wilk test on residuals. If $p < 0.05$, data is considered non-normal.
    2.  **Sphericity**: Mauchly's test. If violated ($p < 0.05$), Greenhouse-Geisser correction applied.
    3.  **Decision Rule**: If Normality is violated, the analysis pipeline **automatically switches** to the non-parametric Friedman test. Follow-up pairwise comparisons will use Wilcoxon signed-rank tests with Bonferroni correction. This pre-registered rule prevents p-hacking by choosing the test post-hoc.
-   **Follow-up**: If the main effect is significant ($p < 0.05$), conduct 6 pairwise t-tests (or Wilcoxon) with **Bonferroni correction** ($\alpha_{adj} = 0.05 / 6 \approx 0.0083$).
-   **Effect Sizes**: Partial $\eta^2$ for ANOVA; Cohen's $d$ (or $r$) for pairwise comparisons.

### 3.2 Robustness Checks (US-3)
**Method**: Linear Mixed-Effects Model (LMM).
-   **Fixed Effects**: Design Condition, Age, Education, and **Interaction Terms** (Condition x Age, Condition x Education).
-   **Random Effects**: Random intercept for `participant_id` to account for baseline rating severity.
-   **Goal**: Verify that the Design Condition effect persists after controlling for demographics and test whether demographics moderate the effect (interaction terms). This corrects the misconception that random intercepts alone "control" for covariates.

### 3.3 Statistical Rigor & Constraints
-   **Multiple Comparisons**: Bonferroni correction applied to all 6 pairwise tests (FR-005).
-   **Causal Inference**: This is a **within-subjects randomized experiment**. The Latin Square randomization of stimulus order allows for causal claims about the effect of aesthetics on credibility, provided the textual content is neutral and constant.
-   **Collinearity**: No predictors are definitionally related.
-   **CPU Feasibility**: ANOVA and LMM (via `statsmodels`) are CPU-tractable. No GPU required.

## 4. Stimulus Content Definition
To ensure internal validity and address the threat of content confounding:
-   **Text Content**: A neutral, factual summary of a generic scientific topic (e.g., "The Water Cycle") is used.
-   **Source**: The text is stored in `code/stimuli/text_content.txt` and is identical across all 4 visual conditions.
-   **Neutrality Check**: The text is pre-screened to ensure it contains no persuasive language, emotional cues, or credibility-inducing claims that could interact with the visual style.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Streamlit for Survey** | Rapid deployment, native Python backend, easy integration with `pandas` for data logging. Runs on free-tier CI. |
| **Latin Square Design** | Essential to control order effects in a within-subjects design where participants see all 4 stimuli. |
| **Bonferroni Correction** | Required by FR-005 to control Family-Wise Error Rate (FWER) across 6 pairwise comparisons. |
| **Mixed-Effects Model** | Required by US-3 to account for individual differences (random intercepts) and test covariates (age/education) as fixed effects and interactions. |
| **CSV Data Format** | Simple, human-readable, compatible with `pandas`, and fits within the 5MB size constraint (SC-005). |
| **Pre-Registered Decision Rule** | Ensures scientific rigor by defining the switch from ANOVA to non-parametric tests based on normality tests, preventing p-hacking. |