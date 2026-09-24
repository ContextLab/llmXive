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
- [X] T001b Initialize Python 3.11 project with pinned dependencies (`requirements.txt`) and `pypy.toml`
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
- [X] T008a [P] Implement model-fallback logic in `code/utils/config.py` to switch from a primary embedding model to a configurable `FALLBACK_EMBEDDING_MODEL`. **Constraint**: The fallback MUST be exactly the model `all-MiniLM-L-v2` (quantized) as mandated by Spec Edge Cases. **Output**: A fallback mechanism that logs the switch and retries with this specific model ID. **Note**: Ambiguity like "or smaller" is removed; the model ID is fixed.
- [X] T008b [P] Implement logging infrastructure for T008a to record model switches and memory fallback events.
- [X] T009 [P] Create `data-sources.yaml` configuration file containing exact API endpoints, DOI lists, and fetch parameters for ML (arXiv) and non-ML (Nature Climate Change, Health Affairs) domains.
- [X] T009a [P] Implement validation logic for `data-sources.yaml` to ensure required fields are present and URLs are valid formats.
- [X] T009b [P] Implement the two-group design constraint in `code/03_proposal_generation.py`. **Action**: Create a strict validation function `validate_generation_design()` that asserts the generation logic only produces 'pattern-guided' and 'baseline' groups, explicitly rejecting any 'random-pattern' logic. **Dependency**: This task enforces Spec FR-003 in code, regardless of plan text. **Output**: A validation function and unit test `test_two_group_design_enforcement`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Corpus Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest and prepare abstracts from ML and non-ML domains (Public Health, Climate Adaptation) to establish the baseline dataset.

