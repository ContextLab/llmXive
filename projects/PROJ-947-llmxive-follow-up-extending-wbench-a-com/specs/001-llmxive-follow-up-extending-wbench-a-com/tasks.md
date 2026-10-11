# Tasks: llmXive Follow‑up: Extending WBench with Sequence Complexity Analysis  

**Input**: `spec.md`, `plan.md`, `data‑model.md`, contracts, and existing research artifacts.  

The tasks are ordered to respect data flow and the research phases described in the template.  Checked boxes (`[X]`) indicate work already verified; unchecked boxes (`[ ]`) are pending and have been re‑opened where verification failed.  Each item lists the primary artifact(s) it creates or modifies and the verification step(s) required.

---

## Phase 1 – Project Setup & Initial End‑to‑End Run  

| Goal | Description |
|------|-------------|
| Establish a clean repository layout that the execution engine can discover. | All directories must exist (even if empty) and be visible in a `git ls‑tree` listing. |
| Provide a minimal runnable command that downloads a tiny WBench sample and runs the full pipeline on it. | The command must complete without error and produce a CSV under `data/results/` with the required columns. |

- [X] T001 [P] **Create top‑level project directories** `code/`, `tests/`, `data/`, `results/`.  
  *Verification*: Run `ls -d */` at repo root and confirm the four directories are listed.

- [X] T002 **Create test sub‑directories** `tests/unit/`, `tests/integration/`, `tests/contract/`.  
  *Verification*: `ls tests/` must show the three folders; each contains a placeholder `__init__.py` file.

- [ ] T003 [P] **Add `requirements.txt`** with pinned versions for the scientific stack (datasets, pandas, networkx, scipy, scikit‑learn, torch, transformers, opencv‑python‑headless).  
  *Verification*: `pip install -r requirements.txt` succeeds in a clean venv.

- [X] T004 [P] **Create `data/raw/`, `data/processed/`, and `data/checksums.json`** placeholder files.  
  *Verification*: Directory tree shows the three locations; `data/checksums.json` is a valid empty JSON object (`{}`).

- [X] T005 [P] **Implement `code/config.py`** exposing random seeds, RAM limits, and model‑path constants.  
  *Verification*: Importing `code.config` yields the expected attributes; `config.RAM_LIMIT_GB == 6.5`.

- [ ] T006 [P] **Add structured JSON logger** in `code/utils/logging.py` (function `get_logger`).   <!-- FAILED-IN-EXECUTION: code/utils/dummy_logger_test.py exit=5 --> <!-- FAILED-IN-EXECUTION: code/utils/dummy_logger_test.py exit=5 -->
  *Verification*: Running a dummy script logs a JSON line to stdout without errors.

- [ ] T007 [P] **Create checksum validator** `code/data/verify_checksums.py` that raises on mismatch.  
  *Verification*: Running the validator on the placeholder `data/checksums.json` passes; tampering the file causes a raised `ChecksumError`.

- [ ] T008 [P] **Add error‑handling helpers** `code/utils/errors.py` with `fail_loudly()` and `skip_on_error()` that raise exceptions rather than synthesize data.  
  *Verification*: Unit test confirms that `skip_on_error()` does **not** catch a raised `RuntimeError`.

---

## Phase 2 – Core Infrastructure (blocks all user stories)  

- [ ] T009 **Create `code/data/download_wbench.py`** that streams the official WBench Parquet from HuggingFace (`datasets.load_dataset(..., streaming=True)`) into `data/raw/`.  
  *Verification*: After execution, `data/raw/wbench.parquet` exists and its SHA‑256 matches the value recorded in `data/checksums.json`.

- [ ] T010 [P] **Add `code/entropy/__init__.py`** and expose public functions.  
  *Verification*: `import code.entropy as ent` works without ImportError.

- [ ] T011 [P] **Add `code/inference/__init__.py`** and expose the model registry.  
  *Verification*: `from code.inference import models` imports correctly.

