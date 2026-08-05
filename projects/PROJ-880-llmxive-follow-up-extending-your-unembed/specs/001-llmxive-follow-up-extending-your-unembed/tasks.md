---
description: "Task list template for feature implementation"
---

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
- [X] T006 Implement `code/data_loader.py` skeleton with functions for downloading, verifying checksums, and hashing datasets. **Depends on** T005.
- [X] T007 Create base `code/__init__.py` and error handling infrastructure.
- [X] T008 [P] Create all contract schemas: Generate `contracts/` directory and create all required schema files (`similarity_matrix.schema.yaml`, `permutation_result.schema.yaml`, `wals_validation.schema.yaml`, `token_attribution.schema.yaml`, `frequency_list.schema.yaml`, `similarity_report.schema.yaml`, `spectrum_output.schema.yaml`, `statistical_results.schema.yaml`, `permutation_results.schema.yaml`, `final_report.schema.yaml`) with definitions matching the spec's output contracts. **Depends on** T005.
 - [X] T008a-1 Create `similarity_matrix.schema.yaml`.
 - [X] T008a-2 Create `permutation_result.schema.yaml`.
 - [X] T008a-3 Create `wals_validation.schema.yaml`.
 - [X] T008a-4 Create `token_attribution.schema.yaml`.
 - [X] T008a-5 Create `frequency_list.schema.yaml`.
 - [X] T008a-6 Create `similarity_report.schema.yaml`.
 - [X] T008a-7 Create `spectrum_output.schema.yaml`.
 - [X] T008a-8 Create `statistical_results.schema.yaml`.
 - [X] T008a-9 Create `final_report.schema.yaml`.
- [X] T008b Implement the skeleton test file `tests/contract/test_schemas.py` with specific test function stubs: `test_similarity_matrix_schema_valid`, `test_permutation_result_schema_valid`, `test_wals_validation_schema_valid`, `test_token_attribution_schema_valid`, `test_frequency_list_schema_valid`, ensuring they import and use the schema files from T008. **Depends on** T008a-1, T008a-2, T008a-3, T008a-4, T008a-5, T008a-6, T008a-7, T008a-8, T008a-9.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Compare Edge Spectrum Subspaces (Priority: P1) 🎯 MVP

**Goal**: Compute the "edge spectrum" subspace (top‑k singular vectors) of $W_U$ for Llama‑3, Mistral, and BLOOM and calculate cosine similarity between subspaces to quantify geometric rotation.

**Independent Test**: The system runs SVD on three models and outputs a JSON report with non‑zero cosine similarity scores between model pairs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 Contract test for `contracts/similarity_matrix.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_similarity_matrix_schema_valid` to validate the JSON output against the schema. (Requires: T008, T008b)
- [X] T010 Unit test for SVD extraction on a mock matrix in `tests/unit/test_math.py`.

### Implementation for User Story 1

