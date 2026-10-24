# Tasks: Statistical Analysis of Speedrun Data  

**Input**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, contract schemas, existing code skeleton.  
**Goal**: Produce a reproducible, CPU‑only pipeline that (1) acquires and cleans speedrun.com data, (2) fits parametric distributions, (3) fits hierarchical mixed‑effects models, (4) validates all outputs against JSON‑Schema contracts, (5) generates a final report that uses only associational language.  

---  

## Phase 0 – Core utilities (must exist before any user‑story work)

- [X] T006a [P] Define the configuration schema (keys: `games`, `min_sample_size`, `random_seed`, `lagged_pressure_window_days`, `effect_size_assumptions`).  
  – **Verification**: `code/config_schema.yaml` is present and `yamllint` passes.  

- [ ] T006b    Create `code/config.yaml` according to the schema defined in T006a.  
  – **Verification**: File exists, is valid YAML, and contains numeric values for `min_sample_size`, `random_seed`, `effect_size_assumptions`.  

- [ ] T007a    Implement `code/scripts/hash_artifacts.py` (SHA‑256 checksums for all files under `data/`).  
  – **Verification**: Running `python -m code.scripts.hash_artifacts` creates `state/artifact_hashes.json` without error.  

- [X] T008a    Implement `code/scripts/utils/checkpoint.py` exposing `save_checkpoint(state: dict, path: str)` and `load_checkpoint(path: str) -> dict`.  
  – **Verification**: Unit test `tests/test_checkpoint.py` passes.  

---  

## Phase 1 – Data acquisition (User Story 1, P1)

- [ ] T033a [P] Refactor pagination logic into reusable helper `code/scripts/utils/pagination.py::paginate_api`.  
  – **Verification**: Helper file exists; `fetch_data.py` calls `paginate_api`; unit test `tests/test_pagination.py` validates full page list.  

- [ ] T001    Create `code/scripts/fetch_data.py` that iterates over `config.yaml`’s `games`, calls the speedrun.com API, respects rate‑limits, uses `paginate_api`, and writes raw JSON to `data/raw/{game_id}.json`.
  – **Verification**: After running on a test game, a non‑empty file appears under `data/raw/`.  

- [ ] T015a    Add checkpoint integration to `fetch_data.py` (FR‑012). After each game download, call `save_checkpoint({"completed_games": [...]}, "data/checkpoints/fetch_checkpoint.json")`.  
  – **Verification**: Simulate interruption; re‑run resumes without re‑downloading completed games.  

---  

## Phase 2 – Pre‑processing (User Story 1, P1)

- [X] T010    Create the **RunRecord** JSON‑Schema file `contracts/run_record.schema.yaml` (matches spec).  
  – **Verification**: `jsonschema.validate` against a sample row succeeds; unit test `tests/test_run_record_schema.py` passes.  

- [ ] T033b [P] Extract competitive‑pressure calculation into reusable function `code/scripts/utils/pressure.py::calculate_lagged_pressure(df, window_days)`.  
  – **Verification**: Function file exists; unit test `tests/test_pressure.py` validates expected counts.  

- [ ] T002    Create `code/scripts/preprocess.py` that reads each `data/raw/*.json`, removes duplicates, filters out records with missing `run_time_seconds`, computes `total_prior_runs`, `time_since_first_run_days`, merges difficulty labels, calls `calculate_lagged_pressure`, and writes `data/processed/run_records.csv`.   <!-- FAILED-IN-EXECUTION: code/scripts/preprocess.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/scripts/preprocess.py exit=1 -->
  – **Verification**: `run_records.csv` retains ≥ 95 % of raw rows and validates against `run_record.schema.yaml`.  

- [ ] T014    Compute lagged competitive pressure for each run (FR‑006) using the helper from T033b and write column `competitive_pressure` to `run_records.csv`.  
  – **Verification**: Column exists, non‑negative integers; spot‑check matches manual calculation.  

- [ ] T015b    Add checkpoint integration to `preprocess.py` (FR‑012). After each game’s records are processed, call `save_checkpoint({"last_game": game_id, "rows_written": n}, "data/checkpoints/preprocess_checkpoint.json")`.   <!-- FAILED-IN-EXECUTION: code/scripts/preprocess.py exit=1 -->
  – **Verification**: Interrupt after first game; re‑run resumes without re‑processing completed game.  

---  

## Phase 3 – Distribution fitting (User Story 2, P2)

- [ ] T023    Create the **DistributionFit** JSON‑Schema file `contracts/distribution_fit.schema.yaml` (matches spec).  
  – **Verification**: `jsonschema.validate` of `distribution_fits.csv` rows passes; unit test `tests/test_distribution_fit_schema.py` succeeds.  

- [ ] T020    Implement `code/scripts/fit_distributions.py` that reads `run_records.csv`, skips games with `< 100` runs, fits Log‑Normal, Weibull, and Gamma by MLE, computes KS D‑statistics, KS p‑values, AIC, applies Bonferroni correction (FR‑004, FR‑005, SC‑001, SC‑004), and writes `data/processed/distribution_fits.csv`.  
  – **Verification**: For a test game, three rows output with non‑null KS/AIC; at least one family has Bonferroni‑adjusted p ≥ 0.05.  

