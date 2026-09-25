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
**⚠️ EXECUTION FLOW**: This phase follows the strict order: T060 → T012.0 → T012-Sens → T012-Design → T012-Runtime → T001.1 → T006.0-InitBundle → T006.1-LoadSubset → T006.2-Calc → T006.3-Select → T006.3-Retry → T015.1-GenAssets → T015.1-LogParams → T017 (baseline) → T017a (manipulated).

### Infrastructure Tasks

- [X] T004 Setup data directory structure: `data/stimuli/`, `data/responses/`, `data/processed/`, `data/stimuli_metadata/`, `data/ethics/`, `data/assets/`
- [X] T005 [P] Implement data checksum utilities in `code/data/checksum.py`
- [X] T013 [P] [US1] Implement Image Entity class in `code/data/image.py`: Define `Image` class with attributes `id`, `path`, `complexity_score`, `metadata_path`.
- [X] T014 [P] [US1] Implement Participant and Response Entity classes in `code/data/participant.py`: Define `Participant` (id, condition, timestamp) and `Response` (id, question_id, value, timestamp) classes.
- [X] T008 Configure logging infrastructure in `code/utils/logging.py`
- [X] T009 [P] Setup environment configuration management in `code/config.py`

### Power Analysis Sub-phase

- [X] T060 [P] [Shared-Infra] [Constitution-VI] [Plan:Scope-Boundary] **Scope Boundary Documentation (Create & Populate)**: Create `docs/ethics/scope_boundary.md` with required content. No dependency.

- [X] T012.0 [P] **Document Effect Size Source**: Append Section 2.1 to `research.md` with "Effect Size Assumption: Cohen's f=0.25 (medium) based on Loftus et al. (1974)". Verification: string present. Dependency: T060.

- [X] T012-Sens **Perform Sensitivity Analysis**: Implement `code/analysis/power.py` to vary effect sizes across a range from small to medium in fine-grained increments. Write `data/analysis/sensitivity_analysis.json` with schema `{"effect_sizes":[float],"required_n":[int],"power":[float]}`. Verification: file exists and matches schema. **Sequential** (no [P]).

- [X] T012-Design **Design‑Phase Power Analysis & Plan Update**: Using `data/analysis/sensitivity_analysis.json`, compute required sample size for Repeated‑Measures ANOVA via `statsmodels.stats.power.FTestAnovaPower`. Select the smallest effect size where `required_n >= 50`. Write `data/analysis/power_report.json` (`{"n_total_subjects":int,"effect_size":float,"power":float,"alpha":float,"power_insufficient":bool,"justification":str}`). Update `plan.md` to state design is "Repeated‑Measures (Within‑Subjects)" and analysis uses "Repeated‑Measures ANOVA". Verification: `power_report.json` exists, matches schema, and `plan.md` contains both phrases. Dependency: T012-Sens.

- [X] T012-Runtime **Power Analysis Validation Gate**: Verify `data/analysis/power_report.json` exists, `power_insufficient` is false, and `n_total_subjects >= 50`. On success create `data/analysis/power_gate_passed.txt` and log to `data/logs/power_gate.log`. On failure raise `SystemExit` with appropriate message, halting downstream tasks. Dependency: T012-Design.

- [X] T001.1 **Verify Plan Update**: After power gate passes, assert `plan.md` contains "Repeated‑Measures" and "Within‑Subjects". Output: updated `plan.md`. Dependency: T012-Runtime.

### Data Fetching & Asset Generation (Foundational)

- [X] T006.0-InitBundle [P] **Initialize Data Bundle Directory with Fallback Fetch**: Create `data/stimuli/raw_subset/`. If `manifest.sha256` missing/invalid, fetch a representative sample of Visual Genome images via `datasets.load_dataset("visual_genome", split="train", streaming=True)`, store subset, generate new `manifest.sha256`. Satisfies FR-001. No further dependency.

- [X] T006.1-LoadSubset [Shared-Infra] **Load Pre‑bundled Visual Genome Subset with Checksum Validation**: Implement `code/utils/data_loader.py` to validate `manifest.sha256`; on mismatch trigger T006.0-InitBundle logic. Output list of valid image paths to `data/stimuli/raw/`. Dependency: T006.0-InitBundle.

