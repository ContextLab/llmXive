# Tasks: llmXive follow-up: extending "ResearchStudio-Idea"

**Input**: Design documents from `/specs/001-llmxive-extension/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-1011-llmxive-follow-up-extending-researchstud/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw`, `data/processed`, `data/results`) and checksum manifest logic
- [ ] T005 [P] Implement seed pinning utility (`code/utils/config.py`) for numpy, torch, and python
- [ ] T006 [P] Setup state management utility (`code/utils/update_state.py`) for artifact versioning (Constitution Principle V)
- [ ] T007 Create base data models (Abstract, PatternCard, Proposal, Rating) in `code/models/`
- [ ] T008 [P] Setup error handling infrastructure that fails loudly on data fetch errors.
- [ ] T008a [P] Implement model-fallback logic in `code/utils/config.py` to switch from `all-MiniLM-L6-v2` to `all-mpnet-base-v2` (or similar smaller model) if memory constraints are hit, with explicit logging of the switch.
- [ ] T008b [P] Implement logging infrastructure for T008a to record model switches and memory fallback events.
- [ ] T009 Setup environment configuration for API keys and runner constraints

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Corpus Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest and prepare abstracts from ML and non-ML domains (Public Health, Climate Adaptation) to establish the baseline dataset.

**Independent Test**: The system can be tested by verifying that the dataset directory contains a representative set of processed JSON files with valid metadata fields and that the data fits within the available RAM constraint.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/01_data_acquisition.py` to download ML and non-ML abstracts from verified URLs. **Specifics**: Use arXiv API with `cat:cs.LG` and `cat:q-bio.QM` for ML, and specific DOI lists or UCI dataset IDs for *Nature Climate Change* and *Health Affairs* to fetch a balanced set of 'accepted' and 'rejected' abstracts. Ensure query parameters explicitly filter for acceptance status where available.
- [ ] T012 [US1] Implement strict validation in T011: Fail loudly if URLs are unreachable or paywalled; do NOT generate synthetic data.
- [ ] T013 [US1] Implement preprocessing pipeline in `code/01_data_acquisition.py` to normalize text and filter malformed entries.
- [ ] T014 [US1] Implement streaming/chunking logic to ensure dataset fits in available RAM during processing.
- [ ] T015 [US1] Add logging for data acquisition failures and preprocessing rejections.
- [ ] T016 [US1] Generate `data/processed/corpus.jsonl` with metadata (title, abstract, venue, acceptance_status, domain).

### Tests for User Story 1

- [ ] T017 [P] [US1] Contract test for data download validation in `tests/unit/test_data_parsing.py`
- [ ] T018 [P] [US1] Test memory usage constraint with full dataset load in `tests/unit/test_memory_usage_constraint.py`
- [ ] T019 [P] [US1] Test preprocessing validation (non-empty abstracts) in `tests/unit/test_preprocessing_validation.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pattern Mapping and Proposal Generation (Priority: P2)

**Goal**: Map non-ML problem statements to ML-derived ideation patterns and generate paired research proposals (pattern-guided vs. random-pattern vs. baseline).

**Independent Test**: The system can be tested by running the generation pipeline on a small subset to verify logic, then scaling to 50 pairs within 4 hours on the CPU runner.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/02_pattern_mapping.py` using `sentence-transformers` (`all-MiniLM-L6-v2` quantized) for CPU-tractable embeddings. **Logic**: Implement top-3 pattern retrieval with cosine similarity threshold ≥ 0.6.
- [ ] T021 [US2] Implement `code/03_proposal_generation.py` to generate pattern-guided proposals using injected pattern cards.
- [ ] T022 [US2] Implement `code/03_proposal_generation.py` to generate baseline proposals using generic prompts.
- [ ] T023 [US2] Implement `code/03_proposal_generation.py` to generate 'random-pattern' proposals (randomly selected pattern cards) to satisfy the three-arm design (Pattern vs. Random vs. Baseline) as per Plan Summary, noting Spec FR-003's two-group constraint is overridden by Plan scope.
- [ ] T024 [US2] Ensure strict pairing: For each of a set of unique non-ML problems, generate exactly one pattern-guided, one random-pattern, and one baseline proposal.
- [ ] T025 [US2] Implement batch processing in T021/T022/T023 to stay within 7 GB RAM limits and complete within 4 hours.
- [ ] T026 [US2] Save generated proposals to `data/results/generated_proposals.jsonl` with generation metadata (stripped for evaluation).

### Tests for User Story 2

- [ ] T027 [P] [US2] Test validity correlation: Verify retrieval thresholds (from T020) correlate with downstream expert 'contextual alignment' scores (SC-004).
- [ ] T028 [P] [US2] Test pattern mapping validation (hold-out logic) in `tests/unit/test_pattern_mapping_validation.py`
- [ ] T029 [P] [US2] Test proposal generation logic (pairing and control) in `tests/unit/test_proposal_generation_logic.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Expert Evaluation and Statistical Analysis (Priority: P3)

