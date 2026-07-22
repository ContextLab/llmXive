# Tasks: llmXive follow-up: extending "DomainShuttle: Freeform Open Domain Subject-driven Text-to-video Gener"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure by executing: `mkdir -p src/{config,data,models,analysis,utils} tests data/{raw,processed,results} specs/001-gene-regulation/contracts docs`. This creates the exact directory tree defined in the plan.md structure section.
- [X] T002 Initialize Python 3.10 project with PyTorch (CPU), scikit-learn, pandas, datasets, pillow, tqdm, opencv-python dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup base configuration management in `src/config/settings.py` (paths, seeds, hyperparameters)
- [X] T004b [P] Define and validate the 'fidelity_threshold' configuration key in `src/config/settings.py`. Set default value to `None`. Ensure the code raises a `ValueError` with a clear message if `None` is accessed by T021. This aligns with the spec's 'deferred' default.
- [X] T005 [P] Implement data I/O utilities in `src/utils/io.py` (checksumming, path handling, JSON/CSV serialization)
- [ ] T006 [P] Create base entity schemas in `specs/001-gene-regulation/contracts/`.
 - Create `subject.schema.yaml` with fields: `subject_id` (string), `complexity_score` (number), `raw_embedding_path` (string).
 - Create `compressed_vector.schema.yaml` with fields: `subject_id` (string), `target_dimension` (integer), `reconstruction_loss` (number), `model_path` (string).
 - Create `fidelity_result.schema.yaml` with fields: `subject_id` (string), `dimension` (integer), `style` (string), `clip_score` (number), `timestamp` (string).
 - Ensure all files are valid YAML syntax.
- [X] T007 Setup logging infrastructure in `src/utils/logging.py` with structured output for pipeline stages
- [X] T008 Implement error handling wrapper for data loading and model inference to enforce "FAIL LOUDLY" policy (no synthetic fallbacks)
- [X] T017 [P] Implement a per-sample timeout wrapper function in `src/utils/timeout.py`.
 - Input: A callable function and a timeout duration (seconds).
 - Behavior: Executes the callable. If a `TimeoutError` or time limit is exceeded, catch the exception, log the specific `sample_id` and duration to `data/processed/timeout_log.json`, and return a sentinel value (e.g., `None` or a specific error code) to allow the pipeline to continue.
 - Constraint: Must NOT raise an exception that aborts the parent process.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download a curated subset of diverse subjects from WebVid-10M, compute visual complexity scores, and extract frozen DomainShuttle embeddings.

**Independent Test**: The pipeline can be tested by running the data loader and encoder, then verifying that the output directory contains a set of tensors and a corresponding CSV of complexity scores, with no missing values.

### Implementation for User Story 1

- [X] T009 [US1] Implement WebVid-10M data loader in `src/data/loaders.py` to fetch exactly 100 diverse subjects via `datasets.load_dataset` using stratified random sampling by the 'category' column (uniform distribution across top categories) with seed=42, with no synthetic fallback
- [X] T010 [US1] Implement visual complexity scoring in `src/data/complexity.py` using Sobel edge density: calculate mean magnitude of Sobel gradient (kernel size) across multiple equidistant frames per subject, with L2 normalization, to calculate a score for each subject's reference image
- [X] T011 [US1] Implement DomainShuttle encoder wrapper in `src/data/embeddings.py` to load frozen weights and extract high-dimensional embeddings for all 100 subjects. **Output**: Save tensors to `data/processed/embeddings/` as `.pt` files named `{subject_id}.pt`. **VALIDATION**: Verify the encoder loads without CUDA errors and produces output tensors before marking this task complete.
- [X] T012 [US1] Create pipeline script in `src/cli.py` to orchestrate: Load -> Complexity -> Embed -> Save (outputs to `data/processed/embeddings/` and `data/processed/complexity_scores.csv`). **Artifact**: `data/processed/complexity_scores.csv` must contain 100 rows with `subject_id` and `complexity_score` columns.
- [X] T013 [US1] Add validation logic to ensure a sufficient number of unique IDs are processed and saved, logging any failures to `data/processed/failed_subjects.log`. **Artifact**: `data/processed/failed_subjects.log` must exist and contain a list of failed subject IDs.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Optimized Compression and Dimensionality Sweep (Priority: P2)