- [X] T011 Implement `code/model_analyzer.py` to load unembedding matrix $W_U$ from HuggingFace models (Llama, Mistral, BLOOM) using CPU‑only float32 loading, with error handling for missing/corrupted weight files.
- [X] T044 Implement a deterministic vocabulary mapping layer: compute the intersection of tokenizers for Llama, Mistral, BLOOM, write `data/processed/vocab_mapping.json` mapping each model's token IDs to shared IDs, and log intersection size. **Output**: `data/processed/vocab_status.json` containing `intersection_size` and `status` ('OK' or 'INSUFFICIENT_OVERLAP'). (Depends on T011)
- [X] T044‑Fallback Implement translation‑map‑based alignment using the **muse library (MUSE) from facebookresearch/MUSE** if `vocab_status.json` reports 'INSUFFICIENT_OVERLAP' (< 5000 tokens). **Output**: `data/processed/vocab_alignment_report.json` with method used and mapping file. (Depends on T044)
- [X] T012 Implement SVD extraction to compute **top‑k (k=100) singular vectors** of the **projected unembedding matrix** (after T044 or T044‑Fallback) using `scipy.sparse.linalg.svds`. Do **not** subset rows/columns. Mask singular values < 1e‑12 and log warnings. (Depends on T044/T044‑Fallback)
- [X] T012b **Feasibility Pre‑check & Hard Abort**: Estimate memory usage for the full‑matrix SVD. If the estimate exceeds 6 GB, **raise `PipelineAbortError` immediately** and write `data/processed/feasibility_report.json` with status `ABORTED`. **Do NOT** attempt out-of-core fallbacks that contradict the spec's feasibility assumptions. **Output**: `data/processed/feasibility_report.json` with fields `model`, `memory_estimate_gb`, `status` (`OK` or `ABORTED`). (Depends on T011)
- [X] T012d **SVD Completion Verification**: After each model's SVD run (if not aborted), verify that the resulting singular vectors file exists and is well‑formed; record success in `model_status.json`. If any model fails, raise a pipeline abort error. (Depends on T012, T012b)
- [X] T013 Implement cosine similarity calculation between subspace bases of English models vs. BLOOM using the shared vocabulary mapping (or fallback). **Output**: `data/processed/similarity_matrix.json` adhering to `similarity_matrix.schema.yaml`. (Depends on T012 or T012b, T044/T044‑Fallback)
- [X] T014 Within‑Language Baseline Calculation: Compute cosine similarity between Llama‑3 and Mistral subspaces (English‑English). **Output**: `data/processed/within_language_baseline.json`. (Depends on T013)
- [X] T050 Implement the SVD and similarity pipeline function in `code/model_analyzer.py` that orchestrates loading, SVD extraction, and similarity calculation. (Depends on T013)
- [X] T052 Orchestrator Integration: Extend `code/main.py` to run the SVD and similarity pipeline, outputting `data/processed/similarity_matrix.json`. Handle memory‑intensive cases by halting with `PipelineAbortError` as defined in T012b. (Depends on T050, T012b)
- [X] T043 **Bootstrap Convergence Check**: Within `code/statistical_test.py`, monitor p‑value stability; if change < 0.001 before the maximum iterations, log "CONVERGED" and stop early, recording actual iteration count. (Depends on T027)
- [X] T015 Compute anisotropy deviation: `deviation = |observed_similarity - reference_value|` where `reference_value` is from `within_language_baseline.json`. Compute a 95 % confidence interval via bootstrap percentile method and output `data/processed/anisotropy_deviation.json` with fields `deviation`, `ci_lower`, `ci_upper`. **Note**: This is a derived metric; the raw similarity is output by T013. (Depends on T013, T014, T043)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Cross‑Lingual Token Shift (Priority: P2)

**Goal**: Identify tokens with highest logit weights in the edge spectrum subspace for each language and compare semantic categories to determine typological shift.

**Independent Test**: The system projects frequency distributions onto the subspace and outputs ranked token lists distinct from the English baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 Contract test for `contracts/token_attribution.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_token_attribution_schema_valid` to validate the JSON output against the schema. (Requires: T008, T008b)
- [X] T017 Unit test for centroid calculation logic in `tests/unit/test_math.py`.

### Implementation for User Story 2

- [X] T018a Implement `code/data_loader.py` functions to download and checksum raw Common Crawl subsets (French/Chinese) to `data/raw/oscar_fr/` and `data/raw/oscar_zh/`. Raise `FileNotFoundError` on failure; no synthetic fallbacks.
- [X] T018b Implement `code/data_loader.py` functions to download, checksum, and validate RedPajama dataset to `data/raw/redpajama/`. Raise `FileNotFoundError` or `ValidationError` on failure.
- [X] T037 Add explicit logging and unit tests in `code/data_loader.py` to verify that `datasets.load_dataset(..., streaming=True)` is used for both RedPajama and OSCAR.
- [X] T039 Update `code/data_loader.py` to use exact Hugging Face identifiers:
 - French: `datasets.load_dataset("oscar", "unshuffled_deduplicated_fr", streaming=True)`
 - Chinese: `datasets.load_dataset("oscar", "unshuffled_deduplicated_zh", streaming=True)`
 - English RedPajama: `datasets.load_dataset("togethercomputer/RedPajama-Data-1T", "default", streaming=True, split="train", trust_remote_code=True)`
