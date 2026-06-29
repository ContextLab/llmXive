# Feature Specification: Statistical Analysis of Speedrun Data

**Feature Branch**: `001-speedrun-statistics`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "How do the statistical properties of speedrun times vary across games, and what factors (game difficulty, runner experience, and competitive pressure) systematically influence the shape of learning curves and performance plateaus?"

## User Stories *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

As a researcher, I want to download and clean speedrun data from speedrun.com for multiple games so that I have a validated dataset ready for statistical analysis.

**Why this priority**: This is the foundational step—without clean, complete data, no downstream analysis can occur. It delivers the raw material for all subsequent research questions.

**Independent Test**: Can be fully tested by verifying that the script downloads run times, runner IDs, attempt numbers, and dates for the target games, removes duplicates, and outputs a CSV with ≥95% record completeness.

**Acceptance Scenarios**:

1. **Given** a list of multiple game IDs from speedrun.com, **When** the data acquisition script runs, **Then** it outputs a CSV containing run times (in seconds), runner IDs, attempt numbers, category (any%/100%), and submission dates for each game.
2. **Given** raw speedrun data with duplicate entries and incomplete runs, **When** the preprocessing step executes, **Then** duplicates are removed and records with missing run times are filtered out, leaving ≥95% of the original records.
3. **Given** a runner with multiple runs across different dates, **When** the experience metrics are computed, **Then** each runner has a derived "total prior runs" count and "time since first run" value attached to every record.

---

### User Story 2 - Distribution Fitting and Goodness-of-Fit Testing (Priority: P2)

As a researcher, I want to fit parametric distributions (log-normal, Weibull, gamma) to speedrun times and evaluate them with Kolmogorov-Smirnov tests and AIC so that I can characterize the shape of performance variability.

**Why this priority**: This addresses the first half of the research question (heavy-tailed distribution confirmation). It is testable independently of the learning-curve modeling and produces standalone insights about performance variability.

**Independent Test**: Can be fully tested by running the distribution-fitting module on a single game's run times and verifying that ≥1 distribution passes the KS test (p ≥ 0.05) and that AIC values are comparable across the 3 candidate families.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset of speedrun times for a single game, **When** the distribution-fitting module executes, **Then** it outputs maximum-likelihood estimates for log-normal, Weibull, and gamma parameters plus KS test statistics (D and p-value) and AIC for each.
2. **Given** multiple games with varying difficulty levels, **When** the module runs across all games, **Then** it produces a summary table showing which distribution family has the lowest AIC for each game.
3. **Given** a distribution that fails the KS test (p < 0.05), **When** the module reports results, **Then** it flags that distribution as rejected for that game and recommends the next-best-fitting alternative.

---

### User Story 3 - Learning-Curve Modeling with Mixed-Effects Regression (Priority: P3)

As a researcher, I want to fit hierarchical mixed-effects models (log(Time) ~ log(Attempt Number) + Game Difficulty + (1 | RunnerID)) with interaction terms for competitive pressure so that I can quantify how experience and external factors modulate performance improvement.

**Why this priority**: This addresses the second half of the research question (factors influencing learning curves). It builds on the cleaned data from US-1 but is independent of the distribution-fitting results in US-2.

**Independent Test**: Can be fully tested by fitting the mixed-effects model to a subset of runners and verifying that the model converges, produces interpretable coefficients, and returns p-values for fixed effects.

**Acceptance Scenarios**:

1. **Given** a dataset with runner IDs, attempt numbers, run times, and game difficulty labels, **When** the mixed-effects model is fit, **Then** it outputs fixed-effect coefficients (with standard errors and p-values) for log(Attempt Number), Game Difficulty, and their interaction with competitive pressure.
2. **Given** nested models (with and without difficulty/competition terms), **When** likelihood-ratio tests are performed, **Then** it reports χ² statistics and p-values comparing the models.
3. **Given** variance components from the mixed-effects model, **When** ANOVA is executed, **Then** it quantifies the proportion of variance explained by game-level vs. runner-level effects.

---

### Edge Cases

