---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "ResearchStudio-Idea"

**Input**: Design documents from `/specs/001-llmxive-extension/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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
- [X] T008 [P] Implement error handling infrastructure that fails loudly on data fetch errors AND implements model fallback with logging. **Specifics**: If the primary embedding model fails to load due to memory constraints (detected by catching `MemoryError` or checking `psutil` memory usage > 6.5GB), the system MUST switch to a smaller, lighter model defined in `config.yaml` (key: `fallback_embedding_model`) and log the switch and reason. **Output**: Log the switch and the reason for the fallback. The fallback model MUST be pinned in `config.yaml` to ensure reproducibility.
- [X] T009 [P] Configure `data-sources.yaml` with URLs for ML, non-ML accepted, and non-ML rejected data.
- [X] T009a [P] Implement validation logic for `data-sources.yaml` to ensure required fields are present and URLs are valid formats.
- [X] T009b [P] Implement logic to identify and configure alternative open-access sources for *Nature Climate Change* and *Health Affairs* in `data-sources.yaml` if primary sources are paywalled.
- [X] T057 [P] Implement data-source health check script to validate all URLs in `data-sources.yaml` are reachable and return expected content types before the main pipeline runs.
- [X] T024b [P] Implement pre-study power analysis configuration generation in `code/utils/config.py` to calculate the required sample size (n=50) based on assumptions (effect size=0.5, alpha=0.05, power=0.80). **Constraint**: This task runs BEFORE T024-gen. **Input**: Read assumptions from `config.yaml`. **Output**: Write `data/results/power_analysis_config.json` containing `{"n": 50}`. **Verification**: Assert file exists and contains valid integer `n` before T024-gen completes. **Dependency**: Must complete before T024-gen.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Corpus Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest and prepare abstracts from ML and non-ML domains (Public Health, Climate Adaptation) to establish the baseline dataset.

**Independent Test**: The system can be tested by verifying that the dataset directory contains a representative set of processed JSON files with valid metadata fields and that the data fits within the available RAM constraint.

### Implementation for User Story 1

- [X] T053 [P] Implement `code/01_data_acquisition.py` logic to handle paywalled/non-accessible venues by explicitly checking HTTP status codes and content-type headers for paywall indicators (e.g., "Access Denied", "Login Required") before attempting to parse. **Constraint**: If a paywall is detected, the script MUST raise a `DataFetchError` with a specific message listing the blocked venue, rather than attempting to proceed with partial data or falling back to synthetic data. **Dependency**: Must run before T014 to ensure only accessible data enters the sampling phase.
- [X] T011 [US1] Implement `code/01_data_acquisition.py` to download ML and non-ML abstracts using endpoints defined in `data-sources.yaml`. **Specifics**: Use arXiv API with `cat:cs.LG` and `cat:q-bio.QM` for ML, and specific DOI lists/API endpoints from `data-sources.yaml` for *Nature Climate Change* and *Health Affairs*. **Algorithm**: Iterate through paginated API results, filtering for acceptance status, and accumulate rows until a balanced sample of ML, Non-ML Accepted, and Non-ML Rejected records are collected. If the API returns more than needed, truncate; if fewer, continue to next page. Stop when counts are met or source exhausted. **Output**: Write raw data to `data/raw/corpus_raw.jsonl`. Ensure query parameters explicitly filter for acceptance status where available. **Dependency**: Must depend on T009b to use fallback sources if primary sources fail.
- [X] T012 [US1] Implement strict validation function `validate_fetch_status()` in `code/01_data_acquisition.py` that raises `DataFetchError` on 403/404 or paywall detection. **Graceful Failure**: Must log the specific venue name (from `data-sources.yaml`) and halt the pipeline with a user-friendly error message indicating which venue failed. **Verification**: Unit test `test_fetch_fail_loudly` asserts exception raised with correct message. Do NOT generate synthetic data.
- [X] T013 [US1] Implement preprocessing pipeline in `code/01_data_acquisition.py` to normalize text and filter malformed entries.
- [X] T014 [US1] Implement streaming extraction with balance validation in `code/01_data_acquisition.py` via `extract_until(target=50, source='full_corpus', seed=42)`. **Algorithm**: Iterate through the full corpus (ML, Non-ML Accepted, Non-ML Rejected). Extract rows until a sufficient number of unique non-ML problem statements (unique by cryptographic hash of abstract text) are found. **Critical Rule**: Simultaneously track the counts of ML and Non-ML Rejected records. If the extraction reaches 50 non-ML statements but the ML or Non-ML Rejected counts deviate significantly from the target proportion (approximately equal proportions, e.g., within 10% of the target), raise `BalanceError` and halt. **Dependency**: Must complete before T016 before writing final processed file.
- [X] T015 [US1] Configure `logging` in `code/01_data_acquisition.py` to write `ERROR` level events to `logs/data_acquisition.log` with timestamp and URL context.
- [X] T016 [US1] Generate `data/processed/corpus.jsonl` with metadata (title, abstract, venue, acceptance_status, domain) from the validated sample.

### Tests for User Story 1

- [X] T017 [P] [US1] Contract test for data download validation in `tests/unit/test_data_parsing.py`
- [X] T018 [P] [US1] Implement `test_memory_usage_full_load` in `tests/unit/test_memory_usage_constraint.py`. **Input**: Full dataset loaded via `stream_and_sample` using REAL data. **Implementation**: Use Python's standard library `tracemalloc` to measure peak memory usage. **Assertion**: Assert `peak_memory_usage < 7000000000` (7 GB). **Output**: Write a deterministic log file `data/results/memory_usage_report.json` containing the peak memory value and pass/fail status. **Schema**: `{ "peak_memory_gb": float, "timestamp": str, "status": "pass" | "fail" }`. **Validation**: Assert file exists and matches schema before passing test. **Fixture**: Use a real dataset subset via streaming logic.
- [X] T019 [P] [US1] Implement `test_preprocessing_validation` in `tests/unit/test_preprocessing_validation.py`. **Input**: Raw corpus with empty abstracts. **Assertion**: Assert `preprocessing_pipeline` raises `ValueError` or filters out empty entries. **Fixture**: Use `data/raw/corpus_raw.jsonl` with injected malformed entries.
- [X] T049 [P] [US1] Implement `test_streaming_data_extraction` in `tests/unit/test_streaming_logic.py`. **Goal**: Verify that the streaming logic correctly processes chunks without loading the entire dataset into memory. **Fixture**: Use a large synthetic file or a subset of the the real corpus to simulate streaming.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pattern Mapping and Proposal Generation (Priority: P2)

**Goal**: Map non-ML problem statements to ML-derived ideation patterns and generate paired research proposals (pattern-guided vs baseline).

**Independent Test**: The system can be tested by running the generation pipeline on a small subset to verify logic, then scaling to 50 pairs within 4 hours on the CPU runner. **Crucial Validation**: The test MUST explicitly assert that the final output file `data/results/generated_proposals.jsonl` contains a balanced set of rows, split strictly into equal proportions of 'pattern-guided' and 'baseline' proposals, as mandated by FR-003 and US-2.

### Implementation for User Story 2

- [X] T020 [US2] Implement `retrieve_top_k_patterns()` in `code/pattern_mapping.py` using `sentence-transformers` (a quantized lightweight model variant) for CPU-tractable embeddings. **Logic**: Return a list of pattern IDs with cosine similarity ≥ `config.similarity_threshold` (read from `data-sources.yaml`). **Dependency**: Must complete before T024-gen.
- [X] T024-gen [US2] Implement proposal generation logic in `code/03_proposal_generation.py` to generate pattern-guided and baseline proposals. **Constraint**: Generate exactly one proposal per problem statement for BOTH groups, resulting in a balanced set of paired entries. **Logic**: Read 'n' from `config.py` (hardcoded to 50 per FR-003). Generate 'n' pattern-guided proposals (using top-3 patterns from T020) and 'n' baseline proposals (using generic prompts). **Note**: This task implements the **Two-Arm Study (Pattern-Guided vs Baseline)** as per FR-003, explicitly excluding any 'random-pattern' group. **Output Schema**: Write to unique deterministic path `data/results/generated_proposals.jsonl`. Each row MUST include `problem_id`, `group` (pattern-guided or baseline), `proposal_text`, **AND** `pattern_confidence_scores` (list of 3 cosine similarity scores for the top-3 patterns used). **Verification**: Assert `generated_proposals.jsonl` contains exactly 100 rows with 50 'pattern-guided' and 50 'baseline' tags before completing. **Dependency**: Depends on T020.
- [X] T024-val-sch [US2] Validate proposal schema in `code/03_proposal_generation.py`. **Action**: Verify that `generated_proposals.jsonl` contains only the allowed group tags ('pattern-guided', 'baseline') and required fields. **Constraint**: Raise `DesignViolationError` if any proposal is found that does not belong to the two allowed groups. **Dependency**: Depends on T024-gen.
- [X] T024-val-count [US2] Validate proposal row count in `code/03_proposal_generation.py`. **Action**: Verify that `generated_proposals.jsonl` contains a balanced number of rows distributed across the two groups. **Constraint**: Raise `DesignViolationError` if counts are mismatched. **Dependency**: Depends on T024-gen.
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

- [X] T059a [US3] Implement blind distribution script in `code/04_evaluation_loader.py`. **Action**: Generate blinded proposal pairs from `data/results/generated_proposals.jsonl` (stripping all generation metadata), format them for upload to an external platform (e.,g., Prolific). **Output**: Write a blinded CSV `data/results/blinded_batches.csv` ready for external upload. **Dependency**: Must run before T065-manual. **Constraint**: Do NOT use mock data for this step; this prepares real data for human evaluation. **Schema**: `proposal_id, problem_statement, domain, group, blinded_id, instructions`. **Verification**: Assert `blinded_batches.csv` contains no strings matching regex `pattern-guided|baseline` in `problem_statement` or `instructions` fields. **Blind Metadata Stripping**: Include explicit function `strip_generation_metadata()` that removes any field containing `pattern-guided`, `baseline`, `group`, or `confidence` from the proposal objects before CSV export. **Verification**: Add an assertion that the resulting `blinded_batches.csv` has 0 matches for the regex `pattern-guided|baseline` in any column. **Constraint**: This must be a hard block; if metadata is found, the script exits with code 1. **Blind Verification**: Include explicit function `verify_blind_metadata()` that runs before generating the blinded CSV to ensure no generation metadata leaks into the `problem_statement` or `instructions` fields. **Constraint**: The script must fail if any metadata string is detected, ensuring the integrity of the blind evaluation. **Regex**: `pattern-guided|baseline`. **Error**: Exit code 1 with message "Blind metadata leak detected".
- [X] T065-manual [US3] Implement manual expert recruitment coordination in `code/04_evaluation_loader.py`. **Action**: Define the process for recruiting verified domain experts (ORCID, ≥5 years experience) and distributing blinded proposals. **Constraint**: Must handle real data ingestion; mock data is only for local testing of the ingestion logic (T030-test). **Output**: Store raw responses in `data/results/ratings_raw.csv`. **Dependency**: Depends on T059a. **Implementation**: Define function `recruit_experts()` that validates ORCID via `api.orcid.org/v3.0` and checks `researcher-activities/summary/research-areas` for domain match. **Expert Domain Validation**: Enhance the ORCID check to explicitly parse the `researcher-activities` JSON and match against a predefined list of keywords (e.g., "Public Health", "Climate Change", "Policy"). **Constraint**: If no matching domain is found, the expert must be rejected from the recruitment list, and a log entry must be created explaining the rejection reason. **Dependency**: Must run after T059a. **Dependency**: Must depend on T030a (ORCID verification).
- [X] T065-trigger [US3] Implement hand-off trigger for real ratings ingestion in `code/04_evaluation_loader.py`. **Action**: Create a file-based check (e.g., `data/results/ratings_raw.csv` exists and has > 0 rows) that signals the automated pipeline can proceed to T065-real. **Dependency**: Must run after T065-manual completes. **Real Data Ingestion Trigger**: The trigger must not only check for file existence but also validate that `data/results/ratings_raw.csv` has a header row and at least 3 rows of data (one per expert minimum per pair). **Constraint**: If the file is empty or malformed, the pipeline must wait (polling) or exit with a specific "Waiting for Real Data" error, preventing T065-real from running on empty/mocked data.
- [X] T065-real [US3] Implement expert rating ingestion script in `code/04_evaluation_loader.py`. **Action**: Load real expert ratings from `data/results/ratings_raw.csv` (collected via T065-manual) into the analysis pipeline. **Constraint**: This task is the bridge between manual data collection and automated analysis. **Output**: Write `data/results/ratings_real.csv`. **Dependency**: Depends on T065-trigger. **Verification**: Assert file contains expected schema and row count.
- [X] T059b [US3] Implement mock data generator in `code/04_evaluation_loader.py`. **Action**: Generate deterministic, seeded mock ratings for testing the ingestion pipeline (T030-test) in isolation. **CONSTRAINT**: This is FOR TESTING ONLY. Do NOT generate mock ratings for the final analysis. Do NOT use this path in CI or production. **Output**: Write `data/results/ratings_filled.csv` with schema matching T030-test. **Dependency**: Must run before T030-test. **Outlier Sensitivity Analysis**: Explicitly link the mock data generation to the *outlier sensitivity analysis* verification required by the spec. The mock data MUST include extreme outliers to test the sensitivity analysis logic.
- [X] T030-test [US3] Implement `tests/unit/test_evaluation_loader.py` to load mock expert ratings from `data/results/ratings_filled.csv` (mock path for testing). **Constraint**: This task is a **CI-compliant unit test** that MUST run in the CI pipeline to verify the ingestion logic. **Dependency**: Depends on T059b. **Verification**: Define test fixture and assert loader handles mock data correctly without crashing. **Schema Verification**: Include explicit task to *verify* that the mock data generator produces data that is *structurally identical* to the real data format required by the reproducibility check. **Note**: This test ensures coverage of the ingestion pipeline with mock data as required by US-3.
- [X] T030-real [US3] Implement `code/04_evaluation_loader.py` to load real expert ratings from `data/results/ratings_real.csv` (real path). **Constraint**: This is the ONLY path for the final analysis pipeline. **Dependency**: Depends on T065-real.
- [X] T030a [US3] Implement ORCID verification in `code/04_evaluation_loader.py`. **Action**: For each expert ORCID provided, query the public ORCID API (`api.orcid.org/v3.0`) to confirm the ORCID exists and is valid. **Domain Check**: Parse the response JSON for `researcher-activities/summary/research-areas`. **Fallback**: If the API returns no keywords, log a warning but do NOT fail; accept the expert unless an explicit domain mismatch is found. **Timeout**: Raise `TimeoutError` after a configurable duration, log warning, and proceed. **Constraint**: Do NOT rely on local format validation only; the API call is mandatory. **Dependency**: Must run BEFORE T030-real (integrated into loading process) and T065-manual. **Test**: Use a specific test ORCID and mock response for unit tests.
- [X] T055 [US3] Implement `code/05_statistical_analysis.py` to enforce the IRR gate (Krippendorff's alpha ≥ 0.6). **Constraint**: If the calculated alpha is < 0.6, the pipeline MUST halt and raise `IRRGateFailError` with a detailed log of the inter-rater disagreement. This is a hard blocking constraint per Constitution Principle VII. **Dependency**: Must run on raw data before T033.
- [X] T033 [US3] Implement `code/05_statistical_analysis.py` to perform outlier removal based on IQR using a standard multiplier. **Constraint**: This step runs AFTER the IRR gate (T055) passes. **Dependency**: Depends on T055.
- [X] T057b [US3] Implement sensitivity analysis report in `code/05_statistical_analysis.py`. **Action**: Perform the statistical test logic (paired t-test or Wilcoxon) on the cleaned data **twice**: once with outliers removed (from T033) and once without. **Output**: Generate a markdown table comparing p-values and effect sizes side-by-side, plus a delta calculation column. **Constraint**: This task is a **HARD GATE** for T060; the pipeline cannot proceed to T060 without this report. The report MUST explicitly state whether outliers were present and how their removal impacted the p-value and effect size. **Dependency**: Depends on T033.
- [X] T031 [US3] Implement `code/05_statistical_analysis.py` to perform normality check on mean scores. **Verification**: Assert normality test returns p-value > 0.05 or < 0.05 to determine test type.
- [X] T060 [US3] Implement the primary statistical test in `code/05_statistical_analysis.py`. **Action**: Perform the paired t-test or Wilcoxon signed-rank test (selected based on T031) on the cleaned, outlier-removed data to calculate p-values and effect sizes. **Dependency**: Depends on T055, T033, and T057b (to use the final cleaned data and sensitivity results).
- [X] T034 [US3] Implement `code/05_statistical_analysis.py` to perform multiple-comparison correction (Bonferroni or Benjamini-Hochberg). **Dependency**: Depends on T060, T055.
- [X] T036 [US3] Implement `calculate_validity_improvement()` in `code/05_statistical_analysis.py` that computes the mean difference in 'contextual alignment' scores between pattern-guided and baseline groups and writes the result to `data/results/validity_metrics.json`. **Schema**: `{ "mean_diff": float, "p_value": float, "effect_size": float }`. **Dependency**: Requires real ratings from T065-real. **Output**: Write to `data/results/validity_metrics.json`.
- [X] T037 [US3] Verify report generation: Implement an assertion or parser check in `code/05_statistical_analysis.py` to confirm the phrase "associational, not causal" is present in `data/results/analysis_report.md`.
- [X] T035 [US3] Implement `code/05_statistical_analysis.py` to generate final report including p-values, effect sizes, and the phrase "associational, not causal". **Constraint**: The final report MUST explicitly include the side-by-side comparison of p-values and effect sizes from the sensitivity analysis (T057b) to demonstrate robustness. **Dependency**: Depends on T061 (Fabrication Guard) to ensure no synthetic data is included.
- [X] T054 [US3] Implement post-hoc power analysis in `code/05_statistical_analysis.py`. **Action**: Calculate the achieved statistical power (1 - β) given the observed effect size, sample size (n=50 pairs), and alpha (0.05). **Constraint**: If the calculated power is < 0.80, the analysis MUST log a warning and append a clear note to the final report stating that the results may be underpowered, but MUST NOT halt the pipeline. **Effect Size**: If the Wilcoxon test was selected, use rank-biserial correlation; if t-test, use Cohen's d via `statsmodels.stats.power.tt_solve_power`. **Output**: Write the power analysis results to `data/results/power_analysis_report.json`.
- [X] T056 [US3] (Optional) Implement correlation analysis between retrieval quality and expert scores. **Action**: Calculate Pearson or Spearman correlation coefficient between the pattern retrieval score (cosine similarity) and the expert 'contextual alignment' score. **Output**: Write the correlation coefficient and p-value to `data/results/correlation_metrics.json`. **Note**: This is **Exploratory Only**; SC-004 states retrieval score is not the validity metric.
- [X] T061 [P] Implement `code/utils/fabrication_guard.py` to scan all generated output files for synthetic data markers (e.g., "mock_", "synthetic", "random_seed") and block the pipeline if found. **Constraint**: This guard must run as a pre-commit hook and as a final CI step before report generation (T035). If synthetic markers are detected, the pipeline MUST halt with a `FabricationError`. **Dependency**: Must run before T035 and T052.
- [X] T067 [US3] Implement explicit "Outlier Handling" documentation and code path in `code/05_statistical_analysis.py`. **Action**: Define the IQR method (using a standard multiplier) clearly in code comments and config. Ensure the sensitivity analysis (T057b) explicitly compares the primary test results against the outlier-removed results. **Constraint**: The final report MUST include a section stating whether outliers were present and how their removal impacted the p-value and effect size. **Function**: `handle_outliers_iqr()`.
- [X] T068 [US3] Enhance the "Data Provenance" section (T063) to include the exact API query parameters and pagination tokens used for each data source. **Action**: Modify `code/01_data_acquisition.py` to log the full query string and response headers for every successful fetch to a `logs/data_provenance.jsonl` file. **Dependency**: This log must be included in the final report artifact to satisfy reproducibility requirements.
- [X] T069 [US3] Implement a "Power Analysis Sensitivity" check in `code/05_statistical_analysis.py`. **Action**: If the post-hoc power (T054) is < 0.80, the script must automatically calculate the minimum detectable effect size (MDES) for the given sample size (n=50) and alpha=0.05, and append this to the final report. **Constraint**: This ensures the report transparently communicates the limitations of the study if the power is insufficient. **Function**: `statsmodels.stats.power.tt_solve_power`.
- [X] T070 [US2] Add a "Pattern Retrieval Confidence" metric to the generation output. **Action**: In `code/03_proposal_generation.py`, record the cosine similarity scores of the top-3 patterns used for each proposal in `data/results/generated_proposals.jsonl`. **Dependency**: This allows for a more granular analysis of whether low-confidence pattern matches correlate with lower expert scores (exploratory analysis). **Note**: This is now handled by the updated T024-gen output schema.
- [X] T071 [US3] Implement a "Blind Verification" step in `code/04_evaluation_loader.py`. **Action**: Before generating the blinded CSV (T059a), run a script to ensure no generation metadata (e.g., "pattern-guided", "baseline") leaks into the `problem_statement` or `instructions` fields. **Constraint**: The script must fail if any metadata string is detected, ensuring the integrity of the blind evaluation. **Regex**: `pattern-guided|baseline`. **Error**: Exit code 1 with message "Blind metadata leak detected".
- [X] T072 [US3] (Merged into Phase 5) Implement explicit "Blind Metadata Stripping" logic in `code/04_evaluation_loader.py` for T059a. **Action**: Create a dedicated function `strip_generation_metadata()` that removes any field containing `pattern-guided`, `baseline`, `group`, or `confidence` from the proposal objects before CSV export. **Verification**: Add an assertion that the resulting `blinded_batches.csv` has 0 matches for the regex `pattern-guided|baseline` in any column. **Constraint**: This must be a hard block; if metadata is found, the script exits with code 1.
- [X] T073 [US3] (Merged into Phase 5) Implement robust "Real Data Ingestion" trigger logic in `code/04_evaluation_loader.py` for T065-trigger. **Action**: The trigger must not only check for file existence but also validate that `data/results/ratings_raw.csv` has a header row and at least 3 rows of data (one per expert minimum per pair). **Constraint**: If the file is empty or malformed, the pipeline must wait (polling) or exit with a specific "Waiting for Real Data" error, preventing T065-real from running on empty/mocked data.
- [X] T074 [US3] (Merged into Phase 5) Implement "Expert Domain Validation" in `code/04_evaluation_loader.py` for T065-auto. **Action**: Enhance the ORCID check to explicitly parse the `research-areas` JSON and match against a predefined list of keywords (e.g., "Public Health", "Climate Change", "Policy"). **Constraint**: If no matching domain is found, the expert must be rejected from the recruitment list, and a log entry must be created explaining the rejection reason.

### Tests for User Story 3

- [X] T040 [P] [US3] Test statistical normality check logic in `tests/unit/test_statistical_normality_check.py`
- [X] T042 [P] [US3] Implement `test_multiple_comparison_correction` in `tests/unit/test_multiple_comparison_correction.py`.
- [X] T043 [P] [US3] Test Inter-Rater Reliability (IRR) gate (Krippendorff's alpha ≥ 0.6) in `tests/unit/test_inter_rater_reliability_gate.py`
- [X] T044 [P] [US3] Test sensitivity analysis paired-difference removal logic in `tests/unit/test_sensitivity_analysis.py`
- [X] T030-test-cov [P] [US3] Implement `test_mock_real_schema_equivalence` in `tests/unit/test_evaluation_loader.py`. **Goal**: Verify that the mock data generator (T059b) produces data structurally identical to the real data format required by reproducibility checks. **Constraint**: This test MUST run in CI to ensure mock data can safely replace real data for unit testing without violating schema constraints. **Dependency**: Depends on T059b and T030-test.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Update `README.md` with CLI usage examples and installation instructions.
- [X] T047 [P] Generate API documentation for `code/01_data_acquisition.py`, `code/02_pattern_mapping.py`, and `code/05_statistical_analysis.py` using Sphinx or MkDocs.
- [X] T048 [P] Update `docs/` with data flow diagrams and architecture overview.
- [X] T049 [P] Refactor T014 to use generator-based streaming to reduce peak memory usage by at least 20%.
- [X] T050 [P] Run `quickstart.md` validation and integration test suite.
- [X] T051 Security hardening: Ensure no PII in logs or output files
- [X] T052 Update `state/manifest.yaml` with final artifact checksums **Dependency**: Must run after T061 (Fabrication Guard) to ensure manifest integrity.

---

## Phase 8: Review-Driven Revisions (Critical Fixes)

**Goal**: Address specific gaps identified during the initial analysis of the feature specification and plan, ensuring robustness against data access failures and statistical power constraints.

- [X] T066 [P] Update `plan.md` summary to remove the reference to a "random-pattern" control group, aligning the plan with the Spec's two-arm study design (pattern-guided vs baseline).

---

## Phase 9: Execution Validation & Safety (New)

**Goal**: Ensure the pipeline adheres to the "Real Data Only" constitution and handles edge cases without fabrication.

- [X] T062 [US1] Add explicit unit test `test_no_synthetic_fallback` in `tests/unit/test_data_acquisition.py` that asserts the `DataFetchError` is raised when a simulated network timeout occurs, verifying that NO fallback to `generate_synthetic_*` is triggered.
- [X] T064 [P] Add a `--dry-run` flag to `run_pipeline.sh` that executes the data source health check (T057) and power analysis (T024b) without fetching data or generating proposals, to allow quick validation of configuration.

---

## Phase 10: Review-Driven Revisions (Statistical Rigor & Reproducibility)

**Goal**: Address specific concerns regarding statistical power, outlier handling, and data provenance identified in the analysis phase.

- [X] T067 [US3] (Merged into Phase 5) Implement explicit "Outlier Handling" documentation and code path in `code/05_statistical_analysis.py`.
- [X] T068 [US3] (Merged into Phase 5) Enhance the "Data Provenance" section (T063) to include the exact API query parameters and pagination tokens used for each data source.
- [X] T069 [US3] (Merged into Phase 5) Implement a "Power Analysis Sensitivity" check in `code/05_statistical_analysis.py`.
- [X] T070 [US2] (Merged into Phase 5) Add a "Pattern Retrieval Confidence" metric to the generation output.
- [X] T071 [US3] (Merged into Phase 5) Implement a "Blind Verification" step in `code/04_evaluation_loader.py`.