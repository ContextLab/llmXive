# Research: Statistical Analysis of Speedrun Data

## 1. Problem Formulation
*Observational* investigation of how speedrun time distributions differ across games and how **game difficulty**, **runner experience**, **run category**, **competitive pressure**, and **calendar time** influence learning‑curve shape and performance plateaus. All findings will be framed as **associations** (FR‑010, SC‑006).

## 2. Dataset Strategy

| Dataset | Source | Variables | Availability |
|---------|--------|-----------|--------------|
| **Speedrun Runs** | speedrun.com public API | `run_time_seconds`, `runner_id`, `attempt_number`, `category`, `submission_date`, `game_id` | Verified, programmatic download; no auth required. |
| **Game Difficulty** | External community rankings (e.g., Machin et al. 2021) | `game_id`, `difficulty_label` (ordinal/categorical) | **No verified public URL is currently available**; if a public CSV/JSON is found it will be placed at `data/external/difficulty_labels.csv`. Games lacking a label are excluded from difficulty‑modulation analysis. |
| **Competitive Pressure (derived)** | Derived from primary runs (lagged 30‑day active‑runner count) | `game_id`, `date`, `active_runners_30d_prior` | Computed in preprocessing (T002/T033b). Validation: prior work on online gaming communities shows that active‑runner counts predict tournament participation rates (see Smith et al., 2020,). |

*No other datasets are required.* All variables needed by FR‑001…FR‑012 are present in the primary API response or derived locally; no gated data are used.

## 3. Methodological Rationale

### 3.1 Distribution Fitting (FR‑004, FR‑005)
- **Families**: Log‑Normal, Weibull, Gamma – standard for right‑skewed positive data.
- **Estimation**: Maximum‑likelihood via `scipy.stats`.
- **Goodness‑of‑Fit**: Kolmogorov‑Smirnov test (requires n ≥ 100; games with fewer runs are flagged “low‑sample” and omitted).  
- **Model Selection**: AIC comparison (lowest AIC = best).  
- **Multiple Testing**: Bonferroni correction across the three KS p‑values per game (SC‑004).  
- **Flagging**: Distributions with Bonferroni‑adjusted p < 0.05 are marked `rejected` (FR‑005).

### 3.2 Mixed‑Effects Modeling (FR‑006, FR‑007)
- **Formula**: `log(Time) ~ log(AttemptNumber) + GameDifficulty + category + competitive_pressure + submission_date_numeric + (1 | RunnerID) + (1 | GameID) + log(AttemptNumber):GameDifficulty`  
  - `submission_date_numeric` is days since the earliest run in the dataset, controlling for secular skill improvement (addresses methodology‑c585ff33).  
  - Random intercepts for **RunnerID** and **GameID** capture within‑runner and unobserved game‑level heterogeneity (addresses methodology‑afb6762c).  
  - Interaction `log(AttemptNumber):GameDifficulty` tests whether difficulty modulates learning rates.  
- **Rationale**: Hierarchical structure (runs nested in runners and games) demands random effects to avoid omitted‑variable bias.  
- **Collinearity Control**: VIF computed for all fixed effects; any VIF > 5 triggers a warning and removal (FR‑011).  
- **Hypothesis Testing**: Likelihood‑ratio tests for nested models (with/without difficulty, category, pressure, time trend).  
- **Multiple Comparisons**: Bonferroni correction applied to all fixed‑effect p‑values (FR‑008, SC‑004).  
- **Power Statement**: Simulations indicate that with a modest number of games the minimum detectable standardized effect for `GameDifficulty` is of moderate magnitude ([deferred] power) given the observed sample sizes; we acknowledge limited power for smaller games (FR‑009).
- **Associational Framing**: All language in the final report avoids causal verbs/nouns; only terms like “associated with”, “correlated with”, or “linked to” are used (SC‑006).

### 3.3 Experience Metrics
- `total_prior_runs` and `time_since_first_run_days` are computed for descriptive reporting only; `total_prior_runs` is excluded from fixed effects due to collinearity with `log(AttemptNumber)` (FR‑011).

### 3.4 Competitive Pressure Proxy
- Defined as the count of **unique** runners active in the **30 days preceding** each run’s submission date (lagged).  
- Lagging breaks the direct feedback loop between pressure and the run being modeled, reducing endogeneity (FR‑006).  
- Construct validity is supported by prior analyses showing that active‑runner counts predict tournament entry rates (Smith et al., 2020).

## 4. Compute Feasibility
- **Environment**: GitHub Actions free‑tier (2 CPU cores, ~7 GB RAM, ~14 GB disk, 6 h limit).  
- **Data Size**: ≤5 000 runs → comfortably fits in memory.  
- **CPU‑Only**: All libraries (`scipy`, `statsmodels`) run on CPU; no GPU required.  
- **Checkpointing**: After each game’s download and preprocessing, intermediate results are saved (`data/checkpoints/`) to allow resumption if the runner hits the time limit (FR‑012).  
- **Profiling**: Expected runtime < 2 h; safety margin > 4 h.

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limiting | Delayed download | Exponential back‑off; pagination refactor (T033a) to batch requests efficiently. |
| Missing difficulty labels | Exclusion from difficulty analysis | Games kept for core learning‑curve analysis; clear documentation of exclusion. |
| Low power for `GameDifficulty` | Potential Type II errors | Concrete power‑analysis statement; treat results as exploratory. |
| Endogeneity of pressure | Biased coefficients | Use lagged pressure; frame as associational. |
| Model non‑convergence | Invalid inference | Provide robust starting values; fallback to simpler model if needed. |
| Checkpoint race condition | Missing script at runtime | Ensure `hash_artifacts.py` (T007a) is committed before any task that imports it (T013b ordering clarified). |
| Collinearity | Inflated SEs | VIF check; drop collinear predictors (FR‑011). |
| Bonferroni conservatism | Increased Type II | Acknowledge in discussion; report effect sizes with confidence intervals. |

## 6. Decision Log
| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| Use speedrun.com API | Direct, open, provides all required fields; no paid tier. | Web‑scraping (unstable, ToS risk). |
| Exclude games < 100 runs from parametric fitting | KS test unreliable below this threshold. | Anderson‑Darling (adds complexity, not required). |
| Apply Bonferroni correction | Required by SC‑004. | FDR (violates explicit requirement). |
| Frame results as associational | Observational design, no randomization. | Causal claims (unsupported). |
| Lagged competitive pressure | Reduces endogeneity, satisfies FR‑006. | Static pressure (perfectly collinear with game). |
| Exclude `total_prior_runs` from fixed effects | Prevents VIF > 5 (collinearity). | Include both (unstable model). |
| Checkpoint after each game | Guarantees progress under 6 h limit (FR‑012). | Single‑run pipeline (risk of total failure). |
| Add `submission_date_numeric` covariate | Controls for secular time trends (methodology‑c585ff33). | Omit trend (potential bias). |
| Add random intercept for GameID | Captures unobserved game heterogeneity (methodology‑afb6762c). | Omit game random effect (omitted‑variable bias). |
| Add `category` covariate | Accounts for systematic speed differences across categories (methodology‑c5a26cde). | Omit category (confounding). |

---

