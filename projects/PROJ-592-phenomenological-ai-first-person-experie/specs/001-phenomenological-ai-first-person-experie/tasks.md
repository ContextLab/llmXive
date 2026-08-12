# Tasks: Phenomenological AI: First-Person Experience Modeling

**Input**: Design documents from `/specs/592-phenomenological-ai-first-person-experie/`
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

- [X] T001 [P] Write `scripts/init_project.py` script to scaffold directories: `code/`, `data/raw/`, `data/processed/`, `data/qualitative/`, `tests/unit/`, `tests/integration/`, `specs/contracts/`. **Execution**: Run `python scripts/init_project.py` to verify completion.
- [ ] T002a [P] Create `.ruff.toml` with specific rules (E, F, W, I) for linting. **Execution**: Verify `ruff check .` passes with no errors.
- [ ] T002b [P] Create `pyproject.toml` with `[tool.black]` configuration for formatting. **Execution**: Verify `black --check .` passes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Implement `code/config.py` with:
 1. Seeds, paths, and model IDs (Primary: `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF` for CI; Secondary: `TheBloke/Mistral-7B-Instruct-v0.2-GGUF` for full study).
 2. **Phenomenological Marker Dictionaries**: Define concrete lists for 'sensory' (e.g., see, hear, feel, touch, taste, smell, light, sound), 'temporal' (e.g., now, then, before, after, moment, duration), and 'intentional' (e.g., think, believe, desire, intend, perceive, experience) keywords as per FR-008 and FR-009.
- [ ] T004 [P] Setup `code/utils/logging.py` for structured logging, warning capture, and retry logic (multiple attempts per sample)
- [ ] T005 [P] Implement `code/utils/io.py` for JSON/CSV schema validation and artifact archiving
- [ ] T006 [P] Create base data schemas in `specs/contracts/`: `specs/contracts/generation_output.schema.yaml`, `specs/contracts/validity_scores.schema.yaml`, `specs/contracts/qualitative_ratings.schema.yaml`
- [ ] T007 [P] Implement `code/generation/prompt_engineering.py` with the defined strategies (Direct, Hypothetical, Comparative, Role-play) and a set of base prompts loaded from `data/prompts/base_prompts.json`. **Execution**: Verify `data/prompts/base_prompts.json` exists and contains a sufficient number of prompts for the study.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Report Generation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate the corpus of phenomenological reports using CPU-tractable models and four prompting strategies.

**Independent Test**: Execute `code/generation/runner.py` and verify `data/raw/` contains ≥80 samples per strategy (totaling a substantial set of samples: 80 samples × 20 prompts × 4 strategies) with valid JSON metadata (seed, prompt, strategy) and no CUDA errors.

### Implementation for User Story 1

- [ ] T008 [P] [US1] Implement `code/generation/runner.py` using `llama-cpp-python` for `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF` (specifically `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`) on CPU-only environment (FR-002). **Constraint**: Generate ≥80 samples per prompt per strategy. **Execution**: Verify `data/raw/` contains files per strategy with ≥80 samples each.
- [ ] T009 [US1] Implement retry logic in `runner.py`: A fixed number of attempts per prompt/strategy combination, marking samples as missing after failure (FR-001). **Execution**: Simulate a failure and verify logs show retries.
- [ ] T010 [US1] Add timeout handling and sample-size logging to ensure ≥80 successful samples per condition. **Execution**: Verify logs show timeout handling and sample-size logging.
- [ ] T011 [US1] Implement `code/generation/runner_7b.py` for the second checkpoint (Mistral-7B or Llama-7B) using `llama-cpp-python` with 4-bit GGUF. **Note**: This is a PRIMARY CI task for the full study volume (≥80 samples per condition), not just local. Must verify absence of CUDA dependencies and fail gracefully if GPU detected. **Execution**: Verify script runs on CPU and generates ≥80 samples per condition.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phenomenological Metric Computation (Priority: P2)

**Goal**: Compute Internal Consistency, Semantic Stability, and Marker Presence metrics, then perform statistical analysis.

**Independent Test**: Run `code/analysis/stats.py` on a small subset of reports and verify `data/processed/validity_scores.csv` contains non-null scores for all three metrics and correct statistical test outputs.

### Implementation for User Story 2

