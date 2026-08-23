# Tasks: Phenomenological AI: First-Person Experience Modeling

**Input**: Design documents from `/specs/592-phenomenological-ai-first-person-experie/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[D]**: Dependent (must wait for specific prior tasks)
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

- [X] T001 [P] Write `scripts/init_project.py` script to scaffold directories: `code/`, `data/raw/`, `data/processed/`, `data/qualitative/`, `tests/unit/`, `tests/integration/`, `specs/contracts/`. **Execution**: Run `python scripts/init_project.py` to verify completion.
- [X] T002 [P] Create `.gitignore` (exclude `data/`, `*.pyc`, `__pycache__`) and `.github/workflows/ci.yml` (basic lint/test trigger). **Verification**: Run `ls -la.gitignore.github/workflows/ci.yml` and verify `.gitignore` contains `data/` and `*.pyc`, and `ci.yml` contains `pytest` trigger.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **Deliverable**: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Verification**: Run `ruff check. --exit-zero` and `black --check.`; verify exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with:
 1. Seeds, paths, and model IDs (Primary: `TheBloke/TinyLlama-Chat-v-GGUF` for CI; Secondary: `mistralai/Mistral-7B-Instruct-v0.2` for GPU-offload).
 2. **Phenomenological Marker Dictionaries**: Define concrete lists for 'sensory' (e.g., see, hear, feel, touch, taste, smell, light, sound), 'temporal' (e.g., now, then, before, after, moment, duration), and 'intentional' (e.g., think, believe, desire, intend, perceive, experience) keywords as per FR-008 and FR-009.
 **Verification**: Run `python -c "from code.config import MARKER_DICTS; assert 'sensory' in MARKER_DICTS and len(MARKER_DICTS['sensory']) > 0"`; verify exit code 0.
- [X] T005 [P] Setup `code/utils/logging.py` for structured logging, warning capture, and retry logic (multiple attempts per sample)
- [X] T006 [P] Implement `code/utils/io.py` for JSON/CSV schema validation and artifact archiving. **CLI**: Expose `python -m code.utils.io --validate-schema <file> <schema>`. **Verification**: Run `python -m code.utils.io --validate-schema data/test.json specs/contracts/test.schema.yaml`; verify exit code 0.
- [X] T007 [P] Create base data schemas in `specs/contracts/`: `specs/contracts/generation_output.schema.yaml`, `specs/contracts/validity_scores.schema.yaml`, `specs/contracts/qualitative_ratings.schema.yaml`
- [X] T008 [US1] Implement `code/generation/prompt_engineering.py` with the defined strategies (Direct, Hypothetical, Comparative, Role-play) and A set of base prompts loaded from `data/prompts/base_prompts.json`. **Deliverable**: Create `data/prompts/base_prompts.json` with a set of prompts. **Dependency**: T004 (for marker logic). **Execution**: Verify prompts are loaded correctly. **Verification**: Run `python -m code.generation.prompt_engineering --verify`; verify the process completes successfully and the output confirms that prompts were loaded.
- [X] T020 [P] [US3] **Create** `code/validation/rubric.md`: Author the independent validation rubric document required by FR-010. **Content**: Define clear criteria for human raters: 1) Coherence (logical flow), 2) Marker Density (presence of sensory/temporal/intentional markers), 3) Structural Integrity (adherence to first-person perspective). **Verification**: Run `grep -c "Coherence" code/validation/rubric.md` and `grep -c "Marker Density" code/validation/rubric.md` and `grep -c "Structural Integrity" code/validation/rubric.md`; verify all return >= 1.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Report Generation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate the corpus of phenomenological reports using CPU-tractable models and four prompting strategies.

**Independent Test**: Execute `code/generation/runner.py` and verify `data/raw/` contains ≥80 samples per prompt per strategy (totaling a substantial number per strategy) with valid JSON metadata (seed, prompt, strategy) and no CUDA errors.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/generation/runner.py` using `llama-cpp-python` for `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF` (specifically `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`) on CPU-only environment (FR-002). **Constraint**: This is the ONLY model for the primary CI path due to limited hardware constraints. Target volume: ≥80 samples **per prompt** per strategy (prompts × 80 = 1600 per strategy). **Note**: The second checkpoint (Mistral-7B/Llama-7B) is handled in T009b via GPU offload. **Verification**: Run `python -c "import json, glob, os; data=[json.load(open(f)) for f in glob.glob('data/raw/generation_batch_*.json')]; counts={s: {p: sum(1 for d in data if d['strategy']==s and d['prompt_id']==p) for p in set(d['prompt_id'] for d in data)} for s in set(d['strategy'] for d in data)}; assert all(all(c>=80 for c in p_counts.values()) for p_counts in counts.values()), f'Missing: {counts}'"`. Ensure ≥80 samples per prompt per strategy. <!-- FAILED: unspecified -->
- [X] T009a [US1] Extend `runner.py` to support the full set of 20 prompts defined in `data/prompts/base_prompts.json` and iterate through all of them for each strategy. **Dependency**: T009. **Verification**: Run `python -c "import json, glob; files=[f for f in glob.glob('data/raw/generation_batch_*.json') if 'TinyLlama' in f]; assert len(files) >= 80*4*20, f'Expected a substantial volume of files, got {len(files)}'"`. <!-- ATOMIZE: requested -->
- [X] T009b [US1] **Implement GPU-Offload Generation**: Create `code/generation/runner_gpu.py` to generate samples using `mistralai/Mistral-7B-Instruct-v0.2` (or equivalent 7B model) via `llama-cpp-python` with `device="cuda"` and -bit quantization. **Constraint**: This task is designed to be executed on a free-tier GPU runner (Kaggle) when the CPU runner detects a CUDA requirement. **Target**: ≥80 samples per prompt per strategy (1600 per strategy) for the second checkpoint. **Dependency**: T009 (logic reuse). **Verification**: Run `python -c "import json, glob; files=[f for f in glob.glob('data/raw/generation_batch_*.json') if 'Mistral' in f]; assert len(files) >= 80*4*20, f'Expected a substantial volume of files, got {len(files)}'"`.
- [X] T010 [US1] Implement retry logic in `runner.py`: Implement a fixed number of attempts per prompt/strategy combination with exponential backoff (increasing intervals). Mark samples as missing only after a consecutive series of failures. **Deliverable**: Create `tests/unit/test_retry.py`. **Verification**: Run `pytest tests/unit/test_retry.py::test_retry_logic` which mocks a timeout on an initial sequence of attempts; verify log contains "Retry 1", "Retry 2", "Success".
- [ ] T011 [US1] Create `code/generation/control_corpus.py` to generate ≥80 control samples using `datasets.load_dataset('tech_reports')` (or similar technical report dataset) with a 'Technical' prompting strategy. **Logic**: Append `type=control` to each sample. Merge with phenomenological outputs into `data/processed/merged_dataset.csv` for downstream analysis (discriminant validity per Plan Complexity Tracking). **Dependency**: T009, T009b. **Additional Verification**: Verify the control corpus lacks phenomenological markers (sensory, temporal, intentional) using `code/config.py` dictionary. **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/processed/merged_dataset.csv'); assert 'type' in df.columns and (df['type']=='control').any()"`. Verify file exists and contains "control" rows with non-null scores.
- [ ] T013 [US1] Add timeout handling and sample-size logging to `runner.py`. **Logic**: Implement a timeout per generation. Log sample counts (success/fail) to `data/raw/generation_log.json`. **Dependency**: Depends on T009 completion. **Verification**: Run `python -c "import json; log=json.load(open('data/raw/generation_log.json')); assert log['total']==log['success']+log['fail']"`. Verify log file exists and counts sum correctly.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3b: Local Reproduction (Optional)

