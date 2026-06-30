# Research: Exploring the Correlation Between Musical Preference and Personality Traits

## Research Question
Do individuals with specific Big Five personality traits show statistically significant preferences for particular musical genres, and how strong are these correlations after controlling for demographic variables (age, gender, country)?

**Note on Validation Mode**: Due to the absence of verified real-world datasets for BFI-2 and Last.fm in the "Verified datasets" block, this study operates in **Validation Mode**. The primary objective is to validate the *pipeline, methodology, and statistical rigor* (FRs) using a deterministic synthetic dataset. The study does not claim to discover empirical truths about real-world populations until verified real data is acquired.

## Dataset Strategy

The analysis requires two primary data sources:
1.  **Personality Data**: Big Five Inventory (BFI-2) scores.
2.  **Behavioral Data**: Last.fm listening history (genre tags and listening time).

### Verified Sources & Availability

| Dataset | Status | Source URL / Loader | Notes |
| :--- | :--- | :--- | :--- |
| **BFI-2** | **NO verified source found** | Synthetic/Local Mock | The "Verified datasets" block explicitly states: "BFI-2: NO verified source found". The plan will generate a synthetic dataset mimicking BFI-2 structure (Openness, Conscientiousness, etc.) with realistic correlations for the purpose of the pipeline validation. No URL will be cited. |
| **Last.fm** | **NO verified source found** | Synthetic/Local Mock | The "Verified datasets" block does not list a verified Last.fm archive URL. The plan will generate a synthetic listening dataset with genre tags mapped to the 10 target categories. No URL will be cited. |
| **Demographics** | **NO verified source found** | Synthetic/Local Mock | Derived from the synthetic personality dataset (Age, Gender, Country). |

**Decision**: Since the required specific datasets (BFI-2, Last.fm) have no verified URLs in the provided block, **we will not fabricate URLs**. Instead, the implementation will use a `code/ingest.py` module that:
1.  Attempts to fetch from canonical sources (if they exist in the wild but aren't in the verified block).
2.  **Falls back gracefully** to a deterministic synthetic generator (seeded) if the fetch fails or if the source is unverified.
3.  Logs the fallback explicitly.
This ensures the pipeline is reproducible (PR-001) and avoids the "Verified Accuracy" violation of citing non-existent URLs.

### Variable Fit Check

*   **Personality**: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism (5-point Likert or continuous).
*   **Behavioral**: `user_id`, `genre` (raw tag), `listening_minutes`.
*   **Demographics**: `age`, `gender`, `country`.
*   **Mapping**: Raw genre tags (e.g., "alt", "rock") must be mapped to: Rock, Pop, Hip-Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other.

**Risk**: If the synthetic data does not contain the necessary variance or correlation structure, the statistical tests may yield null results. This is acceptable for a pipeline validation, as the goal is to verify the *methodology* (FR-003, FR-004, FR-005) rather than discover new psychological truths from unverified data.

## Methodological Approach

### 1. Data Preprocessing (FR-001, FR-002, FR-007)
*   **Ingestion**: Load raw CSVs. If files missing, generate synthetic data with `numpy.random`.
*   **Cleaning**:
    *   Drop rows with missing `user_id`.
    *   Impute missing demographic data (Mean for Age, Mode for Gender/Country). Log counts.
    *   Filter users with `listening_minutes` = 0.
*   **Genre Standardization**: Apply the lookup table (FR-002) to map raw tags to the 10 canonical categories. Unmapped tags -> "Other".
*   **Aggregation**: Group by `user_id` and `genre` to calculate total `listening_minutes`. Normalize to `genre_score` (0-1) per user.

### 2. Statistical Analysis (FR-003, FR-004, FR-005)
*   **Correlation**: Compute Spearman rank correlation ($\rho$) between each of the 5 traits and the 10 genre scores.
    *   *Rationale*: Spearman is robust to non-normal distributions of listening time (often skewed).
*   **Regression**: For each trait, run a Multiple Linear Regression:
    $$ \text{GenreScore} = \beta_0 + \beta_1(\text{Trait}) + \beta_2(\text{Age}) + \beta_3(\text{Gender}) + \beta_4(\text{Country}) + \epsilon $$
    *   *Covariates*: Age (continuous), Gender (dummy), Country (one-hot or regional grouping if high cardinality).
    *   *Collinearity Check*: Calculate VIF. If VIF > 5 for any covariate, drop it and log a warning.
*   **Multiple Comparisons**:
    *   Total tests = 5 traits × 10 genres = 50 tests.
    *   Apply **Benjamini-Hochberg (BH) FDR** correction to the p-values.
    *   Significance threshold: Adjusted $p < 0.05$.

### 3. Effect Size & Reporting (FR-006, SC-001, SC-002, SC-003)
*   **Effect Size**: Convert Spearman $\rho$ to Pearson's $r$ (approximate) or report $\rho$ directly. Calculate Fisher's z-transformation for 95% Confidence Intervals.
*   **SC-001 Check**: Explicitly calculate `effect_size_threshold_met` (True if $|r| > 0.3$).
*   **SC-003 Check**: Run a baseline model (without covariates) and a full model (with covariates). Calculate `beta_delta` (change in coefficient) to measure the validity of demographic controls.
*   **Visualization**:
    *   Heatmap of the 5x10 correlation matrix.
    *   Bar chart of regression coefficients for significant traits.
*   **Output**: `results_report.csv` containing all metrics (rho, p, adj_p, is_significant, effect_size_r, ci_low, ci_high, effect_size_threshold_met, beta_delta).

### 4. Sensitivity Analysis (Spec Assumption)
*   **Alpha Sweep**: Run the significance test at $\alpha = 0.01, 0.05, 0.10$.
*   **Stability Check**: Report the number of significant findings at each level to verify result stability.

## Statistical Rigor & Assumptions

*   **Observational Nature**: The study is correlational. No causal claims will be made.
*   **Power Analysis**:
    *   **Sample Size**: N=500 (default for pipeline validation).
 * **Power Calculation**: For 50 tests with BH-FDR correction, detecting a small effect (r=0.15) at $\alpha=0.05$ requires N > 1000. N=500 provides [deferred] power for r=0.15 but [deferred] power for r=0.30.
    *   **Limitation**: The study is underpowered for small effects. This is acknowledged as a limitation of the "Validation Mode" synthetic dataset. If real data is acquired, N should be increased.
*   **Construct Validity**: The synthetic generator will include a "Psychometric Validation" step. It will verify that the generated BFI-2 data has high internal consistency (Cronbach's alpha > 0.7) and a plausible factor structure before proceeding. If validation fails, the pipeline halts.
*   **Multiple Testing**: The BH-FDR correction (FR-005) is explicitly applied to control the False Discovery Rate, addressing the issue of running 50+ hypothesis tests.
*   **Collinearity**: The plan includes a VIF check. If a genre is perfectly predicted by a demographic (e.g., "Country" music only by users from "USA"), the regression will detect perfect collinearity and drop the redundant predictor, logging the event.

## Compute Feasibility
* **Memory**: The synthetic dataset will be capped at [deferred] rows to ensure it fits comfortably within 7GB RAM.
*   **CPU**: All operations (Spearman, OLS Regression, BH-FDR) are $O(N \log N)$ or $O(N^2)$ and will run in seconds on a 2-core CPU.
*   **Time**: Total runtime estimated < 5 minutes.