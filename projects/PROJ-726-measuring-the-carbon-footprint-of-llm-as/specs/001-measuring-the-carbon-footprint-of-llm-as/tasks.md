# Tasks: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

**Input**: Design documents from `/specs/001-carbon-footprint-llm-code/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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

- [ ] T001 Create project root structure per implementation plan (repository root). **MUST** create directories: `code/`, `data/raw/`, `data/processed/`, `data/outputs/`, `tests/unit/`, `tests/contract/`. **MUST** create empty `__init__.py` files in all `code/` and `tests/` subdirectories to ensure Python package recognition.
- [X] T002 Initialize Python project with `requirements.txt` (pinned versions for `transformers`, `codecarbon`, `datasets`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Implement `download_data.py` to fetch CodeXGLUE Python code-generation subset via HuggingFace `datasets` library. **MUST** sample up to 200 prompts using **random sampling with seed=42**. **MUST** explicitly call `datasets.set_seed(42)` and use a `generator` parameter in the sampling function to ensure deterministic reproducibility across library versions. **MUST** log the specific reason for sample size reduction if N < 200. **MUST** save to `data/raw/codexglue_sample.json`.
- [ ] T005 [P] Implement `validate_baseline.py` to validate human baseline data. **MUST** attempt to extract raw developer time (minutes) from the **specific 2025 comparative analysis paper** (search for DOI or repository path as defined in spec assumptions). **If the 2025 paper is inaccessible, does not exist, or does not contain raw developer time data, the task MUST FAIL LOUDLY** (raise a specific error: `BaselineValidationError: Target paper validation failed. No fallback allowed per FR-008`). **DO NOT** implement a 'Synthesized Baseline Protocol' fallback. **Output file**: `data/raw/human_baseline_times.json` with exact structure `{"prompt_id": <string>, "time_minutes": <float>}` ONLY if validation succeeds. **Includes logic to exclude any prompt in `human_baseline_times.json` that does not have a corresponding entry in `data/raw/codexglue_sample.json`**. **MUST** log the exclusion count and the validation status (Validated). **Depends on T004.** <!-- FAILED: unspecified -->
- [X] T006 [P] Setup environment configuration for regional CO2 conversion factors and power model constants in `config.yaml`
- [ ] T007 [P] Implement checksum validation for downloaded raw data in `download_data.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - LLM Inference & Energy Instrumentation (Priority: P1) 🎯 MVP

**Goal**: Execute code generation tasks using GPT-2-medium on CPU, recording energy and carbon emissions via CodeCarbon.

**Independent Test**: Run a single prompt through the pipeline and verify a JSON record is produced with non-zero `energy_kWh` and `co2_kg`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for `run_inference.py` output schema in `tests/contract/test_inference_schema.py`
- [X] T009 [P] [US1] Unit test for CodeCarbon CPU device detection in `tests/unit/test_codecarbon_cpu.py`

### Implementation for User Story 1

- [ ] T010 [US1] Implement `run_inference.py` to load **openai-community/gpt2-medium** (HuggingFace ID: `openai-community/gpt2-medium`) in **default precision (torch.float32)** on CPU. **MUST explicitly pass `torch_dtype=torch.float32` to the `from_pretrained` call** to ensure deterministic precision. **MUST output the generated code string in the result JSON to allow LOC counting. [UNRESOLVED-CLAIM: c_27beb017 — status=not_enough_info]** **MUST skip energy tracking for any code that fails the syntax validation from T010b. [UNRESOLVED-CLAIM: c_83cca464 — status=not_enough_info]**
- [ ] T010b [US1] **Validate Code Quality**: Implement logic in `run_inference.py` (or a helper module) to validate generated code syntax using `ast.parse()` or a similar Python syntax checker **BEFORE** energy measurement. **MUST mark invalid code with `is_valid_code: false` and skip it from the final emission record.** **Depends on T010 (implementation of inference loop).**
- [ ] T011 [US1] Wrap inference loop in `run_inference.py` with `codecarbon.EmissionsTracker` configured for CPU
- [ ] T012 [US1] Implement error handling in `run_inference.py`: log CodeCarbon failures, skip specific prompt, and continue to next
- [ ] T013 [US1] Implement batch processing loop (targeting a scalable number of prompts) in `run_inference.py` with progress logging
- [ ] T014 [US1] Generate `data/processed/llm_inference_results.json` containing `prompt_id`, `model_used`, `energy_kWh`, `co2_kg`, `generated_code` (the raw string output), `is_valid_code` (boolean), and **calculated `loc_count`** (count lines of the `generated_code` string immediately after generation, do not use placeholders like 0 or -1). **MUST include the full `generated_code` string in the JSON to support downstream LOC verification.**
- [ ] T015 [US1] Add validation to exclude prompts that failed to generate code, resulted in empty strings, or failed syntax validation from the output file

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Human Baseline Estimation & Normalization (Priority: P2)

