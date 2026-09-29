---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "ResearchStudio-Idea"

**Input**: Design documents from `/specs/001-llmxive-extension/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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
- [X] T008 [P] Implement error handling infrastructure that fails loudly on data fetch errors AND implements model fallback with logging. **Specifics**: If the primary embedding model fails to load due to memory constraints, the system MUST switch to a smaller, lighter model defined in the configuration file (not hardcoded) and log the switch and reason. **Output**: Log the switch and the reason for the fallback.
- [X] T009 [P] Configure `data-sources.yaml` with URLs for ML, non-ML accepted, and non-ML rejected data.
- [X] T009a [P] Implement validation logic for `data-sources.yaml` to ensure required fields are present and URLs are valid formats.
- [X] T057 Implement data-source health check script to validate all URLs in `data-sources.yaml` are reachable and return expected content types before the main pipeline runs.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Corpus Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest and prepare abstracts from ML and non-ML domains (Public Health, Climate Adaptation) to establish the baseline dataset.

**Independent Test**: The system can be tested by verifying that the dataset directory contains a representative set of processed JSON files with valid metadata fields and that the data fits within the available RAM constraint.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_data_acquisition.py` to download ML and non-ML abstracts using endpoints defined in `data-sources.yaml`. **Specifics**: Use arXiv API with `cat:cs.LG` and `cat:q-bio.QM` for ML, and specific DOI lists/API endpoints from `data-sources.yaml` for *Nature Climate Change* and *Health Affairs*. **Algorithm**: Iterate through paginated API results, filtering for acceptance status, and accumulate rows until a balanced sample of ML, Non-ML Accepted, and Non-ML Rejected records are collected. If the API returns more than needed, truncate; if fewer, continue to next page. Stop when counts are met or source exhausted. **Output**: Write raw data to `data/raw/corpus_raw.jsonl`. Ensure query parameters explicitly filter for acceptance status where available.
- [X] T012 [US1] Implement strict validation function `validate_fetch_status()` in `code/01_data_acquisition.py` that raises `DataFetchError` on 403/404 or paywall detection. **Graceful Failure**: Must log the specific venue name (from `data-sources.yaml`) and halt the pipeline with a user-friendly error message indicating which venue failed. **Verification**: Unit test `test_fetch_fail_loudly` asserts exception raised with correct message. Do NOT generate synthetic data.
- [X] T013 [US1] Implement preprocessing pipeline in `code/01_data_acquisition.py` to normalize text and filter malformed entries.
- [X] T014 [US1] Implement streaming extraction with balance validation in `code/01_data_acquisition.py` via `extract_until(target=50, source='full_corpus', seed=42)`. **Algorithm**: Iterate through the full corpus (ML, Non-ML Accepted, Non-ML Rejected). Extract rows until a sufficient number of unique non-ML problem statements (unique by SHA-256 hash of abstract text) are found. **Critical Rule**: Simultaneously track the counts of ML and Non-ML Rejected records. If the extraction reaches 50 non-ML statements but the ML or Non-ML Rejected counts deviate by >5% from the target proportion (approx. 1:1:1 ratio), raise `BalanceError` and halt. **Dependency**: Must complete before T016 before writing final processed file.
- [X] T015 [US1] Configure `logging` in `code/01_data_acquisition.py` to write `ERROR` level events to `logs/data_acquisition.log` with timestamp and URL context.
- [X] T016 [US1] Generate `data/processed/corpus.jsonl` with metadata (title, abstract, venue, acceptance_status, domain) from the validated sample.

### Tests for User Story 1

- [X] T017 [P] [US1] Contract test for data download validation in `tests/unit/test_data_parsing.py`
- [X] T018 [P] [US1] Implement `test_memory_usage_full_load` in `tests/unit/test_memory_usage_constraint.py`. **Input**: Full dataset loaded via `stream_and_sample` using REAL data. **Implementation**: Use Python's standard library `tracemalloc` to measure peak memory usage. **Assertion**: Assert `peak_memory_usage < 7000000000` (7 GB). **Output**: Write a deterministic log file `data/results/memory_usage_report.json` containing the peak memory value and pass/fail status. **Schema**: `{ "peak_memory_gb": float, "timestamp": str, "status": "pass" | "fail" }`. **Validation**: Assert file exists and matches schema before passing test. **Fixture**: Use a real dataset subset via streaming logic.
- [X] T019 [P] [US1] Implement `test_preprocessing_validation` in `tests/unit/test_preprocessing_validation.py`. **Input**: Raw corpus with empty abstracts. **Assertion**: Assert `preprocessing_pipeline` raises `ValueError` or filters out empty entries. **Fixture**: Use `data/raw/corpus_raw.jsonl` with injected malformed entries.
- [X] T049 [P] [US1] Implement `test_streaming_data_extraction` in `tests/unit/test_streaming_logic.py`. **Goal**: Verify that the streaming logic correctly processes chunks without loading the entire dataset into memory. **Fixture**: Use a large synthetic file or a subset of the real corpus to simulate streaming.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pattern Mapping and Proposal Generation (Priority: P2)

