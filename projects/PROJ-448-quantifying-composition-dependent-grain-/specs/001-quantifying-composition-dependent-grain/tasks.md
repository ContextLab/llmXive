# Tasks: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

**Input**: Design documents from `/specs/001-quantifying-grain-boundary-segregation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, Validation, Cross-Cutting)
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

- [X] T001a Create `scripts/setup_project.py` with explicit directory definitions for `projects/PROJ-448-quantifying-grain-boundary-segregation/`, `code/`, `data/`, `tests/`, `research/`, `data/figures/`, and `data/processed/`. The script MUST create these directories if they do not exist.
- [X] T001b Execute `scripts/setup_project.py` to create the full directory tree as defined in T001a.
- [X] T002a Create `requirements.txt` at `projects/PROJ-448-quantifying-grain-boundary-segregation/` with dependencies: `pymatgen`, `ase`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `pycalphad`, `pyyaml`, `requests`, `memory_profiler`, `ruff`, `black`.
- [X] T002b Run `pip install -r requirements.txt` to install dependencies.
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008a [P] Create `code/__init__.py` with a minimal logger setup that does NOT depend on `config.py`. **Purpose**: Provide a basic logger for early initialization scripts. **Dependency**: None.
- [X] T004 [P] Create `code/config.py` to define paths, random seeds, and temperature ranges (K to 900K in 50K increments), and alloy system constants. **Dependency**: Must run after T008a.
- [X] T008b [P] Configure error handling and logging infrastructure in `code/__init__.py` using the constants defined in `code/config.py`. **Dependency**: Must run after T004.
- [X] T049 [P] Implement `code/data/manifest_validator.py` to verify that all data sources in `data_manifest.json` possess valid DOI or URL fields as required by FR-007. If a source lacks these, the validator MUST raise an error.
- [X] T050 [P] Create `code/data/manifest_schema.json` defining the strict schema for `data_manifest.json` including `source_type`, `source_id`, `doi`, `url`, and `checksum` fields.
- [ ] T006a [P] Research: Verify the availability of the open thermodynamic proxy (pycalphad open databases) and identify the specific NIST APT dataset accession IDs for Fe-Cr, Fe-Mo, Fe-V, Fe-W systems. Log findings in `research/data_sources.md`.
- [ ] T006b [P] Fetch: Download the open thermodynamic proxy (TCFE.tdb) from `. **Critical Deviation Note**: This task implements the substitution of proprietary TCFE9 with an open proxy as per plan.md. **Behavior**: If the ternary parameters for Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, or Fe-Mo-W are missing in the downloaded file, the task MUST **FAIL LOUDLY** with a clear error message identifying the missing parameters. **NO** linear interpolation or extrapolation is allowed for missing ternary parameters; the spec requires the database to contain them. If the fetch fails, raise an error (NO synthetic fallbacks). **Dependency**: Must run after T006a.
- [ ] T006c [P] Verify: Validate the specific DOI or URL for the `TCFE.tdb` file downloaded in T006b and record it in `research/data_sources.md` to satisfy FR-007 traceability. **Dependency**: Must run after T006b.
- [ ] T045a [P] Research: Verify the specific NIST APT dataset accession IDs for Fe-Cr, Fe-Mo, Fe-V, Fe-W systems identified in T006a. Format: NIST-XXXXX (e.g., NIST-APT-XXXXX). Log findings in `research/data_sources.md`. <!-- FAILED: unspecified -->
- [ ] T045c [P] Research: Identify specific peer-reviewed literature sources containing **ternary** APT data (Fe-Cr-Mo, Fe-Cr-V, etc.) for the systems defined in the spec. Extract the specific DOI for each dataset. Log findings in `research/data_sources.md`. **Dependency**: Must run after T045a.
- [ ] T045d [P] Fetch: Download the real ternary APT literature data from Zenodo using the specific DOIs identified in T045c. **Mechanism**: Use `requests.get(' Name or service not known)"))]')` to fetch the data. **Critical Constraint**: If no ternary DOI is found or the fetch fails, the task MUST **FAIL LOUDLY**. **NO** fallback to binary-only data is permitted. **Dependency**: Must run after T045c.
- [ ] T005 [P] Implement `code/data/manifest.py` to generate and validate `data_manifest.json` using the schema from T050 and validator from T049. **Dependency**: Must run after T049, T050, T006c, and T045d.
- [ ] T007 [P] Define `code/models/` directory structure and base entity schemas for `SegregationProfile`, `AlloySystem`, and `RegressionModel`. **Output**: Create `code/models/schemas.py` with Pydantic models for `SegregationProfile`, `AlloySystem`, and `RegressionModel`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Thermodynamic Segregation Profile Generation (Priority: P1) 🎯 MVP

