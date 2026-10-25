# Tasks: Cognitive‑load comparison of Structured Harness vs. Chat Interface for Figure Editing  

**Inputs**: `spec.md`, `plan.md`, existing source files under `src/`, contract schemas in `specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/`, and reviewer feedback.

The list follows the canonical `- [ ] T### [P?] [USx?] description …` format. Checked boxes indicate completed work that already satisfies the specification; unchecked boxes are pending implementation or revision. All tasks respect data‑flow ordering and the scientific requirements of the specification.

---

## Phase 0 – Environment setup  

- [ ] T000 [P] Create a reproducible Python environment, pin all dependency versions, set a global random seed, and verify SHA‑256 checksums for raw files.  
  - **Files**: `requirements.txt`, `src/utils/seeds.py`, `src/utils/checksums.py`, `data/checksums.txt`, `scripts/verify_env.sh`  
  - **Verification**:  
    1. Run `scripts/verify_env.sh`; it executes `pip install -r requirements.txt` and archives the install log to `data/env_evidence/pip_install.log`.  
    2. The script recomputes SHA‑256 for each file listed in `data/checksums.txt`, archives the output to `data/env_evidence/checksum_verify.log`, and prints “ALL CHECKSUMS MATCH” on success.  
    3. CI test `tests/env/test_verify_env.py` asserts exit code 0 and that the archived logs contain “Successfully installed” and the checksum match message.

## Phase 1 – Data curation, interfaces, and instrumentation  

- [ ] T001 [P] [US-1] Provide a lightweight pipeline entry point that prints help and version information, and document usage in `quickstart.md`.  
  - **Files**: `src/run_pipeline.py`, `quickstart.md`  
  - **Verification**: `python -m src.run_pipeline --help` exits 0 and displays usage; `python -m src.run_pipeline --version` prints a semantic version string.

- [ ] T002 [P] [US-1] Implement a **mandatory** download‑and‑curation script that fetches a **verified** subset of exactly 50 failed figures from CrafterBench; if the verified source is unavailable the script raises a fatal error and aborts the pipeline (fulfilling FR‑001).  
  - **File**: `src/curators/curate_failed_figures.py`  
  - **Verification**: Running the script with `--num 50` succeeds only when `CRAFTERBENCH_URL` points to a verified open‑source location; otherwise it exits 1 with the message “Verified dataset source not available”. Unit test `tests/curators/test_curate_failed_figures.py` checks both paths.

- [ ] T003 [P] [US-1] Deploy two FastAPI editing endpoints (`/structured/edit` and `/chat/edit`) and a session‑initialization endpoint that (a) **counterbalances** interface order across participants, (b) enforces a **minimum 5‑minute wash‑out** interval between interface blocks (FR‑010), and (c) implements the UI/UX for collecting the participant's self-reported **expertise level** (novice, intermediate, expert) and the **NASA-TLX** questionnaire rating (0-100) after each task.  
  - **Files**: `src/interfaces/structured_harness.py`, `src/interfaces/chat_interface.py`, `src/interfaces/session.py`, `tests/interfaces/test_session.py`  
  - **Verification**: `pytest -q tests/interfaces/test_session.py` validates that (i) the `interface_order` list is balanced across a simulated cohort of 100 participants, (ii) a second block request before 5 minutes returns HTTP 429, and (iii) the `/init_session` response includes a field for expertise collection.

- [ ] T004 [P] [US-2] Implement millisecond‑precision interaction logging and expose it via a FastAPI route `/log_interaction`. The logger must record `subjective_load` (NASA‑TLX) and an optional `status` field (e.g., `"aborted"`).  
  - **Files**: `src/logger/interaction_logger.py`, `src/interfaces/logging_endpoint.py`, `tests/logger/test_logging_endpoint.py`  
  - **Verification**: Use FastAPI `TestClient` to submit a dummy edit; assert that the resulting line in `data/logs/interactions.jsonl` conforms to `interaction_log.schema.yaml` and contains the `subjective_load` field. Repeat the test with `status="aborted"` and assert the field is correctly recorded.

- [ ] T005 [P] [US-2] Implement dual‑success validation utilities (exact vector match = primary success, CLIP semantic similarity ≥ 0.95 = secondary pass) **and** add the missing `semantic_validation.schema.yaml` file so that generated records can be validated.  
  - **Files**: `src/validation/vector_match.py`, `src/validation/semantic_similarity.py`, `src/validation/run_validation.py`, `specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/semantic_validation.schema.yaml`, `tests/validation/test_dual_success.py`  
  - **Verification**: Unit tests cover three cases (exact match only, semantic‑only match, total failure) and use `jsonschema.validate` against the newly added schema; the CI step `pytest -q tests/validation/test_dual_success.py` must pass.

- [ ] T006 [P] [US-2] Execute the validation pipeline (`run_validation.py`) to produce raw `SemanticValidation` records for all completed tasks in the current dataset.  
  - **Files**: `src/validation/run_validation.py`, `data/validation/semantic_validation.jsonl`  
  - **Verification**: The script exits 0 and produces a JSONL file where each line is validated against `semantic_validation.schema.yaml`.