- [ ] [X] T012 **Implement `code/entropy/generator.py`** – token‑reweighting & resampling algorithm that creates Low (< 0.3), Medium (0.3‑0.7), High (> 0.7) entropy variants for **every** base WBench case.  
  *Outputs*: `data/processed/variants.csv` (matches `sequence_variant.schema.yaml`) and `data/processed/generation_logs.json`.  
  *Verification*: CSV contains rows for all base cases × 3 variants; entropy values respect thresholds; logs show ≤ 20 iterations per case.

- [ ] [X] T013 [US1] **Implement `code/entropy/validator.py`** – Task Validity Validator (Action‑Chain Check).  
  *Inputs*: `data/processed/variants.csv`.  
  *Outputs*: `data/processed/validity_flags.csv` with columns `case_id`, `variant_type`, `is_valid`.  
  *Verification*: Unit test supplies a deliberately broken variant and asserts `is_valid == False`; all valid rows have `True`.

- [ ] [X] T014 [US1] **Implement `code/entropy/scorer.py`** – computes the full **Sequence Complexity Score**:  
  - Shannon entropy (0‑1)  
  - Semantic similarity (> 0.85) using a pre‑trained intent encoder (CPU‑only)  
  - Dependency depth (longest path) derived **from the original un‑manipulated intent graph**.  
  *Outputs*: `data/processed/complexity_scores.csv` (matches `sequence_variant.schema.yaml`).  
  *Verification*: Spot‑check on a known case yields depth = 3, entropy ≈ 0.62, similarity ≥ 0.90.

- [ ] T015 [US1] **Create pipeline script `code/entropy/run_pipeline.py`** that orchestrates download → generation → validation → scoring for the full dataset.  
  *Verification*: Running the script produces all three CSVs (`variants.csv`, `validity_flags.csv`, `complexity_scores.csv`) and exits with status 0.

- [ ] T016 [US1] **Add pre‑analysis variance guard** in `run_pipeline.py` that aborts with a clear `[CRITICAL]` log if the variance of `entropy_score` across all variants ≤ 0.05.  
  *Verification*: Unit test feeds a low‑variance dummy CSV and expects the script to raise `RuntimeError` with the `[CRITICAL]` message.

---

## Phase 3 – User Story 2: CPU‑Optimized Inference on Stratified Data  

- [ ] T017 [P] **Implement `code/inference/models.py`** – registers up to 5 publicly available CPU‑compatible world models (e.g., GGUF‑converted HuggingFace models < 7 GB). Validates RAM footprint via `torch.cuda.is_available()` fallback and `psutil`.  
  *Verification*: Importing the module lists at least three models with `model.ram_gb < 7`.

- [ ] [X] T018 [US2] **Implement `code/inference/runner.py`** – for each `(variant, model)` pair:  
  1. Profile peak RAM (`psutil.virtual_memory().used`) before launch.  
  2. If projected usage > 6.5 GB, **skip** the model and log a warning.  
  3. Run inference (CPU) and write the MP4 to `results/videos/<model>_<variant>.mp4`.  
  4. On OOM or other failure, record a row with `status='failed'` and `video_path=null`.  
  5. If a model is flagged as unsuitable, record `status='proxy_used'` and fill scores with `NaN`.  
  *Outputs*: `data/processed/inference_results.csv` (conforms to `inference_result.schema.yaml`).  
  *Verification*: Integration test mocks an OOM condition and asserts the CSV contains a `failed` row; another test forces a RAM‑exceed case and checks for a `proxy_used` row.

- [ ] T019 [US2] **Add failure‑handling logic** (part of `runner.py`) that logs the exception, writes the appropriate CSV entry, and continues processing remaining models.  
  *Verification*: Unit test raises a generic `RuntimeError` inside the inference loop and confirms the pipeline does not abort.

