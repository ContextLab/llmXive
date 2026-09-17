# Tasks: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-code-generation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **[S]**: Sequential - must complete before dependent tasks
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

- [X] T001a [P] Create project structure: **Create a script `scripts/setup.sh` with the following exact content**:
 ```bash
 #!/bin/bash
 set -e
 DIRS=("code" "code/utils" "data/raw/repos" "data/processed" "tests/unit" "tests/integration" "state" "state/projects" "logs")
 mkdir -p "${DIRS[@]}"
 for dir in "${DIRS[@]}"; do
 touch "$dir/.gitkeep"
 done
 echo -n "" > logs/setup.log
 for dir in "${DIRS[@]}"; do
 echo "$dir" >> logs/setup.log
 done
 ```
 Run `bash scripts/setup.sh`. **Verification**: Run `bash scripts/setup.sh` and verify `logs/setup.log` exists and contains exactly the list of directory paths, one per line, and that `.gitkeep` files exist in all listed directories. **No dependencies**.
- [X] T001b [S] Verify `.gitkeep` files: **Verify that `.gitkeep` exists in every directory listed in `logs/setup.log` using `for dir in $(cat logs/setup.log); do test -f "$dir/.gitkeep" || exit 1; done`**. **Wait for T001a completion**.

- [X] T002a [P] Create `requirements.txt`: **Create `code/requirements.txt`** with the exact dependencies: `transformers==4.35.0`, `torch==2.1.0`, `bitsandbytes==0.41.0`, `sentence-transformers==2.2.2`, `docstring_parser==0.16`, `scipy==1.11.0`, `requests==2.31.0`, `pyyaml==6.0.1`, `pytest==7.4.0`. **Verification**: Run `pip install -r code/requirements.txt` and verify no errors.
- [X] T002b [P] Implement config.py: **Create `code/config.py`** with explicit random seed pinning for `numpy`, `random`, `torch`, and `transformers` (e.g., `SEED = 42`) and a constant `MAX_METHODS = 1000` to enforce the fixed sample size per Spec FR-001. **Verification**: Run a dummy import of `config.py` and verify the seed and `MAX_METHODS` are set.
- [X] T002c [P] Verify reproducibility: **Create and run a dummy verification script `code/verify_seed.py`** that generates a random number using the pinned seeds and logs it. Run it twice and verify the output is identical. **Verification**: Run `python code/verify_seed.py` twice and compare outputs. **Wait for T002b completion**.

- [X] T003 [P] Create `.flake8` (max-line-length=88) and `pyproject.toml` (black settings) configuration files

