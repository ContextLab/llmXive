# Tasks: Visual Detail and False Memory Susceptibility

**Input**: Design documents from `/specs/001-visual-detail-false-memory/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [X] T001 Create project structure per implementation plan in `projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/` by running: `mkdir -p data/stimuli data/stimuli_metadata data/responses data/processed data/ethics data/assets code/data code/stimuli code/participants code/analysis tests/unit tests/integration tests/contract docs/ethics`.

- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Fetching, Asset Generation, and Power Analysis.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ EXECUTION FLOW**: This phase follows the strict order: T060 (Scope Lock) → T012.0 (Effect Size Doc) → T012 (Power Calc) → T012.1 (Gate) → T006.1 (Data Fetch) → T015.1 (Asset Gen).

### Infrastructure Tasks

- [X] T004 Setup data directory structure: `data/stimuli/`, `data/responses/`, `data/processed/`, `data/stimuli_metadata/`, `data/ethics/`, `data/assets/`
- [X] T005 [P] Implement data checksum utilities in `code/data/checksum.py`
- [X] T013 [P] [US1] Implement Image Entity class in `code/data/image.py`: Define `Image` class with attributes `id`, `path`, `complexity_score`, `metadata_path`.
- [X] T014 [P] [US1] Implement Participant and Response Entity classes in `code/data/participant.py`: Define `Participant` (id, condition, timestamp) and `Response` (id, question_id, value, timestamp) classes.
- [X] T008 Configure logging infrastructure in `code/utils/logging.py`
- [X] T009 [P] Setup environment configuration management in `code/config.py`

### Power Analysis Sub-phase

**⚠️ ATOMIC UNIT**: T012.0 and T012 must be treated as a single atomic unit. Both documentation of the effect size source and the calculation must be completed before the gate T012.1 can execute.

- [X] T060 [P] [Shared-Infra] [Constitution-VI] [Plan:Scope-Boundary] **Scope Boundary Documentation (Create & Populate)**: Create `docs/ethics/scope_boundary.md`. **Content**: Explicitly state that this study measures *behavioral* false memory rates and does not measure or infer specific molecular/cellular mechanisms (e.g., CREB activation, synaptic weight changes) in humans. Cite Constitution VI and the "Associational vs. Causal" constraint. Include a section "Theoretical Framework: Constructive Memory vs. Biological Mechanism" citing Loftus et al. and Schacter. **Dependency**: None. **Note**: This task must be completed before T012.0 to lock the scope for power analysis.
- [X] T012.0 [P] [Shared-Infra] **Document Effect Size Source**: Update `research.md` by appending **Section 2.1** with the text: "Effect Size Assumption: Cohen's f=0.25 (medium) based on Loftus et al. (1974) 'The Misinformation Effect'." **Output**: `research.md` contains Section 2.1. **Dependency**: T060.
- [X] T010 [P] [Shared-Infra] [US1] **Generate Ethics Templates**: Create `data/ethics/informed_consent.md` and `data/ethics/irb_placeholder.md`. **Content**:
 1. `informed_consent.md`: Embed the following GDPR-compliant template text: "I consent to participate in this study (Project ID: PROJ-317). I understand my data will be anonymized (GDPR Art. 6 & 7). **Anonymization Workflow**: All PII (names, emails, IPs) is stripped from the dataset *at the moment of ingestion* by the `code/participants/session.py` script. The resulting raw data stored in `data/responses/` contains only pseudonymous IDs and is checksummed. I have the right to withdraw at any time, and I can contact the PI at [email]. Data Usage: Responses will be used for statistical analysis only." **MANDATORY**: The generated file MUST include the explicit "Anonymization Workflow" section as written above to satisfy Constitution VI.
 2. `irb_placeholder.md`: Create a placeholder document stating "IRB Approval Pending" with a checklist of required documents (consent form, data management plan, recruitment script) to be submitted.
 **Verification**: This task only generates templates. Runtime verification of real IRB approval is handled by T010.1. **Dependency**: None.
- [X] T010.1 [P] [Shared-Infra] [US1] [Gate] **Runtime IRB Verification**: Implement a check in `code/cli.py` or `code/participants/session.py` that verifies the existence of a real IRB approval document in `data/ethics/irb_approval.pdf` before allowing recruitment to start. If missing, raise `SystemExit` with message "IRB Approval Missing". **Dependency**: T010.
- [X] T012 [P] [Shared-Infra] [US1] Implement Power Analysis in `code/analysis/stats.py`: Calculate required sample size for alpha=0.05, power=0.80, effect_size=medium (Cohen's f=0.25) using `statsmodels.stats.power.FTestAnovaPower`. **Algorithm**: Use `FTestAnovaPower().solve_power(effect_size=0.25, alpha=0.05, power=0.80, alternative='two-sided')`. **Output**: Write results to `data/analysis/power_report.json` with keys `n_per_group`, `total_n`, `effect_size`, `power`, `alpha`, and `power_insufficient` (boolean). **Constraint**: If calculated N < 50, set `power_insufficient` to `true` and log a warning. Do NOT raise `SystemExit` here. The pipeline may proceed with a 'Limited Power' status. **Dependency**: T012.0, T060.
- [X] T012.1 [P] [Shared-Infra] [US1] [Gate] **Power Analysis Validation Logic**: Implement the validation logic in `code/analysis/stats.py` to check for existence of `data/analysis/power_report.json` and validate the `power_insufficient` flag. **Constraint**: If `power_insufficient` is `true`, log a warning "Power Calculation < 50 sessions. Proceeding with Limited Power status." and allow the pipeline to continue. If the file is missing, raise `SystemExit`. **Global Block**: This logic blocks ALL subsequent data collection phases (US1, US2, US3) until it passes (or logs the warning). **Dependency**: T012.
- [X] T017 [P] [Shared-Infra] [US1] Implement stimulus metadata generation (YAML) per Constitution VII in `code/stimuli/metadata.py`. **Dependency**: None.

### Data Fetching & Asset Generation (Moved to Foundational)

- [X] T006.1-VG-Stream [P] [Shared-Infra] [FR-001] **Stream Visual Genome Images**: Implement `code/stimuli/downloader.py` to stream images from Visual Genome using `datasets.load_dataset('visual_genome', split='train', streaming=True)`. **Constraint**: If fetch fails for an *individual image*, skip the image and log the error to `data/logs/manipulation_errors.log`. If the *entire* dataset fetch fails, raise a critical error. Output stream iterator to `data/stimuli/raw/`. **Dependency**: None.
- [X] T006.2-Calc [P] [Shared-Infra] [FR-001] **Calculate Complexity Score**: Implement `code/stimuli/filter.py` to calculate `baseline_complexity_score` for downloaded images based on object density (count of objects per image). **Algorithm**: Filter the fetched image set to ensure the Q1-Q3 range is >= 0.3 (target mean=0.5, std=0.15). **Constraint**: Complexity is derived from existing image annotations. Output stats to `data/processed/complexity_stats.json`. **Dependency**: T006.1-VG-Stream.
- [X] T006.3-Filter [P] [Shared-Infra] [FR-001] **Select Representative Sample**: Implement selection logic in `code/stimuli/filter.py` to select images spanning Q1-Q3. **Constraint**: If the specific complexity range (Q1-Q3 >= 0.3) is NOT met in the fetched batch, log a CRITICAL error and raise `SystemExit`. Do NOT proceed. Output filtered images to `data/stimuli/raw/`. **Dependency**: T006.2-Calc.
- [X] T015.1-Script [P] [Shared-Infra] **Generate Minor Object Assets (Script)**: Create a script in `code/stimuli/asset_generator.py` to generate a set of 20 minor object PNG assets. **Schema**: Assets must be valid PNGs with alpha channel. **Dimensions**: 64x64 pixels. **Naming**: `obj_{id}.png`. **Geometry**: Circles (radius 10-20px), Squares (side 10-20px), Triangles. **Colors**: Random distinct colors. **Background**: Transparent (RGBA mode). Save to `data/assets/minor_objects/`. **Dependency**: None.
- [X] T015.1-Run [P] [Shared-Infra] **Execute Asset Generation**: Run `code/stimuli/asset_generator.py` to generate the assets in `data/assets/minor_objects/`. **Output**: 20 PNG files in `data/assets/minor_objects/`. **Dependency**: T015.1-Script.

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

- [X] T015 [US1] Implement enhanced detail compositing with error handling in `code/stimuli/manipulator.py`: Use PIL/Pillow to overlay a small number of minor object PNG assets (generated by T015.1-Run) onto baseline images (from T006.3-Filter). **Source**: Assets loaded from `data/assets/minor_objects/`. **Selection**: Randomly select a small number of assets per image. **Error Handling**: If manipulation fails for an image, skip the image, log the error to `data/logs/manipulation_errors.log`, and continue processing the remaining images. Do NOT abort the pipeline. **Dependency**: T015.1-Run (Output: assets exist), T006.3-Filter.
- [X] T016 [US1] Implement reduced detail manipulation with error handling in `code/stimuli/manipulator.py`: Use Gaussian blur (radius=5) or masking to remove minor elements from baseline images. **Error Handling**: If manipulation fails for an image, skip the image, log the error to `data/logs/manipulation_errors.log`, and continue processing the remaining images. Do NOT abort the pipeline. **Dependency**: T006.3-Filter. (Note: Does NOT depend on T015.1-Run).
- [X] T019 [P] [US1] Add error handling for missing metadata and failed fetches in `code/data/loader.py`: If a real dataset fetch (if implemented) fails or metadata is missing, skip the image and log the error.
- [X] T020 [P] [US1] Add CLI entry point for running the manipulation pipeline in `code/cli.py`

**Dependency Note for T015.1**: T015.1-Run is a prerequisite ONLY for T015 (Enhanced detail compositing). T016 (Reduced detail) does NOT depend on T015.1-Run. This is a targeted dependency for asset generation, not a shared prerequisite for the entire US1 group.

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

- [X] T027.1 [P] [US2] Generate mock object pool: Create `data/assets/mock_objects.json` containing a list of 50 distinct object names and categories (e.g., `[{ "object_name": "red car", "category": "vehicle" }]`).
- [X] T025 [P] [US2] [Model:View] **Implement View: Image Display**: Implement `code/participants/interface.py` to display baseline images for 10 seconds (±0.5s). **Logic**: Timer-based display. **Dependency**: None.
- [X] T026 [US2] [Model:View] **Implement View: Distractor Task**: Implement `code/participants/interface.py` to administer arithmetic questions for 2 minutes (±10s). **Constraint**: If duration is outside the acceptable range, **Flag session as Incomplete** in the response log. Do NOT continue silently. **Dependency**: None.
- [X] T027.2 [US2] [Model:Gen] **Generate Recognition Questions (Strict)**: Implement `code/participants/interface.py` to extract true details from `data/stimuli_metadata/{id}.yaml`. Generate false/lure details by selecting from `data/assets/mock_objects.json` (T027.1) and filtering out items present in the baseline (using T006.3-Filter output). **Algorithm**: 1. Extract true objects from image metadata. 2. Filter mock pool to remove true objects. 3. If len(false_pool) < 10, raise `SystemExit`. 4. Select a balanced set of true and false items. **Constraint**: Must generate a balanced set of questions. **Failure Mode**: If strict 10/10 cannot be met, raise `SystemExit`. Do NOT generate partial sets. **Dependency**: T017, T027.1, T006.3-Filter.
- [X] T027.3 [US2] [Model:Capture] **Implement Response Capture**: Implement `code/participants/session.py` to record responses with timestamps. **Dependency**: T027.2.
- [X] T029 [US2] Implement local caching and retry logic for network timeouts in `code/participants/session.py`
- [X] T030 [US2] Implement partial session recording and flagging for dropouts in `code/participants/session.py`
- [X] T031 [US2] Add CLI entry point for running simulated participant sessions in `code/cli.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Results Generation (Priority: P3)