- [X] T006.2-Calc **Calculate Complexity Score**: Implement `code/stimuli/filter.py` to compute `baseline_complexity_score` using object density. Output stats to `data/processed/complexity_stats.json`. Dependency: T006.1-LoadSubset.

- [X] T006.3-Select **Select Representative Sample**: Deterministically attempt up to **3 attempts** to sample images such that Q1‑Q3 range ≥ 0.3. If after 3 attempts the condition is unmet, raise `SystemExit` with explicit error. Output selected images to `data/stimuli/raw/`. Dependency: T006.2-Calc.

- [X] T006.3-Retry **Retry Logic for Sample Selection**: If T006.3-Select fails, fetch a larger batch and re‑run selection (max total 3 attempts). Dependency: T006.3-Select.

- [X] T006.3-Complete **Aggregate Completion Marker**: Touch `data/stimuli/selection_complete.txt` after successful selection (whether via first try or retry). Dependency: T006.3-Select or T006.3-Retry.

- [X] T015.1-GenAssets [P] **Generate Semantic Minor Object Assets**: Create `code/stimuli/asset_generator.py`. `semantic_object_list.json` is an array of objects `{ "name": "<string>", "category": "<string|optional>" }`. Generate a set of PNG assets in `data/assets/minor_objects/obj_{i}.png`. Dependency: none.

- [X] T015.1-LogParams [P] **Write Asset Generation Log**: Write parameters to `data/assets/generation_log.json`. Dependency: T015.1-GenAssets.

- [X] T017 **Baseline Stimulus Metadata Generation**: Implement `code/stimuli/metadata.py` to create `data/stimuli/{id}_metadata.yaml` for each **baseline** image (from `data/stimuli/raw/`). Include `detail_level: baseline`, `manipulation_timestamp` (UTC ISO), and basic image attributes. No dependency on asset log. Verification: all baseline images have corresponding metadata file.

- [X] T017a **Manipulated Stimulus Metadata Generation**: After manipulation (T015/T016), generate metadata for **enhanced** and **reduced** images, incorporating asset parameters from `data/assets/generation_log.json`. Output files `data/stimuli/enhanced_{id}_metadata.yaml` and `data/stimuli/reduced_{id}_metadata.yaml`. Dependency: T015, T016, T015.1-LogParams.

### IRB Verification (New)

- [X] T027.0 **IRB Approval Check**: Verify existence of `data/ethics/irb_approval.txt`. If missing, raise `SystemExit` with message "IRB approval required before participant sessions." Dependency: None. This satisfies spec assumption about ethics before recruitment.

## Phase 3: User Story 1 - Image Manipulation Pipeline (Priority: P1) 🎯 MVP

### Tests for User Story 1 (OPTIONAL)

- [X] T050 [P] [US1] Unit test for image enhancement logic in `tests/unit/test_stimuli_manipulator.py`.
- [X] T051 [P] [US1] Unit test for image reduction logic in `tests/unit/test_stimuli_manipulator.py`.
- [X] T052 [P] [US1] Integration test for full pipeline in `tests/integration/test_stimuli_pipeline.py`.

### Implementation for User Story 1

- [X] T015 **Implement Enhanced Detail Compositing** (`code/stimuli/manipulator.py`). Depends on T015.1-GenAssets, T015.1-LogParams, T006.3-Select, T006.3-Retry. Handles errors, logs to `data/logs/manipulation_errors.log`.

- [X] T016 **Implement Reduced Detail Manipulation** (`code/stimuli/manipulator.py`). Same dependencies as T015.

- [X] T019 [P] [US1] Add error handling for missing metadata and failed fetches in `code/data/loader.py`.

- [X] T020 [P] [US1] Add CLI entry point for running the manipulation pipeline in `code/cli.py`.

- [X] T017a **Manipulated Stimulus Metadata Generation** (see Phase 2).

## Phase 4: User Story 2 - Participant Testing Interface (Priority: P2)

### Tests for User Story 2 (OPTIONAL)

