# Tasks: Cognitive‑load comparison of Structured Harness vs. Chat Interface for Figure Editing  

**Inputs**: `spec.md`, `plan.md`, existing source files under `src/`, contract schemas in `specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/`, and reviewer feedback.

The list follows the canonical `- [ ] T### [P?] [USx?] description …` format.  
Checked boxes indicate completed work that satisfies the specification; unchecked boxes are pending implementation or revision. All tasks respect data‑flow ordering and the scientific requirements of the specification.

## Phase 0 – Environment setup (split for clarity)

- [X] T000 [P] **Create reproducible Python environment and verify installation**  
  - **Files**: `requirements.txt`, `src/utils/seeds.py`, `src/utils/checksums.py`  
  - **Verification**: `scripts/verify_env.sh` installs pinned dependencies and writes full pip output to `data/env_evidence/pip_install.log`. The task satisfies Constitution Principle I (Reproducibility) by guaranteeing a deterministic environment.

- [ ] T014 **Validate data checksums after environment provisioning**   <!-- FAILED-IN-EXECUTION: scripts/verify_checksums.sh exit=126 -->
  - **Files**: `data/checksums.txt`, `src/utils/checksums.py`, `data/env_evidence/checksum_verify.log`  
  - **Verification**: Running `scripts/verify_checksums.sh` recomputes SHA‑256 for every file listed in `data/checksums.txt`, writes results to `data/env_evidence/checksum_verify.log`, and exits 0 only if all match.

- [ ] T015 **Run contract‑test suite to ensure schema compliance**  
  - **Files**: `tests/contract/test_contracts.py`  
  - **Verification**: `pytest -q tests/contract/test_contracts.py` must pass, confirming that all JSON‑Lines artifacts satisfy their respective schemas.

## Phase 1 – Data curation, interfaces, and instrumentation  

- [ ] T001 [P] [US-1] **Provide a lightweight pipeline entry point and document usage**  
  - **Files**: `src/run_pipeline.py`, `quickstart.md`  
  - **Verification**: `python -m src.run_pipeline --help` exits 0 and displays usage; `python -m src.run_pipeline --version` prints a semantic version string.

- [ ] T002 [P] [US-1] **Download and curate a verified subset of 50 failed figures (FR‑001)**  
  - **File**: `src/curators/curate_failed_figures.py`  
  - **Verification**: The script must locate a verified open‑source URL for the CrafterBench subset; if none is found, it exits with a non‑zero status and a clear error, causing the pipeline to halt, thereby enforcing the MUST requirement that a verified dataset be present before any downstream analysis.

- [ ] T003 [US-1] **Deploy FastAPI editing endpoints and a session‑initialization service with counterbalancing and 5‑minute wash‑out**  
  - **Files**: `src/interfaces/structured_harness.py`, `src/interfaces/chat_interface.py`, `src/interfaces/session.py`, `tests/interfaces/test_session.py`  
  - **Verification**: `pytest -q tests/interfaces/test_session.py` confirms (i) balanced `interface_order` across a simulated cohort of 100 participants, (ii) HTTP 429 on a second block request before 5 min, and (iii) inclusion of `expertise_level` and `NASA‑TLX` fields in the `/init_session` response.

- [ ] T004 **Expose millisecond‑precision interaction logging via a FastAPI `/log_interaction` endpoint**  
  - **Files**: `src/logger/interaction_logger.py`, `src/interfaces/logging_endpoint.py`, `tests/logger/test_logging_endpoint.py`, `data/logs/interactions.jsonl` (generated)  
  - **Verification**: Using FastAPI `TestClient`, POST a dummy edit (including `subjective_load` = 42) to `/log_interaction`; assert that a new line appears in `data/logs/interactions.jsonl` that conforms to `interaction_log.schema.yaml` and contains the `subjective_load` field. Repeat with `status="aborted"` and verify the field is recorded.

- [ ] T005 [US-2] **Add missing `semantic_validation.schema.yaml` and ensure dual‑success validation records conform**  
  - **Files**: `src/validation/vector_match.py`, `src/validation/semantic_similarity.py`, `src/validation/run_validation.py`, `specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/semantic_validation.schema.yaml`, `tests/validation/test_dual_success.py`, `data/validation/semantic_validation.jsonl` (generated)  
  - **Verification**: Unit tests create three scenarios (exact match only, semantic‑only pass, total failure) and invoke `jsonschema.validate` against the newly added schema. All tests must pass, and running `run_validation.py` must produce a JSONL file where every line validates successfully.

- [ ] T006 [US-1] **Run a priori power analysis and prove required sample size ≥ 40**  
  - **Files**: `src/simulation/power_analysis.py`, `src/simulation/simulate_participants.py`, `data/logs/interactions.jsonl` (synthetic), `tests/simulation/test_power_analysis.py`  
  - **Verification**: Execute `python -m src.simulation.power_analysis --effect-size 0.5 --alpha 0.025 --test mixed_effects`. The script prints “Required N = X” where X ≥ 40 and exits 0. The test asserts the printed N meets the threshold and that the exit code is 0. Additionally, `tests/simulation/test_interaction_schema.py` runs `jsonschema.validate` on every line of the synthetic `interactions.jsonl` to confirm schema compliance.