- [ ] T013 [P] [US2] Implement `code/analysis/consistency.py`: Load NLI model `cross-encoder/nli-distilroberta-base` (CPU-safe), compute pairwise contradiction counts, handle length limits by skipping pairs with warnings (US-2 Edge Case), and **track report-level completion rates to ensure ≥95% threshold (SC-001)** is met. **Execution**: Verify completion rate is logged and error raised if <95%.
- [ ] T014 [P] [US2] Implement `code/analysis/stability.py`: Compute embeddings for repeated generations, calculate cosine similarity, and store stability scores.
- [ ] T015 [US2] Implement `code/analysis/markers.py`: Load the keyword dictionary defined in `code/config.py` (T003) to count sensory, temporal, and intentional markers (FR-008). **Dependency**: Requires T003 (Phase 2) and `specs/contracts/generation_output.schema.yaml` (schema) for input format. **Note**: Must run after T003.
- [ ] T016 [P] [US2] Implement `code/analysis/fdr_correction.py` and `code/analysis/tukey_hsd.py` for Benjamini-Hochberg FDR and Tukey HSD post-hoc tests (FR-005).
- [ ] T017 [US2] Implement `code/analysis/stats.py` to orchestrate metric aggregation. **Logic**: Run Shapiro-Wilk and Levene tests (FR-012). If assumptions (p≥0.05) hold, run ANOVA + FDR + Tukey. If violated, skip FDR/Tukey and run Kruskal-Wallis instead. **Dependency**: Requires schema contracts from Phase 2 only (not Phase 3 logic). **Execution**: Verify Kruskal-Wallis is used when Shapiro-Wilk/Levene p < 0.05. **Output**: Save results to `data/processed/stats_results.csv`.
- [ ] T018 [US2] Implement `code/analysis/sensitivity_analysis.py` to test validity score weights (FR-006) and address the sample size gap (CI vs Research) by analyzing robustness across sample subsets. **Justification**: Output a report justifying the fixed weights used in the Constitution based on sensitivity results. **Execution**: Generate sensitivity_analysis_report.csv covering a broad weight range.
- [ ] T019 [P] [US2] Implement `code/analysis/validity_justification.py` to cite phenomenology literature OR perform alternative metric sensitivity (FR-009). **Execution**: Run `scripts/validate_citations.py` against `code/analysis/validity_justification.py` to verify citations are present and valid.
- [ ] T020 [US2] Implement Cohen's κ calculation and threshold sensitivity analysis in `code/analysis/sensitivity_kappa.py`: Analyze robustness of conclusions across a range of kappa thresholds as required by FR-011. **Note**: Report the threshold as the benchmark, but do not enforce it as a hard gate in the analysis logic itself. **Execution**: Generate sensitivity_kappa_report.csv covering a range of kappa values.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Qualitative Validation & Reproducibility (Priority: P3)

**Goal**: Facilitate human evaluation, compute inter-rater reliability, and archive all artifacts.

**Independent Test**: Verify `data/qualitative/` contains anonymized rating sheets, `code/validation/human_rater.py` calculates Cohen's κ correctly, and the archive script commits all artifacts.

### Implementation for User Story 3

- [ ] T021 [P] [US3] **Create** `code/validation/rubric.md`: Author the independent validation rubric document required by FR-010, defining clear criteria for human raters separate from automated metrics. **Execution**: Verify `code/validation/rubric.md` exists and contains **5 distinct criteria**.
- [ ] T022 [US3] Implement `code/validation/human_rater.py` to load generated reports, apply independent validation rubric from `code/validation/rubric.md` (FR-010), and store ratings in `data/qualitative/ratings_raw.csv`. **Dependency**: Requires T021 to create the rubric. **Note**: Must run after T021.
- [ ] T023 [US3] Create `code/validation/stratified_sampler.py` to select a representative set of reports per condition for human rating (SC-002). **Execution**: Verify `data/qualitative/sampled_reports.csv` contains a balanced distribution of reports across conditions.
- [ ] T024 [US3] Implement `code/utils/archiver.py` to package prompts, seeds, scripts, and anonymized ratings for public reproducibility (FR-007).
- [ ] T025 [US3] Implement `code/validation/correlation_analysis.py` to compute and report the statistical correlation (Pearson/Spearman) between human coherence ratings (from T022) and automated validity scores (from T013-T015) as required by FR-010. **Execution**: Verify `data/qualitative/correlation_report.csv` contains correlation coefficients and p-values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review-Driven Enhancements (Priority: P2)

**Goal**: Address specific philosophical and methodological concerns raised by reviewers (Turing, Rockmore, etc.) regarding operational tests, stylistic distinction, and debiasing.

- [ ] T026 [P] [Enh] Implement `code/analysis/stylistic_distinction.py` to verify that generated phenomenological reports are statistically distinguishable from control technical reports (addressing concern about stylistic distinction). **Execution**: Generate `stylistic_distinction_report.csv`.
- [ ] T027 [P] [Enh] Implement `code/analysis/debiasing_protocol.py` to apply the debiasing protocol for human raters (addressing concern about rater bias). **Execution**: Verify debiasing steps are logged.
- [ ] T028 [P] [Enh] Implement `code/analysis/operational_test.py` to verify that the operational tests for coherence are robust across different model configurations (addressing concern about operational tests). **Execution**: Generate `operational_test_report.csv`.
- [ ] T029 [P] [Enh] Implement `code/analysis/internal_state_tracing.py` to provide traces of model internal states for a subset of generations (addressing concern about internal state tracing). **Execution**: Generate `internal_state_traces.json`.
- [ ] T030 [P] [Enh] Implement `code/analysis/incoherence_metric.py` to refine the incoherence metric based on reviewer feedback (addressing concern about incoherence metrics). **Execution**: Generate `incoherence_metric_report.csv`.