- [X] T019a Compute English frequency distribution from RedPajama, processing in streaming chunks, log total token count, and write `data/processed/frequency_distributions_en.json`. Enforce ≥ 1,000,000 tokens; otherwise raise `DataValidationError`. (Depends on T018b, T037, T039)
- [X] T019b Compute French and Chinese frequency distributions similarly, output `frequency_distributions_fr.json` and `frequency_distributions_zh.json`. (Depends on T018a, T037, T039)
- [X] T041 Frequency Distribution Validation: Verify each frequency file contains ≥ 1,000,000 tokens; write `data/processed/frequency_validation_report.json` with per‑language status. (Depends on T019a, T019b)
- [X] T020‑Impl Implement `code/token_attribution.py` to compute the "mean embedding" vector by projecting the external frequency distribution onto the embedding matrix $W_E$ (projected to shared vocab). **Output**: `data/processed/mean_embedding_<lang>.json`. (Depends on T019a/b, T044/T044‑Fallback)
- [X] T020‑Exec Execute mean embedding projection for all languages after SVD artifacts are ready. (Depends on T020‑Impl, T012/T012b)
- [X] T021‑Impl Implement token ranking: project each language's mean embedding onto its edge spectrum subspace and rank tokens by projection magnitude. Map token IDs back via `vocab_mapping.json`. **Output**: `data/processed/token_ranking_<lang>.json` following `token_attribution.schema.yaml`. (Depends on T020‑Impl, T044/T044‑Fallback)
- [X] T021‑Exec Execute token ranking for all languages. (Depends on T021‑Impl, T020‑Exec)
- [X] T021b‑Impl Implement individual high‑frequency token projection (top 1000 tokens) onto edge spectrum subspace, rank by magnitude. **Output**: `data/processed/individual_token_projection_<lang>.json`. (Depends on T012/T012b, T044/T044‑Fallback)
- [X] T021b‑Exec Execute individual token projection for all languages. (Depends on T021b‑Impl)
- [X] T022 Implement overlap ratio calculation between English and non‑English top‑ranked token lists, output `data/processed/token_overlap.json` with fields `overlap_ratio`, `top_n`, `baseline_overlap`. (Depends on T021‑Exec, T021b‑Exec)
- [X] T022b Implement random orthogonal basis generation (QR decomposition of Gaussian matrix) and compute baseline overlap ratio; output `data/processed/random_basis_overlap.json`. (Depends on T044/T044‑Fallback)
- [X] T053 Token Attribution Pipeline Function: orchestrate frequency computation, mean embedding projection, and token ranking. (Depends on T021‑Impl, T021b‑Impl)
- [X] T054 Orchestrator Integration: extend `code/main.py` to run the token attribution pipeline, output `data/processed/token_attribution_report.json` adhering to `token_attribution.schema.yaml`. (Depends on T053, T022, T020‑Exec, T021‑Exec)
- [X] T042 **WALS Correlation Update**: Use the reduced shift vector (from T030) when computing correlation with WALS features; output `data/processed/wals_correlation.json`. (Depends on T030)

**Checkpoint**: User Stories 1 and 2 are independently functional (US‑2 tasks respect US‑1 dependency on shared vocab mapping).

---

## Phase 5: User Story 3 - Validate Statistical Significance of Shift (Priority: P3)

**Goal**: Perform a permutation test (multiple iterations) using a 'within‑language similarity null distribution' to assess if the observed cross‑lingual similarity is statistically significant.

**Independent Test**: The system runs a sufficient number of permutation iterations on CPU and outputs a p‑value and significance flag.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 Contract test for `contracts/permutation_result.schema.yaml` in `tests/contract/test_schemas.py`. Implement function `test_permutation_result_schema_valid` to validate the JSON output against the schema. (Requires: T008, T008b)
- [X] T025 Unit test for permutation logic with fixed seed in `tests/unit/test_math.py`.

### Implementation for User Story 3

