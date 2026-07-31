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
**⚠️ EXECUTION FLOW**: This phase follows the strict order: T060 (Scope Lock) → T012.0 (Effect Size Doc) → T012-Sens (Sensitivity) → T012-Calc (Power Calc) → T012-Runtime (Gate) → T006.0-InitBundle → T006.1-LoadSubset → T006.2-Calc → T006.3-Filter → T015.1-Script → T015.1-Run → T017.

**⚠️ DESIGN CONFLICT RESOLUTION**: The Plan (plan.md:Summary) explicitly mandates a "Between-Subjects design" using "One-Way ANOVA". The Spec (spec.md:FR-005, SC-001) mandates a "Repeated-Measures ANOVA" (within-subjects). **Tasks T012-Calc and T035 implement the Spec-compliant "Repeated-Measures" design**, overriding the Plan's contradictory design to satisfy FR-005. The Plan is flagged for immediate revision.

### Infrastructure Tasks

- [X] T004 Setup data directory structure: `data/stimuli/`, `data/responses/`, `data/processed/`, `data/stimuli_metadata/`, `data/ethics/`, `data/assets/`
- [X] T005 [P] Implement data checksum utilities in `code/data/checksum.py`
- [X] T013 [P] [US1] Implement Image Entity class in `code/data/image.py`: Define `Image` class with attributes `id`, `path`, `complexity_score`, `metadata_path`.
- [X] T014 [P] [US1] Implement Participant and Response Entity classes in `code/data/participant.py`: Define `Participant` (id, condition, timestamp) and `Response` (id, question_id, value, timestamp) classes.
- [X] T008 Configure logging infrastructure in `code/utils/logging.py`
- [X] T009 [P] Setup environment configuration management in `code/config.py`

### Power Analysis Sub-phase

**⚠️ ATOMIC UNIT**: T012.0, T012-Sens, and T012-Calc must be treated as a single atomic unit. Documentation of effect size source, sensitivity analysis, and calculation must be completed before the gate T012-Runtime can execute.

- [X] T060 [P] [Shared-Infra] [Constitution-VI] [Plan:Scope-Boundary] **Scope Boundary Documentation (Create & Populate)**: Create `docs/ethics/scope_boundary.md`. **Content**: Explicitly state that this study measures *behavioral* false memory rates and does not measure or infer specific molecular/cellular mechanisms (e.g., CREB activation, synaptic weight changes) in humans. Cite Constitution VI and the "Observational design" constraint. Include a section "Theoretical Framework: Constructive Memory vs. Biological Mechanism" citing Loftus et al. and Schacter. **Dependency**: None. **Note**: This task must be completed before T012.0 to lock the scope for power analysis.
- [X] T012.0 [P] [Shared-Infra] **Document Effect Size Source**: Update `research.md` by appending **Section 2.1** with the text: "Effect Size Assumption: Cohen's f=0.25 (medium) based on Loftus et al. (1974) 'The Misinformation Effect'. " **Verification**: Assert `research.md` contains the string "Cohen's f=0.25". **Output**: `research.md` contains Section 2.1. **Dependency**: T060.
- [ ] T012-Sens [Shared-Infra] [US1] **Perform Sensitivity Analysis**: Implement `code/analysis/power.py` to perform a sensitivity analysis for Repeated-Measures ANOVA. **Algorithm**: Vary effect size from 0.1 to 0.4 and calculate required sample size for each. **Output**: Write results to `data/analysis/sensitivity_analysis.json` with keys `effect_sizes`, `required_n`, `power`. **Verification**: Assert `data/analysis/sensitivity_analysis.json` exists. **Dependency**: T012.0.
- [ ] T012-Calc [Shared-Infra] [US1] **Implement Power Analysis (Design Phase) for Repeated-Measures ANOVA**: Implement `code/analysis/power.py` to calculate required sample size for a **Repeated-Measures** design (within-subjects). **Algorithm**: Use `statsmodels.stats.power.FTestAnovaPower` (or equivalent repeated-measures power calculation) with `effect_size` **SELECTED FROM** `data/analysis/sensitivity_analysis.json` (generated by T012-Sens). **Selection Logic**: Read the sensitivity output and select the `effect_size` value corresponding to the minimum `required_n` that satisfies `required_n >= 50`. If no value satisfies N>=50, use the effect size for the largest N available and flag `power_insufficient`. **Constraint**: If calculated `n_total_subjects` < 50, set `power_insufficient` to `true` **and** include the numeric value for downstream validation. **Output**: Write results to `data/analysis/power_report.json` with keys `n_total_subjects`, `effect_size`, `power`, `alpha`, `power_insufficient` (boolean), `justification` (string referencing T012-Sens and the selection logic). **Schema**: `{"n_total_subjects": int, `effect_size`: float, `power`: float, `alpha`: float, `power_insufficient`: bool, `justification`: string}`. **Verification**: Assert `data/analysis/power_report.json` exists and matches the schema. **Dependency**: T012.0, T060, T012-Sens.
- [ ] T012-Runtime [Shared-Infra] [US1] [Gate] **Power Analysis Validation Logic**: Implement the validation logic in `code/analysis/power.py` to (1) check for existence of `data/analysis/power_report.json`, (2) verify that `power_insufficient` is `false`, and (3) ensure `n_total_subjects >= 50`. **Constraint**: If any check fails, raise `SystemExit` with message "Power Analysis Failed: Insufficient sample size (N < 50) or power criteria not met." This logic blocks ALL subsequent data collection phases (US1, US2, US3) until it passes. **Output**: If successful, create `data/analysis/power_gate_passed.txt` and log success to `data/logs/power_gate.log`. **Dependency**: T012-Calc.

