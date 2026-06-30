# Tasks: Qwen‑VLA Cross‑Embodiment Transfer Study

**Input**: Design documents from `/specs/qwen-vla-cross-embodiment-transfer/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project structure: Create directories `src/`, `tests/`, `data/`, `scripts/`; Create files `pyproject.toml`, `.gitignore` per implementation plan.
- [X] T002 Initialize Python project with `pyproject.toml` and dependencies (`torch==2.3.0+cpu`, `transformers`, `datasets`, `scipy`, `psutil`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup dataset metadata structure and `data/metadata.yaml` schema for versioning/checksums. **Note**: This task defines the schema only; population occurs after data download.
- [X] T005 [P] Implement base CLI entry point (`src/cli.py`) using `click` with `--ratio` argument support. **Note**: This task implements the argument parser ONLY; aggregation logic and CSV generation for FR-006 are deferred to T025/T027.
- [X] T006 [P] Setup resource monitoring utility (`src/utils/resource_monitor.py`) using `psutil` for RAM/wall-time tracking
- [X] T007 Create base model entities (`src/models/entities.py`) for `DatasetSubset`, `ModelCheckpoint`, `EvaluationResult`
- [X] T008 Configure logging infrastructure with structured JSON output for reproducibility manifest generation
- [X] T009 Setup environment configuration management (`.env` loading, default paths)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cross‑Embodiment Pre‑training & Zero‑Shot Evaluation (Priority: P1) 🎯 MVP

**Goal**: Ingest filtered Open X‑Embodiment data, train a frozen Qwen2‑VL‑2B + DiT head on CPU, and evaluate zero-shot on LIBERO benchmarks.

**Independent Test**: Run the full pre‑training pipeline on the filtered dataset, then evaluate on LIBERO‑Spatial/Object. The test passes if the evaluation script completes, produces a checkpoint ≤2GB, and logs per-seed success rates.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are contract tests to verify the pipeline runs within constraints.

- [X] T010 [P] [US1] Contract test for dataset streaming in `tests/contract/test_dataset_stream.py` (verify <7GB RAM)
- [X] T011 [P] [US1] Contract test for timeout handler in `tests/contract/test_timeout_handler.py` (verify "TIMEOUT_WARNING" log)

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/data/dataset_loader.py` to fetch Open X‑Embodiment via HF Datasets API and filter to ~50k demos across ≥3 platforms. **Output**: `data/filtered_open_x_embodiment.parquet`. **Logic**: Filter `platform_id in [franka, ur5, kuka]`.
- [X] T012b [US1] Implement `src/data/dataset_loader.py` to fetch Open X‑Embodiment and filter to a single-platform subset (for baseline). **Output**: `data/filtered_open_x_embodiment_single_platform.parquet`. **Logic**: Filter `platform_id == 'franka'`.
- [X] T012c [US1] Implement `src/data/verify_dataset.py` to verify T012/T012b outputs: check row count (>= 45000), compute SHA256 checksum, and update `data/metadata.yaml`. **Input**: `data/filtered_open_x_embodiment.parquet` (or single platform variant).
- [X] T014 [US1] Implement `src/models/vla_model.py`: Load Qwen2‑VL‑2B (frozen vision encoder) and attach DiT action head. **DiT Spec**: Implement a DiT action head that fits within 7GB RAM (FR-003). **Action Mapping**: Define the token space strategy (e.g., quantization method) here to allow T013 to map to it. **Validation**: Validate memory footprint of token mapping method before full training.
- [X] T013 [US1] Implement `src/data/preprocess_actions.py` to map raw joint vectors to DiT token space (handle missing formats by dropping/logging). **Dependency**: Uses token space definition from T014.
- [X] T015 [US1] Implement `src/training/train_loop.py`: CPU-only training loop with batch size auto-adjustment if RAM >6.5GB; enforce a **6-hour (21600s)** wall-time limit using `time.time()` checks every batch (Log "TIMEOUT_WARNING" but DO NOT abort). **Output**: `data/checkpoints/model_epoch_{n}.pt`. **Verify**: Run with 50k samples completes in <6h and logs peak RAM <7GB.
- [X] T015a [US1] Implement batch size auto-adjustment logic in `src/training/train_loop.py` to dynamically reduce batch size if `psutil` reports RSS > 6.5GB.
- [X] T016 [US1] Implement `src/evaluation/libero_eval.py`: Zero-shot evaluation on LIBERO‑Spatial/Object for Franka (within-embodiment) and UR (cross-embodiment). **Output**: `data/eval_results.json` with keys `success_rate` (per-seed list), `trajectory_length`, `variance`, `ci_95_lower`, `ci_95_upper`. **Verify**: Distinct metrics for 'within-embodiment' and 'cross-embodiment'.
- [X] T017 [US1] Implement `src/utils/checkpoint_saver.py`: Serialize model weights ensuring size ≤2GB; save to `data/checkpoints/`
- [X] T018 [US1] Implement `src/utils/reproducibility.py`: Log seeds, hyperparams, and versions to `manifest.yaml`. **Output**: Write deterministic `data/seeds.json` with the 5 random seeds used.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison & Statistical Significance (Priority: P2)

**Goal**: Compare cross-embodiment model against single-embodiment baseline using **Wilcoxon signed-rank test** with Holm-Bonferroni correction (Constitution Principle VI).

**Independent Test**: Execute baseline (single-platform subset of Open X-Embodiment) and cross-embodiment runs, then run the statistical test. The test passes if the script outputs a p-value and a significance decision.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for statistical test input validation in `tests/contract/test_stat_utils.py` (verify paired vectors)

### Implementation for User Story 2

