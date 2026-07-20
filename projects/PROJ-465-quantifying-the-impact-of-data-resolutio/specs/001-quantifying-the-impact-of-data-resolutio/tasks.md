# Tasks: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

**Input**: Design documents from `/specs/001-quantify-gw-resolution-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan by creating the following directories and files:
 - `code/`, `code/__init__.py`
 - `code/utils/`, `code/utils/seeds.py`, `code/utils/hash_artifact.py`, `code/utils/logging_config.py`
 - `code/data/`, `code/data/models.py`, `code/data/utils.py`
 - `code/inference/`, `code/inference/models.py`, `code/inference/run_bilby.py`
 - `code/analysis/`, `code/analysis/metrics.py`, `code/analysis/aggregate.py`
 - `code/config.py`, `code/requirements.txt`
 - `data/raw/`, `data/derived/`
 - `results/posteriors/`, `results/metrics/`
 - `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T002 Initialize a Python project with `gwpy`, `bilby`, `scipy`, `numpy`, `pandas`, `matplotlib`, `astropy`, `dynesty` dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement global seed enforcement in `code/utils/seeds.py` (setting `numpy.random.seed`, `bilby.core.utils.set_seed`, and `dynesty` sampler random state) to satisfy Constitution I. **Note**: Must pin `dynesty` internal random state to ensure reproducibility. **Updated**: Removed references to Gelman-Rubin logic to align with `dynesty` nested sampling methodology.
- [X] T005 [P] Implement artifact hashing in `code/utils/hash_artifact.py` for Versioning Discipline (Constitution V)
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to record derivation logs for downsampling/quantization parameters
- [X] T007 Create base data model classes in `code/data/models.py` for `StrainEvent`, `ResolutionConfig`, `PosteriorDistribution`, `BiasMetric`
- [X] T008 Configure environment configuration management for GWOSC API keys and data paths in `code/config.py`
- [X] T009 Implement checksum verification utility in `code/data/utils.py` for raw strain data integrity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Downsample Strain Data and Generate Posteriors (Priority: P1) 🎯 MVP

**Goal**: Process high-SNR gravitational wave events by downsampling and quantizing strain data, then running Bayesian parameter estimation to generate posteriors.

