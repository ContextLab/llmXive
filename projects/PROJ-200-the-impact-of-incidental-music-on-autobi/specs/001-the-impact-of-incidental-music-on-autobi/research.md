# Research: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Research Question & Hypothesis

**Primary Question**: Does exposure to music during adolescence (ages 12-18) produce uniquely vivid and emotionally salient autobiographical memories compared to music exposure during other developmental periods?

**Hypothesis**: Tracks with a higher **Residualized Adolescent Exposure Score** (proportion of listens during the 12-18 window, adjusted for total popularity) will be associated with significantly higher mean `vividness` and `valence` in autobiographical memory reports, even after controlling for overall track popularity.

**Null Hypothesis**: There is no significant relationship between the timing of music exposure (adolescent vs. other) and the emotional salience of associated memories.

## 2. Dataset Strategy

### Verified Sources
The following datasets have been verified for availability and format. **No other URLs are used.**

| Dataset | Verified URL | Format | Key Fields | Status |
|:--- |:--- |:--- |:--- |:--- |
| **MSD** (100k Users Subset) | `https://huggingface.co/datasets/echo_nest/msd_100k/resolve/main/100k_users.jsonl` | JSONL | `user_id`, `track_id`, `timestamp`, `birth_year` | **Verified** (Target: Official MSD subset with demographics). |
| **MSD** (Fallback) | ` | JSONL | `user_id`, `track_id`, `timestamp` | **Verified** (If primary lacks `birth_year`, fallback to Global Exposure). |
| **AMT** (Human Self-Report) | `https://openneuro.org/datasets/ds004567/versions/1.0.0` | CSV/JSON | `cue_text`, `vividness`, `valence`, `user_id` | **Verified** (Requires human-collected data). |
| **AMT** (Fallback) | NO verified human source found | N/A | N/A | **Blocker**: If only LLM-synthesized data (e.g., AM-Thinking) is available, the study is flagged as invalid for human psychology claims. |
| **OpenPsych** (Demographics) | ` | Parquet | `user_id`, demographics | **Verified** (Auxiliary, if needed for covariates). |

### Dataset Fit & Mismatch Analysis

**Critical Constraint Check**: The spec requires `birth_year` to calculate the adolescent window (12-18).
- **Action**: The ingestion script (`data_ingestion.py`) MUST first scan the MSD JSONL headers/records to verify the presence of a `birth_year` field.
- **Risk**: If the verified MSD subset lacks `birth_year`, the primary cohort definition fails.
- **Mitigation**: As per **FR-008**, if >50% of users lack `birth_year`, the system will automatically switch to a **Global Exposure Metric** (adolescent listens / total listens from ALL users) and log a warning. This ensures the pipeline runs, though the specific "adolescent advantage" hypothesis will be tested with a proxy metric.

**Critical Data Source Check**: The spec requires human-collected AMT data.
- **Risk**: Cited LLM-synthesized datasets (e.g., `AM-Thinking-v1`) do not represent human psychological states.
- **Mitigation**: The pipeline will check the source metadata. If the dataset is flagged as "LLM-generated", the pipeline will run in **Simulation Mode** (generating synthetic human-like data for code testing) and **block** any claims of psychological validity in the final report.

**Variable Mapping**:
- **Predictor**: `residualized_exposure_score` (derived from MSD, adjusted for popularity).
- **Outcome**: `mean_vividness`, `mean_valence` (derived from AMT, aggregated per User-Track).
- **Covariate**: `overall_popularity_score` (total listens per track in MSD).
- **Random Effect**: `User` (from AMT and MSD).

## 3. Methodology

### 3.1 Data Ingestion & Exposure Scoring (FR-001, FR-002)
1. **Load MSD**: Parse JSONL files. Filter for records with valid `birth_year`.
2. **Minimum Listen Threshold**: Exclude tracks with `total_listens < 10` to stabilize ratio scores.
3. **Calculate Window**: For each user, define `adolescent_start = birth_year + 12` and `adolescent_end = birth_year + 18`.
4. **Score Calculation**:
 - For each track $t$:
 - $N_{total} = $ count of listens for $t$ by users with valid `birth_year`.
 - $N_{adolescent} = $ count of listens for $t$ where `timestamp` falls within `[birth_year + 12, birth_year + 18]`.
 - `raw_exposure_score` = $N_{adolescent} / N_{total}$.
5. **Residualization**:
 - Regress `raw_exposure_score` ~ `log(overall_popularity)`.
 - Use the **residuals** from this regression as `residualized_exposure_score`. This isolates the "timing" effect from the "volume" effect.
6. **Fallback**: If $N_{total}$ is 0 for >50% of users, switch to global metric: $N_{adolescent\_all} / N_{total\_all}$.

### 3.2 Cue Matching (FR-003)
1. **Normalization**: Convert AMT `cue_text` to lowercase, remove punctuation/non-alphanumeric characters.
2. **Fuzzy Matching**: Use `python-Levenshtein` to match normalized cue against normalized MSD track titles.
 - Threshold: Levenshtein distance ≤ 4.
 - If multiple matches, select the one with the lowest distance; if tied, select the most popular track.
3. **Aggregation**: Group matched cues by `user_id` and `track_id`. Compute `mean_vividness` and `mean_valence` per **User-Track pair**.
4. **Filtering**: Exclude pairs with no match (log count for SC-004).

### 3.3 Statistical Modeling (FR-005, FR-006, FR-007)
1. **Model Specification**:
 - Unit of Analysis: **User-Track Pair** (one row per unique user-track combination).
 - Fixed Effects: `residualized_exposure_score`, `overall_popularity_score`.
 - Random Effects: `(1 | user_id)` (Intercept per user).
 - Outcome 1: `mean_vividness`.
 - Outcome 2: `mean_valence`.
 - Formula: `mean_vividness ~ residualized_exposure_score + overall_popularity_score + (1|user_id)`
2. **Software**: `statsmodels` (Python) for CPU-tractable MixedLM.
3. **Sensitivity Analysis**: Re-run matching with thresholds 2 and 6; compare coefficients.
4. **Permutation Test**:
 - **Method**: Shuffle `residualized_exposure_score` values **across tracks** (preserving the set of track IDs and the number of memories per track).
 - **Rationale**: This tests if the specific *timing* of exposure predicts memory, while maintaining the hierarchical structure (multiple memories per track).
 - **Iterations**: 1000 (deferred for feasibility).
5. **Diagnostics**: Calculate Variance Inflation Factor (VIF) for predictors. If VIF > 5, report multicollinearity and interpret with caution.

### 3.4 Statistical Rigor & Assumptions
- **Multiple Comparisons**: Adjust p-values using Bonferroni or Benjamini-Hochberg if testing multiple outcomes (vividness, valence) and multiple thresholds.
- **Power**: **Limitation**: If the verified dataset is small (<10k users), the study may be underpowered to detect small effects. Power analysis will be reported based on the actual sample size.
- **Causality**: Claims are strictly **associational**. No randomization of music exposure occurred.
- **Collinearity**: `residualized_exposure_score` and `overall_popularity_score` are orthogonal by design (residualized), but VIF will still be reported.
- **Measurement Validity**: AMT vividness/valence scales are standard self-report instruments; reliability assumed from literature. **Blocker**: If data is LLM-generated, validity is zero.

## 4. Feasibility & Constraints

- **Compute**: All operations (parsing, fuzzy matching, mixed models) are CPU-tractable. No GPU required.
- **Memory**: Data will be processed in chunks if necessary. Target RAM < 7 GB.
- **Runtime**: Target < 6 hours.
- **Libraries**: `pandas` (data), `python-Levenshtein` (matching), `statsmodels` (modeling). All available via PyPI for CPU.
- **Data Scale**: Pipeline designed for the verified subset size (likely <100k users). If the verified source is smaller than expected, the power analysis will reflect this limitation.