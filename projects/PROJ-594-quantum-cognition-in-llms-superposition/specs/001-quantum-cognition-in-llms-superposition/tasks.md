# Tasks: Quantum Cognition in LLMs: Superposition States for Ambiguous Reasoning

**Input**: Design documents from `/specs/001-quantum-cognition-in-llms-superposition/`
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

- [ ] T001a [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/code/` directory and `__init__.py`
- [ ] T001b [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/data/raw/` directory and `.gitkeep`
- [ ] T001c [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/data/results/` directory and `.gitkeep`
- [ ] T001d [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/tests/unit/` directory and `__init__.py`
- [ ] T001e [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/tests/contract/` directory and `__init__.py`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (torch-cpu, transformers, datasets, scikit-learn, numpy)
- [ ] T003 [P] Configure linting (flake/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Create `code/utils/complex_ops.py` implementing `to_complex`, `phase_shift`, `vector_add`, `born_rule` with `torch.complex64`
- [ ] T005 [P] Create `code/utils/logging.py` with `detect_nan_inf` and `safe_normalize` utilities
- [ ] T006 Create `code/data/download_wic.py` to fetch WiC from SuperGLUE via `datasets.load_dataset("super_glue", "wic")`
- [ ] T007 Create `code/models/baseline_bert.py` implementing frozen BERT inference (no gradient computation)
- [ ] T008 Create `code/models/bert_adapter.py` skeleton for the complex-valued adapter (linear projection to R^d + I^d)
- [ ] T009 Setup environment configuration management (seed pinning, device selection `cpu`, batch size 8)
- [ ] T009a [P] [Foundational] Implement CPU pinning wrapper script `code/utils/cpu_pinning.sh` that executes `taskset --cpu-list 0` for all experiment runners, satisfying SC-004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Real-Valued Evaluation (Priority: P1) 🎯 MVP

**Goal**: Establish a rigorous, reproducible baseline using frozen BERT on the WiC dataset to serve as the control condition.

**Independent Test**: The system can be fully tested by loading the frozen BERT model, running inference on the WiC test split, and outputting a JSON file containing accuracy and macro-F1 scores. No complex-valued logic is required for this test.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for baseline metrics schema in `tests/contract/test_baseline_schema.py`
- [ ] T011 [P] [US1] Integration test for WiC data loading and frozen BERT inference in `tests/integration/test_baseline_wic.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/experiments/run_baseline.py` to load frozen BERT, process WiC, and output `data/results/baseline_metrics.json`
- [ ] T013 [US1] Implement stability check in `code/experiments/run_baseline.py`: run multiple seeds, add an assertion that raises an error if metric variance > 0.02 across runs.
- [ ] T015 [US1] Add error handling for `[UNK]` tokens in WiC dataset processing

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Complex-Valued Interference Implementation (Priority: P1)

**Goal**: Implement the core quantum-inspired adapter: mapping real-valued hidden states to complex vectors, applying context-dependent phase shifts, performing vector addition (superposition), and applying the Born rule (with softmax normalization).

**Independent Test**: The system can be tested by injecting synthetic complex vectors (known phase and amplitude) into the adapter, performing the interference operation, and verifying that the output probability matches the theoretical squared magnitude of the sum (normalized via softmax).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for destructive interference ($c_1=1, c_2=-1 \to P=0$) in `tests/unit/test_complex_ops.py`
- [ ] T017 [P] [US2] Unit test for constructive interference ($c_1=1, c_2=1 \to P=1$ after softmax) in `tests/unit/test_complex_ops.py`
- [ ] T018 [P] [US2] Contract test for complex adapter output schema in `tests/contract/test_complex_adapter_schema.py`
- [ ] T020b [P] [US2] Verify U_c varies with context: Add unit test in `tests/unit/test_bert_adapter.py` that asserts $U_c$ changes when input context changes (vs. static matrix).

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/models/bert_adapter.py`: Linear projection $\mathbb{R}^d \to \mathbb{C}^d$ (real/imag components)
- [ ] T020 [US2] Implement `code/models/bert_adapter.py`: Context-dependent phase shift operator $U_c$. Input: [batch, seq_len, hidden] real. Operation: compute context embedding via attention pooling over sentence tokens, project to rotation angle theta, apply diagonal phase shift exp(i*theta). Output: [batch, seq_len, hidden] complex. Depends on T019.
- [ ] T021 [US2] Implement `code/models/bert_adapter.py`: Superposition (vector addition) and Born rule ($P_{raw} = \|c_{sum}\|^2$)
- [ ] T022 [US2] Implement `code/models/bert_adapter.py`: Softmax normalization $P_{final} = \frac{e^{P_{raw}}}{e^{P_{raw}} + e^{P_{alt}}}$
- [ ] T023a [US2] [Foundational] Define the FR-009 loss function: Implement `code/models/loss_utils.py` with the specific formula `loss += lambda * (1 + torch.cos(phase_diff))` for ambiguous tokens, where lambda=0.5. Verify this function produces negative gradients for non-anti-parallel phases.
- [ ] T023 [US2] Implement `code/models/bert_adapter.py`: Loss function with penalty term. Depends on T023a. Integrate the specific phase-penalty logic from T023a into the training loop. Verify gradient drives phases toward anti-parallelism in unit test.
- [ ] T024 [US2] Implement `code/experiments/run_quantum.py` to train the adapter (a limited number of epochs), utilize `detect_nan_inf` from T005, and output `data/results/quantum_metrics.json`.
- [ ] T024a [US2] [FR-006] Ensure `code/experiments/run_quantum.py` explicitly frames all output in `quantum_metrics.json` and inference logs as "associational improvements" to avoid causal claims, satisfying FR-006 for all system outputs.
- [ ] T025 [US2] Verify interference cross-term ($2\text{Re}(c_1 \cdot c_2^*)$) can be negative for ambiguous inputs: Add unit test asserting cross_term < 0 for at least 10% of ambiguous samples, output validation to `data/results/interference_validation.json`.
- [ ] T025b [US2] [SC-003] Implement stability check for the complex-valued model: Modify `code/experiments/run_quantum.py` to run multiple seeds, calculate variance of accuracy/F1, and assert variance < 0.02, satisfying SC-003 for the primary hypothesis.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P2)

**Goal**: Execute a paired statistical test comparing the performance of the complex-valued model against the real-valued baseline across multiple random seeds to determine statistical significance.

**Independent Test**: The system can be tested by running the baseline and the complex model with identical seeds, collecting the paired scores, and verifying that the t-test output correctly calculates the p-value and effect size.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for paired t-test calculation (p-value, t-stat, Cohen's d) in `tests/unit/test_stats_test.py`
- [ ] T028 [P] [US3] Contract test for statistical report schema in `tests/contract/test_stats_schema.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/analysis/stats_test.py`: Paired t-test logic (α=0.05) across multiple seeds
- [ ] T029a [US3] [SC-004] Implement runtime measurement: Add logging in `code/analysis/stats_test.py` to record wall-clock time and peak RAM usage for the full 5-seed run, verifying SC-004 (≤6h, ≤7GB).
- [ ] T029b [US3] [Driver] Implement `code/experiments/run_seed_driver.py` to orchestrate the 5-seed loop for both baseline and complex models, aggregating results into a single JSON for the t-test.
- [ ] T030 [US3] Implement `code/analysis/stats_test.py`: Bootstrap resampling (k=1000 iterations) to calculate confidence intervals for the mean difference.
- [ ] T031 [US3] Implement `code/experiments/run_stats.py` to aggregate `baseline_metrics.json` and `quantum_metrics.json` and output `data/results/stats_report.json`
- [ ] T031b [US3] Implement FR-006 framing in `code/analysis/stats_test.py`: Ensure all generated text in `stats_report.json` explicitly frames results as "associational improvements" and avoids causal claims.
- [ ] T032 [US3] Verify `data/results/stats_report.json` contains p-value, t-statistic, Cohen's d, and 95% CI
- [ ] T033 [US3] Add a unit test in `tests/unit/test_stats_test.py` that mocks data to verify p-value logic (p < 0.05 when diff >= 0.05, p > 0.05 when diff < 0.01).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Ablation & Validation (Priority: P2)

**Goal**: Isolate the contribution of the interference cross-term and validate the quantum formalism against classical alternatives.

### Implementation for Ablation & Validation

- [ ] T034 [P] [Ablation] Implement `code/experiments/run_classical_baseline.py` for Classical Sum-of-Squares baseline ($P = \|c_1\|^2 + \|c_2\|^2$). This task implements the classical probability sum without interference cross-term, serving as the primary ablation condition.
- [ ] T035 [P] [Ablation] Implement `code/experiments/run_magnitude_control.py` for Magnitude-Only control ($P = \|c_1\|^2 + \|c_2\|^2$ without phase shifts). This task serves as the control condition to isolate the interference cross-term in the Quantum model by removing phase interactions entirely.
- [ ] T036 [Ablation] Implement `code/analysis/interference_check.py` to validate graded negative cross-term correlation with ambiguity. Input: list of (ambiguity_score, cross_term_value) pairs. Test: Spearman rank correlation. Output: `data/results/interference_correlation.json` containing correlation coefficient and p-value.
- [ ] T037 [Ablation] Generate `data/results/ablation_metrics.json` comparing Quantum vs. Classical vs. Magnitude-Only
- [ ] T038 [Ablation] Verify that interference cross-term assumption (negative values for ambiguity) holds in ablation results

---

## Phase 7: Documentation & Reviewer Alignment (Priority: P3)

**Goal**: Synthesize findings, address specific reviewer concerns from prior research-stage reviews, and prepare for research completion.

### Implementation for Documentation & Reviewer Alignment

- [ ] T039 [P] [Doc] Update `research.md` to explicitly define the "measurement" operation (token selection) and "observable" (ambiguity resolution) addressing Einstein/Von Neumann concerns. Depends on Phase 6 completion (results available).
- [ ] T040 [P] [Doc] Update `research.md` to clarify the distinction between epistemic uncertainty and ontological superposition, framing results as associational (FR-006). Depends on T031b.
- [ ] T041 [P] [Doc] Update `research.md` with a "Back-of-the-Envelope" section addressing Dyson's decoherence/coherence time concerns (classical approximation vs. physical claim)
- [ ] T042 [P] [Doc] Update `research.md` with a worked example of interference (Feynman's "arrows") showing a concrete case where Quantum $\neq$ Classical probability
- [ ] T043 [P] [Doc] Update `research.md` to explicitly define the inner product and basis vectors for the semantic space (Von Neumann's Hilbert space requirement)
- [ ] T044 [P] [Doc] Update `research.md` to include the measurement protocol (Curie's requirements: observable, control, statistical significance)
- [ ] T045 [P] [Doc] Update `research.md` to address Krakauer's request for a specific ambiguity test case (e.g., pronoun resolution) where superposition diverges from attention
- [ ] T046 [P] [Doc] Update `research.md` to address Wolfram's computational irreducibility question (simple rules vs. complex formalism)
- [ ] T047 [P] [Doc] Update `research.md` to address Lovelace's concern on "operations vs. origin" by explicitly detailing the instruction patterns that generate superposition states without the machine "originating" them.
- [ ] T048 [P] [Doc] Update `quickstart.md` with instructions to reproduce the 5-seed experiment and statistical analysis
- [ ] T049 [P] [Doc] Run `quickstart.md` validation to ensure all scripts execute successfully on CPU-only CI

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Documentation updates in `docs/paper/` (draft manuscript)
- [ ] T051 Code cleanup and refactoring in `code/`
- [ ] T052 Performance optimization: ensure batch size and model size fit within 7GB RAM
- [ ] T053 [P] Additional unit tests for edge cases (NaN, Inf, [UNK]) in `tests/unit/`
- [ ] T054 Security hardening (dependency pinning, environment isolation)
- [ ] T055 Run final validation suite

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Ablation (Phase 6)**: Depends on US1 and US2 completion
- **Documentation (Phase 7)**: Depends on US1, US2, US3, and Ablation completion (results available)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Ablation (Phase 6)**: Depends on US1 and US2 completion
- **Documentation (Phase 7)**: Depends on US1, US2, US3, and Ablation completion (results available)

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
Task: "Contract test for baseline metrics schema in tests/contract/test_baseline_schema.py"
Task: "Integration test for WiC data loading and frozen BERT inference in tests/integration/test_baseline_wic.py"

# Launch all models for User Story 1 together:
Task: "Implement code/experiments/run_baseline.py to load frozen BERT..."
Task: "Implement stability check in code/experiments/run_baseline.py..."
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
   - Developer A: User Story 1 (Baseline)
   - Developer B: User Story 2 (Quantum Adapter)
   - Developer C: User Story 3 (Stats)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (a limited number of cores, constrained RAM, 6h limit). No GPU, no -bit quantization.
- **Data Integrity**: All data must be fetched from real sources (SuperGLUE); no synthetic/fake data generation.
- **Reviewer Alignment**: Phase 7 tasks specifically address concerns from Einstein (measurement/realism), Feynman (arrows/interference), Dyson (coherence), Von Neumann (Hilbert space), Krakauer (test case), Curie (protocol), Wolfram (irreducibility), and Lovelace (operations vs. origin).