- [X] T026 Implement `code/statistical_test.py` to generate the **within-language similarity null distribution** by comparing subspaces of same-language model pairs (e.g., Llama-EN vs Mistral-EN) and computing observed similarity. **Output**: `data/processed/null_distribution.json`. **MUST NOT** use geometric baselines. (Depends on T013)
- [X] T026b **Optional Baseline**: Generate random orthogonal bases (QR of Gaussian) for secondary validation; write `data/processed/geometric_null.json`. **MUST NOT** be used for primary p-value calculation. (Depends on T026)
- [X] T027 Implement permutation test loop with fixed seed, at least 1,000 iterations, early convergence detection (change < 0.001). **MUST NOT use geometric baselines** (T026b) for the p-value; use only the within-language null from T026. **Output**: `data/processed/permutation_result.json` following `permutation_result.schema.yaml`. (Depends on T026)
- [X] T028 Compute p‑value and flag "Statistically Significant Shift" in `permutation_result.json`. (Depends on T027)
- [X] T029 **External Validation**: Compute Spearman correlation between the **full shift vector** (NO PCA reduction) and WALS feature differences, and between the shift vector and SentEval performance drop. Output `data/processed/wals_validation.json` and `data/processed/senteval_correlation.json`. If datasets unavailable, log warning and set status `data_unavailable`. (Depends on T020‑Exec/T021‑Exec, T028, T029a, T029b, T029c, T029c‑Exec, T040)
- [X] T030 **Dimensionality Reduction for Visualization**: Apply PCA to the shift vector (difference between English and target language mean embeddings) to retain N components (e.g., N=20) for visualization only. Write `data/processed/reduced_shift_vector.json`. **Do NOT use for correlation**. (Depends on T029)
- [X] T029a **WALS Configuration**: Define required WALS feature set (e.g., WordOrder, Morphology, Phonology) and correlation method (Spearman). (Depends on T013)
- [X] T029b **WALS Acquisition**: Download and checksum WALS dataset to `data/raw/wals/`. Record checksum in `data/checksums.json`. (Depends on T006)
- [X] T029c **SentEval Acquisition**: Download and checksum Multilingual SentEval STS metrics from `datasets.load_dataset('senteval', 'multilingual-sts')` to `data/raw/senteval/`. Record checksum. (Depends on T006)
- [X] T029c‑Exec **SentEval Execution**: **Execute** the SentEval benchmark code against the downloaded datasets to generate the STS accuracy metrics. **Output**: `data/processed/senteval_metrics.json`. (Depends on T029c)
- [X] T040 **WALS Source Verification**: Verify WALS dataset contains required columns; raise `ValidationError` if missing. (Depends on T029b, T029a)
- [X] T055 Statistical Test Function: Orchestrate null distribution generation, permutation loop, and p‑value calculation. (Depends on T028)
- [X] T056 External Validation Function: Orchestrate WALS and SentEval correlation calculations. (Depends on T029)
- [X] T057 Orchestrator Integration: Extend `code/main.py` to run statistical test and external validation, outputting `permutation_result.json`, `wals_validation.json`, and `senteval_correlation.json`. (Depends on T055, T056)
- [X] T043 **Bootstrap Convergence Check**: Within `code/statistical_test.py`, monitor p‑value stability; if change < 0.001 before the maximum iterations, log "CONVERGED" and stop early, recording actual iteration count. (Depends on T027)

**Checkpoint**: All user stories now independently functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 Generate `data/checksums.json` including SHA‑256 hashes for all files in `data/raw` and `code/` recursively.
- [X] T032 **Code Cleanup**: Refactor `code/main.py` to follow PEP8, add docstrings, and ensure lint passes (`flake8`, `black`). Add integration test `tests/integration/test_main.py` that runs the full pipeline with `--dry-run` and asserts exit code 0.
- [X] T033a **SVD Optimization**: Optimize SVD computation in `code/model_analyzer.py` using `scipy.sparse.linalg.svds` with `full_matrices=False` to reduce memory usage. (Depends on T012)
- [X] T033b **Runtime Verification**: Verify that the optimized SVD and permutation loops complete within the < 6 h runtime constraint on the target runner. (Depends on T033a)
- [X] T034a **Unit Test for Missing Vocabulary Mapping**: Add unit test in `tests/unit/` to ensure `model_analyzer` raises a clear error when `vocab_mapping.json` is missing or incomplete. (Depends on T044)
- [X] T034b **Unit Test for Numerical Instability**: Add unit test in `tests/unit/` for handling singular values < 1e‑12 in `model_analyzer`. (Depends on T038)
- [X] T035 Run `quickstart.md` validation by executing `python code/main.py --dry-run` and verifying exit code 0.
- [X] T036 Final verification of all JSON outputs against contract schemas.