### Data Fetching & Asset Generation (Moved to Foundational)

- [ ] T006.0-InitBundle [P] [Shared-Infra] **Initialize Data Bundle Directory**: Create `data/stimuli/raw_subset/` directory and generate a placeholder `manifest.sha256` file with a hash of "EMPTY_BUNDLE" or a note indicating the bundle is pre-bundled. **Constraint**: This task ensures the directory and manifest exist for T006.1. **Output**: `data/stimuli/raw_subset/` and `data/stimuli/raw_subset/manifest.sha256`. **Dependency**: None.
- [ ] T006.1-LoadSubset [Shared-Infra] [FR-001] **Load Pre‑bundled Visual Genome Subset with Checksum Validation**: Implement `code/utils/data_loader.py` to load a pre‑bundled subset of Visual Genome images from `data/stimuli/raw_subset/`. **Constraint**: Verify a secure hash manifest file exists: `data/stimuli/raw_subset/manifest.sha256`. Compute the SHA-256 checksum of the subset directory and compare against the manifest. If the checksum mismatches or the manifest is missing, raise a critical `SystemExit` error (no fallback download). Output the list of valid image paths to `data/stimuli/raw/`. **Dependency**: T006.0-InitBundle.
- [X] T006.2-Calc [Shared-Infra] [FR-001] **Calculate Complexity Score**: Implement `code/stimuli/filter.py` to calculate `baseline_complexity_score` for downloaded images based on object density (count of objects per image). **Algorithm**: Filter the fetched image set to ensure the Q1‑Q3 range is ≥ 0.3 (target mean=0.5, std=0.15). **Constraint**: Complexity is derived from existing image annotations. Output stats to `data/processed/complexity_stats.json`. **Dependency**: T006.1-LoadSubset.
- [ ] T006.3-Filter [Shared-Infra] [FR-001] **Select Representative Sample**: Implement selection logic in `code/stimuli/filter.py` to select images spanning Q1‑Q3. **Algorithm**: Randomly sample images with replacement from the fetched batch until the Q1‑Q3 range ≥ 0.3 is met. **Constraint**: If the specific complexity range (Q1‑Q3 ≥ 0.3) is NOT met in the fetched batch, log a CRITICAL error and fetch a larger batch (next 1000 images). Retry up to 3 times. If all retries fail, raise `SystemExit`. Output filtered images to `data/stimuli/raw/`. **Dependency**: T006.2-Calc.
- [X] T006.4-Resample [P] [Shared-Infra] [FR-001] **Resample on Failure**: Implement retry logic in `code/stimuli/filter.py` to handle T006.3-Filter failures. If T006.3-Filter fails the Q1‑Q3 check, fetch a larger batch (e.g., next 1000 images) and re‑run the filter. **Constraint**: Max 3 retry attempts. If all fail, raise `SystemExit`. **Dependency**: T006.3-Filter.
- [ ] T015.1-Script [P] [Shared-Infra] **Generate Minor Object Assets (Script)**: Create a script in `code/stimuli/asset_generator.py` to generate a set of minor object PNG assets. **Schema**: Assets must be valid PNGs with alpha channel. **Dimensions**: 64x64 pixels. **Naming**: `obj_{id}.png`. **Geometry**: Circles (radius 10‑20px), Squares (side 10‑20px), Triangles. **Colors**: Random distinct colors. **Background**: Transparent (RGBA mode). **Logic**: Generate **exactly 20** distinct objects. Save to `data/assets/minor_objects/`. **Dependency**: None.
- [ ] T015.1-Run [Shared-Infra] **Execute Asset Generation**: Run `code/stimuli/asset_generator.py` to generate the assets in `data/assets/minor_objects/`. **Verification**: Assert exactly 20 valid PNG files exist in `data/assets/minor_objects/`. If count != 20, raise `SystemExit`. **Output**: 20 PNG files in `data/assets/minor_objects/`. **Dependency**: T015.1-Script.
- [ ] T017 [Shared-Infra] [US1] **Implement Stimulus Metadata Generation**: Implement `code/stimuli/metadata.py` to generate metadata files for each baseline image. **Content**: Store `detail_level`, `object_list`, `texture_settings`, `timestamp`, AND **`manipulation_timestamp`** (ISO 8601 format). **Output**: `data/stimuli/{id}_metadata.yaml` (directly inside `data/stimuli/` per Constitution VII). **Verification**: Assert `manipulation_timestamp` is present in all generated files. **Dependency**: T006.3-Filter.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Image Manipulation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Researcher uploads baseline images and receives two manipulated versions per image (enhanced and reduced detail).

