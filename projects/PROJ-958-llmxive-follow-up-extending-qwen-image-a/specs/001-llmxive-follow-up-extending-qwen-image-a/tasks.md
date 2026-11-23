# Tasks: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create directory structure: `src/`, `tests/`, `data/`, `data/raw/`, `data/derived/`, `data/results/`, `state/`
- [X] T001b Create directory structure: `code/`, `docs/`, `code/utils/`, `code/scoring/`, `code/routing/`, `code/fidelity/`, `code/domain/`, `code/pilot/`, `code/pipeline/`
- [X] T001c Create `README.md` and `.gitignore` with standard Python patterns
- [X] T002 Initialize Python project with dependencies (`pandas`, `numpy`, `scikit-learn`, `nltk`, `spacy`, `torch`, `transformers`, `statsmodels`, `textstat`, `datasets`, `huggingface_hub`, `matplotlib`, `seaborn`, `diffusers`, `accelerate`, `tiktoken`) in `requirements.txt`
- [X] T003a Create `pyproject.toml` with `[tool.ruff]` section (rules: E, F, W, I, N, UP, B, C4, SIM, ANN) and `[tool.black]` section (line-length=88, target-version=py311)
- [X] T003b Create `ruff.toml` and `black.toml` (if separate) or ensure `pyproject.toml` is the single source of truth for linting config

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Gate Logic**: T008a must pass before any data is fetched.

- [X] T008a [P] [US1] Implement `src/main.py` orchestration script including the `Reference-Validator` gate invocation BEFORE data loading. **Gate Logic**: Load citations from `plan.md`, run Reference-Validator, and **block** execution (raise error) if any citation fails validation. **This task must be completed and validated before T006a-g.**
- [X] T006a [P] [US1] Implement `src/utils/data_loader.py` function to fetch IA-Bench dataset (prompts + images) using `datasets.load_dataset("nlp-ai-lab/IA-Bench", split="train", streaming=True)` and download real images to `data/raw/ia-bench/`. **Include internal validation**: Verify the dataset source citation in `plan.md` matches the fetched ID; raise error if mismatch. **DEPENDS ON T008a.**
- [X] T006b [P] [US1] Implement `src/utils/data_loader.py` function to validate IA-Bench schema and raise error if mismatched
- [X] T006c [P] [US1] Implement `src/utils/data_loader.py` function to compute SHA-256 checksum for IA-Bench raw data and save to `state/artifact_hashes/ia-bench.json` with schema `{"file": "data/raw/ia-bench", "hash": "<sha256>"}`
- [X] T006d [P] [US1] Implement `src/utils/data_loader.py` function to fetch WISE-Verified dataset (prompts + images + metadata) using explicit URL/package fetch (`datasets.load_dataset("nlp-ai-lab/WISE-Verified", split="train")`) to `data/raw/wise-verified/`
- [X] T006e [P] [US1] Implement `src/utils/data_loader.py` function to validate WISE-Verified schema and raise error if mismatched
- [X] T006f [P] [US1] Implement `src/utils/data_loader.py` function to compute SHA-256 checksum for WISE-Verified raw data and save to `state/artifact_hashes/wise-verified.json` with schema `{"file": "data/raw/wise-verified", "hash": "<sha256>"}`
- [X] T006g-1 [P] [US1] Implement `src/utils/data_loader.py` logic to fetch "human-verified reference descriptions" from the IA-Bench dataset (field: `reference_description`) and save to `data/raw/ia-bench/references.jsonl`. **Fail loudly** if the field is missing or empty.
- [X] T006g-2 [P] [US1] Implement `src/utils/data_loader.py` logic to validate that `references.jsonl` contains the required 'reference_description' field and is non-empty for all rows (Schema Check) AND verify the 'human-verified' flag (if present) or confirm source is gold-standard.
- [X] T006g-3 [P] [US1] Implement `src/utils/data_loader.py` logic to compute SHA-256 checksum for `data/raw/ia-bench/references.jsonl` and save to `state/artifact_hashes/references.json` with schema `{"file": "data/raw/ia-bench/references.jsonl", "hash": "<sha256>"}`. **Output**: `data/raw/ia-bench/references.jsonl` must exist.
- [X] T007 [P] [US1] Implement `src/utils/data_loader.py` logic to fail loudly if real data fetch fails for IA-Bench (NO synthetic fallback)
- [X] T007b [P] [US1] Implement `src/utils/data_loader.py` logic to fail loudly if WISE-Verified fetch fails (NO synthetic fallback)
- [X] T004 Create `src/config.py` with pinned random seeds, path configurations, and threshold constants (0.2, 0.6)
- [X] T005 [P] Implement `src/utils.py` with logging infrastructure, error handling wrappers, and domain stratification helpers

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Syntactic Complexity Scoring & Dataset Stratification (Priority: P1) 🎯 MVP

