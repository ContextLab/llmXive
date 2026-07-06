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

- [ ] T001 Create project root structure per implementation plan (repository root) including `code/`, `data/raw/`, `data/processed/`, `data/outputs/`, `tests/`, `output/`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinned versions for `transformers`, `codecarbon`, `datasets`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `download_data.py` to fetch CodeXGLUE Python code-generation subset via HuggingFace `datasets` library
- [ ] T005 [P] Implement fallback logic in `download_data.py`: If CodeXGLUE fetch fails or is unverified, **DO NOT** switch to HumanEval/MBPP as no human baseline exists for those prompts per Verified Fallback Protocol. Instead, proceed with the available sample size (N < 200) or fail gracefully with a clear error message. **MUST** log the specific reason for sample size reduction.
- [ ] T005.1 [P] Define exclusion criteria for unmatched prompts: Create logic to exclude any prompt from `human_baseline_times.json` that does not have a corresponding entry in the downloaded CodeXGLUE dataset. **MUST** explicitly state that no mapping logic for alternative datasets (HumanEval/MBPP) is required or permitted. **T005.1 must be completed before T005 implementation begins.**
- [ ] T006 [P] Implement `validate_baseline.py` to synthesize local human baseline data: **MUST validate that hardcoded time values from the 2025 comparative analysis paper (Table X, Section Y) represent raw developer time (minutes/hours), not pre-calculated CO₂**. If the 2025 paper data is missing, **execute the Synthesized Baseline Protocol** using specific literature values (e.g., average 30-60 minutes per prompt from IEEE/ACM software engineering literature) with explicit citation. **The task MUST fail ONLY if the Synthesized Baseline Protocol cannot identify a valid literature source.** Load into `data/raw/human_baseline_times.json` with exact structure `{"prompt_id": <string>, "time_minutes": <float>}`. **Depends on T004** to ensure the downloaded prompt IDs exist for matching. **Includes a verification step that fails if the data does not match the raw time schema.**
- [~] T007 [P] Setup environment configuration for regional CO2 conversion factors and power model constants in `config.yaml`
- [~] T008 [P] Implement checksum validation for downloaded raw data in `download_data.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - LLM Inference & Energy Instrumentation (Priority: P1) 🎯 MVP

**Goal**: Execute code generation tasks using GPT-2-medium on CPU, recording energy and carbon emissions via CodeCarbon.

**Independent Test**: Run a single prompt through the pipeline and verify a JSON record is produced with non-zero `energy_kWh` and `co2_kg`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Contract test for `run_inference.py` output schema in `tests/contract/test_inference_schema.py`
- [~] T010 [P] [US1] Unit test for CodeCarbon CPU device detection in `tests/unit/test_codecarbon_cpu.py`

### Implementation for User Story 1

- [~] T011 [US1] Implement `run_inference.py` to load **GPT-2-medium** (not GPT-medium) in default precision (no reduced-bit quantization) on CPU. **MUST output the generated code string in the result JSON to allow LOC counting.**
- [~] T012 [US1] Wrap inference loop in `run_inference.py` with `codecarbon.EmissionsTracker` configured for CPU
- [ ] T013 [US1] Implement error handling in `run_inference.py`: log CodeCarbon failures, skip specific prompt, and continue to next
- [ ] T014 [US1] Implement batch processing loop (targeting a scalable number of prompts) in `run_inference.py` with progress logging
- [ ] T015 [US1] Generate `data/processed/llm_inference_results.json` containing `prompt_id`, `model_used`, `energy_kWh`, `co2_kg`, and **calculated `loc_count`** (count lines of the generated code string immediately after generation, do not use placeholders like 0 or -1).
- [ ] T016 [US1] Add validation to exclude prompts that failed to generate code or resulted in empty strings from the output file

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Human Baseline Estimation & Normalization (Priority: P2)

**Goal**: Calculate estimated human carbon footprint and normalize both LLM and human emissions per Line of Code (LOC).

**Independent Test**: Verify that `data/processed/paired_emissions.csv` contains valid pairs and excludes records with 0 LOC.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for human baseline conversion logic (time to CO2) in `tests/unit/test_baseline_conversion.py`
- [ ] T018 [P] [US2] Unit test for LOC normalization and 0-LOC exclusion logic in `tests/unit/test_normalization.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement logic in `calculate_emissions.py` to join `llm_inference_results.json` with `data/raw/human_baseline_times.json`. **Depends on T006 and T016.**
- [ ] T020 [US2] Implement LOC counting for LLM-generated code in `calculate_emissions.py`. **Depends on T006, T016, and T011 (to access raw code strings).**
- [ ] T021 [US2] Implement human baseline CO2 calculation using mean of reported time range and standard laptop power model in `calculate_emissions.py`
- [ ] T022 [US2] Implement normalization logic to calculate `co2_per_loc` for both LLM and human baselines
- [ ] T023 [US2] Implement exclusion logic in `calculate_emissions.py` to drop any record where LLM LOC or Human LOC is 0
- [ ] T024 [US2] Generate `data/processed/paired_emissions.csv` with columns: `prompt_id`, `loc_count`, `llm_co2_per_loc`, `human_co2_per_loc`
- [ ] T025 [US2] Implement sensitivity analysis script to recalculate human emissions using low, medium, and high power draws. **MUST perform a statistical comparison of the stability results:** calculate the variance of the significance flags (p < 0.05) and effect direction across the three power models. **MUST generate a stability assessment artifact** (`data/outputs/stability_assessment.json`) containing the variance of p-values, the boolean stability flag (stable if no flip in direction or p-value crossing 0.05), and the explicit conclusion. **Output schema: `{"low_p": float, "med_p": float, "high_p": float, "variance": float, "stable": bool, "conclusion": "string"}`. **Depends on T024.**
- [ ] T026 [US2] Generate `data/outputs/sensitivity_analysis_results.csv` for US2 robustness check
- [ ] T027.1 [US2] **Integrate Sensitivity Analysis**: Implement logic in `generate_report.py` (or a helper) to read the stability assessment artifact from T025. **MUST output the stability assessment conclusion** (e.g., "Does the significance hold across all power models?") into a temporary artifact or directly into the report generation input. **Depends on T025.** (Note: T037 will depend on this task to consume the output).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison & Robustness Check (Priority: P3)