**Independent Test**: Execute the downsampling and `bilby` inference pipeline on a single event file and verify that a posterior distribution file is generated for each resolution configuration.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `scipy.signal.decimate` anti-aliasing filter behavior in `tests/unit/test_transform.py`
- [X] T011 [P] [US1] Unit test for 16-bit/32-bit quantization logic in `tests/unit/test_transform.py`
- [X] T012 [US1] Integration test for full downsampling + inference pipeline on GW150914 in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/download.py` to fetch high-SNR strain data (SNR ≥ 20) from GWOSC using `gwpy`. **Must fetch SNR from GWOSC catalog metadata** (FR-001). **Must include logic to detect missing data segments, extract their segment IDs, and log a warning containing the segment ID before proceeding** (US‑1 Scenario 3).
- [X] T020 [US1] Implement validation in `code/data/transform.py` to verify Nyquist limit compliance against the signal's dominant frequency content **before** any downsampling (Edge Case). **Depends on T013**.
- [X] T014 [US1] Implement `code/data/transform.py` to downsample to 4096 Hz, 2048 Hz, and 1024 Hz using `scipy.signal.decimate` with anti‑aliasing (FR-002). **Depends on T020**.
- [X] T015 [US1] Implement `code/data/transform.py` to quantize data to **16-bit and 32-bit float representations** to simulate storage constraints (FR-003).
- [X] T016 [US1] Implement `code/inference/models.py` to configure `IMRPhenomPv2` waveform model (FR-004)
- [X] T017 [US1] Implement `code/inference/run_bilby.py` to execute parameter estimation using `bilby` with `dynesty` (nested sampling) and `IMRPhenomPv2`, running with a maximum of 5000 steps (hard limit) and a `dlogz` threshold of **0.1** (FR-004). **Note**: Implements the scientifically correct `dlogz` convergence check as defined in `plan.md` (Unresolved Concerns #1). If `dlogz` > 0.1 after max steps, flag as "inconclusive". **Depends on T016**.
- [X] T018 [US1] Implement convergence‑check wrapper around T017 in `code/inference/run_bilby.py` that **checks convergence via `dlogz` (evidence tolerance) threshold**; if `dlogz` exceeds threshold after max iterations, **flag the run as "inconclusive"** (FR-004, Edge Case, Plan Unresolved Concerns). **Note**: Explicitly implements the `plan.md` methodology for nested sampling convergence. **Depends on T017**.
- [X] T019 [US1] Add logic to `code/inference/run_bilby.py` to: (1) record the "inconclusive" status in the posterior file metadata and run log, and (2) **exclude events where the posterior width is > 50% of the prior width ** (Edge Case, FR-004). **Note**: This task implements the mandatory spec exclusion rule. Excluded events must be logged with the reason and excluded from downstream bias calculations.
- [X] T019.1 [US1] Implement **Baseline Validation** in `code/inference/run_bilby.py` to ensure the baseline (4096 Hz) posterior is **not flagged 'inconclusive'** and has a valid posterior width < 50% prior width before being used as ground truth. **Output**: A validated baseline posterior artifact file. **Depends on T017, T018 (Baseline Run Completion)**. **Note**: This task validates the baseline run specifically, distinct from T019's general exclusion logic.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Bias and Divergence via Hellinger Distance (Priority: P2)

**Goal**: Compare downsampled posteriors against ground truth or baseline to calculate Hellinger distance and absolute bias.

**Independent Test**: Run the divergence calculation script on a generated posterior file and known ground truth, verifying numerical output of Hellinger distance and bias percentage.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for Hellinger distance calculation against known distributions in `tests/unit/test_metrics.py`
- [X] T022 [P] [US2] Unit test for bias calculation logic against catalog 90 % CI scaling in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T023.1 [US2] Implement helper function in `code/analysis/metrics.py` to retrieve the **intrinsic statistical uncertainty baseline** (defined as the 90% CI width from the 4096 Hz baseline posterior) and cache it for downstream tasks. **Depends on T019.1 (Baseline Validation Output)**. **Note**: Explicitly states dependency on the 'output baseline artifact' generated by T019.1.
- [X] T025 [US2] Implement logic to scale catalog‑reported uncertainty to a high‑confidence interval using the **standard normality assumption** (1σ * 1.645) as per spec.md Assumptions (FR‑006). **Note**: No external citation (e.g., Hildebrandt et al.) used; relies on spec assumption. **Blocking**: T023 depends on this.
- [X] T023 [US2] Implement `code/analysis/metrics.py` to: (1) **Gate Check**: Verify the baseline posterior is not 'inconclusive' (from T019.1); if inconclusive, log error and skip. (2) Retrieve the **intrinsic statistical uncertainty baseline** (defined as the 90% CI width from the 4096 Hz baseline posterior), and (3) calculate Hellinger distance between a downsampled posterior and this baseline/ground truth (FR‑005, SC‑001). **Depends on T023.1, T025**. **Note**: Uses standard normality assumption (1σ * 1.645) as per spec.md Assumptions; no external citation required.
- [X] T024 [US2] Implement `code/analysis/metrics.py` to compute mass and spin bias. **Logic**: (1) **Primary Path**: If simulated injection data is available, compare against injected truth. (2) **Secondary Path**: If only real event data exists, compare against the high-resolution baseline posterior (T019.1). (3) **Tertiary Path**: If neither is available, compare against GWOSC catalog ground truth parameters (FR‑006). **Note**: This implements the plan's methodology shift (Critical Methodological Distinction). **Depends on T023, T026**.
- [X] T026 [US2] Add flagging mechanism for configurations where bias exceeds the catalog‑reported confidence interval threshold (FR‑006). **Note**: Must populate the `exceeds_threshold` attribute in the `BiasMetric` entity. **Blocking**: T024 depends on this.
- [X] T027 [US2] Implement validation for injected data scenarios where bias should be effectively zero (< 1e‑6) (US‑2, Scenario 3). **Note**: Must be tested against known injected truth to validate the pipeline.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Results and Identify Resolution Thresholds (Priority: P3)

**Goal**: Aggregate results across events and resolutions to identify the specific sampling rate/bit depth threshold where bias consistently exceeds uncertainty.

**Independent Test**: Run the aggregation script on a set of result files, verifying it outputs a summary report identifying the rate where bias > catalog 90 % CI for ≥ 50% of events.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for majority rule threshold logic (≥ 50% events) in `tests/unit/test_aggregate.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/analysis/aggregate.py` to load results from multiple events and resolution configurations. **Majority Rule Logic**: (1) **Excluded**: Events flagged as 'inconclusive' due to data quality issues (e.g., missing segments, low SNR) or convergence failure (dlogz > 0.1) are **excluded from the denominator and numerator** to avoid inflating failure rates. (2) **Calculated**: The threshold is the lowest rate where (Count of 'Bias Exceeded' / Total Valid Events) ≥ 50%. **Depends on T029 (Logic Definition)**. **Note**: This resolves the ambiguity in FR-007 regarding 'inconclusive' states by excluding them from the statistical count.
- [X] T030 [US3] Implement logic to calculate **the standard deviation of the identified resolution thresholds across the events**. **Conditional Logic**: If the number of valid events (N) contributing a threshold is ≥ 2, calculate and report the standard deviation. If N < 2, explicitly report "Insufficient data for population consistency" (SC‑004). **Note**: Ensure minimum event count check is implemented to avoid meaningless statistics if only 1-2 events contribute, aligning with `plan.md` Proof of Concept constraints. **Depends on T029**.
- [X] T031 [US3] Implement "No threshold found" reporting logic if bias remains within limits down to a high audio frequency (US‑3, Scenario 2). **Depends on T029**.
- [X] T032 [US3] Generate visualization of sampling rate vs. bias magnitude with catalog uncertainty threshold line (US‑3, Scenario 3). **Depends on T029**.
- [X] T033 [US3] Output summary table identifying the lowest viable sampling rate where the majority rule is met (FR‑007). **Depends on T029**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `specs/001-quantify-gw-resolution-impact/` including `quickstart.md` and `data-model.md`
- [ ] T039 Code cleanup and refactoring to ensure strict typing and docstrings
- [ ] T040 [P] Performance optimization for MCMC runs to ensure completion within the **defined performance goal in plan.md** to comfortably meet the 6-hour constraint (SC‑003). **Note**: Optimizing for a reduced duration goal ensures the success criterion (feasibility) is met comfortably within the 6-hour constraint.
- [ ] T041 [P] Additional unit tests for edge cases (missing segments, convergence failures) in `tests/unit/`
- [ ] T042 Run `specs/001-quantify-gw-resolution-impact/quickstart.md` validation and ensure all artifacts are checksummed

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

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
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence