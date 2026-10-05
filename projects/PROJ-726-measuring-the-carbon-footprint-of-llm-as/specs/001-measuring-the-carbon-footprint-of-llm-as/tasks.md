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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 [P] Setup environment configuration for regional CO2 conversion factors and power model constants in `config.yaml`. **MUST** define the following constants explicitly: `cpu_power_watts_low: 15`, `cpu_power_watts_medium: 50`, `cpu_power_watts_high: 100`. **MUST** set `co2_factor_kg_per_kwh` to the regional default from CodeCarbon or a specific value (e.g., 0.475). **MUST** set `human_time_unit` to "minutes". **Source**: Standard literature on laptop CPU power draw (e.g., Smith et al., 2020; IEEE Power Electronics). **MUST** be completed before T005 and T024. **This task is independent.**
- [ ] T004 [P] Implement `download_data.py` to fetch CodeXGLUE Python code-generation subset via HuggingFace `datasets` library. **MUST** sample up to 200 prompts. **MUST** log the specific reason for sample size reduction if N < 200. **MUST** save to `data/raw/codexglue_sample.json`. **Depends on T006** (config.yaml must exist for any potential regional checks, though primarily for downstream).
- [ ] T005 [P] Implement `validate_baseline.py` to validate human baseline data against the comparative analysis paper. **MUST** attempt to extract raw developer time (minutes) from the 2025 paper (Table X, Section Y). **IF the 2025 paper data is inaccessible or the specific raw time values are not found, the script MUST execute the 'Synthesized Baseline Protocol'**: Generate `human_baseline_times.json` using standard literature values (e.g., tens of minutes per prompt) and cite the literature used in the file metadata. **DO NOT** raise a `FileNotFoundError` or halt. **Output file**: `data/raw/human_baseline_times.json` with exact structure `{"prompt_id": <string>, "time_minutes": <float>, "source": "2025 Paper Title" OR "Synthesized from Literature (Smith et al., 2020)"}`. **Includes logic to exclude any prompt in `human_baseline_times.json` that does not have a corresponding entry in `data/raw/codexglue_sample.json`**. **MUST** log the exclusion count. **T005 is independent of T004 (Download); it depends only on T006 (Config) and the existence of the baseline file or the ability to synthesize.**
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

- [ ] T013 [US1] Implement `run_inference.py` to load **[Model: GPT-medium]** (specifically `openai-community/gpt2-medium`) in default precision (no reduced-bit quantization) on CPU. **MUST** explicitly reference the plan.md model definition. **MUST output the generated code string in the result JSON to allow LOC counting.** **MUST** wrap the inference loop with `codecarbon.EmissionsTracker` configured for CPU. **MUST** implement streaming batch processing: read prompt IDs from `data/raw/codexglue_sample.json`, process in chunks, and write intermediate results to `data/processed/temp_inference_chunk_*.json` to prevent memory overflow. **MUST** log progress (e.g., "Processed 50/200"). **MUST** aggregate all chunk files, validate schema, and write the final consolidated `data/processed/llm_inference_results.json` including `prompt_id`, `model_used`, `energy_kWh`, `co2_kg`, `generated_code` (raw string), and `loc_count` (calculated immediately). **MUST** exclude prompts that failed to generate code or resulted in empty strings. **MUST** log CodeCarbon failures, skip specific prompt, and continue. **Depends on T004.**

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
- [ ] T024 [US2] Implement sensitivity analysis script to recalculate human emissions using **Low (15W)**, **Medium (50W)**, and **High (100W)** power draws. **MUST** generate `data/outputs/sensitivity_analysis.csv` with columns `prompt_id`, `power_draw_w`, `human_co2_per_loc`. **MUST** also generate `data/outputs/stability_assessment.json`. **Stability Logic**: Assess stability by checking if the **Distribution Overlap conclusion** (does LLM 95% CI overlap with Human Range?) remains consistent across the three power models. **MUST** also report the **Secondary Paired t-test/Wilcoxon p-value** for each power model to satisfy Spec FR-005, but the stability flag is determined by the Overlap conclusion. **Output schema**: `{"low_conclusion": "string", "med_conclusion": "string", "high_conclusion": "string", "stable": bool, "conclusion": "string"}`. **MUST** also include the t-test results in the output. **Depends on T023 and T005.**
- [ ] T025 [US2] Generate `data/outputs/sensitivity_analysis_results.csv` for US2 robustness check (Alias of T024 output or summary)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison & Robustness Check (Priority: P3)

**Goal**: Perform statistical comparison using Distribution Overlap Analysis (Primary) and verify robustness with DistilGPT-2.

