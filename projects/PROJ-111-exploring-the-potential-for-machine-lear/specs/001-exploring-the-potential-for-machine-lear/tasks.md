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

- [X] T004a [P] [US1] Implement `code/data_generation.py` for **2D J1-J2 Heisenberg model**:
  - If pre‑computed Monte Carlo data is available (verified via checksum), load it.
  - Otherwise, implement the Metropolis‑Hastings algorithm to generate **raw spin configurations** at lattice sizes **L=16** and **L=24**, covering temperatures **T=0.1‑3.0**.
  - **CRITICAL**: If the real Monte Carlo generation or download fails, the script MUST raise a `RuntimeError` immediately. **DO NOT** use `try/except` blocks or `if download_failed` logic that falls back to `generate_synthetic_*()`, `mock_*()`, or any placeholder data. The pipeline must fail loudly to prevent data fabrication.
  - Use deterministic seeds (pinned via `np.random.seed` and `torch.manual_seed`) to guarantee reproducibility.
  - Output files: `data/raw/j1j2_heisenberg_L16.npy`, `data/raw/j1j2_heisenberg_L24.npy`.
- [X] T004b [P] [US1] Implement `code/data_generation.py` for **XY model**:
  - If pre‑computed Monte Carlo data is available (verified via checksum), load it.
  - Otherwise, implement the Metropolis‑Hastings algorithm to generate **raw spin configurations** at lattice sizes **L=16** and **L=24**, covering temperatures **T=0.1‑3.0**.
  - **CRITICAL**: If the real Monte Carlo generation or download fails, the script MUST raise a `RuntimeError` immediately. **DO NOT** use `try/except` blocks or `if download_failed` logic that falls back to `generate_synthetic_*()`, `mock_*()`, or any placeholder data. The pipeline must fail loudly to prevent data fabrication.
  - Use deterministic seeds (pinned via `np.random.seed` and `torch.manual_seed`) to guarantee reproducibility.
  - Output files: `data/raw/xy_L16.npy`, `data/raw/xy_L24.npy`.
- [X] T005 [P] Implement `code/preprocessing.py` to normalize spin vectors to unit length, reshape to `[batch, 3, L, L]`, and perform an **80/20 stratified train/validation split** with temperature binning.
- [X] T006a [P] Create `specs/001-gene-regulation/contracts/spin-config.schema.yaml` defining fields, types, and constraints for spin configurations.
- [X] T006b [X] Create `specs/001-gene-regulation/contracts/dataset.schema.yaml` defining fields, types, and constraints for the processed dataset.
- [X] T006c [X] Create `specs/001-gene-regulation/contracts/latent-output.schema.yaml` defining fields, types, and constraints for latent representations.
- [X] T006d [X] Create `specs/001-gene-regulation/contracts/model-checkpoint.schema.yaml` defining fields, types, and constraints for model checkpoints.
- [X] T006e [X] Implement `code/utils.py` function `write_checksums()` to generate `data/checksums.txt` for **all files** in `data/raw` and `data/processed`, and verify them on load.
- [X] T006f [P] Implement `code/reference_validator.py`:
  - Read `research.md` (input artifact) and extract all literature citations for critical temperatures (J1-J2 and XY BKT).
  - Verify these citations against the primary source or a canonical DOI with title-token-overlap ≥ 0.7 (as per Constitution Principle II).
  - If any citation is unreachable or mismatched, raise a `RuntimeError` to block analysis.
  - **Blocking prerequisite for US3 tasks**.
- [X] T007 [X] Implement utility functions in `code/utils.py` for:
  - Calculating integrated autocorrelation time τ_int,
  - Thinning datasets by ≥ 2 τ_int,
  - Computing magnetic susceptibility χ for each lattice size,
  - Performing finite‑size scaling of χ to extrapolate $T^*$ to the thermodynamic limit.
  - **Blocking prerequisite for US3 tasks**.
- [X] T008 [X] Setup environment configuration (`.env`) for paths and **pin all random seeds** (NumPy, PyTorch, Python `random`). Add logging infrastructure that records seed values and data‑generation parameters.
- [X] T009 [X] Implement unit tests in `tests/unit/test_stratification.py` to verify:
  - Correct tensor shapes after preprocessing,
  - Unit‑norm of spin vectors,
  - **Stratified split** respects the constraint *max absolute difference in sample count between any two temperature bins ≤ 5*.
  - **Depends on T005**.
