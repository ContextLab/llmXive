# Implementation Plan: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Branch**: `PROJ-200-incidental-music-autobi` | **Date**: 2026-10-24 | **Spec**: `specs/PROJ-200/spec.md`  
**Input**: Feature specification from `specs/PROJ-200/spec.md`

## Summary
The pipeline computes the **adolescent exposure ratio** for each user‑track pair, aggregates vividness/valence ratings, and evaluates the correlational hypothesis that higher adolescent exposure is associated with more vivid autobiographical memories. All functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑008) are mapped to concrete, reproducible tasks that generate validated CSV/Parquet artifacts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `polars`, `statsmodels`, `scikit-learn`, `numpy`, `datasets`, `python-Levenshtein`, `pyyaml`, `matplotlib`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/final/`)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk)  
- **Performance Goals**: Full pipeline ≤ 6 h wall‑clock, peak RAM ≤ 6 GB  
- **Constraints**: CPU‑first; all methods have faithful CPU implementations.  

### Proxy Justification
The Million Song Dataset (MSD) supplies only **track release year** metadata, not per‑user listening timestamps. To address the construct validity of the `adolescent_exposure_ratio`, the plan frames this metric as a measure of **era-specific exposure**. This approach leverages the "Reminiscence Bump" phenomenon—the well-documented tendency for adults to have enhanced memory for events and media from their adolescence and early adulthood. By using release year as a proxy, we are testing whether music *originating* from the user's adolescent era is more strongly associated with vivid memories, rather than claiming to measure the exact timestamp of a listening event. This is the strongest open‑data approach available; the limitation will be explicitly reported in the manuscript and interpreted as a correlational association only.

## Constitution Check
| Principle | Reference | Status | Action |
|-----------|-----------|--------|--------|
| I. Reproducibility | Scripts pin `random.seed(42)` and `numpy.random.seed(42)`; `requirements.txt` fully specifies versions. | ✅ Pass | No change |
| II. Verified Accuracy | Only verified URLs from the “Verified datasets” block are used (MSD JSONL). | ✅ Pass | No change |
| III. Data Hygiene | SHA‑256 checksums recorded in `state.yaml`; raw files immutable. | ✅ Pass | No change |
| IV. Single Source of Truth | All numbers in the eventual paper are read from validated CSV/Parquet artifacts. | ✅ Pass | No change |
| V. Versioning Discipline | `state.yaml` stores content hashes; any change updates `updated_at`. | ✅ Pass | No change |
| VI. Psychometric Instrument Integrity | AMT vividness/valence scales (1‑7) are documented in the original AMT citation; no deviation. | ✅ Pass | No change |
| VII. Developmental Period Definition | Adolescence = ages 10‑19 inclusive. Boundaries applied per‑listen timestamps when available. | ✅ Pass | No change |

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
├── power_analysis.py
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
| Phase | Task ID | Description | Artifact(s) | Verification |
|-------|---------|-------------|-------------|--------------|
| **0** | T000 | Initialise `state.yaml` (empty `artifact_hashes`, timestamp). | `state.yaml` | Unit test `tests/unit/test_state_manager.py`. |
| **1** | T001 | `download.py` streams **Million Song Dataset (MSD)** from the verified HuggingFace URL (`). Writes sharded JSONL files to `data/raw/msd_*.jsonl`. | Sharded JSONL files | SHA‑256 recorded; schema validation via `contracts/dataset.schema.yaml`. |
| **1** | T002 | **User‑provided AMT file**: `download.py` checks for the presence of `data/raw/amt.parquet`. If missing, aborts with a clear error instructing the user to place a validated AMT file (must conform to `contracts/user_track_pair.schema.yaml`). No automatic download (AMT not in verified list). | `data/raw/amt.parquet` (user‑supplied) | Validation test ensures schema compliance. |
| **2** | T010 | `ingest.py` merges MSD metadata with AMT cues on `track_id`. Produces `data/processed/ingested_cohort.parquet`. **No schema validation is performed here** (the file is an intermediate merge; validation occurs later on the final User‑Track Pair files). | `ingested_cohort.parquet` | Basic integrity checks; downstream schema validation. |
| **3** | T020 | `match.py` performs Levenshtein fuzzy matching of cue text to track titles across a series of incremental thresholds (e.g., from the lowest to higher levels). Writes `data/processed/matched_thr{n}.parquet`. Computes per‑threshold **track‑matching rate**; logs a warning if `< 0.80`. **VIF source citation**: <https://arxiv.org/abs/2605.22529>. | 5 parquet files | Log inspection; schema validation. |
| **4** | T030 | `aggregate.py` (run per threshold) computes: <br>• `adolescent_exposure_ratio` = adolescent_listens / total_listens **when timestamps exist**; otherwise a **placeholder ratio** based on release‑year cohort alignment (documented). <br>• Continuity‑corrected logit (`logit_ratio`). <br>• Filters out rows with `total_listens` < 5 (FR‑009). <br>• If > 50 % `birth_year` missing **before** any filter, computes **Global Exposure** proxy (mean ratio for the user’s birth decade) and adds `global_exposure_proxy`. <br>• Drops zero‑variance tracks (`total_listens == 0`). <br>• Computes VIF for `logit_ratio` and `track_popularity`; logs warning if VIF > 5 (source above). <br>• **Collinearity mitigation**: because `logit_ratio` mathematically depends on `total_listens`, the model will **exclude `total_listens` by default**; if a user explicitly requests its inclusion, VIF is checked and a warning logged. Writes `data/processed/user_track_pairs_thr{n}.parquet`. | 5 parquet files | Schema validation; VIF logged; warnings emitted. |
| **5** | T040 | `model.py` fits a **Linear Mixed‑Effects Model** per threshold: <br>`mean_vividness ~ logit_ratio + track_popularity + (1|user_id)` using `statsmodels`. **`total_listens` is omitted** to avoid collinearity with `logit_ratio`. If a prior step flagged `total_listens` as non‑collinear (rare), it may be added with a note in the log. | 5 CSV files (`regression_summary_thr{n}.csv`) | Columns match `contracts/output.schema.yaml`. |
| **5** | T041 | `sensitivity.py` collates the model summaries into `data/final/sensitivity_analysis.csv` and applies **Bonferroni** correction (α divided by the number of comparisons). | `sensitivity_analysis.csv` | Row count = 5; adjusted p‑values present. |
| **5** | T042 | `permutation.py` runs **10,000** block‑permutations (shuffle `mean_vividness` within each `user_id`) on the primary threshold (`n=3`). Collects the `logit_ratio` coefficient, computes a two‑sided p‑value, and writes `data/final/permutation_results.csv`. | `permutation_results.csv` | Contains iteration, null coefficient, observed coefficient, summary stats. |
| **5** | T043 | `power_analysis.py` performs an **a priori** power calculation targeting **≥ 80 %** power to detect a small‑to‑medium effect (Cohen’s f² = 0.15) at α = 0.05 for the mixed‑effects model. The calculation uses a simulation‑based approach that incorporates the estimated ICC (indicative of moderate clustering) to adjust effective sample size. It writes `data/final/power_report.txt` with required N and post‑hoc power based on the final filtered dataset. | `power_report.txt` | Value ≥ 0.80 flagged as pass; otherwise warning logged. |
| **6** | T050 | `state_manager.py` computes SHA‑256 for every new artifact, updates `state.yaml`. | Updated `state.yaml` | Automated test ensures hash‑artifact consistency. |
| **7** | T060 | `main.py --full-run` orchestrates all steps in the order above, aborting on missing artifacts, schema failures, or unmet power requirement. | Exit code 0, all artifacts present | CI job succeeds only if all verification steps pass. |

