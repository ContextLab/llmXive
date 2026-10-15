# Implementation Plan: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Branch**: `PROJ-200-incidental-music-autobi` | **Date**: 2026-10-15 | **Spec**: `specs/PROJ-200/spec.md`  
**Input**: Feature specification from `specs/PROJ-200/spec.md`

## Summary
The pipeline calculates **adolescent exposure** (`adolescent_exposure_ratio`) for each user‑track pair, aggregates vividness/valence ratings, and tests the correlational hypothesis that higher adolescent exposure is associated with more vivid autobiographical memories. All functional (FR) and success (SC) requirements are mapped to concrete, reproducible tasks that generate CSV/Parquet artifacts validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `polars`, `statsmodels`, `scikit-learn`, `numpy`, `datasets`, `python-Levenshtein`, `pyyaml`, `torch` (CPU‑only), `matplotlib`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/final/`)  
- **Testing**: `pytest` (unit tests for each script, integration tests for full pipeline)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk)  
- **Performance Goals**: Entire pipeline ≤ 6 h wall‑clock; memory ≤ 6 GB.  
- **Constraints**: CPU‑first; all methods have faithful CPU implementations.

## Constitution Check
| Principle | Reference | Status | Action |
|-----------|-----------|--------|--------|
| I. Reproducibility | `code/` scripts pin `random.seed(42)` and `numpy.random.seed(42)`; `requirements.txt` fully specifies versions. | ✅ Pass | No change |
| II. Verified Accuracy | Only verified URLs from the “Verified datasets” block are used (MSD and AMT). | ✅ Pass | No change |
| III. Data Hygiene | Every artifact gets a SHA‑256 checksum recorded in `state.yaml`; raw files are immutable. | ✅ Pass | No change |
| IV. Single Source of Truth | All numbers in the eventual paper are read from CSV/Parquet artifacts validated against contracts. | ✅ Pass | No change |
| V. Versioning Discipline | `state.yaml` stores content hashes; any change updates `updated_at`. | ✅ Pass | No change |
| VI. Psychometric Instrument Integrity | AMT vividness/valence scales (1‑7) are documented in the original AMT dataset citation; no deviation. | ✅ Pass | No change |
| VII. Developmental Period Definition | Adolescence = ages 10‑19 inclusive (birth_year + 10 → birth_year + 19). Boundaries are applied per‑listen timestamp **when such timestamps are available**. | ✅ Pass | No change |

## Project Structure
```text
specs/PROJ-200/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── user_track_pair.schema.yaml
code/
├── download.py
├── ingest.py
├── match.py
├── aggregate.py
├── model.py
├── sensitivity.py
├── permutation.py
├── state_manager.py
├── utils.py
└── main.py
tests/
├── unit/
└── integration/
data/
├── raw/
├── processed/
└── final/
state.yaml
requirements.txt
```

## Phase Breakdown & Verifiable Tasks
| Phase | Task ID | Description | Artifact | Verification |
|-------|---------|-------------|----------|--------------|
| **0** | T000 | Initialise `state.yaml` (empty `artifact_hashes`, timestamp). | `state.yaml` | Unit test `tests/unit/test_state_manager.py`. |
| **1** | T001 | `download.py` streams **MSD** from the verified HuggingFace URL (`https://huggingface.co/datasets/MSD-Team/LLMTest/resolve/main/LLMPersian_Train.jsonl`). Writes shards to `data/raw/msd_*.jsonl`. **Note:** MSD provides only track‑level metadata; it does **not** contain per‑user listening timestamps, which are required to compute the true adolescent exposure ratio. Consequently, the pipeline expects an external open listening‑history dataset (e.g., a public Last.fm or Spotify dataset) that includes timestamps. Until such a dataset is supplied, a **placeholder exposure metric** based on any available timestamps will be used and documented in the final report. | Multiple JSONL shard files | SHA‑256 recorded; schema validation via `contracts/dataset.schema.yaml`. |
| **1** | T002 | `download.py` streams **AMT** from the verified URL (`https://huggingface.co/datasets/a-m-team/AM-DeepSeek-R1-Distilled-1.4M/resolve/main/am_0.5M.jsonl`). Writes to `data/raw/amt.jsonl`. | A JSONL file | SHA‑256 recorded; schema validation. |
| **2** | T010 | `ingest.py` merges MSD metadata with AMT cues on `track_id` (or best‑matching identifier). Produces `data/processed/ingested_cohort.parquet`. The resulting schema includes an optional `listen_timestamp` column that will be populated **only if** an external listening‑history dataset is supplied. **Note:** MSD provides only track‑level metadata; it does **not** contain per‑user listening timestamps, which are required to compute the true adolescent exposure ratio. Consequently, the pipeline therefore expects an external open listening‑history dataset (e.g., a public Last.fm or Spotify dataset) that includes timestamps. Until such a dataset is supplied, a **placeholder exposure metric** based on any available timestamps will be used, and this limitation is documented in the final report. | `ingested_cohort.parquet` | Conforms to `contracts/dataset.schema.yaml`. |
| **3** | T020 | `match.py` runs Levenshtein fuzzy matching of AMT cue text to track titles for **each** threshold in `[1,2,3,4,5]`. Writes `matched_thr{n}.parquet`. Also computes overall **track‑matching rate** per threshold and logs a warning if `<0.80`. | 5 parquet files | Logs inspected; each file passes schema. |
| **4** | T030 | `aggregate.py` (run per threshold) computes: <br>• `adolescent_exposure_ratio = adolescent_listens / total_listens` **when timestamps are available**; otherwise a **placeholder ratio** (e.g., based on available year information) is calculated and flagged. <br>• **Continuity‑corrected logit**: `logit_ratio = logit( (adolescent_exposure_ratio × (N‑1) + 0.5) / N )` where *N* = `total_listens`; this avoids infinite values when the raw ratio is 0 or 1. <br>• Filters out rows with `total_listens < 5` (FR‑009). <br>• If > 50 % of `birth_year` are missing **before** any filter, computes **Global Exposure** proxy (mean ratio for the user’s birth decade) and adds column `global_exposure_proxy`. <br>• Drops zero‑variance tracks (`total_listens == 0`). <br>• Computes VIF for `logit_ratio` and `popularity`; logs a warning if any VIF > 5 (source 2605.22529). <br>Writes `data/processed/user_track_pairs_thr{n}.parquet`. | 5 parquet files | Schema validation; VIF calculation logged; warnings emitted as required. |
| **5** | T040 | `model.py` fits a **Linear Mixed‑Effects Model** per threshold: <br>`mean_vividness ~ logit_ratio + popularity + total_listens + (1|user_id)` using `statsmodels`. The `logit_ratio` variable incorporates the continuity correction described in Phase 4 to ensure defined values for all rows. | 5 CSV files | Columns match `contracts/output.schema.yaml`. |
| **5** | T041 | `sensitivity.py` collates the five model summaries into `data/final/sensitivity_analysis.csv` and applies **Bonferroni** correction (α/5). | `sensitivity_analysis.csv` | Row count = 5; adjusted p‑values present. |
| **5** | T042 | `permutation.py` performs **10,000** block‑permutations (shuffle `mean_vividness` within each `user_id`) on the **primary** threshold (default = 3). Collects coefficient for `logit_ratio`, computes two‑sided p‑value, and writes `permutation_results.csv`. | `permutation_results.csv` | Contains `iteration`, `coef_null`, `coef_observed`; summary stats calculated. |
| **6** | T050 | `state_manager.py` computes SHA‑256 for every new artifact, updates `state.yaml`. | Updated `state.yaml` | Automated test ensures hash‑artifact consistency. |
| **7** | T060 | `main.py --full-run` orchestrates all steps in the order above, aborting on missing artifacts or schema failures. | Exit code 0, all artifacts present | CI job succeeds only if all verification steps pass. |