**Independent Test**: The system can be tested by verifying that the dataset directory contains a representative set of processed JSON files with valid metadata fields and that the data fits within the available RAM constraint.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_data_acquisition.py` to download ML and non-ML abstracts using endpoints defined in `data-sources.yaml`. **Specifics**: Use arXiv API with `cat:cs.LG` and `cat:q-bio.QM` for ML, and specific DOI lists/API endpoints from `data-sources.yaml` for *Nature Climate Change* and *Health Affairs*. **Algorithm**: Iterate through paginated API results, filtering for acceptance status, and accumulate rows until a balanced sample of ML, Non-ML Accepted, and Non-ML Rejected records are collected. If the API returns more than needed, truncate; if fewer, continue to next page. Stop when counts are met or source exhausted. **Output**: Write raw data to `data/raw/corpus_raw.jsonl`. Ensure query parameters explicitly filter for acceptance status where available.
- [X] T012 [US1] Implement strict validation function `validate_fetch_status()` in `code/01_data_acquisition.py` that raises `DataFetchError` on 403/404 or paywall detection. **Graceful Failure**: Must log the specific venue name (from `data-sources.yaml`) and halt the pipeline with a user-friendly error message indicating which venue failed. **Verification**: Unit test `test_fetch_fail_loudly` asserts exception raised with correct message. Do NOT generate synthetic data.
- [X] T013 [US1] Implement preprocessing pipeline in `code/01_data_acquisition.py` to normalize text and filter malformed entries.
- [X] T014 [US1] Implement streaming/chunking logic in `code/01_data_acquisition.py` via `extract_until(target=50, source='full_corpus', seed=42)` to dynamically extract rows. **Algorithm**: Iterate through the full corpus (ML, Non-ML Accepted, Non-ML Rejected). Extract rows until a sufficient number of unique non-ML problem statements (unique by SHA-256 hash of abstract text) are found. **Critical Rule**: Simultaneously track the counts of ML and Non-ML Rejected records. If the extraction reaches 50 non-ML statements but the ML or Non-ML Rejected counts deviate by >5% from the target proportion (approx. 1:1:1 ratio), raise `BalanceError` and halt. **Dependency**: Must complete T014a before writing final processed file. **Output**: Write a temporary sample to `data/processed/corpus_sample_temp.jsonl`.
- [X] T014a [US1] Implement domain balance validation in `code/01_data_acquisition.py`. **Action**: After sampling, verify that the final sample maintains the target proportions (balanced ML, Non-ML Accepted, and Non-ML Rejected). **Constraint**: Fail if proportions deviate by >5%. **Input**: Read from `data/processed/corpus_sample_temp.jsonl` (output of T014). **Output**: If valid, write to `data/processed/corpus_sample_validated.jsonl`; if invalid, raise `BalanceError`. **Dependency**: Runs after T014 (temp file) and before T016 (final file).
- [X] T015 [US1] Configure `logging` in `code/01_data_acquisition.py` to write `ERROR` level events to `logs/data_acquisition.log` with timestamp and URL context.
- [X] T016 [US1] Generate `data/processed/corpus.jsonl` with metadata (title, abstract, venue, acceptance_status, domain) from the validated sample.

### Tests for User Story 1

- [X] T017 [P] [US1] Contract test for data download validation in `tests/unit/test_data_parsing.py`
- [X] T018 [P] [US1] Implement `test_memory_usage_full_load` in `tests/unit/test_memory_usage_constraint.py`. **Input**: Full dataset loaded via `stream_and_sample`. **Implementation**: Use Python's standard library `tracemalloc` to measure peak memory usage. **Assertion**: Assert `peak_memory_usage < 7000000000` (7 GB). **Output**: Write a deterministic log file `data/results/memory_usage_report.json` containing the peak memory value and pass/fail status. **Schema**: `{ "peak_memory_gb": float, "timestamp": str, "status": "pass" | "fail" }`. **Validation**: Assert file exists and matches schema before passing test. **Fixture**: Use a mock data source that yields a sufficient number of items to simulate full load.
- [X] T019 [P] [US1] Implement `test_preprocessing_validation` in `tests/unit/test_preprocessing_validation.py`. **Input**: Raw corpus with empty abstracts. **Assertion**: Assert `preprocessing_pipeline` raises `ValueError` or filters out empty entries. **Fixture**: Use `data/raw/corpus_raw.jsonl` with injected malformed entries.
- [X] T018a [P] [US1] Test `data-sources.yaml` validation and usage in `code/01_data_acquisition.py` in `tests/unit/test_data_sources_config.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pattern Mapping and Proposal Generation (Priority: P2)

**Goal**: Map non-ML problem statements to ML-derived ideation patterns and generate paired research proposals (pattern-guided vs. baseline).

**Independent Test**: The system can be tested by running the generation pipeline on a small subset to verify logic, then scaling to 50 pairs within 4 hours on the CPU runner.

### Implementation for User Story 2

