# Implementation Plan: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Branch**: `PROJ-200-incidental-music-autobiographical-memory` | **Date**: 2026-10-15 | **Spec**: `specs/PROJ-200/spec.md`  
**Input**: Feature specification from `specs/PROJ-200/spec.md`

## Summary
The pipeline quantifies **adolescent exposure** to music (`adolescent_exposure_ratio`) for each user‑track pair, aggregates vividness/valence ratings, and tests the hypothesis that higher adolescent exposure is *associated* with more vivid autobiographical memories.  All FRs/SCs are mapped to concrete, verifiable tasks that produce real files adhering to the schemas in `contracts/`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `polars`, `statsmodels`, `scikit-learn`, `scipy`, `pyyaml`, `datasets`, `numpy`, `python-Levenshtein`  
- **Storage**: Local filesystem (Parquet for intermediate data, CSV for final results)  
- **Testing**: `pytest` (unit tests for exposure calc, integration test for full pipeline)  
- **Target Platform**: Linux (GitHub Actions free‑tier CPU runner)  
- **Performance Goals**: Complete full pipeline ≤ 6 h, RAM ≤ 6 GB  
- **Constraints**: No GPU required; all steps run on CPU.

## Constitution Check
| Principle | Reference | Status | Action |
|-----------|-----------|--------|--------|
| I. Reproducibility | `code/` scripts pin `random.seed(42)` and `numpy.random.seed(42)`. All dependencies listed in `requirements.txt`. | ✅ Pass | No change |
| II. Verified Accuracy | Only the verified MSD Zenodo URL is used. No invented URLs. | ✅ Pass | No change |
| III. Data Hygiene | Every artifact written (`*.parquet`, `*.csv`) receives a SHA‑256 checksum stored in `state.yaml`. Raw files under `data/raw/` are immutable. | ✅ Pass | No change |
| IV. Single Source of Truth | All numbers in the eventual paper are read from `data/final/*.csv`. No manual transcription. | ✅ Pass | No change |
| V. Versioning Discipline | `state.yaml` stores content hashes; any change triggers a timestamp update. | ✅ Pass | No change |
| VI. Psychometric Instrument Integrity | Simulated AMT data respects the validated 1‑7 vividness/valence scale; deviations are documented in `technical-design/`. | ✅ Pass | No change |
| VII. Developmental Period Definition | Adolescence = `birth_year` → `birth_year + 15` (inclusive). Boundaries are excluded if a listen falls exactly on the +15 day; this is documented in `config.py`. | ✅ Pass | No change |

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
    └── model_output.schema.yaml   # deprecated; retained for historical reference only
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Block‑Permutation Test | Required by FR‑007 to preserve user‑level correlation. Two‑sided p‑value & Bonferroni‑corrected across thresholds added to control FWER. | Simple shuffling would invalidate LMM assumptions. |
| Streaming MSD JSONL | Prevents OOM on the 7 GB RAM limit. | Loading whole file would crash CI. |
| Global Exposure Fallback Order | EC‑001 mandates fallback BEFORE `total_listens` filter. | Post‑filter fallback would mis‑estimate missing‑birth‑year proportion. |
| Logit Transformation | Ratio (0‑1) heteroscedasticity; logit stabilises variance for LMM. | Using raw ratio would violate homoscedasticity. |
| **Total‑listens Covariate** | Controls for denominator effect of exposure ratio, addressing FR‑005 completeness. | Omission would confound exposure effect. |
| VIF > 5 warning | Aligns with the verified multicollinearity threshold (source 2605.22529). | No warning would hide collinearity issues. |
| Separate matched files per threshold | Guarantees that each sensitivity run is independently verifiable (each file has its own checksum). | Combined file would make per‑threshold verification harder. |
| CSV contract alignment | Ensures validation against `contracts/output.schema.yaml` rather than a mismatched JSON schema. | No alignment would cause schema validation failures. |
| Model output contract trimmed | Marked as deprecated; pipeline only produces CSV outputs validated against `contracts/output.schema.yaml`. | Keeping outdated contract would cause confusion. |

