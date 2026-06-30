# Tasks: Foundation Protocol – Coordination Layer for Agentic Society

**Input**: Design documents from `/specs/feature-001-foundation-protocol/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED for MVP to ensure contract compliance and regression prevention.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create root project structure: `projects/PROJ-628-foundation-protocol-a-coordination-layer/` and verify existence via `tree` or `ls`.
- [ ] T001b Create sub-directories: `code/`, `code/foundation_protocol/`, `code/agents/`, `code/benchmarks/`, `code/experiments/`, `code/reports/`, `code/data/`, `code/tests/`, `data/`, `results/`, `state/`, `docs/`.
- [ ] T002 Initialize Python 3.10 project with `code/requirements.txt` containing pinned versions: `pettingzoo==1.24.0`, `stable-baselines3==2.3.0`, `numpy==1.26.0`, `pandas==2.1.0`, `scipy==1.11.0`, `ed25519==1.5`, `pyyaml==6.0.1`, `jinja2==3.1.2`, `statsmodels==0.14.0`, `pytest==7.4.0`, `pytest-cov==4.1.0`, `pytest-randomly==3.15.0`, `jsonschema==4.19.0`, `ruff==0.1.0`, `black==23.0.0`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools with pre-commit hooks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Define `MessageEnvelope` schema and generate `contracts/dataset.schema.yaml` with fields: `sender_id`, `receiver_id`, `timestamp`, `signature`, `payload_size`, `checkpoint_ref`.
- [ ] T005 Define `MetricRecord` schema and generate `contracts/metrics.schema.yaml` with fields: `seed`, `protocol`, `episode_length`, `msg_count`, `bytes_sent`, `recovery_success`, `recovery_latency`, `task_success`.
- [ ] T006a [P] Implement `code/foundation_protocol/utils.py` with function `log_seed(seed: int)` and `get_hash(file_path: str) -> str` for deterministic seed logging (FR-008).
- [ ] T006b [P] Implement `scripts/hash_artifacts.py` to generate SHA-256 checksums for all files in `data/` and `code/` and write to `state/artifact_hashes.json`.
- [ ] T007b [P] Implement `code/foundation_protocol/checkpoint.py` as a shared module for checkpointing logic (serialization, loading) used by both `middleware.py` and `direct_comm.py`.
- [ ] T007 [P] Implement `code/foundation_protocol/direct_comm.py` (Native Direct Communication Baseline) ensuring logic equivalence with middleware; CRITICAL: Must import `checkpoint` from shared module. Verify logic equivalence by running `tests/test_direct_vs_middleware.py` to confirm identical output hashes for same input.
- [ ] T008 [P] Implement `code/foundation_protocol/middleware.py` (routing, signing, checkpointing) importing `checkpoint` from shared module.
- [ ] T008b [P] Implement `code/foundation_protocol/wrappers.py` to wrap legacy protocols (MCP, A2A) with `FoundationProtocol` API; ensure wrappers can be instantiated and passed messages (functional, not mocks) for API compatibility testing ONLY; NOT for statistical baseline execution.
- [ ] T009 Implement `code/data/generate_spear.py` to generate synthetic audit logs (INPUT DATA) for the SPEAR benchmark, structured to be consumed by the simulation runners. Output must be deterministic based on multiple random seeds.
- [ ] T009b Implement `code/data/generate_seeds.py` to generate deterministic seed configurations for Hanabi and Resource Allocation tasks.
- [ ] T010 Implement `code/data/verified_datasets.yaml` listing all data sources (pettingzoo, IRM4MLS, SPEAR) and checksums.
- [ ] T011b Verify open-source IRM4MLS implementation: Identify and verify the open-source implementation of the IRM4MLS methodology as required by Plan Phase 0. Record verification status in `docs/verification_log.md`.
- [ ] T011 [P] Implement `code/benchmarks/resource_alloc_runner.py` (IRM4MLS simulation) with inputs: `N_agents`, `resource_constraints`; output: `MetricRecord` rows; ensuring CPU-only compatibility.
- [ ] T012 [P] Implement `tests/test_schema_validation.py` (unit test) to validate schema generation logic against `contracts/*.schema.yaml` (does not require runtime logs).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Evaluate Efficiency Gains in a Cooperative Game (Priority: P1) 🎯 MVP

**Goal**: Demonstrate that the Foundation Protocol reduces episode length and message count compared to the Native Direct Communication baseline in Hanabi.

**Independent Test**: Execute Hanabi benchmark with multiple seeds for Foundation and Native Direct protocols; verify mean episode length ≤ 95% of baseline and mean messages ≤ 90% of baseline.

### Tests for User Story 1 (REQUIRED)

- [ ] T013 [P] [US1] Contract test for Hanabi metrics schema in `tests/contract/test_hanabi_metrics.py` with function `test_schema_compliance` asserting logs match `contracts/metrics.schema.yaml`.
- [ ] T014 [P] [US1] Integration test for baseline vs. intervention comparison in `tests/integration/test_hanabi_comparison.py` with function `test_comparison_logic` asserting data generation runs for Foundation and Native Direct protocols.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/agents/ppo_agent.py` (Pre-trained PPO, Inference-only, CPU mode).
- [ ] T016 [US1] Implement `code/agents/rule_based.py` and `code/agents/heuristic.py`.
- [ ] T017 [US1] Implement `code/benchmarks/hanabi_runner.py` with message logging (FR-003) supporting Foundation Protocol and Native Direct Communication.
- [ ] T018 [US1] Implement `code/experiments/run_simulation.py` to orchestrate 30 seeds × 2 protocols (Foundation, Native Direct) for Hanabi.
- [ ] T019 [US1] Implement `code/experiments/stats_analyzer.py` with PRIMARY analysis: Linear Mixed-Effects Models (LMM); SENSITIVITY analysis: McNemar's test, paired t-tests, Bonferroni correction (FR-006).
- [ ] T020a [US1] Implement sensitivity analysis sweep for BINARY metrics (recovery_success, task_success) using McNemar's test across α ∈ {0.01, 0.05, 0.10}; Generate `results/sensitivity_binary.csv` with columns: `alpha`, `metric`, `p_value`, `significant`.
- [ ] T020b [US1] Implement sensitivity analysis sweep for CONTINUOUS metrics (episode_length, messages, bandwidth, latency) using paired t-tests across a range of significance levels and Cohen's d calculation; Generate `results/sensitivity_continuous.csv` with columns: `alpha`, `metric`, `p_value`, `cohen_d`, `significant`.
- [ ] T021 [US1] Verify logic equivalence: Run `tests/test_direct_vs_middleware.py` to confirm identical agent logic in Baseline and Intervention.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Assess Robustness to Agent Failures (Priority: P2)

**Goal**: Validate recovery success and latency under injected crashes using the Foundation Protocol vs. Baseline.

**Independent Test**: Run smart-contract auditing workflow with crash injection at an intermediate progress stage (single and simultaneous); verify recovery success ≥ 90% and latency ≤ 1.5× baseline.

### Tests for User Story 2 (REQUIRED)

- [ ] T022 [P] [US2] Contract test for crash injection metrics in `tests/contract/test_crash_metrics.py` with function `test_crash_schema_compliance`.
- [ ] T023 [P] [US2] Integration test for recovery workflow in `tests/integration/test_recovery_workflow.py` with function `test_recovery_logic`.

### Implementation for User Story 2

- [ ] T024 [P] [US2] Implement `code/experiments/crash_injector.py` supporting configurable crash fraction (FR-004) and single-agent crash.
- [ ] T024b [P] [US2] Extend `code/experiments/crash_injector.py` to support simultaneous crash injection of multiple agents at the same timestep.
- [ ] T025 [US2] Implement `code/benchmarks/spear_runner.py` integrating crash injector (single and simultaneous) and checkpointing (shared module).
- [ ] T026 [US2] Extend `code/experiments/run_simulation.py` to handle SPEAR benchmark with crash injection for Foundation and Native Direct protocols.
- [ ] T027 [US2] Update `code/experiments/stats_analyzer.py` to compute recovery success rate and latency statistics; PRIMARY: LMM; SENSITIVITY: McNemar's test (FR-006).
- [ ] T028 [US2] Implement logging for `recovery_success`, `recovery_latency`, and `task_success` in `MetricRecord`.
- [ ] T029 [US2] Verify baseline uses equivalent checkpointing capabilities by confirming `direct_comm.py` imports `code/foundation_protocol/checkpoint.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Measure Communication Overhead Across Tasks (Priority: P3)

**Goal**: Quantify bandwidth consumption across Hanabi, SPEAR, and Resource Allocation tasks.

**Independent Test**: Collect per-episode byte traffic (normalized) for all three tasks; verify Foundation Protocol ≤ 85-90% of baseline.

### Tests for User Story 3 (REQUIRED)

- [ ] T030 [P] [US3] Contract test for bandwidth metrics in `tests/contract/test_bandwidth_metrics.py` with function `test_bandwidth_schema_compliance`.
- [ ] T031 [P] [US3] Integration test for multi-task bandwidth comparison in `tests/integration/test_multi_task_bandwidth.py` with function `test_multi_task_logic`.

### Implementation for User Story 3

- [ ] T032 [P] [US3] Extend `code/benchmarks/resource_alloc_runner.py` with detailed byte-level logging supporting Foundation and Native Direct protocols.
- [ ] T033 [US3] Update `code/experiments/run_simulation.py` to execute all three tasks (Hanabi, SPEAR, Resource) for Foundation and Native Direct protocols.
- [ ] T034 [US3] Implement `code/experiments/stats_analyzer.py` logic for normalized byte-per-episode aggregation; PRIMARY: LMM; SENSITIVITY: Paired t-test (FR-006).
- [ ] T035 [US3] Generate comparative bandwidth reports per task (Hanabi ≤ 90%, others ≤ 85%) comparing Foundation Protocol against Native Direct Communication baseline.
- [ ] T036 [US3] Verify normalization logic divides total bytes by payload size as per spec.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Concerns & Scaling Analysis (Revision Tasks)

**Purpose**: Address specific concerns from prior research-stage reviews regarding scaling laws and institutional safeguards.

### Reviewer Concern: Freeman Dyson (Simulated) - Scaling & Governance Overhead
*Concern: Need a back-of-the-envelope scaling argument for bandwidth/governance at 10⁶, 10⁸, 10¹⁰ agents.*

- [ ] T037b [P] Document the scaling model in `docs/scaling_model.md`: define the mathematical relationship (e.g., Power Law `y = aN^b`) and the singularity condition (marginal cost > marginal benefit).
- [ ] T037 [P] Implement `code/reports/scaling_analysis.py` to compute theoretical bandwidth and cryptographic overhead for N = 10⁶, 10⁸, 10¹⁰ agents using the model from T037b and empirical per-agent metrics.
- [ ] T038 [P] Generate `results/scaling_table.csv` containing estimated bandwidth (Mbps), latency, and governance overhead for the three scales.
- [ ] T039 [US3] Update `code/reports/generate_report.py` to include a "Scaling Implications" section with the generated table and discussion of institutional safeguards (audit trails, decentralized oversight).

### Reviewer Concern: Geoffrey West (Simulated) - Scaling Laws & Singularity
*Concern: Need quantitative analysis of coordination cost scaling with N agents (linear vs. quadratic) and identification of singularity points.*

- [ ] T040 [P] Implement `code/reports/scaling_law_fit.py` to fit empirical data (from multiple seeds) to power-law models (y = aN^b) using the model from Tb, determining if coordination cost scales sublinearly, linearly, or superlinearly.
- [ ] T041 [P] Implement `code/reports/singularity_detector.py` to identify the agent count N where marginal cost (derivative of power law) exceeds marginal benefit, based on the definition in T037b.
- [ ] T042 [US3] Update `code/reports/generate_report.py` to include a "Scaling Regime Analysis" section explaining the physics of the protocol (sustainable vs. collapsing regime).
- [ ] T043 [P] Add visualization `results/scaling_law_plot.png` showing cost vs. N with fitted curves and singularity threshold.

**Note**: Phase 6 tasks T037-T043 depend on completion of Phase 3, 4, and 5 (data generation). They are NOT parallel-safe with data generation.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `docs/` and `quickstart.md`.
- [ ] T045 Code cleanup and refactoring to ensure CPU-only compliance (FR-009).
- [ ] T046 Performance optimization: Profile `run_simulation.py` and refactor to use multiprocessing if single-threaded; optimize `stats_analyzer.py` vectorization to ensure full experiment suite (30 seeds × 3 tasks × 2 protocols) runs within 6 hours.
- [ ] T047 [P] Implement `Makefile` target `make report` to compile LaTeX-style PDF and archive `results/` for Zenodo (FR-010).
- [ ] T048 Run reproducibility check: Re-run 1 seed, verify checksums via `scripts/hash_artifacts.py`.
- [ ] T049 Validate all citations against `data/verified_datasets.yaml`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - T004/T005 (Schemas) must complete before T009/T009b (Data Generation)
  - T007b (Checkpoint) must complete before T007/T008 (Communication)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Reviewer Concerns (Phase 6)**: Depends on completion of US1, US2, US3 (requires empirical data to model scaling)
- **Polish (Phase 7)**: Depends on all desired user stories and reviewer concerns being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Scaling Analysis (Phase 6)**: Depends on data generation from US1, US2, and US3

### Within Each User Story

- Tests are written first but are part of the same task group as implementation (atomic unit).
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT:
  - T007b must precede T007/T008
  - T004/T005 must precede T009/T009b
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Scaling analysis tasks (T037-T043) can run in parallel ONCE data is available (after Phase 5)

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
5. Add Scaling Analysis (Phase 6) → Address reviewer concerns
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: Scaling Analysis (Phase 6) - data dependent
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
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, constrained memory resources, and no GPU. No 8-bit/4-bit quantization or large model training.
- **Data Flow**: Ensure `generate_spear.py` (T009) and `generate_seeds.py` (T009b) run AFTER schema definitions (T004/T005) and BEFORE `hanabi_runner.py` (T017) and `run_simulation.py` (T018, T026, T033).
- **Baseline Definition**: Experiments run Foundation Protocol vs. Native Direct Communication ONLY. Legacy protocols are wrapped for API compatibility but NOT executed as statistical baselines.
- **Statistical Method**: Linear Mixed-Effects Models (LMM) are PRIMARY; McNemar's test (binary) and paired t-tests (continuous) are SENSITIVITY analysis.