**Checkpoint**: Review concerns addressed

---

## Phase 7: Integration & Orchestration (Priority: P3)

**Purpose**: Orchestration and final validation

- [ ] T031 [P] Implement `code/main.py` to orchestrate the full pipeline: Generation → Metrics → Stats (enables US1+US2 integration testing). **Dependency**: Requires completion of Phase 3 (Generation) and Phase 4 (Analysis) logic. **Note**: Must run after Phase 3 and 4 logic is complete. **Execution**: Run `python code/main.py --mode full` and verify pipeline completion.
- [ ] T032 [P] Add CLI usage examples and environment setup instructions to `quickstart.md`. **Examples**: Append 3 code blocks to `quickstart.md`:. `python main.py --mode generation`, 2. `python main.py --mode analysis`, 3. `python main.py --mode validate`. **Execution**: Verify `quickstart.md` contains all three examples.
- [ ] T033 [P] Add schema descriptions and data flow diagrams to `data-model.md`
- [ ] T034 [P] Refactor `code/analysis/stats.py` to add type hints and remove duplicate imports. **Execution**: Run `ruff check code/analysis/stats.py`.
- [ ] T035 [P] Refactor `code/utils/logging.py` to standardize log levels and output formats. **Execution**: Verify all logs follow standard format.
- [ ] T036 [P] Run `quickstart.md` validation to ensure full pipeline execution ≤6 hours on free-tier. **Execution**: Verify pipeline completes in <6 hours on free-tier runner.
- [ ] T037 [P] Generate `quickstart.md` with complete setup and execution instructions (FR-007). **Content**: Include requirements.txt, model download steps, and execution commands. **Execution**: Verify `quickstart.md` exists and is complete.
- [ ] T038 [P] Generate `data-model.md` with schema descriptions and data flow diagrams (FR-007). **Execution**: Verify `data-model.md` exists and is complete.
- [ ] T039 [P] Update `paper/` draft with results from Phase 6 enhancements. **Dependency**: Requires completion of Phase 6 (T026-T030). **Execution**: Verify paper draft includes new sections.
- [ ] T040 [P] Finalize `README.md` with links to all artifacts and instructions for local 7B model execution. **Execution**: Verify README is complete.
- [ ] T041 [P] Update `CONTRIBUTING.md` with guidelines for adding new prompting strategies or metrics. **Execution**: Verify CONTRIBUTING.md is complete.
- [ ] T042 [P] Run final security scan on all scripts and dependencies. **Execution**: Verify no vulnerabilities found.
- [ ] T043 [P] Archive all final artifacts to `data/final_archive/`. **Execution**: Verify archive integrity.
- [ ] T044 [P] Generate final `research_review.md` document summarizing all findings. **Execution**: Verify review document is complete.
- [ ] T045 [P] Submit project for final advancement evaluation. **Execution**: Verify submission is successful.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review-Driven Enhancements (Phase 6)**: Depends on US1 and US2 logic to be functional.
- **Integration & Orchestration (Phase 7)**: Depends on US1, US2, US3 logic AND Phase 6 enhancements to be in place.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (schema only for parallel dev)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 metrics
- **Review-Driven Enhancements (Phase 6)**: Depends on US1 and US2 logic to be functional.
- **Integration & Orchestration (Phase 7)**: Depends on US1, US2, US3 logic AND Phase 6 enhancements to be in place.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Review-Driven Enhancements (Phase 6) can be implemented in parallel once US1 and US2 are functional.
- Integration & Orchestration (Phase 7) tasks can be implemented in parallel once the base analysis pipeline (US2) and review enhancements (Phase 6) are functional.

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
5. Add Review-Driven Enhancements (Phase 6) → Address specific philosophical concerns
6. Add Integration & Orchestration (Phase 7) → Address specific philosophical concerns
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Generation)
 - Developer B: User Story 2 (Analysis)
 - Developer C: User Story 3 (Validation)
 - Developer D: Review-Driven Enhancements (Phase 6)
 - Developer E: Integration & Orchestration (Phase 7)
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
- **CPU Constraint**: All tasks must be executable on a minimal CPU configuration. No CUDA, no 8-bit/4-bit quantization requiring GPU drivers. Use `llama-cpp-python` with GGUF for TinyLlama.
- **Model Constraint**: TinyLlama-1.1B and Mistral-7B (quantized) are the required models for the primary CI pipeline.
- **Review Integration**: Tasks in Phase 6 and Phase 7 specifically address the philosophical and methodological concerns raised by Alan Turing, Dan Rockmore, David Krakauer, Daniel Kahneman, and Freeman Dyson regarding operational tests, internal state tracing, stylistic distinction, incoherence metrics, and debiasing protocols.