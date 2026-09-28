# Tasks: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

**Input**: Design documents from `/specs/001-llmxive-density-horizon/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create directories `data/raw/`, `data/processed/`, `output/plots/`, `code/`, `code/utils/`, `code/config/`, `tests/unit/`, `tests/integration/`, `tests/contract/` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/`. **Verification**: All directories exist and are writable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `entropy.py` utility in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/utils/entropy.py` to calculate Shannon Entropy on UTF-8 byte-level tokens (FR-008). **Requirement**: If Shannon Entropy calculation results in a negligible or zero value, clamp the value to a small positive constant to prevent division-by-zero errors in downstream density calculations. **Verification**: Unit tests in `test_entropy.py` pass, confirming entropy calculation and clamping for zero density values (Edge Case).
- [X] T008 [P] Implement `heuristics.py` utility in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/utils/heuristics.py` to define the composite density formula. **Requirement**: The list of "technical terms" MUST be loaded from a configuration file `code/config/density_terms.json` at runtime. **CRITICAL**: The calculation logic MUST implement the specific formula `Density = 0.6 * Shannon_Entropy + 0.4 * Technical_Token_Ratio` as defined in FR-008. The code must hardcode the weights for the two components; only the term list is external. **Term Generation**: The task MUST include a script `code/generate_terms.py` that generates the default `density_terms.json` with a **fixed, research-defined list** of terms: `["entropy", "retrieval", "context", "density", "horizon", "masking", "trajectory", "agent", "search", "stale"]`. **JSON Schema**: The generated JSON file MUST follow the schema `{"terms": ["string", ...]}`. The task MUST explicitly document this schema and the file path resolution logic (relative to `code/config/`) to ensure the implementer knows exactly how to load it. **Verification**: Unit tests in `test_heuristics.py` pass, confirming the config file is loaded correctly and the 0.6/0.4 formula is applied.
- [X] T009 [P] Create `test_entropy.py` unit test in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/unit/test_entropy.py` to verify entropy calculation, clamping for zero density (value 1e-6), and **logging of zero-density events** (Edge Case, FR-008).
- [X] T010 [P] Create `test_heuristics.py` unit test in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/unit/test_heuristics.py` to verify technical token ratio calculation and config file loading (FR-008).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Trajectory Generation with Controlled Density (Priority: P1) 🎯 MVP

**Goal**: Generate a set of synthetic search trajectories with parameterized semantic density and ground-truth critical evidence injection.

**Independent Test**: The system can be tested by running the generator with fixed seeds and verifying that the output JSON file contains a sufficient number of trajectories where the calculated entropy per token for injected evidence blocks matches the requested density levels (low, medium, high) within a tolerance of ±0.01 bits/token.

### Implementation for User Story 1

