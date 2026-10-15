# Data Model: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Data Flow Diagram
```mermaid
graph TD
    A[Raw MSD JSONL (streamed)] -->|download.py| B[raw/msd_*.jsonl]
    C[Simulated AMT Parquet] -->|simulate_amt.py| D[data/simulated_amt.parquet]
    B -->|ingest.py| E[ingested_cohort.parquet]
    D --> E
    E -->|match.py (thresholds 1‑5)| F[matched_thr{n}.parquet]
    F -->|aggregate.py| G[user_track_pairs_thr{n}.parquet]
    G -->|model.py| H[regression_summary_thr{n}.csv]
    G -->|sensitivity.py| I[sensitivity_analysis.csv]
    G -->|permutation.py| J[permutation_results.csv]
    H -->|plots| K[plots/]
```

## 2. Schemas

### 2.1 `ingested_cohort.parquet`
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | string | Unique identifier for a participant. |
| `track_id` | string | Unique track identifier from MSD. |
| `birth_year` | integer | User's birth year (nullable). |
| `cue_text` | string | Simulated free‑text memory cue. |
| `vividness` | integer (1‑7) | Rating of vividness. |
| `valence` | integer (1‑7) | Rating of valence. |
| `track_release_year` | integer | Year the track was released. |
| `popularity` | float | Track popularity score from MSD. |
| `listen_timestamp` | datetime | Simulated timestamp of a listen event. |
| `is_adolescent_listen` | boolean | True if the listen occurred ≤ 15 years after `birth_year`. |

### 2.2 `user_track_pairs_thr{n}.parquet` (final analysis dataset)
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | string | Participant ID. |
| `track_id` | string | Track ID. |
| `total_listens` | integer ≥ 3 | Total listens for this pair. |
| `adolescent_listens` | integer ≥ 0 | Listens during adolescence. |
| `adolescent_exposure_ratio` | float [0, 1] | Ratio `adolescent_listens / total_listens`. |
| `logit_ratio` | float | Logit of `adolescent_exposure_ratio`. |
| `mean_vividness` | float [1, 7] | Average vividness rating. |
| `mean_valence` | float [1, 7] | Average valence rating. |
| `track_popularity` | float | Popularity control. |
| `match_threshold_used` | integer ∈ {1,2,3,4,5} | Levenshtein threshold used. |
| `n_cues` | integer ≥ 1 | Number of memory cues for this pair. |
| `global_exposure_proxy` | float [0, 1] | Population‑level exposure (null if not needed). |
| `total_listens` | integer ≥ 3 | Included as covariate per FR‑005. |

### 2.3 `regression_summary_thr{n}.csv`
| Column | Type | Description |
|--------|------|-------------|
| `term` | string | Variable name (`logit_ratio`, `popularity`, `total_listens`, intercept). |
| `estimate` | number | Coefficient estimate. |
| `std_error` | number | Standard error. |
| `t_value` | number | t‑statistic. |
| `p_value` | number [0, 1] | Permutation‑based p‑value (two‑sided, Bonferroni‑adjusted). |
| `vif` | number | Variance Inflation Factor (≥ 1). |

### 2.4 `sensitivity_analysis.csv`
| Column | Type | Description |
|--------|------|-------------|
| `threshold` | integer | Levenshtein distance used. |
| `match_rate` | float [0, 1] | Proportion of cues successfully matched. |
| `coef_estimate` | float | Coefficient for `logit_ratio`. |
| `p_value` | float [0, 1] | Corresponding permutation p‑value (Bonferroni‑adjusted). |

### 2.5 `permutation_results.csv`
| Column | Type | Description |
|--------|------|-------------|
| `iteration` | integer | Permutation iteration index. |
| `coef_null` | float | Coefficient from permuted data. |
| `coef_observed` | float | Re‑reported observed coefficient (for convenience). |

## 3. Data Hygiene & Versioning
- **Checksums**: Every artifact (`*.parquet`, `*.csv`) receives a SHA‑256 checksum stored in `state.yaml`.  
- **Immutability**: Raw MSD files under `data/raw/` are never overwritten. All transformations write to new files in `data/processed/` or `data/final/`.  
- **State Tracking**: `state.yaml` records `artifact_hashes` and a `updated_at` timestamp per run.  
- **Schema Validation**: After each write, `code/utils/state_manager.py` validates the file against the appropriate JSON‑Schema contract (`contracts/`). Failures abort the pipeline, guaranteeing deterministic, verifiable outputs.
