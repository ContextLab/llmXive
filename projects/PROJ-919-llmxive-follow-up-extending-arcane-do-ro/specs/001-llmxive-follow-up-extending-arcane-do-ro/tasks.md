# Tasks: llmXive follow-up: extending "ArcANE"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-arcane-do-ro/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e., US1, US2, US3)
- **Include exact file paths in descriptions**

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- **Paths shown below assume single project - adjust based on plan.md structure**

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and critical data prerequisites.

- [X] T001 Create project directory structure: `src/`, `tests/`, `data/`, `data/raw/`, `data/derived/`, `data/gold_standard/`, `artifacts/`, `specs/001-llmxive-follow-up-extending-arcane-do-ro/`. Create empty `.gitkeep` files in each directory to ensure they are tracked.
- [X] T002 Initialize Python project with `requirements.txt` (transformers, llama-cpp-python, datasets, scikit-learn, scipy, pandas, numpy, tiktoken, hypothesis, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, Data Contracts, and Gold Standard generation that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the definition of all JSON schemas required for data integrity and the generation of the Gold Standard dataset.

- [X] T009a [US1/US3] **Generate Gold Standard Dataset**: Attempt to fetch `llmXive/arcane-gold-standard` from HuggingFace. **Constraint**: If the fetch fails (dataset missing/private), **automatically invoke T009a-gen** to generate the dataset using the protocol in T009c. **Output**: `data/gold_standard/human_annotations.json`. **Note**: This task encapsulates both fetch and fallback generation to ensure the artifact is always produced.
- [X] T009a-gen [US1/US3] **Implement Gold Standard Fallback Generator**: Implement `src/services/gold_standard_generator.py`. **Logic**: 1. Fetch "Pride and Prejudice" (Gutenberg ID: 1342) using `datasets.load_dataset`. 2. Extract paragraphs at regular intervals. 3. Annotate each segment with "Coarse" and "Fine" phase labels using the rule set: "Early chapters = Innocence/Naive Trust", "Late chapters = Experience/Calculated Skepticism". 4. Save to `data/gold_standard/human_annotations.json`. **Constraint**: This is the executable fallback for T009a.
- [X] T009b [US1/US3] **Record Gold Standard Checksum**: Compute the SHA256 checksum of `data/gold_standard/human_annotations.json` (from T009a) and record it in `state/projects/PROJ-919-.../artifact_hashes` to satisfy Constitution Principle III.
- [X] T005 [P] Implement robust logging infrastructure in `src/lib/utils.py` (file + console handlers, JSON formatting)
- [X] T006 [P] Create base configuration management for seeds and model paths in `src/lib/config.py`
- [X] T007 Implement data validation helpers in `src/lib/validators.py` (schema checks, type clamping)
- [X] T008 [P] [US3] Setup experiment state tracking (logging run IDs, timestamps, parameter hashes, AND content hashes for state/parameters) in `src/lib/state.py` to satisfy Constitution Principle V.
- [X] T049 [P] [US2] **Implement Robust Stream Loading**: Create `src/lib/stream_loader.py`. **Signature**: `def load_stream(path: str) -> Iterator[dict]`. **Logic**: Use `datasets.load_dataset(..., streaming=True)` or manual chunking to read large text files (e.g., `data/raw/arcane_corpus.jsonl`) in chunks. **Constraint**: This module MUST be used by T019 (Phase 4) to prevent RAM overflow. **Note**: T013 writes the file; T049 defines the reading logic for large files.
- [X] T010 [P] Create File: `specs/001-llmxive-follow-up-extending-arcane-do-ro/contracts/axis.schema.yaml`. **Content**:
```yaml
$schema: http://json-schema.org/draft-07/schema#
$id:
title: Character Axis Definition
type: object
properties:
 coarse:
 type: object
 properties:
 character:
 type: string
 axis_name:
 type: string
 description:
 type: string
 required:
 - character
 - axis_name
 - description
 fine:
 type: object
 properties:
 character:
 type: string
 axis_name:
 type: string
 description:
 type: string
 source_observation:
 type: string
 minLength: 10
 required:
 - character
 - axis_name
 - description
 - source_observation
required:
 - coarse
 - fine
```
- [X] T012 [US1] Implement semantic validation logic in `src/services/axis_validator.py`. **Logic**: Load two axis definitions (Coarse, Fine).
 1. **Lexical Overlap**: Tokenize both descriptions using `nltk.word_tokenize` (lowercase, strip punctuation, remove stopwords), compute Jaccard similarity (|A ∩ B| / |A ∪ B|).
 2. **Semantic Distance**: Embed both descriptions using `sentence-transformers/all-MiniLM-L6-v2` with 'mean' pooling, compute cosine distance.
 3. **Constraint**: Pass only if lexical overlap > 0.4 AND cosine distance < 0.3. Ensure `source_observation` is non-empty and distinct.
- [X] T014 [US1] Unit test for axis semantic overlap constraint in `tests/unit/test_axis_validation.py`. **Note**: This test depends on T010 (schema) and T012 (service) being implemented first.
- [X] T015 [P] [US1] Create `data/derived/axes.jsonl` writer to store validated axis definitions.
- [X] T011b [P] Create `config/characters.json`. **Content**: JSON mapping of character names to public-domain source IDs (e., `{"Elizabeth Bennet": {"source": "gutenberg", "id": "1342"}, "Ebenezer Scrooge": {"source": "gutenberg", "id": "2401"}}`).
- [X] T013 [US2] **Download Source Text**: Download public domain texts for source corpus. **Logic**: Accept `--character` argument. Read mapping from `config/characters.json` (T011b). Fetch text from Gutenberg using the mapped ID. **Constraint**: If a character is missing from the mapping or fetch fails, **skip that character, log an error, and proceed** with available characters. **NO** synthetic fallback. Concatenate and save to `data/raw/arcane_corpus.jsonl`.
- [X] T037d [P] [US1] **Update Spec Assumptions**: Update `specs/001-llmxive-follow-up-extending-arcane-do-ro/spec.md` Assumptions section to explicitly state that the scope is limited to public-domain characters defined in `config/characters.json`.
- [X] T027a [US3] **Define Sentiment Config**: Create `config/sentiment_targets.json`. **Content**: JSON mapping of "Coarse", "Fine", and "Hybrid" phases to target sentiment values (e.g., `{"Coarse": "positive", "Fine": "neutral", "Hybrid": "mixed"}`). **Logic**: Define the target sentiment for each phase. **Constraint**: This file MUST exist before T027 is implemented. **Depends on**: None.

**Checkpoint**: Foundation and Data Setup ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Character Arc Specifications (Priority: P1) 🎯 MVP

**Goal**: Allow researchers to define and store independent Coarse and Fine psychological axes for characters.

**Independent Test**: A researcher can input a character name and receive two distinct, non‑overlapping JSON objects representing the Coarse and Fine axes, verified against semantic overlap constraints.

- [X] T011a [US1] Implement `src/cli/axis_input.py` with manual input validation logic: requires two separate JSON/YAML files for Coarse and Fine axes via `--coarse-file` and `--fine-file` CLI arguments. **Logic**: Load inputs, validate against T010 schema, then call T012's validation function. If validation fails, reject input and log error. **Depends on**: T010, T012, T015.

---

## Phase 4: User Story 2 - Generate Out-of-World Probes (Priority: P2)

**Goal**: Generate at least 50 unique "Out-of-World" scenario prompts per character that are semantically distant from the source text.

**Independent Test**: average cosine similarity to source text is < 0.3

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T017 [P] [US2] Unit test for probe regeneration loop and similarity threshold in `tests/unit/test_probe_generation.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `src/services/probe_generator.py` with logic to generate novel scenarios based on character axes. **Constraint**: **Prompt**: Use a predefined template: "You are a character with traits [COARSE] and [FINE]. Generate a scenario set in [MODERN/SCI-FI SETTING] that tests these traits. Do NOT use any plot points from the original story." **Seed**: Use a fixed seed for reproducibility. **Setting Selection**: Randomly select `[MODERN/SCI-FI SETTING]` from a predefined list of multiple settings (e.g., "cyberpunk city", "post-apocalyptic wasteland"). **Depends on**: T013 (source text must exist).
- [X] T019 [US2] Implement semantic similarity check (cosine similarity < 0.3) against `data/raw/arcane_corpus.jsonl` (source text) in `src/services/probe_generator.py` using `sentence-transformers/all-MiniLM-L6-v2`. **Constraint**: **Must import `src/lib/stream_loader.py` and use `load_stream` to read the corpus**. Must verify `data/raw/arcane_corpus.jsonl` exists before proceeding. **Depends on**: T013, T049.
- [X] T021 [P] Create `data/derived/probes.jsonl` writer to store validated out‑of‑world probes.
- [X] T020 [US2] Implement regeneration loop in `src/services/probe_generator.py` with explicit discard logic: **Step 1**: Generate candidate (T018). **Step 2**: Run T019 check. **Step 3**: If valid, save via T021. **Step 4**: If retry count > 150, log "Generation Limit Exceeded" and proceed with available valid probes (if >= 50) or mark character as invalid. **Depends on**: T018, T019, T021.
- [X] T022 [US2] Implement error handling for "Generation Limit Exceeded" in `src/services/probe_generator.py`. If `valid_probes < 50` after 150 attempts, set `character_status` to `'invalid'` in `data/derived/probes.jsonl` (Edge Cases, FR‑002).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Hybrid Prompting and Consistency Evaluation (Priority: P3)

**Goal**: Execute the target model under three conditions, calibrate a Judge model, and perform statistical analysis.

**Independent Test**: The system processes a probe through all conditions, outputs structured results with scores, and performs a Shapiro‑Wilk test to select ANOVA or Friedman.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T023 [P] [US3] Contract test for Judge output format and clamping in `tests/unit/test_judge_clamp.py`
- [X] T024 [P] [US3] Integration test for full experiment flow in `tests/integration/test_experiment_flow.py`

### Implementation for User Story 3

- [X] T025 [P] [US3] Implement model loading utilities in `src/models/loader.py` (CPU‑quantized small language models, low‑bit quantization, specifically Phi‑‑mini or TinyLlama‑1.1B via `llama.cpp` or low‑bit `transformers` per Constitution Principle VI).
- [X] T026 [US3] Implement `src/services/judge_service.py` for LLM‑based consistency scoring using a standard Likert scale, with output validation, clamping, **and** adherence flag determined by semantic alignment (LLM Judge) to the target phase. **Constraint**: The adherence flag MUST NOT rely on keyword counting; it must be a semantic judgment. The rule-based metric (T027) will handle the independent check.
- [X] T027 [US3] Implement `src/services/rule_based_metric.py` to calculate `sentiment_score` based on the target sentiment from `config/sentiment_targets.json` (T027a) AND **keyword presence** and **sentiment alignment** with the target phase's expected sentiment. **Logic**:
 1. Calculate sentiment polarity of the response using `textblob` (returns a normalized polarityscore).
 2. Normalize polarity to a unit interval: `normalized_polarity = (polarity + 1.0) / 2.0`.
 3. Calculate target polarity from config (e.g., "positive" -> 1.0, "neutral" -> 0.5, "negative" -> 0.0 (2207.09163, https://arxiv.org/abs/2207.09163)).
 4. Compute sentiment alignment score as `1 - abs(normalized_polarity - target_polarity)`.
 5. **Keyword Check**: Count occurrences of phase-specific keywords defined in the prompt. If count < 2, apply a **keyword penalty** (e.g., subtract 0.2 from the score).
 6. Combine: `final_score = sentiment_alignment_score - keyword_penalty`. **Constraint**: The score is based on both sentiment and keyword presence. **Output**: Return a score within the defined range (0-1). **Note**: This satisfies the spec's requirement for a dual-metric validation strategy.
- [X] T028 [P] Create `data/derived/results_raw.jsonl` writer to store raw responses and scores.
- [X] T029 [US3] Implement Judge Calibration step in `src/services/judge_service.py`. **Logic**: Load `data/gold_standard/human_annotations.json` (T009a). Compute Cohen's Kappa (quadratic weights) between the Judge's scores and the human annotations. **Constraint**: If Kappa ≤ 0.6, raise a RuntimeError with a clear message: "Judge calibration failed: Kappa {kappa} <= 0.6". **Depends on**: T009a, T026 (Interface/Logic). **Note**: T029 validates the T026 configuration before main execution. T026 must not be considered 'ready' until T029 passes.
- [X] T029a [US3] **Record Calibration Metrics**: Write the computed Kappa coefficient, the number of samples used, and the pass/fail status to `data/derived/calibration_metrics.json` as a traceable artifact (FR-007, SC-006).
- [X] T029c [US3] Implement logic to aggregate Judge model output validation failures (scores outside the standard range), calculate the failure rate, and record it as a metric in `data/derived/judge_metrics.json` (SC‑005).
- [X] T030 [US3] Implement `src/services/experiment_runner.py` to run target model under Coarse, Fine, and Hybrid conditions. Explicitly construct "Coarse Context", "Fine Context", and "Hybrid Context" strings as per Spec definitions. **Constraint**: Must handle timeouts per Edge Cases. **Depends on**: T029, T029a.
- [X] T031 [US3] Implement timeout handling inside `experiment_runner`: if a single probe generation exceeds the timeout, log the failure, assign a default consistency score of 0, and continue to the next probe.
- [X] T032 [US3] Instrument `experiment_runner` and `stats_engine` to capture, log, and report the total wall‑clock time of the full experiment run to `data/derived/timing.log`. Read CI time limit from environment variable `CI_TIME_LIMIT_SECONDS` (fallback to a timeout duration of several hours). If cumulative elapsed time exceeds this limit, raise `SystemExit()` to fail the CI job.
- [X] T033 [US3] Implement `check_normality(scores)` in `src/analysis/stats_engine.py` to perform Shapiro‑Wilk test on the residuals of the `judge_score` field from `data/derived/results_raw.jsonl` (NOT aggregated) and return `is_normal` (bool). **Constraint**: This MUST run before any aggregation. **Depends on**: T026, T030.
- [X] T034 [US3] Implement `select_statistical_test(is_normal)` in `src/analysis/stats_engine.py` to return the test type ('anova' or 'friedman') based on `is_normal`.
- [X] T035 [US3] Implement `run_statistical_test(scores, test_type)` in `src/analysis/stats_engine.py` to execute the chosen statistical test (ANOVA or Friedman) and write the p‑value, effect size, mean scores, and variance to `data/derived/stats_results.json` (FR-005, SC-004). **Depends on**: T033, T034.
- [X] T035b [US3] Extend `run_statistical_test` to calculate the variance of consistency scores across the three conditions and include it in `stats_results.json`. **Logic**: Calculate the variance for Coarse, Fine, and Hybrid conditions. Compute the ratio `hybrid_variance / coarse_variance`. **Constraint**: Do NOT apply a pass/fail threshold. **Output**: Write the calculated variances and the ratio to `stats_results.json` as descriptive metrics for assessment. **Depends on**: T035.
- [X] T027a-agg [US3] Implement `aggregate_consistency_scores` in `src/analysis/stats_engine.py` to combine the Judge score (T026) and rule-based scores (T027) into a single 'Consistency Score' artifact. Write final aggregated scores to `data/derived/results_final.jsonl`. **Constraint**: **This task is ONLY for post-hoc reporting and MUST NOT be called before T035**. **Depends on**: T028, T026, T027, T030, T035.
- [X] T029b [US3] Implement `validate_against_gold_standard(results, gold_data)` in `src/analysis/stats_engine.py` to compute correlation/error metrics against `data/gold_standard/human_annotations.json` and ensure the evaluation is not circular. **Depends on**: T027a-agg.
- [X] T036 [P] Add CLI entry point in `src/cli/run_experiment.py` to trigger the full experiment pipeline. **Constraint**: Must perform pre-flight checks: 1) Verify `data/raw/arcane_corpus.jsonl` exists (T013). 2) Verify `data/derived/probes.jsonl` exists (T021). 3) Verify `data/gold_standard/human_annotations.json` exists (T009a). If any fail, exit with code 1 and clear error.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037a [P] Update `specs/001-llmxive-follow-up-extending-arcane-do-ro/quickstart.md` with new CLI flags from T036 and data formats from T010.
- [ ] T037b [P] Update `README.md` with new data formats and execution instructions.
- [ ] T037c [P] Create `specs/001-llmxive-follow-up-extending-arcane-do-ro/quickstart.md` with step-by-step instructions for running the experiment, referencing T036 and T013.
- [ ] T038a Code cleanup: Refactor error handling to be consistent across all services. **Target Pattern**: Replace all bare `except:` with custom `ExperimentError` exceptions. **Files**: `src/services/*.py`, `src/cli/*.py`.
- [ ] T038b Code cleanup: Refactor logging calls to use standardized format.
- [ ] T040 [P] Additional unit tests for statistical engine edge cases in `tests/unit/test_stats_engine.py`
- [ ] T041 Run `quickstart.md` validation to ensure end‑to‑end reproducibility on CPU
- [ ] T046 [P] **Update Research Docs**: Update `specs/001-llmxive-follow-up-extending-arcane-do-ro/research.md` and `plan.md` to explicitly state the exact public domain URLs used for T013, the method for generating T009a, and the actual N value calculated from `data/derived/results_final.jsonl` at runtime.
- [ ] T051 [P] **Add Statistical Power Analysis Placeholder**: Create `src/analysis/power_analysis.py` with a docstring containing the assumptions regarding sample size (N ≥ 150) and effect size used in the plan. This task serves as a placeholder for future work to refine the sample size calculation based on pilot run results.
- [ ] T052 [P] **Add Pre-flight Data Integrity Check**: Create `src/cli/check_data_integrity.py` to verify the existence and checksums of all required input artifacts (`data/raw/arcane_corpus.jsonl`, `data/derived/probes.jsonl`, `data/gold_standard/human_annotations.json`) before the main experiment runner (T036) is invoked. This ensures the execution order is respected and prevents running on missing or corrupted data.

---

## Phase 7: Revision & Analysis Resolution

**Purpose**: Address specific concerns raised by `/speckit.analyze` regarding data integrity, CPU feasibility, and task ordering.

- [X] T045 [P] **Verify CPU Feasibility**: Add a pre-flight check script `scripts/check_cpu_feasibility.py` that attempts to load the target model (Phi-mini/TinyLlama) in quantized mode and the embedding model on the target CI runner specs (cores, 7GB RAM). If memory error occurs, log a warning and suggest GPU offload (though the plan assumes CPU).
- [X] T053 [P] **Enforce Strict Data Flow Ordering**: Update `src/cli/run_experiment.py` (T036) to enforce a strict execution sequence: 1) Verify T013 (Source Text) exists. 2) Verify T009a (Gold Standard) exists. 3) Verify T021 (Probes) exists. 4) Verify T029 (Calibration) has passed. **Constraint**: If T013 fails, the system MUST abort immediately with "Source text missing. Run T013 first." **NO** fallback to synthetic data. This task resolves the "data flow" violation where verification might run before data generation.
- [X] T054 [P] **Add Explicit "Fail Loudly" Logic to Data Loaders**: Refactor `src/lib/stream_loader.py` (T049) and `src/services/axis_validator.py` (T012) to ensure that any failure to fetch real data or validate real axes raises a `DataFetchError` exception immediately. **Constraint**: Remove any `try/except` blocks that silently fallback to `generate_synthetic_*()` or mock data. **Distinction**: This task applies to DATA FETCH failures. Runtime execution failures (timeouts, generation limits) are handled gracefully by T031 and T020 as per the Spec's Edge Cases. This task resolves the "silent synthetic fallback" risk identified in the rules.
- [X] T055 [P] **Add Real Dataset Streaming Verification**: Extend T049 (Stream Loader) to include a unit test that verifies the `streaming=True` parameter is correctly passed to `datasets.load_dataset` and that the generator yields chunks without loading the entire file into memory. **Constraint**: This test must fail if the implementation attempts to load the full dataset into RAM. This task ensures compliance with the "Large real datasets: STREAM" rule.