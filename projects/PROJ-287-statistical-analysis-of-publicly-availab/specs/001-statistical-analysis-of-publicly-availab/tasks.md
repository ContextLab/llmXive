# Tasks: Statistical Analysis of Topic Drift in Academic Abstracts

**Input**: Design documents from `/specs/001-topic-drift-analysis/`
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

- [X] T001 Create project structure per implementation plan: Create directories `src/`, `tests/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/stats/`, `docs/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, scipy, nltk, spacy, pandas, matplotlib, requests, pyyaml)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/utils/logging.py` for standardized logging and error handling
- [X] T005 [P] Implement `src/utils/manifest.py` for reproducibility manifest generation (JSON)
- [X] T006 [P] Create `src/utils/config.py` to load environment variables and random seeds
- [X] T007 [P] Setup `tests/unit/test_utils.py` for logging and manifest validation
- [ ] T008 [P] Create base data structures: `AbstractRecord`, `TopicVector`, `DivergenceMeasurement` in `src/models/entities.py` (Downstream tasks depend on these class definitions)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download abstracts from arXiv/PubMed, filter by year/field, and preprocess with window-specific stoplists.

**Independent Test**: Can be fully tested by downloading a sample of abstracts from each source, preprocessing them with window-specific stopword lists, and verifying that the output CSV contains ≥95% of total fetched records with ≥20 tokens after preprocessing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Unit test for API rate-limit backoff logic in `tests/unit/test_fetch.py`
- [X] T010 [P] [US1] Unit test for token count filtering (min 20 tokens) in `tests/unit/test_preprocess.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `src/data/fetch/arxiv_fetcher.py` with exponential backoff and **at most 3 retry attempts** per endpoint, filtering by publication year from the early 21st century to 2024
- [ ] T012 [P] [US1] Implement `src/data/fetch/pubmed_fetcher.py` with exponential backoff and **at most 3 retry attempts** per endpoint, filtering by publication year 2000–2024
- [X] T013 [US1] Implement `src/data/fetch/orchestrator.py` to coordinate both fetchers and save raw JSONL to `data/raw/` with SHA256 checksums
- [ ] T014 [P] [US1] Implement `src/data/preprocess/tokenizer.py` using NLTK/spaCy with window-specific stopword loading
- [ ] T015 [US1] Implement `src/data/preprocess/filter.py` to exclude records <20 tokens and log exclusion counts
- [ ] T016 [US1] Implement `src/data/storage/saver.py` to save processed CSVs to `data/processed/` partitioned by the **specific 5-year windows**
- [~] T017 [US1] Update `results/manifest.json` with `arxiv_fetch_status`, `pubmed_fetch_status`, and data checksums

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topic Modeling & Temporal Analysis (Priority: P2)

**Goal**: Fit LDA models per window, validate k=10, align topics, and compute proportions.

**Independent Test**: Can be fully tested by fitting an LDA model on a sampled subset, validating k=10 via the elbow method, extracting topic proportions, and verifying that all topics have non-zero probability mass and coherence score ≥0.4.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for k-selection logic (elbow method within 10% tolerance) in `tests/unit/test_lda.py`
- [~] T019 [P] [US2] Unit test for topic alignment (cosine similarity) in `tests/unit/test_align.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `src/models/lda/fitter.py` to fit LDA (k=10, max_iter=20) **iteratively for each of the five defined windows (2000–2004, 2005–2009, 2010–2014, 2015–2019, 2020–2024)** using `scikit-learn`
- [ ] T021 [US2] Implement `src/models/lda/validator.py` to compute c_v coherence; flag runs <0.4 and prevent downstream processing for that window
- [ ] T022 [P] [US2] Implement `src/models/lda/k_selector.py` to validate k=10 using elbow method/held-out likelihood; select optimal k if needed
- [ ] T023 [US2] Implement `src/models/lda/aligner.py` to align topic indices across windows via cosine similarity of topic-word distributions (**Depends on completion of T020 across all 5 windows**; resolves label switching critical for valid divergence)
- [ ] T024 [US2] Implement `src/models/metrics/proportions.py` to compute topic proportion vectors (sum=1.0, no NaN) for each window
- [ ] T025 [US2] Save topic vectors to `results/stats/topic_vectors.json` and update manifest with `k_topics`, `coherence_threshold`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Testing & Visualization (Priority: P3)

**Goal**: Compute JS divergence, run permutation tests, apply MaxT correction, and generate plots.

**Independent Test**: Can be fully tested by running a permutation test (shuffling abstracts, n=1000) on a small dataset and verifying that p-values are computed, confidence intervals have width ≤0.2, and PNG figures are saved.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for JS divergence calculation (base=2) in `tests/unit/test_metrics.py`
- [X] T027 [P] [US3] Unit test for MaxT correction logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `src/models/metrics/divergence.py` using `scipy.spatial.distance.jensenshannon` (base=2)
- [ ] T029 [US3] Implement `src/models/metrics/permutation.py` to perform n=1000 permutations on a **stratified sample of min(2000, available) abstracts/window** with LDA refit (**Depends on raw processed data from T016, refit logic from T020, and alignment logic from T023**; generates null distribution via refit)
- [X] T030 [US3] Implement `src/models/metrics/ci.py` to compute bootstrapped 95% confidence intervals (width ≤0.2)
- [ ] T031 [US3] Implement `src/models/metrics/correction.py` to apply **MaxT procedure for FWER control** across window pairs (per plan.md justification for dependent windows, overriding generic BH mention in spec)
- [ ] T034 [US3] Implement sensitivity analysis in `src/models/metrics/sensitivity.py` sweeping coherence thresholds across a range of values and reporting inconsistency rates (**Depends on completion of T020 and T021**; must run before manifest finalization)
- [ ] T033 [US3] Implement `src/main.py` to orchestrate the full pipeline (Fetch → Preprocess → LDA → Align → Divergence → Test → Sensitivity → Viz)
- [ ] T035 [US3] Finalize `results/manifest.json` with all required parameters (random seeds, k, iterations, checksums, etc.) including sensitivity results
- [ ] T036 [US3] Save final statistics to `results/stats/divergence_results.json` and figures to `results/figures/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` and `quickstart.md` including fallback procedure for arXiv failure
- [ ] T038 Code cleanup and refactoring for CPU efficiency (**Refactor src/models/lda/fitter.py loops** and add **timing logs to src/main.py** for each window to ensure total runtime <6h on 2 cores)
- [ ] T039 [P] Run integration tests on a sample dataset to verify full pipeline flow
- [ ] T040 [P] Validate reproducibility manifest completeness (SC-005)

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 topic vectors

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
Task: "Unit test for API rate-limit backoff logic in tests/unit/test_fetch.py"
Task: "Unit test for token count filtering (min 20 tokens) in tests/unit/test_preprocess.py"

# Launch fetchers in parallel:
Task: "Implement src/data/fetch/arxiv_fetcher.py"
Task: "Implement src/data/fetch/pubmed_fetcher.py"
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data fetching MUST use real API endpoints (arXiv/PubMed) or verified datasets. No synthetic data.
- **CRITICAL**: All analysis MUST run on CPU-only infrastructure (no CUDA/GPU dependencies).
- **CRITICAL**: Permutation tests MUST use stratified sampling (min(2000, available)) to meet runtime constraints.
- **CRITICAL**: Sensitivity analysis MUST sweep thresholds across a range of values and report inconsistency rates.
- **CRITICAL**: MaxT correction is used for FWER control on dependent windows (per plan.md justification).
- **CRITICAL**: Topic alignment is required to resolve label switching before divergence calculation.