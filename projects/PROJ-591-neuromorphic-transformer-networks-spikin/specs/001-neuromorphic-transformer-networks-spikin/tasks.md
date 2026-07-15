# Tasks: Neuromorphic Transformer Networks: Spiking Neural Dynamics in Language Models

**Input**: Design documents from `/specs/591-neuromorphic-transformer-spiking/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-591-neuromorphic-transformer-networks-spikin/`)
- [X] T002 Initialize Python project with `requirements.txt` (torch, snnTorch, codecarbon, datasets, scikit-learn, pandas, numpy)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003.5 [P] **CRITICAL PLAN UPDATE**: Update `plan.md` (Complexity Tracking section) to resolve the contradiction between the current "Unpaired Statistical Design" claim and `spec.md` FR-009 which mandates **paired** t-tests. The plan MUST be updated to reflect "Paired Statistical Design" using matching random seeds for baseline and spiking models to enable statistical pairing. If this is not done, the project will fail the FR-009 requirement.
- [X] T004 Implement `code/data/dataset_loader.py` to download WikiText-2. **Primary Source**: Use `datasets.load_dataset('wikitext', 'wikitext-2-raw-v1')` (HuggingFace) as the canonical source per Constitution Principle I. **Fallback**: If HF fails, use `https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-v1.zip` with 3 retry attempts. **Data Hygiene**: Compute SHA-256 checksum of the downloaded data and record it in `state/projects/PROJ-591-neuromorphic-transformer-networks-spikin.yaml` (Constitution Principle III).
- [X] T005 Implement `code/models/baseline_transformer.py` for a -layer, 4-head Transformer (~2M params) with CPU-only enforcement.
- [X] T006 Implement `code/models/spiking_transformer.py` replacing feed-forward layers with LIF neurons (snnTorch) using **surrogate-gradient learning** (FR-005). **Constitution Principle VII**: Must include a verification function that asserts surrogate-gradient learning produces non-NaN gradients on a mini-batch.
- [X] T007 Implement `code/metrics/energy_logger.py` wrapping `codecarbon` with wall-clock fallback and "estimated" flag logic.
- [X] T008 Implement `code/metrics/temporal_coding.py` to compute inter-spike interval variance, bits/spike, and spike train synchrony.
- [X] T009 Create `code/tests/test_lif_dynamics.py` to verify LIF membrane potential update rules.
- [X] T010 Create `code/tests/test_training_loop.py` to verify CPU execution and early stopping logic.

---

## Phase 3: User Story 1 - Baseline Transformer Training and Evaluation (Priority: P1) 🎯 MVP

**Goal**: Train a conventional 2-layer, 4-head transformer on WikiText-2 and measure validation perplexity as the performance baseline.

**Independent Test**: Can be fully tested by training the baseline transformer for minimum 3 epochs (with early stopping if validation loss plateaus) on WikiText-2 and verifying that validation perplexity is recorded and falls within expected ranges for this architecture size.

### Implementation for User Story 1

- [X] T012 [US1] Implement perplexity calculation in `code/metrics/perplexity.py` and log to CSV after each epoch.
- [X] T013 [US1] Implement baseline training loop in `code/main.py` (seeds 1-5, batch size 32, lr 1e-3). **Signature**: `def train_baseline(seed: int) -> MetricRecord`. **Output**: Save results to `data/processed/baseline_metrics.csv` with columns: `seed`, `epoch`, `perplexity`, `energy_per_token_kWh`, `wall_clock_time`. **Requirement**: Must use the same random seed configuration as the spiking model (T017) to enable paired testing (FR-009).
- [X] T014 [US1] {{claim:c_96b50f74}} <!-- ATOMIZE: requested -->
- [X] T015 [US1] Add random seed configuration (multiple seeds) and store results in `data/processed/baseline_metrics.csv`. <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Spiking Transformer Implementation and Energy Measurement (Priority: P2)

**Goal**: Replace feed-forward sub-layers with leaky-integrate-and-fire (LIF) neurons using snnTorch, train with surrogate-gradient learning, measure computational cost via codeCarbon, and measure temporal coding characteristics.

