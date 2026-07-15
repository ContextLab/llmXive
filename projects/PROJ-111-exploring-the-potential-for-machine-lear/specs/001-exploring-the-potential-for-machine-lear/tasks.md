# Tasks: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

**Input**: Design documents from `/specs/001-gene-regulation/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure: `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `tests/contract`, `specs/001-gene-regulation/contracts`.
- [X] T001b [P] Initialize Python 3.11 project with `torch` (CPU-only), `numpy`, `scikit-learn`, `scipy`, `pandas`, `matplotlib` dependencies in `requirements.txt`.
- [X] T001c [P] Create `README.md` skeleton with project overview and setup instructions.
- [X] T002 [P] Configure linting (ruff) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/data_generation.py`:
 - If pre-computed Monte Carlo data is available (verified via checksum), load it.
 - Otherwise, implement the Metropolis-Hastings algorithm to generate raw spin configurations for the J1‑J2 Heisenberg model **and** the XY model at lattice sizes **L=16** and **L=24**, covering temperatures T=0.1‑3.0.
 - Use deterministic seeds and specified coupling constants (J1, J2 ratios) as defined in the Spec Assumptions to ensure reproducibility.
- [X] T005 [P] Implement `code/preprocessing.py` to normalize spin vectors to unit length, reshape to `[batch, 3, L, L]`, and perform a stratified train/val split.
- [X] T006a [P] Create `specs/001-gene-regulation/contracts/spin-config.schema.yaml` defining fields, types, and constraints for spin configurations.
- [ ] T006b [P] Create `specs/001-gene-regulation/contracts/dataset.schema.yaml` defining fields, types, and constraints for the processed dataset.
- [ ] T006c [P] Create `specs/001-gene-regulation/contracts/latent-output.schema.yaml` defining fields, types, and constraints for latent representations.
- [ ] T006d [P] Create `specs/001-gene-regulation/contracts/model-checkpoint.schema.yaml` defining fields, types, and constraints for model checkpoints.
- [ ] T007 [P] Implement `code/utils.py` functions for:
 - Calculating integrated autocorrelation time $\tau_{\text{int}}$,
 - Thinning datasets by ≥ 2 $\tau_{\text{int}}$,
 - Computing magnetic susceptibility $\chi$ for each lattice size,
 - Performing finite‑size scaling of $\chi$ to **extrapolate $T^*$ to the thermodynamic limit** (satisfying Constitution Principle VII and FR‑008/FR‑010).
 - *Note: While T007 is parallel-safe within Phase 2, its output is a blocking prerequisite for US3 tasks (T028, T030).*
- [ ] T008 [P] Setup environment configuration management (`.env` for seeds/paths) and logging infrastructure.
- [~] T009 [P] Implement unit tests for data shapes, normalization correctness, and stratification logic in `tests/unit/`. <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Acquire and preprocess Monte Carlo data into standardized tensors suitable for CPU‑based unsupervised learning.

**Independent Test**: A script executes to download/generate raw spins, normalize, reshape, and split. Test verifies shape `(N, 3, L, L)`, unit norm, and stratification variance ≤ 5.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for normalization and reshaping in `tests/unit/test_preprocessing.py`
- [X] T011 [P] [US1] Integration test for end‑to‑end data pipeline in `tests/integration/test_data_pipeline.py` verifying memory < 6 GB for L=24
- [X] T012 [P] [US1] Validate that `code/data_generation.py` (implemented in T004) correctly generates **both** J1‑J2 Heisenberg and XY model datasets at **L=16** and **L=24**, and that the output files match expected shapes and temperature coverage.

### Implementation for User Story 1

- [X] T014 [US1] Implement memory monitoring in `code/preprocessing.py` to ensure L=24 fits within the 6 GB RAM constraint.
- [X] T015 [US1] Add an explicit assertion in `code/preprocessing.py` that raises a `ValueError` if the maximum absolute difference in sample count between any two temperature bins exceeds 5.
- [~] T016 [US1] Add logging for data generation parameters (T, L, coupling ratios).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Unsupervised VAE Training and Convergence (Priority: P2)

**Goal**: Train a VAE on preprocessed spin configurations to learn a compressed latent representation without labels.

**Independent Test**: The training loop runs for multiple epochs on CPU. Test verifies loss convergence (|ΔLoss| < 1e‑3 for 5 epochs), latent mean ≈ 0, and total time < 6 h.

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for VAE architecture (2 conv/2 deconv layers, latent dim 10) in `tests/unit/test_vae_model.py`
- [X] T019 [P] [US2] Integration test for training loop convergence and early stopping in `tests/integration/test_training.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/vae_model.py` with 2 convolutional encoder layers and 2 deconvolutional decoder layers, latent dimension 10.
- [ ] T021 [US2] Implement `code/train.py` with Adam optimizer (lr=1e‑3), MSE loss, KL divergence, and early‑stopping logic.
- [ ] T022 [US2] Implement time‑budget enforcement in `code/train.py` to report partial results if execution exceeds 6 h (FR‑004).
- [~] T023 [US2] Integrate data loaders from US1 and ensure batch processing fits within 7 GB RAM.
- [~] T024 [US2] Implement checkpoint saving with checksums and metadata validation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Latent Space Analysis and Critical Point Detection (Priority: P3)

**Goal**: Analyze latent space to identify $T^*$ via variance peak detection, validate against susceptibility, and perform Finite‑Size Scaling.

**Independent Test**: Script encodes data, calculates $\sum \text{Var}(\mu)$, applies GP smoothing + peak detection, computes 95 % CI via bootstrap (after thinning), and performs FSS extrapolation.

### Tests for User Story 3

- [X] T025 [P] [US3] Integration test for FSS extrapolation and bootstrap confidence intervals in `tests/integration/test_fss.py`
- [X] T038 [P] [US3] Unit test for peak‑finding algorithm (GP smoothing, derivative analysis) in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analysis.py` to calculate total latent variance $\sum \text{Var}(\mu)$ for each temperature bin.
- [ ] T027 [US3] Implement Gaussian Process regression (squared‑exponential kernel) for smoothing and peak detection per FR‑005. **Explicitly enforce:**
 - Second derivative threshold: **< -0.01** (normalized by global max).
 - Peak height condition: **> 2σ** above a moving average (window size = 5 points) of the residuals.
