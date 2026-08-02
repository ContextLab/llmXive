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

- [X] T001a [P] Create `projects/PROJ-quantum-cognition-in-llms-superposition/code/` directory. Deliverable: Empty directory.
- [X] T001b [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/data/raw/` directory. Deliverable: Empty directory.
- [X] T001c [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/data/results/` directory. Deliverable: Empty directory.
- [X] T001d [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/tests/unit/` directory. Deliverable: Empty directory.
- [X] T001e [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/tests/contract/` directory. Deliverable: Empty directory.
- [X] T002 Initialize Python project with `requirements.txt` (torch-cpu, transformers, datasets, scikit-learn, numpy)
- [X] T003 [P] Create `projects/PROJ-594-quantum-cognition-in-llms-superposition/.flake8` with content: `[flake8] max-line-length = 120 ignore = E203, W503` and `projects/PROJ-594-quantum-cognition-in-llms-superposition/pyproject.toml` with `[tool.black] line-length = 120`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T004 Create `code/utils/complex_ops.py` implementing `to_complex`, `phase_shift`, `vector_add`, `born_rule` with standard complex precision.
- [X] T005 [P] Create `code/utils/logging.py` with `detect_nan_inf` and `safe_normalize` utilities
- [X] T006 Create `code/data/download_wic.py` to fetch WiC from SuperGLUE via `datasets.load_dataset("super_glue", "wic")`
- [X] T007 Create `code/models/baseline_bert.py` implementing frozen BERT inference (no gradient computation)
- [X] T019 [P] [US2] [FR-001, FR-003] Implement `code/models/bert_adapter.py`: Linear projection R^d -> C^d. **Logic**: Define a `nn.Linear` layer mapping BERT hidden states (R^d) to a complex vector (R^d + iR^d). **Implementation**: Create `ComplexAdapter` class with `forward(h_real)` returning `c_complex`. **Constraint**: Freeze all BERT weights (`requires_grad=False`) in the parent class or wrapper. **Verification**: Unit test in `tests/unit/test_bert_adapter.py` asserting `c_complex.dtype == torch.complex64` and BERT weights remain frozen after adapter instantiation. **Dependency**: T006 (data loading), T004 (complex ops).
- [X] T008 [X] [Foundational] [DEPRECATED] Replaced by T019.
- [X] T023a [P] [US2] [Foundational] Define the FR-009 loss function: Create `code/models/loss_utils.py` with function `phase_penalty_loss(phase_diff, lambda=0.5)`. Formula: `loss += lambda * (1 + torch.cos(phase_diff))`. Verify this function produces negative gradients for non-anti-parallel phases in a unit test.
- [X] T023b [P] [US2] [Foundational] Define explicit cross-term calculation: Create `code/models/loss_utils.py` with function `calculate_interference_cross_term(c1, c2)`. Formula: `2 * torch.real(c1 * torch.conj(c2))`. Verify this function can return negative values in a unit test.
- [X] T009a [P] [Foundational] Create `code/config.yaml` with keys: `seed: 42`, `device: cpu`, `batch_size: 8`, `max_epochs: 3`, `timeout_hours: 6`, `max_ram_gb: 7`. **Note**: Values are fixed per SC-004 constraints.
- [X] T009b [P] [Foundational] Create `code/utils/config_loader.py` to parse `config.yaml` and return a `Config` dataclass.
- [X] T009c [P] [Foundational] Implement CPU pinning wrapper script `code/utils/cpu_pinning.sh` that executes `taskset --cpu-list 0` for all experiment runners, satisfying SC-004.
- [X] T009d [P] [Foundational] Implement `code/utils/runtime_monitor.py` with functions `start_timer()`, `check_ram()`, `assert_limits()`. `assert_limits()` must raise an error if runtime > 6h or RAM > 7GB. This utility is to be *called* by execution tasks (T024b, T029a, T072), not run standalone.
- [X] T073 [P] [Foundational] [FR-006] Create `code/utils/framing_utils.py` with function `format_associational_statement(text)`. **Logic**: Ensure all output strings explicitly use "associational" or "correlational" language and avoid "causal" or "deterministic" claims. **Usage**: All tasks generating text output (T012, T023, T024d, T031, T031b) MUST call this utility.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Real-Valued Evaluation (Priority: P1) 🎯 MVP

**Goal**: Establish a rigorous, reproducible baseline using frozen BERT on the WiC dataset to serve as the control condition.

**Independent Test**: The system can be fully tested by loading the frozen BERT model, running inference on the WiC test split, and outputting a JSON file containing accuracy and macro-F1 scores. No complex-valued logic is required for this test.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for baseline metrics schema in `tests/contract/test_baseline_schema.py`
- [X] T011 [P] [US1] Integration test for WiC data loading and frozen BERT inference in `tests/integration/test_baseline_wic.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/experiments/run_baseline.py`. Logic: Load frozen BERT, iterate WiC test split, compute accuracy/macro-F1. **Stability Check**: Run loop for 5 seeds (from `config.yaml`), collect metrics, calculate variance. **Output**: `data/results/baseline_metrics.json` with schema: `{"accuracy": float, "macro_f1": float, "seed": int, "variance_accuracy": float, "variance_macro_f1": float}`. Assert variance < 0.02; raise error if failed. **FR-006**: Use `code/utils/framing_utils.py` (T073) to ensure all output logs and JSON comments frame results as "associational". **Dependency**: T073, T007, T006.
- [X] T012b [P] [US1] [FR-006] Implement framing utility call in `code/experiments/run_baseline.py`. Logic: Wrap all output strings with `framing_utils.format_associational_statement()`. **Dependency**: T073.
- [X] T015 [US1] Add error handling for `[UNK]` tokens in WiC dataset processing. **File**: `code/utils/tokenizer_utils.py`. **Function**: `handle_unk_tokens(token_ids)`. **Logic**: Replace `[UNK]` with a learned embedding or context-based average. **Verification**: Unit test in `tests/unit/test_tokenizer_utils.py` asserting no crash and valid output shape for inputs containing `[UNK]`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Complex-Valued Interference Implementation (Priority: P1)

**Goal**: Implement the core quantum-inspired adapter: mapping real-valued hidden states to complex vectors, applying context-dependent phase shifts, performing vector addition (superposition), and applying the Born rule (with softmax normalization).

**Independent Test**: The system can be tested by injecting synthetic complex vectors (known phase and amplitude) into the adapter, performing the interference operation, and verifying that the output probability matches the theoretical squared magnitude of the sum (normalized via softmax).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for destructive interference ($c_1=1, c_2=-1 \to P=0$) in `tests/unit/test_complex_ops.py`
- [X] T017 [P] [US2] Unit test for constructive interference ($c_1=1, c_2=1 \to P=1$ after softmax) in `tests/unit/test_complex_ops.py`
- [X] T017b [P] [US2] Unit test for explicit cross-term calculation: Verify $2\text{Re}(c_1 \cdot c_2^*)$ can be negative in `tests/unit/test_complex_ops.py`. Input: $c_1=1+0i, c_2=-0.5+0.5i$. Assert cross-term < 0.
- [X] T018 [P] [US2] Contract test for complex adapter output schema in `tests/contract/test_complex_adapter_schema.py`
- [X] T020b [P] [US2] Verify U_c varies with context: Add unit test in `tests/unit/test_bert_adapter.py` that asserts $U_c$ changes when input context changes (vs. static matrix).

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/models/bert_adapter.py`: Linear projection $\mathbb{R}^d \to \mathbb{C}^d$ (real/imag components). **Logic**: Define `nn.Linear(hidden_dim, 2*hidden_dim)` and split output into real/imag parts. **Verification**: Assert output dtype is `torch.complex64`. **Dependency**: T004, T007.
- [X] T020 [US2] Implement `code/models/bert_adapter.py`: Context-dependent phase shift operator $U_c$. Input: [batch, seq_len, hidden] real. Operation: compute context embedding via attention pooling over sentence tokens, project to rotation angle theta, apply diagonal phase shift exp(i*theta). Output: [batch, seq_len, hidden] complex. Depends on T019.
- [X] T021 [US2] Implement `code/models/bert_adapter.py`: Superposition (vector addition) and Born rule ($P_{raw} = \|c_{sum}\|^2$)
- [X] T022 [US2] Implement `code/models/bert_adapter.py`: Softmax normalization $P_{final} = \frac{e^{P_{raw}}}{e^{P_{raw}} + e^{P_{alt}}}$
- [X] T023 [US2] [Foundational] Implement `code/models/bert_adapter.py`: Loss function with penalty term and cross-term logging. **Logic**: Integrate `phase_penalty_loss` (T023a) and `calculate_interference_cross_term` (T023b) into the training loop. **Verification**: Unit test asserts gradient drives phases toward anti-parallelism (e.g., `assert phase_diff > 2.5 radians` after one step). **Dependency**: T023a, T023b.
- [X] T024a [US2] [P] [Ablation] Implement `code/experiments/run_quantum.py` (Training Loop): Train adapter for 3 epochs, integrate `detect_nan_inf` from T005. **Dependency**: T023.
- [X] T024b [US2] [P] [Ablation] Implement `code/experiments/run_quantum.py` (Error Handling): Wrap training in `runtime_monitor` (T009d) via T072 to enforce limits. **Dependency**: T072.
- [X] T024c [US2] [P] [Ablation] Implement `code/experiments/run_quantum.py` (Metrics Serialization): Output `data/results/quantum_metrics.json` with schema: `{"accuracy": float, "macro_f1": float, "loss_epoch_1": float, "loss_epoch_3": float, "seed": int}`. **Verification**: Assert that `quantum_metrics.json` exists and contains float values for `loss_epoch_1` and `loss_epoch_3`. **Dependency**: T023.
- [X] T024d [US2] [US2] [FR-006] Ensure `code/experiments/run_quantum.py` explicitly frames all output in `quantum_metrics.json` and inference logs as "associational improvements" to avoid causal claims, satisfying FR-006 for all system outputs. **Dependency**: T073.
- [X] T025 [US2] [Foundational] Implement cross-term logging during training: Modify `code/experiments/run_quantum.py` to compute `calculate_interference_cross_term` (T023b) for every ambiguous token (label == 1) during the forward pass. Store these values in memory and write them to `data/results/cross_term_log.json` with schema: `{"cross_term_values": [float], "ambiguous_indices": [int]}`. **Verification**: Assert that `cross_term_log.json` exists and contains a list of floats under `cross_term_values`. **Dependency**: T023b.
- [X] T025b [US2] Verify interference cross-term ($2\text{Re}(c_1 \cdot c_2^*)$) can be negative for ambiguous inputs: Add unit test/assertion in `code/analysis/interference_check.py` that reads `data/results/cross_term_log.json`. **Logic**: Assert `min(cross_term_values) < 0`. **Output**: `data/results/interference_validation.json` with schema: `{"min_cross_term": float, "percentage_negative": float, "valid": bool}`. **Dependency**: T025.
- [X] T025c [US2] [SC-003] Implement stability check for the complex-valued model: Modify `code/experiments/run_quantum.py` to run multiple seeds, calculate variance of accuracy/F1, and assert variance < 0.02, satisfying SC-003 for the primary hypothesis.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P2)

**Goal**: Execute a paired statistical test comparing the performance of the complex-valued model against the real-valued baseline across multiple random seeds to determine statistical significance.

**Independent Test**: The system can be tested by running the baseline and the complex model with identical seeds, collecting the paired scores, and verifying that the t-test output correctly calculates the p-value and effect size.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for paired t-test calculation (p-value, t-stat, Cohen's d) in `tests/unit/test_stats_test.py`
- [X] T028 [P] [US3] Contract test for statistical report schema in `tests/contract/test_stats_schema.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/analysis/stats_test.py`: Paired t-test logic (α=0.05) across multiple seeds. **Output**: `data/results/stats_report.json` with schema: `{"p_value": float, "t_statistic": float, "cohens_d": float}`. **Verification**: Assert that file exists and contains valid float values for all keys. **Dependency**: T012, T024c.
- [X] T029a [US3] [SC-004] Implement runtime measurement: Add logging in `code/analysis/stats_test.py` to record wall-clock time and peak RAM usage for the full multi-seed run, verifying SC-004 (≤6h, ≤7GB). **Dependency**: T072 (Full Run Wrapper).
- [X] T029b [US3] [Driver] Implement `code/experiments/run_seed_driver.py` to orchestrate a multi-seed loop for both baseline and complex models, aggregating results into a single JSON for the t-test.
- [X] T030a [US3] [P] [Bootstrap] Define bootstrap parameters: Create `code/analysis/bootstrap_config.py` with `n_iterations: 1000` and a `confidence_level` set to 0.95.
- [X] T030b [US3] [P] [Bootstrap] Implement `code/analysis/stats_test.py`: Bootstrap resampling (k=1000 iterations) to calculate confidence intervals for the mean difference. **Output**: `data/results/bootstrap_ci.json` with schema: `{"ci_lower": float, "ci_upper": float}`. **Verification**: Assert that the confidence interval width is < 0.1. **Dependency**: T030a.
- [X] T031 [US3] Implement `code/experiments/run_stats.py` to aggregate `baseline_metrics.json` and `quantum_metrics.json` and output `data/results/stats_report.json`. **Output Schema**: `{"p_value": float, "t_statistic": float, "cohens_d": float, "ci_lower": float, "ci_upper": float, "conclusion": "significant" | "not_significant"}`. **Mandatory**: `ci_lower` and `ci_upper` MUST be populated by the Bootstrap results from T030b. **Verification**: Assert that `ci_lower` and `ci_upper` are populated by Bootstrap logic from T030b. **Dependency**: T012, T024c, T030b.
- [X] T031b [US3] Implement FR-006 framing in `code/analysis/stats_test.py`: Ensure all generated text in `stats_report.json` explicitly frames results as "associational improvements" and avoids causal claims. **Dependency**: T073.
- [X] T032 [US3] Verify `data/results/stats_report.json` contains p-value, t-statistic, Cohen's d, and a confidence interval. **Validation**: Assert `ci_lower` and `ci_upper` are not null and are populated by Bootstrap logic from T030b. **Dependency**: T031.
- [X] T033 [US3] Add a unit test in `tests/unit/test_stats_test.py` that mocks data to verify p-value logic (p < 0.05 when diff >= 0.05, p > 0.05 when diff < 0.01).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Ablation & Validation (Priority: P2)

**Goal**: Isolate the contribution of the interference cross-term and validate the quantum formalism against classical alternatives.

### Implementation for Ablation & Validation

- [X] T034 [P] [Ablation] Implement `code/experiments/run_classical_baseline.py` for Classical Sum-of-Squares baseline ($P = \|c_1\|^2 + \|c_2\|^2$). This task implements the classical probability sum without interference cross-term, serving as the primary ablation condition.
- [X] T035 [P] [Ablation] Implement `code/experiments/run_magnitude_control.py` for Phase-Randomized Control ($P = \|c_1 + e^{i\phi_{rand}}c_2\|^2$). **Logic**: Apply random phase shifts $\phi_{rand} \sim U(0, 2\pi)$ to $c_2$ before addition, destroying coherent interference while maintaining vector magnitudes. This isolates the *interference* mechanism specifically, distinct from the 'Sum-of-Squares' baseline.
- [X] T036 [Ablation] Implement `code/analysis/interference_check.py`. Input: list of (ambiguity_score, cross_term_value) pairs from `data/results/cross_term_log.json` (fields: `cross_term_values`, `ambiguous_indices`). Test: Spearman rank correlation. **Output**: `data/results/interference_correlation.json` with schema: `{"spearman_correlation": float, "p_value": float, "interpretation": "negative_correlation" | "no_correlation"}`. **Verification**: Assert that file exists and contains a float for `spearman_correlation`. **Dependency**: T025.
- [X] T037 [Ablation] Generate `data/results/ablation_metrics.json` comparing Quantum vs. Classical vs. Magnitude-Only. Schema: `{"quantum_acc": float, "classical_acc": float, "magnitude_acc": float, "interference_contribution": float}`. **Verification**: Assert that file exists and contains valid float values for all keys. **Dependency**: T034, T035.
- [X] T038 [Ablation] Verify that interference cross-term assumption (negative values for ambiguity) holds in ablation results. Logic: Assert `spearman_correlation` in `data/results/interference_correlation.json` is < -0.3. If failed, log warning. Depends on T036.

**Checkpoint**: At this point, all validation and ablation tasks are complete.

---

## Phase 7: Documentation & Reviewer Alignment (Priority: P3)

**Goal**: Synthesize findings, address specific reviewer concerns from prior research-stage reviews, and prepare for research completion.

### Sub-Phase 7A: Research Artifacts (Prerequisite)

- [X] T071 [P] [Doc] Create initial `research.md` skeleton. **Content**: Title, Abstract, Introduction, Methods (summary), Results (placeholders), Discussion (placeholders). **Purpose**: Establish the artifact required for T074-T087.

### Sub-Phase 7B: Reviewer Alignment (Depends on T071, T012, T024c, T031, T037)

- [X] T074 [P] [Doc] [Einstein/Feynman] Update `research.md` to include a concrete worked example (pseudocode + numerical values) demonstrating the "arrows" (amplitudes) adding up and interfering for a specific ambiguous sentence, explicitly distinguishing the quantum calculation from a classical probability sum. Add Section 5.2. **Dependency**: T071.
- [X] T075 [P] [Doc] [Einstein/Von Neumann] Update `research.md` to explicitly define the "measurement" operator as the selection of the token with the highest Born-rule probability, and define the "observable" as the binary ambiguity label, satisfying the requirement for a physical correspondence. Add Section 4.1. **Dependency**: T071.
- [X] T076 [P] [Doc] [Dyson] Update `research.md` with a "Frog's View" section calculating the decoherence budget: estimate the noise floor of the classical CPU operations vs. the magnitude of the phase shifts, explicitly stating that the "superposition" is a classical approximation of a quantum state, not a physical quantum state. Add Section 5.1. **Dependency**: T071.
- [X] T077 [P] [Doc] [Lovelace] Update `research.md` to explicitly list the "instruction patterns" (mathematical operations) that generate the superposition state, clarifying that the machine is executing a defined algorithm and not "originating" the ambiguity. Add Section 5.7. **Dependency**: T071.
- [X] T078 [P] [Doc] [Krakauer] Update `research.md` with a dedicated section on "Pronoun Resolution as a Test Case," detailing how the model handles a specific ambiguous pronoun (e.g., "The trophy doesn't fit in the suitcase because it is too large") and predicting the interference outcome. Add Section 5.5. **Dependency**: T071.
- [X] T079 [P] [Doc] [Wolfram] Update `research.md` to discuss the computational irreducibility of the interference calculation, acknowledging that while the rules are simple (linear algebra), the outcome for complex contexts cannot be predicted without running the full computation. Add Section 5.6. **Dependency**: T071.
- [X] T080 [P] [Doc] [Pauling] Update `research.md` to define the "energy landscape" of the reasoning process by mapping the loss function (FR-009) to a physical potential, explaining how the "resonance" of the superposition state minimizes this potential. **Note**: This task consolidates T080 and T088. Add Section 5.8 "Resonance and Energy Landscapes". **Dependency**: T071.
- [X] T081 [P] [Doc] [Lovelace/Einstein] Update `research.md` to explicitly distinguish between "operations ordered by the engine" (the algorithmic steps of phase rotation and vector addition) and "originating" ambiguity. Add a subsection "The Analytical Engine and Ambiguity" clarifying that the machine performs operations on abstract relations but does not originate the meaning, addressing the distinction between calculation and general symbolic manipulation. **Dependency**: T071.
- [X] T082 [P] [Doc] [Einstein] Update `research.md` to address the "completeness" question directly: Explicitly state whether the model preserves locality (no instantaneous influence between distant tokens) or embraces non-locality, and justify the choice based on the architecture's design (e.g., attention mechanisms). Add a subsection "Locality and Completeness". **Dependency**: T071.
- [X] T083 [P] [Doc] [Feynman] Update `research.md` with a "Worked Example: The Arrows" section containing a concrete numerical trace of a single ambiguous sentence. Show the initial amplitudes (arrows), the phase shifts applied, the vector addition (interference), and the final probability calculation, explicitly comparing the result to a classical probability sum to demonstrate the difference. **Dependency**: T071.
- [X] T084 [P] [Doc] [Dyson] Update `research.md` with a "Coherence Budget" calculation: Estimate the effective "decoherence factor" per transformer layer based on noise in weight updates (e.g., small magnitudes) and calculate the cumulative suppression of coherent components after N layers (e.g., a deep network). Explicitly state the resulting "Frog's View" of the approximation. **Dependency**: T071.
- [X] T085 [P] [Doc] [Von Neumann] Update `research.md` to explicitly define the inner product structure of the semantic Hilbert space and the self-adjoint operators corresponding to the "ambiguity" observable. Add a subsection "Mathematical Foundations: Inner Products and Observables". **Dependency**: T071.
- [X] T086 [P] [Doc] [Wolfram] Update `research.md` to discuss "Computational Irreducibility": Explicitly test or argue whether the interference calculation exhibits computational irreducibility (i.e., cannot be compressed into a closed-form equation) and whether simple rewriting rules could reproduce the observed ambiguity patterns. Add a subsection "Search for Simple Rules". **Dependency**: T071.
- [X] T087 [P] [Doc] [Curie] Update `research.md` to explicitly detail the "Measurement Protocol": Define the instrument (the evaluation script), the quantity measured (accuracy/F1), the control (classical baseline), and the statistical significance (p-values, confidence intervals). Add a subsection "Curie's Protocol for Verification". **Dependency**: T071.

### Implementation for Documentation & Reviewer Alignment (General)

- [X] T039 [P] [Doc] Update `research.md` to explicitly define the "measurement" operation (token selection) and "observable" (ambiguity resolution) addressing Einstein/Von Neumann concerns. Add Section 4.1 "Measurement Protocol". Depends on Phase 6 completion.
- [X] T040 [P] [Doc] Update `research.md` to clarify the distinction between epistemic uncertainty and ontological superposition, framing results as associational (FR-006). Add Section 4.2 "Epistemic vs Ontological". Depends on T031b.
- [X] T041 [P] [Doc] Update `research.md` with a "Back-of-the-Envelope" section addressing Dyson's decoherence/coherence time concerns (classical approximation vs. physical claim). Add Section 5.1 "Decoherence Budget".
- [X] T042 [P] [Doc] Update `research.md` with a worked example of interference (Feynman's "arrows") showing a concrete case where Quantum $\neq$ Classical probability. Add Section 5.2 "Worked Example".
- [X] T043 [P] [Doc] Update `research.md` to explicitly define the inner product and basis vectors for the semantic space (Von Neumann's Hilbert space requirement). Add Section 5.3 "Hilbert Space Definition".
- [X] T044 [P] [Doc] Update `research.md` to include the measurement protocol (Curie's requirements: observable, control, statistical significance). Add Section 5.4 "Curie Protocol".
- [X] T045 [P] [Doc] Update `research.md` to address Krakauer's request for a specific ambiguity test case (e.g., pronoun resolution) where superposition diverges from attention. Add Section 5.5 "Pronoun Resolution Test Case".
- [X] T046 [P] [Doc] Update `research.md` to address Wolfram's computational irreducibility question (simple rules vs. complex formalism). Add Section 5.6 "Computational Irreducibility".
- [X] T047 [P] [Doc] Update `research.md` to address Lovelace's concern on "operations vs. origin" by explicitly detailing the instruction patterns that generate superposition states without the machine "originating" them. Add Section 5.7 "Instruction Patterns".
- [X] T048 [P] [Doc] Update `quickstart.md` with instructions to reproduce the -seed experiment and statistical analysis
- [X] T049 [P] [Doc] Run `quickstart.md` validation to ensure all scripts execute successfully on CPU-only CI
- [X] T073 [P] [Doc] [FR-006] Create `code/utils/framing_utils.py` with function `format_associational_statement(text)`. **Logic**: Ensure all output strings explicitly use "associational" or "correlational" language and avoid "causal" or "deterministic" claims. **Usage**: All tasks generating text output (T024d, T031b, T039-T088) MUST call this utility.

**Checkpoint**: All documentation and reviewer alignment tasks are complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T050 [P] [Doc] Draft `docs/paper/manuscript.md` (Introduction, Methods, Results, Discussion) using `data/results/` artifacts.
- [X] T051 [P] [Code] Refactor `code/models/bert_adapter.py` and `code/utils/complex_ops.py` to remove duplication and improve type hinting.
- [X] T052 [P] [Perf] Optimize batch size in `config.yaml` to ensure memory usage < 7GB under load; verify with `runtime_monitor`.
- [X] T053 [P] [Test] Add unit tests for edge cases (NaN, Inf, [UNK]) in `tests/unit/test_edge_cases.py`.
- [X] T054 [P] [Sec] Security hardening: Pin all dependencies in `requirements.txt` and verify no CVEs via `pip-audit`.
- [X] T055 [P] [Val] Run final validation suite: `pytest --cov`, `flake8`, `black --check`.
- [X] T072 [P] [SC-004] Implement `code/experiments/run_full_experiment.py` (Full Run Wrapper). **Logic**: Orchestrate the full -seed loop (Baseline + Quantum + Ablation + Stats). **Mandatory**: Wrap the entire execution in `runtime_monitor` (T009d) to enforce the 6h/7GB constraint on the *total* run time. Output a final `runtime_report.json`.
- [X] T089 [P] [Doc] Reconcile run-book vs implementation for `code/experiments/run_ablation.py`: the quickstart run-book invokes this script but it does not exist. **Action**: Update `quickstart.md` to invoke `code/experiments/run_quantum.py` OR create `code/experiments/run_ablation.py`. **Verification**: Verify the command in `quickstart.md` executes successfully.

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
- [X] T072 [P] [SC-004] Implement `code/experiments/run_full_experiment.py` (Full Run Wrapper) to enforce SC-004 on the total 5-seed run.
- [X] T073 [P] [FR-006] Create `code/utils/framing_utils.py` to ensure consistent "associational" framing across all outputs.
- [X] T071 [P] [Doc] Create initial `research.md` skeleton to enable Phase 7B tasks.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T089 [P] [Doc] Reconcile run-book vs implementation for `code/experiments/run_ablation.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/experiments/run_ablation.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.