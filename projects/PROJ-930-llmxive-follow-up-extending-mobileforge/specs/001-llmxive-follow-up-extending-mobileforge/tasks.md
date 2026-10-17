# Tasks: MobileForge Logic Distillation – CPU‑tractable Reasoning Model  

**Project root**: `projects/PROJ-930-llmxive-follow-up-extending-mobileforge`

---

## Phase 1 – Project bootstrap (infrastructure only)

- [ ] T001 **Create the full directory tree required for the study**  
  *Creates* `projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/{data/raw,data/processed,data/evaluation,models,utils,tests/unit,tests/integration}` and `projects/PROJ-930-llmxive-follow-up-extending-mobileforge/data/`, `projects/PROJ-930-llmxive-follow-up-extending-mobileforge/outputs/`.  
  **Verification** – after running the task, a `tree` (or equivalent) shows all listed directories; CI checks that each path exists.

- [X] T002 **Write a pinned `requirements.txt` under `code/`** containing exactly the 11 required lines (no extra packages).  
  ```text
  torch==2.2.2
  transformers==4.41.0
  datasets==2.18.0
  pandas==2.2.2
  scikit-learn==1.5.0
  scipy==1.13.0
  statsmodels==0.14.2
  tqdm==4.66.2
  pytest==8.2.2
  ruff==0.4.2
  black==24.4.2
  ```  
  **Verification** – the file exists at `code/requirements.txt`, contains exactly the lines above, and the CI step `pip install -r code/requirements.txt` runs without error; the CI log is stored as `outputs/install_log.txt`.

- [X] T003 **Configure linting and formatting tools**  
  *Creates* `pyproject.toml` (project‑wide Black configuration) and `.ruff.toml` (Ruff rules) in the repository root.  
  **Verification** – both files exist and contain a `[tool.black]` section with `line-length = 88` and a `[tool.ruff]` section with `select = ["E", "F", "W"]`.

- [X] T004 **Initialize reproducibility artifacts (project‑owned)**  
  *Creates* an (initially empty) `data/checksums.json` (to be populated by download tasks) and `outputs/reproducibility_meta.json` containing the project‑level random seed and timestamp.  
  **Verification** – both JSON files exist; CI validates that they are valid JSON and that `outputs/reproducibility_meta.json` contains a non‑empty `"seed"` field. `data/checksums.json` need only exist at this stage.

---

## Phase 2 – Core utilities (foundation for all user stories)

- [X] T005 **Implement `utils/emulator.py`** with the exact public interface required by the evaluation stage:  
  - Functions: `launch_emulator()`, `send_action(action_seq)`, `check_crash()`, `get_screenshot()`.  
  - Error codes (constants): `EMU_CRASH`, `EMU_TIMEOUT`, `EMU_NOT_FOUND`.  
  All functions raise clear exceptions on failure; no silent fall‑backs.  
  **Path**: `code/utils/emulator.py`  
  **Verification** – `python -c "import utils.emulator as e; assert hasattr(e, 'launch_emulator')"` runs without import errors; unit‑test scaffold is present (see T006).

- [X] T006 **Implement `utils/metrics.py`** providing two lightweight classes:  
  - `SuccessRate` with method `compute(success_flags: List[bool]) -> float`.  
  - `StepEfficiency` with method `compute(steps_taken: List[int], optimal_steps: List[int]) -> float`.  
  **Path**: `code/utils/metrics.py`  
  **Verification** – both classes importable and methods return values in the documented ranges (0‑1 for success rate, ≥0 for efficiency).