**Goal**: Train lightweight, CPU-only Autoencoders to compress embeddings into latent vectors of dimensions ranging from small to large scales, using cosine similarity loss.

**Independent Test**: The training loop can be tested independently by verifying that for each target dimension, a trained model checkpoint is saved, and the training log shows convergence of the cosine similarity loss without GPU utilization.

### Implementation for User Story 2

- [X] T014 [US2] Implement CPU-optimized Autoencoder architecture in `src/models/autoencoder.py`.
 - **Prerequisite**: The `fidelity_threshold` and loss configuration must be defined in `src/config/settings.py` (see T004b).
 - **Architecture**: A multi-layer perceptron with ReLU activation. Hidden layers sized proportionally to the input dimension.
 - **Constraint**: The model must support configurable target dimensions [32, 64, 128, 256].
 - **Loss**: The model class must be configured to use `torch.nn.CosineEmbeddingLoss` (or equivalent 1-cosine_similarity implementation) as the loss function. **FORBID** `MSELoss`.
 - **Execution**: Enforce `batch_size=1` and `gradient_accumulation_steps=1`. Include a runtime memory check that aborts if usage exceeds a predefined threshold.
- [X] T015 [US2] Implement training loop function in `src/models/training.py`.
 - **Input**: Autoencoder model instance, embeddings, target dimension.
 - **Logic**: The function MUST explicitly use `torch.nn.CosineEmbeddingLoss` (or `1 - cosine_similarity`) as the loss function. Log the specific loss value type used to verify compliance with FR-004.
 - **Output**: Save checkpoints to `data/processed/compressed_models/` named `{target_dimension}_ae.pt`.
 - **Dependency**: Requires T017 (timeout utility) to be available for wrapping the training loop if needed.
- [X] T016 [US2] Create dimensionality sweep script in `src/cli.py`.
 - **Logic**: This script MUST iterate over the specific set of dimensions [, 64, 128, 256]. For each dimension, it MUST call the training function implemented in T015.
 - **Output**: Aggregate per-dimension logs into `data/processed/sweep_logs.json`.
 - **Dependency**: Requires T015 (training function) to be implemented and callable.
- [X] T018 [US2] Add validation to exclude subjects where training fails to converge, updating `data/processed/failed_subjects.log`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Identity Fidelity Validation and Phase Transition Detection (Priority: P3)

**Goal**: Generate synthetic videos using compressed vectors across multiple style domains, compute CLIP Image Similarity scores, and detect "phase transition" via segmented regression.

**Independent Test**: The validation pipeline can be tested by running the generation for a single subject at a single dimension, generating the video, computing the CLIP Image Similarity score, and verifying the metric matches the expected range.

### Implementation for User Story 3

- [X] T019 [US3] Implement video generation script in `src/analysis/generation.py` to synthesize videos using frozen DomainShuttle generator, compressed vectors, and prompts for 'Anime', 'Photorealistic', 'Sketch' domains. **Must integrate** the per-sample timeout logic from T017 to handle individual generation timeouts gracefully.
- [X] T020 [US3] Implement Full Fidelity Curve Scoring in `src/analysis/fidelity.py`.
 - **Dependency**: Requires T019 (video generation logic) to be available.
 - **Logic**: Reuse the generation logic from T019 to generate videos for all dimensions [16, 32, 64, 128, 256] and all subjects. Compute CLIP Image Similarity scores (image-image) using a CLIP ViT-B model and mean of equidistant frames.
 - **Output**: Save the **full fidelity-vs-dimension matrix** to `data/results/fidelity_vs_dimension_curve.json` (structure: `{subject_id: {dim: {style: score}}}`).
 - **Verification**: Verify file exists at `data/results/fidelity_vs_dimension_curve.json` and contains valid JSON with keys for all 100 subjects.