**Independent Test**: Can be fully tested by running the image manipulation script on multiple sample images and verifying output files exist with correct detail modifications.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T050 [P] [US1] Unit test for image enhancement logic in `tests/unit/test_stimuli_manipulator.py`: Implement `test_add_minor_objects()`. Assert that `output_image.shape == (512, 512, 3)` (fixed dimensions) and `object_count == 5` after calling `add_minor_objects()`.
- [X] T051 [P] [US1] Unit test for image reduction logic in `tests/unit/test_stimuli_manipulator.py`: Implement `test_remove_minor_elements()`. Assert that `std_dev(output_region) < 0.1 * std_dev(input_region)` where `input_region` is the masked area of the original image and `output_region` is the same area after blurring.
- [X] T052 [P] [US1] Integration test for full pipeline (generate → manipulate → metadata) in `tests/integration/test_stimuli_pipeline.py`: Implement `test_full_pipeline()`. Assert that at least 1 metadata file and 2 manipulated images (enhanced/reduced) are created for each input image.

### Implementation for User Story 1

- [ ] T015 [US1] Implement enhanced detail compositing with error handling in `code/stimuli/manipulator.py`: Use PIL/Pillow to overlay a small number of minor object PNG assets (generated by T015.1-Run) onto baseline images (from T006.3-Filter). **Source**: Assets loaded from `data/assets/minor_objects/`. **Verification**: Assert exactly 20 PNG files exist in `data/assets/minor_objects/` before proceeding. If assets are missing, raise `SystemExit`. **Selection**: Randomly select a small number of assets per image. **Error Handling**: If manipulation fails for an image, skip the image, log the error to `data/logs/manipulation_errors.log`, and continue processing the remaining images. Do NOT abort the pipeline. **Dependency**: T015.1-Run (Output: assets exist), T006.3-Filter.
- [ ] T016 [US1] Implement reduced detail manipulation with error handling in `code/stimuli/manipulator.py`: Use Gaussian blur (radius=5) or masking to remove minor elements from baseline images. **Error Handling**: If manipulation fails for an image, skip the image, log the error to `data/logs/manipulation_errors.log`, and continue processing the remaining images. Do NOT abort the pipeline. **Dependency**: T006.3-Filter, T015.1-Run (to ensure pipeline context is valid).
- [X] T019 [P] [US1] Add error handling for missing metadata and failed fetches in `code/data/loader.py`: If a real dataset fetch (if implemented) fails or metadata is missing, skip the image and log the error.
- [ ] T020 [P] [US1] Add CLI entry point for running the manipulation pipeline in `code/cli.py`

**Dependency Note for T015.1**: T015.1-Run is a prerequisite ONLY for T015 (Enhanced detail compositing) and T016 (Reduced detail) to ensure both versions are generated. This is a targeted dependency for asset generation, not a shared prerequisite for the entire US1 group.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Participant Testing Interface (Priority: P2)

