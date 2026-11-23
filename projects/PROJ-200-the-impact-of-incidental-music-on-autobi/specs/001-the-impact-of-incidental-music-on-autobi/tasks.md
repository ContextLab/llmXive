# Tasks: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`  
**Research Question**: Does exposure to music during adolescence produce uniquely vivid and emotionally salient autobiographical memories compared to music exposure during other developmental periods?

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T000 Initialise `state.yaml` with the required top‑level keys (`artifact_hashes`, `updated_at`, `config`).  
  - **Artifact**: `state.yaml`  
  - **Verification**: `tests/unit/test_state_manager.py` confirms the file contains the expected keys and is valid JSON.

- [ ] T001 Create the canonical project layout (`code/`, `data/raw/`, `data/processed/`, `data/final/`, `tests/`) and pin all dependencies in `requirements.txt`. Add a runnable command to `quickstart.md`.  
  - **Artifact**: `quickstart.md` (shows `python -m code.main --demo`)  
  - **Verification**: CI checks that `pip install -r requirements.txt` succeeds, that the command exits with code 0, **and** `tests/unit/test_quickstart.py` asserts `quickstart.md` contains the exact string `python -m code.main --demo`.

- [ ] T002 Add the JSON‑Schema contracts for the processed dataset and regression outputs (`contracts/dataset.schema.yaml`, `contracts/output.schema.yaml`).  
  - **Artifact**: schema files (unchanged)  
  - **Verification**: `jsonschema` validation passes for every generated parquet/CSV file.

- [ ] T003 Implement a **thin end‑to‑end pipeline** that uses a synthetic validation dataset (10 users × 5 tracks) with hand‑crafted birth years and release years so that the true `adolescent_exposure_ratio` is known.   <!-- FAILED-IN-EXECUTION: code/simulate_demo.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/simulate_demo.py exit=1 -->
  - **Code**: `code/main.py` (demo mode) → `code/simulate_demo.py` → `code/ingest.py` → `code/aggregate.py` → `code/model.py`.  
  - **Outputs**: `data/processed/ingested_cohort.parquet`, `data/processed/user_track_pairs.parquet`, `data/final/regression_summary.csv`.  
  - **Verification**: Unit test `tests/unit/test_exposure_accuracy.py` asserts that the computed ratio matches the expected value within 1e‑6 (SC‑001) and that `regression_summary.csv` contains the required columns.

## Phase 2 – Full‑scale study and validation  

- [ ] T004 **Data download & ingestion** – stream the verified MSD JSONL shards from the official HuggingFace mirror (`hf://datasets/msd/full`) into `data/raw/msd_*.jsonl`; abort with a clear error if the URL is unreachable. Also validate the presence of the user‑provided AMT parquet (`data/raw/amt.parquet`).  
  - **Code**: `code/download.py`, `code/ingest.py`.  
  - **Outputs**: `data/processed/ingested_cohort.parquet`.  
  - **Verification**: Integration test `tests/integration/test_download_and_ingest.py` checks that (1) the MSD stream loads without loading the whole file into memory, (2) the schema of `ingested_cohort.parquet` contains the required raw columns, and (3) a missing AMT file raises `FileNotFoundError`.

- [ ] T005 **Cue matching across thresholds** – for each Levenshtein distance `n ∈ {1,2,3,4,5}` match AMT cue text to MSD track titles, write one parquet per threshold (`data/processed/matched_thr{n}.parquet`), compute the **track‑matching rate** per threshold, and **log a warning** if the rate is `< 0.80`.  
  - **Code**: `code/match.py`.  
  - **Outputs**: `data/processed/matched_thr1.parquet` … `matched_thr5.parquet`; log file `logs/match_rate_{n}.json`.  
  - **Verification**: `tests/unit/test_match_rate.py` asserts that the logged rate matches the on‑disk calculation and that a warning is emitted when below 0.80 (SC‑002, SC‑004).

