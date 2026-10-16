# Tasks: MobileForge Logic Distillation – CPU‑tractable Reasoning Model

**Project root**: `projects/PROJ-930-llmxive-follow-up-extending-mobileforge`

---

## Phase 1 – Project bootstrap (infrastructure only)

- [X] T001 [P] Create the full directory tree required for the study.  
  *Creates* `projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/{data/raw,data/processed,data/evaluation,models,utils,tests/unit,tests/integration}` and `projects/PROJ-930-llmxive-follow-up-extending-mobileforge/state/`.  
  **Verification** – after running the task, `tree` (or equivalent) shows all listed directories; CI checks that each path exists.

- [ ] T002 [P] Write a pinned `requirements.txt` (under `code/`) containing exact versions for all scientific packages required by the specification:  
  ```
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
  **Verification** – file is non‑empty, contains the `torch` line, and passes `pip install -r requirements.txt` in the CI environment.

- [X] T003 [P] Configure linting and formatting tools.  
  *Creates* `pyproject.toml` (project‑wide Black configuration) and `.ruff.toml` (Ruff rules) in the repository root.  
  **Verification** – both files exist and contain a `[tool.black]` section with `line-length = 88` and a `[tool.ruff]` section with `select = ["E", "F", "W"]`.

- [ ] T004 [P] Initialise the reproducibility state directory.  
  *Creates* `state/artifact_hashes.json` (initially `{}`) and a placeholder `data/checksums.json` (also `{}`) to satisfy SC‑III.  
  **Verification** – both JSON files exist, are valid JSON, and contain an empty object.

---

## Phase 2 – Core utilities (foundation for all user stories)

- [X] T005 [P] Implement `utils/emulator.py` with the exact public interface required by the evaluation stage:  
  - Functions: `launch_emulator()`, `send_action(action_seq)`, `check_crash()`, `get_screenshot()`.  
  - Error codes (constants): `EMU_CRASH`, `EMU_TIMEOUT`, `EMU_NOT_FOUND`.  
  - All functions raise clear exceptions on failure; no silent fall‑backs.  
  **Path**: `code/utils/emulator.py`  
  **Verification** – `python -c "import utils.emulator as e; assert hasattr(e, 'launch_emulator')"` runs without import errors; unit‑test scaffold is present (see T006).

- [X] T006 [P] Implement `utils/metrics.py` providing two lightweight classes:  
  - `SuccessRate` with method `compute(success_flags: List[bool]) -> float`.  
  - `StepEfficiency` with method `compute(steps_taken: List[int], optimal_steps: List[int]) -> float`.  
  **Path**: `code/utils/metrics.py`  
  **Verification** – both classes importable and methods return values in the documented ranges (0‑1 for success rate, ≥0 for efficiency).

- [ ] T007 [P] Implement `utils/power_analysis.py` that performs the a‑priori McNemar power calculation (target Power = 0.8, effect size h = 0.2, α = 0.05, baseline p₀ = 0.5).
  - Uses `statsmodels.stats.power.GofChisquarePower`.  
  - Writes the result to `state/validated_n.json` matching `contracts/power_analysis.schema.yaml`.  
  - Exits with a clear error if any data‑extraction artifact already exists (enforces the “before extraction” rule).  
  **Path**: `code/utils/power_analysis.py`  
  **Verification** – after execution, `state/validated_n.json` exists, contains an integer `n_required` ≥ 1 and the full parameter block; CI validates against the JSON schema.

---

## Phase 3 – Data pipeline (US‑1)

- [ ] T008 [P] Implement `data/raw/download_mobileforge.py` that fetches the official MobileForge logs via `datasets.load_dataset("mobileforge")`.  
  - The script writes the raw files under `data/raw/` and verifies SHA‑256 against entries in `data/checksums.json`.  
  - On any network or checksum failure the script raises an exception (no synthetic fallback).  
  **Path**: `code/data/raw/download_mobileforge.py`  
  **Verification** – script returns exit code 0 only when the dataset is present and checksum matches; otherwise CI records a failure.

- [ ] T017 [P] Validate the raw ExtractionDataset file (`data/raw/...`) against `contracts/dataset.schema.yaml`.  
  **Verification** – schema validation passes; CI runs a `jsonschema` check and fails if the raw data does not conform.

- [ ] T009 [P] Implement `utils/extraction.py` that:  
  1. Loads the raw logs produced by T008.  
  2. Filters for `trajectory_status == "failed_then_success"` and discards any `corrective_hint` containing coordinate patterns (`\[\d+,\d+\]`).  
  3. Reads `state/validated_n.json` to obtain the required sample size **N**; aborts with a clear error if `valid_n` is missing or if the number of valid triples < N.  
  4. Writes the filtered dataset to `data/processed/triples_v1.parquet` (schema `contracts/extraction_dataset.schema.yaml`).  
  5. Emits `state/extraction_stats.json` with `{ "valid_count": <int>, "status": "PASS"|"FAIL" }`.  
  **Path**: `code/utils/extraction.py`  
  **Verification** – parquet file exists, schema validation passes, and `extraction_stats.json` reports `"PASS"` with `valid_count ≥ N`.

---

## Phase 4 – Model training (US‑2)

- [ ] T018 [P] Validate the processed training parquet (`data/processed/*.parquet`) against `contracts/training_input.schema.yaml`.  
  **Verification** – schema validation succeeds; CI asserts JSON‑schema compliance before training begins.

- [ ] T010 [P] Implement `models/train_distilled.py` that trains a T5‑small encoder‑decoder model on the processed triples:  
  - Enforces `device="cpu"`; aborts immediately if `torch.cuda.is_available()` is true (SC‑VIII).  
  - Uses a hard timeout (`signal.alarm(6*60*60)`) to guarantee training ≤ 6 h; on timeout exits with message *“Training Timeout: Exceeded 6 h”*.  
  - Batch size ≤ 8, gradient accumulation to stay < 7 GB RAM.  
  - Early‑stopping on validation loss (patience = 1).  
  - Saves the final model weights and config to `models/distilled_t5/` and records its SHA‑256 in `state/artifact_hashes.json`.  
  **Path**: `code/models/train_distilled.py`  
  **Verification** – after a successful run the directory `models/distilled_t5/` contains `pytorch_model.bin` and `config.json`; the runtime log contains “Training completed in XhYm” with X ≤ 6.

---

## Phase 5 – Evaluation & statistical validation (US‑3)

- [ ] T011 [P] Implement the **evaluation pipeline** `models/eval_pipeline.py` that performs the full paired comparison:  
  1. Reads `state/validated_n.json` to obtain **N**.  
  2. Loads the AndroidWorld benchmark via `datasets.load_dataset("androidworld")`; aborts if the dataset contains fewer than N unique tasks.  
  3. Writes the selected task IDs to `data/evaluation/tasks.json`.  
  4. For each task ID, runs the distilled T5 model **and** the TinyLlama baseline on the *exact same* UI state and hint (using `utils.emulator` to execute the generated action sequence).  
  5. Records binary success/failure and step counts for both models in `data/results/paired_results.csv`.  
  6. Constructs the 2 × 2 contingency table, runs a one‑tailed McNemar test (`scipy.stats.mcnemar` with `exact=True` when appropriate), and writes `state/evaluation_results.json` conforming to `contracts/evaluation.schema.yaml`.  
  **Path**: `code/models/eval_pipeline.py`  
  **Verification** – the JSON file contains `statistical_test.test_type == "McNemar"`, a numeric `p_value`, and `significant` is true only when `p_value < 0.05`. All task IDs appear in `paired_results.csv`.

- [ ] T012 [P] Implement the **ablation pipeline** `models/ablation_pipeline.py` that repeats step 4 of T011 but replaces every `Corrective_Hint` with the literal string `"retry"`.  
  - Writes per‑task binary outcomes to `data/results/ablation_results.json`.  
  - Generates a human‑readable markdown report `state/ablation_report.md` summarizing success‑rate differences between the hint‑condition and the generic‑retry condition, and includes a McNemar‑style p‑value (one‑tailed).  
  **Path**: `code/models/ablation_pipeline.py`  
  **Verification** – the markdown report exists, contains a table with both success rates, and a p‑value ≤ 1.0; CI validates the JSON against `contracts/evaluation.schema.yaml` (the ablation schema is a subset).

- [ ] T013 [P] Implement the **sensitivity‑sweep** script `models/sensitivity_sweep.py` that:  
  - Loads `data/results/paired_results.csv`.  
  - For each Levenshtein‑distance threshold in `{0, 1, 2, 3}` recomputes binary success (action sequence considered successful if edit distance ≤ threshold).  
  - Calculates the success‑rate for both models at every threshold, computes variance across thresholds, and writes `state/sensitivity_report.json` matching the `sensitivity_report` section of `contracts/evaluation.schema.yaml`.  
  **Path**: `code/models/sensitivity_sweep.py`  
  **Verification** – JSON contains arrays `thresholds` and `success_rates` of equal length and a numeric `variance`; a quick sanity check confirms that variance > 0 when thresholds differ.

- [ ] T019 [P] Generate the comprehensive statistical report `state/statistical_report.json` conforming to `contracts/statistical_report.schema.yaml`.  
  **Verification** – JSON validates against the schema and includes McNemar test results, observed effect size, and the full sensitivity analysis data.

---

## Phase 6 – End‑to‑end reproducibility check

- [ ] T014 Implement an integration test `tests/integration/test_full_pipeline.py` that executes, in order, the scripts from T008 → T009 → T010 → T011 → T012 → T013 (using a small deterministic seed).  
  - The test asserts that every expected artifact (`state/validated_n.json`, `data/processed/triples_v1.parquet`, `models/distilled_t5/`, `state/evaluation_results.json`, `state/ablation_report.md`, `state/sensitivity_report.json`) exists and passes its respective JSON‑schema validation.  
  **Path**: `code/tests/integration/test_full_pipeline.py`  
  **Verification** – `pytest -q` exits with 0 tests failed; CI reports “All integration checks passed”.

---

## Phase 7 – Documentation & hand‑off

- [ ] T015 Update `README.md` (at the repository root) to include:  
  * Installation instructions (`pip install -r requirements.txt`).  
  * CLI usage examples for each script (`download_mobileforge.py`, `extraction.py`, `train_distilled.py`, `eval_pipeline.py`, `ablation_pipeline.py`, `sensitivity_sweep.py`).  
  * Description of the final deliverables (`state/evaluation_results.json`, `state/ablation_report.md`, `state/sensitivity_report.json`, `state/statistical_report.json`).  
  * Reference to the architecture diagram.  
  **Verification** – README renders on GitHub and contains all listed sections, satisfying SC‑001 reproducibility documentation.

- [ ] T016 Add a placeholder architecture diagram `docs/architecture.png` that visualises the data flow: Raw logs → Extraction → Processed triples → T5 training → Distilled model & TinyLlama baseline → Emulator → Paired results → McNemar test → Sensitivity/Ablation reports.  
  **Verification** – file exists; the README links to it.

- [ ] T020 Create `quickstart.md` with step‑by‑step commands to run the full pipeline on a fresh clone, mirroring the integration test flow.  
  **Verification** – quickstart renders correctly and the commands execute without errors.

### Dependency summary

| Task | Depends on |
|------|------------|
| T001‑T004 | – (bootstrap) |
| T005‑T007 | T001‑T004 |
| T008 | T001‑T004 |
| T017 | T008 |
| T009 | T008 + T007 |
| T018 | T009 |
| T010 | T018 |
| T011 | T010 + T009 |
| T012 | T011 |
| T013 | T011 |
| T019 | T013 |
| T014 | T008‑T013 (full pipeline) |
| T015 | T011‑T013 (deliverables) |
| T016 | T015 |
| T020 | T014 (mirrors integration test) |

All tasks respect the data‑flow ordering required by the specification, stay within the CPU‑only compute budget, and produce real, schema‑validated artifacts ready for statistical verification.