**Goal**: Compute a deterministic "Syntactic Complexity Score" (0.0–1.0) for every input prompt using only syntactic complexity and lexical diversity, explicitly excluding semantic embeddings.

**Independent Test**: Run the scoring script on a known subset of prompts and verify the output CSV contains scores., syntactic features, and lexical features, with no semantic embedding vectors present.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for `src/scoring/syntactic_features.py` in `tests/unit/test_scoring.py` verifying no semantic embeddings are used (check for absence of BERT/CLIP text encoder calls)
- [X] T010 [P] [US1] Unit test for malformed prompt handling in `tests/unit/test_scoring.py` (verify default 0.0 score and warning log)

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `src/scoring/syntactic_features.py` with syntactic complexity metrics (parse tree depth, clause count) using `nltk`/`spacy`
- [X] T012 [P] [US1] Implement `src/scoring/syntactic_features.py` with lexical diversity metric (MTLD) using `textstat`
- [X] T013 [US1] Implement the weighted average formula in `src/scoring/complexity_calculator.py` to combine metrics into a raw score
- [X] T013b [US1] Implement `src/scoring/complexity_calculator.py` normalization logic to clamp raw score strictly to [0.0, 1.0] range (min-max scaling)
- [X] T014 [US1] Implement logic in `src/scoring/syntactic_features.py` to handle parse failures gracefully (assign 0.0, log warning)
- [X] T015a [US1] Create script skeleton `src/scoring/run_scoring.py` with CLI argument parsing (`--input`, `--output`) and file I/O setup.
- [X] T015b [US1] Implement scoring logic in `src/scoring/run_scoring.py` to process prompts using `syntactic_features.py` and `complexity_calculator.py`.
- [X] T015c [US1] Implement file I/O in `src/scoring/run_scoring.py` to write output to `data/derived/scoring_results.csv` with schema: `prompt_id, source, complexity_score, parse_depth, clause_count, mtld`.
- [X] T015d [US1] Add verification step in `src/scoring/run_scoring.py` to validate output schema and row count (N = total prompts). **Output**: `data/derived/scoring_results.csv` must exist and be valid.
- [X] T015b [US1] Add logic in `run_scoring.py` to output reference metadata (if available) alongside scores
- [X] T016 [US1] Add logging in `src/scoring/syntactic_features.py` to confirm no semantic embeddings were used during execution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hybrid Routing & Real Execution (Priority: P2)

**Goal**: Implement a deterministic "Router" that classifies prompts into "low," "medium," or "high" complexity categories and routes them to either rule-based expansion or the REAL Qwen-Image-Agent pipeline.

