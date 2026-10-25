# Tasks: Cognitive‑load comparison of Structured Harness vs. Chat Interface for Figure Editing  

**Inputs**: `spec.md`, `plan.md`, existing source files under `src/`, contract schemas in `specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/`, and reviewer feedback.  

The list follows the canonical `- [ ] T### [P?] [USx?] description …` format. Checked boxes indicate completed work that satisfies the specification; unchecked boxes are pending implementation or revision.

---

## Phase 0 – Environment setup  

- [X] T000 [US-?] Create a reproducible Python environment, pin all dependency versions, set a global random seed, and generate SHA‑256 checksums for raw data.  
  - **Files**: `requirements.txt`, `src/utils/seeds.py`, `src/utils/checksums.py`, `data/checksums.txt`  
  - **Verification**: `pip install -r requirements.txt` succeeds; `python -c "import src.utils.seeds; assert src.utils.seeds.SEED==42"` runs without error; `sha256sum` of each file matches entries in `data/checksums.txt`.

---

## Phase 1 – Data curation, interfaces, and instrumentation  

- [X] T001 [P] [US-1] Provide a lightweight pipeline entry point that prints help and version information, and documents usage in `quickstart.md`.  
  - **Files**: `src/run_pipeline.py`, `quickstart.md`  
  - **Verification**: `python -m src.run_pipeline --help` exits 0 and displays usage; `python -m src.run_pipeline --version` prints a semantic version string.

- [X] T002 [US-1] Implement a **mandatory** download and curation script that fetches a **verified** subset of exactly 50 failed figures from CrafterBench; if the verified source is unavailable the script raises a fatal error and aborts the pipeline (fulfilling FR‑001).  
  - **File**: `src/curators/curate_failed_figures.py`  
  - **Verification**: Running `python -m src.curators.curate_failed_figures --num 50` succeeds only when a verified URL is provided; otherwise it exits with a non‑zero status and an explicit “Verified dataset source not available” message.

- [X] T003 [P] [US-1] Deploy two FastAPI editing endpoints (`/edit` for structured harness, `/edit` for chat) and a session‑initialization endpoint that (a) randomizes and **counterbalances** interface order across participants, and (b) enforces a **10‑minute** wash‑out interval between the two interface blocks (as required by FR‑010).  
  - **Files**: `src/interfaces/structured_harness.py`, `src/interfaces/chat_interface.py`, `src/interfaces/session.py`, `tests/interfaces/test_interfaces.py`  
  - **Verification**: `pytest -q tests/interfaces/test_interfaces.py` passes; a simulated participant receives a JSON response from `/init_session` indicating `interface_order` is balanced, and a second call after the first block is rejected until a 10‑minute interval has elapsed (mocked time in tests).

- [X] T004 [US-2] Implement millisecond‑precision interaction logging that records start/end timestamps, iteration count, payload, response image path, and **NASA‑TLX score** after each task; aborted edits are logged with status `"aborted"`.  
  - **Files**: `src/logger/interaction_logger.py`, `tests/logger/test_interaction_logger.py`  
  - **Verification**: A test edit via FastAPI `TestClient` creates a line in `data/logs/interactions.jsonl` that validates against `specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/interaction_log.schema.yaml` and includes `subjective_load` (NASA‑TLX) and correct `task_start_ms` / `task_end_ms`.

- [ ] T005 [US-2] Implement dual‑success validation utilities where **primary success** (`overall_success`) is defined **solely** by exact vector match; semantic similarity (`semantic_pass`) is recorded separately and does **not** affect primary inclusion.  
  - **Files**: `src/validation/vector_match.py`, `src/validation/semantic_similarity.py`, `src/validation/run_validation.py`, `tests/validation/test_validation.py`  
  - **Verification**: Unit tests cover (a) exact vector match → `overall_success=True`, `semantic_pass` may be True/False; (b) semantic‑only match → `overall_success=False`, `semantic_pass=True`; (c) total failure → both False. All records conform to `semantic_validation.schema.yaml`.

