# Tasks: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

**Input**: Design documents from `/specs/001-quantify-gw-resolution-impact/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize a Python project with `gwpy`, `bilby`, `scipy`, `numpy`, `pandas`, `matplotlib`, `astropy`, `dynesty` dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement global seed enforcement in `code/utils/seeds.py` (setting `numpy.random.seed`, `bilby.core.utils.set_seed`) to satisfy Constitution I
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

- [ ] T013 [US1] Implement `code/data/download.py` to fetch high-SNR strain data (SNR ≥ 20) from GWOSC using `gwpy` (FR-001). **Must include logic to detect missing data segments, extract their segment IDs, and log a warning containing the segment ID before proceeding** (US‑1 Scenario 3).
- [ ] T020 [US1] Implement validation in `code/data/transform.py` to verify Nyquist limit compliance against the signal's dominant frequency content **before** any downsampling (Edge Case). This task must run prior to T014.
- [ ] T014 [US1] Implement `code/data/transform.py` to downsample to 4096 Hz, 2048 Hz, and 1024 Hz using `scipy.signal.decimate` with anti‑aliasing (FR-002). **Depends on T020 validation**.
- [ ] T015 [US1] Implement `code/data/transform.py` to quantize data to 16‑bit and 32‑bit float representations (FR-003)
- [ ] T016 [US1] Implement `code/inference/models.py` to configure `IMRPhenomPv2` waveform model (FR-004)
- [ ] T017 [US1] Implement `code/inference/run_bilby.py` to execute parameter estimation with a maximum of 5000 steps (hard limit) and convergence monitoring (Gelman‑Rubin) (FR-004)
- [ ] T018 [US1] Implement convergence‑check wrapper around T017 in `code/inference/run_bilby.py` that **flags a run as “inconclusive” if the Gelman‑Rubin statistic ≥ 1.01 OR the 5000‑step hard limit is reached** (FR-004, Edge Case)
- [ ] T019 [US1] Add logic to `code/inference/run_bilby.py` that **excludes events where posterior width > 50 % of prior width** and records this exclusion in metadata; this filtering occurs immediately after inference and **before any bias analysis (US‑2)** (Edge Case).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Bias and Divergence via Hellinger Distance (Priority: P2)

**Goal**: Compare downsampled posteriors against ground truth or baseline to calculate Hellinger distance and absolute bias.

**Independent Test**: Run the divergence calculation script on a generated posterior file and known ground truth, verifying numerical output of Hellinger distance and bias percentage.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for Hellinger distance calculation against known distributions in `tests/unit/test_metrics.py`
- [ ] T022 [P] [US2] Unit test for bias calculation logic against catalog 90 % CI scaling in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T023.1 [US2] Define and implement the logic to retrieve or compute the **intrinsic statistical uncertainty baseline** from the high‑resolution baseline posterior (SC‑001).
- [ ] T023 [US2] Implement `code/analysis/metrics.py` to calculate Hellinger distance between a downsampled posterior and the baseline/ground truth **using the baseline computed in T023.1** (FR‑005, SC‑001).
- [ ] T024 [US2] Implement `code/analysis/metrics.py` to compute mass and spin bias as absolute difference from GWOSC catalog ground truth (FR‑006)
- [ ] T025 [US2] Implement logic to scale catalog‑reported uncertainty to a higher confidence interval. 

The research question is: How can we best estimate the systematic uncertainties in weak lensing shear measurements?
The method is: We will utilize simulations to quantify the impact of various systematic error sources on weak lensing measurements, and develop methods to mitigate these effects.
(e.g., Hildebrandt et al. 2017, DOI: 10.1093/mnras/stx2696) for threshold comparison (FR‑006)
- [ ] T026 [US2] Add flagging mechanism for configurations where bias exceeds the catalog‑reported confidence interval threshold (e.g., a high-confidence level) (FR‑006)
- [ ] T027 [US2] Implement validation for injected data scenarios where bias should be effectively zero (< 1e‑6) (US‑2, Scenario 3)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Results and Identify Resolution Thresholds (Priority: P3)

**Goal**: Aggregate results across events and resolutions to identify the specific sampling rate/bit depth threshold where bias consistently exceeds uncertainty.

**Independent Test**: Run the aggregation script on a set of result files, verifying it outputs a summary report identifying the rate where bias > catalog 90 % CI for ≥ 50 % of events.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for majority rule threshold logic (≥ 50 % events) in `tests/unit/test_aggregate.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/analysis/aggregate.py` to load results from multiple events and resolution configurations (FR‑007)
- [ ] T030 [US3] Implement logic to calculate **the standard deviation of the identified thresholds**, where an identified threshold is defined as *the specific sampling‑rate (Hz) at which the majority‑rule (bias > catalog 90 % CI for ≥ 50 % of events) is first met* (SC‑004).
- [ ] T031 [US3] Implement "No threshold found" reporting logic if bias remains within limits down to a high audio frequency 

The research question is: Can generative models trained on audio data produce novel, realistic sounds?
The method is: We will train a Generative Adversarial Network (GAN) on a dataset of environmental sounds and evaluate its performance using a listening test with human participants. (Goodfellow et al., 2014)
References: Goodfellow, I. J., Pouget-Abadie, J., Mirza, M., Xu, B., Warde-Farley, D., Ozair, S., ... & Bengio, Y. (2014). Generative adversarial nets. *Advances in neural information processing systems*, *27*, 2672-2680. (US‑3, Scenario 2)
- [ ] T032 [US3] Generate visualization of sampling rate vs. bias magnitude with catalog uncertainty threshold line (US‑3, Scenario 3)
- [ ] T033 [US3] Output summary table identifying the lowest viable sampling rate where the majority rule is met (FR‑007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T039 Code cleanup and refactoring to ensure strict typing and docstrings
- [ ] T040 Performance optimization for MCMC runs to ensure completion within A time-based confidence interval limit will be applied. 

The research question is: Can reinforcement learning agents effectively learn to navigate complex environments with limited perception and communication? The method is: We will train multi-agent reinforcement learning (MARL) agents in a simulated environment, varying the level of communication bandwidth and sensor noise. Agents will be evaluated on their ability to reach target locations efficiently and avoid collisions. We will use a centralized training with decentralized execution (CTDE) approach (Lowe et al., 2017). References: Lowe et al. (2017). Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments. *Advances in Neural Information Processing Systems* 30. [https://doi.org/10.48550/arXiv.1706.09376] (SC‑003)
- [ ] T041 [P] Additional unit tests for edge cases (missing segments, convergence failures) in `tests/unit/`
- [ ] T042 Run quickstart.md validation and ensure all artifacts are checksummed