- **What happens when a game has <100 runs (insufficient data for distribution fitting)?** → The module flags the game as "low-sample" and skips distribution fitting, recording a minimum sample size of n ≥ 100 runs for Kolmogorov-Smirnov test reliability (convention in distribution fitting literature, see Stephens 1974; Marsaglia et al. 2003). Games with <100 runs are excluded from parametric fitting but retained for descriptive statistics.
- **How does the system handle runners with only 1–2 runs (no learning curve to model)?** → These runners are excluded from the mixed-effects model but retained in the dataset for descriptive statistics.
- **What happens when the GitHub Actions runner exceeds the maximum allowed duration?** → The script includes a checkpoint mechanism that saves intermediate results after each game, allowing resumption from the last completed game.
- **How does the system handle missing game difficulty labels?** → Games without external difficulty metadata are excluded from the difficulty-modulation analysis. Difficulty labels MUST come from external community rankings (e.g., Machin et al.) that are independent of run times. This prevents circular validation where the outcome variable determines the predictor.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download run times, runner IDs, attempt numbers, categories, and submission dates from speedrun.com for 10–15 games (See US-1)
- **FR-002**: System MUST remove duplicate entries and filter out incomplete runs, retaining ≥95% of original records (See US-1)
- **FR-003**: System MUST compute per-runner experience metrics (total prior runs, time since first run) for every record (See US-1)
- **FR-004**: System MUST fit log-normal, Weibull, and gamma distributions using maximum likelihood and report KS test statistics (D, p-value) and AIC for each (See US-2)
- **FR-005**: System MUST flag distributions that fail the KS test (p < 0.05) and recommend the next-best-fitting alternative (See US-2)
- **FR-006**: System MUST fit hierarchical mixed-effects models with the formula log(Time) ~ log(Attempt Number) + Game Difficulty + (1 | RunnerID) + interaction terms for competitive pressure, where Game Difficulty labels come from external community rankings (Machin et al. 2021), not run-time-derived values (See US-3)
- **FR-007**: System MUST perform likelihood-ratio tests comparing nested models (with/without difficulty or competition terms) and report χ² statistics and p-values (See US-3)
- **FR-008**: System MUST apply Bonferroni correction for multiple hypothesis tests (family-wise error rate ≤ 0.05 across all tests) (See US-3)
- **FR-009**: System MUST include a sample-size/power consideration statement (method specified, number may be `[deferred]`) acknowledging power limitations for small games (See US-3)
- **FR-010**: System MUST frame all findings as ASSOCIATIONAL (not causal) in the report, given the observational design (See US-3)
- **FR-011**: System MUST compute variance inflation factors (VIF) for all fixed-effect predictors and flag any pair with VIF > 5 as collinear (See US-3)
- **FR-012**: System MUST save intermediate results after each game (checkpoint mechanism) to allow resumption if the 6-hour limit is exceeded (See US-1)

### Key Entities *(include if feature involves data)*

- **RunRecord**: Represents a single speedrun attempt; key attributes include run_time_seconds, runner_id, attempt_number, category, submission_date, game_id
- **RunnerProfile**: Aggregates per-runner statistics; key attributes include total_prior_runs, time_since_first_run_days, games_played_count
- **GameMetadata**: Represents game-level information; key attributes include game_id, game_name, difficulty_label (from external source, see FR-006), active_runners_count (last 30 days)
- **DistributionFit**: Stores results from parametric fitting; key attributes include game_id, distribution_family, parameters (mu, sigma, etc.), KS_D, KS_pvalue, AIC
- **ModelCoefficient**: Stores mixed-effects model outputs; key attributes include predictor_name, coefficient, standard_error, p_value, random_effect_variance

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Distribution fit quality is measured against the KS test p-value threshold (p ≥ 0.05) and AIC comparison across candidate families (See US-2)
- **SC-002**: Mixed-effects model convergence is measured against successful parameter estimation (no convergence warnings) and interpretable fixed-effect coefficients (See US-3)
- **SC-003**: Data completeness is measured against the ≥95% record retention target after duplicate removal and incomplete-run filtering (See US-1)
- **SC-004**: Multiple-comparison control is measured against the Bonferroni-corrected family-wise error rate (α ≤ 0.05 across all hypothesis tests) (See US-3)
- **SC-005**: Compute feasibility is measured against successful completion within 6 hours on a GitHub Actions free-tier runner (Multiple CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU) (See US-1)
- **SC-006**: Associational framing is measured against the absence of causal language in the final report. Prohibited terms include: causal verbs (causes, affects, impacts, determines, leads to, results in) and causal nouns (effect, impact, cause, consequence). Only associational language (association, correlation, relationship, linked to) is permitted when describing relationships between variables (See US-3)

## Assumptions

- speedrun.com API provides all required variables (run times, runner IDs, attempt numbers, submission dates) for the 10–15 target games without authentication requiring a paid tier
- Game difficulty labels are available from external community rankings (e.g., Machin et al. 2021) that are independent of run times; if external difficulty labels are not available for a game, that game is excluded from the difficulty-modulation analysis
- The 10–15 target games collectively contain ≥5,000 total runs (sufficient for distribution fitting and mixed-effects modeling); games with <100 runs are flagged as "low-sample" and excluded from parametric fitting
- GitHub Actions free-tier runners provide ≥7 GB RAM and ≥14 GB disk for the entire 6-hour job; data must be sampled or subset if exceeding these limits
- Python libraries (pandas, numpy, scipy, statsmodels, matplotlib) are available on the GitHub Actions runner without requiring CUDA or GPU accelerators
- Competitive pressure can be proxied by the count of active runners (unique runner IDs) within a defined time period for each game; this proxy is validated against community activity trends
- All statistical tests assume independent observations within the mixed-effects model structure; random effects (1 | RunnerID) account for within-runner correlation
- The Kolmogorov-Smirnov test is appropriate for sample sizes ≥100; for smaller samples, the Anderson-Darling test is used as an alternative (recorded in assumptions)
- No heavy training or large-model inference is required; all methods are CPU-tractable (classical statistics, scikit-learn on modest data, exact/closed-form computation)