**Independent Test**: Can be fully tested by training the spiking transformer variant and verifying that (i) LIF neurons are active during forward passes, (ii) spike timing metrics are recorded, (iii) computational cost is logged per token, and (iv) perplexity is computed for comparison.

### Implementation for User Story 2

- [X] T017 [US2] Implement spiking training loop in `code/main.py` (multiple seeds, LIF neurons, surrogate gradients). **Merged Logic**: Integrate zero-spike detection logic (FR-006 edge case) as a blocking condition within the training loop. If >50% neurons silent for 3 epochs, raise `TrainingTerminationError`, log warning "WARNING: Zero-spike detection triggered", and save diagnostic report to `data/logs/zero_spike_report.json`. **Requirement**: Must use the **exact same random seeds** as the baseline model (T013) to enable paired testing (FR-009). **Output**: Save results to `data/processed/spiking_metrics.csv` with columns: `seed`, `epoch`, `perplexity`, `energy_per_token_kWh`, `wall_clock_time`, `temporal_coding_metrics` (JSON string).
- [X] T018 [US2] Integrate `code/metrics/energy_logger.py` to log energy-per-token (kWh) with fallback to wall-clock time.
- [X] T019 [US2] Integrate `code/metrics/temporal_coding.py` to record ISI variance, bits/spike, and synchrony during validation.
- [X] T020 [US2] Save spiking results to `data/processed/spiking_metrics.csv` with explicit "estimated" flag for energy if codecarbon fails. <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Performance-Computational Cost Trade-off Reporting (Priority: P3)

**Goal**: Perform paired t-tests comparing perplexity and energy-per-token across seeds for baseline vs. spiking models, apply multiple-comparison correction, perform sensitivity analysis on energy-reduction thresholds, and report the trade-off.

**Independent Test**: Can be fully tested by running the statistical analysis script on the collected metrics and verifying that t-test results, p-values, confidence intervals, and sensitivity sweep results are computed and saved.

### Implementation for User Story 3

- [X] T022 [US3] Implement paired t-tests) in `code/analysis/statistical_tests.py` comparing baseline vs. spiking metrics. **Requirement**: Must use the **same random seed** for both baseline and spiking runs to enable paired testing (per FR-009). **Implementation**: Must read `data/processed/baseline_metrics.csv` and `data/processed/spiking_metrics.csv`, match rows by `seed`, and perform paired t-tests on `perplexity` and `energy_per_token_kWh`.
- [X] T023 [US3] Apply Bonferroni/Holm-Bonferroni correction for multiple hypothesis testing (perplexity + energy).
- [X] T024 [US3] Implement sensitivity analysis sweep over thresholds {0.20, 0.25, 0.30, 0.35} to calculate FP/FN rates (ground truth: ≥30% reduction). **Output**: Save sensitivity curves and rates to `data/results/sensitivity_analysis.csv`.
- [X] T025 [US3] Generate comparison report in `data/results/statistical_analysis_report.md` including temporal coding comparisons.
- [X] T026 [US3] Create visualization script `code/analysis/plots.py` for sensitivity curves and trade-off plots.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T027 [P] Documentation updates in `docs/` including the "CPU Proxy" caveat for energy metrics
- [X] T028 Code cleanup and refactoring <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T029 [P] Performance optimization across all stories (ensure <6h total runtime) <!-- ATOMIZE: requested -->
- [X] T030 [P] Additional unit tests in `code/tests/unit/` <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->
- [X] T031 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST run on CPU-only CI (limited core count, constrained RAM). No GPU, no 8-bit quantization, no large LLMs.
- **Plan Contradiction Note**: T003.5 explicitly addresses the contradiction between `plan.md` and `spec.md` regarding statistical design.
- **Data Source Note**: T004 uses HuggingFace as the primary source per Constitution Principle I, with S3 as a documented fallback.
- **Statistical Design Note**: T013 and T017 must use matching seeds to enable paired t-tests in T022.
- **Scope Note**: Tasks T029-T033 from the previous draft have been removed as they implemented unrequested features not present in `spec.md`.