- [ ] T006 [US-3] Perform a priori power analysis (α = 0.025, effect size d≈0.5, power = 0.80) and generate a deterministic synthetic participant driver that produces schema‑conformant logs at the required scale.  
  - **Files**: `src/simulation/power_analysis.py`, `src/simulation/simulate_participants.py`  
  - **Verification**: `python -m src.simulation.power_analysis` prints required N ≥ 32 and exits 0; after running `simulate_participants.py`, `data/logs/interactions.jsonl` contains ≥ 7 500 lines, all passing the `interaction_log` schema test.

---

## Phase 2 – Aggregation, analysis, and validation  

- [ ] T007 [US-2] Aggregate per‑task `SemanticValidation` records into a **session‑aware** file (`data/results/semantic_validation_by_session.jsonl`). The aggregation step also (a) skips tasks with corrupted ground‑truth vectors (logging a warning), (b) respects the 15‑minute timeout by marking such tasks as `"aborted"` and **excluding** them from primary time‑to‑success calculations, and (c) records the final effective N per participant.  
  - **File**: `src/analysis/validation_by_session.py` (updated)  
  - **Verification**: The output JSONL includes fields `session_id`, `task_id`, `overall_success`, `semantic_pass`, and `status`; a downstream schema validator (`tests/analysis/test_validation_aggregation.py`) passes.

- [ ] T008 [US-3] Implement the main statistical analysis script that (a) reads the session‑aware validation file, (b) **excludes** aborted tasks from all calculations, (c) computes **paired Wilcoxon signed‑rank tests** for `time_to_success_ms`, `iteration_count`, and `subjective_load` (fallback to paired t‑test if Shapiro‑Wilk p > 0.05), (d) applies Bonferroni correction (α = 0.025 per metric), (e) reports rank‑siserial effect size *r*, (f) bootstraps a 95 % confidence interval for the median difference (1 000 resamples), and (g) fits an exploratory linear mixed‑effects model with `expertise_level` as a fixed covariate. Results are written to `outputs/analysis_results.jsonl` conforming to `analysis_result.schema.yaml`.   <!-- FAILED-IN-EXECUTION: src/analysis/wilcoxon_analysis.py exit=2 --> <!-- FAILED-IN-EXECUTION: src/analysis/wilcoxon_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/analysis/wilcoxon_analysis.py exit=1 -->
  - **File**: `src/analysis/wilcoxon_analysis.py`  
  - **Verification**: Running `python -m src.analysis.wilcoxon_analysis` exits 0; the generated JSONL validates against the schema; a sanity‑check test (`tests/analysis/test_wilcoxon.py`) confirms that known synthetic differences produce the expected significant p‑value.

- [ ] T009 [US-3] Generate the final markdown report (`outputs/report.md`) that includes:  
  1. Median and mean tables for each metric per interface,  
  2. Wilcoxon (or t‑test) statistics, corrected p‑values, effect sizes, and 95 % CI,  
  3. Success‑rate breakdowns (vector‑match vs. semantic‑pass),  
  4. Average NASA‑TLX scores per interface,  
  5. A statement that current results are from deterministic simulation pending real‑world data.  
  - **File**: `src/report/generate_report.py`  
  - **Verification**: `python -m src.report.generate_report` creates `outputs/report.md`; a regex‑based test (`tests/report/test_report_contents.py`) checks for presence of all required sections and that numbers match those in `analysis_results.jsonl`.

- [ ] T010 [US-2] Run contract‑validation tests over all JSON‑Lines artifacts (interaction logs, semantic validation records, analysis results).  
  - **File**: `tests/contract/test_contracts.py`  
  - **Verification**: `pytest -q tests/contract/test_contracts.py` passes; any malformed line causes a test failure.