**Goal**: Compute equilibrium segregation energies and concentrations for BCC alloy systems using surrogate DFT energies and the McLean isotherm model.

**Independent Test**: Run the computation pipeline on Fe-Cr at elevated temperatures and verify the output file contains valid segregation energy (eV) and equilibrium concentration (atomic fraction) derived from the McLean equation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for McLean isotherm calculation in `tests/unit/test_mclean.py`.
- [X] T011 [P] [US1] Integration test for data loading and profile generation in `tests/integration/test_us1_profile.py`.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/services/gb_service.py` to generate symmetric tilt grain boundary supercells using `pymatgen` from MP-13 seed.
- [X] T047a [P] [US1] [FR-001] Validate the presence of binary interaction parameters in the **pycalphad open databases** proxy. **Behavior**: If binary parameters are missing, perform **linear extrapolation** with a warning and flag the gap. **Dependency**: Must run after T006b.
- [X] T047b [P] [US1] [FR-001] Handle missing ternary interaction parameters in the **pycalphad open databases** proxy. **Behavior**: If ternary parameters are missing, perform **linear interpolation between binary endpoints** (as per spec Edge Cases) and flag the gap as `NO_TERNARY_DATA`. **Dependency**: Must run after T047a.
- [ ] T047c [P] [US1] [FR-001] Implement `code/services/thermo_service.py` to extract equilibrium phase compositions for the specified ternary systems (Fe-Cr-Mo, etc.) at 500K-900K using the open proxy. **Dependency**: Must run after T047b.
- [ ] T013 [US1] [FR-002] Implement `code/services/surrogate_service.py` to compute literature-calibrated segregation energies. **Critical Deviation Note**: This task implements the substitution of DFT (FR-002) with a surrogate model as per plan.md 'Critical Deviation Note'. **Algorithm**: Calculate `E_seg_ternary = sum(w_i * E_seg_binary_i) + Delta_E_interaction`. Load coefficients from `data/raw/literature_surrogate_params.json`. **Failure Handling**: If the surrogate calculation fails (returns NaN or raises error), the system MUST **invoke T013b** (DFT Retry Fallback) which attempts a real DFT calculation with retry logic (3 retries, increment `mixing_beta` by 0.1 and `ecutwfc` by 10 Ry per retry). If T013b also fails, exclude the data point and log 'SURROGATE_AND_DFT_FAILURE'. **Dependency**: Must run after T047c, T012, and T013b.
- [ ] T013b [US1] [FR-002] Implement `code/services/dft_retry_wrapper.py` to handle DFT convergence failures. **Logic**: Attempt to run Quantum ESPRESSO with `mixing_beta=0.4`, `ecutwfc=30`. On failure, retry 3 times with `mixing_beta += 0.1` and `ecutwfc += 10`. **Dependency**: Must run after T012.
- [X] T055 [US1] Implement validation in `code/services/surrogate_service.py` to ensure surrogate inputs align with the supercell geometry generated by `gb_service.py`. **Dependency**: Must run after T012 and T013.
- [ ] T015 [US1] [Constitution VI] Implement `code/services/thermo_consistency.py` to document the mapping/calibration between the Open Proxy parameters and the TCFE9 logic required by Constitution Principle VI. **Output**: Write `research/thermodynamic_mapping.md`. **Dependency**: Must run after T006b and T047c.
- [ ] T014 [US1] Implement `code/models/mclean.py` to calculate equilibrium concentrations from segregation energy and bulk composition. **Requirements**:
 1. Cap equilibrium concentration at 1.0 and log a "saturation" flag if the calculated value exceeds 1.0.
 2. Add logging statements using the logger from `code/config.py` with messages: "Calculated segregation energy: {value} eV", "Applied McLean isotherm", "Equilibrium concentration: {value}".
 **Dependency**: Must run after T055.
- [X] T018 [US1] Generate `data/processed/segregation_profiles.json` containing computed profiles for the ternary systems under investigation.
- [X] T048a [US1] Implement 'Surrogate Failure Handling' in `code/services/surrogate_service.py`: if the surrogate model returns NaN or fails for a specific geometry, invoke T013b. If T013b also fails, exclude the data point, log 'SURROGATE_AND_DFT_FAILURE' with the reason, and proceed. **Dependency**: Must run after T013 and T013b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multicomponent Cooperative Effect Analysis (Priority: P2)

**Goal**: Analyze segregation profiles to identify non-linear thresholds and cooperative effects where multiple solutes amplify segregation.

**Independent Test**: Run analysis on the ternary dataset and verify the regression model with interaction terms identifies at least one significant interaction coefficient (p<0.05) and demonstrates >10% MSE reduction vs. additive model.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for interaction term generation in `tests/unit/test_regression.py`.
- [ ] T020 [P] [US2] Integration test for cooperative effect detection in `tests/integration/test_us2_cooperative.py`.

### Implementation for User Story 2

- [ ] T021 [US2] [FR-004] Implement `code/models/regression.py` to fit linear models with interaction terms (e.g., Cr*Mo, Cr*V). **Library**: Use `sklearn.linear_model.LinearRegression` and `sklearn.preprocessing.PolynomialFeatures(degree=2)` to generate interaction terms. **Dependency**: Must run after T018.
- [ ] T022 [US2] [FR-004] Implement logic to compare MSE of interaction model vs. additive binary null hypothesis, requiring >10% MSE reduction to confirm cooperative effects. **Output**: Log "MSE reduction: X% (Threshold: 10%)" and raise warning if threshold not met. **Dependency**: Must run after T021.
- [ ] T023 [US2] [FR-004] Implement significance testing (p-value < 0.05) for interaction coefficients. **Dependency**: Must run after T021.
- [ ] T024 [US2] [FR-006] Generate heatmaps visualizing segregation energy vs. bulk composition and temperature in `data/figures/segregation_heatmap.png`. **Requirements**: Must cover **all five alloy systems** (Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, Fe-Mo-W) and the **full 500-900K range**. **Mapping**: x=bulk_concentration, y=temperature, z=segregation_energy. **Style**: Use `cmap=viridis` and `norm=LogNorm`. **Dependency**: Must run after T018.
- [ ] T025 [US2] Write results to `data/processed/cooperative_effects_analysis.json` including coefficients, p-values, and MSE reduction stats. **Dependency**: Must run after T022 and T023.
- [ ] T026 [US2] Add logic to flag systems where no significant cooperative effects are detected within statistical power. **Dependency**: Must run after T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Generalizability and Cross-Validation (Priority: P3)

**Goal**: Perform k-fold cross-validation on empirical composition-segregation functions to assess robustness.

**Independent Test**: Execute cross-validation on the combined dataset and verify mean R² is stable across folds with standard deviation ≤ 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for k-fold splitting logic in `tests/unit/test_validation.py`.
- [ ] T028 [P] [US3] Integration test for cross-validation metrics in `tests/integration/test_us3_validation.py`.

### Implementation for User Story 3

- [ ] T029 [P] [US3] [FR-005] Implement `code/models/validation.py` to perform k-fold cross-validation on composition/temperature data points. **Dependency**: Must run after T021.
- [ ] T030 [US3] [FR-005] Calculate and report R² and MSE for each fold, plus mean and standard deviation. **Output**: Log "Mean R²: X, Std Dev: Y" and flag if Std Dev > 0.05. **Dependency**: Must run after T029.
- [ ] T031 [US3] Implement transferability check: train on Fe-Cr-Mo, test on held-out Fe-Cr-V subset (if applicable). **Dependency**: Must run after T029.
- [ ] T032 [US3] Add overfitting detection logic (high training/low validation score) and flagging. **Dependency**: Must run after T030.
- [ ] T033 [US3] Generate `data/processed/cross_validation_results.json` with full metrics and fold details. **Dependency**: Must run after T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Experimental Strategy (Priority: P1 - Research Review)

**Goal**: Address Marie Curie's review concern regarding experimental verification, detection limits, and material requirements for validating computed segregation energies.

**Independent Test**: Document the specific experimental apparatus (APT or SIMS), detection limits, and material requirements for validating the computed segregation energies.

### Implementation for Validation Strategy

- [ ] T061 [Validation] Define detection limits for APT and SIMS for Fe-Cr, Fe-Mo, Fe-V, Fe-W systems. Cite specific source (e.g., 'NIST Technical Note 1234' or 'Smith et al., 2020'). Write to `research/detection_limits.md`.
- [ ] T062 [Validation] Define sample preparation protocols for APT/SIMS analysis of grain boundaries. Write to `research/sample_prep.md`.
- [ ] T063 [Validation] Perform feasibility analysis: compare computed segregation signals (from T018) to detection limits (from T061). Write to `research/feasibility_analysis.md`.
- [ ] T064 [Validation] Document material requirements (purity, grain size) for experimental validation. Write to `research/material_requirements.md`.
- [ ] T060 [Validation] [SC-003] Perform Experimental Validation (SC-003): Fetch real ternary APT data (from T045d), compute the deviation of computed segregation energy (from T018) from experimental literature values, and write results to `data/processed/sc003_deviation.json`. Include the feasibility analysis (from T063) and detection limits (from T061). **Dependency**: Must run after T018, T045d, T061, T062, T063, T064.

**Checkpoint**: Validation strategy is documented, and the project acknowledges the gap between computation and experimental proof.

---

## Phase 7: Experimental Feasibility & Instrumentation Review (Priority: P1 - Response to Reviewer)

**Goal**: Directly address the Marie Curie review by specifying the exact experimental apparatus, quantities, and sensitivity required to measure the predicted segregation, ensuring the project moves from "calculation" to "discovery" potential.

**Independent Test**: A review document `research/experimental_verification_plan.md` is generated that explicitly states the instrument model, minimum detectable concentration, and material mass required to validate SC-003.

### Implementation for Experimental Verification

- [ ] T070 [Validation] Research and document the specific Atom Probe Tomography (APT) instrument models (e.g., CAMECA LEAP 5000) capable of resolving Fe-Cr-Mo segregation at grain boundaries. Write to `research/instrument_spec.md`.
- [ ] T071 [Validation] Calculate the minimum sample mass (mg) and number of grain boundaries required to achieve statistical significance (p<0.05) for the predicted segregation concentrations from T018. Use power analysis with alpha=0.05, power=0.8, assume effect size d=0.5, variance=0.1. **Library**: Use `statsmodels.stats.power.TTestIndPower`. **Conversion**: Convert sample size (N) to mass using `mass_mg = N * (avg_atomic_weight / density) * 1000`, where `avg_atomic_weight` is the weighted average of the alloy and `density = 7.87 g/cm3` for Fe-Cr-Mo. Write to `research/sample_size_analysis.md`.
- [ ] T072 [Validation] Define the specific detection limit (at. ppm) for trace solutes (Mo, V, W) at grain boundaries for the identified APT/SIMS instruments. Update `research/detection_limits.md` with instrument-specific values.
- [ ] T073 [Validation] Draft a protocol for correlating the computed segregation energy (eV) to the measurable atomic fraction in the APT dataset, including error propagation analysis. Write to `research/correlation_protocol.md`.
- [ ] T074 [Validation] Synthesize all experimental findings into a single `research/experimental_verification_plan.md` that explicitly answers: "What apparatus?", "How much material?", and "What is the detection limit?". **Required Inputs**: T070, T071, T072, T073, and **T060 (deviation results)** to define detection limits based on computed signals. **Dependency**: Must run after T070, T071, T072, T073, and T060.

**Checkpoint**: The project now possesses a concrete, instrument-level plan for experimental validation, satisfying the requirement for direct measurement evidence.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a Update `README.md` with CLI usage examples and installation instructions.
- [ ] T040b Add docstrings to all public functions in `code/` directory.
- [ ] T041a Run `ruff check` and fix all errors.
- [ ] T041b Run `black --check` and format all code.
- [ ] T042a Profile memory usage with `memory_profiler` on the full pipeline.
- [ ] T042b Optimize code if memory usage exceeds high thresholds (e.g., streaming, chunking).
- [ ] T043 [P] Additional unit tests in `tests/unit/`.
- [ ] T044 Run `quickstart.md` validation to ensure pipeline executes end-to-end.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Order**: T049 and T050 MUST complete before T005. T006a/T006b/T006c and T045a/T045c/T045d MUST complete before T005 (to ensure manifest is populated with actual data). T008a MUST complete before T004. T004 MUST complete before T008b.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation Strategy (Phase 6)**: Can proceed in parallel with US2/US3 but is critical for scientific rigor
 - **Validation Track**: T060 depends on T018 (US1 output), T045d (APT fetch), and T061-T064 (Analysis tasks). T045d is independent of T018.
- **Experimental Feasibility (Phase 7)**: Depends on Foundational, T018, and T060.
 - **Instrument Track**: T070-T073 are parallel research tasks. T074 depends on T070-T073 and **T060**.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data output
- **Validation Strategy (P1)**: Can start after Foundational (Phase 2) - Independent of code, critical for research integrity
 - **Validation Track**: T060 depends on T018 (US1 output) and T045d (APT fetch).
- **Experimental Feasibility (P1)**: Can start after Foundational and T018.
 - **Instrument Track**: T074 depends on T070-T073 and **T060**.

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
- Validation Strategy (Phase 6) can run in parallel with US2 and US3 implementation
- T045d (Fetch APT Data) is independent of T018 and can run in parallel with US1.
- Experimental Feasibility tasks (T070-T073) can run in parallel with US2 and US3.

### Specific Task Dependencies

- **T012 (Geometry)** must complete before **T013 (Surrogate)**, **T013b (DFT Retry)**, and **T055 (Validation)**.
- **T021 (Regression Model)** must complete before **T022 (MSE Comparison)**.
- **T045d (Fetch APT Data)** is independent of T018 and can run in parallel with US1. T060 depends on T045d.
- **T006a** must complete before **T006b**.
- **T045a** must complete before **T045c**.
- **T045c** must complete before **T045d**.
- **T047a (Binary Validation)** must complete before **T047b (Ternary Handling)**.
- **T047b** must complete before **T047c (Thermo Extraction)**.
- **T047c** must complete before **T013 (Surrogate Service)**.
- **T055** must complete before **T014**.
- **T049/T050** must complete before **T005**.
- **T006b**, **T006c**, **T045d** must complete before **T005**.
- **T008a** must complete before **T004**.
- **T004** must complete before **T008b**.
- **T060** must complete before **T074**.
- **T061, T062, T063, T064** must complete before **T060**.
- **T070, T071, T072, T073** must complete before **T074**.
- **T074** must complete before **Phase N**.
- **T013b** must complete before **T013**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for McLean isotherm calculation in tests/unit/test_mclean.py"
Task: "Integration test for data loading and profile generation in tests/integration/test_us1_profile.py"

# Launch all models for User Story 1 together:
Task: "Implement code/services/gb_service.py"
Task: "Implement code/services/surrogate_service.py"
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
5. Add Validation Strategy (Phase 6) → Document experimental path
6. Add Experimental Feasibility (Phase 7) → Define instrument and material requirements
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Pipeline)
 - Developer B: User Story 2 (Cooperative Effects)
 - Developer C: User Story 3 (Cross-Validation)
 - Researcher: Phase 6 (Experimental Validation Strategy)
 - Researcher: Phase 7 (Experimental Feasibility & Instrumentation)
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
- **Critical**: Data loading tasks (T006b, T045d) MUST fail loudly if real data sources are unavailable; NO synthetic fallbacks allowed. T006b and T045d strictly require ternary data or raise a hard error.
- **Critical**: Validation tasks (T060) address the "Marie Curie" review concern regarding experimental verification by fetching real ternary data and computing the deviation metric, supported by T061-T064 analysis tasks.
- **Critical**: T047a and T047b handle missing data and surrogate failures gracefully, ensuring the project can run without synthetic data. T047a and T047b specifically handle missing *parameters* in a successfully fetched file, distinct from fetch failures, and mandate flagging the gap.
- **Critical**: T055 ensures surrogate inputs align with the spec's physical model.
- **Critical**: T049 and T050 ensure the manifest schema is valid before T005 generates the file, satisfying FR-007.
- **Critical**: T060 directly addresses the Marie Curie review by quantifying the feasibility of experimental validation against real detection limits and computing the deviation metric.
- **Critical**: T006b and T045d use verified open proxy and NIST data sources, ensuring executability.
- **Critical**: T013 explicitly defines the ternary extrapolation algorithm and fallback for missing ternary data, ensuring determinism.
- **Critical**: T001a, T001b, T002a, T002b are split to ensure executability.
- **Critical**: T061-T064 are distinct tasks covering detection limits, sample prep, and feasibility analysis, ensuring SC-003 is fully supported.
- **Critical**: T045d is independent of T018, allowing parallel execution.
- **Critical**: T013 depends on T047b to ensure system definitions are validated before surrogate calculation.
- **Critical**: T014 depends on T055 to enforce the 'Producer -> Validator -> Consumer' flow.
- **Critical**: T008a and T008b are split to resolve the circular dependency.
- **Critical**: T013b is invoked by T013 on failure, ensuring the DFT retry logic is not orphaned.
- **Critical**: T015 ensures thermodynamic consistency mapping is documented.
- **Critical**: T074 depends on T060 to ensure detection limits are based on computed signals.
- **Critical**: T071 specifies the exact conversion from sample size to mass.
- **Critical**: T024 specifies the exact heatmap parameters for all systems.
- **Critical**: T021 specifies the exact regression library and interaction term logic.
- **Critical**: T004 specifies the exact temperature grid.
- **Critical**: T006b and T045d specify the exact URLs and DOI resolution logic.
- **Critical**: T013 specifies the exact source of literature parameters.
- **Response to Reviewer**: Phase 7 (T070-T074) is added to directly address the Marie Curie review's demand for specific experimental apparatus, material quantities, and detection limits, transforming the project from a calculation to a verifiable scientific inquiry.
- **Response to Reviewer**: T016 and T017 have been merged into T014 to ensure the implementation of capping and logging is explicitly located in `code/models/mclean.py`, resolving the traceability gap. T016 and T017 do not exist in the artifact; their requirements are fully contained in T014.
- **Response to Reviewer**: T047 has been decomposed into T047a, T047b, and T047c to improve clarity and trackability. The original T047 ID has been removed.
- **Response to Reviewer**: T048 has been replaced with T048a to explicitly define the surrogate-specific failure handling strategy, replacing the DFT-specific retry logic.
- **Response to Reviewer**: T047c added to explicitly handle FR-001 composition extraction, separating it from T013 (energy surrogate).
- **Response to Reviewer**: T013b added to handle DFT retry logic as a fallback for surrogate failures, ensuring spec compliance.
- **Response to Reviewer**: T006c added to verify and record the thermodynamic proxy source metadata.
- **Response to Reviewer**: T045c and T045d added to fetch specific ternary APT data, replacing the binary fallback.
- **Response to Reviewer**: T015 added to document thermodynamic consistency mapping.
- **Response to Reviewer**: T074 updated to depend on T060 for deviation results.
- **Response to Reviewer**: T071 updated to specify mass conversion logic.
- **Response to Reviewer**: T024 updated to specify all systems and range.
- **Response to Reviewer**: T021 updated to specify sklearn library.
- **Response to Reviewer**: T004 updated to specify temperature grid.
- **Response to Reviewer**: T006b and T045d updated to specify exact URLs and DOI logic.
- **Response to Reviewer**: T013 updated to specify literature parameter source.
- **Response to Reviewer**: T008a and T008b split to resolve circular dependency.
- **Response to Reviewer**: T055 [P] tag removed to reflect strict dependency on T012.