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
- [X] T003 [P] Configure linting (flake/black) and formatting tools by creating `pyproject.toml` with `[tool.black]` and `[tool.flake8]` sections and verifying setup with `black --check.` and `flake8.`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with paths, seeds, and hyperparameters (k=100, n_bootstrap=1000); ensure these constants are importable by `model_analyzer.py` and `statistical_test.py`.
- [X] T005 Implement `code/validate_citations.py` to parse markdown, extract URLs, and verify against a local manifest (Constitution Principle II).
- [X] T006 [P] Implement `code/data_loader.py` skeleton with functions for downloading, verifying checksums, and hashing datasets (Requires: T005).
- [X] T007 Create base `code/__init__.py` and error handling infrastructure.
- [X] T008 [P] Setup `tests/contract/test_schemas.py` skeleton for validating JSON output schemas, referencing `similarity_matrix.schema.yaml`, `permutation_result.schema.yaml`, `wals_validation.schema.yaml`, `token_attribution.schema.yaml`, and `frequency_list.schema.yaml`. The skeleton must include imports for `jsonschema` and define a base test class for schema validation. (Requires: T005)
- [X] T008a-1 [P] **Schema Creation: similarity_matrix**: Create `contracts/similarity_matrix.schema.yaml` with definition: `{"pairs": [{"model_a": str, "model_b": str, "cosine_similarity": float}]}`. (Requires: T005)
- [X] T008a-2 [P] **Schema Creation: permutation_result**: Create `contracts/permutation_result.schema.yaml` with definition: `{"observed_similarity": float, "null_distribution": [float], "p_value": float, "significant": bool}`. (Requires: T005)
- [X] T008a-3 [P] **Schema Creation: wals_validation**: Create `contracts/wals_validation.schema.yaml` with definition: `{"language_pairs": [{"lang_a": str, "lang_b": str}], "shift_vector": [float], "wals_diff": [float], "correlation_r": float, "p_value": float}`. (Requires: T005)
- [X] T008a-4 [P] **Schema Creation: token_attribution**: Create `contracts/token_attribution.schema.yaml` with definition: `{"model": str, "language": str, "top_tokens": [{"token_id": int, "logit_weight": float, "token_str": str}]}`. (Requires: T005)
- [X] T008a-5 [P] **Schema Creation: frequency_list**: Create `contracts/frequency_list.schema.yaml` with definition: `{"language": str, "total_tokens": int, "unique_tokens": int, "distribution": {"token_id": float}}`. (Requires: T005)
- [X] T008a-6 [P] **Schema Creation: similarity_report**: Create `contracts/similarity_report.schema.yaml` with definition: `{"summary": {"mean_similarity": float, "std_dev": float}, "pairs": [...]}`. (Requires: T005)
- [X] T008a-7 [P] **Schema Creation: spectrum_output**: Create `contracts/spectrum_output.schema.yaml` with definition: `{"model": str, "singular_values": [float], "vectors": [[float]]}`. (Requires: T005)
- [X] T008a-8 [P] **Schema Creation: statistical_results**: Create `contracts/statistical_results.schema.yaml` with definition: `{"bootstrap_iterations": int, "convergence_status": str, "p_value": float}`. (Requires: T005)
- [X] T008a-9 [P] **Schema Creation: permutation_results**: Create `contracts/permutation_results.schema.yaml` with definition: `{"null_distribution": [float], "observed": float, "threshold": float}`. (Requires: T005)
- [X] T008b **Skeleton Test File Creation**: Implement the skeleton test file `tests/contract/test_schemas.py` with specific test function stubs: `test_similarity_matrix_schema_valid`, `test_permutation_result_schema_valid`, `test_wals_validation_schema_valid`, `test_token_attribution_schema_valid`, `test_frequency_list_schema_valid`, ensuring they import and use the schema files from T008a-1 through T008a-9. (Requires: T008a-1, T008a-2, T008a-3, T008a-4, T008a-5, T008a-6, T008a-7, T008a-8, T008a-9)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Compare Edge Spectrum Subspaces (Priority: P1) 🎯 MVP

