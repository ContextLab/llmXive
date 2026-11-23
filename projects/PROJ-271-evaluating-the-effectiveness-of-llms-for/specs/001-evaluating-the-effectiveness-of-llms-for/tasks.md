# Tasks: Evaluating the Effectiveness of LLMs for Detecting Code Smells  

**Input**: The active `spec.md`, `plan.md`, original research idea, existing artifacts, and any reviewer feedback.  

---  

## Phase 1 – Project Initialization & Shared Infrastructure  

*These tasks must be completed before any scientific work begins.*

- [X] T001a [P] Initialize project directory structure (`projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/contract/`).  
  *Verification*: After execution, each listed directory exists and is writable.  

- [ ] T001b Create a `.flake8` configuration file in `code/` with the exact required settings:  

  ```text
  [flake8]
  max-line-length = 88
  ignore = E203,W503
  ```  

  *Verification*: The file exists, is readable, and contains both settings exactly as shown.  

- [ ] T001c Create `pyproject.toml` in `code/` with Black settings (`line-length = 88`, `target-version = py311`).  

  ```toml
  [tool.black]
  line-length = 88
  target-version = ['py311']
  ```  

  *Verification*: The file exists and includes the `[tool.black]` section with the exact `line-length` value.  

- [X] T002 Add `requirements.txt` containing `datasets pandas radon pylint sentence-transformers llama-cpp-python scikit-learn statsmodels numpy psutil`.  

  *Verification*: The file exists and each dependency appears on its own line matching the list above.  

## Phase 2 – Core Foundations (must be complete before any user‑story work)  

- [ ] T003 [P] Verify the HuggingFace dataset URL for `codeparrot/github-code` is reachable, download a small test shard, compute its checksum, and record it in `data/checksums.txt`. Abort if verification fails.   <!-- FAILED-IN-EXECUTION: code/verify_dataset.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_dataset.py exit=1 -->
  *Verification*: Log entry confirms successful URL check, checksum matches, and `data/checksums.txt` is written.  

- [ ] T004 [P] Create `code/config.py` defining paths (`data/`, `results/`), random seed (`42`), and batch‑size constants (`LLM_BATCH_SIZE = 10`).  
  *Verification*: Importing `code.config` yields the expected constants; a unit test asserts their values.  

- [ ] T005 [P] Add `code/__init__.py` and ensure directory layout matches `data/raw`, `data/processed`, `results`.  
  *Verification*: `code/__init__.py` exists and a script confirms the required sub‑directories are present.  

- [ ] T006a [P] Configure logging in `code/config.py` (format, file handler, level).  
  *Verification*: Running a test log entry creates `logs/run.log` with the correct format and level.  

- [ ] T006b [P] Implement `code/monitoring.py` that records RAM, CPU, and elapsed time per batch using `psutil`; writes to `results/resource_metrics.json`.  
  *Verification*: After a dummy batch, `results/resource_metrics.json` contains an entry with `peak_ram_gb`, `cpu_percent`, and `elapsed_seconds`.  

## Phase 3 – User Story 1: Automated Data Pipeline & Static‑Analysis Baseline (Priority P1)  

- [ ] T007 [US1][P] Sample **exactly 800** Python functions from the HuggingFace dataset `codeparrot/github-code` using `datasets.load_dataset("codeparrot/github-code", split="train", streaming=True)` with `seed=42`. Write the sampled functions to `data/raw/sample_functions.jsonl` (one JSON object per line, containing at least `id` and `source_code`).  
  *Verification*: File exists, line count is 800, and a log entry reports “Sampled 800 functions”.  

- [ ] T008 [US1] For each sampled function, compute structural metrics **LOC**, **cyclomatic complexity**, and **nesting depth** using the `radon` library. Store intermediate results in `data/processed/structural_metrics.jsonl` (one JSON object per function).  
  *Verification*: Randomly inspect 5 entries; each contains integer fields `loc`, `cyclomatic_complexity`, `nesting_depth` that match radon’s CLI output for the same code.  

- [ ] T009 [US1] Run **Pylint** on every sampled function, capture raw error codes, and store them in `data/processed/pylint_outputs.jsonl`.  
  *Verification*: Each JSON line includes a list field `static_labels`; the list may be empty but is always present.  

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

  *Verification*: The file is valid JSON and validates against a simple schema (object of string→string).  

- [ ] T011 [US1] Normalize raw Pylint codes to canonical smell names using `contracts/smell_mapping.json`. For any unmapped code, label it `"Unknown"` and emit a warning to `logs/normalization_warnings.log`. Append both `static_labels` (raw codes) and `normalized_static_labels` (canonical names) to each function record in `data/processed/static_normalized.jsonl`.  
  *Verification*: Sample 10 records; every entry’s `normalized_static_labels` contains only values from the mapping or `"Unknown"`.  