**Goal**: Map non-ML problem statements to ML-derived ideation patterns and generate paired research proposals (pattern-guided vs. baseline).

**Independent Test**: The system can be tested by running the generation pipeline on a small subset to verify logic, then scaling to 50 pairs within 4 hours on the CPU runner.

### Implementation for User Story 2

- [X] T020 [US2] Implement `retrieve_top_k_patterns()` in `code/02_pattern_mapping.py` using `sentence-transformers` (`all-MiniLM-L6-v2` quantized) for CPU-tractable embeddings. **Logic**: Return a list of pattern IDs with cosine similarity ≥ 0.6. **Dependency**: Must complete before T024.
- [X] T021 [US2] Implement `code/03_proposal_generation.py` to generate pattern-guided proposals using injected pattern cards. **Constraint**: Generate exactly one proposal per problem statement. **Note**: Strictly adhere to the two-group design (pattern-guided vs baseline) as per FR-003. **Output**: Intermediate proposals written to a temporary file for validation.
- [X] T022 [US2] Implement `code/03_proposal_generation.py` to generate baseline proposals using generic prompts. **Constraint**: Generate exactly one proposal per problem statement. **Note**: Strictly adhere to the two-group design (pattern-guided vs baseline) as per FR-003. **Output**: Intermediate proposals written to a temporary file for validation.
- [X] T023 [US2] Implement `code/02_pattern_validation.py` to validate the generated proposals *after* generation to ensure ONLY pattern-guided and baseline proposals are present. **Constraint**: Raise `DesignViolationError` if any proposal is found that does not belong to the two allowed groups.
- [X] T024b [US2] Implement power analysis configuration generation in `code/05_statistical_analysis.py` to calculate required sample size 'n' and write it to `data/results/power_analysis_config.json`. **Dependency**: Must run before T024.
- [X] T024 [US2] Implement the full generation loop in `code/03_proposal_generation.py` to produce a set of pairs (pattern-guided + baseline) and save to `data/results/generated_proposals.jsonl` with generation metadata stripped for evaluation. **Dependency**: Depends on T020, T023, T024b. **Logic**: Read target sample size 'n' from `data/results/power_analysis_config.json` (written by T024b) and generate n pairs. **Verification**: Assert `data/results/power_analysis_config.json` exists before reading 'n'. **Note**: This task merges generation and saving logic to ensure validation precedes save.
- [X] T025 [US2] Implement batch processing in `code/03_proposal_generation.py` using a generator-based batch loader that yields batches of pairs to stay within 7 GB RAM limits.

### Tests for User Story 2

- [X] T029 [P] [US2] Test proposal generation logic (strict two-group pairing) in `tests/unit/test_proposal_generation_logic.py`
- [X] T050 [P] [US2] Implement `test_pattern_similarity_threshold` in `tests/unit/test_pattern_mapping.py`. **Goal**: Verify that the similarity threshold logic correctly filters patterns below the configured threshold and includes those above. **Fixture**: Use a set of pre-calculated embeddings.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Expert Evaluation and Statistical Analysis (Priority: P3)

**Goal**: Aggregate expert ratings and perform statistical tests to determine if pattern-guided proposals differ significantly from baseline.

**Independent Test**: The system can be tested by feeding pre-defined dummy ratings to verify statistical logic and by verifying the loader script successfully ingests pre-collected expert ratings with blinded metadata.

### Implementation for User Story 3