- [X] T020 [US2] Implement `src/training/train_baseline.py`: Reuse US1 pipeline but train specifically on **single-platform subset of Open X-Embodiment** (from T012b) for the SAME seeds (load from `data/seeds.json`).
- [X] T021 [US2] Implement `src/statistics/wilcoxon_test.py`: Compute **Wilcoxon signed-rank test** on success-rate vectors from US1 and US2; apply Holm-Bonferroni correction. **Output**: `data/stat_results.json` with keys `p_value`, `is_significant`, `method`, `statistic`. **Verify**: Script runs on seed vectors and produces valid JSON.
- [X] T022 [US2] Implement `src/reporting/stat_report.py`: Generate `stat_report.md` containing p-values, corrected decisions, and absolute improvement metrics
- [X] T023 [US2] Integrate statistical test into main CLI flow to trigger automatically after US1 and US2 training complete

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Data‑Composition Ablation (Priority: P3)

**Goal**: Vary data composition (0.0, 0.5, 1.0) to quantify marginal transfer benefits and plot trends with 95% CIs.

**Independent Test**: Run three training runs with different ratios, evaluate each, and plot success-rate vs. proportion. The test passes if the script produces a CSV/plot with a representative set of points and 95% CIs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for ablation ratio validation in `tests/contract/test_ablation.py` (verify 0.0, 0.5, 1.0 inputs)

### Implementation for User Story 3

- [X] T026 [US3] Implement `src/statistics/confidence_intervals.py`: Compute 95% confidence intervals using **bootstrapping** (non-parametric) from the 5 seeds for each ratio to align with non-normal distribution assumptions. **Input**: Read `data/eval_results.json` (from T016) containing success-rate vectors.
- [X] T025 [US3] Implement `src/experiments/ablation_runner.py`: Orchestrate three training runs (ratios, 0.5, 1.0) using the same seeds as US1/US2 (load from `data/seeds.json`) and statistical utils from T026.
- [X] T025b [US3] Implement CLI aggregation and CSV generation logic in `src/experiments/ablation_runner.py` or `src/cli.py` to automatically generate a CSV summarising mean success-rate and 95% confidence intervals for each `--ratio` argument, satisfying FR-006. **Output**: `data/ablation_summary.csv`.
- [ ] T027 [US3] Implement `src/reporting/ablation_report.py`: Generate `ablation_results.csv` (columns: `ratio, mean_success_rate, ci_lower, ci_upper`) and `ablation_plot.png` (x-axis: ratio, y-axis: success_rate, error bars: 95% CI). **Verify**: CSV contains required columns.
- [ ] T028 [US3] Implement `src/reporting/manifest_renderer.py`: Create `render_manifest.py` script that exits 0 and produces `manifest.md` with all versions.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates: Create `docs/README.md` (setup, data provenance) and `docs/CLI_REFERENCE.md` (CLI usage).
- [ ] T030 Code cleanup and refactoring to ensure `psutil` monitoring is consistent across all training loops
- [ ] T031 Performance optimization: Verify that `torch.set_num_threads` is configured to restrict parallelism in all scripts.
- [ ] T032 [P] Additional unit tests for action token mapping edge cases in `tests/unit/test_preprocess_actions.py`
- [ ] T033 Security hardening: Ensure no sensitive keys are logged in `manifest.md`
- [ ] T034 [P] Run `quickstart.md` validation: Execute commands defined in `docs/quickstart.md` and verify exit code 0 for all steps.

---

## Phase 7: Finalization

**Purpose**: Generate final reproducibility artifacts after all experiments complete

- [ ] T035 [Final] Execute `render_manifest.py` to aggregate all logs (including git commit hash and container digest) into `manifest.md`. **Verify**: Exit code 0 and file contains exact versions.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Finalization (Phase 7)**: Depends on completion of Phase 5 (all experiments)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1's evaluation framework but uses different data ratio
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1's training/evaluation framework; depends on US2's statistical utils for CI calculation
- **Note**: US2 and US3 both require the same 5 random seeds to be consistent; T018 and T025 must coordinate seed generation.

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
Task: "Contract test for dataset streaming in tests/contract/test_dataset_stream.py"
Task: "Contract test for timeout handler in tests/contract/test_timeout_handler.py"

# Launch all models/data for User Story 1 together:
Task: "Implement src/data/dataset_loader.py"
Task: "Implement src/data/preprocess_actions.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (training + eval + checkpoint)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Statistical validation)
4. Add User Story 3 → Test independently → Deploy/Demo (Ablation study)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Training/Eval)
 - Developer B: User Story 2 (Baseline/Stats) - *Can start once US1 eval framework is stable*
 - Developer C: User Story 3 (Ablation) - *Can start once US1 training loop is stable*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All training tasks must enforce `torch.set_num_threads(2) ` and monitor RAM via `psutil` to stay within 7GB limit.
- **CRITICAL**: Dataset download tasks MUST specify exact HuggingFace IDs or URLs (e.g., `open-x-embodiment`, `bridge-v2`).
- **Statistical Note**: Per Constitution Principle VI and Spec FR-005, paired comparisons use **Wilcoxon signed-rank test** with Holm-Bonferroni correction (non-parametric), overriding any conflicting plan references to t-tests.
- **Confidence Intervals**: Per Spec SC-003 and Constitution Principle VI (non-normal distribution assumption), 95% CIs MUST be computed via **bootstrapping**, not t-distribution.
- **Seed Management**: `data/seeds.json` is the single source of truth for random seeds across all experiments.
- **Data Consistency**: T020 (Baseline) MUST use the single-platform subset of Open X‑Embodiment (T012b) to ensure paired statistical validity.