- [X] T020 [US2] Implement `retrieve_top_k_patterns()` in `code/02_pattern_mapping.py` using `sentence-transformers` (`all-MiniLM-L6-v2` quantized) for CPU-tractable embeddings. **Logic**: Return a list of pattern IDs with cosine similarity ≥ 0.6. **Dependency**: Must complete before T024.
- [X] T025 [US2] Implement batch processing in `code/03_proposal_generation.py` using a generator-based batch loader that yields batches of pairs to stay within 7 GB RAM limits. **Constraint**: Batch size calculation must be derived from the sample size 'n' defined in `data/results/power_analysis_config.json`. **Dependency**: This task MUST be completed before T021, T022, and T024. **Note**: T025 is NOT marked [P] as it is a hard prerequisite for T024 execution.
- [X] T024a [US2] [P] Implement statistical power analysis in `code/utils/power_analysis.py` using `statsmodels.stats.power` to confirm the spec's assumption of n=50 pairs, 3 raters, targeting a medium effect size (Cohen's d ≈ 0.5) at α=0.05. **Action**: Perform power analysis. If the analysis indicates the sample size is underpowered, the script MUST log a WARNING and proceed with n=50 as mandated by Spec Assumptions, but flag the result as 'potentially underpowered' in the output config. **Output**: Write a structured config file `data/results/power_analysis_config.json` containing the calculated 'n' (which MUST remain 50 per Spec constraints) and a 'power_status' flag. **Dependency**: Must complete before T024.
- [X] T024b [US2] [P] Implement the justification report generation in `code/utils/power_analysis.py`. **Action**: Generate `data/results/power_analysis_report.md` containing the power analysis logic, assumptions, and the explicit confirmation that n=50 is used per Spec constraints. **Dependency**: Depends on T024a.
- [X] T021 [US2] Implement `code/03_proposal_generation.py` to generate pattern-guided proposals using injected pattern cards. **Constraint**: Generate exactly one proposal per problem statement. **Note**: Strictly adhere to the two-group design (pattern-guided vs baseline) as per FR-003. **Output**: Intermediate proposals written to a temporary file for validation.
- [X] T022 [US2] Implement `code/03_proposal_generation.py` to generate baseline proposals using generic prompts. **Constraint**: Generate exactly one proposal per problem statement. **Note**: Strictly adhere to the two-group design (pattern-guided vs baseline) as per FR-003. **Output**: Intermediate proposals written to a temporary file for validation.
- [X] T023 [US2] Implement `code/02_pattern_validation.py` to enforce the two-group design constraint: verify that the generation pipeline only produces 'pattern-guided' and 'baseline' groups. **Dependency**: Depends on T024 (post-generation validation). **Constraint**: This task is a blocking validation gate that runs AFTER T021/T022/T024 execution. **Action**: Read the final generated proposals from T024 and assert the group distribution.
- [X] T024 [US2] Implement the full generation loop in `code/03_proposal_generation.py` to produce a set of pairs (pattern-guided + baseline) and save to `data/results/generated_proposals.jsonl` with generation metadata stripped for evaluation. **Dependency**: Depends on T020, T025, T024a, T021, T022, T023 (as a post-generation check). **Logic**: Read target sample size 'n' from `data/results/power_analysis_config.json` (written by T024a) and generate n pairs. **Verification**: Assert `data/results/power_analysis_config.json` exists before reading 'n'. **Note**: This task merges generation and saving logic to ensure validation precedes save.

### Tests for User Story 2