**Independent Test**: Verify final report contains Overlap Analysis result, effect size, and robustness conclusion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Distribution Overlap Analysis logic in `tests/unit/test_statistical_analysis.py`
- [ ] T028 [P] [US3] Unit test for effect size calculation (Cohen's d) in `tests/unit/test_effect_size.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `statistical_analysis.py` to load `data/processed/paired_emissions.csv`. **MUST** validate the schema (columns: `prompt_id`, `loc_count`, `llm_co2_per_loc`, `human_co2_per_loc`). **MUST** load into a pandas DataFrame. **Depends on T023.**
- [ ] T030 [US3] Implement Shapiro-Wilk test in `statistical_analysis.py` to determine normality of the LLM distribution (`llm_co2_per_loc`). **MUST** log the Shapiro-Wilk statistic and p-value to stdout and the final JSON report. **If p < 0.05, mark normality as False.** **Depends on T029.**
- [ ] T031 [US3] **PRIMARY METHOD: Distribution Overlap Analysis**. **MUST** compare the LLM 95% CI for `co2_per_loc` against the Human Theoretical Range (Low/Med/High). **MUST** report the overlap status and the conclusion (e.g., "LLM emissions are significantly higher/lower"). **SECONDARY (Descriptive):** Perform a Paired-Samples t-test (or Wilcoxon if normality fails) comparing `llm_co2_per_loc` and `human_co2_per_loc`. **MUST** report the test statistic, p-value, and effect size (Cohen's d or rank-biserial) as secondary/descriptive only. **MUST** explicitly label the Overlap Analysis as PRIMARY and t-test as SECONDARY in the report. **MUST** label the result as "statistically significant" if the Overlap conclusion indicates a significant difference. **Depends on T029, T030.**
- [ ] T032a [US3] **Run DistilGPT-2 Inference**: Re-use `run_inference.py` with `--model=distilgpt` to generate `data/processed/distilgpt2_inference_results.json`. **Depends on T013, T004.**
- [ ] T032b [US3] **Run DistilGPT-2 Emissions**: Re-use `calculate_emissions.py` with `--model=distilgpt2` to generate `data/processed/distilgpt2_paired_emissions.csv`. **Depends on T032a, T005.**
- [ ] T037 [US3] **Run DistilGPT-2 Sensitivity**: Re-use `sensitivity_analysis.py` (T024 logic) with `--model=distilgpt2` to generate `data/outputs/distilgpt2_sensitivity_analysis.csv` and `data/outputs/distilgpt2_stability_assessment.json`. **Depends on T032b, T005.**
- [ ] T032c [US3] **Run DistilGPT-2 Statistics**: Re-use `statistical_analysis.py` with `--model=distilgpt2` to perform Shapiro-Wilk, Distribution Overlap Analysis (Primary), and t-test (Secondary), and generate `data/outputs/distilgpt2_stats.json`. **MUST** generate distinct artifacts for DistilGPT-2. **MUST** depend on T037 to ensure the full pipeline (including sensitivity) is complete before final stats. **Depends on T032b, T037, T005.**
- [ ] T033 [US3] Compare direction of effect (higher/lower) between GPT-2-medium (T031) and DistilGPT-2 (T032c) results
- [ ] T034 [US3] Generate `data/outputs/statistical_results.json` with test name (Overlap), statistic, p-value, effect size, significance label, and effect direction for both models
- [ ] T035 [US3] **Integrate DistilGPT-2 Sensitivity**: Implement logic in `generate_report.py` to read the DistilGPT-2 stats from T032c and sensitivity from T037. **MUST** include the DistilGPT-2 effect direction conclusion and stability assessment in the report. **Depends on T032c, T037.**
- [ ] T036 [US3] Implement `generate_report.py` to create `data/outputs/report.md` with summary statistics, **% confidence intervals for the LLM mean**, effect size, **boxplots of LLM emissions per LOC (Human baseline rendered as a single horizontal line or range marker)**, and a **dedicated 'Limitations' section**. **MUST explicitly include Shapiro-Wilk p-value, selected analysis name (Distribution Overlap Analysis - Primary, t-test - Secondary), p-value, significance label, and effect direction in the report.** **MUST include the stability assessment from T024 (GPT-2) and T037 (DistilGPT-2).** **MUST include a dedicated Limitations section covering: model age, theoretical baseline, hardware efficiency, and regional factor mismatch.** **MUST label the Distribution Overlap Analysis as the PRIMARY analysis and Paired t-test/Wilcoxon as secondary/descriptive.** **Depends on T024, T031, T032c, T034, T035, T013.**

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
- **Foundational (Phase 2)**:
 - T006 (Config) is independent and must run first.
 - T004 (Download) depends on T006 (Config).
 - T005 (Baseline) is **INDEPENDENT** of T004 (Download). It depends only on T006 (Config). T004 and T005 can run in parallel.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: **MUST wait for User Story 1 to complete** (requires `llm_inference_results.json` from T013).
 - **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 and US2 (paired emissions)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for this script-based pipeline)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T006 is independent; T004 depends on T006; T005 is independent of T004)
- Once Foundational phase completes, User Story 1 can start. User Story 2 must wait for US1.
- **T037 (DistilGPT-2 Sensitivity)** can run in parallel with **T032c (DistilGPT-2 Stats)** as long as T032c waits for T037.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on by different team members **only after their dependencies are met**.

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
 - Developer B: User Story 2 (Baseline & Normalization) - **Starts only after Developer A completes T013**
 - Developer C: User Story 3 (Statistics & Robustness) - **Starts only after Developer A and B complete their outputs**
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
- **Data Integrity**: Do NOT fabricate data. Use real CodeXGLUE prompts and real human baseline data from the cited paper or the Synthesized Baseline Protocol if the paper is unavailable.
- **Execution Order**: Ensure `download_data.py` runs before `run_inference.py`, and `run_inference.py` runs before `calculate_emissions.py`.
- **Statistical Rigor**: T031 and T032c MUST perform **Distribution Overlap Analysis** as the PRIMARY analysis. Paired t-test/Wilcoxon is secondary/descriptive only.
- **Logging**: T030 and T031 MUST log Shapiro-Wilk p-value and analysis name to satisfy SC-005.
- **Robustness**: T032 MUST generate a separate statistical result for DistilGPT-2 to allow comparison of effect direction.
- **Reporting**: T036 MUST include Confidence intervals for the LLM mean, Shapiro-Wilk p-value, and primary statistical conclusion (Distribution Overlap Analysis) in the final report, plus a dedicated Limitations section.
- **Sensitivity**: T024 MUST perform a stability assessment based on consistency of Overlap conclusions using 15W/50W/100W power draws.
- **Visualization**: T036 MUST render human baseline as a single horizontal line or range marker to respect zero-variance.