- [ ] T012 [US1] Write the final static baseline CSV **`data/static_baseline.csv`** with columns: `id`, `source_code`, `loc`, `cyclomatic_complexity`, `nesting_depth`, `static_labels` (JSON‑encoded list), `normalized_static_labels` (JSON‑encoded list).  
  *Verification*: The CSV contains exactly 800 rows and passes the `static_baseline.schema.yaml` contract test.  

- [ ] T013 [US1] Validate completeness: at least **95 %** of the 800 rows must have non‑null values for all required columns. Produce a summary JSON `results/static_baseline_validation.json` with fields `total_rows`, `valid_rows`, `percent_valid`.  
  *Verification*: `percent_valid` ≥ 95 and the JSON file is present.  

## Phase 4 – User Story 2: Semantic Feature Extraction & LLM Inference (Priority P2)  

- [ ] T014 [US2] Load the `sentence‑transformers/all‑MiniLM‑L6‑v2` model and compute a 384‑dimensional embedding for each function in `data/static_baseline.csv`. Store embeddings in `data/processed/embeddings.jsonl` (each line adds a field `semantic_vector`).  
  *Verification*: Randomly inspect 5 entries; each `semantic_vector` is a list of 384 floats.  

- [ ] T015 [US2] Verify the presence of the **4‑bit quantized** `CodeLlama‑7B‑Instruct‑GGUF` model file `code_llama_7b_q4_0.gguf` in `models/`. Load it with `llama_cpp.Llama` using `device='cpu'`. Raise an explicit error if the model’s quantization metadata does not contain `q4_0`.  
  *Verification*: After loading, a log entry prints `Quantization: q4_0`.  

- [ ] T016 [US2] Create `contracts/llm_prompt.txt` containing the exact prompt:  

  ```
  Identify any code smells present in the following Python function and output a JSON array of smell names. Do not include any additional text.
  ```  

  *Verification*: A unit test reads the file and asserts its content matches the string above exactly.  

- [ ] T017 [US2] Implement batched LLM inference (**batch size ≤ 10**) over the sampled functions:  

  1. Truncate functions that exceed the model’s context window, preserving the function header.  
  2. Feed the prompt from `contracts/llm_prompt.txt` followed by the (possibly truncated) function source.  
  3. Parse the LLM output; on parse failure record `"Unparseable"` for that function and set `parse_status = "PARSE_ERROR"`.  
  4. Store results (`llm_labels`, `parse_status`, optional `llm_raw_output`) in `data/processed/semantic_results.jsonl`.  

  *Verification*: After processing, ≥ 90 % of rows have `parse_status = "SUCCESS"`; any failures are listed in `results/llm_parsing_errors.log`.  

- [ ] T018 [US2] Record per‑batch resource usage (peak RAM, CPU %, elapsed time) using `code/monitoring.py`; append each batch’s metrics to `results/resource_metrics.json`.  
  *Verification*: Every entry includes `batch_index`, `peak_ram_gb` (≤ 7), `cpu_percent`, `elapsed_seconds`.  

- [ ] T019 [US2] Produce a compliance verification file `results/compliance_verification.json` that flags any breach of the **≤ 7 GB RAM** or **≤ 6 h total runtime** constraints.  
  *Verification*: The JSON contains boolean fields `ram_ok` and `time_ok`; both are `true` when the pipeline finishes within limits.  

## Phase 5 – User Story 3: Comparative Statistical Analysis & Reporting (Priority P3)  

- [ ] T020 [US3] **Merge** the static baseline (`data/static_baseline.csv`), the embeddings (`data/processed/embeddings.jsonl`), and the LLM results (`data/processed/semantic_results.jsonl`) into a unified JSONLines file `data/merged_analysis.jsonl`. Each record must contain:  

  `id`, `source_code`, structural metrics, `static_labels`, `normalized_static_labels`, `semantic_vector`, `llm_labels`, and derived boolean flags `static_only`, `llm_only`, `both`.  

  *Verification*: Sample 5 merged records; all fields are present and the three flags are mutually exclusive and correctly computed.  

- [ ] T021 [US3] Validate merged dataset completeness: ≥ 95 % of the 800 functions must have non‑null values for **all** required fields (`semantic_vector`, `llm_labels`, structural metrics). Write a summary to `results/merged_validation.json`.  
  *Verification*: `percent_complete` ≥ 95 in the JSON report.  

- [ ] T022 [US3] Perform **McNemar’s test** for each smell category using the paired outcomes (static vs. LLM). Store p‑values in `results/statistical_significance.json` under the key `mcnemar_pvalues`. Apply Bonferroni correction across categories.  
  *Verification*: The JSON conforms to `statistical_report.schema.yaml`; every p‑value is a number in `[0,1]`.  

