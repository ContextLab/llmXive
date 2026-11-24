# Research: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Domain Overview
The “incidental exposure” hypothesis posits that music encountered during adolescence (ages 10‑19) becomes more accessible for later autobiographical recall, leading to higher vividness ratings. This is theoretically supported by the **Reminiscence Bump**, a psychological phenomenon where adults have a disproportionately high recall for events and media associated with their adolescence and early adulthood. 

Because the available data are observational and the primary predictor is based on track release years, this study investigates the association between **era-specific exposure** (music released during the user's adolescence) and memory vividness. Conclusions are strictly correlational and do not imply that the act of listening caused the memory vividness, but rather that music from that specific developmental window is more strongly linked to autobiographical recall.

## 2. Dataset Strategy
| Dataset | Type | Verified URL(s) | Role |
|---------|------|-----------------|------|
| **Million Song Dataset (MSD) – JSONL** | Open‑source track metadata & audio features | ` | Provides `track_id`, `release_year`, `track_popularity`. **Note:** MSD does **not** contain per‑user listening timestamps. To maintain construct validity, the `adolescent_exposure_ratio` is treated as a measure of **era-specific exposure** (the proportion of tracks released during the user's adolescence). This aligns with the Reminiscence Bump literature, focusing on the *origin* of the music rather than the specific *timestamp* of listening. |
| **Autobiographical Memory Test (AMT)** | Open‑source cue & rating data (user‑provided) | *No verified URL available* (not listed in the “Verified datasets” block). | Supplies free‑text memory cues, vividness (1‑7) and valence (1‑7) ratings, and user identifiers. Users must place a file named `amt.parquet` in `data/raw/` that conforms to `contracts/user_track_pair.schema.yaml`. |

*Rationale*: Both sources are directly loadable via the `datasets` library (MSD) or via pandas (AMT). No manual authentication is required, satisfying the “Data Availability” principle.

## 3. Statistical Methodology
### 3.1 Primary Model (Linear Mixed‑Effects)
- **Outcome**: `mean_vividness` (average vividness per user‑track pair).  
- **Predictors**:  
  - `logit_ratio` = logit( (ratio × (N‑1) + 0.5) / N ) – continuity‑corrected logit of `adolescent_exposure_ratio` (era-specific exposure).  
  - `track_popularity` (track popularity score).  
  - *(Note: `total_listens` is **excluded** from the model to avoid collinearity with `logit_ratio`; it is used only for filtering and weighting.)*  
- **Random Effect**: `(1|user_id)` to capture individual baseline differences.  
- **Formula**: `mean_vividness ~ logit_ratio + track_popularity + (1|user_id)`

### 3.2 Significance Testing (Block‑Permutation)
1. **Permutation Scheme**: Within each `user_id`, shuffle `mean_vividness` while keeping all predictors fixed.  
2. **Iterations**: 10,000 permutations (FR‑007).  
3. **Null Distribution**: Collect the `logit_ratio` coefficient from each permuted fit.  
4. **Two‑sided p‑value**: Proportion of |null coefficients| ≥ |observed coefficient|.  
5. **Multiple‑Comparison Control**: Apply Bonferroni correction across the five Levenshtein thresholds (α_adj = 0.05 / 5) as required by FR‑006.

### 3.3 Sensitivity Analysis (FR‑006)
- Vary Levenshtein distance thresholds `[1,2,3,4,5]`.  
- For each threshold: re‑run matching, aggregation, and the LMM.  
- Report coefficient stability and Bonferroni‑adjusted p‑values in `sensitivity_analysis.csv`.

### 3.4 Robustness Checks
| Check | Implementation |
|-------|----------------|
| **Multicollinearity** | Compute VIF for `logit_ratio` and `track_popularity`; log a warning if VIF > 5 (source: <https://arxiv.org/abs/2605.22529>). |
| **Missing Birth Years** | If > 50 % of `birth_year` are missing **before** any filtering, compute a “Global Exposure” proxy (mean `adolescent_exposure_ratio` for all tracks released in the user’s birth decade) and add `global_exposure_proxy`. |
| **Minimum Listen Threshold** | Exclude rows with `total_listens` < 5 (FR‑009). |
| **Zero‑Variance Tracks** | Drop any user‑track pair where `total_listens` = 0 (EC‑002). |

## 4. Power Analysis (FR‑011)
Using `statsmodels` power utilities (approximating the LMM as a linear regression with ICC ≈ 0.25), targeting a small‑to‑medium effect (Cohen’s f² = 0.15) at α = 0.05 yields a **required sample size of ≈ 395** observations. We round up to **400**. Anticipating attrition from FR‑009, EC‑002, and missing‑birth‑year handling, the pipeline aims to retain **≥ 500** user‑track pairs after ingestion. Post‑hoc power is computed after final filtering; it must be **≥ 0.80** (SC‑005). If N < 400, the power check will flag the limitation.

## 5. Compute Feasibility
- **CPU‑first**: All scripts run on the GitHub Actions free runner.  
- **Streaming**: MSD JSONL streamed (`datasets.load_dataset(..., streaming=True)`) to keep RAM ≤ 6 GB.  
- **Permutation Runtime**: 10,000 permutations on ~10 k rows complete in ≈ 2 h on 2 CPU cores; if runtime threatens the 6 h limit, the iteration count can be reduced (recorded in `power_report.txt`).  
- **Determinism**: `random.seed(42)` and `np.random.seed(42)` set at script start.

## 6. Decision Rationale
| Decision | Reason |
|----------|--------|
| **Use verified MSD dataset** | Provides authentic track metadata; meets data‑availability rule. |
| **Require user‑provided AMT file** | AMT not in verified list; avoids unauthorized download. |
| **Block‑Permutation (10 k iterations)** | Satisfies FR‑007; preserves intra‑user correlation. |
| **Logit transform with continuity correction** | Avoids undefined logit(0/1) per FR‑013. |
| **Exclude `total_listens` from the model** | Prevents collinearity with `logit_ratio` (scientific‑soundness‑64f2b0c6). |
| **Minimum listen filter ≥ 5** | Aligns with FR‑009. |
| **Global Exposure fallback before any filter** | Honors EC‑001 ordering. |
| **Bonferroni correction across thresholds** | Controls family‑wise error per FR‑006. |
| **VIF warning > 5 with proper citation** | Matches verified multicollinearity threshold (source <https://arxiv.org/abs/2605.22529>). |
| **Separate matched files per threshold** | Guarantees independent reproducibility and checksum tracking. |
| **Add ICC‑adjusted simulation for power analysis** | Addresses methodology‑1ca4b412 concern about clustering effects. |
| **Standardise naming to `track_popularity`** | Resolves plan_consistency‑4e4823fa mismatch. |
| **Remove incorrect ingested cohort validation** | Fixes plan_consistency‑9b34ebd8. |

## 7. Verification Strategy
Each pipeline stage writes an artifact whose SHA‑256 checksum is stored in `state.yaml`. Automated `pytest` suites (`tests/unit/`, `tests/integration/`) load each artifact, validate it against the JSON‑Schema contracts (`contracts/dataset.schema.yaml`, `contracts/output.schema.yaml`, `contracts/user_track_pair.schema.yaml`), and assert expected dimensions (e.g., each `user_track_pairs_thr{n}.parquet` contains ≥ 1 row per threshold). The CI job fails on any checksum mismatch or schema violation, guaranteeing no fabricated artifacts.

## 8. Limitations
- **Listening‑history data**: MSD lacks per‑user timestamps. The `adolescent_exposure_ratio` is therefore a proxy for **era-specific exposure** (music released during adolescence) rather than a direct measure of listening behavior. While this is theoretically grounded in the Reminiscence Bump, it remains a limitation compared to a timestamped listening history.
- **AMT availability**: The AMT dataset is not in the verified list; the pipeline expects a user‑provided file conforming to the required schema.  
- **Power**: If the final filtered dataset falls below 400 pairs, post‑hoc power will be < 80 % and will be transparently reported as a limitation.  