- [X] T011 [US1] Implement `generate_trajectories.py` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/generate_trajectories.py` to create synthetic trajectories with controlled density (low/med/high) and critical evidence injection. **Dynamic Count**: The task MUST calculate the required trajectory count (N) dynamically: `N = max(500, num_bins * min_samples_per_bin)`, where `num_bins` is explicitly defined as `density_levels (3) * horizon_levels (10)`, where `horizon_levels` corresponds to the integer range 1 to 10. `min_samples_per_bin` is **10** (derived from FR-003 power analysis). **Deliverable**: Output JSON to `data/raw/trajectories.json` containing an array of trajectory objects. Each object MUST include metadata fields: `evidence_turn_index` (int), `density_value` (float), and `is_critical` (boolean). **Requirements**:
 1. Import and use `entropy.py` and `heuristics.py` from `code/utils/`.
 2. Include clamping logic for zero density values (Edge Case, e-6).
 3. Validate that density is computed solely from input text statistics (FR-007).
 4. **Zero-Density Logging**: When the entropy calculation clamps a value, the script MUST print a structured log entry to **standard output (stdout)** containing the `trajectory_id`, the original calculated entropy, and the clamped value. The JSON schema for this log entry MUST be `{"event": "zero_density_clamp", "trajectory_id": "string", "original_entropy": float, "clamped_value": float}`. This satisfies the spec's Edge Case requirement without imposing an unauthorized file path.
 5. **Verification**: Run a validation check asserting that the calculated entropy per token for injected evidence blocks matches the requested density levels within ±0.01 bits/token. If tolerance is violated, exit with non-zero code and print a detailed error report. (US-1 Independent Test, FR-001, FR-007).
 6. **Seed Support**: Accept a `--seed` argument to ensure reproducible trajectory generation.
 7. **Metadata Validation (Last-Turn Edge Case)**: Before writing the output file, the script MUST validate the metadata structure. Specifically, if `evidence_turn_index` equals the total number of turns in the trajectory (0-based index `T-1`), the script MUST ensure the metadata correctly flags this condition (e.g., by including an `is_last_turn: true` boolean field or ensuring the `evidence_turn_index` is valid for the trajectory length). This ensures downstream tasks can correctly handle the edge case where evidence is at the very end. (Spec Edge Case).
 8. **Alignment with Spec**: The target trajectory count must align with SC-005 (500) for statistical power, while noting that the Plan.md summary mentions [deferred] as a potential future scale. The implementation will default to the Spec's 500 target unless overridden by a CLI argument, ensuring resource constraints (FR-005) are met.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Agent Simulation with Variable Retention Horizons (Priority: P2)

**Goal**: Run a simulation loop where a rule-based agent processes trajectories with varying retention horizons to observe success rate fluctuations.

**Independent Test**: The system can be tested by running the simulation on a small subset of trajectories with a known "ground truth" retention horizon. The system must correctly report "failure" when the retention horizon is set to < 5 turns, and "success" when ≥ 5 turns.

### Implementation for User Story 2

- [X] T014 [US2] Implement `simulate_agent.py` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/simulate_agent.py` to load trajectories and apply retention horizons (1 to T). **Dependency**: This task explicitly depends on **T011** completing successfully and writing `data/raw/trajectories.json`. **Requirements**:
 1. **Data Flow Enforcement**: Before processing, check for the existence and non-zero size of `data/raw/trajectories.json`. If missing, exit with "Data Flow Violation: Trajectory generation not complete".
 2. Implement the "Heuristic Solver" using the specific logistic function `P(retrieval) = sigmoid(α * (density - threshold))` to determine success probabilistically (FR-009). Explicitly define `α` (scaling) and `threshold` (critical density) as **configurable CLI arguments with default values** (e.g., `--alpha [default] --threshold [default]`).
 3. **Reproducibility**: Accept a `--seed` argument. Use this seed to initialize a Random Number Generator (RNG) via `np.random.seed(SEED)` **before** any stochastic calls. Calculate `P(retrieval)` using the deterministic sigmoid function, then sample a binary outcome using `np.random.binomial(1, P(retrieval))`. This ensures the stochasticity is controlled by the seed (Constitution Principle I).
 4. **Strict Horizon Logic**: **DO NOT resize the horizon based on density.** The retention window for each trajectory MUST be exactly the `requested_horizon` passed to the function. The success logic MUST be: `1 if (critical_evidence_turn_index >= current_turn - requested_horizon + 1) AND (agent_heuristic_success = true), else 0` (FR-002). This strict logic is required to measure the *modulation* effect of density on horizon; any dynamic resizing would mask the failure condition and violate the hypothesis.
 5. Implement streaming approach to write results to `data/processed/simulation_logs.csv` immediately after each batch to manage RAM (FR-005).
 6. Handle edge case where critical evidence is at the very last turn ($T$) to ensure horizon $T$ retains it correctly (using the `is_last_turn` flag or index validation from T011).
 7. **Memory Validation**: Implement memory profiling using `memory-profiler` during the run. Parse the log output to extract the "Maximum RSS" value in MB. If Max RSS > 7168 (7 GB), **exit with code 1 and print "MEMORY_LIMIT_EXCEEDED"**. This validation must be internal to the script.
 8. **File Size & Chunking Verification**: After writing the CSV, verify that the file size remains within acceptable limits for the system and that the file was written in chunks by parsing the line count and checking for consistent chunk boundaries. If verification fails, exit with code 1.
 9. **Smoke Test**: Generate a deterministic fixture `data/processed/smoke_test_subset.json` programmatically within the task (or a helper script) containing **a small set of trajectories** with known `evidence_turn_index` and `density_value`. Run the simulation on this fixture and assert that horizon < 5 yields failure (0) and horizon ≥ 5 yields success (1) for high-density evidence. Fail loudly if logic deviates. (US-2 Acceptance 1 & 2).
 10. **Seed Support**: Accept a `--seed` argument passed from the pipeline.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for simulation output schema in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/contract/test_simulation_output.py`
- [X] T017 [P] [US2] Integration test for horizon masking logic in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/integration/test_horizon_masking.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Regime Mapping (Priority: P3)

**Goal**: Perform logistic regression (GLM) with natural splines to quantify the interaction effect and generate a 3D surface plot.

**Independent Test**: The system can be tested by feeding it a synthetic dataset where the interaction effect is hard-coded. The regression output must show a statistically significant interaction term (p < 0.05) and the plot must visually display the surface shift.

### Implementation for User Story 3

- [X] T018 [US3] Implement `analyze_results.py` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/analyze_results.py` to load simulation logs and perform logistic regression using `statsmodels`. **Dependency**: This task explicitly depends on **T014** completing successfully and writing `data/processed/simulation_logs.csv`. **Requirements**:
 1. **Data Flow Enforcement**: Before processing, check for the existence and non-zero size of `data/processed/simulation_logs.csv`. If missing, exit with "Data Flow Violation: Simulation logs not complete".
 2. **Stat Power Validation**: Before fitting the GLM, calculate the number of samples per (density, horizon) bin. If any bin has fewer than **10 samples** (threshold derived from Plan Assumption: Cohen f^2=0.15, power), exit with a clear error message detailing the bin counts. This ensures the sample size is sufficient *before* fitting.
 3. Include **natural splines** for the 'horizon' variable with **dynamic degrees of freedom**: Select the `df` that **minimizes the Akaike Information Criterion (AIC)** among candidates `df=3, 4, 5, 6`. This implements the "flexible" requirement using a standard statistical method. **Derivation**: These values (10 samples, df range 3-6) are derived from the power analysis in FR-003 and the Plan assumptions; the script MUST log this derivation to ensure transparency.
 4. Extract and output regression coefficients and **p-values** for the `density * horizon` interaction term to `output/regression_summary.json` (FR-006, SC-001).
 5. Automatically generate `output/hypothesis_summary.md` containing the regression coefficient, p-value, and a boolean `hypothesis_supported` derived from the p-value threshold (p < 0.05) (US-3, Acceptance 3).
 6. **Seed Support**: Accept a `--seed` argument to ensure reproducible random effects if any (though this is a GLM, seed ensures consistent data loading order if shuffled).
 7. **API Specification**: The task MUST use the `statsmodels` formula API with the specific formula string `success ~ density * ns(horizon, df)`, where `ns` is imported from `patsy.dmatrix` or `statsmodels.formula.api` as appropriate for natural splines.
 8. **Verification**: Merged T043: The sample size validation and AIC-based df selection logic are integrated into T018. **Verification**: Confirm `output/regression_summary.json` and `output/hypothesis_summary.md` exist and contain correct data. Verify the boolean logic in the summary file. Verify that the selected `df` is the one minimizing AIC. (FR-003, FR-006).

