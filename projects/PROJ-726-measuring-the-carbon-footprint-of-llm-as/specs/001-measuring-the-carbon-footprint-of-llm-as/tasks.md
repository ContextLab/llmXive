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

- [ ] T001 Create project root structure per implementation plan (repository root) including `code/`, `data/raw/`, `data/processed/`, `data/outputs/`, `tests/`
- [X] T002 Initialize Python project with `requirements.txt` (pinned versions for `transformers`, `codecarbon`, `datasets`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `download_data.py` to fetch CodeXGLUE Python code-generation subset via HuggingFace `datasets` library. **MUST** sample up to 200 prompts. **MUST** log the specific reason for sample size reduction if N < 200. **MUST** save to `data/raw/codexglue_sample.json`.
- [ ] T005 [P] Implement `validate_baseline.py` to validate human baseline data against the 2025 comparative analysis paper. **MUST** attempt to extract raw developer time (minutes) from the 2025 paper (Table X, Section Y). **If the 2025 paper data is inaccessible**, **execute the Synthesized Baseline Protocol** using specific literature values (e.g., average extended duration per prompt from IEEE/ACM software engineering literature) with explicit citation. **The task MUST fail immediately if the 2025 paper is missing AND no valid literature source for synthesis can be identified.** **Output file**: `data/raw/human_baseline_times.json` with exact structure `{"prompt_id": <string>, "time_minutes": <float>}`. **Includes logic to exclude any prompt in `human_baseline_times.json` that does not have a corresponding entry in `data/raw/codexglue_sample.json`**. **MUST** log the exclusion count.
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

- [ ] T010 [US1] Implement `run_inference.py` to load **GPT-2-medium** (not GPT-medium) in default precision (no reduced-bit quantization) on CPU. **MUST output the generated code string in the result JSON to allow LOC counting.**
- [ ] T011 [US1] Wrap inference loop in `run_inference.py` with `codecarbon.EmissionsTracker` configured for CPU
- [ ] T012 [US1] Implement error handling in `run_inference.py`: log CodeCarbon failures, skip specific prompt, and continue to next
- [ ] T013 [US1] Implement batch processing loop (targeting a scalable number of prompts) in `run_inference.py` with progress logging
- [ ] T014 [US1] Generate `data/processed/llm_inference_results.json` containing `prompt_id`, `model_used`, `energy_kWh`, `co2_kg`, `generated_code` (the raw string output), and **calculated `loc_count`** (count lines of the `generated_code` string immediately after generation, do not use placeholders like 0 or -1). **MUST include the full `generated_code` string in the JSON to support downstream LOC verification.**
- [ ] T015 [US1] Add validation to exclude prompts that failed to generate code or resulted in empty strings from the output file

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Human Baseline Estimation & Normalization (Priority: P2)

**Goal**: Calculate estimated human carbon footprint and normalize both LLM and human emissions per Line of Code (LOC).

**Independent Test**: Verify that `data/processed/paired_emissions.csv` contains valid pairs and excludes records with 0 LOC.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for human baseline conversion logic (time to CO2) in `tests/unit/test_baseline_conversion.py`
- [X] T017 [P] [US2] Unit test for LOC normalization and 0-LOC exclusion logic in `tests/unit/test_normalization.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement logic in `calculate_emissions.py` to join `data/processed/llm_inference_results.json` with `data/raw/human_baseline_times.json`. **Depends on T005 and T015.**
- [ ] T019 [US2] Implement LOC counting for LLM-generated code in `calculate_emissions.py`. **Depends on T015 (to access `generated_code` strings).**
- [ ] T020 [US2] Implement human baseline CO2 calculation using mean of reported time range and standard laptop power model in `calculate_emissions.py`. **Depends on T015.**
- [ ] T021 [US2] Implement normalization logic to calculate `co2_per_loc` for both LLM and human baselines
- [ ] T022 [US2] Implement exclusion logic in `calculate_emissions.py` to drop any record where LLM LOC or Human LOC is 0
- [ ] T023 [US2] Generate `data/processed/paired_emissions.csv` with columns: `prompt_id`, `loc_count`, `llm_co2_per_loc`, `human_co2_per_loc`
- [ ] T024 [US2] Implement sensitivity analysis script to recalculate human emissions using low, medium, and high power draws. **MUST assess stability by checking if the 'Statistical Significance' conclusion (from the paired t-test or Wilcoxon test) remains consistent across the three power models.** **MUST generate a stability assessment artifact** (`data/outputs/stability_assessment.json`) containing the consistency result (stable if conclusion is identical for all three, unstable otherwise), the specific conclusions for each power model, and the explicit stability flag. **Output schema: `{"low_conclusion": "string", "med_conclusion": "string", "high_conclusion": "string", "stable": bool, "conclusion": "string"}`. **Depends on T023.**
- [ ] T025 [US2] Generate `data/outputs/sensitivity_analysis_results.csv` for US2 robustness check
- [ ] T026 [US2] **Integrate Sensitivity Analysis**: Implement function `integrate_stability_results` in `generate_report.py` to read the stability assessment artifact from T024 (`data/outputs/stability_assessment.json`). **MUST output the stability assessment conclusion** (e.g., "Does the significance hold across all power models?") into the report generation input. **Depends on T024.** (Note: T036 will depend on this task to consume the output).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison & Robustness Check (Priority: P3)

**Goal**: Perform statistical comparison using paired t-test/Wilcoxon and verify robustness with DistilGPT-2.

**Independent Test**: Verify final report contains t-test/Wilcoxon result, effect direction, and robustness conclusion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for t-test/Wilcoxon logic in `tests/unit/test_statistical_analysis.py`
- [ ] T028 [P] [US3] Unit test for effect size calculation (Cohen's d for LLM distribution only) in `tests/unit/test_effect_size.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `statistical_analysis.py` to load `data/processed/paired_emissions.csv`
- [ ] T030 [US3] Implement Shapiro-Wilk test in `statistical_analysis.py` to determine normality of the LLM distribution; **Log the Shapiro-Wilk statistic and p-value to stdout and the final JSON report** (for descriptive purposes only, as the human baseline has zero variance).
- [ ] T031 [US3] Implement **Paired Statistical Test** in `statistical_analysis.py`. **Perform a paired-samples t-test** comparing LLM vs. human `co2_per_loc`. **If normality fails (Shapiro-Wilk p < 0.05), FALL BACK to Wilcoxon signed-rank test.** **Log the selected test name (t-test or Wilcoxon), the test statistic, p-value, and effect size (Cohen's d or rank-biserial) to the output.** **Perform Distribution Overlap Analysis as a SUPPLEMENTARY descriptive check only.** **Explicitly label the primary conclusion based on the t-test/Wilcoxon p-value (< 0.05 = significant).** **Note: This is the PRIMARY statistical test per FR-005.**
- [ ] T032 [US3] **Run DistilGPT-2 Pipeline**: Re-use the entire analysis pipeline for DistilGPT-2. **Reuse `run_inference.py` with `--model=distilgpt2`** to generate `data/processed/distilgpt2_inference_results.json`. **Reuse `calculate_emissions.py` with `--model=distilgpt2`** to generate `data/processed/distilgpt2_paired_emissions.csv`. **Reuse `statistical_analysis.py` with `--model=distilgpt2`** to perform Shapiro-Wilk, Paired Statistical Test, and Sensitivity Analysis, generating `data/outputs/distilgpt2_stats.json` and `data/outputs/distilgpt2_stability_assessment.json`. **MUST NOT rewrite the logic; use parameter overrides.** **Depends on T005, T015, T023, T029, T031.**
- [ ] T033 [US3] Compare direction of effect (higher/lower) between GPT-2-medium (T031) and DistilGPT-2 (T032) results
- [ ] T034 [US3] Generate `data/outputs/statistical_results.json` with overlap status, CI, effect direction, and significance label for both models
- [ ] T035 [US3] **Integrate DistilGPT-2 Sensitivity**: Implement logic in `generate_report.py` to read the DistilGPT-2 stability assessment from T032. **MUST include the DistilGPT-2 stability conclusion in the report.** **Depends on T032.**
- [ ] T036 [US3] Implement `generate_report.py` to create `data/outputs/report.md` with summary statistics, **% confidence intervals for the LLM mean**, effect size, boxplots (matplotlib/seaborn), and a **dedicated 'Limitations' section**. **MUST explicitly include Shapiro-Wilk p-value, selected analysis name (Paired t-test or Wilcoxon), p-value, significance label, and effect direction in the report.** **MUST include the stability assessment from T026 (GPT-2) and T035 (DistilGPT-2).** **MUST include a dedicated Limitations section covering: model age, theoretical baseline, hardware efficiency, and regional factor mismatch.** **Depends on T026, T031, T032, T034, T035.**
- [ ] T037 [US3] Add explicit note in Limitations section regarding the mismatch between dynamic CodeCarbon regional factors and static human baseline factors

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Documentation updates: Update `README.md` with CLI usage examples and project structure.
- [ ] T038b [P] Documentation updates: Add docstrings to all functions in `code/`.
- [ ] T039 Code cleanup and refactoring across all scripts
- [ ] T040 [P] Additional unit tests for edge cases (empty code, missing data) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T042 Final review of `data/outputs/report.md` for clarity and scientific rigor

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T005 must be completed after T004 (download_data.py) to ensure prompt IDs exist for matching.
 - T006 depends on T004 (download_data.py) to exist.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (inference results) and Baseline data (T005)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 and US2 (paired emissions)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for this script-based pipeline)
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
2. Once Foundational is done:
 - Developer A: User Story 1 (Inference)
 - Developer B: User Story 2 (Baseline & Normalization)
 - Developer C: User Story 3 (Statistics & Robustness)
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
- **Data Integrity**: Do NOT fabricate data. Use real CodeXGLUE prompts and real human baseline data from the cited paper or the Synthesized Baseline Protocol.
- **Execution Order**: Ensure `download_data.py` runs before `run_inference.py`, and `run_inference.py` runs before `calculate_emissions.py`.
- **Statistical Rigor**: T031 and T032 MUST perform **Paired t-test (or Wilcoxon fallback)** as the PRIMARY test. Distribution Overlap Analysis is supplementary.
- **Logging**: T030 and T031 MUST log Shapiro-Wilk p-value and analysis name to satisfy SC-005.
- **Robustness**: T032 MUST generate a separate statistical result and sensitivity analysis for DistilGPT-2 to allow comparison of effect direction.
- **Reporting**: T036 MUST include confidence intervals for the LLM mean, Shapiro-Wilk p-value, and primary statistical conclusion (t-test/Wilcoxon) in the final report, plus a dedicated Limitations section.
- **Sensitivity**: T024 MUST perform a stability assessment based on consistency of t-test/Wilcoxon conclusions and T026 must integrate these results. T032 and T035 must do the same for DistilGPT-2.