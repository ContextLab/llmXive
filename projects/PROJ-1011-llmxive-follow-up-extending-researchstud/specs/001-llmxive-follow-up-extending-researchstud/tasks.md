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

- [X] T001a Create project directory structure per plan.md (`projects/PROJ-1011-llmxive-follow-up-extending-researchstud/`, `code/`, `data/`, `tests/`, `state/`)
- [X] T001b Initialize Python 3.11 project with pinned dependencies (`requirements.txt`) and `pyproject.toml`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure (`data/raw`, `data/processed`, `data/results`) and checksum manifest logic
- [X] T005 [P] Implement seed pinning utility (`code/utils/config.py`) for numpy, torch, and python
- [X] T006 [P] Setup state management utility (`code/utils/update_state.py`) for artifact versioning (Constitution Principle V)
- [X] T007 Create base data models (Abstract, PatternCard, Proposal, Rating) in `code/models/`
- [X] T008 [P] Setup error handling infrastructure that fails loudly on data fetch errors.
- [X] T008a [P] Implement model-fallback logic in `code/utils/config.py` to switch from `all-MiniLM-L6-v2` to a configurable `FALLBACK_EMBEDDING_MODEL` (defined in config) if memory constraints are hit, with explicit logging of the switch. **Constraint**: Do not hardcode a specific model name in the task description; rely on the config variable.
- [X] T008b [P] Implement logging infrastructure for T008a to record model switches and memory fallback events.
- [X] T009 [P] Create `data-sources.yaml` configuration file containing exact API endpoints, DOI lists, and fetch parameters for ML (arXiv) and non-ML (Nature Climate Change, Health Affairs) domains.
- [X] T009a [P] Implement validation logic for `data-sources.yaml` to ensure required fields are present and URLs are valid formats.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Corpus Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest and prepare abstracts from ML and non-ML domains (Public Health, Climate Adaptation) to establish the baseline dataset.

**Independent Test**: The system can be tested by verifying that the dataset directory contains a representative set of processed JSON files with valid metadata fields and that the data fits within the available RAM constraint.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_data_acquisition.py` to download ML and non-ML abstracts using endpoints defined in `data-sources.yaml`. **Specifics**: Use arXiv API with `cat:cs.LG` and `cat:q-bio.QM` for ML, and specific DOI lists/API endpoints from `data-sources.yaml` for *Nature Climate Change* and *Health Affairs* to fetch a balanced set of 'accepted' and 'rejected' abstracts. **Output**: Write raw data to `data/raw/corpus_raw.jsonl`. Ensure query parameters explicitly filter for acceptance status where available.
- [X] T012 [US1] Implement strict validation function `validate_fetch_status()` in `code/01_data_acquisition.py` that raises `DataFetchError` on 403/404 or paywall detection. **Verification**: Unit test `test_fetch_fail_loudly` asserts exception raised. Do NOT generate synthetic data.
- [X] T013 [US1] Implement preprocessing pipeline in `code/01_data_acquisition.py` to normalize text and filter malformed entries.
- [X] T014 [US1] Implement streaming/chunking logic in `code/01_data_acquisition.py` via `stream_and_sample(n=500, seed=42)` to limit processing to a manageable subset of rows if full load exceeds 6GB RAM, logging the truncation event. **Critical Rule**: Use `datasets.load_dataset(..., streaming=True)` or `islice` with explicit chunk accumulation.
- [X] T015 [US1] Configure `logging` in `code/01_data_acquisition.py` to write `ERROR` level events to `logs/data_acquisition.log` with timestamp and URL context.
- [X] T016 [US1] Generate `data/processed/corpus.jsonl` with metadata (title, abstract, venue, acceptance_status, domain).

### Tests for User Story 1

- [X] T017 [P] [US1] Contract test for data download validation in `tests/unit/test_data_parsing.py`
- [ ] T018 [P] [US1] Test memory usage constraint with full dataset load in `tests/unit/test_memory_usage_constraint.py`
- [ ] T019 [P] [US1] Test preprocessing validation (non-empty abstracts) in `tests/unit/test_preprocessing_validation.py`
- [X] T018a [P] [US1] Test `data-sources.yaml` validation and usage in `code/01_data_acquisition.py` in `tests/unit/test_data_sources_config.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pattern Mapping and Proposal Generation (Priority: P2)