**Goal**: Participant views baseline image, completes distractor task, and answers recognition questions (true vs. false details).

**Independent Test**: Can be fully tested by simulating a single participant session end-to-end and verifying that all responses are recorded correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US2] Unit test for session state management in `tests/unit/test_session.py`
- [X] T023 [P] [US2] Unit test for response generation logic in `tests/unit/test_interface.py`
- [X] T024 [P] [US2] Integration test for simulated session flow in `tests/integration/test_session_flow.py`

### Implementation for User Story 2

- [X] T027.1 [P] [US2] Generate mock object pool: Create `data/assets/mock_objects.json` containing a list of distinct object names and categories (e.g., `[{ "object_name": "red car", "category": "vehicle" }]`). **Constraint**: Generate >= 50 distinct objects to ensure T027.2 can meet the 10/10 split requirement. **Dependency**: None.
- [X] T025 [P] [US2] [Model:View] **Implement View: Image Display**: Implement `code/participants/interface.py` to display baseline images for 10 seconds (±0.5s). **Logic**: Timer‑based display. **Dependency**: None.
- [X] T026 [US2] [Model:View] **Implement View: Distractor Task**: Implement `code/participants/interface.py` to administer arithmetic questions for 2 minutes (±10s). **Constraint**: If duration is outside the acceptable range, **Flag session as Incomplete** in the response log. Do NOT continue silently. **Dependency**: None.
- [ ] T027.2 [US2] [Model:Gen] **Generate Recognition Questions (Strict)**: Implement `code/participants/interface.py` to extract true details from `data/stimuli/{id}_metadata.yaml` (T017). Generate false/lure details by selecting from `data/assets/mock_objects.json` (T027.1) and filtering out items present in the baseline (using T006.3-Filter output). **Algorithm**: 1. Extract true objects from image metadata. 2. Filter mock pool to remove true objects. 3. Select a balanced set of true and false items (target equal numbers of true and false). 4. If len(true_pool) < 10 OR len(false_pool) < 10, **Flag session as incomplete** and write `data/sessions/{id}/questions.json` with `status: "incomplete"` and available questions. **Do NOT raise SystemExit**. **Constraint**: Must generate a balanced set if possible. **Output**: `data/sessions/{id}/questions.json` with schema: `{"status": "complete|incomplete", "questions": [{"id": str, "type": "true|false", "text": str}]}`. **Dependency**: T017, T027.1, T006.3-Filter.
- [X] T027.3 [US2] [Model:Capture] **Implement Response Capture**: Implement `code/participants/session.py` to record responses with timestamps. **Dependency**: T027.2.
- [X] T029 [US2] Implement local caching and retry logic for network timeouts in `code/participants/session.py`
- [X] T030 [US2] Implement partial session recording and flagging for dropouts in `code/participants/session.py`
- [X] T031 [US2] Add CLI entry point for running simulated participant sessions in `code/cli.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Results Generation (Priority: P3)

**Goal**: System executes Repeated-Measures ANOVA and generates visualization with confidence intervals.

**Independent Test**: Can be fully tested by running the analysis script on synthetic/mock participant data and verifying ANOVA results and visualization are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for ANOVA calculation in `tests/unit/test_stats.py`
- [X] T033 [P] [US3] Unit test for multiple‑comparison correction in `tests/unit/test_stats.py`
- [X] T034 [P] [US3] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 3

- [X] T038 [US3] Implement dataset‑variable fit check (compare mock distribution to target) in `code/analysis/stats.py`: **Dependency**: T017, T027.3.
- [X] T035.1 [US3] **Calculate False Memory Rate per Condition Group**: Implement `code/analysis/stats.py` to compute false‑memory rate for each condition (Baseline, Enhanced, Reduced). **Formula**: `false_memory_rate = count(false_positives) / count(total_lure_questions)` computed separately per condition. **Output**: Add per‑condition rates to `data/analysis/anova_results.json`. **Dependency**: T027.3.
- [ ] T035 [US3] **Implement Repeated-Measures ANOVA**: Implement `code/analysis/anova.py`. **Input Format**: Long‑format dataframe with columns `participant_id`, `condition` (Baseline/Enhanced/Reduced), `false_memory_rate`. **Algorithm**: Use `statsmodels.stats.anova.mixed_anova` (or equivalent repeated-measures ANOVA) to compare conditions. **Note**: This task overrides the Plan's "Between-Subjects/One-Way ANOVA" mandate to satisfy Spec FR-005. **Output**: Write results to `data/analysis/anova_results.json` with keys `f_statistic`, `p_value`, `effect_size`, `degrees_of_freedom`. **Schema**: `{"f_statistic": float, `p_value`: float, `effect_size`: float, `degrees_of_freedom`: {"num": int, `den": int}}`. **Constraint**: Use `statsmodels` for ANOVA. **Verification**: Assert `data/analysis/anova_results.json` exists and matches the schema. **Dependency**: T038, T012-Runtime, T017, T027.3, T035.1.
- [X] T036 [US3] Implement multiple‑comparison correction (Bonferroni) in `code/analysis/stats.py`. **Dependency**: T035.
- [X] T037 [US3] Implement visualization generation (mean false memory rates with confidence intervals) in `code/analysis/viz.py`. **Dependency**: T035.
- [X] T072.1 [US3] **Analysis Output: Limitations JSON Update**: Update `code/analysis/anova.py` (T035) to automatically append a `limitations` key to the `anova_results.json` object. **Content**: This key must contain a string stating that the findings are "associational" and "do not establish a molecular or cellular mechanism," citing the scope boundary document (T060). **Dependency**: T035, T060.
- [X] T072.2 [US3] **Analysis Output: Limitations Documentation**: Update `research.md` to include a section "Limitations: Associational Nature" that cites T060 and explains the scope boundary. **Dependency**: T072.1, T060.
- [X] T039 [US3] Add CLI entry point for running analysis in `code/cli.py`. **Dependency**: T035, T036, T037.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review Response - Mechanism Clarification (Priority: P3)

**Goal**: Address Eric Kandel's review regarding the lack of a molecular/cellular mechanism hypothesis. This phase ensures the project explicitly frames its behavioral findings as "associational" and documents the *absence* of mechanistic claims, satisfying the "Walk down the ladder of explanation" critique without overstepping the behavioral scope.

### Implementation for Mechanism Clarification

- [X] T080 [Shared-Infra] [Review-Kandel] **Update Scope Boundary with "Ladder of Explanation"**: Update `docs/ethics/scope_boundary.md` to include a new section "Response to Mechanistic Critique". **Content**: Explicitly state: "While the 'ladder of explanation' (behavior → cells → synapses → molecules) is a valid framework for mechanistic discovery, this study is strictly confined to the behavioral rung. We do not measure, infer, or hypothesize about specific synaptic changes (e.g., CREB activation, PKA pathways) in the visual cortex or hippocampus. The 'visual detail' variable is a psychophysical stimulus parameter, not a proxy for synaptic weight. Any correlation between detail and false memory is an associational finding, not evidence of a molecular mechanism." **Dependency**: T060.
- [X] T081 [Shared-Infra] [Review-Kandel] **Update Research Plan with "Mechanism Gap" Analysis**: Update `research.md` to append a section "Theoretical Gap: Behavioral vs. Mechanistic". **Content**: "Current behavioral models (Loftus, Schacter) describe the *phenomenon* of false memory but do not map it to specific synaptic events in humans. This project accepts this gap. We propose that visual detail modulates susceptibility, but we explicitly *do not* claim this modulation is mediated by specific molecular pathways (e.g., serotonin/CREB) as observed in Aplysia. Future work would be required to bridge this gap using neuroimaging or invasive methods." **Dependency**: T080.
- [X] T082 [US3] **Add Mechanism Disclaimer to ANOVA Output**: Modify `code/analysis/anova.py` (T035) to ensure the `limitations` field in `anova_results.json` explicitly cites T080/T081. **Content**: "Results are associational. No claim is made regarding synaptic or molecular mechanisms (e.g., CREB, PKA). See docs/ethics/scope_boundary.md." **Dependency**: T080, T081, T035.

**Checkpoint**: Review concerns regarding mechanistic claims are explicitly addressed and documented.

---

## Phase 7: Review Response - Ladder of Explanation Gap (Priority: P3)

**Goal**: Address the specific critique that the project must "walk down the ladder of explanation" from behavior to molecules. Since this project is strictly behavioral, the response is to explicitly document the *gap* between the behavioral observation and the hypothesized (but unmeasured) biological substrate, citing the specific molecular pathways (CREB, PKA, Serotonin) mentioned in the review to show awareness of the missing link.

### Implementation for Ladder of Explanation Response

- [ ] T093 [Shared-Infra] [Review-Kandel] **Document "Ladder of Explanation" Gap in Research Plan**: Update `research.md` to append a new section "The Ladder of Explanation: A Behavioral Gap". **Content**: Explicitly map the review's critique: "The reviewer (Kandel) correctly identifies that our behavioral finding (visual detail modulates false memory) lacks a mapped biological correlate. In Aplysia, this would correspond to presynaptic facilitation via serotonin → cAMP → PKA → CREB. In humans, the specific synaptic changes in the visual cortex or hippocampus mediating this effect remain unmeasured. This study stops at the behavioral rung. We do not claim to have identified the 'molecular map' of visual detail, only its behavioral effect." **Dependency**: T080, T081.
- [ ] T094 [Shared-Infra] [Review-Kandel] **Add Biological Context to Ethics Scope Boundary**: Update `docs/ethics/scope_boundary.md` to include a section "Biological Context and Limitations". **Content**: "While the project is strictly behavioral, it acknowledges the biological hypothesis: that increased visual detail may enhance synaptic encoding strength (potentially via CREB-dependent protein synthesis) or alter reconsolidation dynamics. However, this project does not measure these variables. The 'visual detail' parameter is a psychophysical proxy, not a direct measure of synaptic weight." **Dependency**: T093, T060.
- [ ] T095 [US3] **Update Analysis Output with Biological Context Disclaimer**: Modify `code/analysis/anova.py` (T035) to append a `biological_context` field to `anova_results.json`. **Content**: "This result is a behavioral association. It does not confirm or deny the involvement of specific molecular pathways (e.g., CREB, PKA) or synaptic mechanisms in the visual cortex/hippocampus. Future neuroimaging or invasive studies are required to map this behavioral effect to the 'ladder of explanation'." **Dependency**: T093, T094, T035.

**Checkpoint**: The "Ladder of Explanation" gap is explicitly documented, showing awareness of the biological critique while maintaining the behavioral scope.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T045.1 [P] Refactor error handling logic into a utility module in `code/utils/error_handling.py`. **Dependency**: T019.
- [X] T045.2 [P] Extract magic numbers and constants to `code/config.py`. **Dependency**: T009.
- [X] T046-A [P] **Performance Profiling**: Implement `code/utils/profiler.py` to run `cProfile` on the image manipulation pipeline. **Output**: Generate `data/logs/profile_report.txt` identifying the top bottlenecks. **Dependency**: T015, T016.
- [X] T046-B [P] **Performance Optimization**: Optimize the top bottleneck identified in T046-A to ensure <30s/image. **Dependency**: T046-A.
- [X] T047 [P] Additional unit tests for edge cases (dropout, network timeout) in `tests/unit/`. **Dependency**: T027.3, T035.
- [X] T048 Security hardening (ensure no PII leakage in logs). **Dependency**: T010, T027.3.
- [X] T049 [P] Run quickstart validation: **Action**: Execute the `code/cli.py --validate-quickstart` command to verify the project structure and basic functionality. **Dependency**: T060, T046-B.

---

## Phase Dependencies

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Response (Phase 6)**: Depends on Foundational and US3 completion (to ensure analysis results are available for the disclaimer)
- **Review Response (Phase 7)**: Depends on Phase 6 and US3 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 (uses manipulated images) but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data generation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Critical Task Dependencies

- **T012-Calc/T012-Runtime (Power Analysis)**: T012-Calc calculates and writes the report (setting `power_insufficient` flag if needed). T012-Runtime is the sole authority for halting the pipeline if N < 50.
- **T027.2 (Recognition Question Generator)**: Blocked by **T017** (Stimulus Metadata Generation), **T027.1** (Mock Object Pool), and **T006.3-Filter** (Baseline Image Selection).
- **T015/T016 (Manipulation)**: Blocked by **T006.3-Filter** (Data Fetch). **T015** depends on **T015.1-Run** (assets exist). **T016** depends on **T015.1-Run** (to ensure pipeline context is valid).
- **T038 (Dataset-variable fit check)**: Must run before **T035** (ANOVA).
- **T035.1 (Baseline Rate)**: Must run before **T035** (ANOVA) to ensure baseline data is available.
- **T072.1/T072.2 (Limitations)**: Blocked by T035 and T060.
- **T080, T081, T082**: Blocked by T060 and T035 (to ensure analysis context exists).
- **T093, T094, T095**: Blocked by T060, T080, T081, and T035 (to ensure analysis context exists).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational together
2. Add User Story 1 (Stimuli) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Session) → Test independently → Deploy/Demo
4. Add User Story 3 (Analysis) → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Stimuli)
 - Developer B: User Story 2 (Session)
 - Developer C: User Story 3 (Analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **Critical Revision Note**: Task T006.0 removed. It violated the 'Single Source of Truth' principle by attempting to edit spec.md. The dataset deviation (COCO 2017) is correctly documented in plan.md and should not be altered in spec.md by implementation tasks.
- **Critical Revision Note**: T010 updated to include detailed GDPR Anonymization Workflow and generate both consent and IRB placeholders. T010.1 added for runtime IRB verification.
- **Critical Revision Note**: T012 refactored to only calculate and write report; T012-Runtime is now the sole gate for halting the pipeline. T012-Calc sets `power_insufficient` flag; T012-Runtime raises `SystemExit` if flag is true.
- **Critical Revision Note**: T027.2 updated to enforce a minimum threshold (8 items) instead of a rigid 10/10 split and to flag sessions instead of raising hard errors. **REVISION**: T027.2 now ENFORCES strict 10/10 split and raises `SystemExit` on failure. Partial sets removed.
- **Critical Revision Note**: T015.1 split into T015.1‑Script and T015.1‑Run to clarify asset generation dependency; T015 tag updated to [Shared‑Infra] for T015.1‑Script.
- **Critical Revision Note**: T060 moved to Phase 2 and added as dependency for T012.0.
- **Critical Revision Note**: T061.1 removed; citation validation handled by CI/CD.
- **Critical Revision Note**: T061.2 added to address Eric Kandel's review by explicitly contrasting psychological and biological mechanisms in documentation only.
- **Critical Revision Note**: T062 added to formally document the project's response to the biological mechanism critique, acknowledging the reviewer's point while defending the behavioral scope. T062 now explicitly depends on T012-Runtime.
- **Critical Revision Note**: T006.1‑VG‑Stream, T006.2‑Calc, T006.3‑Filter atomized from original T006.1.
- **Critical Revision Note**: T015‑Script, T015‑Run atomized into T015.1‑Script and T015.1‑Run.
- **Critical Revision Note**: T025, T026, T027.2, T027.3 atomized into Model/View components.
- **Critical Revision Note**: Explicit dependencies added for T038, T039, T045.1, T045.2, T046, T047, T048, T063.
- **Critical Revision Note**: Phase 7 (T070‑T073) removed. These tasks were identified as scope creep and out of scope for the current behavioral‑only research phase.
- **Critical Revision Note**: T006.1‑VG‑Stream replaced with T006.1‑LoadSubset to load pre‑bundled data.
- **Critical Revision Note**: T012 split into T012‑Calc and T012‑Runtime to separate design‑phase calculation from runtime gate.
- **Critical Revision Note**: T035 updated to use `code/analysis/anova.py` as per plan.md structure.
- **Critical Revision Note**: T080, T081, T082 [X] (completed) – no further action required.
- **Critical Revision Note**: T073, T074, T075 updated with concrete deliverables (create files).
- **Critical Revision Note**: T017 added to Phase 2 to resolve missing dependency for T027.2 and T035.
- **Critical Revision Note**: T015.1‑Script updated to ensure exactly 20 PNGs are generated.
- **Critical Revision Note**: T027.1 updated to ensure >= 50 distinct objects.
- **Critical Revision Note**: T016 dependency updated to include T015.1‑Run.
- **Critical Revision Note**: T012 and T012-Runtime [P] tag removed to reflect sequential dependency.
- **Critical Revision Note**: T080, T081, T082 [P] tag removed to reflect sequential dependency.
- **Critical Revision Note**: T093, T094, T095 added to address Eric Kandel's review regarding the "Ladder of Explanation" gap, explicitly documenting the behavioral scope and the absence of mechanistic claims.
- **Critical Revision Note**: T090, T091, T092 removed as superseded duplicates.
- **Critical Revision Note**: T027.2 updated to handle partial data gracefully (flag instead of exit) and defined output schema.
- **Critical Revision Note**: T017 updated to explicitly mandate `manipulation_timestamp`.
- **Critical Revision Note**: T035 updated to implement Repeated-Measures ANOVA.
- **Critical Revision Note**: T012-Calc updated to calculate power for Repeated-Measures design.
- **Critical Revision Note**: All [P] tags on sequential tasks removed.
- **Critical Revision Note**: T006.1-LoadSubset updated to specify `manifest.sha256` and SHA-256.
- **Critical Revision Note**: T012-Calc and T012-Runtime updated with explicit verification and success artifacts.
- **Critical Revision Note**: T035 updated with explicit JSON schema and verification.

<!-- auto-added by the execution fix loop: run‑book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T073 Reconcile run‑book vs implementation for `code/analysis/power.py`: the quickstart run‑book invokes this script but it does not exist. **Action**: Create `code/analysis/power.py` and move the power analysis logic from T012‑Calc to this file. **Dependency**: T012‑Calc.
- [X] T074 Reconcile run‑book vs implementation for `code/analysis/anova.py`: the quickstart run‑book invokes this script but it does not exist. **Action**: Create `code/analysis/anova.py` and move the ANOVA logic from T035 to this file. **Dependency**: T035.
- [X] T075 Reconcile run‑book vs implementation for `code/utils/data_loader.py`: the quickstart run‑book invokes this script but it does not exist. **Action**: Create `code/utils/data_loader.py` and implement the data loading logic from T006.1‑LoadSubset to this file. **Dependency**: T006.1‑LoadSubset.
- [X] T080 [Shared‑Infra] [Review‑Kandel] **Update Scope Boundary with "Ladder of Explanation"**: Update `docs/ethics/scope_boundary.md` to include a new section "Response to Mechanistic Critique". **Content**: Explicitly state: "While the 'ladder of explanation' (behavior → cells → synapses → molecules) is a valid framework for mechanistic discovery, this study is strictly confined to the behavioral rung. We do not measure, infer, or hypothesize about specific synaptic changes (e.g., CREB activation, PKA pathways) in the visual cortex or hippocampus. The 'visual detail' variable is a psychophysical stimulus parameter, not a proxy for synaptic weight. Any correlation between detail and false memory is an associational finding, not evidence of a molecular mechanism." **Dependency**: T060.
- [X] T081 [Shared‑Infra] [Review‑Kandel] **Update Research Plan with "Mechanism Gap" Analysis**: Update `research.md` to append a section "The Theoretical Gap: Behavioral vs. Mechanistic". **Content**: "Current behavioral models (Loftus, Schacter) describe the *phenomenon* of false memory but do not map it to specific synaptic events in humans. This project accepts this gap. We propose that visual detail modulates susceptibility, but we explicitly *do not* claim this modulation is mediated by specific molecular pathways (e.g., serotonin/CREB) as observed in Aplysia. Future work would be required to bridge this gap using neuroimaging or invasive methods." **Dependency**: T080.
- [X] T082 [US3] **Add Mechanism Disclaimer to ANOVA Output**: Modify `code/analysis/anova.py` (T035) to ensure the `limitations` field in `anova_results.json` explicitly cites T080/T081. **Content**: "Results are associational. No claim is made regarding synaptic or molecular mechanisms (e.g., CREB, PKA). See docs/ethics/scope_boundary.md." **Dependency**: T080, T081, T035.

**Checkpoint**: Review concerns regarding the "Ladder of Explanation" gap are explicitly addressed and documented.

---

## Phase N: Polish & Cross‑Cutting Concerns (continued)

- [X] T045.1 [P] Refactor error handling logic into a utility module in `code/utils/error_handling.py`. **Dependency**: T019.
- [X] T045.2 [P] Extract magic numbers and constants to `code/config.py`. **Dependency**: T009.
- [X] T046-A [P] **Performance Profiling**: Implement `code/utils/profiler.py` to run `cProfile` on the image manipulation pipeline. **Output**: Generate `data/logs/profile_report.txt` identifying the top bottlenecks. **Dependency**: T015, T016.
- [X] T046-B [P] **Performance Optimization**: Optimize the top bottleneck identified in T046-A to ensure <30s/image. **Dependency**: T046-A.
- [X] T047 [P] Additional unit tests for edge cases (dropout, network timeout) in `tests/unit/`. **Dependency**: T027.3, T035.
- [X] T048 Security hardening (ensure no PII leakage in logs). **Dependency**: T010, T027.3.
- [X] T049 [P] Run quickstart validation: **Action**: Execute the `code/cli.py --validate-quickstart` command to verify the project structure and basic functionality. **Dependency**: T060, T046-B.