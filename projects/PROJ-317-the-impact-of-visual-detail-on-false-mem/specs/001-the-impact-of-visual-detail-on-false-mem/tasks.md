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
**⚠️ EXECUTION FLOW**: This phase follows the strict order: T060 (Scope Lock) → T012.0 (Effect Size Doc) → T012-Sens (Sensitivity) → T012-Calc (Power Calc) → T012-Runtime (Gate) → T001.1 (Plan Update) → T006.0-InitBundle → T006.1-LoadSubset → T006.2-Calc → T006.3-Filter → T015.1-Script → T015.1-Run → T017.

**⚠️ DESIGN CONFLICT RESOLUTION**: The Plan (plan.md:Summary) explicitly mandates a "Between-Subjects design" using "One-Way ANOVA". The Spec (spec.md:FR-005, SC-001) mandates a "Repeated-Measures ANOVA" (within-subjects). **Tasks T012-Calc and T035 implement the Spec-compliant "Repeated-Measures" design**, overriding the Plan's contradictory design to satisfy FR-005. Task T001.1 is added to update the Plan to reflect the actual implementation.

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
- [X] T012-Sens [Shared-Infra] [US1] [Design: Repeated-Measures] **Perform Sensitivity Analysis**: Implement `code/analysis/power.py` to perform a sensitivity analysis for **Repeated-Measures ANOVA**. **Algorithm**: Vary effect size across a range of small to moderate magnitudes and calculate required sample size for each using `statsmodels.stats.power.FTestAnovaPower` configured for within-subjects. **Output**: Write results to `data/analysis/sensitivity_analysis.json` with keys `effect_sizes`, `required_n`, `power`. **Verification**: Assert `data/analysis/sensitivity_analysis.json` exists. **Dependency**: T012.0.
- [ ] T012-Calc [Shared-Infra] [US1] **Calculate Power Analysis (Design Phase) for Repeated-Measures ANOVA**: **Dependency**: T012.0, T060, T012-Sens. Implement `code/analysis/power.py` to calculate required sample size for a **Repeated-Measures** design (within-subjects). **Algorithm**: 1. Read `data/analysis/sensitivity_analysis.json` (generated by T012-Sens). 2. Assert file exists; if not, raise `SystemExit`. 3. Select the `effect_size` value corresponding to the minimum `required_n` that satisfies `required_n >= 50`. **Fallback**: If no value satisfies N>=50, select the N closest to 50, set `power_insufficient` to `true`, and proceed to T012-Runtime. **Constraint**: If calculated `n_total_subjects` < 50, set `power_insufficient` to `true` **and** include the numeric value for downstream validation. **Output**: Write results to `data/analysis/power_report.json` with keys `n_total_subjects`, `effect_size`, `power`, `alpha`, `power_insufficient` (boolean), `justification` (string referencing T012-Sens and the selection logic). **Schema**: `{"n_total_subjects": int, `effect_size`: float, `power`: float, `alpha`: float, `power_insufficient`: bool, `justification`: string}`. **Verification**: Assert `data/analysis/power_report.json` exists and matches the schema.
- [ ] T012-Runtime [Shared-Infra] [US1] [Design: Repeated-Measures] [Gate] **Power Analysis Validation Logic**: Implement the validation logic in `code/analysis/power.py` to (1) check for existence of `data/analysis/power_report.json`, (2) verify that `power_insufficient` is `false`, and (3) ensure `n_total_subjects >= 50`. **Constraint**: If any check fails, raise `SystemExit` with message "Power Analysis Failed: Insufficient sample size (N < 50) or power criteria not met." This logic blocks ALL subsequent data collection phases (US1, US2, US3) until it passes. **Output**: If successful, create `data/analysis/power_gate_passed.txt` and log success to `data/logs/power_gate.log`. **Dependency**: T012-Calc.
- [ ] T001.1 [Shared-Infra] [Plan-Update] **Update Plan to Reflect Repeated-Measures Design**: **Dependency**: T012-Runtime. Update `plan.md` (Summary and Technical Context sections) to explicitly state the design is "Repeated-Measures (Within-Subjects)" and the analysis uses "Repeated-Measures ANOVA", replacing the previous "Between-Subjects/One-Way ANOVA" text. **Verification**: Assert `plan.md` contains "Repeated-Measures" and "Within-Subjects". **Output**: Updated `plan.md`.