- [X] T022 [P] [US2] Unit test for session state management.
- [X] T023 [P] [US2] Unit test for response generation logic.
- [X] T024 [P] [US2] Integration test for simulated session flow.

### Implementation for User Story 2

- [X] T027.1 **Generate Mock Object Pool**: `data/assets/mock_objects.json` with ≥50 distinct objects. No dependency.

- [X] T025 [P] **Implement View: Image Display** (`code/participants/interface.py`) – 10 s ±0.5 s.

- [X] T026 **Implement View: Distractor Task** (`code/participants/interface.py`) – 2 min ±10 s, flag incomplete if out of range.

- [X] T027.2 **Generate Recognition Questions** (`code/participants/interface.py`). Depends on T017 (baseline metadata), T017a (manipulated metadata), T027.1, T006.3-Select, T006.3-Retry. Extract true details from baseline metadata; false details from mock pool. If `false_pool` insufficient, write `data/sessions/{id}/questions.json` with `"status":"incomplete"` and reason. Otherwise write complete JSON with balanced true/false items.

- [X] T027.3 **Implement Response Capture** (`code/participants/session.py`). Depends on T027.2.

- [X] T029 **Local Caching & Retry for Network Timeouts** (`code/participants/session.py`).

- [X] T030 **Partial Session Recording & Dropout Flagging** (`code/participants/session.py`).

- [X] T031 **CLI entry point for simulated participant sessions** (`code/cli.py`).

## Phase 5: User Story 3 - Statistical Analysis and Results Generation (Priority: P3)

### Tests for User Story 3 (OPTIONAL)

- [X] T032 [P] Unit test for ANOVA calculation.
- [X] T033 [P] Unit test for multiple‑comparison correction.
- [X] T034 [P] Integration test for full analysis pipeline on mock data.

### Implementation for User Story 3

- [X] T038 **Dataset‑Variable Fit Check** (`code/analysis/stats.py`). Depends on T017, T017a, T027.3.

- [X] T035.1 **Calculate False Memory Rate per Condition** (`code/analysis/stats.py`). Depends on T027.3. Writes per‑condition rates to `data/analysis/anova_input.csv`.

- [X] T035a **Implement Repeated‑Measures ANOVA Script** (`code/analysis/anova.py`). Depends on T038, T012-Runtime, T001.1, T017a, T027.3, T035.1. Generates `data/analysis/anova_results.json` with required schema.

- [X] T035 **Run ANOVA** (`code/analysis/run_anova.py`). Calls T035a, then verifies `anova_results.json` exists.

- [X] T036 **Multiple‑Comparison Correction (Bonferroni)** (`code/analysis/stats.py`). Depends on T035.

- [X] T037 **Visualization Generation** (`code/analysis/viz.py`). Depends on T035.

- [X] T072.1 **Analysis Output: Limitations JSON Update**: Append `limitations` field to `anova_results.json` citing scope boundary (T060). Depends on T035.

- [X] T072.2 **Analysis Output: Limitations Documentation**: Update `research.md` with "Limitations: Associational Nature" citing T060. Depends on T072.1.

- [X] T082 **Add Mechanism Disclaimer to ANOVA Output**: Append `biological_context` field to `anova_results.json` citing T080/T081. Depends on T035.

- [X] T098 **Add Hypothesis Gap Disclaimer to ANOVA Output**: Ensure `anova_results.json` exists (create placeholder if missing), then append `hypothesis_gap` field with required text. Depends on T035 (or creates file if absent). No longer blocked by prior failures.

- [X] T039 **CLI entry point for running analysis** (`code/cli.py`). Depends on T035, T036, T037.

## Phase 6: Review Response - Mechanism Clarification (Priority: P3)

- [X] T080 **Update Scope Boundary with "Ladder of Explanation"** (depends on T060).

- [X] T081 **Update Research Plan with "Mechanism Gap" Analysis** (depends on T080).

- [X] T082 **Add Mechanism Disclaimer to ANOVA Output** (updated above).

## Phase 7: Review Response - Ladder of Explanation Gap (Priority: P3)

- [X] T093 **Document "Ladder of Explanation" Gap in Research Plan** (depends on T080, T081).

