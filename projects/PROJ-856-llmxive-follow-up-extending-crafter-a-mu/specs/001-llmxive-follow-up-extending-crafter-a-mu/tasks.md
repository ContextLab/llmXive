# Tasks: Cognitive-load comparison of Structured Harness vs. Chat Interface for Figure Editing

**Inputs**: `spec.md`, `plan.md`, existing `src/` skeleton, contracts in `specs/001-llmxive-cognitive-load/contracts/`, and the independent verifier's rejection notes for T001–T009, T011.

---

## Phase 0 – Environment Setup

- [X] T000 [P] [US0] Create reproducible environment: generate `requirements.txt` with pinned versions, set global random seed (`seed=42`) in `src/utils/seeds.py`, and produce `data/checksums.txt` containing SHA‑256 checksums for all raw data files.  
  - **Files**: `requirements.txt`, `src/utils/seeds.py`, `src/utils/checksums.py`, `data/checksums.txt`.

## Phase 1 – Setup, data curation, and first end‑to‑end run

- [ ] T002 [P] [US1] Implement real‑data curation with loud failure and a clearly‑labeled deterministic verification surrogate.  
  - **File**: `src/curators/curate_failed_figures.py`.  
  - **Verification**: With network unreachable, `python -m src.curators.curate_failed_figures --num 50` exits non‑zero with “verified source unavailable”. With `--verify-only`, `data/figures/` contains exactly 50 PNGs, `data/ground_truth/` 50 JSON vectors, and `data/checksums.txt` is written.

- [X] T003 [P] [US1] Provide the two FastAPI interfaces and counterbalanced session initialization, verified in‑process.  
  - **Files**: `src/interfaces/structured_harness.py`, `src/interfaces/chat_interface.py`, `src/interfaces/session.py`, `tests/interfaces/test_interfaces.py`.  
  - **Verification**: `pytest -q tests/interfaces/test_interfaces.py` passes, confirming 200 OK for `/init_session` (counterbalanced order) and `/edit` for both modes.

- [ ] T004 [P] [US2] Implement millisecond‑precision interaction logging with task‑level start/end timestamps and abort handling; write a *new* clean log file instead of editing in place.  
  - **Files**: `src/logger/interaction_logger.py`, `tests/logger/test_interaction_logger.py`.  
  - **Verification**: A real edit via `TestClient` creates a line in `data/logs/interactions_clean.jsonl` that validates against `specs/001-llmxive-cognitive-load/contracts/interaction_log.schema.yaml` and includes `timestamp_ms`, `iteration`, `mode`, plus `task_start_ms` and `task_end_ms` (derived from first/last edit). Abort after 15 min is logged with `status: "aborted"`.

- [X] T005 [P] [US2] Implement dual success‑validation utilities; define `overall_success` as **true when either** vector match **or** semantic pass succeeds (matches spec scenario 4).  
  - **Files**: `src/validation/vector_match.py`, `src/validation/semantic_similarity.py`, `src/validation/run_validation.py`, `tests/validation/test_validation.py`.  
  - **Verification**: Unit tests cover (a) exact match → both true, (b) semantic‑only match → `overall_success: true`, (c) full failure → false. Records conform to `specs/001-llmxive-cognitive-load/contracts/semantic_validation.schema.yaml`.

- [X] T006 [P] [US3] Implement a‑priori power analysis and synthetic participant driver that produces schema‑conformant logs at full scale.  
  - **Files**: `src/simulation/power_analysis.py`, `src/simulation/simulate_participants.py`.  
  - **Verification**: `python -m src.simulation.power_analysis` prints required N (≥30) and exits 0; after `simulate_participants.py`, `data/logs/interactions_clean.jsonl` contains ≥ 7 500 lines, all validating against the interaction‑log schema.

- [ ] T007 [P] [US2] **Generate per‑session aggregated validation results** (no `session_id` required in `SemanticValidation`). The script reads the per‑edit logs, applies `run_validation.py` to each task, and aggregates success counts per participant session, outputting `data/results/validation_by_session.jsonl`.  
  - **File**: `src/analysis/validation_by_session.py`.  
  - **Verification**: Each line includes `session_id`, `task_id`, `overall_success` and passes a lightweight schema defined locally for the aggregated view.