**Goal**: Map non-ML problem statements to ML-derived ideation patterns and generate paired research proposals (pattern-guided vs. baseline).

**Independent Test**: The system can be tested by running the generation pipeline on a small subset to verify logic, then scaling to 50 pairs within 4 hours on the CPU runner.

### Implementation for User Story 2

- [X] T020 [US2] Implement `retrieve_top_k_patterns()` in `code/02_pattern_mapping.py` using `sentence-transformers` (`all-MiniLM-L6-v2` quantized) for CPU-tractable embeddings. **Logic**: Return a list of 3 pattern IDs with cosine similarity ≥ 0.6. **Dependency**: Must complete before T021/T022.
- [X] T021 [US2] Implement `code/03_proposal_generation.py` to generate pattern-guided proposals using injected pattern cards. **Constraint**: Generate exactly one proposal per problem statement. **Note**: Strictly adhere to the two-group design (pattern-guided vs baseline) as per FR-003; ignore any 'random-pattern' references in the plan summary.
- [X] T022 [US2] Implement `code/03_proposal_generation.py` to generate baseline proposals using generic prompts. **Constraint**: Generate exactly one proposal per problem statement. **Note**: Strictly adhere to the two-group design (pattern-guided vs baseline) as per FR-003; ignore any 'random-pattern' references in the plan summary.
- [X] T023 [US2] Implement `code/02_pattern_validation.py` to enforce the two-group design constraint: verify that the generation pipeline only produces 'pattern-guided' and 'baseline' groups and explicitly rejects any 'random-pattern' logic if present in the code or config.
- [ ] T024 [US2] Ensure strict two-group pairing: For each of a set of unique non-ML problems, generate exactly one pattern-guided and one baseline proposal. **Output**: Save to `data/results/generated_proposals.jsonl` with metadata stripped for evaluation. **Note**: This task validates the output of T021/T022 against the two-group constraint.
- [ ] T025 [US2] Implement batch processing in T021/T022 to stay within 7 GB RAM limits and complete within 4 hours.
- [ ] T026 [US2] Save generated proposals to `data/results/generated_proposals.jsonl` with generation metadata (stripped for evaluation).

### Tests for User Story 2