---

## Phase N+1: Review Remediation & Feasibility Validation

**Purpose**: Address specific review concerns regarding data integrity, feasibility, and methodological rigor.

- [X] T060 **Feasibility Gate** (see Phase 2) – now fully implemented with detailed warning, status update, and `feasibility_report.json`. **Output**: `data/processed/feasibility_report.json`. (Depends on T012b)
- [X] T061 **Data Loader Strictness Enforcement**: Add static analysis lint rule `no-synthetic-fallback` that fails if any `try/except` block catches a data‑fetch error and calls a synthetic generator. Include test `tests/unit/test_data_loader_strictness.py`. (Depends on T018a, T018b, T019a, T019b)
- [X] T062 **WALS Data Integrity Check**: Verify that the downloaded WALS CSV contains columns `WordOrder`, `Morphology`, `Phonology`. Raise `ValidationError` if missing. (Depends on T029b, T029a)
- [X] T063 **Token Attribution Logic Verification**: Add unit test `tests/unit/test_mean_embedding.py` that mocks a frequency distribution and asserts that `mean_embedding` uses the external distribution, not model probabilities.
- [X] T064 **Bootstrap Null Distribution Validation**: Add contract test `tests/contract/test_permutation_null.py` that generates a known permuted language‑pair dataset and verifies that the null distribution consists of similarity scores between permuted pairs only.
- [X] T065 **Cross‑Lingual Vocabulary Alignment Robustness** (see Phase 2): Implement intersection‑size check, write `vocab_alignment_warning.json` with fields `intersection_size`, `status`, `halt` (bool). If `intersection_size < 5000`, raise `PipelineAbortError` to stop further processing. **Output**: `data/processed/vocab_alignment_warning.json`. (Depends on T044, T044‑Fallback, T013)

---

## Phase N+2: Runner Specification Update

**Purpose**: Align the project's runner configuration with the spec's requirement of appropriate vCPU and RAM resources.

- [X] T080 **Runner Specification Update**: Modify `.github/workflows/full_pipeline.yml` to request a runner that satisfies the spec's 4 vCPU and 16 GB RAM requirement (e.g., using a self‑hosted runner or a larger GitHub‑provided runner). Ensure all memory‑intensive tasks respect the new limits and document this alignment in the workflow file. This resolves the SC‑005 resource contradiction.

---

## Phase N+3: Polish & Release

**Purpose**: Finalize deliverables, documentation, and reproducibility for publication.

- [X] T071 **Consolidated Final Report**: Generate `results/final_report.json` aggregating:
 - `similarity_matrix` (from `similarity_matrix.json`)
 - `anisotropy_deviation` (with CI fields)
 - `token_overlap` (including baseline)
 - `permutation_result`
 - `wals_validation`
 - `senteval_correlation`
 - `feasibility_report`
 - `vocab_alignment_warning`
 **Schema** defined in `contracts/final_report.schema.yaml`. (Depends on all prior result artifacts)
- [X] T072 Write comprehensive `README.md` describing methodology, data sources, usage instructions, and how to reproduce each experiment, referencing all contract schemas and configuration files.
- [X] T073 Add GitHub Actions workflow `.github/workflows/full_pipeline.yml` that runs the entire pipeline on push, including data download, SVD, token attribution, permutation test, and validation; fails if any contract schema validation or test fails.
- [X] T074 **Technical Report**: Create `docs/report.md` with sections: Introduction, Methods, Results (including generated plots), Discussion, Reproducibility Checklist. Provide a checklist file `docs/checklist.md` to verify presence of each section and that all plots referenced in `results/plots/` exist.

---

## Phase N+4: Review Remediation - Data Source Verification & Streaming Robustness

**Purpose**: Address specific reviewer concerns regarding the reliability of real data streams and the strict enforcement of "Real Data Only" constraints, ensuring no synthetic fallbacks occur silently.