- [X] T010 [P] [US1] Unit test for normalization and reshaping in `tests/unit/test_preprocessing.py`.
- [X] T011 [P] [US1] Integration test for end‑to‑end data pipeline in `tests/integration/test_data_pipeline.py` verifying memory < 6 GB for L=24.
- [X] T012 [P] [US1] Validate that `code/data_generation.py` (implemented in T004a) correctly generates **J1‑J2 Heisenberg** datasets at **L=16** and **L=24**, with expected shapes and temperature coverage.
- [X] T012b [P] [US1] Validate that `code/data_generation.py` (implemented in T004b) correctly generates **XY model** datasets at **L=16** and **L=24**, with expected shapes and temperature coverage.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Acquire and preprocess Monte Carlo data into standardized tensors suitable for CPU‑based unsupervised learning.

**Independent Test**: A script executes to download/generate raw spins, normalize, reshape, and split. Test verifies shape `(N, 3, L, L)`, unit norm, and stratification variance ≤ 5.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for normalization and reshaping in `tests/unit/test_preprocessing.py`
- [X] T011 [P] [US1] Integration test for end‑to‑end data pipeline in `tests/integration/test_data_pipeline.py` verifying memory < 6 GB for L=24
- [X] T012 [P] [US1] Validate that `code/data_generation.py` (implemented in T004a) correctly generates **J1‑J2 Heisenberg** datasets at **L=16** and **L=24**, and that the output files match expected shapes and temperature coverage.
- [X] T012b [P] [US1] Validate that `code/data_generation.py` (implemented in T004b) correctly generates **XY model** datasets at **L=16** and **L=24**, and that the output files match expected shapes and temperature coverage.

### Implementation for User Story 1

- [X] T014 [US1] Implement memory monitoring in `code/preprocessing.py` to ensure L=24 fits within the 6 GB RAM constraint.
- [X] T015 [US1] Add an explicit assertion in `code/preprocessing.py` that raises a `ValueError` if the maximum absolute difference in sample count between any two temperature bins exceeds 5.
- [X] T016 [US1] Add logging for data generation parameters (T, L, coupling ratios).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Unsupervised VAE Training and Convergence (Priority: P2)

**Goal**: Train a VAE on preprocessed spin configurations to learn a compressed latent representation without labels.

**Independent Test**: The training loop runs for multiple epochs on CPU. Test verifies loss convergence (|ΔLoss| < 1e-3 for 5 epochs), latent mean ≈ 0, and total time < 6 h.

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for VAE architecture (2 conv/2 deconv layers, latent dim 10) in `tests/unit/test_vae_model.py`
- [X] T019 [P] [US2] Integration test for training loop convergence and early stopping in `tests/integration/test_training.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/vae_model.py` with 2 convolutional encoder layers and 2 deconvolutional decoder layers, and a **a latent dimension of appropriate scale** (as mandated by FR-003).
- [X] T021 [US2] Implement `code/train.py` with Adam optimizer (lr=1e-3), MSE loss, KL divergence, and early‑stopping logic.
- [X] T022 [US2] Implement time‑budget enforcement in `code/train.py` to report partial results if execution exceeds 6 h (FR‑004).
- [X] T023 [US2] Implement memory‑monitoring for the **entire pipeline** (data loading, training, analysis, bootstrap) ensuring total RAM usage ≤ 7 GB. Output warning flag `pipeline_memory_exceeded`.
- [X] T023b [US2] Implement total‑time monitoring for the **entire pipeline** (including analysis & bootstrap) with a a hard time limit of approximately six hours. **If the limit is exceeded:**
  - Set status flag `pipeline_time_exceeded`.
  - **Generate and output partial results** (e.g., T* for L=16 only) immediately.
  - Do not proceed with further analysis.
- [X] T024 [US2] Implement checkpoint saving with checksums and metadata validation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Latent Space Analysis and Critical Point Detection (Priority: P3)

**Goal**: Analyze latent space to identify $T^*$ via variance peak detection, validate against susceptibility, and perform Finite‑Size Scaling.

**Independent Test**: Script encodes data, calculates $\sum \text{Var}(\mu)$, applies GP smoothing + peak detection, computes 95 % CI via bootstrap (after thinning), and performs FSS extrapolation.

