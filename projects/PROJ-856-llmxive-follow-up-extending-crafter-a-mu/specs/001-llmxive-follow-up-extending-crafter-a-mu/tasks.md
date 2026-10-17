# Tasks: Cognitive‑load comparison of Structured Harness vs. Chat Interface for Figure Editing  

**Inputs**: `spec.md`, `plan.md`, existing code skeleton, contracts, and reviewer feedback.  

The tasks below implement the smallest complete end‑to‑end study that satisfies every functional requirement (FR‑001 – FR‑007) and success‑criteria (SC‑001‑SC‑005).  They are ordered to respect data flow and dependencies.  All paths are relative to the project root and point to files that will be created or modified by the task.

---

## Phase 1 – Setup, data curation & first end‑to‑end run  

- [ ] **T001** [P] [UserStory-1] Create a deterministic environment, pin dependencies, and document the runnable command.  
  - **File**: `quickstart.md` (add a “Run the end‑to‑end pipeline” section).  
  - **Verification**: `pytest -q tests/integration/test_end_to_end.py` passes; the command `python -m src.run_pipeline --config config.yaml` executes without error and prints “Pipeline completed”.  

- [ ] **T002** [P] [UserStory-1] Implement data‑curation script that downloads a reproducible 50‑figure subset from CrafterBench, injects a single localized error per figure, and writes ground‑truth vectors.  
  - **File**: `src/curators/curate_failed_figures.py` (CLI entry point `--output data/figures/`).  
  - **Verification**: After running `python -m src.curators.curate_failed_figures --num 50`, the directory `data/figures/` contains exactly 50 PNG files and `data/ground_truth/` contains 50 matching JSON vector files; a checksum manifest `data/checksums.txt` is generated.  

- [ ] **T003** [P] [UserStory-2] Provide two FastAPI interface stubs (structured harness & chat) with a session‑initialisation endpoint that randomises and counterbalances interface order per participant.  
  - **Files**: `src/interfaces/structured_harness.py`, `src/interfaces/chat_interface.py`, `src/interfaces/session.py`.  
  - **Verification**: `curl -X POST [UNRESOLVED-CLAIM: http://localhost:8000/init_session — ConnectionError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /init_session (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))] -d '{"participant_id":"test"}'` returns JSON with `"order": ["structured","chat"]` or the reverse; both `/edit` endpoints respond `200 OK`.  

- [ ] **T004** [P] [UserStory-2] Add millisecond‑precision interaction logging that writes one JSON line per edit to `data/logs/interactions.jsonl`.  
  - **File**: `src/logger/interaction_logger.py`.  
  - **Verification**: Simulated edit via `curl -X POST .../edit` creates a new line in `data/logs/interactions.jsonl` whose `timestamp_ms` field is an integer and `iteration` increments correctly.  

- [ ] **T005** [P] [UserStory-3] Implement success‑validation utilities that **both** perform exact vector match **and** compute semantic similarity (≥ 0.95). The utilities must be invoked together and only produce a `SemanticValidation` record when **both** checks pass.  
  - **Files**: `src/validation/vector_match.py`, `src/validation/semantic_similarity.py`.  
  - **Verification**: Unit tests confirm that a perfect‑match image passes both checks and generates a validation record; an image that fails either check does not produce a successful validation record.  

---

## Phase 2 – Simulation, power analysis & full pipeline  

- [ ] **T006** [P] [UserStory-4] Compute a priori power analysis for a within‑subjects design (medium effect, α = 0.05, power = 0.80) and abort if the planned N < required.  
  - **File**: `src/simulation/power_analysis.py`.  
  - **Verification**: Running the script prints “Required participants ≥ 30”; the pipeline proceeds only if `config.participants >= 30`.  

- [ ] **T007** [P] [UserStory-5] Create a synthetic participant driver that simulates 30 participants, randomises interface order, streams the 50 curated figures, and generates realistic edit sequences (latencies drawn from log‑normal distributions).  
  - **File**: `src/simulation/simulate_participants.py`.  
  - **Verification**: After execution, `data/logs/interactions.jsonl` contains ≥ 30 × 50 × (1‑5) ≈ 7 500 lines; each line conforms to `interaction_log.schema.yaml`.  

- [ ] **T014** [P] [UserStory-3] Run combined validation on each completed trial: invoke both `vector_match` and `semantic_similarity`; if **both** succeed, write a `SemanticValidation` JSON line to `data/validation/semantic_validation.jsonl`.  
  - **File**: `src/validation/run_combined_validation.py`.  
  - **Verification**: After simulation, the validation file contains one record per trial that succeeded; malformed or partially successful trials are not marked as successful.  

