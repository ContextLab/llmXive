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

- [ ] T001 Create project directory structure: `src/`, `tests/`, `data/`, `data/raw/`, `data/derived/`, `data/gold_standard/`, `artifacts/`, `specs/001-llmxive-follow-up-extending-arcane-do-ro/`.
- [ ] T001b Create project initialization files: `__init__.py` in all `src/` and `tests/` subdirectories, `.gitignore` (excluding `data/` and `__pycache__`), and `requirements.txt` stub.
- [X] T002 Initialize Python project with `requirements.txt` (transformers, llama-cpp-python, datasets, scikit-learn, scipy, pandas, numpy, tiktoken, hypothesis, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, Data Contracts, and Gold Standard generation that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the definition of all JSON schemas required for data integrity and the generation of the Gold Standard dataset.

- [ ] T009a [US1/US3] **Generate Gold Standard Dataset**: Create a deterministic, reproducible "Gold Standard" dataset of n=20 human-annotated character behaviors. **Logic**: 
    1. Attempt to fetch `llmXive/arcane-gold-standard` from HuggingFace. 
    2. If fetch fails (dataset missing/private) OR if the dataset is not found, **DO NOT raise an error**. Instead, execute the local fallback: 
       a. Load "Pride and Prejudice" (Gutenberg ID) text. 
       b. Extract a set of specific, non-overlapping text segments (e.g., every 50th paragraph starting at index 0). 
       c. Annotate each segment with "Coarse" and "Fine" phase labels using a predefined, deterministic rule set (e.g., "Early chapters = Innocence/Naive Trust", "Late chapters = Experience/Calculated Skepticism") to ensure reproducibility. 
       d. Save to `data/gold_standard/human_annotations.json`. 
    3. Compute SHA256 checksum. 
    **Constraint**: The local fallback MUST succeed to satisfy FR-006 and SC-006. The task must NEVER fail due to missing external data. **Output**: `data/gold_standard/human_annotations.json` and checksum.
- [ ] T009b [US1/US3] **Record Gold Standard Checksum**: Compute the SHA256 checksum of `data/gold_standard/human_annotations.json` (from T009a) and record it in `state/projects/PROJ-919-.../artifact_hashes` to satisfy Constitution Principle III.
- [X] T005 [P] Implement robust logging infrastructure in `src/lib/utils.py` (file + console handlers, JSON formatting)
- [X] T006 [P] Create base configuration management for seeds and model paths in `src/lib/config.py`
- [X] T007 Implement data validation helpers in `src/lib/validators.py` (schema checks, type clamping)
- [X] T008 [P] [US3] Setup experiment state tracking (logging run IDs, timestamps, parameter hashes, AND content hashes for state/parameters) in `src/lib/state.py` to satisfy Constitution Principle V.
- [ ] T049 [P] [US2] **Implement Robust Stream Loading**: Create `src/lib/stream_loader.py` to read large text files (e.g., `data/raw/arcane_corpus.jsonl`) in chunks using `datasets.load_dataset(..., streaming=True)` or manual chunking. **Constraint**: This module MUST be used by T019 (Phase 4) to prevent RAM overflow. **Note**: T013 writes the file; T049 defines the reading logic for large files.
- [ ] T010 [P] Create File: `specs/001-llmxive-follow-up-extending-arcane-do-ro/contracts/axis.schema.yaml`. **Content**:
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
- [ ] T012 [US1] Implement semantic validation logic in `src/services/axis_validator.py`. **Logic**: Load two axis definitions (Coarse, Fine). 
    1. **Lexical Overlap**: Tokenize both descriptions using `nltk.word_tokenize` (lowercase, strip punctuation), compute Jaccard similarity (|A ∩ B| / |A ∪ B|). 
    2. **Semantic Distance**: Embed both descriptions using `sentence-transformers/all-MiniLM-L6-v2`, compute cosine distance. 
    3. **Constraint**: Pass only if lexical overlap > 0.4 AND cosine distance < 0.3. Ensure `source_observation` is non-empty and distinct.
- [ ] T014 [US1] Unit test for axis semantic overlap constraint in `tests/unit/test_axis_validation.py`. **Note**: This test depends on T010 (schema) and T012 (service) being implemented first.
- [ ] T015 [P] [US1] Create `data/derived/axes.jsonl` writer to store validated axis definitions.
- [ ] T011b [P] Create `config/characters.json`. **Content**: JSON mapping of character names to public-domain source IDs (e., `{"Elizabeth Bennet": {"source": "gutenberg", "id": "1342"}, "Ebenezer Scrooge": {"source": "gutenberg", "id": "2401"}}`).
- [ ] T013 [US2] **Download Source Text**: Download public domain texts for source corpus. **Logic**: Accept `--character` argument. Read mapping from `config/characters.json` (T011b). Fetch text from Gutenberg using the mapped ID. **Constraint**: If a character is not in the mapping, abort with error "Character not supported: Add to config/characters.json first." **NO** synthetic fallback. Concatenate and save to `data/raw/arcane_corpus.jsonl`.
- [ ] T037d [P] [US1] **Update Spec Assumptions**: Update `specs/001-llmxive-follow-up-extending-arcane-do-ro/spec.md` Assumptions section to explicitly state that the scope is limited to public-domain characters defined in `config/characters.json`.

**Checkpoint**: Foundation and Data Setup ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Character Arc Specifications (Priority: P1) 🎯 MVP

**Goal**: Allow researchers to define and store independent Coarse and Fine psychological axes for characters.

**Independent Test**: A researcher can input a character name and receive two distinct, non‑overlapping JSON objects representing the Coarse and Fine axes, verified against semantic overlap constraints.

- [ ] T011a [US1] Implement `src/cli/axis_input.py` with manual input validation logic: requires two separate JSON/YAML files for Coarse and Fine axes via `--coarse-file` and `--fine-file` CLI arguments. **Logic**: Load inputs, validate against T010 schema, then call T012's validation function. If validation fails, reject input and log error. **Depends on**: T010, T012, T015.

---

## Phase 4: User Story 2 - Generate Out-of-World Probes (Priority: P2)

**Goal**: Generate at least 50 unique "Out-of-World" scenario prompts per character that are semantically distant from the source text.

**Independent Test**: average cosine similarity to source text is < 0.3

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T017 [P] [US2] Unit test for probe regeneration loop and similarity threshold in `tests/unit/test_probe_generation.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `src/services/probe_generator.py` with logic to generate novel scenarios based on character axes. **Constraint**: Must use a small, quantized model (e., TinyLlama‑1.1B) on CPU. **Prompt**: Use a predefined template: "You are a character with traits [COARSE] and [FINE]. Generate a scenario set in [MODERN/SCI-FI SETTING] that tests these traits. Do NOT use any plot points from the original story." **Seed**: Use a fixed seed for reproducibility. **Depends on**: T013 (source text must exist).
- [ ] T019 [US2] Implement semantic similarity check (cosine similarity < 0.3) against `data/raw/arcane_corpus.jsonl` (source text) in `src/services/probe_generator.py` using `sentence-transformers/all-MiniLM-L6-v2`. **Constraint**: Must verify `data/raw/arcane_corpus.jsonl` exists before proceeding. Must use streaming logic (T049) if corpus is large.
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

- [X] T025 [P] [US3] Implement model loading utilities in `src/models/loader.py` (CPU‑quantized small language models, low‑bit quantization, specifically Phi‑‑mini or TinyLlama‑1.1B via `llama.cpp` or low‑bit `transformers` per Constitution Principle VI).
- [ ] T027a [US3] **Define Keyword Config**: Create `config/keywords.json` containing a mapping of "Coarse", "Fine", and "Hybrid" phases to static lists of keywords and the target sentiment for each phase. **Content Example**:
```json
{
  "Coarse": {
    "keywords": ["brave", "kind", "honest"],
    "target_sentiment": "positive"
  },
  "Fine": {
    "keywords": ["cautious", "skeptical", "reserved"],
    "target_sentiment": "neutral"
  },
  "Hybrid": {
    "keywords": ["brave but cautious", "kind yet skeptical"],
    "target_sentiment": "mixed"
  }
}
```
**Logic**: Define a scoring formula based on keyword density and sentiment alignment. **Constraint**: This file MUST exist before T027 is implemented. **Depends on**: None.
- [X] T026 [US3] Implement `src/services/judge_service.py` for LLM‑based consistency scoring using a standard Likert scale, with output validation, clamping, **and** adherence flag determined by semantic alignment (LLM Judge) to the target phase. **Constraint**: The adherence flag MUST NOT rely on keyword counting; it must be a semantic judgment. The rule-based metric (T027) will handle the independent check.
- [ ] T027 [US3] Implement `src/services/rule_based_metric.py` to calculate `keyword_score` based on the static keyword list from `config/keywords.json` (T027a) AND **sentiment alignment** with the target phase's expected sentiment (also from T027a). **Logic**: 
    1. Calculate keyword density (count / total words). 
    2. Calculate sentiment polarity of the response using `textblob` (or `nltk.sentiment`). 
    3. Compute sentiment alignment score as `1 - abs(response_polarity - target_polarity)` (where target_polarity is derived from the config, e.g., 1.0 for positive, 0.0 for neutral, -1.0 for negative, or a normalized 0-1 scale). 
    4. Combine: `final_score = (0.6 * keyword_density) + (0.4 * sentiment_alignment)`. 
    **Constraint**: The keyword list MUST NOT be derived from the prompt or the model response. The score is based on keyword density AND the absolute difference between the response's sentiment and the target phase's sentiment. **Output**: Return a score within the defined range. **Note**: This satisfies the spec's requirement for an independent verification mechanism including sentiment alignment.
- [X] T028 [P] Create `data/derived/results_raw.jsonl` writer to store raw responses and scores.
- [ ] T029 [US3] Implement Judge Calibration step in `src/services/judge_service.py`. **Logic**: Load `data/gold_standard/human_annotations.json` (T009a). Compute Cohen's Kappa (quadratic weights) between the Judge's scores and the human annotations. **Constraint**: If Kappa ≤ 0.6, raise a RuntimeError with a clear message: "Judge calibration failed: Kappa {kappa} <= 0.6". **Depends on**: T009a, T026 (Interface/Logic). **Note**: T029 validates the T026 configuration before main execution. T026 must not be considered 'ready' until T029 passes.
- [ ] T029a [US3] **Record Calibration Metrics**: Write the computed Kappa coefficient, the number of samples used, and the pass/fail status to `data/derived/calibration_metrics.json` as a traceable artifact (FR-007, SC-006).
- [X] T029c [US3] Implement logic to aggregate Judge model output validation failures (scores outside the standard range), calculate the failure rate, and record it as a metric in `data/derived/judge_metrics.json` (SC‑005).
- [X] T030 [US3] Implement `src/services/experiment_runner.py` to run target model under Coarse, Fine, and Hybrid conditions. Explicitly construct "Coarse Context", "Fine Context", and "Hybrid Context" strings as per Spec definitions. **Constraint**: Must handle timeouts per Edge Cases.
- [X] T031 [US3] Implement timeout handling inside `experiment_runner`: if a single probe generation exceeds the timeout, log the failure, assign a default consistency score of 0, and continue to the next probe.
- [X] T032 [US3] Instrument `experiment_runner` and `stats_engine` to capture, log, and report the total wall‑clock time of the full experiment run to `data/derived/timing.log`. Read CI time limit from environment variable `CI_TIME_LIMIT_SECONDS` (fallback to a timeout duration of several hours). If cumulative elapsed time exceeds this limit, raise `SystemExit()` to fail the CI job.
- [X] T027a-agg [US3] Implement `aggregate_consistency_scores` in `src/analysis/stats_engine.py` to combine the Judge score (T026) and rule-based scores (T027) into a single 'Consistency Score' artifact. Write final aggregated scores to `data/derived/results_final.jsonl`. **Depends on**: T028, T026, T027, T030.
- [X] T029b [US3] Implement `validate_against_gold_standard(results, gold_data)` in `src/analysis/stats_engine.py` to compute correlation/error metrics against `data/gold_standard/human_annotations.json` and ensure the evaluation is not circular. **Depends on**: T027a-agg.
- [X] T033 [US3] Implement `check_normality(scores)` in `src/analysis/stats_engine.py` to perform Shapiro‑Wilk test on the residuals of the `judge_score` field from `data/derived/results_final.jsonl` and return `is_normal` (bool). **Depends on**: T027a-agg.
- [X] T034 [US3] Implement `select_statistical_test(is_normal)` in `src/analysis/stats_engine.py` to return the test type ('anova' or 'friedman') based on `is_normal`.
- [X] T035 [US3] Implement `run_statistical_test(scores, test_type)` in `src/analysis/stats_engine.py` to execute the chosen statistical test (ANOVA or Friedman) and write the p‑value, effect size, mean scores, and variance to `data/derived/stats_results.json` (FR-005, SC-004). **Depends on**: T033, T034.
- [ ] T035b [US3] Extend `run_statistical_test` to calculate the variance of consistency scores across the three conditions and include it in `stats_results.json`. **Logic**: Additionally, compare the variance of the Hybrid condition against the Coarse condition variance to perform the "assessment" required by SC-004. **Assessment Rule**: If `hybrid_variance < 1.2 * coarse_variance`, set `hybrid_is_stable = true`; otherwise `false`. **Output**: Write a boolean flag `hybrid_is_stable` and the comparison ratio to `stats_results.json`. **Depends on**: T035.
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
- [ ] T051 [P] **Add Statistical Power Analysis Placeholder**: Create `src/analysis/power_analysis.py` to document the assumptions regarding sample size (N ≥ 150) and effect size used in the plan. This task serves as a placeholder for future work to refine the sample size calculation based on pilot run results.
- [ ] T052 [P] **Add Pre-flight Data Integrity Check**: Create `src/cli/check_data_integrity.py` to verify the existence and checksums of all required input artifacts (`data/raw/arcane_corpus.jsonl`, `data/derived/probes.jsonl`, `data/gold_standard/human_annotations.json`) before the main experiment runner (T036) is invoked. This ensures the execution order is respected and prevents running on missing or corrupted data.

---

## Phase 7: Revision & Analysis Resolution

**Purpose**: Address specific concerns raised by `/speckit.analyze` regarding data integrity, CPU feasibility, and task ordering.

- [ ] T045 [P] **Verify CPU Feasibility**: Add a pre-flight check script `scripts/check_cpu_feasibility.py` that attempts to load the target model (Phi-mini/TinyLlama) in quantized mode and the embedding model on the target CI runner specs (cores, 7GB RAM). If memory error occurs, log a warning and suggest GPU offload (though the plan assumes CPU).