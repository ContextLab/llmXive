# Research: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

## Executive Summary

This research plan addresses the prediction of time-to-peak softening in aluminum alloys based on cold work percentage and alloy composition. The core hypothesis is that the relationship between cold work and recrystallization is modulated by alloying elements (Mn, Si, Cu, Mg) via a "pinning effect," which can be captured by explicit interaction features.

**Critical Scope Clarification**: Since no verified public dataset exists containing the specific triad of **cold work percentage**, **specific alloying element concentrations (Mg, Si, Cu, Mn)**, and **time-to-peak softening** for aluminum alloys, this study relies exclusively on a deterministic synthetic generator. Consequently, the primary objective is **not** to validate the physical existence of the pinning effect in reality (which requires empirical data), but to **validate the analysis pipeline's ability to detect the pinning effect** in data generated with that mechanism. The statistical significance tests (Permutation, SHAP) serve as a "sanity check" to confirm the pipeline correctly identifies the signal embedded in the synthetic ground truth.

## Dataset Strategy

### Primary Source: Deterministic Synthetic Generator
- **Generator Logic**: The generator simulates physical recrystallization kinetics based on established empirical relationships (e.g., Avrami-type kinetics modified for solute drag and particle pinning).
  - *Note*: The generator introduces controlled Gaussian noise to the target variable to prevent perfect mathematical collinearity between `cold_work` and `cold_work * Mn`, ensuring numerical stability in SHAP calculations.
- **Seed**: Fixed at `42` to ensure reproducibility (Constitution Principle I).
- **Variables Generated**:
 - `cold_work`: Continuous variable (0–[deferred]).
  - `alloy_composition`: Dict/Mappings for Mg, Si, Cu, Mn (wt%).
  - `annealing_temp`: Continuous variable (K).
  - `time_to_peak`: Target variable (minutes).
- **Sample Size & Power**: The generator will produce **[deferred] samples**.
 - *Rationale*: A power analysis for non-parametric permutation tests on interaction effects suggests that ~500 samples are required to detect moderate effect sizes with p < 0.05 and power > 0.8. We select [deferred] to ensure robust statistical power while remaining well within the <10,000 row constraint (Constitution Principle VII).

### Secondary Sources (Unavailable)
- **NIST / HuggingFace**: The verified dataset block provided in the prompt contains cybersecurity embeddings and LLM leaderboards, which are irrelevant to materials science.
- **Action**: No attempt will be made to scrape or guess URLs for materials science datasets. The plan relies exclusively on the synthetic generator. If a real dataset is required for validation later, it must be explicitly sourced and verified before use.

### Data Handling Plan
1. **Generation**: Run `generate_synthetic.py` with seed=42.
2. **Cleaning**: Apply mean imputation for any synthetic anomalies (should be rare) and clip outliers in `time_to_peak` at the 99th percentile (FR-007).
3. **Validation**: Check for <50 rows (FR-008) and zero-variance composition columns.

## Methodology

### 1. Feature Engineering (FR-002, Constitution Principle VI)
The core innovation of this study is the explicit construction of interaction terms.
- **Base Features**: `cold_work`, `Mg`, `Si`, `Cu`, `Mn`, `annealing_temp`.
- **Interaction Features**:
  - `cold_work * Mg`
  - `cold_work * Si`
  - `cold_work * Cu`
  - `cold_work * Mn`
- **Rationale**: These terms capture the hypothesis that the effectiveness of cold work in driving recrystallization is reduced (or altered) by the presence of dispersoid-forming elements (pinning effect).

### 2. Model Selection (FR-003)
- **Algorithm**: Random Forest Regressor (Scikit-learn).
- **Justification**:
  - Handles non-linear relationships and interactions naturally.
  - Robust to outliers (compared to linear regression).
  - Provides built-in feature importance.
  - **CPU-First**: Runs efficiently on 2-CPU/4GB RAM for <10k rows.
- **Configuration**:
  - `n_estimators`: 100 (default).
  - `random_state`: 42.
  - `max_depth`: [deferred] (tuned via CV if needed, but default preferred for simplicity).

### 3. Statistical Validation (FR-005, FR-006)
The validation strategy addresses the methodological concerns regarding interaction effects and collinearity.