- [X] T029 [P] [US2] Test proposal generation logic (strict two-group pairing) in `tests/unit/test_proposal_generation_logic.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Expert Evaluation and Statistical Analysis (Priority: P3)

**Goal**: Aggregate expert ratings and perform statistical tests to determine if pattern-guided proposals differ significantly from baseline.

**Independent Test**: The system can be tested by feeding pre-defined dummy ratings to verify statistical logic and by verifying the loader script successfully ingests pre-collected expert ratings with blinded metadata.

### Implementation for User Story 3

- [X] T030a-code [US3] Implement a reusable API client wrapper in `code/04_evaluation_recruitment.py` for the specified crowdsourcing platform (e.g., Prolific). **Logic**: Implement methods for job posting, submission status polling, and data retrieval. **Output**: A testable module that can be used by humans to execute recruitment. **Dependency**: Must complete before T030a-manual.
- [X] T030a-manual [US3] Implement a script to generate the recruitment job payload and instructions for manual posting. **Action**: Consume `code/04_evaluation_recruitment.py` to construct the JSON payload and a `recruitment_instructions.md` guide for human posting. **Output**: Save payload to `data/results/recruitment_payload.json` and instructions to `data/results/recruitment_instructions.md`. **Dependency**: Depends on T030a-code.
- [X] T030b-code [US3] Implement automated ORCID and experience validation in `code/04_evaluation_recruitment.py`. **Action**: Create `validate_expert_credentials(orcid, years_experience)` function. **Constraint**: Must verify ORCID format and `years_experience >= 5`. **Output**: Returns `True`/`False`. **Dependency**: Must complete before T030a-execute.
- [X] T030b-executable [US3] [P] Generate the standalone validation script `code/utils/validate_expert_credentials.py` using the logic from T030b-code. **Action**: Create a CLI script that accepts a CSV of expert rosters and outputs a verified CSV. **Output**: `code/utils/validate_expert_credentials.py`. **Dependency**: Depends on T030b-code logic.
- [X] T030a-execute [US3] [Manual] Use the generated payload (T030a-manual) to manually post the recruitment job, verify ORCIDs using T030b-executable, and ensure ≥5 years of domain experience. **Action**: Run `python code/utils/validate_expert_credentials.py --input data/results/expert_roster.csv` and update the CSV with a 'verified' column. **Output**: Populate `data/results/expert_roster.csv` with verified experts. **Dependency**: Depends on T030a-manual and T030b-executable. **Artifact**: Save job ID to `data/results/recruitment_job_id.txt`. **Constraint**: The manual step MUST execute the automated validation script and log the verification result (checksum of verified roster) to `state/manifest.yaml` to ensure auditability. **Wait-for-manual**: This task must be marked complete by the human operator before proceeding.
- [X] T030c-prep [US3] [P] Implement `code/04_blind_generator.py` to generate blinded proposals. **Action**: Read `data/results/generated_proposals.jsonl` and strip all generation metadata (e.g., 'pattern-guided', 'baseline', model IDs) to ensure blind evaluation. **Output**: `data/results/blinded_proposals.jsonl`. **Dependency**: Depends on T024 output.
- [X] T030c-manual [US3] [Manual] Generate `data/results/ratings_template.csv` with columns `proposal_id`, `expert_orcid`, `feasibility`, `bottleneck`, `alignment` and distribute to recruited experts (from T030a-execute). **Action**: Before distribution, use `code/04_blind_generator.py` (T030c-prep) to generate the blinded version of the proposals. **Wait-for-manual**: Wait for human input to collect filled ratings. **Output**: `data/results/ratings_template.csv` (generated) and `data/results/ratings_filled.csv` (collected by human). **Dependency**: Depends on T030a-execute and T030c-prep. **Constraint**: The manual step must ensure the blinded file is distributed.
- [X] T030 [US3] [Wait-for-manual] Implement `code/04_evaluation_loader.py` to load expert ratings from `data/results/ratings_filled.csv` (blinded, ORCID verified). **Dependency**: Depends on T030c-manual (wait for file existence). **Validation**: Check schema and row count. **Trigger**: This task starts automatically when `data/results/ratings_filled.csv` exists.
- [X] T032 [US3] Implement IRR gate in `code/05_statistical_analysis.py`: Calculate Krippendorff's alpha on collected ratings; **FAIL** pipeline if alpha < 0.6.
- [X] T032a [US3] [Optional] Implement a secondary Linear Mixed-Effects Model (LMM) analysis in `code/05_statistical_analysis.py` for robustness checking, as mentioned in the initial plan draft. **Constraint**: This is an optional robustness check; the primary analysis remains the Spec-mandated paired t-test/Wilcoxon.
- [X] T033 [P] [US3] Implement `code/05_statistical_analysis.py` to perform normality check on mean scores.
- [X] T034 [US3] Implement dynamic test selection in T033: Paired t-test (normal) or Wilcoxon signed-rank (non-normal).
- [X] T035a [US3] Implement outlier detection in `code/05_statistical_analysis.py`. **Action**: Identify outliers using the IQR method with standard interquartile range multipliers (Q1 - k*IQR, Q3 + k*IQR). **Output**: Generate a list of pairs to be removed. **Dependency**: Must complete before T035b.
- [X] T035b [US3] Re-run statistical test on cleaned data. **Action**: Remove the ENTIRE pair if one member is an outlier to preserve the dependency structure of the paired t-test/Wilcoxon test (statistical justification: paired tests require intact pairs). Re-run the statistical test (T033/T034) on the cleaned dataset. **Output**: Store cleaned test results.
- [X] T035c [US3] Generate sensitivity analysis report. **Action**: Generate `data/results/sensitivity_analysis_report.md` containing pre/post p-values, effect sizes, and explicit documentation of the impact on robustness. **Dependency**: Depends on T035b.
- [X] T035 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for the three metrics (feasibility, bottleneck, alignment). **Condition**: Apply correction to the final results from T035c unconditionally, regardless of power status. **Note**: The 'underpowered' flag from T035d determines the final report's validity status (valid vs. underpowered), but does NOT skip the correction.
- [X] T035d [US3] Implement power check: If pair removal reduces n below 30 pairs or calculated power < 0.8, flag the result as 'underpowered' and log the warning. **Action**: This task runs AFTER T035 to flag the results, but BEFORE T037 (report generation). It does NOT block T035. **Output**: A flag in the final report indicating the study may be underpowered. **Dependency**: Must complete before T037. **Constraint**: If flagged, the final report (T037) MUST include a prominent disclaimer and qualify the "associational, not causal" phrase with the power limitation.
- [X] T036 [US3] Implement `calculate_validity_improvement()` in `code/05_statistical_analysis.py` that computes the mean difference in 'contextual alignment' scores between groups and writes the result (p-value, effect size) to `data/results/validity_metrics.json`.
- [X] T037 [US3] Generate final report in `data/results/analysis_report.md` including p-values, effect sizes, and the phrase "associational, not causal". **Dependency**: Depends on T035d (to include power status disclaimer). **Constraint**: If T035d flagged the result as 'underpowered', the report must include a prominent disclaimer about the power limitation.
- [X] T037a [US3] Verify report generation: Implement an assertion or parser check in `code/05_statistical_analysis.py` or a separate script to confirm the phrase "associational, not causal" is present in `data/results/analysis_report.md`. **Fail** if missing.
- [X] T038 [US3] Verify report generation against `data/results/generated_proposals.jsonl` and `data/results/ratings.csv`.

### Tests for User Story 3

- [X] T039 [P] [US3] Test statistical normality check logic in `tests/unit/test_statistical_normality_check.py`
- [X] T040 [P] [US3] Implement `test_multiple_comparison_correction` in `tests/unit/test_multiple_comparison_correction.py`. **Input**: Dummy p-values for metrics. **Assertion**: Assert Bonferroni/BH correction logic returns expected adjusted p-values. **Fixture**: `data/results/dummy_pvalues.csv`.
- [X] T041 [P] [US3] Test Inter-Rater Reliability (IRR) gate (Krippendorff's alpha ≥ 0.6) in `tests/unit/test_inter_rater_reliability_gate.py`
- [X] T042 [P] [US3] Test sensitivity analysis paired-difference removal logic in `tests/unit/test_sensitivity_analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043a [P] Update `README.md` with CLI usage examples and installation instructions. **Required**: Must include verification of recruitment pipeline.
- [X] T043b [P] Generate API documentation for `code/01_data_acquisition.py`, `code/02_pattern_mapping.py`, and `code/05_statistical_analysis.py` using Sphinx or MkDocs. **Required**: Must include recruitment pipeline documentation.
- [X] T043c [P] Update `docs/` with data flow diagrams and architecture overview. **Required**: Must include recruitment flow.
- [X] T044 Code cleanup and refactoring for memory efficiency
- [X] T045 [US3] Implement benchmarking and validation infrastructure to ensure total pipeline runtime ≤ 6 hours.
- [X] T045a [US3] Implement `code/utils/benchmark_profiler.py` to profile runtime and memory usage for each phase (data, generation, analysis) and log results to `data/results/benchmark_log.json`.
- [X] T045b [US3] Implement caching mechanisms for intermediate results (e.g., cached embeddings, cached LLM prompts) in `code/utils/caching.py` to reduce redundant computation and ensure the total runtime stays within a reasonable constraint.
- [X] T045c [US3] Implement `code/utils/benchmark_validator.py` to parse `data/results/benchmark_log.json`, assert that the total runtime is < 6 hours, and fail the build with a clear error message if the threshold is exceeded. **Output**: A validation script that returns exit code 1 on failure.
- [X] T046 [P] Run `quickstart.md` validation and integration test suite. **Action**: Verify that the recruitment pipeline documentation (T043a/b/c) matches the Independent Test criteria in US-3.
- [X] T047 Security hardening: Ensure no PII in logs or output files
- [X] T048 Update `state/manifest.yaml` with final artifact checksums