**Goal**: Compute the "edge spectrum" subspace (top-k singular vectors) of $W_U$ for Llama-3, Mistral, and BLOOM and calculate cosine similarity between subspaces to quantify geometric rotation.

**Independent Test**: The system runs SVD on three models and outputs a JSON report with non-zero cosine similarity scores between model pairs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `contracts/similarity_matrix.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_similarity_matrix_schema_valid` to validate the JSON output against the schema. (Requires: T008a-1, T008b)
- [X] T010 [P] [US1] Unit test for SVD extraction on a mock matrix in `tests/unit/test_math.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/model_analyzer.py` to load unembedding matrix $W_U$ from HuggingFace models (Llama-3, Mistral, BLOOM) using CPU-only float32 loading, with error handling for missing/corrupted weight files.
- [X] T044 [US1] **Vocabulary Mapping**: Implement a deterministic, verifiable vocabulary mapping layer in `code/model_analyzer.py` to align vocabulary IDs between Llama-3, Mistral, and BLOOM using a shared subword dictionary (intersection of tokenizer vocabularies). **Output**: `data/processed/vocab_status.json` containing `intersection_size` and `status` ('OK' or 'INSUFFICIENT_OVERLAP'). (Requires: T011)
- [X] T044b [US1] **Vocabulary Alignment Fallback**: Implement a fallback alignment strategy in `code/model_analyzer.py` using a translation map or `fast_align` if T044 reports 'INSUFFICIENT_OVERLAP'. **Output**: `data/processed/aligned_subspace_matrix.json` with the same schema as the primary path, ensuring compatibility with T013. **Trigger**: This task is a conditional sibling of T044c, triggered if T044 status is 'INSUFFICIENT_OVERLAP'. (Requires: T044)
- [X] T044c [US1] **Translation Map Alignment**: Implement a translation-map-based alignment (using `fast_align` or a pre-trained matrix) in `code/model_analyzer.py` to align vocabularies when shared intersection is insufficient. **Output**: `data/processed/aligned_subspace_matrix.json` with the same schema as the primary path. **Trigger**: This task is a conditional sibling of T044b, triggered if T044 status is 'INSUFFICIENT_OVERLAP'. (Requires: T044)
- [X] T012 [US1] Implement SVD extraction in `code/model_analyzer.py` to compute **top-k (k=100) singular vectors of the FULL unembedding matrix (W_U)**. **Requirement**: If the full matrix exceeds RAM (detected by T012b-PRECHECK), this task MUST fall back to T012c (Randomized SVD) and explicitly log the result as 'approximate' with an estimated error margin. **Output**: `data/processed/svd_result.json`. (Requires: T044, T044b, T044c)
- [X] T012b-PRECHECK [US1] **Full SVD Feasibility Check**: Implement a pre-check in `code/model_analyzer.py` to estimate memory usage and runtime for the *full* unembedding matrix SVD on the target runner (constrained RAM, limited cores). **Logic**: Calculate theoretical memory footprint (matrix size * 4 bytes * 2). If memory > 6GB for ANY of the three models, mark that model as 'SKIPPED' in the output; otherwise 'OK'. **Output**: `data/processed/model_status.json` containing a list of models with status ('OK' or 'SKIPPED') and a boolean `gpu_required` set to true if ANY model is SKIPPED. **Constraint**: If `gpu_required` is true, the pipeline must route to the external GPU strategy (T069) rather than randomized SVD. (Requires: T008a-1, T044, T011, T004)
- [X] T012c [US1] **Randomized SVD Fallback**: Implement a randomized SVD (or subsampling) strategy in `code/model_analyzer.py` to extract the top-k singular vectors for models where T012b-PRECHECK reports 'SKIPPED' AND `gpu_required` is FALSE. **Requirement**: This task MUST produce a valid subspace artifact compatible with T013 and MUST be labeled as 'approximate' in the output. (Requires: T012b-PRECHECK)
- [X] T038 [US1] **Numerical Stability Guard**: Implement a check in `code/model_analyzer.py` to detect and handle singular values < 1e-12 during SVD, logging a warning and masking those dimensions to prevent `NaN` propagation in cosine similarity calculations. (Requires: T012)
- [X] T012-ORCH [US1] **SVD Result Unification**: Implement an orchestration function in `code/model_analyzer.py` that selects the appropriate SVD output (Full from T012b or Randomized from T012c) based on `data/processed/model_status.json` and outputs a unified `data/processed/subspace_matrix.json` with a consistent schema. **Requirement**: This task resolves the dependency conflict for T013 by providing a single input source. (Requires: T012, T012b-PRECHECK, T012c, T038)
- [X] T013 [US1] Implement cosine similarity calculation in `code/model_analyzer.py` between subspace bases of English models vs. BLOOM. **Requirement**: This task MUST utilize the unified `data/processed/subspace_matrix.json` from T012-ORCH. **Dependency Logic**: Depends on T012-ORCH, not directly on T012b or T012c. (Requires: T044, T044b, T044c, T012-ORCH)
- [X] T014 [US1] **Within-Language Baseline Calculation**: Implement a function in `code/model_analyzer.py` to compute the cosine similarity between the edge spectrum subspaces of Llama-3 and Mistral (English-English baseline). **Output**: `data/processed/within_language_baseline.json` containing the similarity score. **Requirement**: This is the reference value for T015. (Requires: T013)
- [X] T050 [US1] **SVD and Similarity Pipeline**: Implement the SVD and similarity pipeline function in `code/model_analyzer.py` that orchestrates loading, SVD extraction (full or randomized), and similarity calculation. (Requires: T013)
- [X] T052 [US1] **Orchestrator Integration**: Implement `code/main.py` orchestrator to run the SVD and similarity pipeline, outputting `data/processed/similarity_matrix.json` with the exact schema: `{"pairs": [{"model_a": str, "model_b": str, "cosine_similarity": float}]}`. **Handling Skips**: Read `data/processed/model_status.json` from T012b-PRECHECK. If a model is marked 'SKIPPED', output a partial matrix with nulls or a specific status 'SKIPPED' in the JSON. (Requires: T050, T012b-PRECHECK)
- [X] T015 [US1] Implement logic to calculate anisotropy deviation from the hypothesized null. **Reference**: The `reference_value` MUST be the within-language baseline similarity (Llama-3 vs. Mistral) from `data/processed/within_language_baseline.json` generated by T014. Use the formula `deviation = |observed_similarity - reference_value|`, and compute the confidence interval using the bootstrap percentile method, outputting results to `data/processed/anisotropy_deviation.json`. (Requires: T013, T014)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Cross-Lingual Token Shift (Priority: P2)