**Goal**: Calculate estimated human carbon footprint and normalize both LLM and human emissions per Line of Code (LOC).

**Independent Test**: Verify that `data/processed/paired_emissions.csv` contains valid pairs and excludes records with 0 LOC.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for human baseline conversion logic (time to CO2) in `tests/unit/test_baseline_conversion.py`
- [X] T017 [P] [US2] Unit test for LOC normalization and 0-LOC exclusion logic in `tests/unit/test_normalization.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement logic in `calculate_emissions.py` to join `data/processed/llm_inference_results.json` with `data/raw/human_baseline_times.json`. **Depends on T013 and T005.**
- [ ] T019 [US2] Implement LOC counting for LLM-generated code in `calculate_emissions.py`. **Depends on T013.**
- [ ] T020 [US2] Implement human baseline CO2 calculation using mean of reported time range and standard laptop power model in `calculate_emissions.py`. **Depends on T013.**
- [ ] T021 [US2] Implement normalization logic to calculate `co2_per_loc` for both LLM and human baselines
- [ ] T022 [US2] Implement exclusion logic in `calculate_emissions.py` to drop any record where LLM LOC or Human LOC is 0
- [ ] T023 [US2] Generate `data/processed/paired_emissions.csv` with columns: `prompt_id`, `loc_count`, `llm_co2_per_loc`, `human_co2_per_loc`
- [ ] T024a [US2] **Prepare Data for Sensitivity Analysis**: Implement logic in `calculate_emissions.py` to generate `data/processed/sensitivity_input.csv` containing `prompt_id`, `llm_co2_per_loc`, and `human_time_minutes` (raw time). **MUST NOT** perform statistical tests here. **Depends on T023.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (excluding sensitivity analysis which is in Phase 5)

---

## Phase 5: User Story 3 - Statistical Comparison & Robustness Check (Priority: P3)

**Goal**: Perform statistical comparison using Paired-samples t-test (or Wilcoxon) and verify robustness with DistilGPT-2.

**Independent Test**: Verify final report contains t-test/Wilcoxon result, effect size, and robustness conclusion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Paired t-test/Wilcoxon logic in `tests/unit/test_statistical_analysis.py`
- [ ] T028 [P] [US3] Unit test for effect size calculation (Cohen's d for t-test, rank-biserial for Wilcoxon) in `tests/unit/test_effect_size.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `statistical_analysis.py` to load `data/processed/paired_emissions.csv`
- [ ] T030 [US3] Implement Shapiro-Wilk test in `statistical_analysis.py` to determine normality of the **differences** (LLM - Human) in emissions per LOC. **MUST use the result to SELECT the appropriate test**: if p > 0.05, select Paired t-test; if p <= 0.05, select Wilcoxon signed-rank test. **Log the Shapiro-Wilk statistic, p-value, and the selected test name to stdout and the final JSON report.** **MUST reference Spec FR-005 and Constitution Principle VII as the authority for Paired-samples t-test, overriding any Plan contradictions.**
- [ ] T031 [US3] Implement **Paired-samples t-test (or Wilcoxon Signed-Rank)** in `statistical_analysis.py`. **MUST compare `llm_co2_per_loc` vs `human_co2_per_loc` as paired samples**. **MUST calculate the test statistic, p-value, and effect size (Cohen's d if t-test; rank-biserial if Wilcoxon)**. **MUST log the selected method, test statistic, p-value, effect size, and the primary conclusion (Significant/Not Significant based on p < 0.05) to the output.** **Note: This is the PRIMARY statistical test per FR-005 and Constitution Principle VII, overriding the Plan's 'One-Sample t-test' instruction.** **Depends on T029, T030.**
- [ ] T032 [US3] **Run DistilGPT-2 Pipeline**: Re-use the entire analysis pipeline for DistilGPT-2. **Reuse `run_inference.py` with `--model=distilgpt2`** to generate `data/processed/distilgpt2_inference_results.json`. **Reuse `calculate_emissions.py` with `--model=distilgpt2`** to generate `data/processed/distilgpt2_paired_emissions.csv`. **Reuse `statistical_analysis.py` with `--model=distilgpt2`** to perform Shapiro-Wilk, **Paired t-test/Wilcoxon** (per Spec FR-005), and Sensitivity Analysis, generating `data/outputs/distilgpt2_stats.json` and `data/outputs/distilgpt2_stability_assessment.json`. **MUST NOT rewrite the logic; use parameter overrides.** **Depends on T005, T015, T023, T029, T031 (implementation of scripts).**
- [ ] T033 [US3] Compare direction of effect (higher/lower) between GPT-2-medium (T031) and DistilGPT-2 (T032) results
- [ ] T034 [US3] Generate `data/outputs/statistical_results.json` with test type, p-value, effect size, and conclusion label for both models
- [ ] T024 [US3] **Perform Sensitivity Analysis**: Implement logic to recalculate human emissions using low, medium, and high power draws using `data/processed/sensitivity_input.csv`. **MUST assess stability by checking if the mean difference and effect size remain consistent (within a defined tolerance) across the three power models using the Paired t-test (or Wilcoxon) as defined in T031.** **MUST generate a stability assessment artifact** (`data/outputs/stability_assessment.json`) containing the consistency result (stable if mean difference and effect size are consistent), the specific mean differences and effect sizes for each power model, and the explicit stability flag. **Output schema: `{"low_mean_diff": float, "med_mean_diff": float, "high_mean_diff": float, "low_effect_size": float, "med_effect_size": float, "high_effect_size": float, "mean_diff_stable": bool, "effect_size_stable": bool, "stable": bool, "conclusion": "string"}`. **Depends on T023, T031 (for test method).**
- [ ] T026 [US3] **Integrate Sensitivity Results**: Implement function `integrate_stability_results` in `generate_report.py` to read the stability assessment artifact from T024 (`data/outputs/stability_assessment.json`). **MUST output the stability assessment conclusion** (e.g., "Does the statistical significance conclusion hold across all power models?") into the report generation input. **Depends on T024.**
- [ ] T035 [US3] **Integrate DistilGPT-2 Sensitivity**: Implement logic in `generate_report.py` to read the DistilGPT-2 stability assessment from T032. **MUST include the DistilGPT-2 stability conclusion in the report.** **Depends on T032.**
- [ ] T036 [US3] Implement `generate_report.py` to create `data/outputs/report.md` with summary statistics, **p-values**, effect size, boxplots (matplotlib/seaborn), and a **dedicated 'Limitations' section**. **MUST explicitly include Shapiro-Wilk p-value, selected analysis name (Paired t-test or Wilcoxon), test statistic, p-value, effect size, and conclusion label in the report.** **MUST include the stability assessment from T026 (GPT-2) and T035 (DistilGPT-2).** **MUST include a dedicated Limitations section covering: model age, theoretical baseline, hardware efficiency, and regional factor mismatch.** **Depends on T026, T031, T032, T034, T035.**
- [ ] T037 [US3] Add explicit note in Limitations section regarding the mismatch between dynamic CodeCarbon regional factors and static human baseline factors

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Documentation updates: Update `README.md` with CLI usage examples and project structure.
- [ ] T038b [P] Documentation updates: Add docstrings to all **public** functions in `code/*.py`.
- [ ] T039a [P] **Refactor LOC Counting**: Refactor `calculate_emissions.py` to separate LOC counting logic into a dedicated function `count_lines(code_string)`.
- [ ] T039b [P] **Refactor Energy Calculation**: Refactor `calculate_emissions.py` to separate energy calculation logic into a dedicated function `calculate_energy(time_minutes, power_kw, emission_factor)`.
- [ ] T040a [P] **Unit Test: Empty Code**: Add unit test for empty code handling in `tests/unit/test_normalization.py`.
- [ ] T040b [P] **Unit Test: Missing Data**: Add unit test for missing data handling in `tests/unit/test_baseline_conversion.py`.
- [ ] T040c [P] **Unit Test: NaN Values**: Add unit test for NaN value handling in `tests/unit/test_statistical_analysis.py`.
- [ ] T041 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T042 Final review of `data/outputs/report.md` for clarity and scientific rigor

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T005 must be completed after T004 (download_data.py) to ensure prompt IDs exist for matching.
 - T006 is independent of T004 and can run in parallel.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed) **ONLY AFTER** their specific data dependencies are met.
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) **AND** completion of T015 (US1 output). Requires output from US1 (inference results) and Baseline data (T005).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) **AND** completion of US1 and US2. Requires output from US1 and US2 (paired emissions).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for this script-based pipeline)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **except T005 which depends on T004**.
- Once Foundational phase completes and dependencies are met, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **once their upstream data is generated**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for `run_inference.py` output schema in `tests/contract/test_inference_schema.py`"
Task: "Unit test for CodeCarbon CPU device detection in `tests/unit/test_codecarbon_cpu.py`"