- [ ] T012 [P] [US-1] Execute the retention verification that checks after data collection that **≥ 28** of the recruited **≥ 32** participants have completed both interface blocks with at least one primary‑success trial each (SC‑004). The script must abort with an informative error if the criterion is not met.  
  - **Files**: `src/validation/retention_check.py`, `tests/validation/test_retention_check.py`  
  - **Verification**: Running the script on the synthetic dataset prints “Retention check passed: 32/32 participants meet criteria” and exits 0. The test feeds edge‑case synthetic logs (e.g., only 27 participants meeting the rule) and asserts that the script exits 1 with the correct error message.

- [ ] T007 [P] [US-2] Aggregate per‑task `SemanticValidation` records into a session‑aware file `data/results/semantic_validation_by_session.jsonl` **and** produce `data/results/effective_N_by_participant.jsonl` that records, for each participant, the count of valid (non‑aborted) tasks used in the analysis.  
  - **Files**: `src/analysis/aggregate_validation.py`, `data/results/semantic_validation_by_session.jsonl`, `data/results/effective_N_by_participant.jsonl`, `tests/analysis/test_aggregation.py`  
  - **Verification**: The aggregation script prints “Aggregation complete: X participants, Y valid tasks”. The test loads both JSONL files, checks that every record contains `session_id`, `task_id`, `overall_success`, and that the effective‑N file has an integer `effective_N` ≥ 1 for each participant.

- [ ] T008 [P] [US-3] Implement the statistical analysis script that (a) reads the session‑aware validation file, (b) **excludes** aborted tasks, (c) computes paired Wilcoxon signed‑rank tests for `time_to_success_ms`, `iteration_count`, and `subjective_load` (fallback to paired t‑test if Shapiro‑Wilk p > 0.05), (d) applies Bonferroni correction (α = 0.025 per metric), (e) reports rank‑biserial effect size *r* with 95 % bootstrap CI, and (f) fits a linear mixed‑effects model with `expertise_level` as a fixed covariate. Output must be `outputs/analysis_results.jsonl` conforming to `analysis_result.schema.yaml`.  
  - **Files**: `src/analysis/wilcoxon_analysis.py`, `outputs/analysis_results.jsonl`, `tests/analysis/test_wilcoxon.py`  
  - **Verification**: Running the script on the synthetic dataset exits 0 and produces exactly three JSON objects (one per metric). The test loads the file, validates each object against the schema, and checks that `p_value_corrected` ≤ 1 and that `mixed_effects` fields are present (or null when not applicable).

- [ ] T009 [P] [US-3] Generate the final markdown report `outputs/report.md` that includes (1) mean/median tables per interface for each metric, (2) test statistics, corrected p‑values, effect sizes, and 95 % CIs, (3) success‑rate breakdowns (vector‑match vs. semantic‑pass), (4) average NASA‑TLX scores per interface, and (5) a statement that the current numbers stem from deterministic synthetic data pending real‑world collection.  
  - **Files**: `src/report/generate_report.py`, `outputs/report.md`, `tests/report/test_report_contents.py`  
  - **Verification**: The test runs the script, parses `report.md` with regexes, and asserts that each required section header appears and that the numeric values match those in `analysis_results.jsonl`.

- [ ] T010 [P] Run comprehensive contract validation, runtime tracking, and reference‑validator checks.  
  - **Files**: `tests/contract/test_contracts.py`, `src/utils/runtime_tracker.py`, `src/validation/reference_validator.py`, `data/checksums.txt`  
  - **Verification**:  
    1. `pytest -q tests/contract/test_contracts.py` must pass, confirming that all JSON‑Lines artifacts (`interactions.jsonl`, `semantic_validation_by_session.jsonl`, `analysis_results.jsonl`) satisfy their schemas.  
    2. `runtime_tracker.py` writes `data/checksums.txt` entry `pipeline_runtime_seconds: <value>`; a test asserts the value ≤ 21600 (6 h).  
    3. `reference_validator.py` exits 0 only if every citation in `spec.md`, `plan.md`, and `report.md` is verified; CI fails otherwise.

- [ ] T011 [P] Write the methods/results markdown (`outputs/methods.md`) that references the exact pipeline steps, data sources, and synthetic scope, and create a paper‑stage handoff manifest (`paper/handoff.yaml`) enumerating all artifacts required for manuscript preparation.  
  - **Files**: `outputs/methods.md`, `paper/handoff.yaml`, `tests/docs/test_methods_and_handoff.py`  
  - **Verification**: The test renders `methods.md` and checks for sections “Data Curation”, “Interface Design”, “Logging”, “Validation”, and “Statistical Analysis”. It also loads `paper/handoff.yaml` and asserts that keys include `outputs/report.md`, `data/logs/interactions.jsonl`, `data/results/semantic_validation_by_session.jsonl`, and the source code directory.

---  

*All tasks respect the Constitution Principles, use only real data sources (or deterministic synthetic stand‑ins for CI), and write outputs exclusively under the `data/`, `outputs/`, `src/`, and `paper/` directories.*