- [X] T059 [US3] Implement expert evaluation workflow in `code/04_evaluation_loader.py` and `code/05_statistical_analysis.py`. **Action**: Generate blinded proposal pairs from `data/results/generated_proposals.jsonl` (stripping all generation metadata), distribute them to a mock or crowd interface for a small cohort of experts, and collect the raw ratings into `data/results/ratings_filled.csv`. **Constraint**: Ensure the output CSV matches the expected schema for T030. **Dependency**: Must run before T030.
- [X] T030 [US3] Implement `code/04_evaluation_loader.py` to load expert ratings from `data/results/ratings_filled.csv` (blinded, ORCID verified). **Dependency**: Depends on T059.
- [X] T030a [US3] Implement ORCID verification in `code/04_evaluation_loader.py`. **Action**: For each expert ORCID provided, query the public ORCID API to confirm the ORCID exists and is valid. **Domain Check**: Parse the response JSON for 'researcher-activities' or 'keywords' to verify the expert's domain affiliation matches 'public health' or 'climate adaptation'. **Failure**: Raise `VerificationError` if ORCID is invalid, not found, or domain affiliation does not match. **Constraint**: Do NOT rely on local format validation only; the API call is mandatory. **Dependency**: Must run AFTER T030.
- [X] T031 [US3] Implement `code/05_statistical_analysis.py` to perform normality check on mean scores.
- [X] T033 [US3] Implement `code/05_statistical_analysis.py` to perform outlier removal based on IQR.
- [X] T060 [US3] Implement the primary statistical test in `code/05_statistical_analysis.py`. **Action**: Perform the paired t-test or Wilcoxon signed-rank test (selected based on T031) on the cleaned, outlier-removed data to calculate p-values and effect sizes. **Dependency**: Depends on T033.
- [X] T034 [US3] Implement `code/05_statistical_analysis.py` to perform multiple-comparison correction (Bonferroni or Benjamini-Hochberg). **Dependency**: Depends on T060.
- [X] T035 [US3] Implement `code/05_statistical_analysis.py` to generate final report including p-values, effect sizes, and the phrase "associational, not causal".
- [X] T036 [US3] Implement `calculate_validity_improvement()` in `code/05_statistical_analysis.py` that computes the mean difference in 'contextual alignment' scores between groups and writes the result to `data/results/validity_metrics.json`.
- [X] T037 [US3] Verify report generation: Implement an assertion or parser check in `code/05_statistical_analysis.py` to confirm the phrase "associational, not causal" is present in `data/results/analysis_report.md`.
- [X] T038 [US3] Verify report generation against `data/results/generated_proposals.jsonl` and `data/results/ratings.csv`.
- [X] T041 [US3] Implement Inter-Rater Reliability (IRR) gate (Krippendorff's alpha ≥ 0.6) in tests.
- [X] T056 [US3] Implement correlation analysis between retrieval quality and expert scores.
- [X] T054 [US3] Implement post-hoc power analysis in `code/05_statistical_analysis.py`. **Action**: Calculate the achieved statistical power (1 - β) given the observed effect size, sample size (n=50 pairs), and alpha (0.05). **Constraint**: If the calculated power is < 0.80, the analysis MUST log a warning and append a clear note to the final report stating that the results may be underpowered, but MUST NOT halt the pipeline. **Output**: Write the power analysis results to `data/results/power_analysis_report.json`.
- [X] T055 [US3] Implement `code/05_statistical_analysis.py` to enforce the IRR gate (Krippendorff's alpha ≥ 0.6) as a hard stop. **Constraint**: If the calculated alpha is < 0.6, the analysis MUST halt and raise an `IRRGateFailError`, preventing the generation of the final report until expert re-rating or data cleaning is performed. **Dependency**: Must run before T034 (multiple-comparison correction) to ensure only reliable data is tested.
- [X] T057 [US3] Implement a sensitivity analysis report in `code/05_statistical_analysis.py` comparing results with and without outlier removal.

### Tests for User Story 3

- [X] T040 [P] [US3] Test statistical normality check logic in `tests/unit/test_statistical_normality_check.py`
- [X] T042 [P] [US3] Implement `test_multiple_comparison_correction` in `tests/unit/test_multiple_comparison_correction.py`.
- [X] T043 [P] [US3] Test Inter-Rater Reliability (IRR) gate (Krippendorff's alpha ≥ 0.6) in `tests/unit/test_inter_rater_reliability_gate.py`
- [X] T044 [P] [US3] Test sensitivity analysis paired-difference removal logic in `tests/unit/test_sensitivity_analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Update `README.md` with CLI usage examples and installation instructions.
- [X] T047 [P] Generate API documentation for `code/01_data_acquisition.py`, `code/02_pattern_mapping.py`, and `code/05_statistical_analysis.py` using Sphinx or MkDocs.
- [X] T048 [P] Update `docs/` with data flow diagrams and architecture overview.
- [X] T049 Code cleanup and refactoring for memory efficiency
- [X] T050 [P] Run `quickstart.md` validation and integration test suite.
- [X] T051 Security hardening: Ensure no PII in logs or output files
- [X] T052 Update `state/manifest.yaml` with final artifact checksums

---

## Phase 8: Review-Driven Revisions (Critical Fixes)

**Goal**: Address specific gaps identified during the initial analysis of the feature specification and plan, ensuring robustness against data access failures and statistical power constraints.

- [X] T053 [P] Implement `code/01_data_acquisition.py` logic to handle paywalled/non-accessible venues by explicitly checking HTTP status codes and content-type headers for paywall indicators (e.g., "Access Denied", "Login Required") before attempting to parse. **Constraint**: If a paywall is detected, the script MUST raise a `DataFetchError` with a specific message listing the blocked venue, rather than attempting to proceed with partial data or falling back to synthetic data. **Dependency**: Must run before T014 to ensure only accessible data enters the sampling phase.
- [X] T058 [P] Implement a "data-source health check" script `code/utils/health_check.py` that validates all URLs in `data-sources.yaml` are reachable and return expected content types before the main pipeline runs.