- [ ] T018b [S] **Update Plan to Align with Spec**: **Edit `plan.md` to ensure the 'Performance Goals' and 'Constraints' sections explicitly state '20 repos × [deferred] methods = 20,000 total [UNRESOLVED-CLAIM: c_4ab8f021 — status=not_enough_info]' and remove any reference to '100 methods' or '[deferred] methods' as a placeholder for the cap, replacing it with the concrete 1000 limit mandated by FR-001**. **Verification**: Grep `plan.md` for '100 methods' and ensure it is absent; grep for '[deferred] methods' and ensure it is present. **Wait for T002c completion**. <!-- FAILED: unspecified -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading utilities and model loaders.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T011b [S] **Define `MemoryLimitException`** class in `code/utils/exceptions.py` for use by memory monitoring tasks. **[FR-006: Defines the exception class required for memory monitoring compliance]**. **No dependencies**.
- [X] T010 [S] **Create/freeze `data/raw/frozen_repo_list.json`**: **Implement `code/utils/repo_fetcher.py` to fetch a representative set of top-ranked Python repositories on the PyPI leaderboard via the HuggingFace dataset `pypi/top-100` or the PyPI JSON API (` or `https://pypi.org/pypi/{package}/json`) with a **retry mechanism with exponential backoff (A limited number of retries)**. Sort them deterministically by star count. Write the list to `data/raw/frozen_repo_list.json`. The script MUST enforce that the final list contains a predetermined number of items. If the API/mirror fails to return the required number of valid repos after retries, the script MUST raise an exception and fail loudly. [UNRESOLVED-CLAIM: c_0564bfcd — status=not_enough_info] (do NOT proceed with a fallback list). Copy `data/raw/frozen_repo_list.json` to `data/raw/repo_list.json`.** **Output Schema**: JSON array of objects with `repo_url`, `github_url`, `star_count`. **Verification**: Ensure JSON schema includes required fields and count is **exactly 20**. Log the selected repo URLs and confirm the count is 20. **Wait for T002c completion**.
- [X] T011 [S] **Implement strict low-bit quantization model loader with fallback**: **Create `code/utils/model_loader.py` to load `Salesforce/codegen-mono

The research question is to evaluate the effectiveness of code generation models in mono-lingual settings. The method involves fine-tuning open-source transformer-based language models on large-scale code corpora, following the approach described by Nijkamp et al. (2023). [UNRESOLVED-CLAIM: c_65f21f62 — status=not_enough_info] ` using **4-bit quantization** via `bitsandbytes`. **If 4-bit quantization fails (e.g., OOM or unsupported), the script MUST attempt 8-bit quantization. If 8-bit fails, it MUST attempt full precision. If all quantization levels fail, the script MUST raise a `QuantizationError` and abort.** Explicitly verify quantization configuration is active before returning the model. **Verification**: Run the loader and verify the log output shows the successful fallback chain if 4-bit fails (e.g., "Attempting 4-bit... Failed. Attempting 8-bit... Success"). **Wait for T011b completion**.
- [X] T012 [US1] Unit test for AST parser skipping malformed files in `tests/unit/test_ast_parser.py`
- [X] T013 [US1] Unit test for `null` handling when no docstring exists in `tests/unit/test_coverage.py`
- [X] T014 [US1] Integration test for single-repo extraction pipeline in `tests/integration/test_extraction.py`
- [X] T041b [S] **Define CLI interface for analyze.py**: **Refactor `code/analyze.py` to expose a `main()` function with explicit argument parsing for `--step` (values: `coverage`, `similarity`, `stats`, `report`).** **Wait for T002c completion**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repository Data Extraction and Ground Truth Preparation (Priority: P1) 🎯 MVP

**Goal**: Extract public method signatures and human-written docstrings from a representative set of top PyPI repositories, **truncate the list to a maximum of 1,000 methods per repository ** (fixed sample per Spec FR-001), and output a structured JSON dataset.

**Independent Test**: Run extraction on a single known repository (e.g., `requests`) and verify output JSON contains correct signatures, `null` for missing docstrings, and **row count <= 1,000** (or less if repo has fewer).

### Implementation for User Story 1

- [X] T015 [US1] Implement Git repository clone utility in `code/utils/git_clone.py` and verify repo exists in `data/raw/repos/`. **Wait for T010 completion**
- [X] T016 [US1] Implement file walker to filter `.py` files (generator function) and verify via unit test returning list of.py files in `code/utils/file_walker.py`
- [X] T017 [US1] Integrate AST parser to extract public method signatures and docstrings in `code/extract.py`. **Wait for T015 completion**
- [X] T018 [US1] Implement logic to truncate method lists to **max 1000 methods per repository** (fixed sample, per Spec FR-001 and Constitution Principle VII), log counts, and **verify output JSON row count <= 1,000 ** in `code/extract.py`. **Wait for T017 completion**. **Note**: The task MUST iterate over ALL 20 repos listed in `data/raw/frozen_repo_list.json`. **Before processing, verify `data/raw/frozen_repo_list.json` exists and contains exactly 20 items; if not, raise `FileNotFoundError`**. **Output files must be named `data/raw/repos/{repo_slug}.json`**. **Wait for T010 completion, T018b completion**. <!-- FAILED: unspecified -->
- [X] T019 [US1] Serialize extracted data (including **`ast_params`** list) to `data/raw/repos/{repo_slug}.json`, **compute SHA-256 checksum for EACH raw JSON file in `data/raw/repos/` BEFORE recording the hash [UNRESOLVED-CLAIM: c_96068c76 — status=not_enough_info], and record the hash in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` under `artifact_hashes` using the key format `artifact_hashes: { 'data/raw/repos/{repo_slug}.json': 'sha256...' }`**. **Sub-task**: Ensure `state/projects/` directory exists (Wait for T001a) and initialize the YAML file if missing with the schema: `artifact_hashes: {}` before recording the hash. If the file exists, merge the new hash under `artifact_hashes` using the logic `artifact_hashes[filename] = sha256_hash`. **Wait for T018 completion, T001a completion**. **Note**: This task satisfies Constitution Principle V (Versioning Discipline) as mandated by the Plan's 'Constitution Check' section.
- [X] T020 [US1] Add validation to ensure `human_docstring` is `null` (not empty string) when missing in `code/extract.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - LLM Docstring Generation with Resource Constraints (Priority: P2)

**Goal**: Load the `Salesforce/codegen-350M-mono` model in **4-bit quantization with fallback** (no abort on 4-bit failure) and generate docstrings for the **truncated list of up to 1,000 methods per repository** with a **fixed temperature (a low, subcritical value)**, ensuring completion within 6 hours on CPU [UNRESOLVED-CLAIM: c_e24b5acb — status=not_enough_info].

**Independent Test**: Run generation on a subset of **50** methods. [UNRESOLVED-CLAIM: c_183a667e — status=not_enough_info] Verify output file contains generated text, model loads in CPU mode (with fallback if 4-bit fails), and memory stays **under 7 GB RAM** as monitored via `/proc/self/status` [UNRESOLVED-CLAIM: c_10620d96 — status=not_enough_info].

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [US2] Unit test for model loading with 4-bit quantization and fallback logic in `tests/unit/test_generation.py`
- [X] T022 [US2] Unit test for memory monitoring during generation in `tests/unit/test_monitor.py`
- [X] T023 [US2] Integration test for generation on a small batch in `tests/integration/test_generation.py`

### Implementation for User Story 2

- [X] T024 [US2] [S] Implement docstring generation loop: **Execute `python code/generate.py --temperature 0.2 --input-dir data/raw/repos --output-dir data/processed`** to iterate over all JSON files in `data/raw/repos/{repo_slug}.json` in sorted filename order (single script invocation). The script MUST load the model with **4-bit quantization** [UNRESOLVED-CLAIM: c_82e2ab22 — status=not_enough_info] (enforced by T011, with fallback to 8-bit/full precision if 4-bit fails) and generate docstrings with a **fixed temperature parameter (a low value)**. **Explicitly enforce a hard limit on the number of methods per repository** by reading `MAX_METHODS` from `code/config.py` (defined in T002b). Slice the list if necessary. The script MUST re-verify the quantization configuration before generation to prevent drift. Write intermediate results to `data/processed/generation_batch_{repo_slug}.json` **preserving `ast_params`**. **Verification**: Explicitly check that row count per batch <= 1,000. **Wait for T019 completion**. **Note**: The generation loop MUST explicitly re-verify the quantization configuration before generation to prevent drift. **Wait for T011 completion**.
- [X] T025 [US2] Integrate memory monitoring to abort if RAM > 7 GB [UNRESOLVED-CLAIM: c_3a6c5fb5 — status=not_enough_info], logging a specific `RAM_LIMIT_EXCEEDED` entry to `logs/monitor.log` and raising a `MemoryLimitException` (defined in `code/utils/exceptions.py`) in `code/generate.py`. **Implementation Detail**: If RAM limit is hit, **immediately abort the process** after logging. **Do NOT retry with smaller chunks**. **Wait for T024 completion, T011b completion**
- [X] T027 [US2] [S] **Handle empty/whitespace generated docstrings**: **Create a new script `code/post_process.py`** to read from `data/processed/generation_batch_{repo_slug}.json` (after T024 completes), **flag records with empty/whitespace docstrings by setting `needs_review` to true AND calculate Parameter Coverage Score as 0.0 for these records**. **Logic**: `if not docstring.strip(): needs_review = True; coverage_score = 0.0`. **Write the updated records back to a NEW file: `data/processed/generation_batch_{repo_slug}_cleaned.json`**. **Output Schema**: Input schema (from T024) + `needs_review: boolean` + `coverage_score: float`. **Wait for T024 completion (all batches)**
- [ ] T027a [S] **Document Intermediate Schema**: **Update `data-model.md` to explicitly define the schema for `generation_batch_{repo_slug}_cleaned.json` (Input + `needs_review` boolean + `coverage_score`)**. **Wait for T027 completion**
- [X] T026 [US2] **Aggregate and Consolidate**: **Execute `python code/aggregate.py`** to merge `data/processed/generation_batch_*_cleaned.json` into a single `data/processed/results.json`, **preserving `ast_params`**, and **verify the final file structure and total row count <= 20,000 (20 repos * 1000 methods) [UNRESOLVED-CLAIM: c_9475fdb0 — status=not_enough_info] **. **Wait for T027 completion**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Parameter Coverage Analysis and Statistical Comparison (Priority: P3)

**Goal**: Calculate Parameter Coverage Scores, compute auxiliary semantic similarity, and perform a Wilcoxon signed-rank test to determine statistical significance.

**Independent Test**: Feed synthetic dataset of balanced perfect matches and mismatches; verify Wilcoxon p-value < 0.05 [UNRESOLVED-CLAIM: c_b0080d0c — status=not_enough_info] and coverage scores align with labels.
### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] **Implement unit tests for semantic similarity calculation and Wilcoxon test with small dataset warning in `tests/unit/test_stats.py`**. **Verification**: Run `pytest tests/unit/test_stats.py` and ensure all tests pass. **Verify that the log contains the warning message "Statistical power may be low (n < 30)" when n < 30 and that the test proceeds**. **Wait for T026 completion**

### Implementation for User Story 3

- [ ] T033 [US3] **Verify `data/processed/results.json` exists and is non-empty**. If missing, raise `FileNotFoundError`. **Implement Parameter Coverage Score calculation**: `(matched params / total AST params)` using **`docstring_parser`** to parse docstring text and matching against **`ast_params`** from `data/processed/results.json`. **Ground Truth**: The denominator (total params) MUST be the `ast_params` list extracted by the AST parser in T017/T018. If `ast_params` is empty, score = 0.0. If `docstring_parser` fails, set `parse_error: true` and score = 0.0. **Execute `python code/analyze.py --step=coverage`** to calculate scores and **write to `data/processed/results_with_coverage.json`**. **Verification**: Confirm output file exists and contains a `coverage_score` field for every record. **Wait for T026 completion, T041b completion**
- [ ] T034 [US3] **Verify `data/processed/results_with_coverage.json` exists and is non-empty**. **Implement semantic similarity calculation** using `sentence-transformers/all-MiniLM-L-v2` as auxiliary metric reading from `data/processed/results_with_coverage.json` (output of T033). **Execute `python code/analyze.py --step=similarity`** to calculate scores and **append results to create `data/processed/results_with_scores.json`**. **Verification**: Confirm output file exists and contains a `semantic_similarity` field for every record. **Wait for T033 completion**
- [X] T035a [S] **Implement small dataset warning logic**: **Refactor `code/utils/stats.py` to include a function that logs a warning "Statistical power may be low (n < 30)" if the number of pairs is small, but still proceeds with the Wilcoxon calculation**. **Wait for T034 completion**.
- [ ] T035 [US3] **Verify `data/processed/results_with_scores.json` exists and is non-empty**. **Implement Wilcoxon signed-rank test** for **paired comparison of Human vs. LLM coverage scores** reading from `data/processed/results_with_scores.json` (output of T034). **Include logic to log a warning if total method pairs < 30 AND proceed with the calculation [UNRESOLVED-CLAIM: c_03acc083 — status=not_enough_info]** (using T035a). **Execute `python code/analyze.py --step=stats`** and **write to `data/processed/results_with_stats.json`**. **Wait for T034 completion, T035a completion**
- [ ] T037 [US3] **Verify `data/processed/results_with_stats.json` exists**. Generate final report with p-value, test statistic, and coverage rates to `data/processed/final_report.json`. **Execute `python code/analyze.py --report`**. **Wait for T035 completion**

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
- **IMPORTANT**: The analysis pipeline tasks (T033, T034, T035, T037) are **strictly sequential** and CANNOT be parallelized. The note "Models within a story marked [P] can run in parallel" does NOT apply to these sequential data-processing steps.

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
- **CRITICAL**: Model loading MUST enforce 4-bit quantization with fallback to 8-bit/full precision (Constitution Principle VII, Spec FR-002). If 4-bit fails, attempt 8-bit. If 8-bit fails, attempt full precision. Only abort if all fail.
- **CRITICAL**: All data sources must be real; no synthetic fallbacks for data loading.
- **CRITICAL**: Fixed sample size is capped at **[deferred]** methods per repository as per Spec FR-001. The Plan's mention of "100 methods" has been corrected by T018b.
- **NOTE**: T011b defines `MemoryLimitException` required by T025 and is now in Phase 2, before T011.
- **NOTE**: T025 mandates immediate abort on RAM limit breach; no chunking retries allowed.
- **NOTE**: T027 now flags `needs_review`, calculates `coverage_score` as 0.0 for empty docstrings, and writes to a new `_cleaned` file before T026 aggregates.
- **NOTE**: T026 and T033 now write to distinct files (`results.json` vs `results_with_coverage.json`) to prevent overwrites.
- **NOTE**: T010 prioritizes a frozen, deterministic list (exactly 20) to ensure reproducibility, sourced from PyPI/HuggingFace. If the API returns < 20, the task fails (no fallback).
- **NOTE**: T011c explicitly verifies the quantization fallback logic (integrated into T011).
- **NOTE**: T030 merges T030a and T030b for better granularity.
- **NOTE**: T033-T037 are strictly sequential to prevent race conditions and now include file existence checks and correct dependency chains.
- **NOTE**: T019 explicitly references Constitution Principle V to ensure traceability for versioning requirements and specifies the YAML key format.
- **NOTE**: T041b is marked [S] (Sequential) and moved to Phase 2 to prevent race conditions with dependent analysis tasks.
- **NOTE**: T024 is marked [S] (Sequential) as it is a single script iterating over all repos.
- **NOTE**: T038 has been removed; complex type hint handling is integrated into T033.
- **NOTE**: T018b is added to update the Plan.md to align with Spec FR-001 ([deferred] methods cap) and moved to Phase 1.
- **NOTE**: T034 uses `sentence-transformers/all-MiniLM-L-v2` as specified in the User Story 3 acceptance criteria.
- **NOTE**: T035a is added to implement the small dataset warning logic.