**Independent Test**: Feed a mix of clearly simple and complex prompts and verify that simple prompts trigger the rule-based path (logging "Router: Low") while complex prompts trigger the REAL agent path (logging "Router: High"), confirming real images are generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for `src/routing/router.py` in `tests/unit/test_router.py` verifying threshold logic (< 0.2, 0.2–0.6, > 0.6)
- [X] T018 [P] [US2] Unit test for `src/routing/lightweight_expander.py` in `tests/unit/test_expander.py` verifying fixed template generation

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `src/routing/router.py` with deterministic classification logic based on Syntactic Complexity Score thresholds
- [X] T020 [P] [US2] Implement `src/routing/lightweight_expander.py` with rule-based context expansion module (fixed templates) for low/medium complexity
- [X] T020b [US2] Implement `src/routing/lightweight_expander.py` to calculate and expose `actual_token_count` for the expanded text output using `tiktoken.get_encoding('cl100k_base').encode(text)` (used for efficiency comparison in T023)
- [X] T021b [P] [US2] Implement `src/pipeline/agent_config.py` to define the entry point, API signature, and configuration for the REAL Qwen-Image-Agent pipeline (FR-009). **Output**: `src/pipeline/agent_config.py` with explicit function call or script path.
- [X] T021 [US2] Implement `src/pipeline/runner.py` to dispatch "low/medium" prompts to the lightweight expander and "high" prompts to the REAL Qwen-Image-Agent pipeline (FR-009) using the entry point from T021b.
- [X] T022 [US2] Integrate Router, Expansion, and Agent execution in `src/pipeline/runner.py` to process the dataset and log routing decisions (FR-007)
- [X] T023 [US2] Add logging in `src/pipeline/runner.py` to record measured token counts (LLM) and latency for the agent path, and `actual_token_count` and latency for the rule-based path (FR-008)
- [X] T024 [US2] Write routing logs to `data/derived/routing_decisions.csv` including input score, category, target path, token counts (real), and latency
- [X] T024b [US2] Ensure `src/pipeline/runner.py` generates actual images for "high" complexity prompts using the REAL agent (or verified proxy) and saves them to `data/derived/images/hybrid/high/`. **Output**: `data/derived/images/hybrid/high/` must exist.
- [X] T024c [US2] Implement a separate script `src/pipeline/generate_baseline.py` to generate "baseline" (full agent) images ONLY for the "high" complexity subset (as identified in T024) and save to `data/derived/images/baseline/high/` to enable Fidelity Delta calculation for high prompts (FR-004)
- [X] T024e [US2] Implement a separate script `src/pipeline/generate_baseline.py` to generate "baseline" (full agent) images for a **stratified random sample of [deferred] (minimum 500 samples)** of the entire dataset (stratified by complexity score bins and visual domain using seed 42) and save to `data/derived/images/baseline/full_sample/`. This provides the necessary baseline for the Fidelity Delta calculation for low/medium prompts where the hybrid path uses the rule-based expander (FR-004). **Output**: `data/derived/images/baseline/full_sample/` and `data/derived/baseline_sample_ids.json`.

**Pilot Study (FR-012) - Moved to Phase 4 to ensure Agent pipeline availability**

- [X] T012a [US1/US2] Implement `src/pilot/study_runner.py` to select a **known subset of prompts** from `data/derived/scoring_results.csv` (for US-1 Independent Test). Execute BOTH the **Full Agent** (baseline) and **Hybrid** (rule-based for low/medium, agent for high) pipelines for these prompts. Save baseline images to `data/derived/images/pilot_100/baseline/` and hybrid images to `data/derived/images/pilot_100/hybrid/`. Input: `data/derived/scoring_results.csv`. **DEPENDS ON T015 (Scoring) and T021/T024b (Agent Pipeline).**
- [X] T012b [US1/US2] Implement `src/pilot/study_runner.py` to select a **random subset of prompts** from `data/derived/scoring_results.csv` (for Pilot Study). Execute BOTH pipelines. Save baseline images to `data/derived/images/pilot_200/baseline/` and hybrid images to `data/derived/images/pilot_200/hybrid/`.
- [X] T012c [US1/US2] Implement `src/pilot/failure_rate_computer.py` to compute the **"Fidelity Delta"** (Baseline CLIP Score - Hybrid CLIP Score) for each prompt in the pilot subset (both 100 and 200). This delta serves as the proxy for "need for agentic reasoning". Output: `data/derived/pilot_deltas.json`.
- [X] T012d [US1/US2] Implement `src/pilot/study_runner.py` to compute the correlation coefficient (Pearson/Spearman) between the **Syntactic Complexity Score** (from `scoring_results.csv`) and the **Fidelity Delta** (from T012c) for the 200-prompt pilot. Output `data/derived/pilot_correlation.json` with the correlation coefficient and p-value (FR-012).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fidelity Measurement & Threshold Detection (Priority: P3)

**Goal**: Compute "Context Fidelity" delta using frozen CLIP (ViT-B/32) against human-verified references and identify the "knee point" via piecewise linear regression with statistical validation.

