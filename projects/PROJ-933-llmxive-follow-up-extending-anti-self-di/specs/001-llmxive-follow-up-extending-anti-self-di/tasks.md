# Tasks: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Research, Feasibility & Project Setup

**Purpose**: Validate experimental design, perform pre-study power analysis, and initialize project structure.

- [X] T001.1 [P] **Research & Setup (Structure)**: Create project directory structure (`mkdir -p projects/PROJ-933-llmxive-followup-extending-anti-self-di/code/{data,models,analysis,config} data/ results/`) and `quickstart.md`. **Verification**: Run `ls -R projects/...` to confirm all directories exist. (FR-001, Plan Phase 0 & 1).
- [X] T001.2 [P] **Research & Setup (Feasibility)**: Generate `research.md` confirming dataset feasibility using *literature-based* effect size estimates (d=0.5) and produce `data-model.md` and `contracts/*.schema.yaml`. **Verification**: Verify `research.md` exists and contains effect size justification. **Does NOT require data download yet.** (FR-013, Plan Phase 0 & 1).
- [X] T002.1 [P] **Project Initialization**: Initialize `requirements.txt` (pinned versions), `config/settings.yaml` (seeds, hyperparameters, timeout). **Verification**: Run `pip install -r requirements.txt` to confirm no errors.
- [X] T002.2 [P] **Linting Configuration**: Create explicit configuration files: `.ruff.toml` and `pyproject.toml` sections for black/ruff. **Verification**: Run `ruff check .` to confirm config loads. (FR-001, Plan Phase 0).
- [X] T006 [P] **Pre-Study Power Analysis**: Perform power analysis in `code/analysis/statistical_test.py` to confirm N ≥ 30 for power ≥ 0.8 using literature-based effect size (d=0.5). **Verification**: Script outputs `results/pre_study_power.json` with `power >= 0.8`. **Depends on T001.2** (must run after feasibility check but BEFORE data download T015). (FR-013, SC-007).

**Checkpoint**: Verify `results/pre_study_power.json` exists and contains `power >= 0.8`.

---

## Phase 1: Data Acquisition and Context Simulation (Priority: P1) 🎯 MVP

**Goal**: Ingest UltraFeedback and Dolly, filter for ≥4 traces, and simulate privileged context vs. target distribution.

**Independent Test**: Load dataset, perform split, output JSON report confirming prompt count, rationale count (≥4), and statistical distribution of selected privileged contexts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Unit test for dataset filtering logic in `code/data/test_preprocess.py` (verify prompts with <4 traces are skipped per FR-016)
- [X] T014 [P] [US1] Integration test for context simulation in `code/data/test_context_sim.py` (verify random sampling of 1 privileged vs. remaining target)

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `code/data/download.py` to fetch UltraFeedback and Dolly via `datasets.load_dataset` (streaming=True) with checksumming per Constitution. **Must raise on fetch failure; NO synthetic fallback.** **Verification**: Script outputs `data/checksums.txt` and `data/raw/` directory with files.
- [X] T016 [P] [US1] Implement `code/data/preprocess.py` to filter prompts with ≥4 distinct annotated reasoning traces (FR-001, FR-016). **Verification**: Script outputs `data/filtered_prompts.jsonl` with count >= 30.
- [X] T017 [US1] **Context Simulator (Sampling)**: Implement logic in `code/data/preprocess.py` to randomly sample 1 rationale as "privileged context" $c$. **Logic**: Detect if sampled context is identical to unselected rationales; re-sample up to N=10 times. If identical rationales persist after N=10 attempts, **exclude the prompt** from the dataset (FR-002, Edge Case). **Output**: `data/context_splits.json` (split data) and `data/excluded_prompts.log` (exclusion log). **Verification**: Verify `data/context_splits.json` exists and contains `privileged` and `target` keys for each prompt; verify `data/excluded_prompts.log` exists. (FR-002, Edge Case).
- [X] T017.1 [US1] **Context Simulator (Exclusion & Reporting)**: Implement logic to log excluded prompts and output final statistics reporter in `code/data/preprocess.py` (prompt count, avg tokens, deliberation token frequency). **Verification**: Verify `data/excluded_prompts.log` exists and `data/context_stats.json` is generated. (FR-002, Edge Case).
- [X] T019 [US1] Add validation to ensure no synthetic fallback occurs; raise error if real data fetch fails (Constitution Rule). **Verification**: Unit test confirms `ValueError` on simulated network failure.