#### A. Delta-Permutation Test (Validating Interaction Significance)
To test if interaction terms provide a statistically significant improvement over an additive baseline, we employ a **Delta-Permutation Test**:
1. **Train Model A (Additive)**: `cold_work` + `composition` + `temp`.
2. **Train Model B (Interaction)**: Model A + `interaction_terms`.
3. **Calculate Baseline Delta**: Compute `Delta_Original = MAE(Model A) - MAE(Model B)`. (Positive delta implies Model B is better).
4. **Permutation Procedure**:
   - Shuffle the `interaction_terms` columns in Model B's input data `N` times (where N = [deferred], e.g., 1000).
   - For each shuffle, re-predict and calculate `MAE(Shuffled Model B)`.
   - Compute `Delta_Shuffled = MAE(Model A) - MAE(Shuffled Model B)`.
5. **P-Value Calculation**: The p-value is the proportion of `Delta_Shuffled` values that are greater than or equal to `Delta_Original`.
   - *Null Hypothesis*: The interaction terms provide no improvement (Delta is zero or negative).
   - *Significance*: p < 0.05 (SC-002).
6. **Synthetic Data Context**: In this synthetic setup, where the target is generated with the interaction mechanism, a p-value ~0.0 is expected. The test validates that the pipeline correctly detects the signal.

#### B. SHAP Interaction Values (Addressing Collinearity)
Standard feature importance is biased by the collinearity between `cold_work` and `cold_work * Mn`. To isolate the specific contribution of the interaction:
- **Method**: Use `shap.TreeExplainer` with `interaction_values=True`.
- **Output**: This decomposes the prediction into main effects and interaction effects (e.g., `cold_work` contribution, `Mn` contribution, and `cold_work * Mn` contribution).
- **Validation**: We will report the mean absolute SHAP interaction value for the `cold_work * Mn` term. This metric explicitly quantifies the unique variance explained by the pinning hypothesis, independent of the main effects.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: The permutation test inherently controls for the specific comparison being made (Interaction vs. Additive). If multiple interaction terms are tested individually, a Bonferroni correction will be applied to the p-values (SC-002).
- **Sample Size**: The synthetic generator will produce [deferred] rows. A minimum of 50 rows is enforced (FR-008). The [deferred]-row size is justified by power analysis for non-parametric interaction tests.
- **Causal Claims**: None. The study is observational (even with synthetic data). Claims will be framed as "associative" or "predictive" (Assumption 2).
- **Collinearity**: `cold_work` and `cold_work * Mn` are definitionally related. The plan acknowledges this collinearity. **SHAP Interaction Values** are used specifically because they are designed to handle correlated features by attributing the interaction effect to the pair rather than splitting it. The synthetic generator includes noise to prevent perfect collinearity.

## Synthetic Data Limitation & Interpretation

- **Tautological Validation**: Since the target `time_to_peak` is generated using a formula that includes the interaction terms, the permutation test will inevitably yield a significant p-value (p ~ 0.0). This is not a discovery of a new physical law but a **verification of the analysis pipeline**.
- **Scientific Value**: The study demonstrates that the proposed pipeline (Feature Engineering -> Random Forest -> Delta-Permutation Test -> SHAP Interaction) is capable of detecting the pinning effect when it exists in the data.
- **Future Work**: To validate the physical hypothesis in reality, this pipeline must be applied to a verified experimental dataset containing real-world measurements of cold work, composition, and softening time.

## Compute Feasibility (CPU-First)
- **Runtime**: Random Forest on [deferred] rows with <20 features will complete in <10 minutes on a standard 2-CPU runner.
- **Memory**: Dataset size <10k rows fits easily in 4GB RAM.
- **GPU Escape Hatch**: Not required. The Random Forest algorithm and permutation test are CPU-tractable.

## References
- **Synthetic Generator**: Custom implementation based on literature principles (Avrami kinetics, Zener pinning).
- **Statistical Methods**: Scikit-learn documentation for Random Forest and Permutation Tests; SHAP documentation for interaction values.
- **Constitution**: Adherence to Project Constitution Principles I-VII.