- [ ] T028 [US3] Implement bootstrap resampling with a sufficient number of iterations to ensure stability. **after** computing integrated autocorrelation time $\tau_{\text{int}}$ (via output of T007) and thinning the dataset by a factor ≥ 2 $\tau_{\text{int}}$ (FR‑006).
- [ ] T029 [US3] Implement Finite‑Size Scaling (FSS) logic to extrapolate $T^*$ to $L\!\to\!\infty$ using $T^{*}(L)=T_c + a L^{-1/\nu}$. Use $\nu=1$ for known 2D Ising/XY universality. **If the universality class is unknown, fix $\nu=1$ or apply a regularization method to avoid an underdetermined system** (FR‑010).
- [ ] T029b [US3] Explicitly validate and report the fitted exponent $\nu$ if it was fitted (rather than fixed) as a distinct output field in the results report (FR‑010).
- [ ] T030 [US3] Cross‑validate the ML‑derived $T^*$ against magnetic susceptibility $\chi$ (output of T007) and literature values. **Use Pearson correlation coefficient** to compute the p-value for the XY model BKT transition correlation (FR‑008).
- [ ] T031 [US3] Detect flat variance curves. **If no significant peak is found:**
 - Calculate the reconstruction error variance as a secondary indicator (per Spec Assumptions/FR‑005 fallback).
 - Report "No significant transition detected" **including the reconstruction error variance metrics and a confidence interval derived from this secondary indicator** (without using reconstruction error to redefine $T^*$).
- [ ] T032 [US3] Report **pseudo-critical temperatures for L=16 and L=24** as distinct primary output fields, along with the extrapolated $T^*$ and status flags (e.g., "FSS Inconclusive" if fitting fails) (FR‑009).
- [ ] T032b [US3] Implement logic to frame all findings regarding the relationship between latent space variance and temperature as **associational**, avoiding causal claims, and validate the generated report text against this constraint (FR‑007).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Cross‑Cutting Validation & Physical Verification

- [ ] T033a [P] Update `README.md` with usage instructions and setup guide.
- [ ] T033b [P] Update `README.md` with detailed FSS methodology description.
- [ ] T033c [P] Update `README.md` with validation procedures and physical verification steps.
- [ ] T034 [P] Code cleanup and refactoring for performance optimization (vectorization).
- [ ] T035 [P] Additional unit tests for edge cases (flat variance, missing data) in `tests/unit/`.
- [ ] T036 [P] Run `quickstart.md` validation and ensure all scripts run within the CI time limit.
- [ ] T037 [P] Verify all random seeds are pinned and data generation is deterministic for reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories until finished.
- **User Stories (Phase 3‑5)**: All depend on Foundational phase completion.
 - Stories can proceed in parallel after Foundational.
- **Cross‑Cutting Validation (Phase 6)**: Depends on outputs from US3 (latent variance) and utils (χ) but does not block prior stories.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked **[P]** can run in parallel.
- All Foundational tasks marked **[P]** can run in parallel (within Phase 2).
- Once Foundational is complete, all user stories can start in parallel (if staffed).
- All tests for a user story marked **[P]** can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- **[P]** tasks = different files, no dependencies.
- **[Story]** label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid vague tasks, same‑file conflicts, hidden cross‑story dependencies.
- **CRITICAL**: All data generation must use real Monte Carlo simulations (no synthetic/fake data) to satisfy FR‑001 and the "Real data + real results" rule.
- **CRITICAL**: All tasks must respect the 6‑hour time and 7 GB RAM limits; if a task risks exceeding this, it must include partial‑result reporting logic.
- **CRITICAL**: Task ordering respects data flow: `code/utils.py` (T007) and `code/data_generation.py` (T004) MUST be completed before `code/analysis.py` (T026-T032) which depends on them.