---

## Phase 7: Deferred Validation (Optional)

**Purpose**: Additional validation tests that are not required for the MVP but are valuable for robustness.

- [ ] T049 [US1] **DEFERRED** - Implement `test_streaming_data_extraction` in `tests/unit/test_streaming_logic.py`. **Input**: A mock data source that yields 1000 items. **Assertion**: Assert that `extract_until` stops after a sufficient number of unique problem statements are found. and that the stream is closed. **Fixture**: Use a generator that yields items with a unique ID field. **Reason**: Optional validation test for MVP scope; can be added in Phase 7 if resources permit.
- [ ] T050 [US2] **DEFERRED** - Implement `test_pattern_similarity_threshold` in `tests/unit/test_pattern_mapping.py`. **Input**: A set of problem statements and pattern cards with known cosine similarities. **Assertion**: Assert that `retrieve_top_k_patterns` returns exactly 3 patterns only if their similarity score is ≥ 0.6, and returns fewer if the threshold is not met. **Fixture**: Use pre-computed embeddings with known similarity scores. **Reason**: Optional validation test for MVP scope; can be added in Phase 7 if resources permit.
- [ ] T051 [US3] **DEFERRED** - Implement `test_blind_evaluation_metadata_stripping` in `tests/unit/test_evaluation_loader.py`. **Input**: A set of proposals with generation metadata. **Assertion**: Assert that `load_expert_ratings` and the preceding preparation step strip all metadata (e.g., 'pattern-guided', 'baseline') from the proposals before they are presented to raters. **Fixture**: Use `data/results/generated_proposals.jsonl` and verify the stripped version. **Reason**: Optional validation test for MVP scope; can be added in Phase 7 if resources permit.

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
- **Pattern mapping (T020)** before proposal generation (T024)
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
- **Note**: T025 (Batch Processing) is NOT marked [P] as it is a hard prerequisite for T024 execution.

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
- **Critical**: The evaluation workflow (T030a/T030c-manual) MUST generate blinded templates for manual distribution and load pre-collected ratings, not automate recruitment.
- **Critical**: The two-group design (Pattern vs. Baseline) is strictly enforced per Spec FR-003; no random-pattern arm. T009b, T023 and T023b explicitly enforce this.
- **Critical**: The data acquisition task (T014) must explicitly state the dynamic extraction rule (extract until 50 unique statements or source exhausted) to handle large datasets without memory overflow, and must fail loudly if source is exhausted.
- **Critical**: The statistical analysis (T033-T035) must explicitly state the power analysis assumptions (n=50 pairs, 3 raters) and the effect size (Cohen's d of moderate magnitude) being targeted, as per the "Assumptions" section of the spec.
- **Critical**: The sensitivity analysis in T035a must preserve paired structure by removing entire pairs if one member is an outlier and re-run the test.
- **Critical**: T035d must flag the result if n drops below the power threshold, but MUST NOT block T035 or T037.
- **Critical**: T037a must verify the rhetorical constraint "associational, not causal" is present in the final report.
- **Critical**: T008a uses a configurable fallback model constant with a specific default (e.g., `all-MiniLM-L6-v2`) to ensure memory safety.
- **Critical**: T025 (Batch Processing) must be implemented before T021/T022/T024 to ensure memory constraints are met during generation.
- **Critical**: T030a-code (Recruitment API) must be implemented before T030a-manual (payload generation) to provide the wrapper.
- **Critical**: T024a (Power Analysis) must be implemented before T024 (Generation) to justify sample size. T024 must read 'n' from the JSON config generated by T024a. T024a is a strict sequential dependency.
- **Critical**: T014 (Sample) -> T014a (Validate) -> T016 (Write Final) is the correct order.
- **Critical**: T023 (Static Analysis) must run AFTER T024 to ensure the build fails if the design is wrong.
- **Critical**: T043a, T043b, T043c are required for US-3 verification and must include recruitment pipeline documentation.
- **Critical**: T046 explicitly verifies the recruitment pipeline documentation against the Independent Test criteria.
- **Critical**: The Plan's mention of 'random-pattern' is a violation of Spec FR-003 and is flagged for kickback. The tasks strictly enforce the two-group design.
- **Critical**: T018 must use `tracemalloc` to assert memory usage < 7 GB on the full dataset load.
- **Critical**: T024a must output `data/results/power_analysis_config.json` with the calculated 'n' to be consumed by T024.
- **Critical**: T035a must remove entire pairs if one member is an outlier to preserve the paired design of the statistical test.
- **Critical**: T037a must fail the build if the phrase "associational, not causal" is missing from the final report.
- **Critical**: T030a-execute must be marked as [Manual] and wait for human input to complete the recruitment step.
- **Critical**: T030c-manual must be marked as [Manual] and wait for human input to collect filled ratings.
- **Critical**: T030 must depend on T030c-manual (wait for file existence) to ensure ratings are available before loading.
- **Critical**: T035d must flag the result as 'underpowered' if n drops below a sufficient threshold for adequate statistical power, but must NOT block T035 or T037.
- **Critical**: T035 must apply multiple-comparison correction unconditionally, regardless of the power status flag from T035d.
- **Critical**: T032 must calculate Krippendorff's alpha and fail the pipeline if alpha < 0.6.
- **Critical**: T033 must perform a normality check on mean scores before selecting the statistical test.
- **Critical**: T034 must dynamically select between paired t-test and Wilcoxon signed-rank based on the normality check result.
- **Critical**: T036 must compute the mean difference in 'contextual alignment' scores and write the result to `data/results/validity_metrics.json`.
- **Critical**: T037 must generate the final report with p-values, effect sizes, and the phrase "associational, not causal".
- **Critical**: T038 must verify the report generation against the generated proposals and ratings data.
- **Critical**: T039 must test the statistical normality check logic.
- **Critical**: T040 must test the multiple-comparison correction logic with dummy p-values.
- **Critical**: T041 must test the IRR gate (Krippendorff's alpha ≥ 0.6).
- **Critical**: T042 must test the sensitivity analysis paired-difference removal logic.
- **Critical**: T043a must update README.md with CLI usage examples and include verification of the recruitment pipeline.
- **Critical**: T043b must generate API documentation for key modules and include recruitment pipeline documentation.
- **Critical**: T043c must update docs/ with data flow diagrams and include the recruitment flow.
- **Critical**: T045 must implement benchmarking and validation infrastructure to ensure total pipeline runtime ≤ 6 hours.
- **Critical**: T045a must profile runtime and memory usage for each phase and log results.
- **Critical**: T045b must implement caching mechanisms to reduce redundant computation.
- **Critical**: T045c must validate the benchmark log and fail the build if runtime exceeds 6 hours.
- **Critical**: T046 must run quickstart.md validation and verify the recruitment pipeline documentation.
- **Critical**: T047 must ensure no PII is present in logs or output files.
- **Critical**: T048 must update the state manifest with final artifact checksums.
- **Critical**: T018 must be implemented to test memory usage with the full dataset load.
- **Critical**: T024a must be implemented to perform statistical power analysis and output the calculated sample size.
- **Critical**: T035a must be implemented to perform sensitivity analysis and remove entire pairs if one member is an outlier.
- **Critical**: T035d must be implemented to flag the result as 'underpowered' if n drops below the power threshold.
- **Critical**: T037a must be implemented to verify the presence of the phrase "associational, not causal" in the final report.
- **Critical**: T030a-code must be implemented to provide a reusable API client wrapper for recruitment.
- **Critical**: T030a-manual must be implemented to generate the recruitment job payload and instructions.
- **Critical**: T030b-code must be implemented to automate ORCID and experience validation.
- **Critical**: T030a-execute must be implemented as a manual step to post the recruitment job and verify experts.
- **Critical**: T030c-manual must be implemented as a manual step to generate the ratings template and distribute it.
- **Critical**: T030 must be implemented to load expert ratings from the filled CSV.
- **Critical**: T032 must be implemented to calculate Krippendorff's alpha and fail the pipeline if alpha < 0.6.
- **Critical**: T033 must be implemented to perform a normality check on mean scores.
- **Critical**: T034 must be implemented to dynamically select the statistical test based on normality.
- **Critical**: T035 must be implemented to apply multiple-comparison correction.
- **Critical**: T036 must be implemented to calculate the validity improvement metric.
- **Critical**: T037 must be implemented to generate the final report.
- **Critical**: T038 must be implemented to verify the report generation.
- **Critical**: T039 must be implemented to test the statistical normality check logic.
- **Critical**: T040 must be implemented to test the multiple-comparison correction logic.
- **Critical**: T041 must be implemented to test the IRR gate.
- **Critical**: T042 must be implemented to test the sensitivity analysis logic.
- **Critical**: T043a must be implemented to update the README.
- **Critical**: T043b must be implemented to generate API documentation.
- **Critical**: T043c must be implemented to update the docs.
- **Critical**: T045 must be implemented to ensure total pipeline runtime ≤ 6 hours.
- **Critical**: T045a must be implemented to profile runtime and memory usage.
- **Critical**: T045b must be implemented to implement caching mechanisms.
- **Critical**: T045c must be implemented to validate the benchmark log.
- **Critical**: T046 must be implemented to run quickstart.md validation.
- **Critical**: T047 must be implemented to ensure no PII is present.
- **Critical**: T048 must be implemented to update the state manifest.
- [ ] T049 [US1] **DEFERRED** - Implement `test_streaming_data_extraction` in `tests/unit/test_streaming_logic.py`. **Input**: A mock data source that yields 1000 items. **Assertion**: Assert that `extract_until` stops exactly after 50 unique problem statements are found and that the stream is closed. **Fixture**: Use a generator that yields items with a unique ID field. **Reason**: Optional validation test for MVP scope; can be added in Phase 7 if resources permit.
- [ ] T050 [US2] **DEFERRED** - Implement `test_pattern_similarity_threshold` in `tests/unit/test_pattern_mapping.py`. **Input**: A set of problem statements and pattern cards with known cosine similarities. **Assertion**: Assert that `retrieve_top_k_patterns` returns exactly 3 patterns only if their similarity score is ≥ 0.6, and returns fewer if the threshold is not met. **Fixture**: Use pre-computed embeddings with known similarity scores. **Reason**: Optional validation test for MVP scope; can be added in Phase 7 if resources permit.
- [ ] T051 [US3] **DEFERRED** - Implement `test_blind_evaluation_metadata_stripping` in `tests/unit/test_evaluation_loader.py`. **Input**: A set of proposals with generation metadata. **Assertion**: Assert that `load_expert_ratings` and the preceding preparation step strip all metadata (e.g., 'pattern-guided', 'baseline') from the proposals before they are presented to raters. **Fixture**: Use `data/results/generated_proposals.jsonl` and verify the stripped version. **Reason**: Optional validation test for MVP scope; can be added in Phase 7 if resources permit.