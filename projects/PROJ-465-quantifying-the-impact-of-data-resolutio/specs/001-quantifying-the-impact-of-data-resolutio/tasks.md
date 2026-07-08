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

- [ ] T001 Create project structure per implementation plan by creating the following directories and files:
  - `code/`, `code/__init__.py`
  - `code/utils/`, `code/utils/seeds.py`, `code/utils/hash_artifact.py`, `code/utils/logging_config.py`
  - `code/data/`, `code/data/models.py`, `code/data/utils.py`
  - `code/inference/`, `code/inference/models.py`, `code/inference/run_bilby.py`
  - `code/analysis/`, `code/analysis/metrics.py`, `code/analysis/aggregate.py`
  - `code/config.py`, `code/requirements.txt`
  - `data/raw/`, `data/derived/`
  - `results/posteriors/`, `results/metrics/`
  - `tests/unit/`, `tests/integration/`, `tests/contract/`
- [ ] T002 Initialize a Python project with `gwpy`, `bilby`, `scipy`, `numpy`, `pandas`, `matplotlib`, `astropy`, `dynesty` dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement global seed enforcement in `code/utils/seeds.py` (setting `numpy.random.seed`, `bilby.core.utils.set_seed`, and `dynesty` sampler random state) to satisfy Constitution I. **Note**: Must pin `dynesty` internal random state to ensure reproducibility for the specific "inconclusive" logic required by FR-004.
- [ ] T005 [P] Implement artifact hashing in `code/utils/hash_artifact.py` for Versioning Discipline (Constitution V)
- [ ] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to record derivation logs for downsampling/quantization parameters
- [ ] T007 Create base data model classes in `code/data/models.py` for `StrainEvent`, `ResolutionConfig`, `PosteriorDistribution`, `BiasMetric`
- [ ] T008 Configure environment configuration management for GWOSC API keys and data paths in `code/config.py`
- [ ] T009 Implement checksum verification utility in `code/data/utils.py` for raw strain data integrity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Downsample Strain Data and Generate Posteriors (Priority: P1) 🎯 MVP

**Goal**: Process high-SNR gravitational wave events by downsampling and quantizing strain data, then running Bayesian parameter estimation to generate posteriors.

