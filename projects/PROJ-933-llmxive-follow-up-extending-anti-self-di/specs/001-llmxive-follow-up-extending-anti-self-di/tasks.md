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

- [X] T001.1A [P] **Research & Setup (Structure)**: Create project directory structure (`mkdir -p projects/PROJ-933-llmxive-followup-extending-anti-self-di/code/{data,models,analysis,config} data/ results/`). **Verification**: Run `ls -R projects/...` to confirm all directories exist. (FR-001, Plan Phase 0 & 1).
- [X] T001.1B [P] **Research & Setup (Quickstart)**: Generate `quickstart.md` with run instructions. **Verification**: Verify `quickstart.md` exists and is readable. (Plan Phase 0 & 1).
- [X] T001.2A [P] **Research & Setup (Feasibility)**: Generate `research.md` confirming dataset feasibility using *literature-based* effect size estimates (d=0.5). **Verification**: Verify `research.md` exists and contains effect size justification. (FR-013, Plan Phase 0 & 1).
- [X] T001.2B [P] **Research & Setup (Data Model)**: Generate `data-model.md` defining schemas for prompts, rationales, and splits. **Verification**: Verify `data-model.md` exists and covers all entities. (Plan Phase 0 & 1).
- [X] T001.2C [P] **Research & Setup (Contracts)**: Generate `contracts/*.schema.yaml` (dataset, training, analysis). **Verification**: Verify schema files exist and are valid YAML. (Plan Phase 0 & 1).
- [X] T002.1 [P] **Project Initialization**: Initialize `requirements.txt` (pinned versions), `config/settings.yaml` (seeds, hyperparameters, timeout). **Verification**: Run `pip install -r requirements.txt` to confirm no errors.
- [X] T002.2 [P] **Linting Configuration**: Create explicit configuration files: `.ruff.toml` and `pyproject.toml` sections for black/ruff. **Verification**: Run `ruff check.` to confirm config loads. (FR-001, Plan Phase 0).

### Sub-tasks for T001.2A (Feasibility)
- [X] T006 [US0] **Pre-Study Power Analysis**: Perform power analysis in `code/analysis/statistical_test.py` to confirm N ≥ 30 for power ≥ 0.8 using literature-based effect size (d=0.5). **Verification**: Script outputs `results/pre_study_power.json` with `power >= 0.8`. **Depends on T001.2A** (must run after feasibility check but BEFORE data download T015). (FR-013, SC-007).

**Checkpoint**: Verify `results/pre_study_power.json` exists and contains `power >= 0.8`. **Phase 1 cannot start until T006 completes.**

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

### Context Simulation (Atomized)

- [ ] T017-A [US1] **Context Simulator (Filtering)**: Implement logic in `code/data/preprocess.py` to pre-filter prompts with <4 total traces (FR-016). **Verification**: Script outputs `data/filtered_prompts.jsonl` and logs excluded prompt IDs. (FR-002, Edge Case).
- [ ] T017-B [US1] **Context Simulator (Sampling)**: Implement logic in `code/data/preprocess.py` to randomly sample 1 rationale as "privileged context" $c$ and save to `data/context_splits.json`. **Logic**:
 1. **Sampling**: Randomly select 1 rationale.
 2. **Independence Check**: If the selected rationale is identical to any of the remaining (unselected) rationales, re-sample up to N=10 times.
 3. **Exclusion**: If identical rationales persist after N=10 attempts, exclude the prompt.
 **Output Schema**: `data/context_splits.json` lines: `{"prompt_id": str, "privileged_rationale_id": str, "unselected_rationale_ids": [str,...], "excluded": bool}`.
 **Verification**: Verify `data/context_splits.json` exists, schema is valid, and count of non-excluded prompts >= 30. (FR-002, Edge Case).
- [ ] T017-C [US1] **Context Simulator (Logging & Reporting)**: Implement logging of excluded prompts to `data/excluded_prompts.log` and statistics reporter (prompt count, avg tokens) to `data/context_stats.json`. **Depends on T017-B**. (FR-002, Edge Case).

### Post-Filter Verification

- [ ] T017.2 [US1] **Post-Filter Power Verification**: Load `data/context_splits.json`, count valid prompts (N). **Logic**: If N < 30, raise `ValueError` and halt the build. Output `results/final_sample_size.json`. **Verification**: Script exits with code 0 only if N >= 30. **Depends on T017-B**. (SC-007, FR-013).

