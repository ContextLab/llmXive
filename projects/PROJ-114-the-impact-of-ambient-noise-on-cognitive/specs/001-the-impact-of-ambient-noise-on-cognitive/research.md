# Research: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

## Research Question & Hypothesis (Reframed for Prototype Phase)

**Primary Question (Current Phase)**: Can the statistical pipeline correctly ingest, preprocess, and model non-linear relationships between ambient noise and cognitive flexibility when provided with appropriate data structures?

**Secondary Question (Future Phase)**: Does objectively measured ambient noise in home work environments affect cognitive flexibility in remote workers, and does this relationship follow a non-linear (inverted-U) pattern?

**Hypothesis (Prototype)**: The pipeline will correctly identify a non-linear relationship **if** an inverted-U pattern is injected into the synthetic data (Debug Mode), and will correctly return a null result **if** noise is generated independently of performance (Standard Validation Mode).

**Hypothesis (Scientific)**: Cognitive flexibility (measured by task-switching performance) will peak at moderate noise levels (~45-65 dB) and decline at both low (<45 dB) and high (>65 dB) levels, consistent with the "inverted-U" hypothesis (Arousal Theory). *Note: This hypothesis cannot be tested with the current dataset configuration.*

## Dataset Strategy

The analysis relies on the following verified dataset. No other datasets are used for behavioral outcomes.

