# Tasks: llmXive follow-up: extending "ArcANE"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- **Include exact file paths in descriptions**

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- **Paths shown below assume single project - adjust based on plan.md structure**

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `specs/001-gene-regulation/`)
- [X] T002 Initialize Python project with `requirements.txt` (transformers, llama-cpp-python, datasets, scikit-learn, scipy, pandas, numpy, tiktoken, hypothesis, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and Data Contracts that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the definition of all JSON schemas required for data integrity.

- [ ] T004 Setup data directory structure (`data/raw/`, `data/derived/`, `data/gold_standard/`, `artifacts/`)
- [X] T005 [P] Implement robust logging infrastructure in `src/lib/utils.py` (file + console handlers, JSON formatting)
- [X] T006 [P] Create base configuration management for seeds and model paths in `src/lib/config.py`
- [X] T007 Implement data validation helpers in `src/lib/validators.py` (schema checks, type clamping)
- [X] T008 [P] [US3] Setup experiment state tracking (logging run IDs, timestamps, parameter hashes, AND content hashes for state/parameters) in `src/lib/state.py` to satisfy Constitution Principle V.
- [ ] T009 Load external Gold Standard dataset from `data/gold_standard/human_annotations.json` (no code‑generated data). This file must be a version-controlled JSON artifact containing 20 manually annotated samples. [UNRESOLVED-CLAIM: c_4301ffc4 — status=not_enough_info] <!-- FAILED: unspecified -->
- [ ] T010 [P] Create File: `specs/001-gene-regulation/contracts/axis.schema.yaml`. **Content**: Define YAML schema for `CharacterAxis` containing TWO objects: `Coarse` (fields: `character`, `axis_name`, `description`) and `Fine` (fields: `character`, `axis_name`, `description`, `source_observation`). **Note**: Single file for both schemas to prevent overwrite.
- [ ] T015 [P] Create `data/derived/axes.jsonl` writer to store validated axis definitions.
- [ ] T011b [P] Create File: `config/axes_input.yaml`. **Content**: Template YAML file with example Coarse/Fine axis definitions for 'Scrooge' and 'Elizabeth Bennet' to be used by T011 in CI mode.
- [ ] T011 [US1] Implement `src/services/axis_generator.py` with logic to load axis definitions from `config/axes_input.yaml` (non‑interactive CI mode) or interactive CLI prompt. **Output**: `data/derived/axes.jsonl`.
- [ ] T012 [US1] Implement semantic validation logic in `src/services/axis_generator.py` (lexical overlap > 0.4, embedding cosine distance < 0.3) using `sentence-transformers/all-MiniLM-L6-v2`. This logic MUST be called by T011a to block invalid input.
- [ ] T011a [US1] Implement `src/cli/axis_input.py` with independent input validation logic: requires two separate text blocks for Coarse and Fine axes. **Depends on**: T010, T012. **Logic**: Call T012's automated check before accepting input. If validation fails, reject input and log error.
- [ ] T014 [P] [US1] Unit test for axis semantic overlap constraint in `tests/unit/test_axis_validation.py`. **Note**: This test depends on T010 (schema) and T012 (service) being implemented first.
- [ ] T013 [US1] **Download Source Text**: Download public domain texts for source corpus. **Primary Sources**: 1) ` (Pride and Prejudice), 2) ` (A Christmas Carol). **Action**: Concatenate and save to `data/raw/arcane_corpus.jsonl`. **Constraint**: Must raise exception on download failure; NO synthetic fallback.
- [ ] T037d [P] Document legal justification for substituting copyrighted characters (e.g., Harry Potter) with public‑domain characters in the source‑text download step (T013). Update spec assumptions accordingly.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Character Arc Specifications (Priority: P1) 🎯 MVP

**Goal**: Allow researchers to define and store independent Coarse and Fine psychological axes for characters.

**Independent Test**: A researcher can input a character name and receive two distinct, non‑overlapping JSON objects representing the Coarse and Fine axes, verified against semantic overlap constraints.

*(All implementation tasks for US1 are defined in Phase 2; no additional tasks are required here.)*

---

## Phase 4: User Story 2 - Generate Out-of-World Probes (Priority: P2)

**Goal**: Generate at least 50 unique "Out-of-World" scenario prompts per character that are semantically distant from the source text.