**Checkpoint**: Verify `data/context_splits.json` exists and contains valid split data for all prompts.

---

## Phase 2: Pre-Training Infrastructure (Blocking for US2)

**Purpose**: Execute Inference-Only Pass, compute Teacher Distribution, and verify model feasibility.

- [X] T020 [P] [US2] Implement `code/models/inference_only.py` to load `data/context_splits.json` and compute Teacher Distribution (average logit distribution over all unselected rationales) **using streaming and chunked/batched inference**. **Output**: `data/teacher_logits_raw.jsonl`. **Verification**: Verify `data/teacher_logits_raw.jsonl` exists and contains N entries matching prompt count. (FR-014).
- [X] T021 [US2] **Inference-Only Pass (Streaming)**: Execute inference on all unselected rationales for each prompt **using batch size 50**. **Algorithm**: Stream logits to `data/teacher_logits_raw.jsonl` (append mode) immediately after each batch to prevent OOM. **Do NOT load all logits into RAM.** **Verification**: Verify file size is reasonable and no OOM occurs. (FR-014, Plan Complexity Tracking).
- [X] T022 [US2] Implement validation to ensure `data/teacher_logits_raw.jsonl` is complete and matches expected prompt count. **Verification**: Script asserts line count matches prompt count in `data/context_splits.json`.
- [X] T048 [US2] **Teacher Distribution Averaging**: Implement averaging logic in `code/models/inference_only.py` to compute the "Teacher Distribution" (average of raw logits) from `data/teacher_logits_raw.jsonl` **via streaming aggregation** and save to `data/teacher_distribution.json`. **Verification**: Verify `data/teacher_distribution.json` exists and schema matches `contracts/training_output.schema.yaml`. **Depends on T021** (FR-003, FR-014).
- [X] T049 [US2] Verify model architecture/size (e.g., DistilBERT) against CPU constraints (RAM, compute) in `code/models/model_check.py` before training begins. **Verification**: Script outputs `results/model_feasibility.json` confirming RAM < 6.5GB. (Assumptions)

**Checkpoint**: Verify `data/teacher_distribution.json` exists and is valid.

---

## Phase 3: User Story 2 - AntiSD Signal Computation and Training Loop (Priority: P2)

**Goal**: Implement custom PyTorch training loop with gradient inversion to ascend JS divergence, running on CPU with full/partial fine-tuning.

**Independent Test**: Run training on single prompt, log loss curves, verify negative gradient dot product and increasing JS divergence over multiple training steps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for JS divergence calculation in `code/models/test_metrics.py` (verify numerical stability)
- [X] T024 [P] [US2] Unit test for gradient inversion logic in `code/models/test_anti_sd.py` (verify ascending vs. descending divergence)

### Implementation for User Story 2

- [X] T028-ENFORCE [US2] **Hard Timeout Enforcer**: Implement `code/models/signal_handler.py` with a signal handler (SIGALRM/SIGTERM) that raises `SystemExit` with a specific "timeout" status on 5.5h limit. **Must be integrated into main.py and run BEFORE training starts.** **Verification**: Script exits with code 1 after 5.5h. (FR-007, SC-004).
- [X] T025 [P] [US2] Implement `code/models/anti_sd_loop.py` custom PyTorch training loop with token-level gradient inversion (FR-008). **Depends on T028-ENFORCE** (timeout mechanism must be ready). **Runtime Note**: Must be invoked *after* T028-ENFORCE is active in the runtime environment. **Verification**: Script outputs `results/training_trajectory.json` with loss curves.
- [X] T026 [US2] Implement JS divergence calculation between student and the averaged Teacher Distribution (from T048) using PMI (FR-003). **Verification**: Unit test confirms JS divergence calculation.
- [X] T027 [US2] Implement gradient ascent logic for AntiSD condition and gradient descent for standard condition (FR-004). **Verification**: Unit test confirms gradient direction.
- [X] T028 [US2] **Timeout & Logging**: Implement logging logic to capture `status` ("timeout" or "completed") and `elapsed_time` to `results/training_metrics.json`. **Depends on T028-ENFORCE** (must log the status set by the enforcer). **Verification**: Verify `results/training_metrics.json` contains `status` and `elapsed_time`. (FR-007, SC-004).
- [X] T029 [US2] Implement logging for token probabilities, loss curves, and trajectory data for a sufficient number of steps to capture training dynamics; explicitly generate multiple trajectories for evaluation. **Verification**: Verify `results/trajectories.jsonl` exists. (FR-008)
- [X] T030 [US2] Implement memory monitoring using `psutil` to assert peak RAM < 6.5 GB during training; output `results/memory_log.json` with peak values. **Verification**: Verify `results/memory_log.json` exists and `peak_ram < 6.5`. (SC-005)

