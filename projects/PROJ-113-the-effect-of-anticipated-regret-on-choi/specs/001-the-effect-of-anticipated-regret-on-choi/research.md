# Research: The Effect of Anticipated Regret on Choice Deferral

## Research Question
Does higher anticipated regret increase the likelihood that individuals defer making a choice, after controlling for option set size, perceived risk, time pressure, and individual decision-making style?

## Theoretical Background
Anticipated regret is the emotional expectation of feeling worse after making a suboptimal choice compared to a foregone alternative. In high-stakes or complex decision environments, the fear of this emotion can lead to "choice deferral" (postponing or avoiding a decision). This study operationalizes anticipated regret not via self-report (which is prone to recall bias) but via a structural proxy: **Min-Max Regret** (the opportunity cost of the chosen option relative to the best available alternative). This approach isolates the *potential* for regret by measuring the gap between the best possible outcome and the actual outcome, distinct from general loss aversion (which focuses on the magnitude of loss).

**Distinction from Choice Difficulty**: Unlike "SD of EU" (which measures general spread/complexity), Min-Max Regret is zero if the best option is chosen and positive only if a suboptimal option is selected or if deferral occurs to avoid a bad outcome. This specifically targets the psychological mechanism of regret.

## Dataset Strategy

The study utilizes two verified datasets to ensure robustness and generalizability.

| Dataset | Source | Variables of Interest | Relevance |
| :--- | :--- | :--- | :--- |
| **DecisionMaking** (Primary) | HuggingFace: `zhehuderek/textual_decisionmaking_data` (Parquet) | Option attributes (price, rating), choice outcome, deferral flags, participant ID. | Contains structured decision trials with clear deferral outcomes and option attributes to compute the regret proxy. |
| **Online Shopping Behavior** (Secondary) | HuggingFace: `PhillyMac/Decision_Making_Content_1` (Parquet) | Transaction logs, item attributes, abandonment/deferral events. | Provides a secondary context (e-commerce) to test the generalizability of the regret-deferral relationship. |

**Dataset Variable Fit Confirmation**:
- **Deferral Flag**: Both datasets contain indicators for non-action or timeout events, which will be mapped to the binary `deferral` outcome.
- **Option Attributes**: Both datasets provide numeric attributes (e.g., price, rating) necessary to calculate "expected utilities."
- **Missing Variables**: If "perceived risk" scores are missing (as noted in FR-003), the analysis will use "price variance" as a mandatory proxy, as specified in the spec.
- **Self-Report Validation**: If self-reported regret scores are available, a correlation check (SC-006, target r > 0.3) will be performed. If not, validity is assessed via the theoretical construct and sensitivity analysis.

**Note**: The spec's reference to "OpenML Task ID #42238" and "Kaggle Dataset URL ()" are treated as placeholders. The implementation will use the verified HuggingFace sources listed above, as the original IDs do not correspond to datasets with the required variables.

## Methodology

### 1. Data Preprocessing
- **Ingestion**: Load raw parquet files from verified HuggingFace sources. Filter for valid choice trials.
- **Deferral Definition**: A trial is marked `deferral=1` if no choice was made within the specified time window (e.g., 24h) or if the explicit "abandonment" flag is set.
- **Regret Proxy Calculation (Min-Max Regret)**:
  - Normalize option attributes (price, rating) using **global** Min-Max scaling (dataset-wide min/max) to preserve stake magnitude.
  - Compute Expected Utility (EU) for each option as a weighted sum of normalized attributes.
  - Calculate `regret_proxy` = **max(EU) - EU_chosen** for selected options. For deferral trials, `regret_proxy` = **max(EU) - 0** (assuming zero utility for no choice, or a defined baseline).
  - Handle single-option trials: `regret_proxy` = 0.
  - **Normalization**: To account for set-size dependence, compute `normalized_regret` = `regret_proxy` / (max(EU) - min(EU)) for each trial.
- **Covariate Handling**: Impute missing covariates (e.g., perceived risk) using mean imputation or the mandatory proxy (price variance) as per FR-003. Log the number of imputed rows.

### 2. Statistical Modeling
- **Model Type**: Mixed-effects logistic regression.
- **Outcome**: Binary `deferral` (0/1).
- **Fixed Effects**:
  - `normalized_regret` (the primary predictor).
  - `option_count` (number of options) - included as a standard covariate (no residualization).
  - `perceived_risk` (or price variance proxy).
  - `time_pressure` (if available).
  - `decision_style` (if available).
  - `stakes` (global magnitude of attributes) to test interaction with regret.
  - Interaction: `normalized_regret` × `option_count`.
- **Random Effects**: Random intercept for `participant_id`.
- **Collinearity Check**: Calculate Variance Inflation Factors (VIF) for all fixed effects. Flag if VIF > 5.
- **Multiple-Comparison Correction**: **Apply Bonferroni or Benjamini-Hochberg correction** to p-values for the main effect (`normalized_regret`) and the interaction term (`normalized_regret` × `option_count`) immediately after model fitting.
- **Cross-Validation**: 5-fold CV to estimate out-of-sample AUC.

### 3. Robustness & Sensitivity
- **Secondary Dataset**: Replicate the primary analysis on the Online Shopping dataset.
- **Sensitivity Analysis**: Sweep the regret proxy definition over three **independent** variations:
  1. **Min-Max Regret** (Primary): max(EU) - EU_chosen.
  2. **Price Variance**: SD of normalized prices only.
  3. **Attribute Entropy**: Entropy of the normalized attribute distribution (measures "confusion" or "difficulty").
- **Validation**: Compare the predictive power of "Min-Max Regret" vs. "Attribute Entropy". If Min-Max Regret predicts deferral while Entropy does not (or predicts it differently), this supports the regret hypothesis over the "confusion" hypothesis.

## Addressing Reviewer Concerns (Kahneman-Simulated)

**Concern**: *Isolation of anticipated regret from general loss aversion.*
**Response**: The proposed proxy (Min-Max Regret) is specifically designed to isolate the *opportunity cost* of the chosen option rather than the magnitude of loss. By using **global** normalization (preserving stake magnitude) and measuring the gap between the best and chosen option, we distinguish regret (fear of missing out on the best) from loss aversion (fear of a specific loss). The interaction term with `stakes` allows us to test if the effect is moderated by loss magnitude.

**Concern**: *Operational definition clarity.*
**Response**: The operational definition is explicit: `regret_proxy` = max(EU) - EU_chosen. This is a structural measure derived directly from the choice set, avoiding the ambiguity of self-report. The "global normalization" step ensures comparability across trials while preserving the magnitude of stakes.

## Statistical Rigor & Assumptions

- **Observational Nature**: The study is observational. Claims will be framed as associational, not causal, unless randomization is explicitly present (which is not assumed).
- **Power & Sample Size**: A post-hoc power analysis will be conducted if the sample size is small. Given the computational constraints, we will use all available data.
- **Collinearity**: The inclusion of `option_count` as a standard covariate and the use of `normalized_regret` (regret / max_possible_regret) addresses the definitional relationship between regret and set size. VIF checks will confirm this.
- **Measurement Validity**: The proxy is validated against the theoretical construct of regret (opportunity cost). If self-report regret scores are available in the dataset, a correlation check (target r > 0.3) will be performed (SC-006).

## Computational Feasibility
All steps are designed for CPU-only execution:
- **Data**: Parquet format is efficient for streaming.
- **Model**: `statsmodels` mixed-effects models are CPU-tractable for <100k rows.
- **Memory**: Data will be processed in chunks if necessary to stay within 7GB RAM.
- **Time**: Estimated runtime < 4 hours on 2 CPU cores.