**Independent Test**: The system generates a batch of probes, and a sample check confirms none contain direct quotes/plot points and average cosine similarity to source text is < 0.3 [UNRESOLVED-CLAIM: c_7d42aa8c — status=not_enough_info].

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T017 [P] [US2] Unit test for probe regeneration loop and similarity threshold in `tests/unit/test_probe_generation.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `src/services/probe_generator.py` with logic to generate novel scenarios based on character axes. **Constraint**: Must use a small, quantized model (e.g., TinyLlama‑1.1B) on CPU. If generation fails, retry with different seed; do NOT fall back to synthetic templates.
- [ ] T019 [US2] Implement semantic similarity check (cosine similarity < 0.3) against `data/raw/arcane_corpus.jsonl` (source text) in `src/services/probe_generator.py` using `sentence-transformers/all-MiniLM-L6-v2`. Must stream the corpus if too large for RAM, or load in chunks.
- [ ] T021 [P] Create `data/derived/probes.jsonl` writer to store validated out‑of‑world probes.
- [ ] T020 [US2] Implement regeneration loop in `src/services/probe_generator.py` with explicit discard logic: **Step 1**: Generate candidate (T018). **Step 2**: Run T019 check. **Step 3**: If valid, save via T021. **Step 4**: If retry count > 150, log "Generation Limit Exceeded" and proceed with available valid probes (if >= 50) or mark character as invalid. **Depends on**: T018, T019, T021.
- [ ] T022 [US2] Implement error handling for "Generation Limit Exceeded" in `src/services/probe_generator.py`. If `valid_probes < 50` after 150 attempts, set `character_status` to `'invalid'` in `data/derived/probes.jsonl` (Edge Cases, FR‑002).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Hybrid Prompting and Consistency Evaluation (Priority: P3)

**Goal**: Execute the target model under three conditions, calibrate a Judge model, and perform statistical analysis.

**Independent Test**: The system processes a probe through all conditions, outputs structured results with scores, and performs a Shapiro‑Wilk test to select ANOVA or Friedman.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T023 [P] [US3] Contract test for Judge output format and clamping in `tests/unit/test_judge_clamp.py`
- [X] T024 [P] [US3] Integration test for full experiment flow in `tests/integration/test_experiment_flow.py`

### Implementation for User Story 3

- [X] T025 [P] [US3] Implement model loading utilities in `src/models/loader.py` (CPU‑quantized small language models, low‑bit quantization, specifically Phi‑3‑mini or TinyLlama‑1.1B via `llama.cpp` or low‑bit `transformers` per Constitution Principle VI).
- [X] T026 [US3] Implement `src/services/judge_service.py` for LLM‑based consistency scoring using a standard Likert scale, with output validation, clamping, **and** adherence flag determined by checking that the response contains **at least 2 phase‑specific keywords** from the prompt.
- [X] T027 [US3] Implement `src/services/rule_based_metric.py` to calculate a composite rule‑based score based on **keyword presence**, VADER sentiment alignment, and a configurable weighting factor (`w`). Formula: `score = w * sentiment_score + (1‑w) * keyword_match_score`. Keyword match score counts presence of phase‑specific keywords.
- [X] T028 [P] Create `data/derived/results_raw.jsonl` writer to store raw responses and scores.
- [X] T029 [US3] Implement Judge Calibration step in `src/services/judge_service.py` ({{claim:c_e64a59a9}} using `sklearn.metrics.cohen_kappa_score` with quadratic weights). If Kappa ≤ 0.6, raise a RuntimeError and halt execution. [UNRESOLVED-CLAIM: c_cce40fc1 — status=not_enough_info] If the gold standard file is missing or malformed, raise a clear error. **Depends on**: T009.
- [X] T029c [US3] Implement logic to aggregate Judge model output validation failures (scores outside the standard range), calculate the failure rate, and record it as a metric in `data/derived/judge_metrics.json` (SC‑005).
- [X] T030 [US3] Implement `src/services/experiment_runner.py` to run target model under Coarse, Fine, and Hybrid conditions. Explicitly construct "Coarse Context", "Fine Context", and "Hybrid Context" strings as per Spec definitions. **Constraint**: Must handle timeouts per Edge Cases.
- [X] T031 [US3] Implement timeout handling inside `experiment_runner`: if a single probe generation exceeds the timeout, log the failure, assign a default consistency score of 0, and continue to the next probe.
- [X] T032 [US3] Instrument `experiment_runner` and `stats_engine` to capture, log, and report the total wall‑clock time of the full experiment run to `data/derived/timing.log`. Read CI time limit from environment variable `CI_TIME_LIMIT_SECONDS` (fallback to a timeout duration of several hours). If cumulative elapsed time exceeds this limit, raise `SystemExit(1)` to fail the CI job.
- [X] T027a [US3] Implement `aggregate_consistency_scores` in `src/analysis/stats_engine.py` to combine the Judge score (T026) and rule‑based score (T027) into a single 'Consistency Score' artifact. Write final aggregated scores to `data/derived/results_final.jsonl`. **Depends on**: T028, T026, T027, T030.
- [X] T029b [US3] Implement `validate_against_gold_standard(results, gold_data)` in `src/analysis/stats_engine.py` to compute correlation/error metrics against `data/gold_standard/human_annotations.json` and ensure the evaluation is not circular. **Depends on**: T027a.
- [X] T033 [US3] Implement `check_normality(scores)` in `src/analysis/stats_engine.py` to perform Shapiro‑Wilk test on the residuals of the `judge_score` field from `data/derived/results_final.jsonl` and return `is_normal` (bool). **Depends on**: T027a.
- [X] T034 [US3] Implement `select_statistical_test(is_normal)` in `src/analysis/stats_engine.py` to return the test type ('anova' or 'friedman') based on `is_normal`.
- [X] T035 [US3] Implement `run_statistical_test(scores, test_type)` in `src/analysis/stats_engine.py` to execute the chosen statistical test (ANOVA or Friedman) and write the p‑value, effect size, mean scores, and variance to `data/derived/stats_results.json` (FR‑005, SC‑004). **Depends on**: T033, T034.
- [X] T035b [US3] Extend `run_statistical_test` to calculate the variance of consistency scores across the three conditions and include it in `stats_results.json`.
- [X] T036 [P] Add CLI entry point in `src/cli/run_experiment.py` to trigger the full experiment pipeline.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037a [P] Update `specs/001-gene-regulation/quickstart.md` with new CLI flags and data format changes.
- [ ] T037b [P] Update `README.md` with new data formats and execution instructions.
- [ ] T038a Code cleanup: Refactor error handling to be consistent across all services.
- [ ] T038b Code cleanup: Refactor logging calls to use standardized format.
- [ ] T039 Performance optimization for batch processing of probes
- [ ] T040 [P] Additional unit tests for statistical engine edge cases in `tests/unit/test_stats_engine.py`
- [ ] T041 Run `quickstart.md` validation to ensure end‑to‑end reproducibility on CPU