**Checkpoint**: Verify `data/context_splits.json` exists and contains valid split data for all prompts. **T017.2 must pass before Phase 2 begins.**

---

## Phase 2: Pre-Training Infrastructure (Blocking for US2)

**Purpose**: Execute Inference-Only Pass, compute Teacher Distribution, and verify model feasibility.

- [ ] T020-A [US2] **Inference-Only Pass (Implementation)**: Implement `code/models/inference_only.py` to load `data/context_splits.json` and compute Teacher Distribution (average logit distribution over all unselected rationales) **using streaming and chunked/batched inference**. **Logic**:
 1. Load prompts from `data/context_splits.json`.
 2. For each prompt, run inference on all `unselected_rationale_ids`.
 3. Stream logits to `data/teacher_logits_raw.jsonl` immediately after each batch (batch size 50) to prevent OOM.
 **Output Schema**: `data/teacher_logits_raw.jsonl` lines must contain: `{"prompt_id": str, "rationale_id": str, "logits": [float,...], "tokens": [str,...]}`.
 **Verification**: Verify `data/teacher_logits_raw.jsonl` exists, schema is valid (check first 5 lines), and line count matches expected total unselected rationales. (FR-014, FR-003).
- [ ] T020-B [US2] **Inference-Only Pass (Execution)**: Execute the inference pass defined in T020-A on the full dataset. **Algorithm**: Stream logits to `data/teacher_logits_raw.jsonl` (append mode) immediately after each batch to prevent OOM. **Do NOT load all logits into RAM.** **Verification**: Verify file size is reasonable and no OOM occurs. (FR-014, Plan Complexity Tracking).
- [ ] T021 [US2] **Stream Finalization & Manifest Generation**: Implement logic in `code/models/inference_only.py` to explicitly close the file handle for `data/teacher_logits_raw.jsonl`, flush buffers, and generate a manifest file `data/teacher_logits_raw.jsonl.manifest` containing the file size, line count, and SHA256 checksum. **Verification**: Verify `data/teacher_logits_raw.jsonl.manifest` exists and contains valid metadata. **Depends on T020-B**. (FR-014, FR-003).
- [ ] T022 [US2] Implement validation to ensure `data/teacher_logits_raw.jsonl` is complete and matches expected prompt count. **Logic**:
 1. Load `data/context_splits.json` to calculate expected total unselected rationales.
 2. Read `data/teacher_logits_raw.jsonl.manifest` (from T021) to get line count.
 3. Assert manifest line count == expected count.
 4. Validate schema of first 5 lines of the raw file.
 **Output**: `results/validation_report.json` with `status: "pass" | "fail"`, `expected_count`, `actual_count`.
 **Verification**: Script exits with code 0 on pass, 1 on fail. (FR-014, FR-003). **Depends on T021**.
- [ ] T048-A [US2] **Teacher Distribution Averaging (Computation)**: Implement averaging logic in `code/models/inference_only.py` to compute the "Teacher Distribution" (average of raw logits) from `data/teacher_logits_raw.jsonl` **via streaming aggregation (chunked re-reading)**. **Logic**:
 1. Re-read `data/teacher_logits_raw.jsonl` in fixed-size chunks (e.g., 1000 lines).
 2. Maintain a running sum of logits and a count of rationales per prompt.
 3. Compute average logits per prompt after processing all chunks.
 4. Save to `data/teacher_distribution.json`.
 **Verification**: Verify `data/teacher_distribution.json` exists and schema matches `contracts/training_output.schema.yaml`. **Depends on T022** (FR-003, FR-014).
- [ ] T048-B [US2] **Teacher Distribution Averaging (Validation)**: Validate the resulting distribution against the schema and check for NaN/Inf values. **Verification**: Script exits with code 0 on pass. **Depends on T048-A**. (FR-003, FR-014).
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