- [ ] [X] T020 [US2] **Create inference pipeline script `code/inference/run_inference.py`** that reads `data/processed/validity_flags.csv`, selects only rows with `is_valid=True`, and executes `runner.py` for every selected variant across all registered models.  
  *Verification*: After execution on the full dataset, `inference_results.csv` contains ≤ N × 3 × M rows (where M is the number of valid models) and no duplicate `result_id`s.

- [ ] [X] T021 [US2] **Enforce minimum‑model constraint** – `run_inference.py` must raise a clear error if fewer than three models pass the RAM check.  
  *Verification*: Unit test temporarily removes two models from the registry and expects a `RuntimeError` with the message “At least 3 valid models required”.

---

## Phase 4 – User Story 3: Correlation & Trend Analysis  

- [ ] T022 [P] **Unit tests for statistical modules** (`tests/unit/analysis/test_correlation.py`, `tests/unit/analysis/test_correction.py`) already exist and pass.  

- [ ] T023 [US3] **Implement `code/metrics/baseline.py`** – generates a short random‑noise video, runs the WBench motion‑artifact metric, and writes `data/processed/baseline_scores.json` containing the scalar baseline value.  
  *Verification*: Running the script creates the JSON file; its value is a float between 0 and 1.

- [ ] T024 [US3] **Implement `code/metrics/wbench_suite.py`** – computes physics compliance and temporal consistency for a given video, subtracts the baseline from `baseline_scores.json`, and returns the corrected scores.  
  *Outputs*: Appends rows to `data/processed/fidelity_metrics.csv` (`case_id`, `model_name`, `physics_score`, `consistency_score`, `execution_mode`).  
  *Verification*: Unit test feeds a deterministic video (e.g., a static frame) and checks that `physics_score` equals `baseline` → 0 after subtraction.

- [ ] [X] T025a [US3] **Implement `code/analysis/pearson.py`** – computes Pearson correlation coefficient *r* and its two‑tailed p‑value between `complexity_score` and `physics_score` for each model.  
  *Outputs*: `data/processed/pearson_correlation.csv` (`model_name`, `r`, `p_value`).  
  *Verification*: Synthetic data with known correlation yields `|r| > 0.8` and `p_value < 0.001`.

- [ ] [X] T025b [US3] **Implement `code/analysis/correlation.py`** – performs **One‑Way ANOVA** across the three entropy levels for each model, computes the F‑statistic, raw p‑value, and determines the trend direction (linear vs. non‑linear) using `scipy.stats`.  
  *Outputs*: `data/processed/analysis_intermediate.csv` (model, entropy_level, mean_score, std_score).  
  *Verification*: Synthetic data with a strong effect yields `p_value < 0.001` and `trend_type='linear'`.

- [ ] [X] T026 [US3] **Implement `code/analysis/correction.py`** – applies Bonferroni correction across the set of models and writes `data/processed/analysis_summary.csv` matching `analysis_summary.schema.yaml`.  
  *Verification*: For a test set of 4 models, corrected p‑values equal `raw_p * 4`; the `significant` flag flips appropriately **and** asserts `bonferroni_p_value < 0.05` for any flagged significant result.

- [ ] [X] T027a [US3] **Create `code/analysis/degradation_curve.py`** – merges `complexity_scores.csv`, `inference_results.csv`, and `fidelity_metrics.csv` into `data/processed/degradation_curve.csv` conforming to the `DegradationCurve` schema.  
  *Verification*: CSV loads without error and contains columns `model_name`, `entropy_level`, `mean_physics_score`, `std_physics_score`, `f_statistic`, `p_value`, `bonferroni_p_value`, `significant`, `trend_type`, `execution_mode`.

- [ ] [X] T027 [US3] **Create analysis pipeline `code/analysis/run_analysis.py`** that:  
  1. Merges `complexity_scores.csv`, `inference_results.csv`, and `fidelity_metrics.csv`.  
  2. Calls `pearson.py`, `correlation.py`, `correction.py`, and `degradation_curve.py`.  
  3. Writes final `results/analysis_summary.csv` and a human‑readable `results/summary.txt` that explicitly lists **Pearson r**, **ANOVA F‑statistic**, **p‑values**, **Bonferroni‑corrected p‑values**, and **trend_type** for each model.  
  *Verification*: End‑to‑end run on the full dataset produces a non‑empty summary with at least one model flagged as significant (if data permits) and confirms that `trend_type` is present.