# Launch all models for User Story 1 together:
Task: "Implement `run_inference.py` to load GPT-2-medium in default precision on CPU"
Task: "Wrap inference loop in `run_inference.py` with `codecarbon.EmissionsTracker`"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure CodeCarbon works on CPU, JSON output is valid)
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
2. Once Foundational is done and data is available:
 - Developer A: User Story 1 (Inference)
 - Developer B: User Story 2 (Baseline & Normalization) - **Starts after T015 completes**
 - Developer C: User Story 3 (Statistics & Robustness) - **Starts after T023 completes**
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
- **Critical Constraint**: All model inference MUST run on CPU. Do NOT use `load_in_8bit`, `bitsandbytes`, or `device_map="cuda"`. Use default precision GPT-2-medium and DistilGPT-2.
- **Data Integrity**: Do NOT fabricate data. Use real CodeXGLUE prompts and real human baseline data from the cited paper. **NO fallback constants allowed.**
- **Execution Order**: Ensure `download_data.py` runs before `run_inference.py`, and `run_inference.py` runs before `calculate_emissions.py`.
- **Statistical Rigor**: T030 and T031 MUST implement **Paired-samples t-test (or Wilcoxon Signed-Rank)** as the PRIMARY test per Spec FR-005 and Constitution Principle VII. One-Sample t-test and Distribution Overlap Analysis are explicitly FORBIDDEN for the primary comparison.
- **Logging**: T030 and T031 MUST log Shapiro-Wilk p-value, selected analysis name, and test results to satisfy SC-005.
- **Robustness**: T032 MUST generate a separate statistical result and sensitivity analysis for DistilGPT-2 to allow comparison of effect direction.
- **Reporting**: T036 MUST include p-values, effect sizes, test results, and a dedicated Limitations section.
- **Sensitivity**: T024 MUST perform a stability assessment based on consistency of **mean differences and effect sizes** across power models. T026 must integrate these results. T032 and T035 must do the same for DistilGPT-2.
- **Code Quality**: T010b MUST validate code syntax before energy measurement to prevent skewed data from hallucinated outputs.