# Research: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

## Problem Statement

The goal is to determine if specific game features (opening choice, move time, material imbalance) systematically correlate with deviations from Elo-predicted outcomes. This involves quantifying "Elo bias" – situations where players outperform or underperform their rating-based expectations. **Crucially**, the analysis frames findings as **associational deviations from the Elo logistic model** (model misspecification) rather than causal claims about player skill, acknowledging that player ratings are cumulative estimates derived from historical outcomes influenced by these same features.

## Dataset Strategy

### Primary Data Source: Lichess Games Database (HuggingFace)
The spec requires a subset of games with **complete rating and move-time data**.
- **Verified Source**: `https://huggingface.co/datasets/lichess/big-chess-dataset` (or specific verified mirror URL).
- **Verification**: This dataset is known to contain `move_times` metadata for the specified subsets.
- **Action**: The implementation will download this specific dataset.
- **Fallback**: If the verified URL is unreachable or the dataset lacks move-time metadata for >5% of the sample, the pipeline **HALTS** immediately (Constitution Principle II) and reports the verification failure. No unverified fallbacks are permitted.
- **Variable Fit Check**:
  - **Required**: `white_rating`, `black_rating`, `eco_code`, `move_times` (per move), `outcome`, `material_state` (for move 5).
  - **Verification**: The parsing script must verify that `move_times` are present for every game. Games missing move times are **excluded** (FR-Edge Case 3), not imputed.
  - **Constraint**: If the verified source lacks move-time metadata for >5% of games, the analysis scope will be limited to the subset with complete data, and this limitation will be reported.

### Data Volume & Feasibility
- **Target**: [deferred] games (likely [deferred] - [deferred] to fit 7GB RAM).
- **Memory Management**: Data will be loaded in chunks or sampled if the full dataset exceeds RAM. The plan prioritizes a representative sample over the full corpus to ensure CPU feasibility.

## Methodological Approach

### 1. Feature Engineering (FR-001 to FR-004)
- **Elo Expectation**: Calculated using $P = 1 / (1 + 10^{(R_{black} - R_{white})/400})$.
- **Outcome Deviation**: $Dev = Actual - Expected$.
  - `Actual`: 1 (Win), 0.5 (Draw), 0 (Loss).
  - **Numerical Stability**: Probabilities capped at [0.0001, 0.9999] to prevent log-odds errors (FR-Edge Case 2).
- **Material Imbalance**: Calculated at **move 5** (not move 10) using standard piece values (P=1, N=3, B=3, R=5, Q=9).
  - **Rationale**: Move 10 is too close to the final outcome, introducing endogeneity (circularity). Move 5 provides a more independent proxy for early-game complexity.
- **ECO Collapsing**: ECO codes will be mapped to families (e.g., "King's Pawn", "Queen's Gambit") to reduce dimensionality and multicollinearity (FR-011).

### 2. Statistical Modeling (FR-005, FR-007)
- **Model A: Gaussian GLM (Identity Link)**:
  - **Rationale**: `outcome_deviation` is bounded in $[-1, 1]$ but is a **discrete, zero-inflated mixture** (spikes at 1-E, 0.5-E, -E). Standard Beta regression requires continuous (0, 1) data and is invalid here. Gaussian GLM is robust to the discrete nature of the residuals and avoids the distortion of non-linear scaling.
  - **Implementation**: `statsmodels` `GLM` with `family=Gaussian()`.
- **Model B: Ridge Regression**:
  - **Rationale**: Linear baseline with L2 regularization to handle potential multicollinearity among predictors.
  - **Implementation**: `sklearn` `Ridge`.
- **Significance Testing**:
  - **Wald Z-tests** or **Likelihood Ratio Tests (LRT)** for GLM coefficients (not t-tests, which assume normal errors).
  - **FDR Correction**: Benjamini-Hochberg procedure applied to all p-values across models and predictors (FR-009).
  - **Causal Disclaimer**: All findings are framed as **associational**. No randomization exists; the study is observational.

### 3. Validation & Diagnostics (FR-006, FR-008, FR-010)
- **Cross-Validation**: 5-fold CV to assess generalizability (SC-003).
- **Diagnostics**: Residual plots, Predicted vs. Actual scatterplots.
- **Sensitivity Analysis**: Sweep significance thresholds ($\{0.005, 0.01, 0.05\}$) to check stability of significant predictors (SC-004).

### 4. Pilot Power Analysis (Mandatory)
- **Action**: Before full ingestion, a pilot sample (e.g., a representative subset of games) will be used to estimate effect sizes and variance.
- **Gating**: If the pilot indicates the study is underpowered to detect small effect sizes (e.g., subtle biases in move time) after FDR correction, the plan mandates either:
  1. Increasing the sample size (if feasible within RAM/Runtime limits).
  2. Explicitly reporting the power limitation as a study constraint in the final report.
- **Outcome**: The full analysis will not proceed without a power justification or an explicit limitation statement.

## Statistical Rigor Checklist

| Requirement | Method | Status |
|-------------|--------|--------|
| **Multiple Comparison Correction** | Benjamini-Hochberg FDR | ✅ Planned |
| **Sample Size / Power** | Mandatory Pilot Power Analysis with gating logic. | ✅ Planned |
| **Causal Assumptions** | Explicitly stated as Observational/Associational. No causal claims. | ✅ Planned |
| **Measurement Validity** | Standard Elo formula; ECO codes from standard opening books; Move time from PGN metadata. | ✅ Planned |
| **Collinearity** | ECO codes collapsed; Ridge regularization used; Material imbalance at Move 5. | ✅ Planned |
| **Distributional Validity** | Gaussian GLM used instead of Beta Regression to handle discrete, zero-inflated outcomes. | ✅ Planned |

## Compute Feasibility Plan

- **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Libraries**: `scikit-learn` (CPU only), `statsmodels` (CPU only). No deep learning frameworks.
- **Data Sampling**: If the dataset exceeds 7 GB, a random sample (stratified by rating) will be taken.
- **Runtime**: Estimated < 2 hours for 50k games.
- **No GPU**: All operations are CPU-tractable.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No Verified Chess Dataset** | Blocking | Pipeline HALTS immediately if the verified HuggingFace URL is unreachable or metadata is missing. |
| **Missing Move Time Data** | Bias | Exclude games with missing move times (FR-Edge Case 3). |
| **Memory Overflow** | Crash | Stream data or sample aggressively. Use `dtype` optimization (float32). |
| **Numerical Instability** | Error | Cap probabilities at [0.0001, 0.9999]. |
| **Endogeneity (Material Imbalance)** | Bias | Use Move 5 instead of Move 10 to reduce circularity. |
| **Underpowered Study** | Invalid Results | Mandatory Pilot Power Analysis with gating logic. |