**Independent Test**: Run the regression analysis on pre-computed data and verify the output includes a calculated knee point, a plot, and a statistical justification (F-test + LRT) that the piecewise model is superior.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for `src/fidelity/clip_evaluator.py` in `tests/unit/test_fidelity.py` verifying CLIP inference and error handling (skip on format mismatch)
- [X] T026 [P] [US3] Unit test for `src/fidelity/regression_analysis.py` in `tests/unit/test_regression.py` verifying F-test and knee point detection logic

### Implementation for User Story 3

- [X] T031 [P] [US3] Implement `src/domain/classifier.py` with a pre-trained ResNet-50 classifier to determine visual domain (photorealistic, abstract, illustration) for generated images (FR-011). **Output**: `data/derived/domain_labels.csv` (prompt_id, domain).
- [X] T027 [P] [US3] Implement `src/fidelity/clip_evaluator.py` with frozen CLIP (ViT-B/32) inference, CPU-batched processing, and delta calculation (Baseline vs. Hybrid).
 - **Inputs**:
 - `data/derived/images/baseline/full_sample/` (from T024e) - Baseline for all
 - `data/derived/images/hybrid/` (from T024b) - Hybrid for high; Rule-based for low/medium
 - `data/raw/ia-bench/references.jsonl` (from T006g-3)
 - **Logic**: Calculate CLIP similarity for Baseline and Hybrid pairs. Compute **Fidelity Delta** = Baseline Score - Hybrid Score.
 - **Output**: `data/derived/fidelity_scores.csv` containing prompt_id, complexity_score, domain, baseline_score, hybrid_score, fidelity_delta. (FR-004)
- [X] T028 [P] [US3] Implement `src/fidelity/clip_evaluator.py` to handle CLIP failures gracefully (log error, skip data point, continue)
- [X] T029 [US3] Implement `src/fidelity/regression_analysis.py` with piecewise linear regression to identify the "knee point" where slope change < 0.01. **Output**: Piecewise model object and initial knee point estimate.
- [X] T030a [US3] Implement statistical validation in `src/fidelity/regression_analysis.py` including: 1) F-test (p < 0.05) AND 2) Likelihood Ratio Test (LRT) against a linear model. **BOTH** tests must pass to validate the 'knee point' as a statistically superior non-linear relationship. If either test fails, output "No Threshold Found" flag. **Output**: LRT stats and p-values.
- [X] T030b [US3] Implement a permutation test with **10,000 permutations** (FR-006) to validate the significance of fidelity difference below threshold. Alpha = 0.05. **Output**: Permutation p-value.
- [X] T030c [US3] Implement decision logic in `src/fidelity/regression_analysis.py` to combine F-test, LRT, and Permutation test results. Output `data/derived/regression_results.json` with knee point, p-values, and LRT stats (FR-005, FR-006). If "No Threshold Found", output flag and max observed delta.
- [X] T032a [US3] Implement `src/fidelity/regression_analysis.py` with stratified regression analysis by visual domain using domain labels from `src/domain/classifier.py` (FR-010). **MANDATORY**: Perform an ANOVA or Levene's test for statistical equivalence of domain slopes. **Output**: p-value for equivalence.
- [X] T032b [US3] Implement logic in `src/fidelity/regression_analysis.py`: If p > 0.05 (equivalence), proceed to global regression. If p <= 0.05 (significant difference), **exclude** global regression and compute domain-specific thresholds only.
- [X] T032c [US3] Implement output generation in `src/fidelity/regression_analysis.py`: If global model is valid, output `data/results/regression_results.json` (with knee point). If global model is invalid, output `data/results/domain_specific_thresholds.json` with schema `{"domains": [{"domain": "photorealistic", "threshold": 0.XX}, ...]}`. **Output**: Final regression results file.
- [X] T033 [US3] Create script `src/fidelity/run_fidelity_analysis.py` to orchestrate CLIP scoring, regression, and stratified analysis, outputting `data/derived/regression_results.json` (including knee point, p-values, and stratified plots)
- [X] T034 [US3] Add logic to handle "No Threshold Found" case (R² < 0.85 or slope change < 0.01) and record max observed delta

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Update `docs/data_flow.md` with diagram showing data flow from raw fetch (T006a-g) to derived results
- [X] T035b [P] Update `docs/thresholds.md` with explicit definitions of routing thresholds (0.2, 0.6) and normalization logic
- [X] T035c [P] Update `docs/api.md` with module descriptions for `scoring.py`, `router.py`, `fidelity.py`
- [X] T036a [P] Refactor `src/scoring/syntactic_features.py` to remove duplicate parsing logic and standardize error handling
- [X] T036b [P] Refactor `src/fidelity/clip_evaluator.py` to standardize logging format and batch processing logic
- [X] T037 [P] Implement dynamic batch sizing in `src/fidelity/clip_evaluator.py` to ensure peak RAM usage remains within 6GB limits using a binary search algorithm; output a memory profile log to `data/derived/memory_profile.log` (Assumptions / FR-008)
- [X] T038 [P] Additional unit tests for edge cases (e.g., empty datasets, all-malformed prompts)
- [X] T039 Run `quickstart.md` validation to ensure end-to-end pipeline execution
- [X] T040 Verify all artifacts in `data/derived/` are reproducible with pinned seeds
- [X] T041 [P] Implement `src/state_manager.py` to generate and commit `state/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a.yaml` with `updated_at` timestamp and `artifact_hashes` map after data processing (Constitution Principle V). **Output**: `state/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a.yaml` must exist.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. Produces `data/derived/scoring_results.csv`.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Consumes `scoring_results.csv`. Produces `routing_decisions.csv`, generated images, and efficiency metrics. **Note**: Pilot Study (T012a-d) is now part of Phase 4 as it depends on the Agent pipeline.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Consumes `scoring_results.csv`, `routing_decisions.csv`, generated images, and **human-verified references** (from T006g-3). Produces `regression_results.json`.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Modules before integration
- Core implementation before logging/reporting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for src/scoring/syntactic_features.py in tests/unit/test_scoring.py"
Task: "Unit test for malformed prompt handling in tests/unit/test_scoring.py"