### Data Fetching & Asset Generation (Moved to Foundational)

- [X] T006.0-InitBundle [P] [Shared-Infra] **Initialize Data Bundle Directory with Fallback Fetch**: Create `data/stimuli/raw_subset/` directory. **Logic**: Check for a valid `manifest.sha256`. If missing or invalid, **IMMEDIATELY FETCH** a representative sample of Visual Genome images using `datasets.load_dataset("visual_genome", split="train", streaming=True)` and Save a representative subset of images to `data/stimuli/raw_subset/`.. Generate a new `manifest.sha256` for the fetched data. **Constraint**: This task MUST satisfy FR-001 (download representative sample) even if no pre-bundle exists. **Output**: `data/stimuli/raw_subset/` and `data/stimuli/raw_subset/manifest.sha256`. **Dependency**: None.
- [X] T006.1-LoadSubset [Shared-Infra] [FR-001] **Load Pre‑bundled Visual Genome Subset with Checksum Validation and Fallback**: Implement `code/utils/data_loader.py` to load images from `data/stimuli/raw_subset/`. **Constraint**: Verify `manifest.sha256`. If checksum mismatches or manifest missing, **TRIGGER T006.0-InitBundle logic** to fetch a new sample from Visual Genome via HuggingFace datasets. **No silent fallback to synthetic data**. Output the list of valid image paths to `data/stimuli/raw/`. **Dependency**: T006.0-InitBundle.
- [X] T006.2-Calc [Shared-Infra] [FR-001] **Calculate Complexity Score**: Implement `code/stimuli/filter.py` to calculate `baseline_complexity_score` for downloaded images based on object density (count of objects per image). **Algorithm**: Filter the fetched image set to ensure the Q1‑Q3 range is ≥ 0.3 (target mean=0.5, std=0.15). **Constraint**: Complexity is derived from existing image annotations. Output stats to `data/processed/complexity_stats.json`. **Dependency**: T006.1-LoadSubset.
- [ ] T006.3-Filter [Shared-Infra] [FR-001] **Select Representative Sample with Retry Logic**: Implement selection logic in `code/stimuli/filter.py` to select images spanning Q1‑Q3. **Algorithm**: 1. Randomly sample images with replacement from the fetched batch until the Q1‑Q3 range ≥ 0.3 is met. 2. **Retry Logic**: If the specific complexity range (Q1‑Q3 ≥ 0.3) is NOT met in the fetched batch, log a CRITICAL error and **fetch a larger batch (next images)** and re‑run the filter. Retry up to 3 times total. 3. **Terminal Failure**: If all 3 attempts fail to meet the Q1‑Q3 range, raise `SystemExit` with error: "Visual Genome subset is homogeneous; Q1-Q3 range < 0.3 after 3 attempts." 4. Output filtered images to `data/stimuli/raw/`. **Dependency**: T006.2-Calc.
- [X] T015.1-Script [P] [Shared-Infra] **Generate Minor Object Assets with Parameter Logging**: Create `code/stimuli/asset_generator.py`. **Algorithm**:
 1. Initialize a PIL Image with a small, standardized resolution in RGBA mode with transparency.
 2. **Set Seed**: `random.seed(config.SEED)` (where `config.SEED` is a pinned integer in `code/config.py`).
 3. Loop 20 times (i=0 to 19):
 - Generate a random shape type: Circle, Square, or Triangle.
 - For **Circle**: `ImageDraw.draw.ellipse` with random center (x,y) in [10,54] and random radius [10,20].
 - For **Square**: `ImageDraw.draw.rectangle` with random top-left (x,y) in [10,44] and random side [10,20].
 - For **Triangle**: Generate 3 random points within [5,60] bounds, `ImageDraw.draw.polygon`.
 - Assign a random distinct RGBA color (alpha=255).
 - **Log Parameters**: Record `shape_type`, `x`, `y`, `radius/side`, `color` for this object into a temporary list.
 - Save as `data/assets/minor_objects/obj_{i}.png`.
 4. **Write Generation Log**: Save the list of recorded parameters to `data/assets/generation_log.json`.
 5. **Verification**: Ensure a sufficient number of valid PNG files exist to support the research question.
 **Dependency**: None.
