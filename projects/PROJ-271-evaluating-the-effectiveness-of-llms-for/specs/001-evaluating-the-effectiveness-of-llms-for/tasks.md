# Tasks: Evaluating the Effectiveness of LLMs for Detecting Code Smells

**Input**: Design documents from `specs/001-evaluating-the-effectiveness-of-llms-for/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

## Phase 1 – Project Initialization & Shared Infrastructure  

*These tasks are already completed and verified.*

- [X] T001a [P] Initialize project directory structure (`projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/contract/`).  
- [ ] T001b [P] Create `.flake8` in `code/` with `max-line-length = 88`, ignore `E203,W503`.  
- [X] T001c [P] Create `pyproject.toml` in `code/` with Black settings (`line-length = 88`, `target-version = py311`).  
- [X] T002  [P] Add `requirements.txt` containing `datasets pandas radon pylint sentence-transformers llama-cpp-python scikit-learn statsmodels numpy psutil`.  

## Phase 2 – Core Foundations (must be complete before any user‑story work)  

*These tasks are already completed and verified.*

- [X] T004 [P] Create `code/config.py` defining paths (`data/`, `results/`), random seed (`42`), and batch‑size constants (`LLM_BATCH_SIZE = 10`).  
- [X] T005 [P] Add `code/__init__.py` and ensure directory layout matches `data/raw`, `data/processed`, `results`.  
- [X] T006a Configure logging in `code/config.py` (format, file handler, level).  
- [X] T006b Implement `code/monitoring.py` that records RAM, CPU, and elapsed time per batch using `psutil`; writes to `results/resource_metrics.json`.  

## Phase 3 – User Story 1: Automated Data Pipeline & Static‑Analysis Baseline (Priority P1)

- [ ] T007 [US1] Sample **exactly 800** Python functions from the HuggingFace `codeparrot/github-code` dataset using `datasets.load_dataset(..., streaming=True)` with `seed=42`; write the raw sampled functions to `data/raw/sample_functions.jsonl`.   <!-- FAILED-IN-EXECUTION: code/sample_functions.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/sample_functions.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/sample_functions.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/sample_functions.py exit=1 -->
  - *Verification*: Log the number of sampled functions; abort with an explicit error if the count is < 800.  

- [ ] T008 [US1] For each sampled function, compute structural metrics **LOC**, **cyclomatic complexity**, and **nesting depth** using the `radon` library; store intermediate results in `data/processed/structural_metrics.jsonl`.  
  - *Verification*: Spot‑check 5 random entries to confirm metric values match `radon` output.  

- [ ] T009 [US1] Run **Pylint** on every sampled function; capture raw error codes; store in `data/processed/pylint_outputs.jsonl`.  
  - *Verification*: Ensure each entry contains a non‑empty list of Pylint codes (or an empty list if none).  

- [ ] T010 [US1] Create `contracts/smell_mapping.json` that maps the five required Pylint codes to canonical smell names:  
  ```json
  {
    "C0111": "Missing Docstring",
    "R0913": "Too Many Arguments",
    "C0103": "Invalid Name",
    "R0904": "Too Many Public Methods",
    "W0613": "Unused Argument"
  }
  ```  
  - *Verification*: JSON validates against the schema (no extra fields).  

- [ ] T011 [US1] Normalize raw Pylint codes to canonical smell names using `contracts/smell_mapping.json`; for any unmapped code, label as `"Unknown"` and log a warning. Append the normalized list as `static_labels` **and** `normalized_static_labels` to each function record.  
  - *Verification*: Sample 10 records and confirm that every code is either in the mapping or marked `"Unknown"`.  

- [ ] T012 [US1] Write the final static baseline CSV **`data/static_baseline.csv`** with columns: `id`, `source_code`, `loc`, `cyclomatic_complexity`, `nesting_depth`, `static_labels` (JSON‑encoded list), **`normalized_static_labels`** (JSON‑encoded list).  
  - *Verification*: The file contains **800 rows**; passes the `static_baseline.schema.yaml` contract test.  

- [ ] T013 [US1] Validate completeness: at least **95 %** of the 800 rows must have non‑null values for all required columns. Write a summary to `results/static_baseline_validation.json`.  
  - *Verification*: The JSON contains fields `valid_rows`, `total_rows`, `percent_valid` and `percent_valid ≥ 95`.  

## Phase 4 – User Story 2: Semantic Feature Extraction & LLM Inference (Priority P2)

- [ ] T014 [US2] Load the **`sentence‑transformers/all‑MiniLM‑L6‑v2`** model and compute a 384‑dimensional embedding for each function in `data/static_baseline.csv`; store embeddings in `data/processed/embeddings.jsonl`.  
  - *Verification*: Randomly inspect 5 entries; each must contain a list of 384 floats.  

- [ ] T015 [US2] Verify the presence of the **4‑bit quantized** `CodeLlama‑7B‑Instruct‑GGUF` model file (`code_llama_7b_q4_0.gguf`). Load it with `llama‑cpp‑python` on `device="cpu"`; raise an explicit error if the model is not 4‑bit.  
  - *Verification*: Print `model.info.quantization` after load; it must contain `q4_0`.  

- [ ] T016 [US2] Create `contracts/llm_prompt.txt` containing the exact prompt:  
  ```
  Identify any code smells present in the following Python function and output a JSON array of smell names. Do not include any additional text.
  ```  
  - *Verification*: Unit test confirms the file content matches the string used in inference.  

- [ ] T017 [US2] Implement batched LLM inference (**batch size ≤ 10**) over the sampled functions:  
  1. Truncate functions that exceed the model’s context window, preserving the function header.  
  2. Run the prompt from `contracts/llm_prompt.txt`.  
  3. Parse the LLM output; on parse failure record `"Unparseable"` for that function.  
  Store results (`llm_labels` and `parse_status`) in `data/processed/semantic_results.jsonl`.  
  - *Verification*: After processing, at least 90 % of rows have `parse_status = "SUCCESS"`; any `"UNPARSEABLE"` entries are logged in `results/llm_parsing_errors.log`.  

- [ ] T018 [US2] Record per‑batch resource usage (peak RAM, CPU %, elapsed time) using `code/monitoring.py`; append to `results/resource_metrics.json`.  
  - *Verification*: The JSON contains an entry for each batch; all `peak_ram_gb ≤ 7`.  

- [ ] T019 [US2] Produce a compliance verification file `results/compliance_verification.json` that flags any breach of the **≤ 7 GB RAM** or **≤ 6 h total runtime** constraints.  
  - *Verification*: The file contains fields `ram_ok` and `time_ok` (both boolean).  

## Phase 5 – User Story 3: Comparative Statistical Analysis & Reporting (Priority P3)

- [ ] T020 [US3] **Merge** the static baseline (`data/static_baseline.csv`), the embeddings (`data/processed/embeddings.jsonl`), and the semantic results (`data/processed/semantic_results.jsonl`) into a unified JSONLines file **`data/merged_analysis.jsonl`**. Each record must contain: `id`, `source_code`, structural metrics, `static_labels`, `normalized_static_labels`, `semantic_vector`, `llm_labels`, and derived boolean flags `static_only`, `llm_only`, `both`.  
  - *Verification*: Randomly sample 5 merged records; all fields present, flags correctly computed.  

- [ ] T021 [US3] Validate merged dataset completeness: ≥ 95 % of the 800 functions must have non‑null values for **all** required fields (`semantic_vector`, `llm_labels`, structural metrics). Write a summary to `results/merged_validation.json`.  
  - *Verification*: The JSON reports `percent_complete ≥ 95`.  

- [ ] T022 [US3] Perform **McNemar’s test** for each smell category using the paired outcomes (static vs. LLM). Store p‑values in `results/statistical_significance.json` under the key `mcnemar_pvalues`.  
  - *Verification*: The JSON conforms to `statistical_report.schema.yaml`; all p‑values are numbers in `[0,1]`.  

- [ ] T023 [US3] Compute **Variance Inflation Factor (VIF)** for predictors `loc`, `cyclomatic_complexity`, `nesting_depth`, and `semantic_mean` (mean of embedding dimensions). Write VIF scores to `results/vif_scores.json`.  
  - *Verification*: Any predictor with `VIF ≥ 5` is listed in `results/vif_report.md` with a warning.  

- [ ] T024 [US3] Fit a **single binary logistic regression** model to predict the detection mode (`llm_detected` vs. `static_detected`) using the retained predictors (after excluding any with `VIF ≥ 5`). Store coefficients in `results/logistic_regression.json` under key `detection_mode`.  
  - *Verification*: Coefficients are numeric; model summary includes `AIC` and `pseudo_R2`.  

- [ ] T025 [US3] Conduct a **sensitivity analysis** sweeping structural LOC thresholds `{50, 100, 150}`. For each threshold compute **false‑positive** and **false‑negative** rates for static‑only detections; output an array of objects to `results/sensitivity_metrics.json` with schema `[{threshold:int, fp_rate:float, fn_rate:float}]`.  
  - *Verification*: The JSON contains three entries (one per threshold) and rates are in `[0,1]`.  

- [ ] T032 [US3] Compute the **Pearson correlation** between each structural metric (`loc`, `cyclomatic_complexity`, `nesting_depth`) and the binary flag `static_only`. Store results in `results/structural_correlation.json` (fields: `metric`, `correlation_coefficient`, `p_value`).  
  - *Verification*: All p‑values are ≤ 0.05 for at least one metric, demonstrating a significant relationship.  

- [ ] T026 [US3] Compute the **Pearson correlation** between the mean semantic embedding (average of the 384 dimensions) and the binary flag `llm_only`. Report Pearson’s r, p‑value, and compare to the logistic‑regression coefficient for the semantic predictor; write to `results/semantic_correlation.json`.  
  - *Verification*: The JSON contains fields `correlation_coefficient`, `p_value`, `regression_coefficient`, `method`.  

- [ ] T027 [US3] Generate a **complementarity summary** (`results/complementarity_report.md`) that enumerates:  
  - Smells detected **only** by static analysis.  
  - Smells detected **only** by the LLM.  
  - Overlap (both).  
  Include brief interpretation of the overlap size.  
  - *Verification*: Manual inspection confirms the three lists are non‑empty (unless data dictate otherwise).  

- [ ] T028 [US3] Validate all result artifacts against their respective JSON/YAML schemas (`static_baseline.schema.yaml`, `statistical_report.schema.yaml`, etc.) using contract tests located in `tests/contract/`.  
  - *Verification*: All contract tests pass (`exit code 0`).  

## Phase 6 – Polish, Reproducibility & Handoff  

- [ ] T029 [P] Update `README.md` with a concise CLI overview, environment‑setup instructions, and links to the main result files.  
- [ ] T030 [P] Create `quickstart.md` that walks a new user through: (1) installing dependencies, (2) running the full pipeline (`python -m code.main`), and (3) locating the final statistical report.  
- [ ] T031 [P] Add a reproducibility metadata file `results/run_metadata.json` capturing: `pip freeze` snapshot, dataset version/commit hash, random seed, and timestamps.  
  - *Verification*: The file is generated automatically at the end of `code/main.py` and contains the required fields.  

---

### Dependency Mapping (Specification → Tasks)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 – Sample 800 functions | T007 |
| FR‑002 – Structural metrics | T008 |
| FR‑003 – Pylint baseline & normalization | T009, T010, T011 |
| FR‑004 – Load 4‑bit CodeLlama on CPU | T015 |
| FR‑005 – Compute semantic embeddings | T014 |
| FR‑006 – McNemar’s test | T022 |
| FR‑007 – Logistic regression (single model) | T023, T024 |
| FR‑008 – Resource usage logging | T006b, T018, T019 |
| FR‑009 – Sensitivity analysis | T025 |
| FR‑010 – VIF calculation & handling | T023 |
| SC‑001 – Correlation (structural ↔ static‑only) | T032 |
| SC‑002 – Correlation (semantic ↔ LLM‑only) | T026 |
| SC‑003 – McNemar significance | T022 |
| SC‑004 – Runtime & RAM compliance | T019 |
| SC‑005 – ≥ 95 % completeness | T013, T021, T028 |

--- 

*All unchecked tasks are pending implementation. Once a task is completed, the checkbox should be marked `[X]` and the verification step confirmed.*  