- [ ] T011 [US-3] End‑to‑end integration test that executes the full pipeline on the synthetic dataset, enforces the ≤ 6 hour wall‑clock budget (simulated with a time‑limit decorator), and verifies that `outputs/report.md` exists and contains both median and mean statistics traceable to input logs.  
  - **File**: `tests/integration/test_end_to_end.py`  
  - **Verification**: `pytest -q tests/integration/test_end_to_end.py` passes; the test asserts that total runtime < 360 seconds (mocked) and that the report references the synthetic N.

- [ ] T015 [US-3] Implement a real‑world retention verification that checks after data collection that **≥ 28** of the recruited **≥ 32** participants have completed both interface blocks with at least one primary‑success trial each (SC‑004). The task aborts with an informative error if the criterion is not met.  
  - **File**: `src/validation/retention_check.py`  
  - **Verification**: Running the script after participant data ingestion prints a pass/fail summary; a unit test (`tests/validation/test_retention_check.py`) validates correct behavior on synthetic edge cases.

- [ ] T016 [US-3] Record the actual wall‑clock runtime of the entire pipeline (from start of `run_pipeline.py` to completion of `generate_report.py`) and assert it does not exceed 6 hours on CPU‑only resources (SC‑005).  
  - **File**: `src/utils/runtime_tracker.py` (integrated into `run_pipeline.py`)  
  - **Verification**: After pipeline execution, a runtime log is written to `data/checksums.txt`; a test (`tests/utils/test_runtime_tracker.py`) confirms that the logged duration ≤ 21600 seconds.

- [ ] T017 [US-3] Execute the Reference‑Validator Agent on all citations in the project (including those in `plan.md`, `spec.md`, and generated reports) before final evaluation, satisfying Constitution Principle II.  
  - **File**: `src/validation/reference_validator.py`  
  - **Verification**: The script exits with status 0 only if all citations pass; a CI step fails otherwise.

---

## Phase 3 – Documentation, handoff, and human‑study scaffolding  

- [ ] T012 [P] [US-3] Write the methods/results markdown (`outputs/methods.md`) that references the exact pipeline steps, data sources, and simulation scope, and create a paper‑stage handoff manifest (`paper/handoff.yaml`) listing all artifacts required for manuscript preparation.  
  - **Files**: `outputs/methods.md`, `paper/handoff.yaml`  
  - **Verification**: `paper/handoff.yaml` validates as YAML and enumerates `outputs/report.md`, `data/logs/interactions.jsonl`, `data/results/semantic_validation_by_session.jsonl`, and the source code files; `methods.md` contains the required sections (Data, Interfaces, Logging, Validation, Analysis).

- [ ] T013 [P] [US-3] Implement a stub for ingesting real participant logs (`src/simulation/human_data_collection.py`) that parses logs adhering to the `interaction_log` schema and converts them into the unified session‑aware format used by downstream analysis.  
  - **File**: `src/simulation/human_data_collection.py`  
  - **Verification**: Running `python -m src.simulation.human_data_collection --input data/real_logs/` succeeds and produces `data/results/semantic_validation_by_session.jsonl` without schema violations.

- [ ] T014 [P] [US-1] Document the full reproducible workflow in `quickstart.md`, including commands to (a) set up the environment, (b) run the synthetic pipeline, (c) replace the synthetic data with real CrafterBench data once a verified URL is available, and (d) execute the analysis on real participant logs.  
  - **File**: `quickstart.md`  
  - **Verification**: A reviewer can follow the steps on a fresh runner and reproduce `outputs/report.md` using only the commands listed; a CI step (`tests/docs/test_quickstart.py`) checks that each command runs without error.

---

## Phase 4 – Optional future extensions (placeholder for later work)  

- T018 (future) – Extend the pipeline to support GPU‑accelerated CLIP inference for larger models if CPU performance becomes a bottleneck.  
- T019 (future) – Integrate a web‑based participant recruitment portal that writes session metadata directly to the `ParticipantSession` JSON store.

*These tasks are intentionally left unchecked and un‑detailed until the core study is completed and the real dataset becomes available.*  