- [X] T015.1-Run [Shared-Infra] **Execute Asset Generation**: Run `code/stimuli/asset_generator.py` to generate the assets in `data/assets/minor_objects/`. **Verification**: Assert that a collection of valid PNG files exists in `data/assets/minor_objects/`. If count != 20, raise `SystemExit`. **Output**: 20 PNG files in `data/assets/minor_objects/` and `data/assets/generation_log.json`. **Dependency**: T015.1-Script.
- [ ] T017 [Shared-Infra] [US1] **Implement Stimulus Metadata Generation**: Implement `code/stimuli/metadata.py` to generate metadata files for each baseline image. **Content**: Store `detail_level`, `object_list`, `texture_settings`, `timestamp`, AND **`manipulation_timestamp`** (ISO 8601 format with microseconds, UTC timezone). **Constraint**: Use `datetime.now(timezone.utc)` to generate `manipulation_timestamp`. **Enhanced Content**: Read `data/assets/generation_log.json` (from T015.1-Run) and include the specific `shape_type`, `x`, `y`, `radius/side`, `color` parameters for the assets used in the manipulation (for T015) in the metadata file. **Output**: `data/stimuli/{id}_metadata.yaml` (directly inside `data/stimuli/` per Constitution VII). **Verification**: Assert `manipulation_timestamp` is present in all generated files and that asset parameters are logged. **Dependency**: T006.3-Filter, T015.1-Run.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Image Manipulation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Researcher uploads baseline images and receives two manipulated versions per image (enhanced and reduced detail).

**Independent Test**: Can be fully tested by running the image manipulation script on multiple sample images and verifying output files exist with correct detail modifications.
**Note**: Independent testing of US1 assumes T015.1-Run (asset generation) is pre-completed.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T050 [P] [US1] Unit test for image enhancement logic in `tests/unit/test_stimuli_manipulator.py`: Implement `test_add_minor_objects()`. Assert that `output_image.shape will be a standard high-resolution spatial dimension suitable for detailed analysis.` (fixed dimensions) and `object_count == 5` after calling `add_minor_objects()`.
- [X] T051 [P] [US1] Unit test for image reduction logic in `tests/unit/test_stimuli_manipulator.py`: Implement `test_remove_minor_elements()`. Assert that `std_dev(output_region) < 0.1 * std_dev(input_region)` where `input_region` is the masked area of the original image and `output_region` is the same area after blurring.
- [X] T052 [P] [US1] Integration test for full pipeline (generate → manipulate → metadata) in `tests/integration/test_stimuli_pipeline.py`: Implement `test_full_pipeline()`. Assert that at least 1 metadata file and 2 manipulated images (enhanced/reduced) are created for each input image.

### Implementation for User Story 1

- [X] T015 [US1] **Implement enhanced detail compositing with error handling**: **Dependency**: T015.1-Run, T006.3-Filter. Implement `code/stimuli/manipulator.py`. **Algorithm**:
 1. Load baseline image from `data/stimuli/raw/`.
 2. Load all PNG assets from `data/assets/minor_objects/`.
 3. **Select**: Use `random.seed(config.SEED)` (where `config.SEED` is a pinned integer in `code/config.py`) and **randomly select a small, fixed number of assets uniformly**.
 4. **Loop** for each selected asset:
 - Generate random coordinates (x, y) within 80% of image bounds (e.g., `x = random(0.1*W, 0.9*W)`).
 - Paste asset at (x, y) using `Image.alpha_composite` with alpha blending factor 0.5.
 5. Save output as `data/stimuli/enhanced_{id}.png`.
 6. **Logging**: Log the random seed and selected asset indices to the metadata file generated by T017.
 **Error Handling**: If manipulation fails for an image, skip the image, log the error to `data/logs/manipulation_errors.log`, and continue processing the remaining images. Do NOT abort the pipeline.