- [X] T021 [US3] Implement Minimum Dimensionality Calculation in `src/analysis/fidelity.py`.
 - **Input**: Load `fidelity_threshold` from `src/config/settings.py` (raise `ValueError` if `None`).
 - **Logic**: Iterate through the **full fidelity curve** generated by T020, find the *first* dimension where CLIP score >= threshold for each subject.
 - **Output**: Save the result as `data/results/minimum_dimensions.json` containing `{subject_id: min_dim}`.
- [ ] T022 [US3] Create correlation analysis script in `src/analysis/regression.py`.
 - **Input**: Complexity scores from T012 and full fidelity curve from T020.
 - **Logic**:
 1. Attempt to fit a 2-segment piecewise linear model using `scipy.optimize.curve_fit`.
 2. **Critical Fallback**: If the breakpoint p-value >= 0.05 or the fit fails to converge, **automatically fall back** to a simple linear regression model.
 3. **Recording**: Log the chosen model type. If the fallback is used, the result (linear degradation) MUST be recorded as a valid scientific outcome indicating the hypothesis was falsified.
 - **Output**:
 - `data/results/phase_transition_analysis.pdf`
 - `data/results/metrics.json` with the following exact structure:
 ```json
 {
 "model_type": "phase_transition" | "linear",
 "breakpoint": <number or null>,
 "r_squared": <number>,
 "hypothesis_status": "supported" | "falsified",
 "details": "..."
 }
 ```
 - If `model_type` is "linear", `hypothesis_status` MUST be "falsified".

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T026 [P] Documentation updates in `docs/` covering data flow and artifact locations
- [ ] T027 Code cleanup and refactoring of `src/` modules
- [ ] T028 Performance optimization for CPU-bound operations (e.g., batch processing strategies)
- [ ] T029 [P] Run quickstart.md validation to ensure all paths and scripts are executable
- [ ] T030 Verify all contracts in `specs/001-gene-regulation/contracts/` match generated data structures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 outputs (embeddings)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 outputs (complexity) and US2 outputs (compressed models)

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tasks for User Story 1 together:
Task: "Implement WebVid-10M data loader in src/data/loaders.py"
Task: "Implement visual complexity scoring in src/data/complexity.py"
Task: "Implement DomainShuttle encoder wrapper in src/data/embeddings.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify 100 embeddings + complexity scores)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (compression sweep)
4. Add User Story 3 → Test independently → Deploy/Demo (final analysis)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data & Embeddings)
 - Developer B: User Story 2 (Autoencoders)
 - Developer C: User Story 3 (Generation & Analysis)
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
- **Data Hygiene**: Real data only. If WebVid fetch fails, raise error. Do not generate synthetic data.
- **Compute Constraints**: All models must run on CPU. If GPU is required, task must explicitly state "CPU-optimized" or "streaming" approach.
- **Timeout Handling**: All generation and training tasks must include per-sample timeout logic (T017) to respect CI limit without crashing. T017 is a shared utility that records timeouts and forbids global aborts.
- **Dimensionality Sweep**: Strictly use dimensions [16, 32, 64, 128, 256] (5 values) as per FR-003.
- **Configurable Threshold**: The fidelity threshold MUST be loaded from `src/config/settings.py` and not hard-coded.
- **Data Flow Integrity**: Ensure T019 (Generation) executes strictly after T016 (Sweep) completes. T020 (Full Curve) depends on T019. T021 (Min Dim) depends on T020. T022 (Regression) depends on T020.
- **Error Propagation**: If T018 marks a subject as failed, T019 and T020 must explicitly skip that subject ID to prevent cascade errors.
- **Loss Function**: T014/T015 MUST use Cosine Similarity loss; MSE is forbidden.
- **Regression Fallback**: T022 MUST handle non-significant breakpoints by falling back to linear regression and recording it as a valid scientific outcome.