# Launch implementation tasks for User Story 1 together:
Task: "Implement src/scoring/syntactic_features.py with syntactic complexity metrics"
Task: "Implement src/scoring/syntactic_features.py with lexical diversity metric (MTLD)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify no semantic embeddings, correct scoring)
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
 - Developer A: User Story 1 (Scoring)
 - Developer B: User Story 2 (Routing/Real Execution)
 - Developer C: User Story 3 (Fidelity/Regression)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Data Rule**: The `src/utils/data_loader.py` MUST fail loudly if real data fetch fails. NO synthetic fallbacks allowed.
- **Critical Scoring Rule**: `src/scoring/syntactic_features.py` MUST NOT use any semantic embeddings (BERT, CLIP text). Only syntax/lexical.
- **Critical Compute Rule**: CLIP inference must be CPU-batched to fit in limited RAM

The research question, method, and references remain unchanged as no specific values were present in the original text to alter beyond the generalization of the memory constraint.. If GPU is needed for speed, the execution stage will auto-offload, but the code must be written for CPU-first compatibility.
- **Critical Regression Rule**: T032 MUST perform a statistical equivalence test (ANOVA) before global regression. If domains differ significantly, global regression is forbidden.
- **Critical Fidelity Rule**: Fidelity calculation (T027) MUST use **human-verified reference descriptions** (Task T006g-3), not raw prompts or images.
- **Critical Normalization Rule**: Syntactic Complexity Score MUST be strictly clamped to [0.0, 1.0] (Task T013b).
- **Critical Token Count Rule**: Rule-based expansion MUST expose `actual_token_count` (Task T020b) using a real tokenizer, not a proxy.
- **Critical Real Execution Rule**: "High" complexity prompts MUST trigger the REAL Qwen-Image-Agent pipeline (T021, T024b) to generate actual images, not simulated data.
- **Critical Baseline Rule**: T024e MUST generate baseline images for a **stratified random sample of [deferred] (min 500)** of the full dataset to enable valid Fidelity Delta calculation for all categories without violating the hybrid routing logic.
- **Critical Pilot Rule**: T012a-d MUST measure **Fidelity Delta** (Baseline - Hybrid) as the proxy for "need for agentic reasoning", not failure rate.