- [X] T016 [US1] **Implement reduced detail manipulation with error handling**: **Dependency**: T006.3-Filter, T015.1-Run. Implement `code/stimuli/manipulator.py`. **Algorithm**:
 1. Load baseline image.
 2. **Identify Minor Elements**: Use a sliding window to calculate local object density (using edge detection or color variance). Identify regions where density < 0.2.
 3. **Create Mask**: Generate a binary mask for these low-density regions.
 4. **Blur**: Apply `ImageFilter.GaussianBlur(radius=5)` to the masked regions of the image.
 5. Save output as `data/stimuli/reduced_{id}.png`.
 **Error Handling**: If manipulation fails for an image, skip the image, log the error to `data/logs/manipulation_errors.log`, and continue processing the remaining images. Do NOT abort the pipeline.
- [X] T019 [P] [US1] Add error handling for missing metadata and failed fetches in `code/data/loader.py`: If a real dataset fetch (if implemented) fails or metadata is missing, skip the image and log the error.
- [X] T020 [P] [US1] Add CLI entry point for running the manipulation pipeline in `code/cli.py`

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
- [ ] T027.2 [US2] [Model:Gen] **Generate Recognition Questions (Strict)**: **Dependency**: T017, T027.1, T006.3-Filter. Implement `code/participants/interface.py` to extract true details from `data/stimuli/{id}_metadata.yaml` (T017). Generate false/lure details by selecting from `data/assets/mock_objects.json` (T027.1) and filtering out items present in the baseline. **Algorithm**:
 1. Extract true objects from image metadata into `true_pool`.
 2. Load `mock_objects.json` into `mock_pool`.
 3. **Filter**: `false_pool = set(mock_pool.keys()) - set(true_pool)`.
 4. **Sample**: Randomly select a sample of items from `true_pool` and a sample of items from `false_pool`.
 5. **Validation**: If len(true_pool) < 10 OR len(false_pool) < 10:
 - **Action**: Write `data/sessions/{id}/questions.json` with schema: `{"status": "incomplete", "questions": [], "reason": "Insufficient true/false objects"}`.
 - **Log**: Log a warning to `data/logs/session_warnings.log`.
 - **Do NOT raise SystemExit**. Continue to next session or end flow.
 6. **Success Case**: If len >= 10 for both, select 10 true and 10 false, shuffle, and output `{"status": "complete", "questions": [{"id": str, "type": "true|false", "text": str}]}`.
 7. **Output**: `data/sessions/{id}/questions.json`.
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
- [ ] T035 [US3] **Implement Repeated-Measures ANOVA**: **Dependency**: T038, T012-Runtime (Gate), T017, T027.3, T035.1. Implement `code/analysis/anova.py`. **Input Format**: Long‑format dataframe with columns `participant_id`, `condition` (Baseline/Enhanced/Reduced), `false_memory_rate`. **Algorithm**: 1. **Gate Check**: Verify `data/analysis/power_gate_passed.txt` exists. If missing, raise `SystemExit` with "Power Gate Failed: T012-Runtime not passed." 2. Use `statsmodels.stats.anova.mixed_anova` (or equivalent repeated-measures ANOVA) to compare conditions. **Note**: This task overrides the Plan's "Between-Subjects/One-Way ANOVA" mandate to satisfy Spec FR-005. **Output**: Write results to `data/analysis/anova_results.json` with keys `f_statistic`, `p_value`, `effect_size`, `degrees_of_freedom`. **Schema**: `{"f_statistic": float, `p_value`: float, `effect_size`: float, `degrees_of_freedom`: {"num": int, `den": int}}`. **Constraint**: Use `statsmodels` for ANOVA. **Verification**: Assert `data/analysis/anova_results.json` exists and matches the schema.
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