- [X] T028-ENFORCE-LOGIC [US2] **Hard Timeout Enforcer (Logic)**: Implement `code/models/signal_handler.py` with a signal handler (SIGALRM) that raises `SystemExit` with a specific "timeout" status on a predefined time limit. **Verification**: Unit test confirms handler raises `SystemExit` after a short mock timeout (e.g., 1 second). (FR-007, SC-004).
- [X] T028-ENFORCE-INVOKE [US2] **Hard Timeout Enforcer (Integration)**: Integrate `signal_handler.py` into `main.py` to wrap the training execution. **Verification**: Script exits with an error code after a simulated duration of 5.5h (simulated via config). (FR-007, SC-004).
- [X] T025 [P] [US2] Implement `code/models/anti_sd_loop.py` custom PyTorch training loop with token-level gradient inversion (FR-008). **Must be invoked *within* the T028-ENFORCE signal handler context.** **Depends on T028-ENFORCE-LOGIC and T028-ENFORCE-INVOKE**. **Verification**: Script outputs `results/training_trajectory.json` with loss curves.
- [X] T026 [US2] Implement JS divergence calculation between student and the averaged Teacher Distribution (from T048) using PMI (FR-003). **Verification**: Unit test confirms JS divergence calculation.
- [X] T027 [US2] Implement gradient ascent logic for AntiSD condition and gradient descent for standard condition (FR-004). **Verification**: Unit test confirms gradient direction.
- [X] T028 [US2] **Timeout & Logging**: Implement logging logic to capture `status` ("timeout" or "completed") and `elapsed_time` to `results/training_metrics.json`. **Depends on T028-ENFORCE-LOGIC** (must log the status set by the enforcer). **Verification**: Verify `results/training_metrics.json` contains `status` and `elapsed_time`. (FR-007, SC-004).
- [ ] T029 [US2] **Trajectory Generation**: Implement logic to generate **K=10 trajectories per prompt** for evaluation. **Logic**:
 1. Load trained model from T025.
 2. For each prompt in the dataset, generate K=10 distinct trajectories using temperature sampling.
 3. Save to `results/trajectories.jsonl` with metadata: `{"prompt_id": str, "trajectory_id": int, "tokens": [str,...]}`.
 **Verification**: Verify `results/trajectories.jsonl` exists and contains exactly K=10 trajectories per prompt. **Depends on T025**. (FR-008, SC-002).
- [X] T030 [US2] Implement memory monitoring using `psutil` to assert peak RAM < 6.5 GB during training; output `results/memory_log.json` with peak values. **Verification**: Verify `results/memory_log.json` exists and `peak_ram < 6.5`. (SC-005)

**Checkpoint**: Verify `results/training_trajectory.json` and `results/training_metrics.json` exist.

---

## Phase 4: User Story 3 - Diversity Measurement, Quality Validation, and Statistical Analysis (Priority: P3)

**Goal**: Compute BLEU/semantic similarity, validate with Human Evaluation Proxy (Mock), and run Wilcoxon signed-rank tests.

**Independent Test**: Compute metrics against unselected rationales, output Wilcoxon p-value, effect size, and correlation coefficient.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Unit test for BLEU and semantic similarity calculation in `code/models/test_metrics.py`
- [X] T032 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `code/analysis/test_statistical_test.py`

### Implementation for User Story 3

- [ ] T035-REF-SAMPLE [US3] **Generate Reference Subset**: Implement script to sample and save a "human-annotated subset" of the *original* unselected rationales (FR-010). **Logic**:
 1. Randomly select N=100 unique prompts from `data/context_splits.json`.
 2. Extract the **original unselected rationales** for these prompts.
 3. Save to `data/human_reference_subset.json`.
 **Output Schema**: `data/human_reference_subset.json` must contain `[{ "prompt_id": str, "rationale_id": str, "rationale_text": str }]`. **NO SCORES ARE GENERATED HERE**.
 **Verification**: Verify `data/human_reference_subset.json` exists and contains exactly N=100 entries. (FR-010, FR-015).
- [ ] T035-MOCK-PROTOCOL [US3] **Mock Scoring Protocol**: Define the "Mock Human Proxy" protocol in `docs/mock_eval_protocol.md` (FR-015). **Logic**:
 1. Describe the scoring function: Use a frozen `sentence-transformers` model to compute semantic similarity between generated trajectories and the `human_reference_subset`.
 2. Define the scoring scale: Map similarity scores to a 1-5 Likert scale (e.g., 0.0-0.2 -> 1, 0.2-0.4 -> 2, ...).
 3. State that this is a deterministic, reproducible proxy for human consensus.
 **Verification**: Verify `docs/mock_eval_protocol.md` exists and details the scoring logic. (FR-010, FR-015).