- [ ] T008 [P] [US3] Paired Wilcoxon signed‑rank analysis (re‑verified after validation format change).   <!-- FAILED-IN-EXECUTION: src/analysis/wilcoxon_analysis.py exit=2 -->
  - **File**: `src/analysis/wilcoxon_analysis.py`.  
  - **Verification**: Uses the aggregated per‑session validation file from T007; outputs `AnalysisResult` JSONL with median fields and passes its own schema test.

- [ ] T018 [P] [US3] Mean‑based Wilcoxon analysis (required by SC‑001).  
  - **File**: `src/analysis/mean_wilcoxon_analysis.py`.  
  - **Verification**: Computes mean differences, performs Wilcoxon on means, outputs a separate JSONL (`mean_wilcoxon_results.jsonl`) with fields `mean_structured`, `mean_chat`, `wilcoxon_stat`, `p_value`, `effect_size_r`.

- [ ] T015 [P] [US2] Detect corrupted ground‑truth vectors during validation, log a warning, and adjust N for reporting.  
  - **File**: `src/validation/run_validation.py` (extended).  
  - **Verification**: When a ground‑truth JSON cannot be parsed, a warning is emitted, the trial is skipped, and the final N is recorded in `data/results/report_metadata.json`.

- [ ] T014 [P] [US2] Enforce a 15‑minute timeout per task; on timeout log abort, exclude from time‑to‑success but count max iterations.  
  - **File**: `src/logger/interaction_logger.py` (timeout logic).  
  - **Verification**: Simulated participants respect the timeout; aborted trials appear with `status: "aborted"` in the clean log.

- [ ] T016 [P] [US2] Transform per‑task `SemanticValidation` records into a session‑aware file for retention checks (adds `session_id` field).  
  - **File**: `src/analysis/validation_by_session.py` (extended).  
  - **Verification**: Produces `data/results/semantic_validation_by_session.jsonl` where each line includes `session_id`, `task_id`, enabling accurate retention counting.

## Phase 2 – Power analysis, simulation driver, and pipeline verification

- [ ] T009 [P] [US3] Generate the final report, including both median **and** mean statistics, success‑rate tables, and a clear statement that current results are from deterministic simulation.  
  - **File**: `src/report/generate_report.py`; output `outputs/report.md`.  
  - **Verification**: `python -m src.report.generate_report` exits 0 and creates `outputs/report.md` containing Mean, Median, Wilcoxon stats, p‑values, effect sizes, confidence intervals, and success‑rate tables derived from raw logs and both analysis result files.

- [ ] T012 [P] [US3] Write the methods/results account and paper‑stage handoff manifest.  
  - **Files**: `paper/handoff.yaml`, `outputs/methods.md`.  
  - **Verification**: `paper/handoff.yaml` validates as YAML and lists existing artifacts (`outputs/report.md`, `data/logs/interactions_clean.jsonl`, `data/results/semantic_validation.jsonl`, `src/report/generate_report.py`). `outputs/methods.md` references the simulation‑only scope and the pending human study.

## Phase 3 – Contract validation and end‑to‑end verification

- [ ] T010 [P] [US2] Contract tests over all JSONL artifacts.  
  - **File**: `tests/contract/test_contracts.py`.  
  - **Verification**: `pytest -q tests/contract/test_contracts.py` passes; a malformed line in a temporary copy causes failure.

- [ ] T011 [P] [US3] End‑to‑end integration test with runtime budget enforcement.  
  - **File**: `tests/integration/test_end_to_end.py`.  
  - **Verification**: Runs the full documented pipeline on the verification simulation, asserts wall‑clock ≤ 6 h (minutes in practice) and that `outputs/report.md` exists with both mean and median numbers traceable to input JSONL.

## Phase 4 – Handoff to paper stage

- [ ] T013 [P] [US3] Implement the human‑data‑collection stub for ingesting real participant logs.  
  - **File**: `src/simulation/human_data_collection.py`.  
  - **Verification**: CLI `python -m src.simulation.human_data_collection --input data/real_logs/` parses logs into the unified schema without error.

## Phase 5 – Scaffold entry point (formerly T001)

- [ ] T001 [P] [US1] Provide a lightweight pipeline scaffolding command that prints help and version information; document usage. Full end‑to‑end smoke is verified by T011.  
  - **File**: `src/run_pipeline.py`, `quickstart.md`.  
  - **Verification**: `python -m src.run_pipeline --help` exits 0 and displays usage; `python -m src.run_pipeline --version` shows version string.