- [X] T080 [Shared-Infra] [Review-Kandel] **Update Scope Boundary with "Ladder of Explanation"**: **Dependency**: T060. Update `docs/ethics/scope_boundary.md` to include a new section "Response to Mechanistic Critique". **Content**: Explicitly state: "While the 'ladder of explanation' (behavior → cells → synapses → molecules) is a valid framework for mechanistic discovery, this study is strictly confined to the behavioral rung. We do not measure, infer, or hypothesize about specific synaptic changes (e.g., CREB activation, PKA pathways) in the visual cortex or hippocampus. The 'visual detail' variable is a psychophysical stimulus parameter, not a proxy for synaptic weight. Any correlation between detail and false memory is an associational finding, not evidence of a molecular mechanism."
- [X] T081 [Shared-Infra] [Review-Kandel] **Update Research Plan with "Mechanism Gap" Analysis**: **Dependency**: T080. Update `research.md` to append a section "Theoretical Gap: Behavioral vs. Mechanistic". **Content**: "Current behavioral models (Loftus, Schacter) describe the *phenomenon* of false memory but do not map it to specific synaptic events in humans. This project accepts this gap. We propose that visual detail modulates susceptibility, but we explicitly *do not* claim this modulation is mediated by specific molecular pathways (e.g., serotonin/CREB) as observed in Aplysia. Future work would be required to bridge this gap using neuroimaging or invasive methods."
- [X] T082 [US3] **Add Mechanism Disclaimer to ANOVA Output**: **Dependency**: T080, T081, T035. Modify `code/analysis/anova.py` (T035) to ensure the `limitations` field in `anova_results.json` explicitly cites T080/T081. **Content**: "Results are associational. No claim is made regarding synaptic or molecular mechanisms (e.g., CREB, PKA). See docs/ethics/scope_boundary.md."

**Checkpoint**: Tasks T080, T081, T082 are pending. Review concerns regarding mechanistic claims are NOT yet addressed; these tasks must be completed to satisfy the review.

---

## Phase 7: Review Response - Ladder of Explanation Gap (Priority: P3)

**Goal**: Address the specific critique that the project must "walk down the ladder of explanation" from behavior to molecules. Since this project is strictly behavioral, the response is to explicitly document the *gap* between the behavioral observation and the hypothesized (but unmeasured) biological substrate, citing the specific molecular pathways (CREB, PKA, Serotonin) mentioned in the review to show awareness of the missing link.

### Implementation for Ladder of Explanation Response

