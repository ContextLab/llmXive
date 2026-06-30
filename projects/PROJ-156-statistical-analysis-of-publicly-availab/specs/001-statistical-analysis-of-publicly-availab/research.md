# Research: Statistical Analysis of Speedrun Data

## 1. Problem Formulation

The research question asks: *How do the statistical properties of speedrun times vary across games, and what factors (game difficulty, runner experience, and competitive pressure) systematically influence the shape of learning curves and performance plateaus?*

This is an **observational study**. No causal claims will be made. All relationships will be framed as associations (FR-010, SC-006).

## 2. Dataset Strategy

### 2.1 Primary Source: speedrun.com API
- **Source**: `
- **Variables Required**: `run_time` (seconds), `runner_id`, `attempt_number`, `category`, `date_submitted`, `game_id`.
- **Feasibility**: The API is public, rate-limited but accessible without authentication for read-only queries. It provides all variables required for FR-001.
- **Validation**: The API returns structured JSON; parsing into pandas DataFrames is standard.
- **Sample Size**: Target 10–15 games, aiming for ≥5,000 total runs. Games with <100 runs are flagged as "low-sample" and excluded from parametric fitting (Edge Case).

### 2.2 Secondary Source: Game Difficulty Metadata
- **Source**: External community rankings (e.g., Machin et al. 2021).
- **Variables Required**: `game_id`, `difficulty_label` (ordinal or categorical).
- **Constraint**: Difficulty labels MUST be independent of run times to avoid circular validation (FR-006, Edge Case).
- **Feasibility**: If no external source is available for a specific game, that game is **excluded from the difficulty-modulation analysis** but **retained for the primary learning-curve analysis** (Attempt Number only). This mitigates survivorship bias by retaining data for the core research question.

### 2.3 Proxy for Competitive Pressure (Revised)
- **Definition**: Count of unique `runner_id`s active within a **fixed-duration window preceding the specific run's submission date**.
- **Derivation**: Computed from the primary dataset (FR-001) with a temporal lag.
- **Rationale**: This temporal separation (lagged pressure) mitigates endogeneity (reverse causality: more runs causing higher pressure) and reduces collinearity with the game-level random effect.
- **Validation**: Proxy validated against community activity trends (Assumption).

### 2.4 Dataset Summary Table

| Dataset | Source | Variables | Status |
|---------|--------|-----------|--------|
| Speedrun Runs | speedrun.com API | `run_time`, `runner_id`, `attempt`, `category`, `date` | Verified (API accessible) |
| Difficulty Labels | External (e.g., Machin et al. 2021) | `game_id`, `difficulty` | Conditional (depends on availability; excluded from difficulty analysis if missing) |
| Competitive Pressure | Derived (Lagged) from Speedrun Runs | `game_id`, `active_runners_30d_prior` | Derived |

> **Note**: No HuggingFace or UCI datasets are used. The "Verified datasets" block in the user message refers to unrelated datasets (AIC, IDs) and is **not applicable** to this speedrun study. The speedrun.com API is the sole data source.

## 3. Methodological Rationale

### 3.1 Distribution Fitting (FR-004, FR-005)
- **Candidate Families**: Log-normal, Weibull, Gamma.
- **Justification**: These are standard models for right-skewed, positive-only data like run times.
- **Goodness-of-Fit**:
 - **Selection**: Best distribution selected by **AIC comparison** (information-theoretic fit).
 - **Hypothesis Testing**: Kolmogorov-Smirnov (KS) test (p ≥ 0.05) with **Bonferroni correction** applied to the p-values to control family-wise error rate (SC-004). A distribution is flagged as "rejected" if its corrected p-value < 0.05.
- **Sample Size Constraint**: KS test reliability requires n ≥ 100 (Stephens 1974). Games with <100 runs are excluded from parametric fitting.
- **Multiple Testing**: Bonferroni correction applied to KS p-values (3 tests per game) as per SC-004.

### 3.2 Mixed-Effects Modeling (FR-006, FR-007)
- **Model Formula**: `log(Time) ~ log(Attempt Number) + Game Difficulty + Lagged Competitive Pressure + (1 | RunnerID)`
 - *Note*: `total_prior_runs` is **excluded** from fixed effects due to high collinearity with `log(Attempt Number)`; it is retained only for descriptive statistics.
- **Justification**: Hierarchical structure (runs nested in runners) requires random effects to avoid pseudoreplication.
- **Interaction Terms**: `log(Attempt Number) * Game Difficulty` to test if difficulty modulates learning rate.
- **Convergence**: Checked via `statsmodels` warnings; non-convergent models are flagged.
- **Collinearity**: VIF calculated for all fixed effects; VIF > 5 flagged as collinear (FR-011).
- **Power Considerations**:
 - The number of groups (games) for the `Game Difficulty` fixed effect is small (N=10–15).
 - Statistical power to detect a significant difficulty effect is likely low regardless of total runs (N=5,000).
 - Findings for the `Game Difficulty` coefficient will be framed as **exploratory and associational**, with explicit warnings about the large margin of error and potential for Type II errors.
- **Multiple Testing**: Bonferroni correction applied to all coefficient p-values (FR-008, SC-004).
 - *Warning*: This strict correction may increase Type II error rates. Non-significant results should be interpreted as "no evidence of association" rather than "proof of no association".

### 3.3 Statistical Rigor & Assumptions
- **Multiple Comparisons**: Bonferroni correction applied to all hypothesis tests (FR-008, SC-004).
- **Causal Inference**: None. All claims are associational (FR-010, SC-006).
- **Measurement Validity**: Speedrun times are objective; difficulty labels rely on external validation.
- **Predictor Collinearity**: `log(Attempt Number)` and `total_prior_runs` are definitionally related; only `log(Attempt Number)` is included in the model to avoid collinearity (FR-011).

## 4. Compute Feasibility

- **Environment**: GitHub Actions free-tier (standard CPU allocation, 7 GB RAM, 14 GB disk, 6h limit).
- **Data Volume**: 10–15 games, [deferred] runs total. Fits easily in RAM.
- **Computation**:
 - Distribution fitting: O(n) per game; negligible time.
 - Mixed-effects: O(n * k) where k is number of runners; converges quickly for n=5,000.
- **No GPU Required**: All methods are CPU-tractable (scipy, statsmodels).
- **Checkpointing**: Intermediate results saved after each game to allow resumption (FR-012).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| speedrun.com API rate limits | Delayed data fetch | Implement exponential backoff; batch requests. |
| Missing difficulty labels | Exclusion from difficulty analysis | Games excluded only from difficulty analysis; retained for primary learning-curve analysis to mitigate survivorship bias. |
| Low power for 'Game Difficulty' effect | False negatives | Explicitly report power limitations; frame findings as exploratory/associational. |
| Endogeneity of 'Competitive Pressure' | Biased coefficients | Use **lagged** rolling average (30 days prior); frame as associational. |
| Model non-convergence | Invalid results | Use robust starting values; simplify model if needed. |
| 6-hour CI timeout | Incomplete analysis | Checkpoint after each game; resume from last success. |
| Collinearity in predictors | Biased coefficients | VIF check; exclude 'total_prior_runs' from fixed effects. |
| Type II Errors (Bonferroni) | Missed significant associations | Acknowledge in report; interpret non-significance carefully. |

## 6. Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| Use speedrun.com API | Direct access to raw run data; no paid tier needed. | Web scraping (unstable, against ToS). |
| Exclude games with <100 runs | KS test unreliable for small n. | Use Anderson-Darling (less standard for this context). |
| Use Bonferroni correction | Required by SC-004 for family-wise error rate control. | False Discovery Rate (FDR) (violates SC-004). |
| Frame as associational | Observational design; no randomization. | Causal claims (invalid without RCT). |
| Lagged Competitive Pressure | Mitigates endogeneity while satisfying FR-006. | Static game-level pressure (perfectly collinear with game ID). |
| Exclude 'total_prior_runs' from fixed effects | Avoids collinearity with 'Attempt Number'. | Including both (causes model instability). |