**Goal**: Provide a script for users with local hardware (≥16GB RAM) to run larger models (Phi-2) for optional validation, NOT for the primary CI path.

- [ ] T012 [US1-Optional] Implement `code/generation/runner_local.py` for the second checkpoint (`microsoft/phi` 2.7B) using `llama-cpp-python` with -bit GGUF (`phi-2.Q4_K_M.gguf`). **Note**: This script is OPTIONAL and for local reproduction only. It is NOT part of the primary CI pipeline. **Verification**: Run `python code/generation/runner_local.py --test`; verify `data/raw/local_generation_test.json` exists with a representative sample.

---

## Phase 4: User Story 2 - Phenomenological Metric Computation (Priority: P2)

**Goal**: Compute Internal Consistency, Semantic Stability, and Marker Presence metrics, then perform statistical analysis.

**Independent Test**: Run `code/analysis/stats.py` on a small subset of reports and verify `data/processed/validity_scores.csv` contains non-null scores for all three metrics and correct statistical test outputs.

### Implementation for User Story 2

- [X] T014 [US2] Implement `code/analysis/consistency.py`: Load NLI model `cross-encoder/stsb-distilroberta-base` (CPU-safe), compute pairwise contradiction counts, handle length limits by skipping pairs with warnings (US-2 Edge Case). **Deliverable**: Create `tests/unit/test_consistency.py`. **Verification**: Run `pytest tests/unit/test_consistency.py::test_pairwise_contradiction` with a known input string; verify output matches expected contradiction count.
- [X] T015 [US2] Implement `code/analysis/stability.py`: Compute embeddings for repeated generations, calculate cosine similarity, and store stability scores. **Deliverable**: Create `tests/unit/test_stability.py`. **Verification**: Run `pytest tests/unit/test_stability.py::test_cosine_similarity` with known embeddings; verify output matches expected similarity score within tolerance sufficiently small to ensure numerical stability.
- [ ] T016 [US2] Implement `code/analysis/markers.py`: Load the keyword dictionary defined in `code/config.py` (T004) to count sensory, temporal, and intentional markers (FR-008). **Deliverable**: Create `tests/unit/test_markers.py`. **Dependency**: Requires T004 (Phase 2). **Verification**: Run `pytest tests/unit/test_markers.py::test_count_keywords` with a known text; verify output matches expected count.
- [ ] T017 [US2] Implement `code/analysis/fdr_correction.py` and `code/analysis/tukey_hsd.py` for Benjamini-Hochberg FDR and Tukey HSD post-hoc tests (FR-005). **Deliverable**: Create `tests/unit/test_stats.py`. **Verification**: Run `pytest tests/unit/test_stats.py::test_fdr_correction` with known p-values; verify output matches expected adjusted p-values.
- [ ] T018 [US2] Implement `code/analysis/stats.py` to orchestrate metric aggregation. **Logic**: Run Shapiro-Wilk and Levene tests (FR-012). **CRITICAL**: If assumptions (p≥0.05) hold, run ANOVA + FDR + Tukey. **IF VIOLATED**: Run Kruskal-Wallis **INSTEAD** of ANOVA and **SKIP** FDR/Tukey (as they are parametric corrections). Report the violation and the non-parametric result. **Verification**: Run `python code/analysis/stats.py --input data/processed/merged_dataset.csv --output data/processed/stats_report.json`; verify `data/processed/stats_report.json` exists, contains either parametric OR non-parametric results (not both if assumptions fail), and the input CSV has a 'type' column.
- [ ] T019 [US2] Implement `code/analysis/sensitivity_analysis.py` to test validity score weights (FR-006) by varying weights across a range from a low threshold to a high threshold and analyzing robustness across sample subsets. **Justification**: Output a report justifying the fixed weights used in the Constitution based on sensitivity results. **Verification**: Run `python code/analysis/sensitivity_analysis.py --weights [low_value, mid_value, high_value]`; verify `data/processed/sensitivity_report.md` exists and contains a table of results for the tested weights.
- [ ] T024 [US2] Implement `code/main.py` to orchestrate the full pipeline: Generation → Metrics → Stats. **CLI**: `python main.py --mode generation|analysis|validate --config config.yaml --output data/processed`. **Input**: `data/processed/merged_dataset.csv` (from T011). **Dependency**: T011, T014, T015, T016, T017, T018, T019. **Verification**: Run `python code/main.py --mode generation --limit --config config.yaml`; verify exit code 0 and `data/processed/validity_scores.csv` contains 5 rows.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Qualitative Validation & Reproducibility (Priority: P3)