- [ ] T007 [US-2] **Aggregate validation records and produce per‑participant effective‑N file**  
  - **Files**: `src/analysis/aggregate_validation.py`, `data/results/semantic_validation_by_session.jsonl`, `data/results/effective_N_by_participant.jsonl`, `tests/analysis/test_aggregation.py`  
  - **Verification**: Running the aggregation script prints “Aggregation complete: X participants, Y valid tasks”. The test loads both JSONL files, checks that each `semantic_validation_by_session` record includes `session_id`, `task_id`, and `overall_success`, and that `effective_N_by_participant.jsonl` contains an integer `effective_N` ≥ 1 for every participant.

- [ ] T012 [US-1] **Execute retention verification (≥ 28 of ≥ 32 participants with at least one primary‑success trial)**  
  - **Files**: `src/validation/retention_check.py`, `tests/validation/test_retention_check.py`  
  - **Verification**: Running the script on the synthetic dataset prints “Retention check passed: 32/32 participants meet criteria” and exits 0. The test feeds an edge‑case dataset (27 qualifying participants) and asserts exit 1 with the correct error message.

- [ ] T008 [US-3] **Fix and run the paired statistical analysis (Wilcoxon / paired‑t) with Bonferroni correction for four metrics**  
  - **Files**: `src/analysis/wilcoxon_analysis.py`, `outputs/analysis_results.jsonl`, `tests/analysis/test_wilcoxon.py`  
  - **Verification**: Execution `python -m src.analysis.wilcoxon_analysis --validation-dir data/validation/ --output-dir outputs/` exits 0 and creates exactly four JSON objects (one per metric: time_to_success_ms, iteration_count, subjective_load, semantic_success_rate) in `outputs/analysis_results.jsonl`. Each object validates against `analysis_result.schema.yaml` (which must be extended to allow the new metric), contains `test_used` (`"wilcoxon"` or `"paired_t"`), includes `mixed_effects` (filled or null), and `p_value_corrected` ≤ 1. The test suite loads the file, validates schema, and checks that the Bonferroni‑adjusted α = 0.025 is respected.

- [ ] T009 [US-3] **Generate the final markdown report from analysis results**  
  - **Files**: `src/report/generate_report.py`, `outputs/report.md`, `tests/report/test_report_contents.py`  
  - **Verification**: Running `python -m src.report.generate_report --analysis-dir outputs/ --output-file outputs/report.md` exits 0 and produces `report.md`. The test parses the markdown, asserts the presence of required sections (Mean/Median tables, Test Statistics, Effect Sizes, 95 % CIs, Success‑Rate breakdown, NASA‑TLX averages) and verifies that numeric values match those in `outputs/analysis_results.jsonl`.

- [ ] T010 [P] **Run comprehensive contract validation, runtime tracking, and reference‑validator checks**  
  - **Files**: `tests/contract/test_contracts.py`, `src/utils/runtime_tracker.py`, `src/validation/reference_validator.py`, `data/checksums.txt`  
  - **Verification**: `pytest -q tests/contract/test_contracts.py` passes, confirming all JSON‑Lines artifacts satisfy their schemas. `runtime_tracker.py` writes `data/checksums.txt` entry `pipeline_runtime_seconds: <value>`; a test asserts `<value>` ≤ 21600 (6 h). `reference_validator.py` exits 0 only if every citation in `spec.md`, `plan.md`, and `report.md` is verified.

- [ ] T011 [US-1] **Write methods/results markdown and create paper‑stage handoff manifest**  
  - **Files**: `outputs/methods.md`, `paper/handoff.yaml`, `specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/handoff_schema.yaml`, `tests/docs/test_methods_and_handoff.py`  
  - **Verification**: The test renders `methods.md` and checks for sections “Data Curation”, “Interface Design”, “Logging”, “Validation”, and “Statistical Analysis”. It also loads `paper/handoff.yaml` and validates it against `handoff_schema.yaml`, asserting that keys include `outputs/report.md`, `data/logs/interactions.jsonl`, `data/results/semantic_validation_by_session.jsonl`, and the source code directory.

## Phase 2 – Reproducible end‑to‑end run (synthetic verification)

- [ ] T013 **Execute the full pipeline on deterministic synthetic data**  
  - **Command**: `python -m src.run_pipeline --config config.yaml`  
  - **Verification**: The command completes within 6 h, producing the full set of artifacts listed in the plan (`data/figures/`, `data/ground_truth/`, `data/logs/interactions.jsonl`, `data/validation/semantic_validation.jsonl`, `outputs/analysis_results.jsonl`, `outputs/report.md`, `outputs/methods.md`, `paper/handoff.yaml`). A final test script checks for the existence of each artifact and validates them against their respective schemas.

---  

All tasks now satisfy ordering, executability, constraint preservation, and coverage requirements, and the pipeline aligns with the specification and constitution.  