- [ ] T028 [US3] **Optional Chow test for breakpoint detection** – if `trend_type='non-linear'`, run a Chow test (via `statsmodels`) and, when `p < 0.05`, add a `breakpoint` column to `analysis_summary.csv`.  
  *Verification*: Unit test with synthetic two‑segment data confirms the breakpoint is recorded.

---

## Phase 5 – Polish, Validation & Handoff  

- [ ] T029a [P] **Generate content hashes** for core CSV artifacts (`variants.csv`, `complexity_scores.csv`, `inference_results.csv`, `fidelity_metrics.csv`, `pearson_correlation.csv`, `analysis_summary.csv`).  
  *Verification*: Script prints a SHA‑256 for each file; the JSON `data/checksums.json` contains matching entries.

- [ ] T029b [P] **Generate content hashes** for derived analysis artifacts (`degradation_curve.csv`, `summary.txt`).  
  *Verification*: Same as T029a but for the derived files.

- [ ] T030 [P] **Run full integration test suite** (`pytest -q`) on the full dataset.  
  *Verification*: All tests pass; total runtime < 30 minutes on the CI runner.

- [ ] T030a [HIGH] **Measure total inference runtime** and assert it is < 6 hours.  
  *Verification*: `code/inference/run_inference.py` records wall‑clock time; a post‑run check raises an error if runtime exceeds 6 h.

- [ ] T031 [P] **Update `code/requirements.txt`** with the exact versions pinned during the successful run (output of `pip freeze`).  
  *Verification*: The file is non‑empty and sorted alphabetically.

- [ ] T032 [US3] **Produce final results artifacts**:  
  - `results/analysis_summary.csv` (already created by T027)  
  - `results/trend_plot.png` visualizing mean physics score vs. entropy level per model (using `matplotlib`).  
  *Verification*: Opening the PNG shows labeled axes and a legend; the CSV can be loaded without error.

- [ ] T033 [P] **Write `quickstart.md`** with step‑by‑step commands to reproduce the entire pipeline from data download to final analysis, including required environment variables.  
  *Verification*: A fresh clone that follows the instructions reproduces the same `analysis_summary.csv` (identical hash).

- [ ] T034 [P] **Add contract documentation** under `contracts/` linking each schema file to the producing script (e.g., `generator.py → sequence_variant.schema.yaml`).  
  *Verification*: Each contract file contains a markdown table with “produced by” entries matching the code paths.

- [ ] T035 [P] **Finalize handoff note** `results/handoff.txt` summarizing: research question, key findings (correlation coefficient, significance), limitations (variance threshold, CPU‑only models), and next‑step suggestions.  
  *Verification*: The file is ≤ 500 words and includes the exact numeric values from `analysis_summary.csv`.

---

### Dependency & Execution Order Summary  

1. **Phase 1** tasks must complete before any code can be imported.  
2. **Phase 2** (download & core modules) must finish before **User Story 1** (T012‑T016).  
3. **User Story 1** produces `variants.csv`, `validity_flags.csv`, and `complexity_scores.csv` → required by **User Story 2** (inference).  
4. **User Story 2** creates `inference_results.csv` → required by **User Story 3** (analysis).  
5. **User Story 3** consumes all three CSVs, the baseline JSON, and produces the final summary and `degradation_curve.csv`.  
6. **Phase 5** runs after the full pipeline succeeds, ensuring reproducibility and documentation.

--- 

*All pending tasks are written as unchecked boxes; completed tasks retain their checked status.  The list respects the canonical format `- [ ] T### [P?] [USx?] description …` and includes explicit artifact paths and verification steps, ready for the next verification round.* 