**Goal**: Facilitate human evaluation, compute inter-rater reliability, and archive all artifacts.

**Independent Test**: Verify `data/qualitative/` contains anonymized rating sheets, `code/validation/human_rater.py` calculates Cohen's κ correctly, and the archive script commits all artifacts.

### Implementation for User Story 3

- [ ] T026 [US3] Perform Power Analysis and Sample Size Determination for SC-002. **Logic**: Calculate minimum sample size required to achieve κ≥0.6 with [deferred] power. **Deliverable**: Create `data/qualitative/power_analysis_report.md`. **Verification**: Run `python code/validation/power_analysis.py`; verify `data/qualitative/power_analysis_report.md` exists and contains a calculated sample size ≥10 per condition.
- [ ] T023 [US3] Create `code/validation/stratified_sampler.py` to select a representative set of reports per condition for human rating (SC-002). **Logic**: Select a representative sample of reports per condition using stratified random sampling based on prompt strategy. **Dependency**: T009, T009b, **T026** (for sample size 'n'). **Constraint**: Must enforce exactly **10 reports per condition** (strategy). **Verification**: Run `python code/validation/stratified_sampler.py --n 10`; Verify `data/qualitative/sampling_list.csv` exists and contains a representative number of rows per strategy (Direct, Hypothetical, Comparative, Role-play). Run `python -c "import pandas as pd; df=pd.read_csv('data/qualitative/sampling_list.csv'); counts=df['strategy'].value_counts(); assert all(c==10 for c in counts.values()), f'Expected 10 per strategy, got {counts}'"`.
- [ ] T021 [US3] Implement `code/validation/human_rater.py` to load generated reports, apply independent validation rubric from `code/validation/rubric.md` (FR-010), and store ratings. **Dependency**: Depends on T020 (rubric creation) and T023 (sampling list). **Verification**: Run `python -m code.utils.io --validate-schema data/qualitative/ratings_test.csv specs/contracts/qualitative_ratings.schema.yaml`; verify `data/qualitative/ratings_test.csv` exists and schema matches `specs/contracts/qualitative_ratings.schema.yaml`.
- [ ] T022 [P] [US3] Implement Cohen's κ calculation and threshold sensitivity analysis in `code/analysis/sensitivity_kappa.py`. **Logic**: Analyze robustness of conclusions across a range of kappa thresholds per FR-011. **Constraint**: If κ < 0.6, trigger the mandatory re-evaluation workflow: select new samples and re-instruct raters via the rubric. **Dependency**: T021. **Verification**: Run `python code/analysis/sensitivity_kappa.py --kappa 0.5`; verify `data/qualitative/flags.json` exists and contains a "re-evaluate" flag for the test batch with the schema `{"flag": "re-evaluate", "action": "re-rate"}`.
- [ ] T025 [P] [US3] Implement `code/utils/archiver.py` to package prompts, seeds, scripts, and anonymized ratings for public reproducibility (FR-007). **Verification**: Run `python code/utils/archiver.py --output archive.zip`; verify `archive.zip` exists and contains `code/`, `data/prompts/`, `data/qualitative/ratings.csv` by running `unzip -l archive.zip | grep -E "code/|data/prompts/|data/qualitative/ratings.csv"`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review-Driven Enhancements (Priority: P2)