- [X] T094 **Add Biological Context to Ethics Scope Boundary** (depends on T093, T060).

- [X] T095 **Analysis Output: Biological Context Disclaimer** (depends on T035, T080, T081).

## Phase 8: Review Response - Synaptic Hypothesis Gap (Priority: P3)

- [X] T096 **Update Plan.md with Ladder of Explanation & Synaptic Gap**: Independent of ANOVA. Depends on T060. Verification: `plan.md` contains phrases "ladder of explanation" and "serotonin → cAMP → PKA → CREB". No dependency on T035.

- [X] T097 **Update Ethics Scope Boundary with "Hypothesis Gap" Statement**: Depends on T060. Verification: `docs/ethics/scope_boundary.md` contains "No Cellular Correlate Claimed" and "ladder of explanation".

- [X] T098 **Add Hypothesis Gap Disclaimer to ANOVA Output**: Independent of ANOVA success; creates `anova_results.json` if missing, then appends `hypothesis_gap` field with required text. Depends on T060 for wording but not on T035.

## Phase 9: Mechanism Mapping & Biological Context Integration (Priority: P3)

**Goal**: Address the "Eric Kandel" review by explicitly mapping the visual detail manipulation to potential synaptic mechanisms, acknowledging the gap while defining the theoretical framework.

**Independent Test**: Verify that `research.md` and `docs/ethics/scope_boundary.md` contain the specific "Ladder of Explanation" text and the proposed molecular pathway (serotonin/cAMP/PKA/CREB) as a *hypothesis for future investigation*, not a measured result.

### Implementation for Mechanism Mapping

- [ ] T100 [P] **Define Molecular Hypothesis in Research Plan**: Append Section 4.2 to `research.md` titled "Proposed Molecular Correlates". Explicitly state: "While this study measures behavioral false memory rates, we hypothesize that increased visual detail may modulate synaptic efficacy in the visual cortex/hippocampus via serotonergic pathways, analogous to the cAMP/PKA/CREB cascade observed in Aplysia sensitization." Dependency: T080, T081.

- [ ] T101 [P] **Update Ethics Scope Boundary with Mechanism Disclaimer**: Update `docs/ethics/scope_boundary.md` to include a "Mechanism Gap" section. Explicitly state: "This study does not measure synaptic changes (e.g., protein synthesis, receptor trafficking). The link between visual detail and memory is observed behaviorally; the cellular mechanism remains a hypothesis to be tested in future neurophysiological studies." Dependency: T060, T100.

- [ ] T102 [P] **Generate Mechanism Visualization**: Create `code/analysis/viz_mechanism.py` to generate a schematic diagram (saved to `data/assets/mechanism_ladder.png`) illustrating the "Ladder of Explanation" (Behavior → Cells → Synapses → Molecules) and marking the current study's position (Behavior) vs. the proposed gap (Molecules). Dependency: T037 (for viz utilities), T100.

- [ ] T103 [P] **Update ANOVA Output with Biological Context**: Ensure `data/analysis/anova_results.json` includes a `mechanism_hypothesis` field containing the text from T100. Dependency: T035, T100.

- [ ] T104 [P] **Documentation: Ladder of Explanation in Quickstart**: Update `docs/quickstart.md` to include a section "Theoretical Framework" that explains the study's position on the "Ladder of Explanation" and explicitly disclaims causal claims about synaptic mechanisms. Dependency: T101, T049.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T045.1 **Refactor error handling into utility module** (`code/utils/error_handling.py`). Depends on T019.
- [X] T045.2 **Extract magic numbers to `code/config.py`**. Depends on T009.
- [X] T046-A **Performance Profiling** (`code/utils/profiler.py`). Depends on T015, T016.
- [X] T046-B **Performance Optimization** (target <30 s/image). Depends on T046-A.
- [X] T047 **Additional unit tests for edge cases** (`tests/unit/`). Depends on T027.3, T035.
- [X] T048 **Security hardening (PII leakage)**. Depends on T010, T027.3.
- [X] T049 **Run quickstart validation** (`code/cli.py --validate-quickstart`). Depends on T060, T046-B.

## Phase Dependencies

(unchanged – see original plan)