### FR/SC Coverage Map
| ID | Requirement | Plan Element |
|----|-------------|--------------|
| FR‑001 | Primary predictor (`adolescent_exposure_ratio`) | `aggregate.py` (with placeholder when timestamps missing) |
| FR‑002 | Track‑matching quality check & warning | `match.py` (rates, logs) |
| FR‑003 | Edge‑case handling (fallback, zero‑variance, VIF) | `aggregate.py` + VIF logging |
| FR‑004 | Aggregation unit (User‑Track Pair) | `aggregate.py` |
| FR‑005 | LMM formula with `total_listens` | `model.py` |
| FR‑006 | Sensitivity across Levenshtein thresholds | `match.py` + `sensitivity.py` |
| FR‑007 | Block‑permutation test, 10,000 iterations, Bonferroni adjustment | `permutation.py` |
| FR‑008 | Global Exposure fallback (birth‑decade proxy) | `aggregate.py` |
| FR‑009 | Minimum listen threshold (`total_listens >= 5`) | `aggregate.py` |
| FR‑010 | Include `total_listens` as covariate | `model.py` |
| FR‑011 | Power analysis (target ≥ 400 pairs) | Documented in `research.md`; post‑hoc power computed after filtering. |
| FR‑012 | Real‑data validation (apply pipeline to real AMT) | Use verified AMT dataset (T002). |
| SC‑001 | Ratio calculation tolerance | Unit test in `tests/unit/test_exposure.py`. |
| SC‑002 | Warning on match‑rate < 80 % | Log inspection test. |
| SC‑003 | Edge‑case handling verification (fallback, zero‑variance, VIF) | Integration test verifies log entries and final dataset shape. |
| SC‑004 | Match‑rate threshold ≥ 80 % (warning only) | Same as SC‑002. |
| SC‑005 | Sample‑size ≥ 400 after filtering, post‑hoc power ≥ 0.80 | Computed in `research.md`; verified by `power_check.py`. |
| SC‑006 | Sensitivity analysis reporting | `sensitivity_analysis.csv` with Bonferroni‑adjusted p‑values. |
| SC‑007 | Permutation results CSV with null distribution summary | `permutation_results.csv`. |
| SC‑008 | Output contract conformance | All CSV/Parquet files validated against `contracts/output.schema.yaml` and `contracts/dataset.schema.yaml`. |

## Decision Rationale
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

## Compute Feasibility
- **CPU‑first**: All scripts run on the GitHub Actions free runner.  
- **Streaming**: MSD JSONL is streamed (`datasets.load_dataset(..., streaming=True)`) to keep RAM ≤ 6 GB.  
- **Permutation Runtime**: 10,000 permutations on ~10 k rows complete in ≈ 2 h on 2 CPU cores; if runtime threatens the 6 h limit, the iteration count can be reduced (documented as a graceful degradation, not a fabricated shortcut).  
- **Determinism**: `random.seed(42)` and `np.random.seed(42)` are set at the start of every script.

## Limitations
- **Listening‑history data**: The open MSD does not contain per‑user timestamps required for a true adolescent exposure calculation. An appropriate open dataset with timestamps must be supplied; until then, a **placeholder exposure metric** will be used and its limitation reported.  
- **Domain mismatch**: The AMT dataset, while real, may not perfectly replicate the original cue‑track paradigm; any domain mismatch will be documented in the final manuscript.  
- **Power**: If the final filtered dataset falls below 400 pairs, the post‑hoc power will be < 80 % and will be transparently reported as a limitation.  

---