**Goal**: Perform statistical comparison using paired t-test (or Wilcoxon) and verify robustness with DistilGPT-2.

**Independent Test**: Verify final report contains test statistic, p-value, effect size, and robustness conclusion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for Shapiro-Wilk normality check and test selection logic in `tests/unit/test_statistical_selection.py`
- [ ] T029 [P] [US3] Unit test for effect size calculation (Cohen's d / rank-biserial) in `tests/unit/test_effect_size.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `statistical_analysis.py` to load `paired_emissions.csv`
- [ ] T031 [US3] Implement Shapiro-Wilk test in `statistical_analysis.py` to determine normality; **Log the Shapiro-Wilk statistic and p-value to stdout and the final JSON report**
- [ ] T032 [US3] Implement **paired-samples t-test** (using `scipy.stats.ttest_rel`) on `llm_co2_per_loc` vs `human_co2_per_loc`. **If normality fails, use Wilcoxon signed-rank test (`scipy.stats.wilcoxon`).** **MUST handle the zero-variance human baseline by calculating the difference (LLM - Human) and testing if the mean difference is significantly different from zero.** **Log the selected analysis name (Paired T-Test or Wilcoxon), test statistic, p-value, and effect size to the output.** **Note: This task replaces the Distribution Overlap Analysis to comply with FR-005 and Constitution Principle VII.**
- [ ] T033a [US3] **DistilGPT-2 Inference**: Run inference loop for DistilGPT-2 on the same prompt subset using the script pattern established in T011-T016 and generate `data/processed/distilgpt2_inference_results.json`. **Depends on T011-T016 artifacts.**
- [ ] T033b [US3] **DistilGPT-2 Normalization**: Join DistilGPT-2 results with the *same* human baseline mapping (from T006) used in T019, calculate `loc_count` (from generated code), and generate `data/processed/distilgpt2_paired_emissions.csv`. **MUST re-run the full normalization logic (T019-T024) for the new model.** **Depends on T033a, T006, T019/T020 logic.**
- [ ] T033c [US3] **DistilGPT-2 Statistics**: Re-run Shapiro-Wilk and **paired-samples t-test (or Wilcoxon)** on DistilGPT-2 data against human baseline; **generate `data/outputs/distilgpt2_stats.json`** with test statistic, p-value, and effect size. **Depends on T033b.**
- [ ] T033d [US3] **DistilGPT-2 Sensitivity**: Re-run the sensitivity analysis (T025 logic) for DistilGPT-2 data to ensure the entire pipeline is repeated. **Depends on T033b.**
- [ ] T034 [US3] Compare direction of effect (higher/lower) between GPT-2-medium (T032) and DistilGPT-2 (T033c) results
- [ ] T035 [US3] Generate `data/outputs/statistical_results.json` with test statistic, p-value, effect size, and significance label for both models
- [ ] T037 [US3] Implement `generate_report.py` to create `output/report.md` with summary statistics, **95% confidence intervals for the mean difference in co2_per_loc**, effect size, boxplots (matplotlib/seaborn), and a **dedicated 'Limitations' section**. **MUST explicitly include Shapiro-Wilk p-value, selected test name (Paired T-Test or Wilcoxon), p-value, and significance label in the report.** **MUST include the stability assessment from T027.1.** **MUST include a dedicated Limitations section covering: model age, theoretical baseline, hardware efficiency, and regional factor mismatch.** **Depends on T027.1.**
- [ ] T038 [US3] Add explicit note in Limitations section regarding the mismatch between dynamic CodeCarbon regional factors and static human baseline factors

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039a [P] Documentation updates: Update `README.md` with CLI usage examples and project structure.
- [ ] T039b [P] Documentation updates: Add docstrings to all functions in `code/`.
- [ ] T040 Code cleanup and refactoring across all scripts
- [ ] T041a [P] Performance optimization: Implement batch size throttling logic in `run_inference.py` to ensure runtime ≤ 6 hours.
- [ ] T041b [P] Performance optimization: Add memory profiling hooks to `utils.py` to ensure RAM ≤ 7 GB.
- [ ] T042 [P] Additional unit tests for edge cases (empty code, missing data) in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T044 Final review of `output/report.md` for clarity and scientific rigor

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T005.1 must be completed before T005 implementation begins.
 - T006 depends on T004 (download_data.py) to exist.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (inference results) and Baseline data (T006)
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
- **Data Integrity**: Do NOT fabricate data. Use real CodeXGLUE prompts and real human baseline data from the cited paper.
- **Execution Order**: Ensure `download_data.py` runs before `run_inference.py`, and `run_inference.py` runs before `calculate_emissions.py`.
- **Statistical Rigor**: T032 and T033c MUST perform **paired-samples t-test** (or Wilcoxon) as required by the spec and Constitution.
- **Logging**: T031 and T032 MUST log Shapiro-Wilk p-value and test name to satisfy SC-005.
- **Robustness**: T033a-T033d MUST generate a separate statistical result and sensitivity analysis for DistilGPT-2 to allow comparison of effect direction.
- **Reporting**: T037 MUST include 95% confidence intervals for the mean difference in co2_per_loc, Shapiro-Wilk p-value, and significance label in the final report, plus a dedicated Limitations section.
- **Sensitivity**: T025 MUST perform a statistical comparison of stability results (variance of p-values) and T027.1 must integrate these results.