- [X] T090 [P] [US2] **Streaming Integrity Check**: Implement `code/data_loader.py` function `verify_stream_chunk_integrity` that validates the schema of each chunk received from `datasets.load_dataset(..., streaming=True)` before processing. Schema: `{'text': str, 'id': str}`. If a chunk fails schema validation (e.g., missing `text` field), raise `DataCorruptionError` immediately rather than skipping. **Output**: Log `stream_integrity_report.json` with chunk counts and error details. **Depends on** T037, T039.
- [ ] T091 [P] [US2] **Token Count Verification**: Add a hard guard in `code/data_loader.py` that halts the pipeline if the total token count (sum of token counts) from a streaming source (RedPajama/OSCAR) is < 1,000,000 after processing the entire available stream. Do not proceed with a smaller sample; raise `DataInsufficiencyError`. **Output**: `data/processed/token_count_guard.json` with status `PASS` or `FAIL`. **Depends on** T019a, T019b.
- [X] T092 [P] [US2] **Cross-Lingual Frequency Distribution Stability Test**: Implement `tests/unit/test_freq_stability.py` that runs the frequency distribution computation multiple times on a small fixed seed subset (e.g., 10k tokens) to verify that the resulting distribution vectors are bitwise identical (deterministic). This ensures the streaming logic is not introducing non-deterministic noise. **Depends on** T019a, T019b.
- [X] T093 [P] [US2] **WALS/SentEval Fallback Prevention**: Modify `code/external_validation.py` to remove any `try/except` blocks that catch download errors for WALS or SentEval and substitute default/mock values. Instead, implement a `strict_download` mode that raises `ExternalDataUnavailable` if the verified URL fails. **Output**: `data/processed/external_data_status.json` with fields `wals_status`, `senteval_status`. **Depends on** T029b, T029c.
- [X] T094 [P] [US3] **Permutation Test Determinism Check**: Add a unit test `tests/unit/test_permutation_determinism.py` that runs the permutation test with a fixed seed and verifies that the generated null distribution is identical across runs. This ensures the "within-language similarity" baseline is reproducible and not affected by random number generator state drift. **Depends on** T027.
- [X] T095 [P] [US1] **SVD Numerical Stability Verification**: Add a unit test `tests/unit/test_svd_stability.py` that constructs a known matrix with small singular values and verifies that `scipy.sparse.linalg.svds` correctly masks values < 1e-12 without crashing or producing NaNs. **Depends on** T012.

---

## Phase N+5: Review Remediation - Methodological Rigor & Documentation

**Purpose**: Address reviewer concerns regarding the theoretical justification of the "Shared-Vocabulary Projection" and the clarity of the "Mean Embedding" computation.

- [X] T096 [P] [US1] **Vocabulary Projection Justification**: Update `docs/methodology.md` (or `research.md`) to include a mathematical derivation of the Shared-Vocabulary Projection, explicitly stating why intersecting token IDs is preferred over translation-based alignment for this specific hypothesis test. Include a citation to the "Edge Spectrum" paper's section on basis invariance. **Depends on** T044.
- [X] T097 [P] [US2] **Mean Embedding Interpretation**: Update `docs/methodology.md` to clarify the physical interpretation of the "Mean Embedding" vector $\hat{h} = W_E \times f$. Explicitly state that this represents the "vocabulary centroid" in the embedding space and discuss the assumption that frequency-weighted centroids capture "common sense" priors. **Depends on** T020-Impl.
- [X] T098 [P] [US3] **Null Hypothesis Definition**: Update `docs/methodology.md` to explicitly define the Null Hypothesis for the permutation test: "The observed cross-lingual subspace similarity is indistinguishable from the similarity observed between within-language model pairs." Ensure this definition matches the implementation in T026. **Depends on** T026.
- [ ] T099 [P] **Final Reproducibility Audit**: Run the full pipeline with `--reproducibility-check` flag (new feature in `main.py`) that re-downloads all data (if checksums differ), re-runs all computations with fixed seeds, and asserts that all output hashes match the previous run. **Logic**: Compare SHA-256 hashes of all files in `data/processed` and `results/` against the `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml` `artifact_hashes` map. **Output**: `results/reproducibility_audit.json` with schema `{"status": str, "mismatches": [{"file": str, "expected_hash": str, "actual_hash": str}], "passed": bool}`. **Depends on** T031, T073.