- [X] T028 [P] [US2] Test pattern mapping validation (hold-out logic) in `tests/unit/test_pattern_mapping_validation.py`
- [ ] T029 [P] [US2] Test proposal generation logic (strict two-group pairing) in `tests/unit/test_proposal_generation_logic.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Expert Evaluation and Statistical Analysis (Priority: P3)

**Goal**: Aggregate expert ratings and perform statistical tests to determine if pattern-guided proposals differ significantly from baseline.

**Independent Test**: The system can be tested by feeding pre-defined dummy ratings to verify statistical logic and by verifying the loader script successfully ingests pre-collected expert ratings with blinded metadata.

### Implementation for User Story 3

- [ ] T030a [US3] Implement `code/04_evaluation_recruitment.py` to generate blinded CSV template `data/results/ratings_template.csv` with columns (proposal_id, metric, score) and a script to strip metadata from `data/results/generated_proposals.jsonl`.
- [X] T030b [US3] Implement `code/04_evaluation_recruitment.py` to perform validation on expert inputs: consume a pre-verified `expert_roster.csv` (containing ORCID, verified status, and years of experience) and validate that every rating in the input file corresponds to an ORCID in the roster with `verified=true` and `years_experience >= 5`. **Constraint**: Do not rely solely on regex; must cross-reference the verified roster.
- [ ] T030c [US3] Implement `code/04_evaluation_recruitment.py` to ingest the manually filled `data/results/ratings_filled.csv` (user fills template and saves as this file) only after T030b validation passes.
- [ ] T030 [US3] Implement `code/04_evaluation_loader.py` to load expert ratings from `data/results/ratings_filled.csv` (blinded, ORCID verified).
- [ ] T032 [US3] Implement IRR gate in `code/05_statistical_analysis.py`: Calculate Krippendorff's alpha on collected ratings; **FAIL** pipeline if alpha < 0.6.
- [ ] T033 [P] [US3] Implement `code/05_statistical_analysis.py` to perform normality check on mean scores.
- [ ] T034 [US3] Implement dynamic test selection in T033: Paired t-test (normal) or Wilcoxon signed-rank (non-normal).
- [ ] T035a [US3] Implement sensitivity analysis: Identify outliers using the IQR method with standard interquartile range multipliers (Q1 - k*IQR, Q3 + k*IQR). If one member of a pair is an outlier, remove the ENTIRE pair. **Critical Step**: Re-run the statistical test (T033/T034) on the cleaned dataset. **Output**: Generate `data/results/sensitivity_analysis_report.md` containing pre/post p-values and effect sizes to verify robustness.
- [ ] T035b [US3] Implement power check in T035a: If pair removal reduces n below a threshold deemed insufficient for statistical power, flag the result as 'underpowered' and log the warning; do not proceed to final conclusion without this flag.
- [ ] T035 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for the three metrics (feasibility, bottleneck, alignment). **Condition**: Apply correction to the final results from T035a ONLY if T035b does not flag the result as 'underpowered'.
- [ ] T036 [US3] Implement `calculate_validity_improvement()` in `code/05_statistical_analysis.py` that computes the mean difference in 'contextual alignment' scores between groups and writes the result (p-value, effect size) to `data/results/validity_metrics.json`.
- [ ] T037 [US3] Generate final report in `data/results/analysis_report.md` including p-values, effect sizes, and the phrase "associational, not causal".
- [ ] T037a [US3] Verify report generation: Implement an assertion or parser check in `code/05_statistical_analysis.py` or a separate script to confirm the phrase "associational, not causal" is present in `data/results/analysis_report.md`. **Fail** if missing.
- [ ] T038 [US3] Verify report generation against `data/results/generated_proposals.jsonl` and `data/results/ratings.csv`.

### Tests for User Story 3

- [ ] T039 [P] [US3] Test statistical normality check logic in `tests/unit/test_statistical_normality_check.py`
- [ ] T040 [P] [US3] Test multiple comparison correction (Bonferroni/BH) in `tests/unit/test_multiple_comparison_correction.py`
- [ ] T041 [P] [US3] Test Inter-Rater Reliability (IRR) gate (Krippendorff's alpha ≥ 0.6) in `tests/unit/test_inter_rater_reliability_gate.py`
- [ ] T042 [P] [US3] Test sensitivity analysis paired-difference removal logic in `tests/unit/test_sensitivity_analysis.py`

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

- **Data download (T011)** before preprocessing (T013)
- **Pattern mapping (T020)** before proposal generation (T021)
- **Evaluation loading (T030)** and template generation (T030a) before statistical analysis (T033)
- **Core implementation** before integration
- **Story complete** before moving to next priority

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
Task: "Test data-sources.yaml validation in tests/unit/test_data_sources_config.py"

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
- **Critical**: The evaluation workflow (T030a/T030b) MUST generate blinded templates for manual distribution and load pre-collected ratings, not automate recruitment.
- **Critical**: The two-group design (Pattern vs. Baseline) is strictly enforced per Spec FR-003; no random-pattern arm. T023 explicitly enforces this.
- **Critical**: The data acquisition task (T011) must explicitly state the streaming/sampling rule (e.g., `streaming=True` with chunk accumulation or `islice` of N rows) to handle large datasets without memory overflow, as per the "Large real datasets" rule.
- **Critical**: The statistical analysis (T033-T035) must explicitly state the power analysis assumptions (n=50 pairs, 3 raters) and the effect size (Cohen's d of moderate magnitude) being targeted, as per the "Assumptions" section of the spec.
- **Critical**: The sensitivity analysis in T035a must preserve paired structure by removing entire pairs if one member is an outlier and re-run the test.
- **Critical**: T035b must flag the result if n drops below the power threshold, preventing T035 from proceeding if underpowered.
- **Critical**: T037a must verify the rhetorical constraint "associational, not causal" is present in the final report.
- **Critical**: T008a uses a configurable fallback model constant, not a hardcoded name.