| Dataset Name | Description | Source URL | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **MTurk Task Scores** | Aggregated task-switching performance scores and participant metadata. | [https://huggingface.co/datasets/mdcgp/mturk_scores/resolve/main/final_turk_with_scores.csv](https://huggingface.co/datasets/mdcgp/mturk_scores/resolve/main/final_turk_with_scores.csv) | Primary source for `TaskScore` entities. Contains reaction times, error counts, and participant IDs. |
| **Synthetic Noise Logs** | *Note*: No verified public dataset links continuous ambient noise logs to specific MTurk participants. The `preprocess.py` module will generate synthetic noise logs aligned with the MTurk participant IDs for the purpose of **pipeline validation**. | N/A (Synthetic for pipeline validation) | Used to test `FR-001` (filtering), `FR-002` (aggregation), and `FR-003` (normalization) logic. **Crucially**, this data is **NOT** used to draw scientific conclusions about the "inverted-U" effect in this phase. |

**Dataset-Variable Fit Verification**:
- **Required Variables**: `participant_id`, `reaction_time`, `trial_type` (switch/repeat), `test_time` (baseline/final), `noise_level` (continuous), `noise_std` (variability).
- **Fit Status**: 
  - **Behavioral**: The MTurk dataset is verified to contain `participant_id` and `reaction_time`. **Schema Verification Step**: The pipeline will first inspect the CSV headers to confirm the presence of `trial_type` (switch/repeat) and `test_time` (baseline/final). If these columns are missing, the pipeline will halt with a `SchemaMismatchError` and report that the analysis cannot proceed.
  - **Environmental**: The noise variables are simulated for the pipeline to ensure the *code* works, as the spec describes a "mobile app deployment" for noise logging which is not present in the static CSV. The plan explicitly handles this by generating synthetic noise data aligned with the verified MTurk IDs for the `data/processed/` stage.

**Simulation Fidelity & Validation Modes**:
To address the risk of circular validation or tautological results:
1.  **Standard Validation Mode (Default)**: Synthetic noise is generated as **random independent noise** (uniform distribution). The pipeline is expected to return **non-significant** results for the quadratic term. This validates that the model does not hallucinate relationships.
2.  **Debug Mode (Unit Test)**: Synthetic noise is generated with a **known injected inverted-U relationship**. The pipeline is expected to detect this relationship. This validates that the model *can* detect non-linearity if it exists.
3.  **Scientific Inquiry Mode (Deferred)**: Requires a real dataset with both noise and behavior. This mode is currently **unavailable**.

## Statistical Methodology

### 1. Preprocessing (FR-001 to FR-003)
- **Filtering**: Exclude participants with <80% valid logging hours or <90% task completion.
- **Normalization**: Log-transform reaction times. Remove outliers using the Median Absolute Deviation (MAD) method (threshold = 3.5 * MAD) per participant.
- **Aggregation**: Bin noise into Low (≤44.9), Moderate (45.0–64.9), High (≥65.0). Calculate hourly standard deviation.
- **Schema Check**: Before any analysis, the pipeline verifies that the input MTurk CSV contains `trial_type` and `test_time` columns. If missing, the run aborts.

### 2. Primary Analysis (FR-004, FR-005, FR-008)
- **Model**: Linear Mixed-Effects Model (LMM) using `statsmodels`.
  - **Outcome**: Normalized Reaction Time (RT).
  - **Fixed Effects**: `Avg_Noise` (continuous), `Avg_Noise^2` (quadratic), `Noise_Std` (variability), `Trial_Type` (switch/repeat).
  - **Random Effects**: Random intercept for `Participant_ID`.
- **Hypothesis Test**: Likelihood-Ratio Test (LRT) comparing the Quadratic Model vs. a Linear Model (without the squared term).
  - **Interpretation**: In **Standard Validation Mode**, a significant LRT indicates a bug (spurious correlation). In **Debug Mode**, a non-significant LRT indicates a bug (failure to detect injected effect). In **Scientific Mode**, a significant LRT supports the hypothesis.
- **Post-Hoc**: Tukey HSD for pairwise comparisons between noise bins (Low vs. Mod, Mod vs. High, Low vs. High).
- **Correction**: Bonferroni or FDR correction applied to all p-values from the post-hoc tests (FR-008).

### 3. Robustness & Sensitivity (FR-006, FR-007)
- **Sensitivity Sweep**: Re-run the primary model with thresholds shifted by ±5 dB (Low: {40, 45, 50}, High: {60, 65, 70}). Report the variation in significance rates.
- **Baseline Control**: Replicate analysis using only `Final_Score` - `Baseline_Score` (delta RT) to isolate environmental effects.
- **Convergence Check**: If model fails to converge, flag and report power limitation (Constitution VII).

## Decision Rationale

**Why LMM?**
Remote worker data is hierarchical (multiple trials per participant). LMMs correctly model within-subject correlation and handle unbalanced data (missing logs) better than repeated-measures ANOVA.

**Why CPU-Only?**
The sample size (N=150) and model complexity (LMM with 3-4 fixed effects) are well within the capabilities of standard CPU-optimized libraries (`statsmodels`, `lme4` equivalent in Python). No GPU is required or permitted.

**Why Synthetic Noise for Pipeline?**
The spec describes a "mobile app deployment" for noise logging. The verified dataset (MTurk CSV) contains only task scores. To ensure the *implementation pipeline* (filtering, aggregation, modeling) is testable and reproducible on the CI runner, the `preprocess.py` step will generate synthetic noise data. **This is strictly for code validation.** The plan explicitly acknowledges that this approach **cannot** validate the scientific "inverted-U" hypothesis.

## Power & Limitations

- **Sample Size**: N=150 is assumed sufficient for a medium effect size (f² ≈ 0.15) in an LMM. If convergence fails or power is low, this will be explicitly reported as a limitation (SC-005).
- **Observational Nature**: The study is observational. Claims will be framed as "associational" (Constitution Assumption).
- **Noise Measurement**: Relies on the assumption that the mobile app logs are calibrated. The sensitivity analysis (FR-006) mitigates calibration errors.
- **Causal Validity Gap**: **Critical Limitation**: The current implementation uses synthetic noise data. Therefore, **no scientific conclusions** regarding the relationship between ambient noise and cognitive flexibility can be drawn from this run. The results are strictly for **pipeline validation**. The scientific hypothesis test is **deferred** pending the acquisition of a real dataset with linked noise and behavioral data.

## Circularity Mitigation

To ensure the analysis does not validate a spurious relationship:
- The synthetic predictor (noise) is generated either as **statistically independent** of the outcome (Standard Mode) or with a **known injected effect** (Debug Mode).
- The Likelihood-Ratio Test (LRT) is interpreted strictly as a **unit test**:
  - **Standard Mode**: Expected result = Null. If significant, the pipeline has a bug (spurious correlation).
  - **Debug Mode**: Expected result = Significant. If null, the pipeline has a bug (failure to detect effect).
- This approach separates **testing the code** from **testing the hypothesis**, ensuring the LRT is not misinterpreted as an empirical finding on synthetic data.