- [ ] T035-MOCK-GENERATE [US3] **Mock Scoring Execution (Automated)**: Implement script to generate `data/human_scores.csv` automatically using the protocol from T035-MOCK-PROTOCOL. **Logic**:
 1. Load `results/trajectories.jsonl` (from T029) and `data/human_reference_subset.json` (from T035-REF-SAMPLE).
 2. For each trajectory, compute semantic similarity to the reference set.
 3. Map similarity to a 1-5 Likert score (coherence and consensus).
 4. Simulate multiple "raters" by adding small deterministic noise to the base score.
 5. Output `data/human_scores.csv` (format: `trajectory_id, rater_id, coherence_score, consensus_score`).
 **Verification**: Verify `data/human_scores.csv` exists and contains scores for all trajectories from T029. **Depends on T035-REF-SAMPLE and T035-MOCK-PROTOCOL**. (FR-010, FR-015, SC-001, SC-006).
- [ ] T035-MOCK-VALIDATE [US3] **Mock Score Validation (Gate)**: Implement script to verify `data/human_scores.csv` exists and matches the expected schema (`trajectory_id, rater_id, coherence_score, consensus_score`). **Logic**: If file is missing or schema is invalid, raise `ValueError` and halt. **Verification**: Script exits with code 0 on valid CSV. **Depends on T035-MOCK-GENERATE**. (FR-010, FR-015).
- [X] T047 [US3] **Human Score Ingest (Code)**: Implement parser in `code/analysis/human_score_ingest.py` to read `data/human_scores.csv` (from T035-MOCK-VALIDATE) and `data/human_reference_subset.json` (from T035-REF-SAMPLE) to compute the final "Human Evaluation Proxy Score" (FR-010). **Logic**:
 1. Load CSV and JSON.
 2. Aggregate scores (median of coherence/consensus) per trajectory.
 3. Output `results/human_proxy_scores.json`.
 **Verification**: Verify `results/human_proxy_scores.json` exists and contains aggregated scores. **Depends on T035-MOCK-VALIDATE**. (FR-010, FR-015).
- [X] T033 [P] [US3] Implement pairwise BLEU and semantic similarity calculation in `code/models/metrics.py` against unselected rationales (FR-005). **Verification**: Unit test confirms BLEU calculation.
- [X] T034 [US3] Implement deliberation token counter (e.g., "Wait", "However") in `code/models/metrics.py` (FR-009). **Verification**: Unit test confirms token counting.
- [X] T036 [US3] Implement Pearson correlation calculation between deliberation token frequency and Human Evaluation Proxy Score (FR-011). **Verification**: Unit test confirms correlation calculation.
- [X] T037 [US3] Implement Wilcoxon signed-rank test comparing AntiSD vs. standard self-distillation on diversity and quality metrics (FR-006, FR-017). **Verification**: Unit test confirms Wilcoxon test.
- [X] T046 [US3] **Post-Hoc Power Analysis**: Implement post-hoc power analysis in `code/analysis/statistical_test.py` to calculate observed statistical power (1-β) based on effect size (FR-018). **Verification**: Script outputs `results/observed_power.json`. **Mandatory**: This output is a required field in the final report. **Depends on T037** (requires final test results).
- [X] T038 [US3] **Final Report Generation**: Generate final analysis report with p-values, effect sizes, correlation coefficients, and **observed statistical power** as a required field (FR-013, FR-018, SC-001, SC-002, SC-003). **Verification**: Verify `results/final_report.md` contains all required fields. **Depends on T046**.
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
- [X] T045 [P] Run validation script to verify SC-001 through SC-007 against `data/` and `results/` (using `quickstart.md` guidelines). **Verification**: Script outputs `results/validation_report.json` with all SCs passing. **Must verify human scores are real (not simulated) before validating SC-006**.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately. **T006 depends on T001.2A**.
- **Phase 1 (US1)**: Depends on Phase 0 completion. **T015 depends on T006**. **T017-A, T017-B, T017-C depend on T016**. **T017.2 depends on T017-B**.
- **Phase 2 (Pre-Training)**: Depends on Phase 1 (US1) completion - Produces Teacher Distribution. **T020-A depends on T017-B**. **T020-B depends on T020-A**. **T021 depends on T020-B**. **T022 depends on T021**. **T048-A depends on T022**. **T048-B depends on T048-A**.
- **Phase 3 (US2)**: Depends on Phase 2 completion - Requires Teacher Distribution. **T025 and T028 depend on T028-ENFORCE-LOGIC and T028-ENFORCE-INVOKE** (T028-ENFORCE must be active/wrapping T025). **T029 depends on T025**.
- **Phase 4 (US3)**: Depends on Phase 3 completion - Requires Training Output. **T035-REF-SAMPLE depends on T017-B**. **T035-MOCK-GENERATE depends on T035-REF-SAMPLE and T035-MOCK-PROTOCOL**. **T035-MOCK-VALIDATE depends on T035-MOCK-GENERATE**. **T047 depends on T035-MOCK-VALIDATE**. **T046 depends on T037**. **T038 depends on T046**.
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
# Launch all Phase 0 tasks together (except T006 which needs T001.2A):
Task: "Research & Setup (Structure) (T001.1A)"
Task: "Research & Setup (Quickstart) (T001.1B)"
Task: "Research & Setup (Feasibility) (T001.2A)"
Task: "Research & Setup (Data Model) (T001.1B)"
Task: "Research & Setup (Contracts) (T001.2C)"
Task: "Project Initialization (T002.1)"
Task: "Linting Configuration (T002.2)"
# T006 (Power Analysis) must wait for T001.2A (Feasibility) to complete
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