- [X] T007 **Implement `utils/power_analysis.py`** that performs the a‑priori McNemar power calculation (target Power = 0.8, effect size h = 0.2, α = 0.05, baseline p₀ = 0.5).  
  - Uses a McNemar‑appropriate power estimator (e.g., `statsmodels.stats.power.NormalIndPower` approximation).  
  - Writes the result to `outputs/power_analysis.json` conforming to `contracts/power_analysis.schema.yaml`.  
  - Exits with a clear error if any data‑extraction artifact already exists (enforces the “before extraction” rule).  
  **Path**: `code/utils/power_analysis.py`  
  **Verification** – after execution, `outputs/power_analysis.json` exists, contains an integer `n_required` ≥ 1 and the full `parameters` block; CI validates the file against its JSON schema.

---

## Phase 3 – Data pipeline (US‑1)

- [ ] T008 **Implement `data/raw/download_mobileforge.py`** that fetches the official MobileForge logs via the HuggingFace Hub:   <!-- FAILED-IN-EXECUTION: code/data/raw/download_mobileforge.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/raw/download_mobileforge.py exit=1 -->
  ```python
  from datasets import load_dataset
  ds = load_dataset("mobileforge/logs", split="train", streaming=False)
  ds.save_to_disk("data/raw/mobileforge_logs")
  ```  
  - After download, compute SHA‑256 checksums for each file and write them to `data/checksums.json`.  
  - On any network error or checksum mismatch the script raises an exception (no synthetic fallback).  
  **Path**: `code/data/raw/download_mobileforge.py`  
  **Verification** – script exits with code 0 only when the dataset is present and checksums match; CI records a success log in `outputs/download_log.txt`.

- [ ] T009 **Validate the raw ExtractionDataset file** (`data/raw/mobileforge_logs/...`) against `contracts/dataset.schema.yaml`.  
  **Verification** – schema validation passes; CI runs a `jsonschema` check and fails if the raw data does not conform.

- [ ] T010 **Implement `utils/extraction.py`** that:  
  1. Loads the raw logs produced by T008.  
  2. Filters for `trajectory_status == "failed_then_success"` and discards any `corrective_hint` containing coordinate patterns (`\[\d+,\d+\]`).  
  3. Reads the random seed from `outputs/reproducibility_meta.json` and sets it before any stochastic operation (e.g., shuffling).  
  4. Reads `outputs/power_analysis.json` to obtain the required sample size **N**; aborts with a clear error if `n_required` is missing or if the number of valid triples < N.  
  5. Writes the filtered dataset to `data/processed/triples_v1.parquet` (schema `contracts/extraction_dataset.schema.yaml`).  
  6. Emits `outputs/extraction_stats.json` with `{ "valid_count": <int>, "status": "PASS"|"FAIL" }`.  
  **Path**: `code/utils/extraction.py`  
  **Verification** – parquet file exists, schema validation passes, and `extraction_stats.json` reports `"PASS"` with `valid_count ≥ N`.

---

## Phase 4 – Model training (US‑2)

- [ ] T011 **Validate the processed training parquet** (`data/processed/triples_v1.parquet`) against `contracts/training_input.schema.yaml`.  
  **Verification** – schema validation succeeds; CI asserts JSON‑schema compliance before training begins.

- [ ] T012 **Implement `models/train_distilled.py`** that trains a T5‑small encoder‑decoder model on the processed triples:  
  - Enforces `device="cpu"`; aborts immediately if `torch.cuda.is_available()` is true (SC‑008).  
  - Reads the random seed from `outputs/reproducibility_meta.json` and sets it for deterministic training.  
  - Uses a hard timeout (`signal.alarm(6*60*60)`) to guarantee training ≤ 6 h; on timeout exits with message *“Training Timeout: Exceeded 6 h”*.  
  - Batch size ≤ 8, gradient accumulation to stay < 7 GB RAM.  
  - Early‑stopping on validation loss (patience = 1).  
  - Saves the final model weights and config to `outputs/distilled_t5/` (contains `pytorch_model.bin` and `config.json`).  
  - Writes `outputs/training_log.json` that records the seed used, hyper‑parameters, epoch times, and final loss.  
  **Path**: `code/models/train_distilled.py`  
  **Verification** – after a successful run the directory `outputs/distilled_t5/` contains the expected files; the runtime log `outputs/training_log.txt` records “Training completed in XhYm” with X ≤ 6.