**Goal**: Identify tokens with highest logit weights in the edge spectrum subspace for each language and compare semantic categories to determine typological shift.

**Independent Test**: The system projects frequency distributions onto the subspace and outputs ranked token lists distinct from the English baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for `contracts/token_attribution.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_token_attribution_schema_valid` to validate the JSON output against the schema. (Requires: T008a-4, T008b)
- [X] T017 [P] [US2] Unit test for centroid calculation logic in `tests/unit/test_math.py`.

### Implementation for User Story 2

- [X] T018a [US2] **Data Acquisition (Common Crawl)**: Implement `code/data_loader.py` functions to download and checksum raw Common Crawl subsets (French/Chinese). **Requirement**: Output raw files to `data/raw/` (e.g., `data/raw/oscar_fr/raw.parquet`) and record SHA-256 hashes in `data/checksums.json`. Raise `FileNotFoundError` on fetch failure; NO synthetic fallbacks allowed. (Requires: T006)
- [X] T018b [US2] **Data Acquisition & Validation (RedPajama)**: Implement `code/data_loader.py` functions to download, checksum, AND validate (size check, completeness) the RedPajama dataset. **Requirement**: Output raw files to `data/raw/` and record SHA-256 hashes in `data/checksums.json`. Raise `FileNotFoundError` or `ValidationError` if validation fails; NO synthetic fallbacks allowed. (Requires: T006)
- [X] T037 [US2] **Data Streaming Verification**: Add explicit logging and unit tests in `code/data_loader.py` to verify that `datasets.load_dataset(..., streaming=True)` is used for RedPajama and Common Crawl, ensuring no full dataset is loaded into RAM. **This task MUST be completed AFTER T018a and T018b implementation to verify the actual streaming logic.** (Requires: T018a, T018b)
- [X] T039 [US2] **Explicit Data Fetch Implementation**: Update `code/data_loader.py` to use `datasets.load_dataset("oscar", "fr_2022_10", streaming=True)` for French and `datasets.load_dataset("oscar", "zh_2022_10", streaming=True)` for Chinese, and `datasets.load_dataset("togethercomputer/RedPajama-Data-1T", "default", streaming=True, split="train", trust_remote_code=True)` for English. **Requirement**: Replace any generic "download from UCI" or "download from Common Crawl" logic with these exact, verifiable Hugging Face dataset identifiers. (Requires: T018a, T018b)
- [X] T019a [US2] Implement `code/data_loader.py` to compute frequency distributions from the streamed RedPajama (English) dataset and output `data/processed/frequency_distributions_en.json`. **Requirement**: Process data in chunks to maintain memory safety; explicitly log the total token count processed to verify sample representativeness. (Requires: T018b, T037, T039)
- [X] T019b [US2] Implement `code/data_loader.py` to compute frequency distributions from the streamed Common Crawl (French/Chinese) datasets and output `data/processed/frequency_distributions_fr.json` and `data/processed/frequency_distributions_zh.json`. **Requirement**: Process data in chunks to maintain memory safety; explicitly log the total token count processed to verify sample representativeness. (Requires: T018a, T037, T039)
- [X] T020-Impl [US2] **Mean Embedding Projection (Implementation)**: Implement `code/token_attribution.py` to compute the "mean embedding" vector by projecting the **external frequency distribution** (from T019a/T019b) onto the **embedding matrix (W_E)** of the corresponding model. **Requirement**: Use external corpus frequency lists as the sole source of truth per FR-005. This is the PRIMARY implementation of the mean embedding vector. **Note**: This task creates the logic but does not execute on full data until T012-ORCH is complete. (Requires: T019a, T019b)
- [X] T020-Exec [US2] **Mean Embedding Execution**: Execute the mean embedding projection on the full frequency distributions. **Requirement**: This task is blocked until T012-ORCH completes. (Requires: T020-Impl, T012-ORCH)
- [X] T021-Impl [US2] **Mean Embedding Ranking (Implementation)**: Implement token ranking logic in `code/token_attribution.py` to rank tokens based on the projection of the **external frequency-weighted mean embedding vector** (computed in T020-Impl) onto the Edge Spectrum subspace (from T012-ORCH). This explicitly implements the metric required by FR-005 and US-2. **Requirement**: Map ranked token IDs back to specific language vocabularies using the layer from T044/T044b/T044c. **Note**: This task creates the logic but does not execute on full data until T012-ORCH is complete. (Requires: T020-Impl, T044, T044b, T044c)
- [X] T021-Exec [US2] **Mean Embedding Ranking Execution**: Execute the token ranking on the full data. **Requirement**: This task is blocked until T012-ORCH and T020-Exec complete. (Requires: T021-Impl, T020-Exec, T012-ORCH)
- [X] T021b-Impl [US2] **Individual Token Projection (Implementation)**: Implement logic in `code/token_attribution.py` to project **individual high-frequency tokens** (from the top-ranked tokens in the frequency distribution) onto the Edge Spectrum subspace. (from T012-ORCH) and rank them by projection magnitude. **Requirement**: This is the PRIMARY metric for US-2 to identify specific tokens driving the shift. (Requires: T012-ORCH, T044, T044b, T044c)
- [X] T021b-Exec [US2] **Individual Token Projection Execution**: Execute the individual token projection and ranking on the full data. **Requirement**: This task is blocked until T012-ORCH completes. (Requires: T021b-Impl, T012-ORCH)
- [X] T022 [US2] Implement overlap ratio calculation between English and non-English top-ranked token lists (from T021-Exec and T021b-Exec), outputting results to `data/processed/token_overlap.json` with schema: `{"overlap_ratio": float, "top_n": int, "baseline_overlap": float}`. **Requirement**: This task MUST consume the baseline overlap from T022b to satisfy SC-002. (Requires: T021-Exec, T021b-Exec, T044b, T044c, T022b)
- [X] T022b [US2] **Random Orthogonal Basis Baseline**: Implement logic in `code/token_attribution.py` to generate random orthogonal bases (using QR decomposition of a random Gaussian matrix) and compute the overlap ratio of top tokens against these bases to establish the `baseline_overlap`. **Requirement**: This is required for SC-002. (Requires: T044, T044b, T044c)
- [X] T053 [US2] **Token Attribution Pipeline Function**: Implement the token attribution pipeline function in `code/token_attribution.py` that orchestrates frequency distribution computation, mean embedding projection, and token ranking. (Requires: T021-Impl, T021b-Impl)
- [X] T054 [US2] **Orchestrator Integration**: Integrate `code/main.py` to execute the token attribution pipeline, outputting `data/processed/token_attribution_report.json`. (Requires: T053, T022)
- [X] T041 [US2] **Frequency Distribution Validation**: Add a validation step in `code/data_loader.py` (T019a/b) that explicitly checks if the computed frequency distribution contains at least **[deferred] tokens** (total occurrences) per FR-006. **Requirement**: If the threshold is not met, raise a `DataValidationError` with a clear message indicating insufficient data size, preventing the pipeline from proceeding with a weak sample. (Requires: T019a, T019b)
- [X] T042 [US1] **Vocabulary Intersection Verification**: Add a logging task in `code/model_analyzer.py` (T044) that explicitly counts and logs the size of the shared vocabulary intersection between Llama-3, Mistral, and BLOOM. **Requirement**: If the intersection size is **substantially large**, log a critical warning and suggest a fallback strategy. (e.g., using a subword alignment tool) rather than proceeding with a potentially invalid comparison. (Requires: T044)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Note: T020-Exec/T021-Exec execution requires T012-ORCH completion)

