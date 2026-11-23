# Research: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

## Problem Statement
We aim to discover whether game‑level characteristics (opening family, average move time, early material imbalance) systematically correlate with **outcome categories** (win/draw/loss) and, **if** a dataset with player ratings and move‑time metadata is available, with the **outcome deviation** from Elo expectations. Because player ratings are historical aggregates, any systematic residuals indicate model misspecification rather than causal skill effects. All conclusions will be framed as **associational**.

## Dataset Strategy

| Dataset | Verified URL | Variables Present | Gaps |
|---------|--------------|-------------------|------|
| **official‑stockfish/fishtest_pgns** (HuggingFace) | `https://huggingface.co/datasets/official-stockfish/fishtest_pgns` | `pgn` (string) | **Missing**: `white_rating`, `black_rating`, per‑move `move_times`. |

*The Lichess “big‑chess‑dataset” required by the original spec is **not** present in the verified list, and no other open dataset currently provides the full set of required fields.*  
**Action**: The pipeline first attempts to download the Stockfish PGN dataset. A verification step checks for the required columns. Because `white_rating`, `black_rating`, and `move_times` are absent, the pipeline **halts** with a clear “Dataset verification failed: required columns missing” error, satisfying Constitution Principle II.

**Revised Research Question**  
Given the lack of an open source dataset containing both ratings and move‑time metadata, the study is re‑scoped to **investigate associations between opening families, average move times, material imbalance at move 10, and the categorical game outcome (win/draw/loss)**. When (or if) a future open dataset providing the missing fields becomes available, the same pipeline can be re‑run to incorporate Elo‑based expected probabilities and outcome deviations.

## Methodological Approach

### 1. Feature Engineering (FR‑001 → FR‑004)
- **Elo Expected Probability**: Computed **only if** `white_rating` and `black_rating` exist: `P = 1 / (1 + 10**((R_black - R_white)/400))`.  
  - Probabilities are capped to `[0.0001, 0.9999]` to avoid log‑odds extremes (Edge Case 2).  
- **Outcome Deviation**: `Dev = Actual - P` (if `P` is available). When ratings are missing, `Dev` is omitted and the target becomes the categorical outcome.  
- **Material Imbalance at Move 10**: Compute piece‑value difference (P=1, N/B=3, R=5, Q=9) from the board after each side’s 10th move. Move 10 is chosen to capture opening‑phase complexity while respecting FR‑002.  
- **Average Move Time**: `avg_move_time = mean(move_times)` per player; games lacking any move‑time entry are excluded (Edge Case 3).  
- **ECO Family Collapsing**: Map ECO codes to families (e.g., “King’s Pawn”, “Queen’s Gambit”) using a static lookup table, reducing dimensionality and multicollinearity (FR‑011).  
- **Time‑Control Covariate**: Extract time‑control category from PGN tags (blitz, rapid, classical) to control for game speed (methodology‑256a282c).

### 2. Statistical Modeling (FR‑005, FR‑007)
- **Model A – Beta Regression** (`statsmodels.GLM` with `family=Beta(link=logit)`) on the transformed outcome `y = (outcome_deviation + 1) / 2` **when** Elo data are present.  
- **Model B – Ridge Regression** (`sklearn.linear_model.Ridge`) on the same transformed outcome.  
- **Predictor Set**: All engineered features **except** `white_rating` and `black_rating` (scientific_soundness‑fdc905fb). Time‑control and rating‑distribution covariates are included for adjustment but are **not** part of the primary inference set.  
- **Significance Tests**: Wald Z‑tests for Beta coefficients; bootstrapped t‑statistics for Ridge.  
- **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR applied across *all* raw p‑values from both models (FR‑009).  

### 3. Validation & Diagnostics (FR‑006, FR‑008, FR‑010)
- **5‑Fold Cross‑Validation** (k=5) on the full feature set; record R², AIC, and CV‑score distribution. **Target**: standard deviation of R² < 0.05 (SC‑003).  
- **Diagnostic Plots**: residuals vs. fitted, predicted vs. actual deviation (when applicable), feature‑importance bar chart (Ridge coefficients magnitude).  
- **Sensitivity Analysis**: Sweep corrected p‑thresholds `{0.005, 0.01, 0.05}`; compute Jaccard index of the significant‑feature sets across thresholds (target ≥ 0.8, SC‑004).  

### 4. Pilot Power Analysis (Mandatory)
A pilot of **20 k** games (if available) is drawn to estimate effect sizes for each predictor. Using `statsmodels.stats.power.FTestPower`, we compute the detectable R² with 80 % power at α = 0.01 (FDR‑adjusted).  
- **Gate**: If the detectable effect size exceeds the observed pilot effect size by > 50 %, the pipeline aborts with a “Power limitation” warning and proceeds only with a transparent limitation statement in the final report.

## Statistical Rigor Checklist
| Requirement | Method | Status |
|-------------|--------|--------|
| Multiple‑Comparison Correction | Benjamini‑Hochberg FDR (FR‑009) | ✅ Planned |
| Sample‑Size / Power | Pilot power analysis with 20 k sample (Section 4) | ✅ Planned |
| Causal Assumptions | Explicitly observational; no causal claims (Principle VII) | ✅ Planned |
| Measurement Validity | Standard Elo formula; ECO families from established taxonomy; piece‑value scheme for material imbalance | ✅ Planned |
| Collinearity Handling | ECO collapsing; Ridge regularisation; VIF check (reported) | ✅ Planned |
| Distributional Validity | Beta Regression on bounded transformed outcome (justified in Section 2) | ✅ Planned |

## Compute Feasibility Plan
- **Environment**: GitHub Actions free tier (2 CPU, ≤ 7 GB RAM).  
- **Libraries**: All CPU‑only; no CUDA imports.  
- **Data Handling**: `datasets.load_dataset(..., streaming=True)` for the Stockfish PGN dataset; incremental parsing to keep memory < 2 GB.  
- **Runtime Estimate**:  
  - Streaming + parsing ≈ tens of minutes for 100 k games.  
  - Modeling + CV ≈ a brief interval.  
  - Diagnostics & reporting ≈ a brief interval (on the order of minutes).  
  - Total < 2 h, well under the 6 h ceiling.  

## Risks & Mitigations (re‑stated)
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open dataset with required fields | Blocking – cannot compute Elo expectations; leads to scope revision (addressed above). | Abort early with explicit error; revised research question does not depend on missing fields. |
| Missing move‑time metadata | Reduced sample size; may affect power | Exclude such games; pilot power analysis will flag if sample becomes too small. |
| Memory overflow | CI crash | Streaming ingestion; optional stratified sampling. |
| Numerical extremes in probability | Division‑by‑zero / log‑of‑zero errors | Clamp probabilities to `[0.0001, 0.9999]`. |
| Under‑powered analysis | Non‑robust conclusions | Larger pilot (20 k) and explicit power‑analysis gate; report limitation if needed. |
| Confounding by time‑control or rating distribution | Spurious associations | Include time‑control and rating‑distribution covariates; later exclude from primary inference. |

---