**Goal**: System executes repeated-measures ANOVA and generates visualization with confidence intervals.

**Independent Test**: Can be fully tested by running the analysis script on synthetic/mock participant data and verifying ANOVA results and visualization are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for ANOVA calculation in `tests/unit/test_stats.py`
- [ ] T033 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_stats.py`
- [ ] T034 [P] [US3] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 3

- [X] T038 [US3] Implement dataset-variable fit check (compare mock distribution to target) in `code/analysis/stats.py`: **Dependency**: T017, T027.3.
- [X] T035.1 [US3] **Calculate Baseline False Memory Rate**: Implement `code/analysis/stats.py` to calculate the false memory rate specifically for the 'Baseline' condition. **Output**: Add `baseline_false_memory_rate` to `data/analysis/anova_results.json`. **Dependency**: T027.3.
- [X] T035 [US3] Implement repeated-measures ANOVA using scipy.stats in `code/analysis/stats.py`. **Input Format**: Wide-format dataframe with columns: `participant_id`, `baseline`, `enhanced`, `reduced`. **Algorithm**: Perform Mauchly's test for sphericity. If sphericity is violated, apply Greenhouse-Geisser correction. Calculate F-statistic using `scipy.stats.f_oneway` on the three condition columns (baseline, enhanced, reduced) treating them as repeated measures. **Output**: Write results to `data/analysis/anova_results.json` with keys `f_statistic`, `p_value`, `effect_size`, `degrees_of_freedom`, `sphericity_corrected`. **Constraint**: Do NOT use One-Way ANOVA logic. **Dependency**: T038, T012.1, T017, T027.3, T035.1.
- [X] T036 [US3] Implement multiple-comparison correction (Bonferroni) in `code/analysis/stats.py`. **Dependency**: T035.
- [X] T037 [US3] Implement visualization generation (mean false memory rates with confidence intervals) in `code/analysis/viz.py`. **Dependency**: T035.
- [X] T072 [US3] **Analysis Output: Limitations Section**: Update `code/analysis/stats.py` (T035) to automatically append a `limitations` key to the `anova_results.json` object. **Content**: This key must contain a string stating that the findings are "associational" and "do not establish a molecular or cellular mechanism," citing the scope boundary document (T060). **Dependency**: T035, T060.
- [X] T039 [US3] Add CLI entry point for running analysis in `code/cli.py`. **Dependency**: T035, T036, T037.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Scope Boundary & Reviewer Response (Revision Response)

**Goal**: Address reviewer concerns regarding the lack of a biological mechanism while strictly adhering to the project's "associational" scope and Constitution VI (Human Subjects Ethics).

**Context**: The reviewer (Eric Kandel-simulated) requested a hypothesis linking visual detail to synaptic changes (e.g., CREB, PKA). However, the project spec explicitly defines the scope as **behavioral only** (associational, not causal) and Constitution VI explicitly **excludes** biological mechanism mapping tasks. The project cannot measure synaptic changes in human subjects; it can only measure behavioral correlates.

**Strategy**: Instead of implementing untestable biological claims, we will:
1. Explicitly document the **Scope Boundary** in `docs/ethics/scope_boundary.md` (Task T060, now in Phase 2).
2. Add a **Theoretical Framework** task that cites established literature (e.g., Loftus, Schacter) to explain the *behavioral* mechanism (constructive memory) without making unverified claims about specific synaptic pathways in humans.
3. Ensure the analysis output frames results as "associational evidence" rather than "mechanistic proof".
4. Provide a formal response to the reviewer acknowledging the biological question while explaining the methodological constraints of human behavioral research.

- [X] T061.2 [US3] **Theoretical Framework Update (Documentation Only)**: Update `research.md` to include a section "Theoretical Framework: Constructive Memory vs. Biological Mechanism". **Content**: Cite Loftus et al. (misinformation effect) and Schacter (seven sins of memory) to explain the *psychological* mechanism of false memory. Explicitly contrast this with the *biological* mechanisms (e.g., Kandel's Aplysia work) to clarify that while the latter inspires the former, this study does not claim to measure synaptic changes. **Constraint**: This task is for documentation purposes only; no biological mechanism mapping is implemented. **Note**: Citation validation is handled by CI/CD, not manual tasks. **Dependency**: T060.
- [X] T062 [US3] **Analysis Output Framing**: Update `code/analysis/stats.py` (T035) and `code/analysis/viz.py` (T037) to ensure all printed outputs and plot titles use language such as "Associational Evidence," "Behavioral Correlate," or "Statistical Association" rather than "Mechanism," "Cause," or "Synaptic Change". **Verification**: Add a regex check in `tests/unit/test_viz.py` that asserts plot titles contain "Associational Evidence". **Dependency**: T035, T037.
- [X] T063 [US3] **Reviewer Response Artifact**: Create `docs/reviews/review_response_001.md`. **Content**: A formal response to the Eric Kandel-simulated review, acknowledging the importance of the biological question, explaining the scope constraints (Constitution VI), and detailing how the project remains scientifically rigorous within its behavioral bounds. **Dependency**: T012.1, T062.

**Checkpoint**: Scope is explicitly defined, biological claims are removed/clarified, and reviewer concerns are formally addressed in documentation.

---

## Phase 7: Revision-Driven Reviewer Response Tasks (Addressing Eric Kandel's Specific Concerns)

**Goal**: Directly address the specific "ladder of explanation" critique by documenting the *limits* of the current behavioral methodology while providing a clear path for future mechanistic studies.

**Context**: The reviewer specifically asked: "where is this 'detail' written in the neuron?" and suggested hypotheses about "synaptic weight" and "reconsolidation". Since we cannot measure these in humans, we must explicitly document why we cannot, and propose a *future* study design that would.

- [ ] T070 [US3] **Reviewer Response: Ladder of Explanation Gap**: Update `docs/reviews/review_response_001.md` (T063) to include a specific section "The Ladder of Explanation Gap". **Content**: Explicitly map the current study's position on the ladder (Behavioral Observation) vs. the reviewer's desired position (Molecular Mechanism). Cite the specific constraints (human subjects, non-invasive methods) that prevent climbing the ladder further. **Dependency**: T063.
- [ ] T071 [Shared-Infra] **Future Work Proposal: Mechanistic Pathway**: Create `docs/research/future_mechanistic_study.md`. **Content**: Propose a *future* study design (e.g., using fMRI + computational modeling, or animal model analogs) that *could* address the synaptic weight question. Outline the specific molecular markers (CREB, PKA) and cellular changes that would be measured if the behavioral effect is replicated. **Constraint**: Clearly state this is a *proposal* for future work, not part of the current scope. **Dependency**: T070.
- [ ] T073 [US3] **Reviewer Response: Specific Hypothesis Rebuttal**: Update `docs/reviews/review_response_001.md` (T063) to directly address the reviewer's specific hypothesis about "synaptic weight vs. reconsolidation failure". **Content**: Acknowledge the plausibility of both hypotheses, but explain that the current behavioral paradigm (false memory recognition) cannot distinguish between them without additional neurobiological data. Propose that the current study's goal is to *establish the behavioral effect* as a prerequisite for such mechanistic studies. **Dependency**: T070.

**Checkpoint**: All specific reviewer concerns are addressed with clear documentation of limitations and future directions.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T045.1 [P] Refactor error handling logic into a utility module in `code/utils/error_handling.py`. **Dependency**: T019.
- [X] T045.2 [P] Extract magic numbers and constants to `code/config.py`. **Dependency**: T009.
- [X] T046-A [P] **Performance Profiling**: Implement `code/utils/profiler.py` to run `cProfile` on the image manipulation pipeline. **Output**: Generate `data/logs/profile_report.txt` identifying the top 3 bottlenecks. **Dependency**: T015, T016.
- [X] T046-B [P] **Performance Optimization**: Optimize the top bottleneck identified in T046-A to ensure <30s/image. **Dependency**: T046-A.
- [X] T047 [P] Additional unit tests for edge cases (dropout, network timeout) in `tests/unit/`. **Dependency**: T027.3, T035.
- [X] T048 Security hardening (ensure no PII leakage in logs). **Dependency**: T010, T027.3.
- [X] T049 [P] Run quickstart validation: **Action**: Execute the `code/cli.py --validate-quickstart` command to verify the project structure and basic functionality. **Dependency**: T060, T046-B.

**Note on Removed Phase 6**: Phase 6 (Mechanism Mapping) and tasks T040-T042 from the *previous* iteration were removed. The new T060-T063 in this revision are specifically for *documenting* the scope boundary and *responding* to the reviewer, not for implementing the biological mechanism itself.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Scope Clarification (Phase 6)**: Depends on Foundational phase; can be done in parallel with US3 implementation.
- **Revision-Driven Reviewer Response (Phase 7)**: Depends on Phase 6 completion.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 (uses manipulated images) but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data generation
- **Scope Clarification (Phase 6)**: Can start after Foundational; depends on US3 for analysis framing.
- **Revision-Driven Reviewer Response (Phase 7)**: Depends on Phase 6 and US3.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Critical Task Dependencies

- **T012/T012.1 (Power Analysis)**: T012 calculates and writes the report. T012.1 is the sole authority for halting the pipeline if N < 50 (or logging warning).
- **T027.2 (Recognition Question Generator)**: Blocked by **T017** (Stimulus Metadata Generation), **T027.1** (Mock Object Pool), and **T006.3-Filter** (Baseline Image Selection).
- **T015/T016 (Manipulation)**: Blocked by **T006.3-Filter** (Data Fetch). **T015** depends on **T015.1-Run** (assets exist). **T016** does NOT depend on T015.1-Run.
- **T038 (Dataset-variable fit check)**: Must run before **T035** (ANOVA).
- **T035.1 (Baseline Rate)**: Must run before **T035** (ANOVA) to ensure baseline data is available.
- **T060-T063 (Scope Clarification)**: **T060** is in Phase 2 and must be completed before **T012.0** (Power Analysis) to lock scope. **T062/T063** are blocked by T012.1.
- **T070-T073 (Reviewer Response)**: **T070** depends on **T063**. **T071** depends on **T070**. **T072** depends on **T035** and **T060**. **T073** depends on **T070**.
- **T006.0 (Spec Update)**: REMOVED. Dataset deviation is documented in plan.md.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Scope Clarification (Phase 6) can be worked on in parallel with US3 implementation.
- Revision-Driven Reviewer Response (Phase 7) tasks can be worked on in parallel with each other once T063 is complete.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for image enhancement logic in tests/unit/test_stimuli_manipulator.py"
Task: "Unit test for image reduction logic in tests/unit/test_stimuli_manipulator.py"

# Launch all models for User Story 1 together:
Task: "Implement enhanced detail compositing (add minor objects) in code/stimuli/manipulator.py"
Task: "Implement reduced detail manipulation in code/stimuli/manipulator.py"
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
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Stimuli)
 - Developer B: User Story 2 (Session)
 - Developer C: User Story 3 (Analysis)
 - Developer D: Scope Clarification (Phase 6)
 - Developer E: Reviewer Response (Phase 7)
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
- **Critical Revision Note**: Task T006.0 removed. It violated the 'Single Source of Truth' principle by attempting to edit spec.md. The dataset deviation (COCO 2017) is correctly documented in plan.md and should not be altered in spec.md by implementation tasks.
- **Critical Revision Note**: T010 updated to include detailed GDPR Anonymization Workflow and generate both consent and IRB placeholders. T010.1 added for runtime IRB verification.
- **Critical Revision Note**: T012 refactored to only calculate; T012.1 is now the sole gate for halting the pipeline.
- **Critical Revision Note**: T027.2 updated to enforce a minimum threshold (8 items) instead of a rigid 10/10 split and to flag sessions instead of raising hard errors. **REVISION**: T027.2 now ENFORCES strict 10/10 split and raises `SystemExit` on failure. Partial sets removed.
- **Critical Revision Note**: T026 updated to flag sessions as incomplete if duration is out of range.
- **Critical Revision Note**: T015.1 split into T015.1-Script and T015.1-Run to clarify asset generation dependency; T015 tag updated to [Shared-Infra] for T015.1-Script.
- **Critical Revision Note**: T060 moved to Phase 2 and added as dependency for T012.0.
- **Critical Revision Note**: T061.1 removed; citation validation handled by CI/CD.
- **Critical Revision Note**: T049 replaced with a concrete executable validation task.
- **Critical Revision Note**: T017 moved to Phase 2 to resolve cross-phase dependency for T027.2.
- **Critical Revision Note**: T061.2 added to address Eric Kandel's review by explicitly contrasting psychological and biological mechanisms in documentation only.
- **Critical Revision Note**: T062 added to ensure analysis outputs frame results as "Associational Evidence" to prevent misinterpretation of behavioral data as mechanistic proof.
- **Critical Revision Note**: T063 added to formally document the project's response to the biological mechanism critique, acknowledging the reviewer's point while defending the behavioral scope. T063 now explicitly depends on T012.1.
- **Critical Revision Note**: T006.1-VG-Stream, T006.2-Calc, T006.3-Filter atomized from original T006.1.
- **Critical Revision Note**: T025, T026, T027.2, T027.3 atomized into Model/View components.
- **Critical Revision Note**: Explicit dependencies added for T038, T039, T045.1, T045.2, T046, T047, T048, T063.
- **Critical Revision Note**: Phase 7 (T070-T073) added to directly address the "ladder of explanation" critique and propose future mechanistic work.
- **Critical Revision Note**: T006.1-VG-Stream, T006.2-Calc, T006.3-Filter, T015.1-Script, T015.1-Run moved to Phase 2 to ensure data and assets are ready before US1.
- **Critical Revision Note**: T035 updated to mandate Repeated-Measures ANOVA logic and remove One-Way fallback.
- **Critical Revision Note**: T035.1 added to explicitly calculate baseline false memory rate.
- **Critical Revision Note**: T072 moved to Phase 5 and updated to append `limitations` key to JSON.
- **Critical Revision Note**: T046 split into T046-A (Profiling) and T046-B (Optimization).