---

## Phase 5: User Story 3 - Validate Statistical Significance of Shift (Priority: P3)

**Goal**: Perform a permutation test (multiple iterations) using a 'within-language similarity null distribution' to assess if the observed cross-lingual similarity is statistically significant.

**Independent Test**: The system runs a sufficient number of bootstrap iterations on CPU and outputs a p-value and significance flag.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for `contracts/permutation_result.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_permutation_result_schema_valid` to validate the JSON output against the schema. (Requires: T008a-2, T008b)
- [X] T025 [P] [US3] Unit test for permutation logic with fixed seed in `tests/unit/test_math.py`.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/statistical_test.py` to generate the null distribution by **Permutation Test** using a **within-language similarity null distribution** (shuffling language pairs). **Requirement**: Strictly adhere to FR-004. This is a **Permutation Test** (shuffling language pairs), NOT a bootstrap resampling test. **Secondary Validation**: Generate random orthogonal bases (using QR decomposition of a random Gaussian matrix) ONLY as a secondary validation. (Requires: T013)
- [X] T026b [US3] **Geometric Null Generation**: Implement the generation of random orthogonal bases using QR decomposition of a random Gaussian matrix in `code/statistical_test.py` for secondary validation only. **Requirement**: Define dimensionality logic explicitly to ensure reproducibility. **Dependency**: This task now runs in parallel with T026 and feeds into the final report, not T026 itself. (Requires: T026)
- [X] T027 [US3] Implement the permutation test loop (sufficient iterations for convergence) in `code/statistical_test.py`, ensuring CPU-only execution and < h runtime, using a fixed random seed from config. (Requires: T026)
- [X] T028 [US3] Implement p-value calculation and "Statistically Significant Shift" flag generation in `code/statistical_test.py`. (Requires: T027)
- [X] T029a [US3] **WALS Configuration**: Implement `code/external_validation.py` to define the specific WALS feature set (phonological/morphological) and correlation method (Spearman's rank) as a configuration step, ensuring SC-004 is testable. (Requires: T013)
- [X] T029b [US3] **WALS Acquisition**: Implement `code/data_loader.py` to download, validate, and checksum the WALS dataset from the official source (e.g., WALS API or verified repository) to `data/raw/wals/`. **Requirement**: Record checksum in `data/checksums.json`. (Requires: T006)
- [X] T029c [US3] **SentEval Acquisition**: Implement `code/data_loader.py` to download, validate, and checksum the Multilingual SentEval STS task accuracy metrics for English, French, and Chinese from the official SentEval repository or a verified mirror. **Requirement**: Record checksum in `data/checksums.json`. (Requires: T006)
- [X] T040 [US3] **WALS Source Verification**: Implement `code/external_validation.py` to verify the WALS dataset source and integrity after acquisition. **Requirement**: Depends on T006 and T029a. (Requires: T006, T029a)
- [X] T029 [US3] Implement `code/external_validation.py` to fetch WALS data from the verified artifact (via T029b) and SentEval data (via T029c) and compute Spearman's rank correlation coefficient between subspace orientation and WALS features, AND between subspace shift and SentEval performance drop. **Requires**: T029a to define the feature set and method. **Graceful Degradation**: If WALS/SentEval data is unavailable, log a warning, output a 'data_unavailable' status in the report, and allow the pipeline to continue. **Validation**: Explicitly check if `correlation_r >= 0.5` per SC-004 and flag the result as 'valid' or 'invalid' in the output. (Requires: T013, T029a, T029b, T029c, T028, T040)
- [X] T055 [US3] **Statistical Test Function**: Implement the statistical test function in `code/statistical_test.py` that orchestrates null distribution generation, permutation loop, and p-value calculation. (Requires: T028)
- [X] T056 [US3] **External Validation Function**: Implement the external validation function in `code/external_validation.py` that orchestrates WALS/SentEval acquisition, correlation calculation. (Requires: T029)
- [X] T057 [US3] **Orchestrator Integration**: Integrate `code/main.py` to run the statistical test and external validation, outputting `data/processed/permutation_result.json` and `data/processed/wals_validation.json` with exact schemas. (Requires: T055, T056)
- [X] T043 [US3] **Bootstrap Convergence Check**: Implement a convergence check in `code/statistical_test.py` (T027) that monitors the stability of the p-value estimate as iterations increase. **Requirement**: If the p-value stabilizes (change < 0.001) before [deferred] iterations, log a "CONVERGED" status and stop early to save time, while still recording the actual number of iterations performed. (Requires: T027)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Generate `data/checksums.json` including SHA-256 hashes for all files in `data/raw` and `code/` recursively.
- [X] T032 Code cleanup and refactoring of `code/main.py` orchestrator.
- [X] T033a [P] **SVD Optimization**: Optimize SVD computation in `code/model_analyzer.py` using `scipy.linalg.svd` with `full_matrices=False` to reduce memory usage and runtime. (Requires: T012)
- [X] T033b [P] **Runtime Verification**: Verify that the optimized SVD and permutation loops complete within the < 6h runtime constraint on the target runner. (Requires: T033a)
- [X] T034a [P] **Unit Test for Missing Vocabulary Mapping**: Add unit test in `tests/unit/` for missing vocabulary mapping in `code/model_analyzer.py`. (Requires: T044)
- [X] T034b [P] **Unit Test for Numerical Instability**: Add unit test in `tests/unit/` for numerical instability in SVD (e.g., singular values < 1e-12) in `code/model_analyzer.py`. (Requires: T038)
- [X] T035 Run `quickstart.md` validation by executing `python code/main.py --dry-run` and verifying exit code 0.
- [X] T036 Final verification of all JSON outputs against contract schemas.

---

## Phase N+1: Review Remediation & Feasibility Validation

**Purpose**: Address specific review concerns regarding data integrity, feasibility, and methodological rigor.

- [X] T060 [P] [Review] **Mandatory CPU Feasibility Gate**: Implement a strict pre-execution check in `code/main.py` that calculates the theoretical RAM usage for the full SVD of the largest model (BLOOM or similar) on the target runner (limited RAM). **Logic**: If `matrix_size * 4 bytes * 2 > 6GB`, log a **Feasibility Warning** with a detailed message explaining that the CPU runner cannot support the full SVD for this model size, and **mark T012b as SKIPPED for that model**; do NOT raise a `FatalError` or abort the entire pipeline. **Action**: The pipeline MUST continue with valid models or a sampled approach; output `data/processed/feasibility_report.json` with the warning status. (Requires: T012b-PRECHECK, T004)
- [X] T061 [P] [Review] **Data Loader Strictness Enforcement**: Audit `code/data_loader.py` to ensure NO `try/except` blocks exist that fall back to `generate_synthetic_*()` or `mock_*()` functions when real data fetching fails. **Action**: Replace any such fallbacks with explicit `raise FileNotFoundError` or `raise DataFetchError` statements that halt execution. Verify that `datasets.load_dataset` is called with `streaming=True` for all large datasets (RedPajama, OSCAR) to prevent OOM. (Requires: T018a, T018b, T019a, T019b)
- [X] T062 [P] [Review] **WALS Data Integrity Check**: Add a validation step in `code/external_validation.py` (T029) that verifies the WALS dataset contains the specific feature columns required for the target languages (English, French, Chinese) before attempting correlation. **Action**: If required columns are missing, raise a `ValidationError` with a list of missing features. Ensure the correlation calculation strictly uses the verified WALS data and does not default to random or placeholder values. (Requires: T029b, T029a)
- [X] T063 [P] [Review] **Token Attribution Logic Verification**: Implement a unit test in `tests/unit/test_token_attribution.py` that verifies the "mean embedding" projection logic (T020-Impl) correctly uses the external frequency distribution and not the model's internal token probabilities. **Action**: Mock the frequency distribution and verify that the projection result matches the expected linear algebra operation on the external data. Ensure the test fails if the internal model probabilities are used. (Requires: T020-Impl, T019a, T019b)
- [X] T064 [P] [Review] **Bootstrap Null Distribution Validation**: Add a contract test in `tests/contract/test_schemas.py` that verifies the `null_distribution` generated in T026 consists of similarities between the observed subspace and *permutation shuffled language pairs*, not random permutations of the observed subspace or random orthogonal bases. **Action**: Generate a known permuted dataset and verify the similarity calculation logic produces a valid scalar. Ensure the test fails if the null distribution is derived from the observed data itself or geometric bases. (Requires: T026, T024)
- [X] T065 [P] [Review] **Cross-Lingual Vocabulary Alignment Robustness**: Implement a validation task in `code/model_analyzer.py` (T044) that explicitly checks the size of the shared vocabulary intersection between Llama-3, Mistral, and BLOOM. **Action**: If the intersection size is < 50,000 tokens, log a critical warning and output `data/processed/vocab_alignment_warning.json` with the intersection size. Do NOT proceed with the similarity calculation if the intersection is too small to support a statistically valid comparison without the fallback T044c. (Requires: T044, T044c, T013)

---

## Phase N+2: GPU Offload & Large-Scale Execution (Revision for Feasibility)

**Purpose**: Address the critical feasibility gap identified by T060/T012b-PRECHECK. This phase defines the strategy for external GPU execution without embedding it in the main CPU pipeline, preserving the "CPU-first" principle.

- [ ] T066 [P] [GPU-Offload] **Feasibility Detection**: Update `code/config.py` and `code/main.py` to detect the `RUNNER_TYPE` environment variable and output a `gpu_required` flag based on T012b-PRECHECK results. **Requirement**: This task ONLY detects the need for GPU; it does not execute GPU code. (Requires: T012b-PRECHECK)
- [ ] T069 [P] [GPU-Offload] **External Runner Strategy**: Define the exact command-line arguments and script structure for the Kaggle GPU kernel in a separate `kaggle_runner.py` or documentation. **Requirement**: This task defines the *strategy* for offloading, but the actual execution is handled by the execution stage, not the main task list. The main pipeline (T012) remains CPU-only. (Requires: T066)
- [ ] T070 [P] [GPU-Offload] **GPU Runtime Validation**: Implement a test in `tests/unit/test_gpu_feasibility.py` that mocks the CUDA environment and verifies that the `kaggle_runner.py` script would successfully load a simulated large matrix and perform SVD without OOM, confirming the logic for the Kaggle offload path. (Requires: T069)
- [ ] T071 [P] [GPU-Offload] **SentEval/WALS GPU Compatibility**: Verify that the external validation tasks (T029) and SentEval correlation logic do not introduce CPU-only bottlenecks that prevent the GPU-optimized SVD from being utilized. **Requirement**: Ensure data transfer between GPU (SVD results) and CPU (correlation logic) is handled efficiently. (Requires: T029)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Remediation (Phase N+1)**: Depends on all User Stories and Polish phases; addresses specific review concerns.

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
- All Review Remediation tasks (Phase N+1) can run in parallel as they are independent validation checks.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for similarity_matrix.schema.yaml in tests/contract/test_schemas.py"
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
- **Feasibility Note**: All tasks strictly adhere to CPU-first constraints. T012 allows Randomized SVD as a valid fallback when RAM constraints are hit, with explicit logging of the approximation. T012b-PRECHECK, T060, and T066 handle feasibility detection. T069 defines the external GPU strategy.
- **Data Integrity**: No synthetic data generation; all tasks require real datasets (Common Crawl, RedPajama, WALS) via `data_loader.py`. T018a, T018b, T029b, T029c, and T061 explicitly mandate downloading and checksumming raw files before streaming/processing. T061 ensures no synthetic fallbacks.
- **Methodology note**: T020 implements the 'frequency distribution' projection onto **W_E** (embedding matrix) per FR-005 as the primary and ONLY method. T026 implements the strict FR-004 **Permutation Test** (shuffling language pairs), NOT a geometric null. T029 enforces WALS/SentEval validation with SC-004 threshold check but allows graceful degradation. T044/T044b/T044c handles vocabulary misalignment with a deterministic strategy and fallback. T029a defines WALS parameters for SC-004. T008a-1..T008a-9 validates SC-005 early with specific thresholds. T033a/T033b optimize and verify runtime. T060, T061, T062, T063, T064, T065 address specific review concerns. T014 computes the within-language baseline. T021b implements individual token projection. T022b implements the random orthogonal basis baseline.
- **Cross-Phase Dependency**: T020-Exec, T021-Exec, T021b-Exec (US2) depend on T012-ORCH (US1). While US2 implementation can start after Foundational, T020-Exec/T021-Exec/T021b-Exec execution is blocked until T012-ORCH completes.
- **Streaming Enforcement**: T037 ensures that large datasets are processed via streaming to prevent OOM errors on the 7GB RAM runner, adhering to the "Stream real data" rule. T037 is now a prerequisite for T019a/b to catch violations early. T061 reinforces this.
- **Numerical Safety**: T038 adds a guard against numerical instability in SVD, ensuring robustness for the statistical tests.
- **Strict Compliance**: All tasks now strictly adhere to the ratified spec. No scope creep, no proxy substitutions, no alternative metrics. T060-T065 ensure strict adherence to feasibility and data integrity rules.
- **ID Uniqueness**: All task IDs (T001-T071) are unique. T008a-1..T008a-9 are exclusive to Phase 2. T044, T044b, T044c are exclusive to Phase 3. T050-T057 are exclusive to Phases 3-5. T060-T071 are exclusive to Phases N+1 and N+2. No duplicates exist.
- **GPU Offload Logic**: T012b-PRECHECK outputs `gpu_required`. If true, T069 (External Runner Strategy) is triggered. The main pipeline (T012) remains CPU-only. The execution stage handles the offload.