### Tests for User Story 3

- [X] T025 [P] [US3] Integration test for FSS extrapolation and bootstrap confidence intervals in `tests/integration/test_fss.py`
- [X] T038 [P] [US3] Unit test for peak‑finding algorithm (GP smoothing, derivative analysis) in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis.py` to calculate total latent variance $\sum \text{Var}(\mu)$ for each temperature bin.
- [X] T027 [US3] Implement Gaussian Process regression with a **squared‑exponential kernel** to smooth the variance curve and perform derivative analysis. Enforce:
  - Second‑derivative threshold **< -0.01** (normalized by global maximum),
  - Peak height **> 2σ** above a moving average (window = 5 points) of the residuals.
  - **Depends on T026**.
- [X] T028 [US3] Perform bootstrap resampling with **1000 iterations** (as mandated by FR-006) to compute the 95 % CI for $T^*$. **First thin the dataset by ≥ 2 τ_int** (output from T007). Generate artifact `data/bootstrap_ci.json`.
  - **Depends on T007**.
- [X] T029 [US3] Implement Finite‑Size Scaling (FSS) using the relation $T^*(L) = T_c + a L^{-1/\nu}$ with $\nu=1$ (or fitted). Output `results/fss_extrapolation.csv`.
- [X] T029b [US3] Report the fitted exponent ν (or the fixed value) as field `fitted_nu` in `results/fss_extrapolation.csv`.
- [X] T030 [US3] Cross‑validate the ML‑derived $T^*$ against magnetic susceptibility χ (from T007) and literature values (verified by T006f).
  - Compute Pearson correlation and p‑value for the XY model BKT transition.
  - **Explicitly perform a hypothesis test** to verify if the detected $T^*$ falls within the confidence interval of the literature value, satisfying the **p-value < 0.05** condition in SC-005.
  - Output `results/cross_validation.json`.
  - **Depends on T007, T006f**.
- [X] T031 [US3] Detect flat variance curves. If no significant peak is found:
  - **DO NOT** use reconstruction error as an alternative detection mechanism.
  - Report "No significant transition detected" together with a confidence interval.
  - **Depends on T026/T027**.
- [X] T032 [US3] Report pseudo‑critical temperatures for L=16 and L=24, the extrapolated $T^*$, and status flags (e.g., "FSS Inconclusive"). Output `results/pseudo_critical.csv`.
- [X] T032b [US3] Ensure all narrative findings are framed as **associational** (no causal claims) and validate the generated report text against this constraint. Output `results/report.txt`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Cross‑Cutting Validation & Physical Verification

- [X] T033a [P] Update `README.md` with usage instructions and a command to run the full pipeline (`bash run_all.sh`).
- [X] T033b [P] Add a detailed FSS methodology section to `README.md`, including the formula $T^*(L) = T_c + a L^{-1/\nu}$ and the default $\nu=1$.
- [X] T033c [P] Add a validation procedures section to `README.md` describing cross‑validation against magnetic susceptibility and bootstrap CI computation.
- [X] T034 [P] Code cleanup and refactoring for performance optimization (vectorization).
- [X] T035 [P] Additional unit tests for edge cases (flat variance, missing data) in `tests/unit/`.
- [X] T036 [P] Run `quickstart.md` validation and ensure all scripts run within the CI time limit.
- [X] T037 [P] **Removed** – seed verification now handled in T008.

---

## Phase 7: Revision & Robustness (Addressing Review Concerns)

**Goal**: Address specific reviewer concerns regarding data integrity, sensitivity analysis, and failure modes.

### Implementation for Sensitivity & Robustness

- [ ] T042 [US3] **GP Kernel Sensitivity Analysis**: Implement a sensitivity sweep in `code/analysis.py` for the Gaussian Process smoothing. Sweep the length-scale hyperparameter $\ell \in \{0.1, 0.5, 1.0, 2.0\}$ (normalized units) and verify that the detected $T^*$ remains stable (within the 95% CI). Output `results/gp_sensitivity.csv` documenting the peak location for each kernel setting.
- [ ] T043 [US3] **Peak Detection Threshold Sensitivity**: Implement a sensitivity sweep for the peak detection thresholds (derivative < -0.01, height > 2σ). Vary the derivative threshold by $\pm 50\%$ and the sigma threshold by $\pm 1\sigma$ to ensure the "No significant transition" flag is not an artifact of a single arbitrary cutoff. Output `results/peak_threshold_sensitivity.csv`.

### Implementation for Edge Cases & FSS

- [ ] T044 [US3] **Mid-Bin Critical Temperature Handling**: Update `code/analysis.py` to handle the case where the detected peak falls exactly between two sampled temperature bins. Implement a quadratic interpolation around the peak to estimate $T^*$ with sub-bin resolution.
- [ ] T045 [US3] **FSS Inconclusive Reporting**: Enhance `code/analysis.py` to explicitly handle the case where only two lattice sizes (L=16, L=24) are available. If the fit for $T_c$ and $\nu$ is unstable (e.g., condition number of the design matrix > 100), the system MUST output `results/fss_extrapolation.csv` with the status "FSS Inconclusive", report the raw pseudo-critical temperatures for L=16 and L=24 **without extrapolation**, and explicitly state that extrapolation to the thermodynamic limit is impossible with the current data quality.
- [ ] T046 [US3] **Flat Variance Fallback Logic**: Refine the logic in `code/analysis.py` for the "flat variance" edge case. Ensure that if the primary latent variance peak is flat, the system **does NOT** attempt reconstruction error variance as a secondary indicator. Instead, report "No significant transition detected" with a confidence interval, strictly adhering to FR-005 and Constitution Principle VI.

### Implementation for Physical Verification

- [ ] T048 [US3] **Susceptibility Calculation Verification**: Add a unit test in `tests/unit/test_utils.py` to verify the magnetic susceptibility calculation $\chi = \frac{1}{N} (\langle M^2 \rangle - \langle |M| \rangle^2)$ against a known analytical or numerical result for a small lattice to ensure the implementation in `code/utils.py` is correct.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion – **BLOCKS** all user stories until finished.
- **User Stories (Phase 3‑5)**: All depend on Foundational phase completion.
  - Stories can proceed in parallel after Foundational.
- **Cross‑Cutting Validation (Phase 6)**: Depends on outputs from US3 (latent variance) and utils (χ) but does not block prior stories.
- **Revision & Robustness (Phase 7)**: Depends on the completion of Phase 5 (US3) to apply sensitivity analyses and edge-case handling.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked **[P]** can run in parallel.
- All Foundational tasks marked **[P]** can run in parallel (within Phase 2) **except** T007 (blocking), T008, T009 (sequenced after T005), and T006e (sequenced after data generation).
- Once Foundational is complete, all user stories can start in parallel (if staffed).
- All tests for a user story marked **[P]** can run in parallel.
- Different user stories can be worked on in parallel by different team members.
- Phase 7 tasks (Sensitivity Analyses) can run in parallel with each other but depend on the core analysis logic from Phase 5.

### Explicit Phase 5 Dependencies

- **Phase 5 (US3) tasks T028, T030, T029, T031, T032** explicitly depend on **T007** (autocorrelation time τ_int and susceptibility χ) and **T006f** (Reference-Validator).
- **T007** depends on **T004a/T004b** (data generation).
- **T006f** depends on **research.md** (input artifact).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
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

- **[P]** tasks = different files, no dependencies.
- **[Story]** label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid vague tasks, same‑file conflicts, hidden cross‑story dependencies.
- **CRITICAL**: All data generation must use **real Monte Carlo simulations** (no synthetic/fake data) to satisfy FR‑001 and the "Real data + real results" rule. T004a/T004b enforce this by raising `RuntimeError` on failure.
- **CRITICAL**: All tasks must respect the 6‑hour time and 7 GB RAM limits. If a task risks exceeding this, it must include partial‑result reporting logic (T023b).
- **CRITICAL**: Task ordering respects data flow: `code/utils.py` (T007) and `code/data_generation.py` (T004a/b) **MUST** be completed before `code/analysis.py` (T026‑T032) which depends on them.
- **CRITICAL**: Phase 7 tasks (T042-T048) are mandatory revisions to address concerns regarding sensitivity of peak detection, and robustness of FSS extrapolation. T040 was removed as its logic is now integrated into T004a/b.
- **CRITICAL**: T031 and T046 strictly forbid using reconstruction error as a secondary indicator for $T^*$ detection, adhering to FR-005.
- **CRITICAL**: T006f ensures literature citations are verified before analysis, satisfying Constitution Principle II.