**Goal**: Aggregate expert ratings and perform statistical tests to determine if pattern-guided proposals differ significantly from baseline.

**Independent Test**: The system can be tested by feeding pre-defined dummy ratings to verify statistical logic and by verifying the recruitment pipeline ingests real expert ratings.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/04_evaluation_loader.py` to load expert ratings (blinded, ORCID verified) from CSV generated by T031.
- [ ] T031 [US3] Implement the 'blind evaluation' recruitment pipeline in `code/04_evaluation_recruitment.py`: 
    - Verify expert ORCID and ≥5 years experience.
    - Implement blinding mechanism: strip all generation metadata (pattern type, model) from proposals before presentation.
    - Create data collection interface (CSV export) for blinded ratings.
    - Ensure minimum of 3 independent experts per proposal.
- [ ] T032 [US3] Implement IRR gate in T031/030: Calculate Krippendorff's alpha on collected ratings; fail if < 0.6.
- [ ] T033 [P] [US3] Implement `code/05_statistical_analysis.py` to perform normality check on mean scores.
- [ ] T034 [US3] Implement dynamic test selection in T033: Paired t-test (normal) or Wilcoxon signed-rank (non-normal).
- [ ] T035 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for the three metrics (feasibility, bottleneck, alignment).
- [ ] T036 [US3] Implement sensitivity analysis in T033: Re-run tests with outliers removed using IQR method (Q1 - 1.5*IQR, Q3 + 1.5*IQR), explicitly filtering out rows where value < lower_bound OR value > upper_bound.
- [ ] T037 [US3] Correlate retrieval thresholds (from T020) with downstream expert 'contextual alignment' scores to verify the predictive power of the threshold (SC-004).
- [ ] T038 [US3] Generate final report in `data/results/analysis_report.md` including p-values, effect sizes, and the phrase "associational, not causal".
- [ ] T039 [US3] Verify report generation against `data/results/generated_proposals.jsonl` and `data/results/ratings.csv`.

### Tests for User Story 3

- [ ] T040 [P] [US3] Test statistical normality check logic in `tests/unit/test_statistical_normality_check.py`
- [ ] T041 [P] [US3] Test multiple comparison correction (Bonferroni/BH) in `tests/unit/test_multiple_comparison_correction.py`
- [ ] T042 [P] [US3] Test Inter-Rater Reliability (IRR) gate (Krippendorff's alpha ≥ 0.6) in `tests/unit/test_inter_rater_reliability_gate.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `docs/` and `README.md`
- [ ] T044 Code cleanup and refactoring for memory efficiency
- [ ] T045 Performance optimization: Ensure total pipeline runtime ≤ 6 hours on GitHub Actions runner
- [ ] T046 [P] Run `quickstart.md` validation and integration test suite
- [ ] T047 Security hardening: Ensure no PII in logs or output files
- [ ] T048 Update `state/manifest.yaml` with final artifact checksums

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 proposal output

### Within Each User Story

- **Development Methodology**: Tests MUST be written and FAIL before implementation (TDD workflow).
- **Execution Order**: Implementation tasks MUST be listed BEFORE Test tasks in the task list to ensure code exists for the tests to run against.
- Data download (T011) before preprocessing (T013)
- Pattern mapping (T020) before proposal generation (T021)
- Evaluation loading (T030) and recruitment (T031) before statistical analysis (T033)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (after implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after implementation is complete):
Task: "Contract test for data download validation in tests/unit/test_data_parsing.py"
Task: "Test memory usage constraint with full dataset load in tests/unit/test_memory_usage_constraint.py"
Task: "Test preprocessing validation (non-empty abstracts) in tests/unit/test_preprocessing_validation.py"

# Launch implementation tasks:
Task: "Implement code/01_data_acquisition.py to download ML and non-ML abstracts"
Task: "Implement preprocessing pipeline in code/01_data_acquisition.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Acquisition)
4. **STOP and VALIDATE**: Test User Story 1 independently with real data
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
   - Developer A: User Story 1 (Data)
   - Developer B: User Story 2 (Generation)
   - Developer C: User Story 3 (Analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD workflow)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Do NOT use synthetic data if real data fetch fails. The system must fail loudly.
- **Critical**: Ensure `all-MiniLM-L6-v2` is quantized to run within 7 GB RAM on CPU.
- **Critical**: The recruitment pipeline (T031) MUST implement ORCID verification, blinding, and data collection, not just loading existing data.
- **Critical**: The three-arm design (Pattern vs. Random vs. Baseline) is implemented per Plan Summary, overriding Spec FR-003's two-group constraint.