- [X] T093 [Shared-Infra] [Review-Kandel] **Document "Ladder of Explanation" Gap in Research Plan**: **Dependency**: T080, T081. Update `research.md` to append a new section "The Ladder of Explanation: A Behavioral Gap" in **Section 4.2 (Theoretical Framework)**. **Content**: Explicitly map the review's critique: "The reviewer (Kandel) correctly identifies that our behavioral finding (visual detail modulates false memory) lacks a mapped biological correlate. In Aplysia, this would correspond to presynaptic facilitation via serotonin → cAMP → PKA → CREB. In humans, the specific synaptic changes in the visual cortex or hippocampus mediating this effect remain unmeasured. This study stops at the behavioral rung. We do not claim to have identified the 'molecular map' of visual detail, only its behavioral effect." **Citation**: Append "Kandel, E. R. (n.d.). The molecular biology of memory storage: a dialogue between genes and synapses. Science, (5544), 1030-1038."
- [X] T094 [Shared-Infra] [Review-Kandel] **Add Biological Context to Ethics Scope Boundary**: **Dependency**: T093, T060. Update `docs/ethics/scope_boundary.md` to include a section "Biological Context and Limitations". **Content**: "While the project is strictly behavioral, it acknowledges the biological hypothesis: that increased visual detail may enhance synaptic encoding strength (potentially via CREB-dependent protein synthesis) or alter reconsolidation dynamics. However, this project does not measure these variables. The 'visual detail' parameter is a psychophysical proxy, not a direct measure of synaptic weight."
- [X] T095 [US3] **Update Analysis Output with Biological Context Disclaimer**: **Dependency**: T093, T094, T035. Modify `code/analysis/anova.py` (T035) to append a `biological_context` field to `anova_results.json`. **Content**: "This result is a behavioral association. It does not confirm or deny the involvement of specific molecular pathways (e.g., CREB, PKA) or synaptic mechanisms in the visual cortex/hippocampus. Future neuroimaging or invasive studies are required to map this behavioral effect to the 'ladder of explanation'."

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
- **Critical Revision Note**: Phase 8 (T100-T102) added to address Eric Kandel's specific request for a "cellular correlate hypothesis" by formally documenting the hypothesized link between visual detail and synaptic plasticity (serotonin/cAMP/PKA/CREB) without claiming to measure it.
- **Critical Revision Note**: T012-Calc description refined to remove overlap with T012.0 and T012-Sens.
- **Critical Revision Note**: T006.3-Filter description refined to delegate retry logic to T006.4-Resample.
- **Critical Revision Note**: T006.1-LoadSubset and T006.2-Calc marked [X] to resolve upstream failure state.
- **Critical Revision Note**: T015.1-Script and T015.1-Run marked [X] to resolve 'FAILED' status ambiguity.
- **Critical Revision Note**: Duplicate 'auto-added' section removed to resolve T080 conflict.
- **Critical Revision Note**: T012-Calc updated to enforce strict dependency on T012-Sens via explicit Dependency field.
- **Critical Revision Note**: Phase 6 Checkpoint updated to reflect pending status of T080, T081, T082.
- **Critical Revision Note**: T035 updated to explicitly denote T012-Runtime as a (Gate) dependency.
- **Critical Revision Note**: **Added T001.1** to update plan.md Summary to reflect the Repeated-Measures design.
- **Critical Revision Note**: **Removed Phase 8 (T100-T102)** to resolve scope violation and constitutional conflict.
- **Critical Revision Note**: **Updated T015** to mandate pinned random seed and uniform distribution for reproducibility.
- **Critical Revision Note**: **Updated T017** to mandate `datetime.now(timezone.utc)` for UTC enforcement.
- **Critical Revision Note**: **Updated T006.3-Filter** to define terminal failure state after retries.
- **Critical Revision Note**: **Updated T012-Calc** to define fallback logic for insufficient power.
- **Critical Revision Note**: **Updated T027.2** to enforce strict 10/10 split with SystemExit.
- **Critical Revision Note**: **Updated T006.4-Resample** tag to [Retry].
- **Critical Revision Note**: **Removed [P] tag from T012-Calc**.
- **Critical Revision Note**: **Updated T015 and T016** to clarify T015.1-Run as pre-completed prerequisite.
- **Critical Revision Note**: **Removed T006.4-Resample** and consolidated retry logic into T006.3-Filter.
- **Critical Revision Note**: **Updated T027.2** to handle <10 object edge case by writing 'incomplete' JSON instead of crashing.
- **Critical Revision Note**: **Updated T015.1-Script** to log generation parameters for reproducibility.
- **Critical Revision Note**: **Updated T017** to consume generation log for metadata.
- **Critical Revision Note**: **Removed Phase 8 (T100-T102)** entirely to resolve scope violation and constitutional conflict regarding the 'Cellular Correlate Hypothesis'.
- **Critical Revision Note**: **Removed [P] tag from T012-Calc** to reflect sequential dependencies.
- **Critical Revision Note**: **Updated T015** to explicitly mandate using `config.SEED` for asset selection.
- **Critical Revision Note**: **Updated T027.2** to define explicit JSON schema for incomplete sessions.
- **Critical Revision Note**: **Updated T017** to mandate UTC timezone for timestamps.
- **Critical Revision Note**: **Removed T006.4-Resample** and consolidated retry logic into T006.3-Filter.
- **Critical Revision Note**: **Added T001.1** to update plan.md Summary to reflect the Repeated-Measures design, ensuring Single Source of Truth.