- [X] T037 [US3] Implement `visualize_results.py` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/visualize_results.py` to generate the 3D surface plot (PNG) visualizing Success Rate vs. Masking Horizon and Semantic Density, specifically the **regime map of optimal retention windows**. **Requirements**:
 1. Use `matplotlib` or `plotly` (CPU-compatible) to render the 3D surface.
 2. Ensure axes are labeled exactly as "Masking Horizon", "Semantic Density", and "Success Rate" (FR-004, SC-002).
 3. Enforce output file size limit of ≤ 5 MB (US-3 Acceptance 2).
 4. Save output to `output/plots/regime_map.png`.
 **Verification**: Verify `output/plots/regime_map.png` exists, is valid PNG, ≤ 5 MB, and contains correctly labeled axes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Contract test for regression output schema in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/contract/test_regression_output.py`
- [X] T024 [P] [US3] Integration test for plot generation in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/integration/test_plot_generation.py`
- [X] T022 [P] [US3] Verify hypothesis summary output: Run `code/analyze_results.py` and confirm `output/hypothesis_summary.md` is created with the correct `.md` extension and contains the expected boolean logic (US-3 Acceptance 3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [P] Update `README.md` with project overview, installation instructions, and usage examples in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/`. **Requirement**: Ensure `README.md` is created in the **repository root** (standard Python project convention), distinct from project-specific documentation under `specs/`. **Verification**: Confirm `README.md` exists in the root and contains the required sections.
- [X] T026 [P] Create `docs/api.md` documenting the public functions in `code/utils/`, `code/generate_trajectories.py`, and `code/simulate_agent.py`
- [X] T027 [P] Create `docs/quickstart.md` with a step-by-step guide to run the full pipeline
- [X] T028 Code cleanup: Remove dead code in `code/generate_trajectories.py`
- [X] T029 Code cleanup: Remove dead code in `code/simulate_agent.py`
- [X] T031 Code cleanup: Standardize import orders in `code/generate_trajectories.py` using `isort`
- [X] T032 Code cleanup: Standardize import orders in `code/simulate_agent.py` using `isort`
- [X] T033 Code cleanup: Standardize import orders in `code/analyze_results.py` using `isort`
- [X] T034 [S] [US2, US3] Performance optimization: **SKIPPED** - Logic merged into T014. **Note**: Do not execute this task.
- [X] T035 [P] Additional unit tests: Create `tests/unit/test_simulate_agent.py` covering edge cases: last turn evidence, zero density, and horizon=1. Create `tests/unit/test_analyze_results.py` covering empty bins and df-selection logic.
- [X] T036 [P] Run quickstart.md validation: Execute all commands in `docs/quickstart.md` sequentially. **Requirement**: If any command fails, the script must exit with a non-zero code and log the specific error. Success is defined as all commands returning exit code 0.