---

## Phase 5 – Evaluation & statistical validation (US‑3)

- [ ] T013 **Implement the evaluation pipeline `models/eval_pipeline.py`** that performs the full paired comparison:  
  1. Reads the random seed from `outputs/reproducibility_meta.json` and sets it.  
  2. Reads `outputs/power_analysis.json` to obtain **N**.  
  3. Loads the AndroidWorld benchmark via `datasets.load_dataset("androidworld", split="test")`; aborts if the dataset contains fewer than N unique tasks.  
  4. Writes the selected task IDs to `outputs/eval_tasks.json`.  
  5. **CPU‑only guard** – aborts if `torch.cuda.is_available()`.  
  6. For each task ID, runs the distilled T5 model **and** the TinyLlama baseline on the *exact same* UI state and hint (using `utils.emulator` to execute the generated action sequence).  
  7. Records binary success/failure and step counts for both models in `outputs/paired_results.csv`.  
  8. Constructs the 2 × 2 contingency table, runs a one‑tailed McNemar test (`scipy.stats.mcnemar` with `exact=True` when appropriate), and writes `outputs/evaluation_results.json` conforming to `contracts/evaluation.schema.yaml`.  
  **Path**: `code/models/eval_pipeline.py`  
  **Verification** – the JSON file contains `statistical_test.test_type == "McNemar"`, a numeric `p_value`, and `significant` is true only when `p_value < 0.05`. All task IDs appear in `paired_results.csv`.

- [ ] T014 **Implement the ablation pipeline `models/ablation_pipeline.py`** that repeats step 6 of T013 but replaces every `Corrective_Hint` with the literal string `"retry"`:  
  - Includes the same CPU‑only guard as T013.  
  - Writes per‑task binary outcomes to `outputs/ablation_results.json`.  
  - Generates a human‑readable markdown report `outputs/ablation_report.md` summarizing success‑rate differences between the hint‑condition and the generic‑retry condition, and includes a one‑tailed McNemar p‑value.  
  **Path**: `code/models/ablation_pipeline.py`  
  **Verification** – the markdown report exists, contains a table with both success rates, and a p‑value ≤ 1.0; CI validates the JSON against `contracts/evaluation.schema.yaml` (the ablation schema is a subset).

- [ ] T015 **Implement the sensitivity‑sweep script `models/sensitivity_sweep.py`** that:  
  - Loads `outputs/paired_results.csv`.  
  - For each Levenshtein‑distance threshold in `{0, 1, 2, 3}` recomputes binary success (action sequence considered successful if edit distance ≤ threshold).  
  - Calculates the success‑rate for both models at every threshold, computes variance across thresholds, and writes `outputs/sensitivity_report.json` matching the `sensitivity_report` section of `contracts/evaluation.schema.yaml`.  
  **Path**: `code/models/sensitivity_sweep.py`  
  **Verification** – JSON contains arrays `thresholds` and `success_rates` of equal length and a numeric `variance`; a quick sanity check confirms that variance > 0 when thresholds differ.

- [ ] T016 **Generate the comprehensive statistical report `outputs/statistical_report.json`** conforming to `contracts/statistical_report.schema.yaml`.  
  **Verification** – JSON validates against the schema and includes McNemar test results, observed effect size, and the full sensitivity‑analysis data.

---

## Phase 6 – End‑to‑end reproducibility check

