# Tasks: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Input**: Design documents from `/specs/001-llmxive-crosslingual/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
- Paths shown below assume single project structure as defined in `plan.md`

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

- [X] T001 Create project structure per `plan.md` with exact file paths: `code/__init__.py`, `code/config.py`, `code/data_loader.py`, `code/model_analyzer.py`, `code/token_attribution.py`, `code/statistical_test.py`, `code/external_validation.py`, `code/validate_citations.py`, `code/main.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `tests/contract/.gitkeep`, `tests/unit/.gitkeep`, `contracts/.gitkeep`.
- [X] T002 Initialize a Python project with `requirements.txt` pinning exact versions: `torch==2.1.0`, `transformers==4.36.0`, `numpy==1.24.3`, `scipy==1.11.4`, `pandas==2.1.4`, `huggingface_hub==0.20.3`, `datasets==2.16.1`.
- [X] T003 [P] Configure linting (flake/black) and formatting tools by creating `pyproject.toml` with `[tool.black]` and `[tool.flake8]` sections and verifying setup with `black --check.` and `flake8.`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with paths, seeds, and hyperparameters (k=100, n_bootstrap=1000); ensure these constants are importable by `model_analyzer.py` and `statistical_test.py`.
- [X] T005 Implement `code/validate_citations.py` to parse markdown, extract URLs, and verify against a local manifest (Constitution Principle II).
- [X] T006 [P] Implement `code/data_loader.py` skeleton with functions for downloading, verifying checksums, and hashing datasets (Requires: T005).
- [X] T007 Create base `code/__init__.py` and error handling infrastructure.
- [X] T008 [P] Setup `tests/contract/test_schemas.py` skeleton for validating JSON output schemas, referencing `similarity_report.schema.yaml`, `permutation_result.schema.yaml`, `wals_validation.schema.yaml`, and `token_attribution.schema.yaml`. The skeleton must include imports for `jsonschema` and define a base test class for schema validation. (Requires: T005)
- [X] T008a [P] **Schema File Creation**: Create the schema files `contracts/similarity_report.schema.yaml`, `contracts/permutation_result.schema.yaml`, `contracts/wals_validation.schema.yaml`, and `contracts/token_attribution.schema.yaml` with exact definitions matching the expected JSON output structures. (Requires: T006)
- [X] T008b [P] **Skeleton Test File Creation**: Implement the skeleton test file `tests/contract/test_schemas.py` with specific test function stubs: `test_similarity_report_schema_valid`, `test_permutation_result_schema_valid`, `test_wals_validation_schema_valid`, `test_token_attribution_schema_valid`, ensuring they import and use the schema files from T008a. (Requires: T008a)
- [X] T037 [P] **Data Streaming Verification**: Add explicit logging and unit tests in `code/data_loader.py` to verify that `datasets.load_dataset(..., streaming=True)` is used for RedPajama and Common Crawl, ensuring no full dataset is loaded into RAM. **This task MUST be completed BEFORE T019a/b to catch violations early.** (Requires: T006)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Compare Edge Spectrum Subspaces (Priority: P1) 🎯 MVP

**Goal**: Compute the "edge spectrum" subspace (top-k singular vectors) of $W_U$ for Llama-3, Mistral, and BLOOM and calculate cosine similarity between subspaces to quantify geometric rotation.

**Independent Test**: The system runs SVD on three models and outputs a JSON report with non-zero cosine similarity scores between model pairs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `contracts/similarity_report.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_similarity_report_schema_valid` to validate the JSON output against the schema. (Requires: T008a, T008b)
- [X] T010 [P] [US1] Unit test for SVD extraction on a mock matrix in `tests/unit/test_math.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/model_analyzer.py` to load unembedding matrix $W_U$ from HuggingFace models (Llama-3, Mistral, BLOOM) using CPU-only float32 loading, with error handling for missing/corrupted weight files.
- [X] T011a [US1] **Vocabulary Mapping**: Implement a deterministic, verifiable vocabulary mapping layer in `code/model_analyzer.py` to align vocabulary IDs between Llama-3, Mistral, and BLOOM using a shared subword dictionary (intersection of tokenizer vocabularies). **Fallback**: Skip non-overlapping tokens with explicit logging to prevent silent failure in T013. (Requires: T011)
- [X] T012 [US1] Implement SVD extraction in `code/model_analyzer.py` to compute top-k (k=100) singular vectors on a representative subset (k=10, of vocab) for profiling purposes, handling numerical instability and rank-deficient matrices. (Requires: T011a)
- [X] T008a [US1] **MANDATORY PROFILING**: Implement `code/benchmark_runner.py` to perform a profiling run of SVD and permutation loops on the representative subset (k=10, vocab) to verify the computational time constraint (SC-005). **Failure Threshold**: Projected runtime > 5 hours must cause the build to fail. This task MUST produce a 'pass/fail' artifact that gates T012b. (Requires: T012)
- [X] T012b-PRECHECK [US1] **Full SVD Feasibility Check**: Implement a pre-check in `code/model_analyzer.py` to estimate memory usage and runtime for the *full* unembedding matrix SVD on the target runner (7GB RAM, 2 cores). **Logic**: Calculate theoretical memory footprint (matrix size * 4 bytes * 2). If memory > 6GB, reduce k to 50; if k=50 fails, skip the specific model and log 'SKIPPED'. This task MUST run BEFORE T012b. (Requires: T008a)
- [X] T038 [US1] **Numerical Stability Guard**: Implement a check in `code/model_analyzer.py` to detect and handle singular values < 1e-12 during SVD, logging a warning and masking those dimensions to prevent `NaN` propagation in cosine similarity calculations. (Requires: T012)
- [X] T012b [US1] **Full SVD Execution**: Implement the full SVD extraction in `code/model_analyzer.py` for the complete unembedding matrix, to be executed ONLY after T008a passes AND T012b-PRECHECK confirms feasibility. (Requires: T008a, T011a, T012b-PRECHECK, T038)
- [X] T013 [US1] Implement cosine similarity calculation in `code/model_analyzer.py` between subspace bases of English models vs. BLOOM. **Requirement**: This task MUST utilize the vocabulary mapping layer from T011a to ensure valid comparison across models with different vocabularies. (Requires: T011a, T012b)
- [X] T014a [US1] **SVD Pipeline Function**: Implement the SVD pipeline function in `code/model_analyzer.py` that orchestrates loading, SVD extraction, and similarity calculation. (Requires: T013)
- [X] T014b [US1] **Similarity Calculation Function**: Implement the specific cosine similarity calculation function in `code/model_analyzer.py` that outputs the similarity matrix. (Requires: T013)
- [X] T014c [US1] **Orchestrator Integration**: Implement `code/main.py` orchestrator to run the SVD and similarity pipeline, outputting `data/processed/similarity_matrix.json` with the exact schema: `{"pairs": [{"model_a": str, "model_b": str, "cosine_similarity": float}]}`. (Requires: T014a, T014b)
- [X] T015 [US1] Implement logic to calculate anisotropy deviation from the hypothesized null. **Reference**: The `reference_value` MUST be the within-language baseline similarity (Llama-3 vs. Mistral) computed in T013. Use the formula `deviation = |observed_similarity - reference_value|`, and compute the confidence interval using the bootstrap percentile method, outputting results to `data/processed/anisotropy_deviation.json`. (Requires: T013)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Cross-Lingual Token Shift (Priority: P2)

**Goal**: Identify tokens with highest logit weights in the edge spectrum subspace for each language and compare semantic categories to determine typological shift.

**Independent Test**: The system projects frequency distributions onto the subspace and outputs ranked token lists distinct from the English baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for `contracts/token_attribution.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_token_attribution_schema_valid` to validate the JSON output against the schema. (Requires: T008a, T008b)
- [X] T017 [P] [US2] Unit test for centroid calculation logic in `tests/unit/test_math.py`.

### Implementation for User Story 2

- [X] T018a [US2] **Data Acquisition (Common Crawl)**: Implement `code/data_loader.py` functions to download and checksum raw Common Crawl subsets (French/Chinese). **Requirement**: Output raw files to `data/raw/` (e.g., `data/raw/oscar_fr/raw.parquet`) and record SHA-256 hashes in `data/checksums.json`. Raise `FileNotFoundError` on fetch failure; NO synthetic fallbacks allowed. (Requires: T037)
- [X] T018b [US2] **Data Acquisition & Validation (RedPajama)**: Implement `code/data_loader.py` functions to download, checksum, AND validate (size check, completeness) the RedPajama dataset. **Requirement**: Output raw files to `data/raw/` and record SHA-256 hashes in `data/checksums.json`. Raise `FileNotFoundError` or `ValidationError` if validation fails; NO synthetic fallbacks allowed. (Requires: T037)
- [X] T019a [US2] Implement `code/data_loader.py` to compute frequency distributions from the streamed RedPajama (English) dataset and output `data/processed/frequency_distributions_en.json`. **Requirement**: Process data in chunks to maintain memory safety; explicitly log the total token count processed to verify sample representativeness. (Requires: T018b, T037)
- [X] T019b [US2] Implement `code/data_loader.py` to compute frequency distributions from the streamed Common Crawl (French/Chinese) datasets and output `data/processed/frequency_distributions_fr.json` and `data/processed/frequency_distributions_zh.json`. **Requirement**: Process data in chunks to maintain memory safety; explicitly log the total token count processed to verify sample representativeness. (Requires: T018a, T037)
- [X] T020 [US2] Implement `code/token_attribution.py` to compute the "mean embedding" vector by projecting the **external frequency distribution** (from T019a/T019b) onto the Moore-Penrose pseudo-inverse of $W_U$. **Requirement**: Use external corpus frequency lists as the sole source of truth per FR-005. This is the PRIMARY implementation of the mean embedding vector. (Requires: T019a, T019b, T012b)
- [X] T020c [US2] **Model Token Embeddings Projection (Comparative)**: Implement `code/token_attribution.py` to project **model token embeddings** (not frequency distributions) onto the Edge Spectrum subspace, as described in the plan.md Summary. This task implements a *comparative* analysis to validate the Plan's hypothesis against the FR-005 result. **Requirement**: Output a separate JSON file `data/processed/model_embedding_projection.json` for comparison. (Requires: T012b)
- [X] T021 [US2] **Token Ranking (Frequency)**: Implement token ranking logic in `code/token_attribution.py` to rank tokens based on the projection of the **external frequency-weighted mean embedding vector** (computed in T020) onto the Edge Spectrum subspace (from T012b). This explicitly implements the metric required by FR-005 and US-2. **Requirement**: Map ranked token IDs back to specific language vocabularies using the layer from T011a. (Requires: T020, T012b, T011a)
- [X] T021a [US2] **Token Ranking (Model Embeddings)**: Implement token ranking logic in `code/token_attribution.py` to rank tokens based on the projection of the **model token embeddings** (from T020c) onto the Edge Spectrum subspace (from T012b). This implements the plan's stated methodology as a secondary metric. **Requirement**: Map ranked token IDs back to specific language vocabularies using the layer from T011a. (Requires: T020c, T012b, T011a)
- [X] T022 [US2] Implement overlap ratio calculation between English and non-English top-ranked token lists (from T021), outputting results to `data/processed/token_overlap.json` with schema: `{"overlap_ratio": float, "top_n": int}`. (Requires: T021)
- [X] T023a [US2] **Token Attribution Pipeline Function**: Implement the token attribution pipeline function in `code/token_attribution.py` that orchestrates frequency distribution computation, mean embedding projection, and token ranking. (Requires: T021)
- [X] T023b [US2] **Orchestrator Integration**: Integrate `code/main.py` to execute the token attribution pipeline, outputting `data/processed/token_attribution_report.json`. (Requires: T023a, T022)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Note: T021a execution requires T012b completion)

---

## Phase 5: User Story 3 - Validate Statistical Significance of Shift (Priority: P3)

**Goal**: Perform a permutation test (multiple iterations) using a 'Within-Language Baseline' (Llama-3 vs. Mistral) as the empirical proxy for initialization variance to assess if the observed cross-lingual similarity is statistically significant.

**Independent Test**: The system runs a sufficient number of bootstrap iterations on CPU and outputs a p-value and significance flag.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for `contracts/permutation_result.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_permutation_result_schema_valid` to validate the JSON output against the schema. (Requires: T008a, T008b)
- [X] T025 [P] [US3] Unit test for permutation logic with fixed seed in `tests/unit/test_math.py`.

### Implementation for User Story 3

- [X] T026a-AMEND [US3] **Spec Amendment for FR-004**: Implement a formal amendment to the spec/plan to relax FR-004's "model-seed null distribution" requirement to accept the "Within-Language Baseline" (Llama-3 vs. Mistral) proxy. This task MUST document the deviation and provide justification based on the unavailability of seed-variant models. (Requires: T013)
- [X] T026 [US3] Implement `code/statistical_test.py` to generate the null distribution by bootstrapping the 'Within-Language Baseline' (Llama-3 vs. Mistral) similarity scores. (Requires: T013)
- [X] T026a [US3] **Model-Seed Null Distribution Proxy**: Implement the 'Within-Language Baseline' null distribution generation in `code/statistical_test.py` by computing similarity scores between Llama-3 and Mistral (same language, different model) to approximate initialization variance, replacing the 'weight perturbation' approach. **Deviation Note**: This task explicitly documents the deviation from FR-004's 'model-seed' requirement due to unavailability of seed-variant models, and includes a sub-step to validate the proxy's statistical equivalence against the spec's rigor. (Requires: T026a-AMEND, T013)
- [X] T027 [US3] Implement the permutation test loop (sufficient iterations for convergence) in `code/statistical_test.py`, ensuring CPU-only execution and < 6h runtime, using a fixed random seed from config. (Requires: T026a)
- [X] T028 [US3] Implement p-value calculation and "Statistically Significant Shift" flag generation in `code/statistical_test.py`. (Requires: T027)
- [X] T029a [US3] **WALS Configuration**: Implement `code/external_validation.py` to define the specific WALS feature set (phonological/morphological) and correlation method (Spearman's rank) as a configuration step, ensuring SC-004 is testable. (Requires: T013)
- [X] T029b [US3] **WALS Acquisition**: Implement `code/data_loader.py` to download, validate, and checksum the WALS dataset from the official source (e.g., WALS API or verified repository) to `data/raw/wals/`. **Requirement**: Record checksum in `data/checksums.json`. (Requires: T006)
- [X] T029-ALT [US3] **Alternative Validation Metric**: Implement an alternative validation metric (e.g., correlation with typological distance matrices from Ethnologue) in `code/external_validation.py` to be used if WALS data is unavailable. This task ensures SC-004 remains measurable even if the primary data source fails. (Requires: T029a)
- [X] T029 [US3] Implement `code/external_validation.py` to fetch WALS data from the verified artifact (via T029b) and compute Spearman's rank correlation coefficient between subspace orientation and WALS features. **Requires**: T029a to define the feature set and method. If WALS data is unavailable, use the alternative metric from T029-ALT. **NO graceful degradation** that bypasses validation; the task MUST output a valid metric or fail. (Requires: T013, T029a, T029b, T029-ALT, T028)
- [X] T030a [US3] **Statistical Test Function**: Implement the statistical test function in `code/statistical_test.py` that orchestrates null distribution generation, permutation loop, and p-value calculation. (Requires: T028)
- [X] T030b [US3] **External Validation Function**: Implement the external validation function in `code/external_validation.py` that orchestrates WALS acquisition, correlation calculation, and alternative metric fallback. (Requires: T029)
- [X] T030c [US3] **Orchestrator Integration**: Integrate `code/main.py` to run the statistical test and external validation, outputting `data/processed/permutation_result.json` and `data/processed/wals_validation.json` with exact schemas and alternative metric logic. (Requires: T030a, T030b)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Generate `data/checksums.json` including SHA-256 hashes for all files in `data/raw` and `code/` recursively.
- [X] T032 Code cleanup and refactoring of `code/main.py` orchestrator.
- [X] T033a [P] **SVD Optimization**: Optimize SVD computation in `code/model_analyzer.py` using `scipy.linalg.svd` with `full_matrices=False` to reduce memory usage and runtime. (Requires: T012b)
- [X] T033b [P] **Runtime Verification**: Verify that the optimized SVD and permutation loops complete within the < 6h runtime constraint on the target runner. (Requires: T033a)
- [X] T034a [P] **Unit Test for Missing Vocabulary Mapping**: Add unit test in `tests/unit/` for missing vocabulary mapping in `code/model_analyzer.py`. (Requires: T011a)
- [X] T034b [P] **Unit Test for Numerical Instability**: Add unit test in `tests/unit/` for numerical instability in SVD (e.g., singular values < 1e-12) in `code/model_analyzer.py`. (Requires: T038)
- [X] T035 Run `quickstart.md` validation by executing `python code/main.py --dry-run` and verifying exit code 0.
- [X] T036 Final verification of all JSON outputs against contract schemas.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for similarity_report.schema.yaml in tests/contract/test_schemas.py"
Task: "Unit test for SVD extraction on a mock matrix in tests/unit/test_math.py"

# Launch all models for User Story 1 together:
Task: "Implement code/model_analyzer.py to load unembedding matrix W_U..."
Task: "Implement SVD extraction in code/model_analyzer.py..."
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
- **Feasibility Note**: All tasks strictly adhere to CPU-only constraints (no CUDA, no 8-bit quantization, float32 SVD on sampled k=100 vectors). T012b-PRECHECK adds a mandatory feasibility check for the full matrix SVD with explicit fallback logic.
- **Data Integrity**: No synthetic data generation; all tasks require real datasets (Common Crawl, RedPajama, WALS) via `data_loader.py`. T018a, T018b, and T029b explicitly mandate downloading and checksumming raw files before streaming/processing. T018b adds explicit validation for RedPajama.
- **Methodology note**: T020 implements the 'frequency distribution' projection per FR-005 as the primary method. T020c implements the 'model token embeddings' projection as a secondary comparative analysis to validate the Plan's hypothesis. T026a-AMEND formally relaxes FR-004 to accept the 'Within-Language Baseline' proxy. T029-ALT ensures SC-004 remains measurable if WALS is unavailable. T011a handles vocabulary misalignment with a deterministic strategy. T029a defines WALS parameters for SC-004. T008a validates SC-005 early with specific thresholds. T033a/T033b optimize and verify runtime.
- **Cross-Phase Dependency**: T021 (US2) depends on T012b (US1). While US2 implementation can start after Foundational, T021 execution is blocked until T012b completes.
- **Streaming Enforcement**: T037 ensures that large datasets are processed via streaming to prevent OOM errors on the 7GB RAM runner, adhering to the "Stream real data" rule. T037 is now a prerequisite for T019a/b to catch violations early.
- **Numerical Safety**: T038 adds a guard against numerical instability in SVD, ensuring robustness for the statistical tests.