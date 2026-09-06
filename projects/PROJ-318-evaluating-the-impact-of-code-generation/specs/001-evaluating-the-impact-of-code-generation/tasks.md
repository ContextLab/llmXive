# Tasks: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-code-generation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `code/utils/`, `data/`, `tests/` at repository root
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

- [ ] T001a [P] Create project structure: **Create a script `scripts/setup.sh`** that runs `mkdir -p code code/utils data/raw/repos data/processed tests/unit tests/integration state logs` and outputs the list of created directories to `logs/setup.log`. **Verification**: Run `bash scripts/setup.sh` and verify `logs/setup.log` exists and contains the directory paths. **Wait for T002 completion** (for requirements) or run first if no dependencies.
- [ ] T001b [P] Create `.gitkeep` files: **Run `bash scripts/setup.sh` (from T001a) and then verify that `.gitkeep` exists in every directory listed in `logs/setup.log` using `for dir in $(cat logs/setup.log); do test -f "$dir/.gitkeep" || touch "$dir/.gitkeep"; done`**. **Verification**: Run the command and ensure no errors are thrown and all directories have `.gitkeep`. **Wait for T001a completion**.

- [X] T002 [P] Initialize Python + project with `requirements.txt` dependencies (`transformers==4.35.0`, `torch==2.1.0`, `bitsandbytes==0.41.0`, `sentence-transformers==2.2.2`, `docstring_parser==0.16`, `scipy==1.11.0`, `requests==2.31.0`, `pyyaml==6.0.1`, `pytest==7.4.0`) **with strict 4-bit quantization fallback logic: if 4-bit fails, the script MUST attempt 8-bit, then full precision, and ONLY abort if all quantization schemes fail to prevent OOM crashes, ensuring deterministic generation per Constitution Principle VII. MUST also explicitly pin random seeds in `code/config.py` (numpy, random, torch, transformers) and verify via a dummy run that outputs are identical on repeated runs.**
- [X] T003 [P] Create `.flake8` (max-line-length=88) and `pyproject.toml` (black settings) configuration files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading utilities and model loaders.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 [S] **Create/freeze `data/raw/repo_list.json`**: **Implement `code/utils/repo_fetcher.py` to fetch a representative set of top-ranked Python repositories on the PyPI leaderboard via the PyPI JSON API. Sort them deterministically by star count. Write the list to `data/raw/frozen_repo_list.json`. If the PyPI API fails to return a sufficient number of valid repos after 3 retries with exponential backoff, fall back to a hard-coded, verified list of top PyPI repos. (e.g., requests, flask, django, etc.) stored in a constant within the script. Copy `data/raw/frozen_repo_list.json` to `data/raw/repo_list.json`.** **Verification**: Ensure JSON schema includes `repo_url`, `github_url`, `star_count` and count is **exactly 20**. Log the selected repo URLs and confirm the count is 20. **Wait for T009 completion**.
- [X] T011 [P] Implement model loader for `Salesforce/codegen-350M-mono` with **strict 4-bit quantization fallback logic: if 4-bit fails, attempt 8-bit, then full precision, and abort only if all fail** and **explicitly verify quantization configuration is active** in `code/utils/model_loader.py`
- [X] T011b [P] **Define `MemoryLimitException`** class in `code/utils/exceptions.py` for use by memory monitoring tasks. **[FR-006: Defines the exception class required for memory monitoring compliance]**. **No dependency on T008; the exception class is independent of the monitoring utility setup.**
- [X] T011c [P] **Verify Quantization Fallback**: Create a unit test or script in `code/utils/` that explicitly triggers the fallback logic (e.g., by mocking a 4-bit failure) and verifies the system successfully loads the model using 8-bit or full precision. **Verification**: Run the test script and confirm it exits with code 0 and logs "Fallback successful". **Wait for T011 completion**
- [X] T012 [US1] Unit test for AST parser skipping malformed files in `tests/unit/test_ast_parser.py`
- [X] T013 [US1] Unit test for `null` handling when no docstring exists in `tests/unit/test_coverage.py`
- [X] T014 [US1] Integration test for single-repo extraction pipeline in `tests/integration/test_extraction.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repository Data Extraction and Ground Truth Preparation (Priority: P1) 🎯 MVP

**Goal**: Extract public method signatures and human-written docstrings from a representative set of top PyPI repositories, **truncate the list to a maximum of 1,000 methods per repository** (fixed sample), and output a structured JSON dataset.

**Independent Test**: Run extraction on a single known repository (e.g., `requests`) and verify output JSON contains correct signatures, `null` for missing docstrings, and **row count <= 1,000** (or less if repo has fewer).

### Implementation for User Story 1

- [X] T015 [US1] Implement Git repository clone utility in `code/utils/git_clone.py` and verify repo exists in `data/raw/repos/`. **Wait for T010 completion**
- [X] T016 [US1] Implement file walker to filter `.py` files (generator function) and verify via unit test returning list of.py files in `code/utils/file_walker.py`
- [X] T017 [US1] Integrate AST parser to extract public method signatures and docstrings in `code/extract.py`. **Wait for T015 completion**
- [X] T018 [US1] Implement logic to truncate method lists to **max [deferred] methods per repository** (fixed sample, per FR-001 and Constitution Principle VII), log counts, and **verify output JSON row count <= 1,000** in `code/extract.py`. **Wait for T017 completion**
- [ ] T019 [US1] Serialize extracted data (including **`ast_params`** list) to `data/raw/repos/`, **compute SHA-256 checksum, and record ONLY in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` under `artifact_hashes`**. **Sub-task**: Ensure `state/projects/` directory exists and initialize the YAML file if missing with the schema: `artifact_hashes: { filename: "sha256_hash" }` before recording the hash. **Wait for T018 completion**. **Note**: This task satisfies Constitution Principle V (Versioning Discipline) as mandated by the Plan's 'Constitution Check' section.
- [X] T020 [US1] Add validation to ensure `human_docstring` is `null` (not empty string) when missing in `code/extract.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - LLM Docstring Generation with Resource Constraints (Priority: P2)

**Goal**: Load the `Salesforce/codegen-350M-mono` model in **4-bit** quantization (strict, with fallback) and generate docstrings for the **truncated list of up to 1,000 methods per repository** with a **fixed temperature**, ensuring completion within 6 hours on CPU.

**Independent Test**: Run generation on a subset of **50** methods. Verify output file contains generated text, model loads in CPU mode (strict 4-bit with fallback), and memory stays **under 7 GB RAM** as monitored via `/proc/self/status`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [US2] Unit test for model loading with 4-bit quantization and fallback enforcement in `tests/unit/test_generation.py`
- [X] T022 [US2] Unit test for memory monitoring during generation in `tests/unit/test_monitor.py`
- [X] T023 [US2] Integration test for generation on a small batch in `tests/integration/test_generation.py`

### Implementation for User Story 2

- [X] T024 [US2] Implement docstring generation loop: **Execute `python code/generate.py`** to iterate over all JSON files in `data/raw/repos/*.json` in sorted filename order (run in parallel per repo), load each, generate docstrings with **a fixed temperature of 0.2**, and **explicitly enforce a hard limit on the number of methods per repository in the generation logic** (slice the list if necessary). Write intermediate results to `data/processed/generation_batch_{repo_id}.json` **preserving `ast_params`**. **Verification**: Explicitly check that row count per batch <= 1,000. **Wait for T019 completion**
- [X] T025 [US2] Integrate memory monitoring to abort if RAM > 7 GB, logging a specific `RAM_LIMIT_EXCEEDED` entry to `logs/monitor.log` and raising a `MemoryLimitException` (defined in `code/utils/exceptions.py`) in `code/generate.py`. **Implementation Detail**: If RAM limit is hit, **immediately abort the process** after logging. **Do NOT retry with smaller chunks**. **Wait for T024 completion**
- [X] T027 [US2] **Handle empty/whitespace generated docstrings**: **Create a new script `code/post_process.py`** to read from `data/processed/generation_batch_{repo_id}.json` (after all T024 batches complete), **flag records with empty/whitespace docstrings by setting `needs_review` to true**. **Do NOT calculate coverage_score here**. **Write the updated records back to a NEW file: `data/processed/generation_batch_{repo_id}_cleaned.json`**. **Wait for T024 completion (all batches)**
- [X] T026 [US2] **Aggregate and Consolidate**: **Execute `python code/aggregate.py`** to merge `data/processed/generation_batch_*_cleaned.json` into a single `data/processed/results.json`, **preserving `ast_params`**, and **verify the final file structure and total row count <= 20,000 (20 repos * 1000 methods)**. **Wait for T027 completion**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Parameter Coverage Analysis and Statistical Comparison (Priority: P3)

**Goal**: Calculate Parameter Coverage Scores, compute auxiliary semantic similarity, and perform a Wilcoxon signed-rank test to determine statistical significance.

**Independent Test**: Feed synthetic dataset of balanced perfect matches and mismatches; verify Wilcoxon p-value < 0.05 and coverage scores align with labels.
### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [US3] Unit test for Parameter Coverage Score calculation edge cases (complex type hints) in `tests/unit/test_coverage.py`
- [ ] T030a [P] **Create file `tests/unit/test_stats.py`**. **Wait for T026 completion**
- [ ] T030b [P] **Implement unit tests for both semantic similarity calculation and Wilcoxon test with small dataset warning in `tests/unit/test_stats.py`**. **Verification**: Run `pytest tests/unit/test_stats.py` and ensure all tests pass. **Wait for T030a completion**

### Implementation for User Story 3

- [ ] T041b [P] Refactor `code/analyze.py` to expose `main()` functions with explicit argument parsing and remove global execution code. **Wait for T026 completion**
- [ ] T033 [US3] **Verify `data/processed/results.json` exists and is non-empty**. If missing, raise `FileNotFoundError`. **Implement Parameter Coverage Score calculation**: `(matched params / total AST params)` using **`docstring_parser`** to parse docstring text and matching against **`ast_params`** from `data/processed/results.json`. **Execute `python code/analyze.py --step=coverage`** to calculate scores and **write to `data/processed/results_with_coverage.json`**. **Verification**: Confirm output file exists and contains a `coverage_score` field for every record. **Wait for T026 completion, T041b completion**
- [ ] T034 [US3] **Verify `data/processed/results_with_coverage.json` exists and is non-empty**. **Implement semantic similarity calculation** using `sentence-transformers/all-MiniLM-L6-v2` as auxiliary metric reading from `data/processed/results_with_coverage.json` (output of T033). **Execute `python code/analyze.py --step=similarity`** to calculate scores and **append results to create `data/processed/results_with_scores.json`**. **Verification**: Confirm output file exists and contains a `semantic_similarity` field for every record. **Wait for T033 completion**
- [ ] T035 [US3] **Verify `data/processed/results_with_scores.json` exists and is non-empty**. **Implement Wilcoxon signed-rank test** for paired Human vs. LLM scores reading from `data/processed/results_with_scores.json` (output of T034). **Include logic to log a warning if total method pairs < 30 AND proceed with the calculation**. **Execute `python code/analyze.py --step=stats`** and **write to `data/processed/results_with_stats.json`**. **Wait for T034 completion**
- [ ] T037 [US3] **Verify `data/processed/results_with_stats.json` exists**. Generate final report with p-value, test statistic, and coverage rates to `data/processed/final_report.json`. **Execute `python code/analyze.py --report`**. **Wait for T035 completion**
- [ ] T038 [US3] **Verify `data/processed/final_report.json` exists**. Handle complex type hints (e.g., `List[Dict[str, Any]]`) as unmatched but non-crashing reading from `data/processed/final_report.json` (or re-run analysis on final dataset if needed). **Execute `python code/analyze.py`**. **Wait for T037 completion**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Update README.md with installation instructions and usage examples
- [ ] T040 [P] Update quickstart.md with step-by-step execution guide
- [X] T041a [P] Refactor `code/extract.py` to expose a `main()` function with explicit argument parsing and remove global execution code.
- [ ] T043 [P] Add unit tests for uncovered code paths identified by coverage report
- [ ] T044 Run `python -m code.quickstart` and verify exit code 0
- [ ] T045 Run `scripts/verify_repro.sh` and ensure `state/projects/$(PROJECT_SLUG).yaml` matches the hash recorded in the initial commit or a baseline file.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: **Sequential Data Flow Required**
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: **Depends on US1 (T019)** - Requires output from US1 (`data/raw/repos/`)
 - **User Story 3 (P3)**: **Depends on US2 (T026)** - Requires output from US2 (`data/processed/results.json`)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Depends on US1 (T019)** - **Data Dependency**: Requires output from US1 (`data/raw/repos/`)
- **User Story 3 (P3)**: **Depends on US2 (T026)** - **Data Dependency**: Requires output from US2 (`data/processed/results.json`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Utilities (AST, Coverage, Stats) in Phase 2 must be complete first
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **User Stories CANNOT start in parallel due to data dependencies.**
 - US1 must complete before US2 begins.
 - US2 must complete before US3 begins.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel **ONLY if they are independent tasks (e.g., T015, T016).**
- **IMPORTANT**: The analysis pipeline tasks (T033, T034, T035, T037, T038) are **strictly sequential** and CANNOT be parallelized. The note "Models within a story marked [P] can run in parallel" does NOT apply to these sequential data-processing steps.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for AST parser skipping malformed files in tests/unit/test_ast_parser.py"
Task: "Unit test for null handling when no docstring exists in tests/unit/test_coverage.py"

# Launch all models for User Story 1 together:
Task: "Implement Git repository clone utility in code/utils/git_clone.py"
Task: "Implement file walker to filter.py files in code/utils/file_walker.py"
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
 - Developer B: User Story 2 (can start if mock data is available for dev, but final run needs US1)
 - Developer C: User Story 3 (can start if mock data is available for dev, but final run needs US2)
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
- **CRITICAL**: Data flow must be respected: US1 (Extract) → US2 (Generate) → US3 (Analyze). Do not run US2 before US1 produces data.
- **CRITICAL**: Model loading MUST enforce 4-bit quantization with fallback to 8-bit/full precision if 4-bit fails, aborting only if all fail (Constitution Principle VII).
- **CRITICAL**: All data sources must be real; no synthetic fallbacks for data loading.
- **CRITICAL**: Fixed sample size is capped at **[deferred]** methods per repository as per Spec (FR-001) and Constitution Principle VII.
- **NOTE**: T011b defines `MemoryLimitException` required by T025 and is now in Phase 2.
- **NOTE**: T027 correctly reads from intermediate batch files, sets flags, and writes to a new `_cleaned` file before T026 aggregates.
- **NOTE**: T026 and T033 now write to distinct files (`results.json` vs `results_with_coverage.json`) to prevent overwrites.
- **NOTE**: T010 prioritizes a frozen, deterministic list (exactly 20) to ensure reproducibility, sourced from PyPI.
- **NOTE**: T011c explicitly verifies the quantization fallback logic.
- **NOTE**: T030a and T030b split test creation and implementation for better granularity.
- **NOTE**: T033-T038 are strictly sequential to prevent race conditions and now include file existence checks and correct dependency chains.
- **NOTE**: T019 explicitly references Constitution Principle V to ensure traceability for versioning requirements.
- **NOTE**: T025 mandates immediate abort on RAM limit breach; no chunking retries allowed.
- **NOTE**: T027 now only flags `needs_review` and does not calculate coverage scores.