# Data Model: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Data Flow Diagram
```mermaid
graph TD
    A[Raw MSD JSONL (streamed)] -->|download.py| B[data/raw/msd_*.jsonl]
    C[User‑provided AMT Parquet] -->|ingest.py| D[data/processed/ingested_cohort.parquet]
    B --> D
    D -->|match.py (thresholds 1‑5)| E[data/processed/matched_thr{n}.parquet]
    E -->|aggregate.py| F[data/processed/user_track_pairs_thr{n}.parquet]
    F -->|model.py| G[data/final/regression_summary_thr{n}.csv]
    F -->|sensitivity.py| H[data/final/sensitivity_analysis.csv]
    F -->|permutation.py| I[data/final/permutation_results.csv]
    G -->|plots| J[data/final/plots/]
```

## 2. Schemas

### 2.1 `ingested_cohort.parquet`
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | string | Unique participant identifier. |
| `track_id` | string | Unique track identifier (from MSD). |
| `birth_year` | integer | User's birth year (nullable). |
| `cue_text` | string | Memory cue (from AMT). |
| `vividness` | integer (1‑7) | Vividness rating. |
| `valence` | integer (1‑7) | Valence rating. |
| `track_release_year` | integer | Year track was released. |
| `track_popularity` | float | Track popularity score (MSD). |
| `listen_timestamp` | datetime | **Only populated if an external listening‑history dataset with timestamps is supplied**; otherwise null. |
| `is_adolescent_listen` | boolean | `True` if listen occurred when user age ∈ [10, 19] (requires timestamps). |

### 2.2 `matched_thr{n}.parquet` (intermediate)
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | string | |
| `track_id` | string | |
| `cue_text` | string | |
| `matched_track_title` | string | Title after fuzzy matching. |
| `levenshtein_distance` | integer | Distance used for the match. |
| `threshold` | integer | Levenshtein threshold (`n`). |
| `match_success` | boolean | Whether distance ≤ threshold. |

### 2.3 `user_track_pairs_thr{n}.parquet` (final analysis dataset)
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | string | |
| `track_id` | string | |
| `total_listens` | integer ≥ 5 | Total listens for this pair (FR‑009). |
| `adolescent_listens` | integer ≥ 0 | Listens during adolescence (requires timestamps). |
| `adolescent_exposure_ratio` | number [0, 1] | `adolescent_listens / total_listens` (or placeholder). |
| `logit_ratio` | number | Continuity‑corrected logit of `adolescent_exposure_ratio`. |
| `mean_vividness` | number [1, 7] | Average vividness rating. |
| `mean_valence` | number [1, 7] | Average valence rating. |
| `track_popularity` | number | Popularity control. |
| `match_threshold_used` | integer ∈ {1, 2, 3, 4, 5} | Levenshtein threshold applied. |
| `n_cues` | integer ≥ 1 | Number of cues for this pair. |
| `global_exposure_proxy` | number [0, 1] | Population‑level proxy for missing birth years (null if not used). |

### 2.4 `regression_summary_thr{n}.csv`
| Column | Type | Description |
|--------|------|-------------|
| `term` | string | Variable name (`logit_ratio`, `track_popularity`, `total_listens`, `Intercept`). |
| `estimate` | number | Coefficient estimate. |
| `std_error` | number | Standard error. |
| `t_value` | number | t‑statistic. |
| `p_value` | number [0, 1] | Bonferroni‑adjusted p‑value. |
| `vif` | number | Variance Inflation Factor (≥ 1.0). |

### 2.5 `sensitivity_analysis.csv`
| Column | Type | Description |
|--------|------|-------------|
| `threshold` | integer | Levenshtein distance used. |
| `match_rate` | number [0, 1] | Proportion of cues successfully matched. |
| `coef_estimate` | float | `logit_ratio` coefficient from the LMM. |
| `p_value` | float [0, 1] | Bonferroni‑adjusted p‑value. |

### 2.6 `permutation_results.csv`
| Column | Type | Description |
|--------|------|-------------|
| `iteration` | integer | Permutation index (1‑10,000). |
| `coef_null` | float | Coefficient for `logit_ratio` from this permuted dataset. |
| `coef_observed` | float | Observed coefficient (repeated for all rows). |

## 3. Data Hygiene & Versioning
- **Checksums**: Every artifact (`*.parquet`, `*.csv`) receives a SHA‑256 hash stored in `state.yaml`.  
- **Immutability**: Raw files under `data/raw/` are never overwritten; all transformations write new files in `data/processed/` or `data/final/`.  
- **State Tracking**: `state.yaml` records `artifact_hashes` and a `updated_at` timestamp per run.  
- **Schema Validation**: After each write, `code/state_manager.py` validates the file against the appropriate JSON‑Schema contract (`contracts/dataset.schema.yaml` for parquet, `contracts/output.schema.yaml` for CSV, `contracts/user_track_pair.schema.yaml` for the aggregated dataset). Failures abort the pipeline, guaranteeing deterministic, verifiable outputs.

---

