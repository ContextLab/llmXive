# Tasks: llmXive follow-up: extending “FastContext: Training Efficient Repository Explorer for Coding Agents”

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and the current `tasks.md` template.  
All tasks are written as checklist items with unique IDs, required artifact paths, and explicit verification steps.

---

## Phase 1 – Project Setup (foundational infrastructure)

- [ ] **T001** [US0] Create the project directory hierarchy under `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/`  
  `data/raw`, `data/processed`, `data/results`, `code/`, `tests/unit/`, `tests/integration/`, `specs/contracts/`, `state/`  
  **Verification**: Run `tree -L 2 projects/PROJ-905-llmxive-follow-up-extending-fastcontext/` and assert that each of the nine directories exists.

- [ ] **T002** [US0] Add a pinned `requirements.txt` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/requirements.txt` containing the exact package list required for the study (CPU‑only wheels).  
  **Verification**: `cat …/requirements.txt` must list all packages; `pip install -r …` completes without requesting CUDA or non‑CPU wheels.

- [ ] **T003a** [US0] Create a lint‑configuration file `.ruff.toml` in `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` with the rule set `["E", "F", "I", "W"]` and `target-version = "py311"`.  
  **Verification**: `ruff check …` runs without configuration errors.

- [ ] **T003b** [US0] Create `pyproject.toml` in `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` with Black configuration (`line-length = 88`, `target-version = ["py311"]`).  

- [ ] **T004** [US0] Implement `code/versioning.py` to compute SHA‑256 hashes for all files under `data/` and `code/` and write a manifest to `state/projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml`.  

- [ ] **T005** [US0] Add `code/__init__.py` and copy the JSON schema files from `specs/contracts/` into `code/` for easy import.  

- [ ] **T006** [US0] Create `code/config.py` exposing constants for dataset identifiers, TF‑IDF hyper‑parameters, and weighting factors (`w1`, `w2`).  

- [ ] **T007** [US0] Implement `code/data_loader.py` that streams the SWE‑bench Lite dataset via `datasets.load_dataset("princeton-nlp/SWE-bench_Lite", split="test", streaming=True)`. The script must verify the SHA‑256 checksum of each downloaded shard and raise an exception on mismatch (no synthetic fallback).  

---

## Phase 2 – Core Data Curation (User Story 1)

- [ ] **T011** [US1] Implement `code/static_analysis.py` to compute a composite `regularity_score` (dir_score + w1·test_score + w2·import_score).  
  **Verification**: Run the script on a small repo fixture and confirm the CSV output contains a `regularity_score` column with values in [0, 1].

- [ ] **T012** [US1] Add edge‑case handling in `static_analysis.py` (missing test files, extreme irregularity) returning a default score defined in `config.py`.  

- [ ] **T013** [US1] Create `code/stratification.py` that sorts all repositories by `regularity_score` and splits them into two balanced strata (“Regular” and “Irregular”).  

- [ ] **T014** [US1] Export the scores and stratification to `data/processed/regularity_scores.csv` (columns: `instance_id`, `repo`, `regularity_score`, `split`).  

- [ ] **T007c** [US1] Pilot validation script `code/pilot_validation.py`  
  * Loads the first **20** entries of `regularity_scores.csv`.  
  * Runs a lightweight retrieval baseline (e.g., keyword TF‑IDF over file names) on each repository to obtain a **precision** estimate.  
  * Computes the Pearson correlation between `regularity_score` and the baseline precision.  
  * Writes `data/processed/pilot_correlation.json` with schema `{ "pearson_r": float, "p_value": float, "n_samples": int }`.  
  **Verification**: The JSON file must exist, contain exactly three keys, and `n_samples` ≥ 20.

---

## Phase 3 – Deterministic Engine & Baseline (User Story 2)

- [ ] **T019** [US2] Implement `code/fastcontext_lite.py`  
  * Deterministic parser extracts issue keywords.  
  * Builds a **streaming** TF‑IDF index over repository files (chunked reads, `ngram_range=(1,2)`, `max_features=10000`).  
  * Retrieves top‑K snippets matching the issue vector.  
  * Returns a JSON log with `context_precision`, `total_tokens`, and `exploration_latency_ms`.  
  **Verification**: Run on a single “Regular” repo fixture; the output JSON must validate against `exploration_log.schema.yaml` and contain all three fields.

- [ ] **T019b** [US2] Add `code/benchmark_lite.py` to benchmark the Lite engine on a stratified sample (e.g., 50 repos) and record wall‑clock latency and peak memory usage in `data/results/lite_benchmark.json`.  

- [ ] **T021a-1** [US2] Implement `code/baseline_runner.py` (Step 1) to load the original FastContext 4B model (`princeton-nlp/fastcontext-4b`) on CPU (`device_map="cpu"`). Log `hardware: cpu`.  

- [ ] **T021a-2** [US2] Extend `baseline_runner.py` (Step 2) with a **GPU escape hatch**: on any OOM or CUDA‑related error, automatically re‑run on a single GPU (`device_map="auto"`, `max_memory=16GB`). Record `hardware: gpu`. No model down‑scaling or synthetic fallback is allowed.  

- [ ] **T021a-3** [US2] Add metric normalisation (Step 3) to `baseline_runner.py`: compute `tokens_per_sec = total_tokens / (latency_ms/1000)` and store the result alongside other metrics in `data/results/exploration_logs.jsonl`, preserving the schema `execution_schema.yaml`.  

- [ ] **T022** [US2] Create `code/metrics_logger.py` that validates each metric record against `execution_schema.yaml` before appending to `exploration_logs.jsonl`.  

- [ ] **T023** [US2] Write orchestration script `code/main.py` that iterates over the stratified splits, runs **both** `fastcontext_lite.py` and `baseline_runner.py`, and writes all logs to `data/results/exploration_logs.jsonl`.  

---

## Phase 4 – Statistical Comparison & Boundary Detection (User Story 3)

- [ ] **T027** [US3] Implement `code/analysis.py` to:  
  * Perform a normality test (`scipy.stats.shapiro`) on the paired metric differences for the “Regular” set.  
  * Choose a paired t‑test or Wilcoxon signed‑rank test accordingly.  
  * Compute effect size (Cohen’s d or rank‑biserial).  
  * If `pilot_correlation.json` exists, use its Pearson r to inform a power analysis (target β = 0.8); otherwise fall back to a default medium effect size (d = 0.5).  
  * Write a summary JSON `data/results/statistical_summary.json` conforming to `statistical_summary.schema.yaml`.  

- [ ] **T028b** [US3] Extend `analysis.py` to compute descriptive statistics (mean, std) **and** a linear regression of `regularity_score` vs. performance delta (Lite − Baseline) for the full dataset. Store `regression_slope` and `r_squared` in the same summary JSON.  

- [ ] **T029** [US3] Add degradation calculation for the “Irregular” set: compute the percentage drop in precision of Lite vs. Baseline, compare against the 10 % threshold (SC‑004), and add fields `degradation_percent` and `boundary_exceeded` (boolean) to `statistical_summary.json`.  

- [ ] **T031** [US3] Finalize the output schema for `statistical_summary.json` to include all required keys (`test_type`, `dataset`, `metrics`, `boundary_analysis`, plus the regression fields). Validate the file against `analysis_schema.schema.yaml`.  

---

## Phase 5 – Documentation, Cleanup & Final Checks

- [ ] **T032a** [US0] Update `README.md` at the project root with installation steps, usage examples for the three entry points (`data_loader.py`, `fastcontext_lite.py`, `baseline_runner.py`), and contribution guidelines.  

- [ ] **T032b** [US0] Add API documentation in `docs/` for `static_analysis.py`, `fastcontext_lite.py`, and `analysis.py` (auto‑generated with `pdoc` or similar).  

- [ ] **T033a** [US0] Remove unused imports from all files under `code/`.  

- [ ] **T033b** [US0] Enforce line‑length ≤ 88 characters across the code base (run `ruff` or `black --check`).  

- [ ] **T033c** [US0] Add type hints to all public functions in `code/`.  

- [ ] **T035a** [US0] Unit test `tests/unit/test_edge_cases.py::test_empty_repo_handling` – ensure `static_analysis.py` returns a default score for an empty repository without raising.  

- [ ] **T035b** [US0] Unit test `tests/unit/test_edge_cases.py::test_binary_files_only_handling` – verify the import‑graph scorer gracefully skips binary files.  

- [ ] **T035c** [US0] Unit test `tests/unit/test_edge_cases.py::test_circular_imports_handling` – confirm the import‑graph score does not enter an infinite loop on circular imports.  

- [ ] **T036** [US0] Run the end‑to‑end pipeline documented in `quickstart.md` and confirm that:  
  1. `regularity_scores.csv` is generated,  
  2. `exploration_logs.jsonl` contains entries for both methods,  
  3. `statistical_summary.json` validates against its schema, and  
  4. All unit and integration tests pass (`pytest -q`).  

---

## Dependencies & Execution Order

| Phase | Prerequisite Tasks | Blocking Tasks |
|------|--------------------|----------------|
| **Setup** | – | T001 → T002 → T003a → T003b → T004 → T005 → T006 → T007 |
| **User Story 1** | Setup | T011 → T012 → T013 → T014 → T007c |
| **User Story 2** | Setup & US 1 (for split) | T019 → T019b → T021a‑1 → T021a‑2 → T021a‑3 → T022 → T023 |
| **User Story 3** | US 2 (metrics) & optional pilot | T027 → T028b → T029 → T031 |
| **Polish** | All previous phases | T032a, T032b, T033a‑c, T035a‑c, T036 |

Tasks marked **[P]** can run in parallel when their file targets do not overlap. All other tasks must respect the data‑flow order shown above.  

--- 

*End of `tasks.md`.*