- [ ] T021a    Add logic to `fit_distributions.py` that flags games with `< 100` runs as `sample_flag = "low‑sample"` and writes a descriptive row (`distribution_family = "descriptive"`) containing only `game_id` and `sample_flag`.  
  – **Verification**: Such rows appear with `rejected = false`.  

---  

## Phase 4 – Mixed‑effects modeling (User Story 3, P3)

- [ ] T024    Create the **ModelCoefficient** JSON‑Schema file `contracts/model_coefficient.schema.yaml` (matches data‑model definition).  
  – **Verification**: `jsonschema.validate` of `mixed_effects_results.csv` rows succeeds; unit test `tests/test_model_coefficient_schema.py` passes.  

- [ ] T027    Implement `code/scripts/fit_mixed_effects.py` that reads `run_records.csv`, merges external `game_metadata.csv` (difficulty labels), fits hierarchical model  
  `log(run_time_seconds) ~ log(attempt_number) + difficulty_label + competitive_pressure + (1|runner_id) + log(attempt_number):competitive_pressure`,  
  computes VIF (rejecting > 5), performs likelihood‑ratio tests, applies Bonferroni correction, and writes `data/processed/mixed_effects_results.csv`.  
  – **Verification**: Model converges without warnings; VIF ≤ 5; fixed‑effect table includes Bonferroni‑corrected `p_value`.  

- [ ] T030    Add pre‑run check that excludes any game lacking a difficulty label (FR‑006). Log excluded `game_id`s to `data/processed/excluded_games.log`.  
  – **Verification**: Log file exists and contains entries when labels missing.  

---  

## Phase 5 – Validation, reporting & hand‑off

- [ ] T009    Contract validation: run `jsonschema` against `run_record.schema.yaml`, `distribution_fit.schema.yaml`, and `model_coefficient.schema.yaml` for their respective CSVs.  
  – **Verification**: All rows validate; pipeline aborts on any schema violation.  

- [ ] T029b    Implement `code/scripts/generate_report.py` that aggregates tables/figures, scans for prohibited causal terms (SC‑006), calls the reference‑validator agent, and writes `paper/draft.md`.  
  – **Verification**: Script produces `paper/draft.md`; grep finds no prohibited terms; reference validator log shows `{"status":"VERIFIED"}`.  

- [ ] T028b    Append a “Power Analysis” paragraph to `paper/draft.md` after the report is generated, reporting effect‑size assumptions from `config.yaml`, total sample size per game, and noting limited power for `< 100`‑run games (FR‑009).  
  – **Verification**: Paragraph appears verbatim in the final markdown with numeric effect‑size value.  

- [ ] T036    Run `hash_artifacts.py` one final time to record SHA‑256 hashes of all output artifacts under `data/` and `paper/`.  
  – **Verification**: `state/artifact_hashes.json` includes entries for `run_records.csv`, `distribution_fits.csv`, `mixed_effects_results.csv`, and `paper/draft.md`.  

- [ ] T037    Execute the full end‑to‑end pipeline on the default configuration as a CI smoke test.  
  – **Verification**: CI job finishes within the 6‑hour wall‑time limit, exits with status 0, and the final report contains the Power Analysis section and no causal language.  

---  

## Phase 6 – Optional polish (parallelizable)

- [ ] T032 [P] Update `quickstart.md` with exact commands to (a) install dependencies, (b) run the full pipeline, and (c) reproduce the report.  
  – **Verification**: Documentation builds without broken links; fresh clone reproduces identical artifacts (hashes match).  

- [ ] T034a [P] Add a memory‑profile log `data/checkpoints/memory_log.txt` produced by `python -m memory_profiler code/scripts/main.py`.  
  – **Verification**: Log file exists and reports peak memory < 7 GB.  

---  

### Summary of pending (unchecked) tasks  

| ID | Phase | Description |
|----|-------|-------------|
| T010 | 2 | Create `contracts/run_record.schema.yaml`. |
| T023 | 3 | Create `contracts/distribution_fit.schema.yaml`. |
| T024 | 4 | Create `contracts/model_coefficient.schema.yaml`. |
| T015a | 1 | Add checkpointing to `fetch_data.py`. |
| T015b | 2 | Add checkpointing to `preprocess.py`. |
| T033a | 1 | Refactor pagination logic into reusable helper. |
| T033b | 2 | Extract lagged‑pressure calculation into utils. |
| T030 | 4 | Exclude games without difficulty labels & log them. |
| T028b | 5 | Append power‑analysis paragraph to the report (now after report generation). |
| T029b | 5 | Generate final report with associational‑language check. |
| T036 | 5 | Record final artifact hashes. |
| T037 | 5 | Run full end‑to‑end smoke test on CI. |
| T032 | 6 | Update `quickstart.md`. |
| T034a | 6 | Record memory‑profile log. |

All tasks are expressed as Markdown checklist items with explicit artifact paths and verification steps, ready for the execution stage.  