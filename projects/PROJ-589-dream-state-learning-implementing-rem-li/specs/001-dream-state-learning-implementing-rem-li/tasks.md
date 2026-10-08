# Tasks: Dream-State Learning: Implementing REM-like Consolidation in Language Models

**Input**: Design documents from `/specs/001-dream-state-learning-implementing-rem-li/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 Create project structure per implementation plan: create directories `code/`, `tests/`, `data/`, `data/raw/`, `data/checkpoints/`, `data/results/`, `data/logs/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T001b [P] Initialize Python package files: Create `__init__.py` in all created directories (`code/`, `tests/`, `data/`, `data/checkpoints/`, `data/results/`, `data/logs/`, `tests/unit/`, `tests/integration/`, `tests/contract/`) to ensure they are recognized as Python packages. Note: `data/raw/` is excluded as it stores non-Python data files and should not contain `__init__.py`.
- [X] T002a [P] Initialize Python project file: Create `code/requirements.txt` with base dependencies (torch, transformers, datasets, scikit-learn, accelerate, pytest, scipy)
- [X] T002b [P] Pin Python versions: Update `code/requirements.txt` with exact version pins (e.g., `torch==2.0.0`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for hyperparameters, paths, seed management, and CPU-only device enforcement
- [X] T005 [P] Implement `code/utils/memory_monitor.py` to track peak RSS via `/proc/self/status` and enforce hard abort (FR-005)
- [X] T006 [P] Implement `code/data/loader.py` to download GLUE/SuperGLUE subsets via `datasets` library with SHA-256 checksum verification; MUST abort execution and raise `RuntimeError` if checksum mismatch occurs
- [X] T007 Create `code/models/__init__.py` and initialize DistilBERT/TinyLlama model loader (CPU-optimized, default precision)
- [X] T008 Implement `code/utils/logger.py` for structured logging to `data/logs/` and stdout
- [X] T009 Setup `tests/contract/` schema validation for `training_config.schema.yaml` and `evaluation_result.schema.yaml`
- [X] T017a [P] [US1] Define `LowEntropyWarning` exception: Create `code/utils/exceptions.py` and define `class LowEntropyWarning(Exception):...` to be used in T017b.
- [X] T057 [P] [Spec] Ratify DAE Architecture: Update `spec.md` FR-002 to explicitly mandate "Denoising Autoencoder (DAE) on masked real data" as the canonical implementation, replacing "generative replay" language. This task MUST complete before T015.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Wake/Dream Training Cycle (Priority: P1) 🎯 MVP

**Goal**: Implement the alternating wake/dream training loop with DAE-based consolidation, warm-up, and entropy checks.

**Independent Test**: Run a training job on a single GLUE subset, verify alternating phases, entropy checks, and checkpoint output.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for warm-up logic (no dream phase in the initial steps) in `tests/unit/test_trainer.py`
- [X] T011 [P] [US1] Unit test for entropy calculation and low-entropy retry logic in `tests/unit/test_trainer.py`
- [X] T011b [P] [US1] Unit test for `LowEntropyWarning` exception: Verify that `LowEntropyWarning` is raised when retry limit (3) is exhausted in `tests/unit/test_trainer.py`.
- [X] T012 [P] [US1] Integration test for a multi-step wake/dream cycle on a tiny dataset in `tests/integration/test_training_loop.py`

### Implementation for User Story 1

- [X] T013a [P] [US1] Define masking constant: Define `MASK_RATE = 0.15` constant in `code/config.py`.
- [X] T013b [P] [US1] Implement masking logic: Create `code/data/augment.py` and implement the random token masking function using the `MASK_RATE` constant from config, consistent with BERT masking strategies.
- [X] T014 [P] [US1] Implement `code/models/trainer.py` core loop: Wake phase (standard cross-entropy on real data using `torch.nn.CrossEntropyLoss` and `torch.optim.AdamW`), including explicit data batching strategy (e.g., `DataLoader` with `batch_size` from config).
- [X] T015 [US1] Implement `code/models/trainer.py` Dream phase: **DEPENDS ON T057 (Spec Ratification)**. Implement DAE reconstruction: Generate masked inputs using T013b (MASK_RATE=0.15), reconstruct original tokens (DAE loss using `torch.nn.CrossEntropyLoss`), enforce a multi-to-one wake-to-dream step ratio via a `DreamScheduler` class. **Requirement**: Accept `temperature` parameter from config for sampling. **Requirement**: Log per-sample reconstruction error to `data/logs/` for downstream metrics.
- [X] T016 [US1] Implement `code/models/trainer.py` Warm-up protocol: Skip dream phase for an initial period to ensure initial representation stability. Do not raise an error; simply delay the phase.
- [X] T017b [US1] Implement `code/models/trainer.py` Entropy check: Detect low-entropy outputs (<0.5 bits per token), calculated as average of -p*log2(p) per token (excluding padding tokens, base-2 log), trigger retry up to 3 times with local retry counter increment. **Requirement**: If retries are exhausted, discard the batch, log the 'discard batch' action to `data/logs/`, and raise the `LowEntropyWarning` exception defined in T017a.
- [X] T018 [US1] Integrate `memory_monitor` (T005) into the training loop to abort and save checkpoint on OOM
- [X] T019 [US1] Add logging for phase transitions (Wake/Dream), entropy metrics, and warm-up status (depends on T008). **Requirement**: Explicitly log phase transitions and metrics to satisfy FR-005 (audit logging) and FR-001 (phase tracking). Must output structured JSON logs for auditability.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Evaluation Baseline (Priority: P2)

**Goal**: Run a parallel continuous-training baseline and perform statistical comparison.

**Independent Test**: Run baseline script on same seed/data, compare final loss/accuracy, output statistical p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for statistical significance calculation (paired t-test) in `tests/unit/test_metrics.py`
- [X] T021 [P] [US2] Integration test comparing two dummy models in `tests/integration/test_evaluation.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/eval/metrics.py` for few-shot accuracy calculation on held-out GLUE subsets. **Requirement**: Protocol must evaluate on the single held-out few-shot task (singular) as per SC-002, not a multi-shot sweep.
- [X] T023 [US2] Implement `code/models/trainer.py` Baseline mode: Continuous SFT with identical total token count (not just steps) and data tokens as the experimental run
- [X] T024a [US2] Implement `code/main.py` orchestration setup: Logic to orchestrate parallel runs (Experimental vs. Baseline) with same seeds (depends on T014-T017 and T023 implementation)
- [X] T024b [US2] Implement `code/main.py` result aggregation: Logic to collect and aggregate results from parallel runs (depends on T024a). **Note**: T025a depends on T024b.
- [X] T025a [US2] Implement data aggregation: Prepare the list of paired accuracy results across 5 random seeds from T023 and T024b for statistical analysis. Input: list of accuracy floats per model, PAIRED BY SEED INDEX.
- [X] T025b [US2] Implement statistical analysis: Compute accuracy difference and **paired t-test** (`scipy.stats.ttest_rel`, α=0.05) p-value across 5 seeds (per spec.md SC-002 and Constitution Principle VII).
- [X] T025c [US2] Implement result formatting: Format the statistical output (p-value, effect size) for the final report.
- [X] T026 [US2] Implement result reporting: Save comparative report to `data/results/comparison_report.json` (depends on T025c)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource Constraint Verification (Priority: P3)

**Goal**: Ensure the pipeline runs within GitHub Actions free-tier limits (limited CPU, constrained RAM, 6h).

**Independent Test**: Run full pipeline on local resource-limited environment, verify no OOM and time < 5h.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for memory limit logic in `tests/unit/test_memory_monitor.py`
- [X] T030 [P] [US3] Integration test for time limit enforcement in `tests/integration/test_resource_limits.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement `code/main.py` time monitoring and abort logic if wall-clock > 5.5 hours (read `MAX_WALL_CLOCK_HOURS` from `config.py`, raise `TimeLimitExceeded`)
- [X] T032 [US3] Implement `code/main.py` memory monitoring integration with `memory_monitor` (T005) to enforce GB limit
- [X] T033 [US3] Create `code/scripts/verify_feasibility.sh` to run a dry-run with resource limits

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Sensitivity Analysis (Priority: P4)

**Goal**: Sweep temperature hyperparameters as mandated by FR-006 and report variance.

**Independent Test**: Run temperature sweep across a range of values {0.5, 1.0, 1.5, 2.0}, following a grid search protocol, report variance in final accuracy.

### Implementation for User Story 1 (Sensitivity Extension)

- [X] T036a [US1] Implement temperature sweep orchestration: Execute the full training pipeline (US1 + US2 logic) for each temperature value in {0.5, 1.0, 1.5, 2.0} with 5 seeds per temperature value. **Requirement**: Output artifact structure must be `data/results/sweep_{temp}_{seed}.json`. **Requirement**: Statistical analysis (T025b) must be performed per temperature value on its 5 seeds to isolate the variable. **Dependency**: Depends on completion of T015 (Core Loop with temperature param) and T023 (Baseline logic).
- [X] T036b [US1] Implement per-run isolation: RE-INITIALIZE MODEL WEIGHTS, OPTIMIZER STATE, AND RANDOM SEED for each run to ensure state isolation. Collect final accuracy for each run.
- [X] T036c [US1] Implement variance calculation: Compute variance of the final accuracy values across the temperature sweep using `scikit-learn`'s `var` function and save to `data/results/variance_report.json`.
- [X] T037 [US1] Implement reporting logic to save variance_report.json to data/results/ containing variance of final accuracy across temperature sweep (calculated as population variance of the accuracy values) to satisfy SC-005

**Checkpoint**: Sensitivity analysis complete

---

## Phase 7: Review Resolution & Theoretical Rigor (Priority: P2)

**Goal**: Address specific reviewer concerns regarding "Logical Depth," "Salience," and "Evidence of Consolidation" by implementing targeted metrics and selection mechanisms.

**Independent Test**: Verify that the training loop logs "Logical Depth" metrics, uses a salience-based selection for dream samples, and produces a specific "Consolidation Evidence" report comparing error reduction rates.

### Implementation for Review Resolution

- [ ] T061 [US1] Implement Logical Depth Proxy: Modify `code/models/trainer.py` to compute and log a "Logical Depth" proxy during the dream phase. Calculate this as the reduction in reconstruction loss on *held-out masked samples* from the start of the dream phase vs. the end, serving as a proxy for Kolmogorov complexity reduction (addressing von Neumann's critique). Save metrics to `data/logs/logical_depth_metrics.json`.
- [ ] T062 [US1] Implement Salience-Based Replay Selection: Replace random sampling in the dream phase with a salience-weighted selection mechanism. Implement `code/data/salience.py` to score wake-phase samples by gradient norm magnitude or loss surprise, and sample dream inputs proportional to these scores (addressing Turing/Kandel's critique on non-random selection).
- [ ] T063 [US2] Implement Consolidation Evidence Report: Create `code/eval/consolidation_report.py` to generate a specific report comparing error reduction rates. The report must calculate the rate of loss decrease on held-out tasks *before* and *after* the dream phase cycle, explicitly testing the hypothesis that "dreaming" improves performance on previously encountered tasks (addressing Turing's "evidence of useful work" critique).
- [ ] T064 [US1] Implement Metabolic Cost Proxy: Add a `code/utils/metabolic_proxy.py` module that estimates computational "energy" (FLOPs) consumed during wake vs. dream phases. Log the ratio of FLOPs to accuracy gain to address Dyson/Kandel's concern about the cost of consolidation (addressing "biological cost" critique).
- [ ] T065 [P] Update `quickstart.md` and `docs/architecture.md`: Add a section explicitly defining the "Logical Depth" metric and the "Salience" selection algorithm used in T061/T062 to satisfy the "bird/frog" distinction and formalism requirements (addressing Dyson/von Neumann critiques).

**Checkpoint**: Review concerns formally addressed with implemented metrics and selection logic.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T051 [P] Documentation updates in `docs/` and `quickstart.md`
- [X] T052 Code cleanup and refactoring
- [X] T053 Performance optimization (batching, data loading) across all stories
- [X] T054 [P] Additional unit tests (if requested) in `tests/unit/` <!-- ATOMIZE: requested -->
- [X] T055 Security hardening
- [X] T056 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Resolution (Phase 7)**: Depends on US1 (Core Loop) and US2 (Evaluation) completion to calculate metrics
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for model state and training logic
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for full pipeline execution
- **Review Resolution (Phase 7)**: Depends on US1 and US2 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for warm-up logic in tests/unit/test_trainer.py"
Task: "Unit test for entropy calculation in tests/unit/test_trainer.py"

# Launch all implementation for User Story 1 together (after tests):
Task: "Implement code/data/augment.py for DAE masking"
Task: "Implement code/models/trainer.py core loop (Wake/Dream)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story independently (multi-step run, entropy check, warm-up)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Baseline comparison)
4. Add User Story 3 → Test independently → Deploy/Demo (Resource verification)
5. Add Phase 6 (Sensitivity Analysis) → Test independently → Deploy/Demo (Hyperparameter robustness)
6. Add Phase 7 (Review Resolution) → Test independently → Deploy/Demo (Theoretical rigor)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Loop)
 - Developer B: User Story 2 (Evaluation & Baseline)
 - Developer C: User Story 3 (Resource Limits & Feasibility)
 - Developer D: Phase 6 (Sensitivity Analysis)
 - Developer E: Phase 7 (Review Resolution & Metrics)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability to specific user story
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST run on CPU-only CI with a minimal core count and limited RAM.. No GPU, no low-bit quantization, no large models.
- **Data Integrity**: All data must be real (GLUE/SuperGLUE) via `datasets` library. No fake data generation.
- **Statistical Method**: Primary success criterion uses **paired t-test** (per spec.md SC-002) across 5 random seeds.
- **Warm-up**: Hard constraint enforced by skipping the dream phase for a fixed number of steps.
- **Sensitivity**: Protocol defined as grid search over a range of temperature values with multiple seeds per temperature for the sweep.
- **Architecture Note**: Implementation follows the ratified FR-002 (DAE on masked real data) as amended by T057.
- **Removed Scope**: Tasks T040-T045 (Salience, Logical Depth, Metabolic Cost, Multi-shot) were removed as they introduced unauthorized scope and contradicted the spec.
- **Correction**: Phase 7 has been removed. The multi-shot evaluation task (T044) was removed as it contradicted SC-002. The gradient-based selection tasks (T040-T045) were removed as they contradicted FR-002.
- **Review Resolution Added**: Phase 7 (T061-T065) has been re-added specifically to address the "minor_revision" feedback from Turing, Kandel, Dyson, and von Neumann regarding Logical Depth, Salience, and Evidence of Consolidation. These are now mandatory implementation tasks.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T058 Reconcile run-book vs implementation for `code/data_loader.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data_loader.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T059 Reconcile run-book vs implementation for `code/train.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/train.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T060 Reconcile run-book vs implementation for `code/eval.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/eval.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