**Goal**: Address specific philosophical and methodological concerns raised by reviewers (Turing, Rockmore, Kahneman, Krakauer, Dyson) regarding operational tests, stylistic distinction, debiasing, and incoherence.

- [ ] T030a [P] Add CLI usage examples and environment setup instructions to `quickstart.md`. **Examples**: Document `python main.py --mode generation`, `python main.py --mode analysis`, `python main.py --mode validate`. **Verification**: Run `grep -c "python main.py --mode generation" quickstart.md` and verify it returns >= 1. **Note**: This task is currently incomplete; verification must confirm file is non-empty.
- [X] T031a [P] Refactor `code/analysis/stats.py` to add type hints and remove duplicate imports. **Verification**: Run `ruff check code/analysis/stats.py`; verify exit code 0.
- [X] T031b [P] Refactor `code/utils/logging.py` to standardize log levels and output formats. **Verification**: Run `ruff check code/utils/logging.py`; verify exit code 0.
- [X] T032 [P] Add unit tests in `tests/unit/`: specifically `tests/unit/test_markers.py::test_count_sensory_keywords`, `tests/unit/test_consistency.py::test_pairwise_contradiction`. **Verification**: Run `pytest tests/unit/test_markers.py::test_count_sensory_keywords tests/unit/test_consistency.py::test_pairwise_contradiction`; verify all tests pass.
- [ ] T033a [P] Create `config.yaml` with all necessary parameters for the pipeline. **Deliverable**: Create `config.yaml` in the root. **Verification**: Run `python -c "import yaml; yaml.safe_load(open('config.yaml')); print('Content verified')"`. Verify exit code 0 and file is non-empty.
- [ ] T033 [P] Run `quickstart.md` validation to ensure full pipeline execution ≤6 hours on free-tier. **Dependency**: T033a, T030a. **Verification**: Run `time python code/main.py --mode generation --limit 100 --config config.yaml`; verify exit code 0 and total time < 6h (simulated by limit).
- [D] T034 [P] [US2] **Implement Turing-Style Operational Test (Exploratory)**: Create `code/analysis/turing_test.py` to evaluate the "indistinguishability" criterion (Turing Review). **Logic**: Generate a mixed corpus of human-written phenomenological reports (from a small, verified public dataset or synthetic human-like samples for testing) and LLM reports. Implement a classifier (e.g., logistic regression or simple SVM) to predict origin. Report the accuracy; if accuracy is near chance ([deferred]), the model sustains the "fiction" effectively. **Note**: This is **SUPPLEMENTARY** and does **NOT** replace FR-010 (Human Qualitative Auditing). **Dependency**: T009, T009b, T024. **Verification**: Run `python code/analysis/turing_test.py --n 100`; verify `data/processed/turing_accuracy.json` exists and contains a key `accuracy` as a float.
- [D] T035 [P] [US2] **Implement "Experience Trace" Visualization**: Create `code/analysis/experience_trace.py` to map model latent states to phenomenological categories (Rockmore Review). **Logic**: Use attention head visualization or embedding projection (t-SNE/UMAP) on the generated reports to show clustering of "sensory", "temporal", and "intentional" concepts in the latent space. Output a static plot or HTML report. **Dependency**: T009, T009b, T024. **Verification**: Run `python code/analysis/experience_trace.py --input data/processed/merged_dataset.csv --n 100`; verify `data/processed/latent_trace.html` or `.png` exists.
- [D] T036 [P] [US2] **Implement Debiasing/Contradiction Test**: Create `code/analysis/debiasing_test.py` to address Kahneman's concern about "consistently wrong" systems (Kahneman Review). **Logic**: For a subset of prompts, force the model to generate a report under "high noise" conditions (e.g., corrupted prompt, random seed injection) and then generate a contradictory report. Measure if the "phenomenological markers" dissolve or persist incoherently. Compare marker density between "clean" and "noisy" conditions. **Dependency**: T009, T009b, T024. **Verification**: Run `python code/analysis/debiasing_test.py --noise 0.5`; verify `data/processed/debiasing_report.md` exists and contains a key `p_value` as a float.
- [D] T037 [P] [US2] **Implement Embodiment/Style Distinction Metric**: Create `code/analysis/embodiment_score.py` to measure the difference between "phenomenological style" and "ordinary conversation" (Krakauer Review). **Logic**: Define a set of "embodied" features (e.g., sensorimotor verbs, spatial prepositions) and compare their frequency in the generated reports vs. a baseline of standard technical reports. Calculate a "Phenomenological Index" (ratio of embodied features to total features). **Dependency**: T009, T009b, T024. **Verification**: Run `python code/analysis/embodiment_score.py --n 100`; verify `data/processed/embodiment_index.csv` exists and contains a key `index` as a float.
- [D] T038 [P] [US2] **Implement Incoherence/Quantum Metric**: Create `code/analysis/incoherence_metric.py` to test Dyson's hypothesis that "truthful" reports might be inherently incoherent (Dyson Review). **Logic**: Compute a "logical contradiction density" (using NLI) but also a "semantic entropy" (variance in embeddings of repeated generations for the *same* prompt). Correlate high entropy with high marker density. If high entropy correlates with high marker presence, it supports the "incoherent truth" hypothesis. **Dependency**: T009, T009b, T024. **Verification**: Run `python code/analysis/incoherence_metric.py --n 100`; verify `data/processed/incoherence_correlation.json` exists and contains a key `correlation` as a float.
- [ ] T039a [P] [US2] **Implement Construct Validity Justification (Primary)**: Create `code/analysis/construct_validity.py` to cite phenomenological literature for marker definitions. **Logic**: Generate a report citing specific phenomenological texts (e.g., Husserl, Merleau-Ponty) that justify the chosen markers. **Dependency**: T004, T016. **Verification**: Run `python code/analysis/construct_validity.py`; verify `data/processed/construct_validity_report.md` exists and contains citations and a table of results for alternative metric definitions.
- [ ] T039b [P] [US2] **Implement Construct Validity Sensitivity (Secondary)**: Perform sensitivity analysis on alternative metric definitions. **Logic**: Vary the marker dictionary and report the impact on validity scores. **Dependency**: T039a. **Verification**: Run `python code/analysis/construct_validity.py --sensitivity`; verify `data/processed/construct_validity_sensitivity.md` exists.
- [ ] T040 [P] [US1] **Document Scope Limitation**: Create `docs/scope_limitation.md` to formally document the deviation from FR-001 (two checkpoints) due to hardware constraints. **Content**: Explain that TinyLlama is used in CI due to RAM constraints., and the second checkpoint is available via T009b (GPU offload). **Verification**: Run `grep -c "TinyLlama" docs/scope_limitation.md` and `grep -c "GPU" docs/scope_limitation.md`; verify both return >= 1.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review-Driven Enhancements (Phase 6)**: Depends on US1 and US2 logic to be functional.
- **Integration & Orchestration (Phase 7)**: Depends on US1, US2, US3 logic AND Phase 6 enhancements to be in place.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (schema only for parallel dev)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 metrics
- **Review-Driven Enhancements (Phase 6)**: Depends on US1 and US2 logic to be functional.
- **Integration & Orchestration (Phase 7)**: Depends on US1, US2, US3 logic AND Phase 6 enhancements to be in place.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Review-Driven Enhancements (Phase 6) can be implemented in parallel once US1 and US2 are functional.
- Integration & Orchestration (Phase 7) tasks can be implemented in parallel once the base analysis pipeline (US2) and review enhancements (Phase 6) are functional.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
5. Add Review-Driven Enhancements (Phase 6) → Address specific philosophical concerns
6. Add Integration & Orchestration (Phase 7) → Address specific philosophical concerns
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Generation)
 - Developer B: User Story 2 (Analysis)
 - Developer C: User Story 3 (Validation)
 - Developer D: Review-Driven Enhancements (Phase 6)
 - Developer E: Integration & Orchestration (Phase 7)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [D] tasks = Dependent (must wait for specific prior tasks)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must be executable on a minimal CPU configuration. No CUDA, no 8-bit/4-bit quantization requiring GPU drivers. Use `llama-cpp-python` with GGUF for TinyLlama and Phi-2.
- **Model Constraint**: TinyLlama-1.1B (T009) is the **only** model for the primary CI pipeline. Mistral-7B (T009b) is for **GPU offload** and is mandatory for FR-001 compliance. Phi-2 (T012) is for **local reproduction only** and is optional.
- **Review Integration**: Tasks T034-T038 address the specific concerns raised by Turing (operational test), Rockmore (latent trace), Kahneman (debiasing), Krakauer (embodiment distinction), and Dyson (incoherence/entropy).