---

## Phase O: Visualization & Reporting

**Goal**: Generate the required 3D surface plot and finalize the regime map visualization.
*(Note: Visualization tasks moved to Phase 5. This phase is now a placeholder for future reporting tasks.)*

---

## Phase P: Final Validation & Documentation

**Goal**: Ensure the entire pipeline runs end-to-end and documentation is up to date.

- [X] T038 [P] Create `run_pipeline.sh` script in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/` to orchestrate the full flow: `generate_trajectories.py` → `simulate_agent.py` → `analyze_results.py` → `visualize_results.py`. **Requirements**:
 1. Accept a single `--seed` argument.
 2. **Unified Seed Propagation**: Pass the *exact same* `--seed` value to `generate_trajectories.py`, `simulate_agent.py`, and `analyze_results.py` via CLI arguments (e.g., `python code/generate_trajectories.py --seed $SEED`).
 3. **Data Flow Enforcement**: Check for the existence and non-zero size of `data/raw/trajectories.json` before invoking `simulate_agent.py`. If missing, fail immediately with "Data Flow Violation: Trajectory generation not complete".
 4. Check for the existence and non-zero size of `data/processed/simulation_logs.csv` before invoking `analyze_results.py`. If missing, fail immediately with "Data Flow Violation: Simulation logs not complete".
 5. Include error handling to stop on failure and log exit codes.
- [X] T039 [P] Execute the full pipeline using `run_pipeline.sh` on a small subset (e.g., a limited number of trajectories) to verify end-to-end data flow and output generation. **Verification**: All expected output files (`data/raw/*.json`, `data/processed/*.csv`, `output/regression_summary.json`, `output/hypothesis_summary.md`, `output/plots/regime_map.png`) are generated and valid.
- [X] T040 Update `docs/quickstart.md` with the final `run_pipeline.sh` instructions and expected output locations.

---

## Phase Q: Review Remediation (Critical Fixes)

**Goal**: Address specific reviewer concerns regarding data flow, reproducibility, and statistical validity.
*(Note: Review Fix tasks T041-T045 have been merged into their respective primary implementation tasks (T011, T014, T018) to eliminate redundancy and broken dependencies. This phase is now a placeholder for any future non-redundant fixes.)*

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Visualization (Phase 5)**: Moved from Phase O to Phase 5, immediately following T018
- **Final Validation (Phase P)**: Depends on all implementation phases
- **Review Remediation (Phase Q)**: Tasks merged into T011, T014, T018. No separate execution required.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (T011)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 simulation logs (T014)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Services before endpoints/analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement generate_trajectories.py in code/generate_trajectories.py"
Task: "Implement clamping logic in generate_trajectories.py"

# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for trajectory schema in tests/contract/test_trajectory_schema.py"
Task: "Integration test for density injection logic in tests/integration/test_density_injection.py"
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
- [S] tasks = sequential, depend on previous tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Phase Q**: Review Fix tasks merged into primary implementation tasks to eliminate redundancy.