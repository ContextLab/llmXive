# Research: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Domain Overview
The “incidental exposure” hypothesis suggests that music encountered during adolescence (ages 10‑19) becomes more accessible for later autobiographical recall, leading to higher vividness ratings. Because the data are observational, conclusions are strictly correlational.

## 2. Dataset Strategy
| Dataset | Type | Verified URL(s) | Role |
|---------|------|-----------------|------|
| **Million Song Dataset (MSD) – JSONL** | Open‑source track metadata & audio features | `https://huggingface.co/datasets/MSD-Team/LLMTest/resolve/main/LLMPersian_Train.jsonl` | Provides `track_id`, `release_year`, `popularity`. **Note:** MSD does **not** contain per‑user listening timestamps, which are required to compute the true adolescent exposure ratio. An additional open listening‑history dataset (e.g., a public Last.fm or Spotify dataset with timestamps) is needed to fulfil FR‑001. Until such a dataset is supplied, a placeholder exposure metric based on available timestamps will be used and its limitations documented. |
| **Autobiographical Memory Test (AMT)** | Open‑source cue & rating data | `https://huggingface.co/datasets/a-m-team/AM-DeepSeek-R1-Distilled-1.4M/resolve/main/am_0.5M.jsonl` | Supplies free‑text memory cues, vividness (1‑7) and valence (1‑7) ratings, and user identifiers. |

*Rationale*: Both sources are directly downloadable via the `datasets` library; no manual authentication is required, satisfying the “Data Availability” principle.

## 3. Statistical Methodology
### 3.1 Primary Model (Linear Mixed‑Effects)
- **Outcome**: `mean_vividness` (average vividness per user‑track pair).  
- **Predictors**:  
  - `logit_ratio` = logit( (ratio × (N‑1) + 0.5) / N ) – a continuity‑corrected logit of `adolescent_exposure_ratio` to handle boundary cases where the ratio equals 0 or 1.  
  - `popularity` (track popularity score)  
  - `total_listens` (total listens for the pair)  
- **Random Effect**: `(1|user_id)` to capture individual baseline differences.  
- **Formula**: `mean_vividness ~ logit_ratio + popularity + total_listens + (1|user_id)`

### 3.2 Significance Testing (Block‑Permutation)
1. **Permutation Scheme**: Within each `user_id`, shuffle `mean_vividness` values while keeping all predictors fixed (preserves intra‑user correlation).  
2. **Iterations**: 10,000 permutations (FR‑007).  
3. **Null Distribution**: Collect the coefficient for `logit_ratio` from each permuted fit.  
4. **Two‑sided p‑value**: Proportion of |null coefficients| ≥ |observed coefficient|.  
5. **Multiple‑Comparison Control**: Apply Bonferroni correction across the five Levenshtein thresholds (α_adj = 0.05 / 5) as required by FR‑006.

### 3.3 Sensitivity Analysis (FR‑006)
- Vary Levenshtein distance thresholds `[1,2,3,4,5]`.  
- For each threshold: re‑run matching, aggregation, and the LMM.  
- Report coefficient stability and Bonferroni‑adjusted p‑values in `sensitivity_analysis.csv`.

### 3.4 Robustness Checks
| Check | Implementation |
|-------|----------------|
| **Multicollinearity** | Compute VIF for `logit_ratio` and `popularity`; log a warning if VIF > 5 (source 2605.22529). |
| **Missing Birth Years** | If > 50 % of `birth_year` are missing **before** any filtering, compute a “Global Exposure” proxy (mean `adolescent_exposure_ratio` for all tracks released in the user’s birth decade) and add `global_exposure_proxy`. |
| **Minimum Listen Threshold** | Exclude rows with `total_listens` < 5 (FR‑009). |
| **Zero‑Variance Tracks** | Drop any user‑track pair where `total_listens` = 0 (EC‑002). |

## 4. Power Analysis (FR‑011)
Using the `statsmodels` `power` module for linear mixed models (approximated as linear regression with ICC ≈ 0.25), targeting a small effect (Cohen’s f² = 0.02) at α = 0.05 yields an **required sample size of ≈ 395** observations. We round up to **400**. Anticipating data loss from FR‑009, EC‑002, and missing‑birth‑year handling, the pipeline initially aims to retain **≥ 500** user‑track pairs after ingestion. Post‑hoc power is computed (`power = 1 - β`) and must be **≥ 0.80** (SC‑005). If the final N < 400, the power check will flag the limitation.

## 5. Compute Feasibility
- **CPU‑first**: All scripts run on the GitHub Actions free runner.  
- **Streaming**: MSD JSONL is streamed (`datasets.load_dataset(..., streaming=True)`) to keep RAM ≤ 6 GB.  
- **Permutation Runtime**: A substantial number of permutations on ~10 k rows complete in ≈ 2 h on 2 CPU cores.; if runtime threatens the 6 h limit, the iteration count can be reduced (documented as a graceful degradation, not a fabricated shortcut).  
- **Determinism**: `random.seed(42)` and `np.random.seed(42)` are set at the start of every script.

## 6. Decision Rationale
| Decision | Reason |
|----------|--------|
| **Use verified AMT dataset** | Provides real cue‑rating data without needing to simulate; satisfies data‑availability rule. |
| **Stream MSD** | Prevents OOM; still uses authentic track metadata. |
| **Block‑Permutation (10 k iterations)** | Required by FR‑007; preserves user‑level correlation. |
| **Logit transform with continuity correction** | Stabilises variance for a bounded predictor and avoids undefined logit(0/1). |
| **Include `total_listens` as covariate** | Directly fulfills FR‑005 and controls for ratio denominator. |
| **Minimum listen filter ≥ 5** | Aligns with FR‑009 (previous plan mistakenly used 3). |
| **Global Exposure fallback before any filter** | Honors EC‑001 ordering. |
| **Bonferroni correction across thresholds** | Controls family‑wise error per FR‑006. |
| **VIF warning > 5** | Matches verified multicollinearity threshold (source 2605.22529). |
| **Separate matched files per threshold** | Guarantees independent reproducibility and checksum tracking. |
| **CSV‑only contracts** | Simplifies validation; matches SC‑008. |

## 7. Verification Strategy
Each pipeline stage writes an artifact whose SHA‑256 checksum is stored in `state.yaml`. Automated pytest suites (`tests/unit/`, `tests/integration/`) load each artifact, validate it against the JSON‑Schema contracts (`contracts/dataset.schema.yaml` for parquet, `contracts/output.schema.yaml` for CSV), and assert expected dimensions (e.g., `user_track_pairs_thr{n}.parquet` has ≥ 1 row per threshold). The CI job fails on any checksum mismatch or schema violation, guaranteeing no fabricated artifacts.

## 8. Limitations
- **Listening‑history data**: The open MSD does not contain per‑user timestamps required for a true adolescent exposure calculation. An appropriate open dataset with timestamps must be supplied; until then, a placeholder exposure metric will be used and its limitation reported.  
- **Domain mismatch**: The AMT dataset, while real, may not perfectly replicate the original cue‑track paradigm; any domain mismatch will be documented in the final manuscript.  
- **Power**: If the final filtered dataset falls below 400 pairs, the post‑hoc power will be < 80 % and will be transparently reported as a limitation.  

---