- [ ] T006 **Aggregation & edge‑case handling** – for each threshold `n`:
  1. Join matched cues with the ingested cohort.  
  2. Filter out rows with `total_listens < 5` **after** the fallback check (FR‑009 & EC‑001).  
  3. If **> 50 %** of `birth_year` values are missing **before** any filtering, compute the **Global Exposure proxy** (mean adolescent exposure for the user's birth‑decade) and add column `global_exposure_proxy`.  
  4. Remove zero‑variance tracks (`total_listens == 0`).  
  5. Compute `adolescent_exposure_ratio = adolescent_listens / total_listens`.  
  6. Apply the continuity‑corrected logit transformation (FR‑013) → `logit_ratio`.  
  7. Compute VIF for `logit_ratio` and `track_popularity`; log a warning if any VIF > 5 (FR‑003, EC‑003).  
  8. Write `data/processed/user_track_pairs_thr{n}.parquet`.  
  - **Code**: `code/aggregate.py`.  
  - **Verification**: `tests/unit/test_aggregation.py` checks that (a) the fallback is triggered before the listen‑count filter, (b) the logit calculation matches the continuity‑corrected formula, and (c) VIF warnings appear when appropriate. Schema validation against `contracts/dataset.schema.yaml` must pass.

- [ ] T007 **Linear Mixed‑Effects modelling** – for each threshold `n`, fit the LMM:  
  `mean_vividness ~ logit_ratio + track_popularity + (1|user_id)` using `statsmodels`’s `MixedLM`. Exclude `total_listens` to avoid collinearity. Write a CSV summary `data/final/regression_summary_thr{n}.csv` that conforms to `contracts/output.schema.yaml` (includes VIF values).  
  - **Code**: `code/model.py`.  
  - **Verification**: `tests/unit/test_model.py` confirms that the CSV contains the required columns, that the random‑intercept variance is > 0, and that VIF columns are present.

- [ ] T008 **Sensitivity analysis & Bonferroni correction** – collate the five regression summaries, compute Bonferroni‑adjusted p‑values (`α_adj = 0.05 / 5`), and write `data/final/sensitivity_analysis.csv` with columns `threshold, match_rate, coef_estimate, p_value_adj`.  
  - **Code**: `code/sensitivity.py`.  
  - **Verification**: `tests/unit/test_sensitivity.py` checks that exactly five rows are present, that each row’s `p_value_adj` equals `min(p_value * 5, 1.0)`, and that at least one threshold shows significance **or** the file records “non‑significant” correctly (SC‑006).

- [ ] T009 **Block‑permutation test** – on the primary threshold (`n = 3`) perform **10 000** permutations that shuffle `mean_vividness` **within each `user_id` block** while keeping all predictors fixed. Collect the coefficient for `logit_ratio` from each permuted model, compute a two‑sided p‑value, and write `data/final/permutation_results.csv` containing `iteration, coef_null, coef_observed`. Also write a summary row (`iteration = 0`) with the observed coefficient, null‑distribution mean/SD, and final p‑value.  
  - **Code**: `code/permutation.py`.  
  - **Verification**: `tests/unit/test_permutation.py` ensures that (a) the block structure is respected (no cross‑user swaps), (b) exactly 10 000 null coefficients are generated, and (c) the reported p‑value matches the empirical proportion.

- [ ] T010 **Power analysis** – run a simulation‑based a priori power calculation targeting **≥ 80 %** power to detect a small‑to‑medium effect (Cohen’s f² = 0.15) at α = 0.05 for the LMM, incorporating an ICC estimate from a pilot run. Write `data/final/power_report.txt` that lists the required sample size, the achieved sample size after filtering, and the post‑hoc power estimate. If post‑hoc power < 0.80, log a warning.  
  - **Code**: `code/power_analysis.py`.  
  - **Verification**: `tests/unit/test_power.py` checks that the required N is computed, that the final N is read from the filtered dataset, and that the reported power matches a reference implementation (SC‑005).

- [ ] T011 **Artifact verification & state update** – after all computational steps, (1) run schema validation on every parquet and CSV artifact, (2) compute SHA‑256 hashes for each **processed**, **final**, **and raw** file (`data/raw/msd_*.jsonl`), (3) update `state.yaml` with two sections: `artifact_hashes` (processed/final) and `raw_hashes` (raw MSD shards), and (4) refresh the `updated_at` timestamp.  
  - **Code**: `code/state_manager.py`.  
  - **Verification**: `tests/integration/test_state_updates.py` asserts that `state.yaml` contains a hash entry for every file in `data/raw/`, `data/processed/`, and `data/final/` and that the hashes match the actual file contents.

- [ ] T014 **Reproducibility verification** – re‑run the full pipeline with the same random seeds (`random.seed(42)`, `np.random.seed(42)`) and compare SHA‑256 hashes of all final artifacts (`data/final/*.csv`, `data/final/*.txt`). The task fails if any hash differs, guaranteeing identical outputs across runs as required by Constitution Principle I.  
  - **Code**: `code/reproducibility_check.py`.  
  - **Verification**: `tests/unit/test_reproducibility.py` runs the pipeline twice in a temporary environment and asserts hash equality of all final outputs.

## Phase 3 – Reproducible results & handoff  

(Tasks T012 and T013 have been removed because they were not traceable to any functional requirement or success criterion.)

### Coverage Table

| Spec ID | Task(s) | Verification |
|---------|---------|--------------|
| FR‑001 | T006 | `tests/unit/test_aggregation.py` |
| FR‑002 | T005 | `tests/unit/test_match_rate.py` |
| FR‑003 | T006 | VIF warning test |
| FR‑004 | T006 | schema `dataset.schema.yaml` |
| FR‑005 | T007 | `tests/unit/test_model.py` |
| FR‑006 | T008 | `tests/unit/test_sensitivity.py` |
| FR‑007 | T009 | `tests/unit/test_permutation.py` |
| FR‑008 | T006 | fallback logic test |
| FR‑009 | T006 | minimum‑listen filter test |
| FR‑010 | T007 | `track_popularity` included in model |
| FR‑011 | T010 | `tests/unit/test_power.py` |
| FR‑013 | T006 | logit transformation test |
| SC‑001 | T003 | exposure‑accuracy unit test |
| SC‑002 | T005 | match‑rate warning test |
| SC‑003 | T006 | edge‑case handling test |
| SC‑004 | T005 | same as SC‑002 |
| SC‑005 | T010 | power‑report test |
| SC‑006 | T008 | sensitivity‑analysis test |
| SC‑007 | T009 | permutation‑results test |
| SC‑008 | T011, T014 | schema‑validation and reproducibility tests |