**Checkpoint**: Verify `results/training_trajectory.json` and `results/training_metrics.json` exist.

---

## Phase 4: User Story 3 - Diversity Measurement, Quality Validation, and Statistical Analysis (Priority: P3)

**Goal**: Compute BLEU/semantic similarity, validate with Human Evaluation Proxy, and run Wilcoxon signed-rank tests.

**Independent Test**: Compute metrics against unselected rationales, output Wilcoxon p-value, effect size, and correlation coefficient.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Unit test for BLEU and semantic similarity calculation in `code/models/test_metrics.py`
- [X] T032 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `code/analysis/test_statistical_test.py`

### Implementation for User Story 3

- [X] T035.1 [US3] **Generate Reference Subset**: Implement script to sample and save a "human-annotated subset" of the *original* unselected rationales (FR-010). **Logic**: Randomly select a subset of rationales from `data/context_splits.json` (unselected set) and save to `data/human_reference_subset.json`. This serves as the ground-truth reference for the simulation. **Verification**: Verify `data/human_reference_subset.json` exists and contains a sufficient number of entries for the study. (FR-010, FR-015).
- [X] T035-SIM [US3] **Human Evaluation Proxy (Deterministic Simulation)**: Implement `code/analysis/human_proxy_sim.py` to generate deterministic scores for generated trajectories. **Logic**: Use a fixed seed and a defined distribution (Normal) to mimic human raters, scoring against `data/human_reference_subset.json` (from T035.1) to compute "consensus alignment". **Justification**: Reproducibility Principle I requires deterministic simulation for CI; manual recruitment is not feasible in automated pipelines. **Fallback**: If simulation is deemed insufficient by review, the task is marked 'blocked' and requires manual human data injection (FR-015) which is outside CI scope. **Output**: `data/human_scores.csv`. (FR-010, FR-015, SC-001, SC-006).
- [X] T047 [US3] **Human Score Ingest**: Implement parser in `code/analysis/human_score_ingest.py` to read `data/human_scores.csv` (generated by T035-SIM) and `data/human_reference_subset.json` (from T035.1) to compute the final "Human Evaluation Proxy Score" (FR-010). **Depends on T035.1 and T035-SIM**. **Verification**: Verify `results/human_proxy_scores.json` exists.
- [X] T033 [P] [US3] Implement pairwise BLEU and semantic similarity calculation in `code/models/metrics.py` against unselected rationales (FR-005). **Verification**: Unit test confirms BLEU calculation.
- [X] T034 [US3] Implement deliberation token counter (e.g., "Wait", "However") in `code/models/metrics.py` (FR-009). **Verification**: Unit test confirms token counting.
- [X] T036 [US3] Implement Pearson correlation calculation between deliberation token frequency and Human Evaluation Proxy Score (FR-011). **Verification**: Unit test confirms correlation calculation.
- [X] T037 [US3] Implement Wilcoxon signed-rank test comparing AntiSD vs. standard self-distillation on diversity and quality metrics (FR-006, FR-017). **Verification**: Unit test confirms Wilcoxon test.
- [X] T046 [US3] Implement post-hoc power analysis in `code/analysis/statistical_test.py` to calculate observed statistical power (1-β) based on effect size (FR-018). **Verification**: Script outputs `results/observed_power.json`. **Mandatory**: This output is a required field in the final report.
- [X] T038 [US3] **Final Report Generation**: Generate final analysis report with p-values, effect sizes, correlation coefficients, and **observed statistical power** as a required field (FR-013, FR-018, SC-001, SC-002, SC-003). **Verification**: Verify `results/final_report.md` contains all required fields.
- [X] T039 [US3] Visualize loss curves and diversity metrics in `code/analysis/visualize.py`. **Verification**: Verify `results/plots/` directory contains expected images.