- [ ] T017 **Implement an integration test `tests/integration/test_full_pipeline.py`** that executes, in order, the scripts from T008 → T010 → T012 → T013 → T014 → T015 (using a fixed random seed).  
  - The test asserts that every expected artifact (`outputs/power_analysis.json`, `data/processed/triples_v1.parquet`, `outputs/distilled_t5/`, `outputs/evaluation_results.json`, `outputs/ablation_report.md`, `outputs/sensitivity_report.json`, `outputs/statistical_report.json`) exists and passes its respective JSON‑schema validation.  
  **Path**: `code/tests/integration/test_full_pipeline.py`  
  **Verification** – `pytest -q` exits with 0 tests failed; CI reports “All integration checks passed”.

---

## Phase 7 – Documentation & hand‑off

- [ ] T018 **Update `README.md` (at the repository root)** to include:  
  * Installation instructions (`pip install -r code/requirements.txt`).  
  * CLI usage examples for each script (`download_mobileforge.py`, `extraction.py`, `train_distilled.py`, `eval_pipeline.py`, `ablation_pipeline.py`, `sensitivity_sweep.py`).  
  * Description of the final deliverables (`outputs/evaluation_results.json`, `outputs/ablation_report.md`, `outputs/sensitivity_report.json`, `outputs/statistical_report.json`).  
  * Reference to the architecture diagram.  
  * Automated verification step: run `markdownlint-cli` and assert zero warnings.  
  **Verification** – README renders on GitHub and passes markdown‑lint CI.

- [ ] T019 **Add a placeholder architecture diagram `docs/architecture.png`** that visualises the data flow: Raw logs → Extraction → Processed triples → T5 training → Distilled model & TinyLlama baseline → Emulator → Paired results → McNemar test → Sensitivity/Ablation reports.  
  **Verification** – file exists; the README links to it.

- [ ] T020 **Create `quickstart.md`** with step‑by‑step commands to run the full pipeline on a fresh clone, mirroring the integration test flow.  
  **Verification** – quickstart renders correctly and the commands execute without errors on a clean runner.

- [ ] T021 **Generate a traceability manifest** that maps every figure, statistic, and interpretation in the final paper to the exact data row and code block that produced it.  
  - Writes `outputs/traceability_manifest.json` conforming to a new schema `contracts/traceability.schema.yaml`.  
  - The manifest is reviewed by the verification stage to ensure each entry has a single source.  
  **Verification** – CI runs a schema validation on `outputs/traceability_manifest.json` and checks that every key referenced in the paper appears exactly once.

- [ ] T022 **Run the Reference‑Validator Agent** to verify all citations used in `spec.md`, `plan.md`, and `README.md`.  
  - Executes the platform‑provided validator and writes a report `outputs/reference_validation.json`.  
  - CI fails if any citation is marked unreachable or mismatched.  
  **Verification** – validator report exists and contains no errors.

---

## Phase 8 – Additional reproducibility support

- [ ] T023 **Record the random seed used by every major script** (`extraction.py`, `train_distilled.py`, `eval_pipeline.py`, `ablation_pipeline.py`) in their respective log files (`outputs/extraction_log.json`, `outputs/training_log.json`, `outputs/evaluation_log.json`, `outputs/ablation_log.json`).  
  **Verification** – each log JSON contains a `"seed"` field matching the value in `outputs/reproducibility_meta.json`.

---

### Dependency summary

| Task | Depends on |
|------|------------|
| T001‑T004 | – (bootstrap) |
| T005‑T007 | T001‑T004 |
| T008 | T001‑T004 |
| T009 | T008 |
| T010 | T009 |
| T011 | T010 + T009 |
| T012 | T011 |
| T013 | T012 |
| T014 | T013 |
| T015 | T013 |
| T016 | T015 |
| T017 | T008‑T015 (full pipeline) |
| T018‑T020 | T013‑T016 (deliverables) |
| T021 | T016 (uses final statistical outputs) |
| T022 | All documentation artifacts |
| T023 | T010, T012, T013, T014 (adds logging) |

All tasks respect the data‑flow ordering required by the specification, stay within the CPU‑only compute budget, and produce real, schema‑validated artifacts ready for statistical verification.  