**Independent Test**: Execute the downsampling and `bilby` inference pipeline on a single event file and verify that a posterior distribution file is generated for each resolution configuration.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for `scipy.signal.decimate` anti-aliasing filter behavior in `tests/unit/test_transform.py`
- [ ] T011 [P] [US1] Unit test for 16-bit/32-bit quantization logic in `tests/unit/test_transform.py`
- [ ] T012 [US1] Integration test for full downsampling + inference pipeline on GW150914 in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/data/download.py` to fetch high-SNR strain data (SNR ≥ 20) from GWOSC using `gwpy`. **Must fetch SNR from GWOSC catalog metadata** (FR-001). **Must include logic to detect missing data segments, extract their segment IDs, and log a warning containing the segment ID before proceeding** (US‑1 Scenario 3).
- [ ] T020 [US1] Implement validation in `code/data/transform.py` to verify Nyquist limit compliance against the signal's dominant frequency content **before** any downsampling (Edge Case).
- [ ] T014 [US1] Implement `code/data/transform.py` to downsample to 4096 Hz, 2048 Hz, and 1024 Hz using `scipy.signal.decimate` with anti‑aliasing (FR-002). **Depends on T020**.
- [ ] T015 [US1] Implement `code/data/transform.py` to quantize data to standard float representations. (FR-003)
- [ ] T016 [US1] Implement `code/inference/models.py` to configure `IMRPhenomPv2` waveform model (FR-004)
- [ ] T017 [US1] Implement `code/inference/run_bilby.py` to execute parameter estimation using `bilby` with `dynesty` (nested sampling) and `IMRPhenomPv2`, running with a maximum of 5000 steps (hard limit) (FR-004). **Note**: This task implements `dynesty` nested sampling. **CRITICAL**: The `spec.md` 'Edge Cases' section incorrectly mandates Gelman-Rubin checks; this task MUST use `dlogz` (evidence tolerance) as per `plan.md` 'Unresolved Concerns' resolution. If `dlogz` > threshold after max steps, flag as "inconclusive".
- [ ] T018 [US1] Implement convergence‑check wrapper around T017 in `code/inference/run_bilby.py` that **checks convergence via `dlogz` (evidence tolerance) threshold**; if `dlogz` exceeds threshold after max iterations, **flag the run as "inconclusive"** (FR-004, Edge Case, Plan Unresolved Concerns). **Note**: Explicitly overrides `spec.md` 'Edge Cases' Gelman-Rubin requirement which is inapplicable to `dynesty`.
- [ ] T019 [US1] Add logic to `code/inference/run_bilby.py` to record the "inconclusive" status in the posterior file metadata and run log, ensuring FR-004 coverage for the `dynesty` approach (Edge Case). **Note**: This task handles status flagging, NOT event exclusion. The `spec.md` requirement to exclude events based on posterior width is **not implemented** per `plan.md` 'Unresolved Concerns' resolution; instead, the posterior width is recorded as a metric.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Bias and Divergence via Hellinger Distance (Priority: P2)

**Goal**: Compare downsampled posteriors against ground truth or baseline to calculate Hellinger distance and absolute bias.

**Independent Test**: Run the divergence calculation script on a generated posterior file and known ground truth, verifying numerical output of Hellinger distance and bias percentage.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for Hellinger distance calculation against known distributions in `tests/unit/test_metrics.py`
- [ ] T022 [P] [US2] Unit test for bias calculation logic against catalog 90 % CI scaling in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T023.1 [US2] Implement helper function in `code/analysis/metrics.py` to retrieve the **intrinsic statistical uncertainty baseline** (defined as the 90% CI width from the 4096 Hz baseline posterior) and cache it for downstream tasks.
- [ ] T023 [US2] Implement `code/analysis/metrics.py` to: (1) retrieve the **intrinsic statistical uncertainty baseline** (defined as the 90% CI width from the 4096 Hz baseline posterior), and (2) calculate Hellinger distance between a downsampled posterior and this baseline/ground truth (FR‑005, SC‑001). **Depends on T023.1**. **Note**: Uses standard normality assumption (1σ * 1.645) as per spec.md Assumptions; no external citation required.
- [ ] T024 [US2] Implement `code/analysis/metrics.py` to compute mass and spin bias as absolute difference from GWOSC catalog ground truth (FR‑006)
- [ ] T025 [US2] Implement logic to scale catalog‑reported uncertainty to a 90% confidence interval using the **standard normality assumption** (1σ * 1.645) as per spec.md Assumptions (FR‑006). **Note**: No external citation (e.g., Hildebrandt et al.) used; relies on spec assumption.
- [ ] T026 [US2] Add flagging mechanism for configurations where bias exceeds the catalog‑reported confidence interval threshold (FR‑006)
- [ ] T027 [US2] Implement validation for injected data scenarios where bias should be effectively zero (< 1e‑6) (US‑2, Scenario 3)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Results and Identify Resolution Thresholds (Priority: P3)

**Goal**: Aggregate results across events and resolutions to identify the specific sampling rate/bit depth threshold where bias consistently exceeds uncertainty.

**Independent Test**: Run the aggregation script on a set of result files, verifying it outputs a summary report identifying the rate where bias > catalog 90 % CI for ≥ 50% of events.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for majority rule threshold logic (≥ 50% events) in `tests/unit/test_aggregate.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/analysis/aggregate.py` to load results from multiple events and resolution configurations. **Must include all processed events (including inconclusive ones) in the denominator for the majority rule calculation** to satisfy FR‑007 (FR‑007).
- [ ] T030 [US3] Implement logic to calculate **the standard deviation of the identified thresholds**, where an identified threshold is defined as *the specific sampling‑rate (Hz) at which the majority‑rule (bias > catalog 90 % CI for ≥ 50% of events) is first met*. **If no threshold is found for an event, treat the value as NaN/sentinel to ensure the standard deviation calculation is defined** (SC‑004). **Note**: Ensure minimum event count check is implemented to avoid meaningless statistics if only 1-2 events contribute.
- [ ] T031 [US3] Implement "No threshold found" reporting logic if bias remains within limits down to a high audio frequency (US‑3, Scenario 2)
- [ ] T032 [US3] Generate visualization of sampling rate vs. bias magnitude with catalog uncertainty threshold line (US‑3, Scenario 3)
- [ ] T033 [US3] Output summary table identifying the lowest viable sampling rate where the majority rule is met (FR‑007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T039 Code cleanup and refactoring to ensure strict typing and docstrings
- [ ] T040 Performance optimization for MCMC runs to ensure completion within a predefined time-based confidence interval limit will be applied (SC‑003)
- [ ] T041 [P] Additional unit tests for edge cases (missing segments, convergence failures) in `tests/unit/`
- [ ] T042 Run quickstart.md validation and ensure all artifacts are checksummed