# Research: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Research Question
How does the duration of visual attention on source attribution (fixation duration) interact with headline emotional valence and cognitive reflection scores to predict self-reported belief susceptibility?

**Note on Phase**: The current phase is **Pipeline Validation**. The scientific hypothesis (WYSIATI) is **deferred** until a real-world dataset is acquired. The following sections describe the pipeline validation strategy.

## Dataset Strategy

The analysis requires a dataset containing:
1.  **Eye-tracking data**: Raw gaze coordinates, timestamps, and ROI definitions (specifically "source attribution" and "headline body").
2.  **Stimuli**: Text of the headlines.
3.  **Participant Data**: Cognitive Reflection Test (CRT) scores and post-task belief ratings.

### Verified Datasets
Based on the provided verified sources, the following datasets are available. **Note**: The spec assumes the existence of a dataset with *paired* eye-tracking and belief ratings. The verified sources listed below are primarily for *components* (ROIs, lexicons) or *unrelated* data. **No single verified dataset in the provided list contains the full triad of (Eye-tracking + Headline Text + Belief Rating) required for the primary scientific analysis.**

To proceed under the constraint of "verified sources only," the plan adopts a **Pipeline Validation** strategy using synthetic data. The verified datasets are used *only* to validate the *structural* and *geometric* properties of the pipeline (e.g., coordinate ranges, I-VT algorithm correctness), not to calibrate the hypothesis variables.

| Variable | Source Strategy | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **ROI Definitions / Gaze Behavior** | Use verified ROI dataset to validate I-VT algorithm and ROI mapping logic. **Not used for correlation calibration.** | `datasets.load_dataset("ROI-su7/eval_act_koch_test01", split="train")` (via parquet URL) | **Verified** (Structural Validation Only) |
| **Emotional Valence Lexicon** | Use verified NRC/VADER datasets to derive sentiment scores for synthetic headlines. | `datasets.load_dataset("bartoszmaj/vader_sentiment_full")` | **Verified** (Structural Validation Only) |
| **Cognitive Reflection (CRT)** | Synthetic generation using generic normal distribution (mean ~1.5, SD ~0.8). **No correlation with gaze.** | N/A (Simulated) | **Simulated** (Null Hypothesis) |
| **Belief Ratings** | Synthetic generation using generic uniform distribution. **No correlation with gaze or CRT.** | N/A (Simulated) | **Simulated** (Null Hypothesis) |

**Data Gap Resolution**: Since no verified dataset provides the specific experimental pairing of eye-tracking and belief ratings for *misleading headlines*, the implementation will generate a synthetic dataset that mimics the *structural* properties (e.g., coordinate ranges, trial counts) of such a study, but with **zero assumed correlation** between gaze, belief, and CRT. This ensures the pipeline is tested for its ability to handle *null results* and computational constraints, not for a pre-programmed hypothesis. The `research.md` explicitly states that the *statistical logic* is verified, but the *empirical generalizability* awaits a real-world dataset.

### Synthetic Data Generation Protocol
- **Independence Guarantee**: Gaze, belief, and CRT variables are generated from **independent random seeds** with **no shared latent variables**. This ensures that any correlation found is a bug in the generator or a result of the pipeline's processing, not an artifact of the data generation.
- **Structural Validation**: The verified ROI dataset is used to confirm that the I-VT algorithm correctly identifies fixations within realistic coordinate ranges. The VADER lexicon is used to confirm that valence scores are calculated correctly for text inputs.
- **Null Hypothesis**: The base synthetic generation assumes **zero correlation** between fixation duration, valence, and belief. The pipeline is tested to ensure it correctly reports a non-significant interaction term (p >= 0.05) in this scenario.

## Statistical Methodology

### Model Specification
The primary analysis for **Pipeline Validation** uses a Linear Mixed-Effects Model (LMM) to test the three-way interaction.
$$
Belief_{ij} = \beta_0 + \beta_1(Fixation_{ij}) + \beta_2(Valence_{ij}) + \beta_3(CRT_i) + \beta_4(Fixation \times Valence) + \beta_5(Fixation \times CRT) + \beta_6(Valence \times CRT) + \beta_7(Fixation \times Valence \times CRT) + u_{0i} + v_{0j} + \epsilon_{ij}
$$
Where:
- $i$ = Participant, $j$ = Headline/Stimulus.
- $u_{0i}$ = Random intercept for Participant.
- $v_{0j}$ = Random intercept for Headline.
- $\beta_7$ = The coefficient of interest (three-way interaction).

**Note**: This model is used to validate the *code's ability to run* the specified FR-004 model. The coefficients from this run are **Pipeline Artifacts** and have **no external validity** for the WYSIATI hypothesis.

### Statistical Rigor & Corrections
- **Multiple Comparisons**: As per FR-007 and SC-004, if multiple hypotheses are tested (e.g., main effects + interactions), the Holm-Bonferroni method will be applied to control the family-wise error rate. The `family_wise_error_rate` and `alpha_level_used` will be reported in `robustness_summary.csv`.
- **Power Analysis**: **Deferred**. A power analysis for the real-data phase will be conducted once a real dataset with known effect sizes is available. The current synthetic run does not support power analysis.
- **Causal Inference**: **Not Applicable for Synthetic Data**. Causal claims are only valid for real experimental data where independent variables are manipulated. The synthetic run is strictly for pipeline validation.
- **Collinearity**: Fixation duration and Valence may be correlated. Variance Inflation Factors (VIF) will be calculated. If VIF > 5, the model will be re-specified or the collinearity reported descriptively.
- **Outlier Handling**: As per spec, CRT scores will be capped at the extreme percentiles to prevent skewing. This is applied **before** any correlation analysis.

### WYSIATI Hypothesis & Non-Linear Effects
The WYSIATI hypothesis posits that *lack* of attention to source leads to belief. This suggests a **threshold effect** (e.g., Fixation < X ms) rather than a linear relationship. The current linear model (FR-004) is used for pipeline validation. The robustness analysis (FR-005) will test the pipeline's ability to handle these threshold variations (50/100/150ms), acknowledging the hypothesis's non-linear nature. For the **Scientific Inquiry** phase, a non-linear or threshold-based model will be prioritized.

## Robustness & Sensitivity
- **Fixation Thresholds**: The pipeline will re-run the regression with fixation duration thresholds of 50ms, 100ms, and 150ms (FR-005).
- **Lexicon Fallback**: If NRC coverage < 50% for a headline, the system switches to VADER (FR-003).
- **Sensitivity to Alpha**: The significance of the interaction term will be tested against $\alpha \in \{0.01, 0.05, 0.1\}$ in a post-hoc analysis of the robustness report (T032).

## Decision Rationale
The choice to use synthetic data for the primary pipeline validation is driven by the **absence of a verified, complete dataset** in the provided list. The verified ROI and VADER datasets are used to ensure the *structure* and *statistical logic* of the pipeline are correct. This approach satisfies the "Compute Feasibility" constraint (no GPU, small dataset) and allows for rigorous testing of the regression logic (FR-004) without waiting for a specific real-world dataset that may not exist in the public domain. **This validation is for the code, not the science.**