- [ ] **T008** [P] [UserStory-6] Add a retention‑check step that ensures at least 25 of the 30 simulated sessions contain one non‑aborted successful trial (as recorded in `semantic_validation.jsonl`); if not, emit a warning and halt analysis.  
  - **File**: `src/analysis/retention_check.py`.  
  - **Verification**: Unit test manipulates the log to produce only 24 successful sessions and asserts that the script exits with a non‑zero status and prints “Retention threshold not met”.  

---

## Phase 3 – Statistical analysis & reporting  

- [ ] **T009** [P] [UserStory-7] Implement paired Wilcoxon signed‑rank analysis for `time_to_success` and `iteration_count`. Compute **both mean and median** differences, apply Bonferroni correction, compute effect‑size *r* and bootstrap 95 % confidence intervals, and output `AnalysisResult` JSON objects for each metric.  
  - **File**: `src/analysis/wilcoxon_analysis.py`.  
  - **Verification**: Running the script on a synthetic dataset with a known difference yields the expected `p_value < 0.05`, correct mean and median differences, and prints the full `AnalysisResult` JSON objects.  

- [ ] **T010** [P] [UserStory-8] Generate the final human‑readable report (`outputs/report.md`) containing:  
  1. **Mean** and **median** times & iterations for each interface,  
  2. Wilcoxon statistics, p‑values, effect sizes, confidence intervals,  
  3. Separate success‑rate tables for **vector‑match** and **semantic‑similarity** passes,  
  4. A brief “Methods” paragraph referencing the scripts used.  
  - **File**: `src/report/generate_report.py`.  
  - **Verification**: The script creates `outputs/report.md`; a regex check confirms presence of “Mean”, “Median”, “Wilcoxon statistic”, “p‑value”, and both success‑rate tables.  

---

## Phase 4 – Contract validation & CI integration  

- [ ] **T011** [P] [UserStory-9] Write contract tests that validate every JSON line in `data/logs/interactions.jsonl` against `contracts/interaction_log.schema.yaml` and every validation record against `contracts/semantic_validation.schema.yaml`.  
  - **File**: `tests/contract/test_contracts.py`.  
  - **Verification**: `pytest -q tests/contract/test_contracts.py` passes; deliberately malformed JSON causes the test to fail.  

- [ ] **T012** [P] [UserStory-10] Add an integration test that runs the full pipeline (`quickstart` command) on the synthetic data, measures total wall‑clock time, asserts it is ≤ 6 hours, and asserts that `outputs/report.md` exists and contains a valid `AnalysisResult` conforming to `contracts/analysis_result.schema.yaml`.  
  - **File**: `tests/integration/test_end_to_end.py`.  
  - **Verification**: The test executes in ≤ 6 h on the GitHub Actions CPU runner, records the elapsed time, fails if > 21600 s, and succeeds otherwise.  

- [ ] **T015** [P] [UserStory-10] Standalone runtime‑verification task: execute the entire pipeline while timing it; exit with non‑zero status if total duration exceeds 6 hours. This task can be invoked independently for CI monitoring.  
  - **File**: `src/ci/runtime_check.py`.  
  - **Verification**: Running `python -m src.ci.runtime_check` prints the elapsed time and exits with status 0 only when ≤ 21600 seconds.  

---

## Phase 5 – Handoff to paper stage  

- [ ] **T013** [P] [UserStory-12] Create a handoff manifest (`paper/handoff.yaml`) that lists all artefacts required for the manuscript (figure images, tables, report, raw logs, and code version).  
  - **File**: `paper/handoff.yaml`.  
  - **Verification**: The manifest is syntactically valid YAML and includes entries for `data/figures/`, `outputs/report.md`, and `src/report/generate_report.py`.  

---

### Dependency Map (summary)

| Requirement | Tasks that satisfy it |
|-------------|-----------------------|
| FR‑001 / SC‑004 | T002, T004, T007 |
| FR‑002 | T003, T007 |
| FR‑003 | T004, T007 |
| FR‑004 | T005 (both checks enforced) |
| FR‑005 | T005 (semantic similarity) |
| FR‑006 | T009 |
| FR‑007 / SC‑001‑SC‑003 | T009, T010 |
| SC‑005 (≤ 6 h) | T012, T015 |
| Contract integrity | T011, T012 |
| Paper handoff | T013 |
| Quick‑start documentation | T001 |

All tasks are unchecked (`- [ ]`) to be executed by the CI pipeline.  When a task is completed and verified, the platform will mark its checkbox automatically.  