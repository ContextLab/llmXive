# Tasks: Visual Detail and False Memory Susceptibility

**Input**: Design documents from `/specs/001-visual-detail-false-mem/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `projects/PROJ-317-the-impact-of-visual-detail-false-mem/` by running: `mkdir -p data/stimuli data/stimuli_metadata data/responses data/processed data/ethics data/assets code/data code/stimuli code/participants code/analysis tests/unit tests/integration tests/contract docs/ethics`.

- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Fetching, Asset Generation, and Power Analysis.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ EXECUTION FLOW**: This phase follows the strict order: T000-ResolveDesign → T060 → T012.0 → T012-Sens → T012-Design → T012-Runtime → T001.1 → T006.0-InitBundle → T006.1-LoadSubset → T006.2-Calc → T006.3-Select → T006.3-Retry → T006.3-Complete → T015.1-GenAssets → T015.1-LogParams → T017 (baseline).

### Design Resolution & Infrastructure

- [ ] T000-ResolveDesign [S] **Resolve Design Mismatch (Plan vs Spec)**: Update `plan.md` Summary and Technical Context to explicitly state "Repeated-Measures (Within-Subjects) design" and "Repeated-Measures ANOVA" to match spec.md SC-002 and US-3. Remove all references to "Between-Subjects" and "One-Way ANOVA". **Verification**: `plan.md` contains exact phrases "Repeated-Measures (Within-Subjects)" and "Repeated-Measures ANOVA" in Summary. Dependency: None. This task resolves the circular dependency where downstream tasks assume a plan state that contradicts the current document.

### Infrastructure Tasks

- [X] T004 Setup data directory structure: `data/stimuli/`, `data/responses/`, `data/processed/`, `data/stimuli_metadata/`, `data/ethics/`, `data/assets/`
- [X] T005 [P] Implement data checksum utilities in `code/data/checksum.py`
- [X] T013 [P] [US1] Implement Image Entity class in `code/data/image.py`: Define `Image` class with attributes `id`, `path`, `complexity_score`, `metadata_path`.
- [X] T014 [P] [US1] Implement Participant and Response Entity classes in `code/data/participant.py`: Define `Participant` (id, condition, timestamp) and `Response` (id, question_id, value, timestamp) classes.
- [X] T008 Configure logging infrastructure in `code/utils/logging.py`
- [X] T009 [P] Setup environment configuration management in `code/config.py`

### Power Analysis Sub-phase

- [X] T060 [P] [Shared-Infra] [Constitution-VI] [Plan:Scope-Boundary] **Scope Boundary Documentation (Create & Populate)**: Create `docs/ethics/scope_boundary.md` with required content. No dependency.

- [X] T012.0 [P] **Document Effect Size Source & Validate**: Append Section 2.1 to `research.md` with "Effect Size Assumption: Cohen's f=0.25 (medium) based on Loftus et al. (1974) ". **Validation**: Before T012-Sens begins, verify the claim source is valid. If validation fails, flag as "unresolved" and halt T012-Sens. Verification: string present in Section 2.1 and validation log exists. Dependency: T060. Note: This is a design parameter for power calculation, not a measured result.

- [ ] T012.0-ValidateClaim [S] **Validate Effect Size Claim**: Verify the claim source in T012.0 is valid. If validation fails, raise `SystemExit` with message "Effect size claim validation failed". Dependency: T012.0.

- [X] T012-Sens [S] **Perform Sensitivity Analysis**: Implement `code/analysis/power.py` to vary effect sizes across a range from small to medium in fine-grained increments. Write `data/analysis/sensitivity_analysis.json` with schema `{"effect_sizes":[float],"required_n":[int],"power":[float]}`. Verification: file exists and matches schema. **Sequential** (no [P]). Dependency: T012.0-ValidateClaim.

- [X] T012-Design [S] **Design‑Phase Power Analysis & Plan Update**: Using `data/analysis/sensitivity_analysis.json`, compute required sample size for Repeated‑Measures ANOVA via `statsmodels.stats.power.FTestAnovaPower`. Select the smallest effect size where `required_n >= 50`. Write `data/analysis/power_report.json` (`{"n_total_subjects":int,"effect_size":float,"power":float,"alpha":float,"power_insufficient":bool,"justification":str}`). Dependency: T012-Sens.

- [X] T012-Runtime [S] **Power Analysis Validation Gate**: Verify `data/analysis/power_report.json` exists, `power_insufficient` is false, and `n_total_subjects >= 50`. On success create `data/analysis/power_gate_passed.txt` and log to `data/logs/power_gate.log`. On failure raise `SystemExit` with appropriate message, halting downstream tasks. Dependency: T012-Design.

- [X] T001.1 [S] **Verify Plan Update**: After power gate passes, assert `plan.md` contains "Repeated‑Measures" and "Within‑Subjects". Output: updated `plan.md`. Dependency: T012-Runtime.

### Data Fetching & Asset Generation (Foundational)

- [X] T006.0-InitBundle [P] **Initialize Data Bundle Directory with Fallback Fetch**: Create `data/stimuli/raw_subset/`. If `manifest.sha256` missing/invalid, fetch a representative sample of Visual Genome images via `datasets.load_dataset("visual_genome", split="train", streaming=True)`, store subset, generate new `manifest.sha256`. Satisfies FR-001. No further dependency.

- [X] T006.1-LoadSubset [Shared-Infra] **Load Pre‑bundled Visual Genome Subset with Checksum Validation**: Implement `code/utils/data_loader.py` to validate `manifest.sha256`; on mismatch trigger T006.0-InitBundle logic. Output list of valid image paths to `data/stimuli/raw/`. Dependency: T006.0-InitBundle.

- [X] T006.2-Calc **Calculate Complexity Score**: Implement `code/stimuli/filter.py` to compute `baseline_complexity_score` using object density. Output stats to `data/processed/complexity_stats.json`. Dependency: T006.1-LoadSubset.

- [X] T006.3-Select **Select Representative Sample**: Deterministically attempt up to **3 attempts** to sample images such that Q1‑Q3 range ≥ 0.3. If after 3 attempts the condition is unmet, raise `SystemExit` with explicit error. Output selected images to `data/stimuli/raw/`. Dependency: T006.2-Calc.

- [X] T006.3-Retry [S] **Retry Logic for Sample Selection**: If T006.3-Select fails, increase sample size by [deferred] per retry, max 3 retries, and re‑run selection. Dependency: T006.3-Select (on failure).

- [X] T006.3-Complete **Aggregate Completion Marker**: Touch `data/stimuli/selection_complete.txt` after successful selection (whether via first try or successful retry loop). Dependency: T006.3-Select OR T006.3-Retry (on success).

- [X] T015.1-GenAssets [P] **Generate Semantic Minor Object Assets**: Create `code/stimuli/asset_generator.py`. `semantic_object_list.json` is an array of objects `{ "name": "<string>", "category": "<string|optional>" }`. Generate a set of PNG assets in `data/assets/minor_objects/obj_{i}.png`. **Dependency**: T060 (Scope Boundary Documentation) which defines minor object categories. Dependency: T060.

- [X] T015.1-LogParams [P] **Write Asset Generation Log**: Write parameters to `data/assets/generation_log.json`. Dependency: T015.1-GenAssets.

- [X] T017 [P] **Baseline Stimulus Metadata Generation**: Implement `code/stimuli/metadata.py` to create `data/stimuli/{id}_metadata.yaml` for each **baseline** image (from `data/stimuli/raw/`). Include `detail_level: baseline`, `manipulation_timestamp` (UTC ISO), and basic image attributes. No dependency on asset log. Verification: all baseline images have corresponding metadata file.

### IRB Verification (Conditional)

- [ ] T027.0 [S] **IRB Approval Check**: Check if `data/responses/` contains any files with real participant data (non-empty, non-mock). If real data exists, verify existence of `data/ethics/irb_approval.txt`. If missing and real data present, raise `SystemExit` with message "IRB approval required before participant sessions." If no real data (mock/CI mode), log warning and proceed. Dependency: None. This satisfies spec assumption about ethics before recruitment while allowing CI validation.

## Phase 3: User Story 1 - Image Manipulation Pipeline (Priority: P1) 🎯 MVP

### Tests for User Story 1 (OPTIONAL)

- [X] T050 [P] [US1] Unit test for image enhancement logic in `tests/unit/test_stimuli_manipulator.py`. Must include functions `test_enhance_adds_objects` and `test_reduce_removes_objects`.
- [X] T051 [P] [US1] Unit test for image reduction logic in `tests/unit/test_stimuli_manipulator.py`.
- [X] T052 [P] [US1] Integration test for full pipeline in `tests/integration/test_stimuli_pipeline.py`.

### Implementation for User Story 1

- [ ] T015 **Implement Enhanced Detail Compositing** (`code/stimuli/manipulator.py`). Depends on T015.1-GenAssets, T015.1-LogParams, T006.3-Select, T006.3-Retry. **Verification**: For each baseline image in `data/stimuli/raw/`, generate a corresponding `data/stimuli/enhanced_{id}.png`. Log all errors to `data/logs/manipulation_errors.log`. Handles errors, logs to `data/logs/manipulation_errors.log`. Verify `data/stimuli/enhanced_{id}.png` exists for all baselines.

- [ ] T016 **Implement Reduced Detail Manipulation** (`code/stimuli/manipulator.py`). Same dependencies as T015.

- [X] T019 [P] [US1] Add error handling for missing metadata and failed fetches in `code/data/loader.py`.

- [X] T020 [P] [US1] Add CLI entry point for running the manipulation pipeline in `code/cli.py`.

- [ ] T017a **Manipulated Stimulus Metadata Generation**: After manipulation (T015/T016), generate metadata for **enhanced** and **reduced** images. **Output Schema**: `data/stimuli/enhanced_{id}_metadata.yaml` and `data/stimuli/reduced_{id}_metadata.yaml` MUST include: `detail_level` (enhanced/reduced), `object_list` (list of added/removed objects), `texture_settings` (blur/contrast params), `manipulation_timestamp` (UTC ISO). **Verification**: All enhanced and reduced images have corresponding metadata files with required fields. Dependency: T015, T016, T015.1-LogParams.

## Phase 4: User Story 2 - Participant Testing Interface (Priority: P2)

### Tests for User Story 2 (OPTIONAL)

- [ ] T022 [P] [US2] Unit test for session state management.
- [ ] T023 [P] [US2] Unit test for response generation logic.
- [ ] T024 [P] [US2] Integration test for simulated session flow.

### Implementation for User Story 2

- [ ] T027.1-ContextualLures **Generate Contextual False Details** (`code/participants/interface.py`). **Logic**: For each baseline image, query Visual Genome metadata for objects NOT present in the specific baseline image's metadata. Select a random subset of these "contextual lures" to serve as false details. Ensure no overlap with baseline image metadata. Output `data/sessions/{id}/questions.json` with `"status":"complete"` if sufficient lures are found, or `"status":"incomplete"` if not. **Dependency**: T017 (baseline metadata), T006.1-LoadSubset, T060 (Scope Boundary Documentation).

- [ ] T025 [P] **Implement View: Image Display** (`code/participants/interface.py`) – Implement View: Image Display (code/participants/interface.py) – 10 s ±0.5 s.

- [ ] T026 **Implement View: Distractor Task** (`code/participants/interface.py`) – Implement View: Distractor Task (code/participants/interface.py) – 2 min ±10 s, flag incomplete if out of range.

- [X] T027.2 **Generate Recognition Questions** (`code/participants/interface.py`). Depends on T017 (baseline metadata), T017a (manipulated metadata), T027.1-ContextualLures, T006.3-Select, T006.3-Retry. Extract true details from baseline metadata; false details from T027.1-ContextualLures. Write `data/sessions/{id}/questions.json` with balanced true/false items. **Note**: T017a must complete successfully before T027.2 begins.

- [ ] T027.3 **Implement Response Capture** (`code/participants/session.py`). Depends on T027.2.

- [ ] T029 **Local Caching & Retry for Network Timeouts** (`code/participants/session.py`).

- [ ] T030 **Partial Session Recording & Dropout Flagging** (`code/participants/session.py`).

- [ ] T031 **CLI entry point for simulated participant sessions** (`code/cli.py`).

## Phase 5: User Story 3 - Statistical Analysis and Results Generation (Priority: P3)

### Tests for User Story 3 (OPTIONAL)

- [ ] T032 [P] Unit test for ANOVA calculation.
- [ ] T033 [P] Unit test for multiple‑comparison correction.
- [ ] T034 [P] Integration test for full analysis pipeline on mock data.

### Implementation for User Story 3

- [ ] T038 **Dataset‑Variable Fit Check** (`code/analysis/stats.py`). **Verification**: Generate `data/analysis/dataset_variable_fit.json` with schema `{"status":"pass|fail","missing_vars":[str],"details":str}`. Write `data/analysis/dataset_fit_check.txt` with status: pass/fail. Depends on T017, T017a, T027.3.

- [X] T035.1 **Calculate False Memory Rate per Condition** (`code/analysis/stats.py`). Depends on T027.3. Writes per‑condition rates to `data/analysis/anova_input.csv`.

- [X] T035a **Implement Repeated‑Measures ANOVA Script** (`code/analysis/anova.py`). Depends on T038, T012-Runtime, T001.1, T017a, T027.3, T035.1. Generates `data/analysis/anova_results.json` with required schema.

- [ ] T035 **Run ANOVA** (`code/analysis/run_anova.py`). Calls T035a, then verifies `anova_results.json` exists.

- [ ] T036 **Multiple‑Comparison Correction (Bonferroni)** (`code/analysis/stats.py`). Depends on T035.

- [ ] T037 **Visualization Generation** (`code/analysis/viz.py`). Depends on T035.

- [ ] T072.1 **Analysis Output: Limitations JSON Update**: Append `limitations` field to `anova_results.json` citing scope boundary (T060). Depends on T035.

- [ ] T072.2 **Analysis Output: Limitations Documentation**: Update `research.md` with "Limitations: Associational Nature" citing T060. Depends on T072.1.

- [ ] T039 **CLI entry point for running analysis** (`code/cli.py`). Depends on T035, T036, T037.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T045.1 **Refactor error handling into utility module** (`code/utils/error_handling.py`). Depends on T019.
- [X] T045.2 **Extract magic numbers to `code/config.py`**. Depends on T009.
- [X] T046-A **Performance Profiling** (`code/utils/profiler.py`). Depends on T015, T016.
- [X] T046-B **Performance Optimization** (target <30 s/image). Depends on T046-A.
- [X] T047 **Additional unit tests for edge cases** (`tests/unit/`). Depends on T027.3, T035.
- [X] T048 **Security hardening (PII leakage)**. Depends on T010, T027.3.
- [X] T049 **Run quickstart validation** (`code/cli.py --validate-quickstart`). Depends on T060, T046-B.

**Note**: Cellular Correlate Hypothesis (Kandel et al.) removed from implementation scope; to be discussed as secondary limitation in research.md if IRB approved for future study.

## Phase Dependencies

(unchanged – see original plan)