## Phase Breakdown & Verifiable Tasks
| Phase | Task ID | Description | Expected Artifact | Verification |
|-------|---------|-------------|-------------------|--------------|
| **0** | T000 | Initialise `state.yaml` with empty `artifact_hashes` and timestamp. | `state.yaml` (contains keys) | `tests/unit/test_state_manager.py` checks JSON schema. |
| **1** | T001 | Install dependencies (handled by CI). | — | CI logs. |
| **2** | T010 | `download.py` streams the verified MSD tarball from Zenodo, extracts JSONL files to `data/raw/`. | 3 files under `data/raw/` | SHA‑256 of each file recorded in `state.yaml`. |
| **2** | T011 | `simulate_amt.py` generates deterministic AMT data (500 users, 20 tracks each) and writes `data/simulated_amt.parquet`. | `data/simulated_amt.parquet` | Fixed seed → reproducible checksum. |
| **3** | T020 | `ingest.py` merges raw MSD metadata with simulated AMT cues → `data/processed/ingested_cohort.parquet`. Maps fields to schema (including `total_listens`). | `ingested_cohort.parquet` | Conforms to `contracts/dataset.schema.yaml` (validated by pytest). |
| **3** | T021 | `match.py` runs Levenshtein matching for **each** threshold in `[1,2,3,4,5]`, writes intermediate matched parquet files `matched_thr{n}.parquet`. | `matched_thr{n}.parquet` (5 files) | `metrics.py` logs match rate; each file passes schema check. |
| **4** | T030 | `aggregate.py` (run per threshold) computes exposure ratio, applies FR‑009 filter, EC‑001 fallback, EC‑002 zero‑variance filter, writes `data/processed/user_track_pairs_thr{n}.parquet`. | 5 parquet files | Each file validated against `contracts/dataset.schema.yaml`. |
| **5** | T040 | `model.py` fits LMM on each threshold dataset, includes `logit_ratio`, `popularity`, **`total_listens`** as covariates, writes `regression_summary_thr{n}.csv`. | 5 CSV files | Columns match `contracts/output.schema.yaml` (regression summary). |
| **5** | T041 | `sensitivity.py` aggregates the 5 model summaries into `data/final/sensitivity_analysis.csv`. | `sensitivity_analysis.csv` | Row count = 5, columns as defined. |
| **5** | T042 | `permutation.py` performs 1000 block‑permutations on the **primary** threshold (default = 3), two‑sided test, Bonferroni‑corrected across thresholds, writes `permutation_results.csv`. | `permutation_results.csv` | Contains `iteration`, `coef_null`, `coef_observed`. |
| **6** | T050 | `state_manager.py` computes SHA‑256 for every new artifact, updates `state.yaml`. | Updated `state.yaml` | Automated test ensures hashes match files. |
| **6** | T060 | `main.py --full-run` orchestrates steps 0‑6 in order, aborts on any missing artifact. | Exit code 0, all files present | CI job succeeds only if all verification steps pass. |

### FR/SC Coverage Map
| ID | Requirement | Plan Element |
|----|-------------|--------------|
| FR‑001 | Primary predictor | `aggregate.py` (ratio calc) |
| FR‑004 | Aggregation unit | `aggregate.py` (User‑Track Pair) |
| FR‑005 | LMM formula (now includes `total_listens`) | `model.py` |
| FR‑006 | Sensitivity thresholds | `match.py` + `sensitivity.py` |
| FR‑007 | Block‑Permutation (two‑sided, Bonferroni) | `permutation.py` |
| FR‑008 | Global Exposure fallback | `aggregate.py` (fallback logic) |
| FR‑009 | Minimum listen filter | `aggregate.py` (`total_listens >= 3`) |
| US‑001 | Exposure metrics | FR‑001 |
| US‑002 | Match‑rate verification | `metrics.py` logs warning if < 80 % |
| US‑003 | Edge‑case handling | `aggregate.py` & `metrics.py` (missing birth, zero‑variance, VIF) |
| SC‑004 | Match‑rate threshold | `metrics.py` (warn ≥ 80 %) |
| EC‑001 | Fallback order | `aggregate.py` (fallback before filter) |
| EC‑002 | Zero‑variance tracks | `aggregate.py` filter `n_cues == 0` |
| EC‑003 | Multicollinearity | `metrics.py` computes VIF, warns if > 5 |

---


## Decision Rationale
| Decision | Reason |
|----------|--------|
| **Simulate AMT** | No open AMT dataset; simulation provides a complete, reproducible pipeline while respecting data‑hygiene rules. |
| **Stream MSD** | Prevents OOM on the free‑tier runner; still uses real track metadata. |
| **Block‑Permutation (two‑sided, Bonferroni)** | Preserves the hierarchical structure required by the random intercept and controls family‑wise error across thresholds. |
| **Logit Transform** | Stabilises variance for bounded ratio predictor. |
| **Total‑listens Covariate** | Controls for denominator effect of exposure ratio, addressing FR‑005 completeness. |
| **Global Exposure Fallback (only sensitivity)** | Avoids ecological fallacy; used solely to test robustness when birth years are missing. |
| **VIF > 5 warning** | Aligns with the verified multicollinearity threshold (source 2605.22529). |
| **Separate matched files per threshold** | Guarantees that each sensitivity run is independently verifiable (each file has its own checksum). |
| **CSV contract alignment** | Ensures validation against `contracts/output.schema.yaml` rather than a mismatched JSON schema. |
| **Model output contract trimmed** | Marked as deprecated; pipeline only produces CSV outputs validated against `contracts/output.schema.yaml`. |

## Verification Strategy
Each pipeline stage writes a file whose SHA‑256 is recorded in `state.yaml`. Automated pytest suites (`tests/unit/`, `tests/integration/`) load the file, validate against the JSON‑Schema contracts in `contracts/`, and assert expected dimensions (e.g., `user_track_pairs.parquet` has ≥ 1 row per threshold). The CI job fails if any checksum mismatches or schema violations occur, ensuring no fabricated artifacts.

## Limitations
- The primary hypothesis that adolescent exposure predicts vivid autobiographical memories is evaluated **only on fully simulated AMT data** where the effect size (β = 0.3) is embedded by design. This means the analysis can only confirm that the pipeline recovers a known, pre‑specified effect, **not that the effect exists in real human data**. Relying solely on simulated data therefore does not provide empirical evidence for the research question and constitutes a methodological limitation: the validation is not independent of the hypothesis and cannot substantiate the claimed real‑world relationship. Future work should seek an open, ethically‑shareable autobiographical memory dataset to replace the simulation and enable genuine inference.