- [P] tasks = different files, no dependencies (except T006 which needs T001.2A)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data loading tasks must use streaming or strict sampling; never load full dataset into RAM.
- **No Fabrication**: If real data fetch fails, the script must raise an error; never fallback to synthetic data.
- **CPU Constraints**: Training loop must be optimized for CPU; use small models (DistilBERT/TinyLlama) and partial fine-tuning if necessary.
- **Timeout**: A hard timeout of 5.5 hours must be enforced via `signal_handler.py` (T028-ENFORCE-LOGIC) and logged (T028). T028-ENFORCE must be active (wrapping) during T025 execution.
- **Human Proxy**: FR-015 requires a reproducible "Human Evaluation Proxy". **NO MANUAL HUMAN INTERVENTION** is allowed in CI. T035-MOCK-GENERATE implements a deterministic scoring function (sentence-transformer similarity) to generate scores automatically. T035-MOCK-PROTOCOL documents this proxy. T035-MOCK-VALIDATE ensures the CSV is valid. T047 ingests the resulting CSV and computes the final score. T035-REF-SAMPLE provides the reference set (original rationales).
- **Power Analysis**: Must be performed AFTER research feasibility (T001.2A) but BEFORE data collection (T015) to validate experimental design; T017.2 verifies the final sample size after filtering; T046 calculates observed power post-experiment and is mandatory for the final report.
- **Teacher Distribution**: Must be computed via Inference-Only Pass (T020-A/B), Finalization (T021), and Averaging Logic (T048-A/B) before training begins. T048 explicitly depends on T022 and must use streaming aggregation (chunked re-reading).
- **Context Simulation**: T017-A/B/C includes a strict fallback (exclude after N=10 retries) to prevent infinite loops.
- **Streaming**: T020-B must process in batches of 50 and stream to JSONL to prevent OOM. T048-A must re-read in chunks (1000 lines) to prevent OOM.
- **Linting**: T002.2 must create explicit `.ruff.toml` and `pyproject.toml` files.
- **Atomization**: T001 split into T001.1A/B; T017 split into T017-A/B/C; T020 split into T020-A/B; T028 split into T028-ENFORCE-LOGIC/INVOKE and T028; T035 split into T035-REF-SAMPLE, T035-MOCK-PROTOCOL, T035-MOCK-GENERATE, T035-MOCK-VALIDATE. T048 split into T048-A/B.
- **Dependencies**: T006 depends on T001.2A. T017.2 depends on T017-B. T020-A depends on T017-B. T020-B depends on T020-A. T021 depends on T020-B. T022 depends on T021. T048-A depends on T022. T025 depends on T028-ENFORCE-LOGIC/INVOKE (active). T029 depends on T025. T035-REF-SAMPLE depends on T017-B. T035-MOCK-GENERATE depends on T035-REF-SAMPLE and T035-MOCK-PROTOCOL. T035-MOCK-VALIDATE depends on T035-MOCK-GENERATE. T047 depends on T035-MOCK-VALIDATE. T046 depends on T037. T038 depends on T046.