- [ ] T023 [US3] Compute **Variance Inflation Factor (VIF)** for predictors `loc`, `cyclomatic_complexity`, `nesting_depth`, and `semantic_mean` (mean of the 384‑dim embedding). Write VIF scores to `results/vif_scores.json`.  
  *Verification*: Any predictor with `VIF ≥ 5` is listed in `results/vif_report.md` with a warning.  

- [ ] T024 [US3] Fit **binary logistic regression** models to predict the two detection modes:  

  1. `static_only` ≈ structural + semantic predictors.  
  2. `llm_only` ≈ structural + semantic predictors.  

  Exclude any predictor flagged by VIF ≥ 5. Store coefficients in `results/logistic_regression.json` under keys `static_only` and `llm_only`. Include model diagnostics (`AIC`, `pseudo_R2`).  
  *Verification*: Each coefficient is numeric; the JSON validates against the statistical‑report schema.  

- [ ] T025 [US3] Conduct a **sensitivity analysis** sweeping LOC thresholds `{50, 100, 150}`. For each threshold compute false‑positive (`fp_rate`) and false‑negative (`fn_rate`) rates for static‑only detections **and** the `static_only_proportion`. Output an array of objects to `results/sensitivity_metrics.json` with schema `[{threshold:int, static_only_proportion:float, fp_rate:float, fn_rate:float}]`.  
  *Verification*: The file contains three entries (one per threshold) and all rates lie in `[0,1]`.  

- [ ] T032 [US3] Compute the **Pearson correlation** between each structural metric (`loc`, `cyclomatic_complexity`, `nesting_depth`) and the binary flag `static_only`. Store results in `results/structural_correlation.json` (fields: `metric`, `correlation_coefficient`, `p_value`).  
  *Verification*: At least one metric has `p_value ≤ 0.05`.  

- [ ] T026 [US3] Compute the **Pearson correlation** between the mean semantic embedding (average of the 384 dimensions) and the binary flag `llm_only`. Write `results/semantic_correlation.json` containing `correlation_coefficient`, `p_value`, `regression_coefficient` (from the logistic model), and `method`.  
  *Verification*: JSON fields are present and `p_value ≤ 0.05` for at least one correlation.  

- [ ] T027 [US3] Generate a **complementarity summary** `results/complementarity_report.md` that enumerates:  

  * Smells detected **only** by static analysis.  
  * Smells detected **only** by the LLM.  
  * Overlap (detected by both).  

  Include a brief interpretation of the overlap size and any notable patterns.  
  *Verification*: Manual inspection confirms the three lists are non‑empty (unless the data dictate otherwise).  

- [ ] T028 [US3] Validate all result artifacts against their respective JSON/YAML schemas (`static_baseline.schema.yaml`, `statistical_report.schema.yaml`, etc.) using the contract tests in `tests/contract/`.  
  *Verification*: All contract tests exit with code 0.  

## Phase 6 – Additional Scientific Rigor (addresses reviewer epistemology comment)

- [ ] T033 [US3] Perform a **manual sanity‑check** on a random sample of 20 functions where the LLM reported a smell that static analysis did not (i.e., `llm_only = true`). A domain‑expert reviewer reads each function and the LLM’s reported smell, then records a binary judgment (`ground_truth = true/false`). Summarize the proportion of LLM‑only detections that appear plausible in `results/manual_llm_validation.json`.  
  *Verification*: The JSON contains fields `sample_size`, `plausible_count`, `plausible_rate`; the rate is reported in the final paper methods section.  

## Phase 7 – Polish, Reproducibility & Paper Handoff  

- [ ] T029 [P] Update `README.md` with a concise CLI overview, environment‑setup instructions, and direct links to the main result files.  
- [ ] T030 [P] Create `quickstart.md` that walks a new user through: (1) installing dependencies, (2) running the full pipeline (`python -m code.main`), and (3) locating the final statistical report.  
- [ ] T031 [P] Add a reproducibility metadata file `results/run_metadata.json` capturing: `pip freeze` snapshot, dataset version/commit hash, random seed, start/end timestamps, and git commit SHA.  
  *Verification*: The file is automatically generated at the end of `code/main.py` and contains all required keys.  

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
| FR‑007 – Logistic regression (binary) | T023, T024 |
| FR‑008 – Resource usage logging | T006b, T018, T019 |
| FR‑009 – Sensitivity analysis | T025 |
| FR‑010 – VIF calculation & handling | T023 |
| SC‑001 – Correlation (structural ↔ static‑only) | T032 |
| SC‑002 – Correlation (semantic ↔ LLM‑only) | T026 |
| SC‑003 – McNemar significance | T022 |
| SC‑004 – Runtime & RAM compliance | T019 |
| SC‑05 – ≥ 95 % completeness | T013, T021, T028 |
| Reviewer epistemology concern | T033 |

---  

*All unchecked tasks are pending implementation. Once a task is completed, mark the checkbox `[X]` and ensure the verification step passes.*  