### FR/SC Coverage Map
| ID | Requirement | Plan Element |
|----|-------------|--------------|
| FR‑001 | Primary predictor (`adolescent_exposure_ratio`) | `aggregate.py` (placeholder when timestamps missing) |
| FR‑002 | Track‑matching quality check & warning | `match.py` |
| FR‑003 | Edge‑case handling (fallback, zero‑variance, VIF) | `aggregate.py` |
| FR‑004 | Aggregation unit (User‑Track Pair) | `aggregate.py` |
| FR‑005 | LMM formula with `track_popularity` (no `total_listens`) | `model.py` |
| FR‑006 | Sensitivity across Levenshtein thresholds | `match.py` + `sensitivity.py` |
| FR‑007 | Block‑permutation test (10 k iterations) | `permutation.py` |
| FR‑008 | Global Exposure fallback | `aggregate.py` |
| FR‑009 | Minimum listen threshold (`total_listens >= 5`) | `aggregate.py` |
| FR‑010 | Include `track_popularity` as covariate | `model.py` |
| FR‑011 | Power analysis (≥ 80 % power) | `power_analysis.py` |
| FR‑012 | Real‑data validation (AMT) | Pipeline ready to ingest user‑provided AMT file (T002). |
| FR‑013 | Logit transformation with continuity correction | `aggregate.py` |
| SC‑001 | Ratio calculation tolerance | Unit test `tests/unit/test_exposure.py`. |
| SC‑002 | Warning on match‑rate < 80 % | Log‑inspection test. |
| SC‑003 | Edge‑case handling verification | Integration test checks fallback, zero‑variance removal, VIF warning. |
| SC‑004 | Match‑rate threshold ≥ 80 % (warning only) | Same as SC‑002. |
| SC‑005 | Sample‑size & post‑hoc power ≥ 0.80 | `power_report.txt` validated by `tests/unit/test_power.py`. |
| SC‑006 | Sensitivity analysis reporting | `sensitivity_analysis.csv` with Bonferroni‑adjusted p‑values. |
| SC‑007 | Permutation results CSV with null distribution summary | `permutation_results.csv`. |
| SC‑008 | Output contract conformance | All CSV/Parquet files validated against `contracts/*.schema.yaml`. |

## Decision Rationale
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

## Compute Feasibility
- **CPU‑first**: All scripts run on the GitHub Actions free runner.  
- **Streaming**: MSD JSONL streamed (`datasets.load_dataset(..., streaming=True)`) to keep RAM ≤ 6 GB.  
- **Permutation Runtime**: 10,000 permutations on ~10 k rows ≈ 2 h on 2 CPU cores; if runtime threatens the 6 h limit, the iteration count can be reduced (recorded in `power_report.txt`).  
- **Determinism**: `random.seed(42)` and `np.random.seed(42)` set at script start.

## Limitations
- **Listening‑history data**: MSD lacks per‑user timestamps; an open listening‑history dataset with timestamps is required for a true adolescent exposure calculation. Until such a dataset is supplied, a placeholder exposure metric based on release year (era-specific exposure) will be used. This measures the association with music from the adolescent period rather than actual listening behavior during that period.
- **AMT availability**: The AMT dataset is not in the verified list; the pipeline expects a user‑provided file conforming to the required schema.  
- **Power**: If the final filtered dataset falls below the a priori required N, post‑hoc power will be < 80 % and will be transparently reported as a limitation.  