**Checkpoint**: Verify `results/final_report.md` exists and contains all required statistical fields.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `docs/` including runbook for streaming datasets
- [X] T041 Code cleanup and refactoring of training loop for readability
- [X] T042 Performance optimization for CPU-only inference pass
- [X] T043 [P] Additional unit tests for edge cases (e.g., identical privileged context) in `tests/unit/`
- [X] T044 Security hardening of dataset download scripts
- [X] T045 Run validation script to verify SC-001 through SC-007 against `data/` and `results/` (using `quickstart.md` guidelines). **Verification**: Script outputs `results/validation_report.json` with all SCs passing.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately. **T006 depends on T001.2**.
- **Phase 1 (US1)**: Depends on Phase 0 completion.
- **Phase 2 (Pre-Training)**: Depends on Phase 1 (US1) completion - Produces Teacher Distribution. **T048 depends on T021**.
- **Phase 3 (US2)**: Depends on Phase 2 completion - Requires Teacher Distribution. **T025 and T028 depend on T028-ENFORCE**.
- **Phase 4 (US3)**: Depends on Phase 3 completion - Requires Training Output. **T047 depends on T035.1 and T035-SIM; T035-SIM depends on T035.1**.
- **Phase N (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 0 - No dependencies on other stories
- **User Story 2 (P2)**: Depends on Phase 2 (Inference-Only Pass + Averaging) which depends on US1
- **User Story 3 (P3)**: Depends on US2 training output and US1 data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 0 tasks marked [P] (except T006) can run in parallel
- Once Phase 0 completes, US1 (Phase 1) can start
- Once US1 completes, Pre-Training (Phase 2) can start
- Once Pre-Training completes, US2 (Phase 3) can start
- Once US2 completes, US3 (Phase 4) can start

---

## Parallel Example: Phase 0

```bash
# Launch all Phase 0 tasks together (except T006 which needs T001.2):
Task: "Research & Setup (Structure) (T001.1)"
Task: "Research & Setup (Feasibility) (T001.2)"
Task: "Project Initialization (T002.1)"
Task: "Linting Configuration (T002.2)"
# T006 (Power Analysis) must wait for T001.2 (Feasibility) to complete
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research
2. Complete Phase 1: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add Phase 2 (Inference + Averaging) → Test independently
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 together
2. Once Phase 0 is done:
 - Developer A: User Story 1
 - Developer B: Pre-Training Infrastructure (Phase 2) - *after US1 completes*
 - Developer C: User Story 2 - *after Phase 2 completes*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except T006 which needs T001.2)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data loading tasks must use streaming or strict sampling; never load full dataset into RAM.
- **No Fabrication**: If real data fetch fails, the script must raise an error; never fallback to synthetic data.
- **CPU Constraints**: Training loop must be optimized for CPU; use small models (DistilBERT/TinyLlama) and partial fine-tuning if necessary.
- **Timeout**: A hard timeout of 5.5 hours must be enforced via `signal_handler.py` (T028-ENFORCE) and logged (T028). T028-ENFORCE must run before training.
- **Human Proxy**: FR-015 requires a deterministic simulation (T035-SIM) scoring against a generated reference subset (T035.1) to satisfy Reproducibility (Constitution I). Manual recruitment is replaced by simulation. Justification: CI reproducibility. Fallback: Manual data injection if simulation is rejected.
- **Power Analysis**: Must be performed AFTER research feasibility (T001.2) but BEFORE data collection (T015) to validate experimental design; T046 calculates observed power post-experiment and is mandatory for the final report.
- **Teacher Distribution**: Must be computed via Inference-Only Pass (T021) and Averaging Logic (T048) before training begins. T048 explicitly depends on T021 and must use streaming aggregation.
- **Context Simulation**: T017 includes a strict fallback (exclude after N=10 retries) to prevent infinite loops.
- **Streaming**: T021 must process in batches of 50 and stream to JSONL to prevent OOM.
- **Linting**: T002.2 must create explicit `.ruff.toml` and `pyproject.toml` files.
- **Atomization**: T001 split into T001.1 (Structure) and T001.2 (Feasibility); T017 split into T017 (Sampling) and T017.1 (Reporting); T028 split into T028-ENFORCE (Enforcement) and T028 (Logging); T035 split into T035.1 (Reference) and T035-SIM (Simulation).