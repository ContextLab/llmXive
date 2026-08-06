---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Input**: Design documents from `/specs/001-predict-reaction-yields-from-spectra/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**CRITICAL SCOPE ALIGNMENT NOTE**:
This project has pivoted from "Predicting Reaction Yields" (as defined in `spec.md`) to "Predicting Normalized DFT Total Molecular Energy" (as defined in `plan.md`) due to the unavailability of verified real-world datasets containing paired (Reaction SMILES, Experimental Yield, Spectrum) data.
- **Impact**: Functional Requirements FR-001 through FR-011 and Success Criteria SC-001 through SC-005 in `spec.md` that reference "yield" are **currently invalid** for the proposed plan.
- **Action**: Task T000 performs the mandatory "Spec Amendment" to formally update `spec.md` to reflect this pivot, establishing the Plan's scope as the new Spec truth. All subsequent tasks implement the **Plan's** pivot (DFT Energy). A formal "Pivot & Limitation Report" (Task T020c) will be generated to document the resolution for the research review stage.

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., User Story 1, User Story 2)
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

- [ ] T000 [P] **Spec Amendment: Pivot to DFT Energy**. **Logic**: 1) Read `plan.md` Summary to confirm pivot to "Normalized DFT Total Molecular Energy". 2) Update `spec.md` to reflect this pivot: Amend FR-001, FR-002, FR-010, and SC-001 to SC-005 to reference "DFT Energy" instead of "Yield". 3) Add a new "Scope Note" section to `spec.md` explicitly stating the pivot and the use of simulated data. 4) Commit this change as a formal "Spec Amendment" to satisfy the Single Source of Truth principle (Constitution Principle IV) before any implementation begins. **Deliverables**: Updated `spec.md` with amended FRs/SCs and Scope Note.
- [ ] T001 Create project structure per implementation plan (`src/`, `data/`, `tests/`, `state/`)
- [X] T002 Initialize Python project with `requirements.txt` (PyTorch CPU, scikit-learn, RDKit, pandas, numpy, matplotlib, seaborn, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/utils/seeds.py` for deterministic random seed management (global seed, PyTorch, NumPy, Python)
- [X] T005 [P] Implement `src/utils/state_manager.py` to update project state hashes and timestamps (Principle V)
- [ ] T006 [P] Configure linting (ruff/flake8) and formatting tools
- [ ] T007 Implement `src/utils/validators.py` for schema validation helpers (YAML/JSON)
- [ ] T008 Create `contracts/` directory with `dataset.schema.yaml` and `model_output.schema.yaml` based on `data-model.md`
- [ ] T008b Retrieve reference functional group frequencies from NIST Chemistry WebBook. **Logic**: Populate `data/references/literature_values.csv` with standard ranges (e.g., Carbonyl: -1750, O-H: -3600) directly in the task logic. **Do NOT fetch from NIST; use hardcoded values for self-containment.**
- [ ] T009 Implement `src/cli/main.py` entry point with `--update-state` flag and basic argument parsing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw spectral/structural data, resample to fixed grids, normalize, encode conditions, and split by reaction template to prevent leakage. **Note**: Target variable is now "normalized DFT total molecular energy" per Plan Summary (post-T000).

**Independent Test**: The pipeline can be executed on a subset of simulated DFT data (MolSpectra), producing three distinct CSV/Parquet files (train, val, test) and a log confirming the absence of overlapping reaction templates across splits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] Unit test for spectral resampling logic in `tests/unit/test_resampling.py`
- [X] T011 [P] Unit test for reaction template extraction and leakage check in `tests/unit/test_splitting.py`
- [X] T012 [P] Integration test for full pipeline end-to-end on dummy data in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [User Story 1] Implement `src/data/ingestion.py` to fetch primary training data and check for independent experimental dataset. **Logic**: 1) Fetch the **primary** training dataset: Simulated DFT data (MolSpectra) from HuggingFace repository ID `sdmattpotter/dft-spectra-energies-v1`. This fetch MUST occur. 2) If the fetch of the primary training data fails (e.g., network error or missing HuggingFace mirror), raise an exception immediately (DO NOT fall back to synthetic; the simulated data IS the primary source here). 3) Attempt to locate an independent experimental dataset for validation. If found, log status='found'; if not (expected), log status='missing' in `data/validation_status.json`. 4) Log the data source used, the exact dataset ID, and the checksum in `data/ingestion_log.json`. 5) If independent dataset is 'found', flag it for T043; if 'missing', document the limitation for T010c. **Deliverables**: Create/Write `data/validation_status.json` (schema: `{status: string, timestamp: string}`) and `data/ingestion_log.json` (schema: `{source: string, dataset_id: string, checksum: string, timestamp: string}`).
- [ ] T014 [User Story 1] Implement `src/data/preprocessing.py`: Resampling IR/Raman to a standard mid-infrared range (starting from the lower wavenumber limit) and NMR to a defined chemical shift range. (or schema-defined ranges from MolSpectra) to fixed grids, unit variance normalization.
- [ ] T015 [User Story 1] Implement `src/data/encoding.py`: Encoding reaction conditions (solvent, catalyst, temperature) as one-hot or embedding vectors. **Note**: These MUST be used as features in the split logic (T017a) to prevent confounding. **Dependency**: This task MUST complete before T017a.
- [ ] T016 [User Story 1] Implement `src/data/template_extraction.py`: Reaction template extraction (substructure at reaction center) using RDKit.
- [ ] T017a [User Story 1] Implement `src/data/splitting.py`: **Reaction Template Splitting**. **Algorithm**: 1) Shuffle samples. 2) Group by `reaction_template_id`. 3) Assign groups to training, validation, and test sets. *Stratify by template_id AND condition_vector_hash*.  4) **Small Dataset Handling**: If a template appears in only 1 sample, assign it to the Train set by default to avoid stratification errors. 5) Verify zero overlap of `template_id` between train, val and test sets. 6) Generate `data/artifacts/leakage_report.json` with hashes for verification. **Deliverables**: 1) Generate `data/processed/split_indices.parquet` with schema `{split: string, index: int}`. 2) Generate `data/artifacts/split_manifest.json` with schema `{train_count: int, val_count: int, test_count: int, overlap_check: boolean}`. **Constraint**: If overlap > 0, raise an error and halt the pipeline. **Dependency**: T015.
- [ ] T017b [User Story 1] Implement `src/data/verification.py`: **Reaction Template Overlap Verification**. **Logic**: Verify that the split produced by T017a has zero overlap of reaction templates between train, val, and test sets using hashes from `data/artifacts/leakage_report.json`. If overlap > 0, raise an error and halt the pipeline.
- [ ] T018 [User Story 1] Implement `src/data/loaders.py`: PyTorch `Dataset` classes for `ReactionSample` handling missing channels (masking). Target variable: normalized DFT total molecular energy.
- [ ] T019 [User Story 1] Create `data/` directory structure (`raw/`, `processed/`, `artifacts/`) and implement checksum logging in `state/`.
- [X] T019b [User Story 1] Create `data/references/literature_values.csv` containing functional group frequencies. **Schema**: Columns must be `functional_group` (string), `min_wavenumber` (float), `max_wavenumber` (float), `unit` (string, e.g., "cm-1"). **Content**: Populate with standard functional group ranges (e.g., Carbonyl: -1750, O-H: -3600, N-H: -3500, C-H: lower frequency range) directly in the task logic. **Note**: Do NOT fetch from NIST; use hardcoded values for self-containment.
- [ ] T020 [User Story 1] Add validation script to verify no scaffold leakage between splits and log results to `data/artifacts/leakage_report.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Attention-Based Yield Prediction Model Training (Priority: P2)

**Goal**: Implement and train the multi-head self-attention model combining spectra, fingerprints, and conditions on CPU. **Target**: Normalized DFT total molecular energy.

**Independent Test**: The training script executes successfully on a CPU-only environment, producing a saved model file and a log showing a decreasing validation loss over defined epochs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] Unit test for model architecture construction in `tests/unit/test_attention_net.py`
- [X] T022 [P] Unit test for training loop logic (loss calculation, backprop) in `tests/unit/test_trainer.py`

### Implementation for User Story 2

- [ ] T023 [P] Implement `src/models/baselines.py`: Fingerprint-only, Spectrum-only, and Condition-only baseline models. Target: normalized DFT total molecular energy.
- [ ] T024 [User Story 2] Implement `src/models/attention_net.py`: Multi-head self-attention network accepting concatenated spectral tensors, ECFP4 vectors, and condition embeddings. Target variable: normalized DFT total molecular energy; Loss function: MSE.
- [ ] T025 [User Story 2] Implement `src/models/trainer.py`: Training loop with Adam optimizer (learning rate), batch size 32, a limited number of epochs, early stopping on validation RMSE (of energy).
- [ ] T026 [User Story 2] Implement `src/models/checkpoint.py`: Checkpointing logic saving weights and config hash to `data/artifacts/`.
- [ ] T027 [User Story 2] Implement `src/cli/main.py` subcommand `train` to orchestrate data loading, model training, and logging.
- [ ] T028 [User Story 2] Add deterministic reproducibility check: re-run training with same seed and verify identical weights/metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Evaluation and Interpretability Analysis (Priority: P3)

**Goal**: Evaluate against baselines, perform statistical tests, generate attention visualizations, and run permutation tests. **Target**: Normalized DFT total molecular energy.

**Independent Test**: The evaluation script runs on the test set, outputs RMSE/MAE/R² metrics, performs a paired t-test, and generates an attention heatmap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] Unit test for metric calculation (RMSE, MAE, R²) in `tests/unit/test_metrics.py`
- [ ] T030 [P] Unit test for paired t-test implementation in `tests/unit/test_statistics.py`

### Implementation for User Story 3

- [ ] T031 [User Story 3] Implement `src/eval/metrics.py`: Compute RMSE, MAE, R² for attention model and all baselines against normalized DFT total molecular energy.
- [ ] T032 [User Story 3] Implement `src/eval/metrics.py`: Paired t-test on absolute errors (Attention vs. best baseline) with Bonferroni correction.
- [ ] T033a [User Story 3] Implement `src/eval/interpretability.py`: **Attention Weight Extraction**. Extract attention weights from the trained model for the test set.
- [ ] T033b [User Story 3] Implement `src/eval/interpretability.py`: **Heatmap Generation**. Generate heatmaps for each sample using the extracted weights.
- [ ] T033c [User Story 3] Implement `src/eval/interpretability.py`: Correlation analysis between attention weights and energy residuals (controlling for fingerprints).
- [ ] T034 [User Story 3] Implement `src/eval/permutation.py`: Permutation test (shuffled energies) to verify R² < 0.05.
- [ ] T035 [User Story 3] Implement `src/cli/main.py` subcommand `eval` to run full evaluation suite and generate `data/artifacts/evaluation_report.json`.
- [ ] T036 [User Story 3] Generate attention weight visualizations mapping the spectral axis to highlight regions with the highest predictive contribution, validating against both literature values from `data/references/literature_values.csv` and simulation injection points. Report correlation between peak locations and expected frequencies in both cases.
- [ ] T043 [User Story 3] **Independent Experimental Validation**. **Logic**: 1) Read `data/validation_status.json`. 2) If status is 'found', load the independent dataset, run the trained model (T027) on it, and compute RMSE, MAE, R². Generate a "Independent Validation Report" comparing these results to the test set results to verify generalizability (FR-010). 3) If status is 'missing', log a "Skipped" status and document the limitation in `data/artifacts/fr010_limitation_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 Documentation updates in `docs/` and `README.md`
- [ ] T038 Code cleanup and refactoring
- [ ] T039 Performance optimization across all stories (ensure CPU execution < 6 hours)
- [ ] T040 Additional unit tests in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation and update `research.md` with findings
- [ ] T042 [Phase N] **Document FR-010 Limitation**. **Logic**: Create `data/artifacts/fr010_limitation_report.json`. **Content**: 1) State that FR-010 (Independent Experimental Validation) cannot be satisfied due to the pivot to simulated data. 2) Document the Plan's mitigation strategy: reliance on Structure-Only Baseline (T023) and Permutation Test (T035).
- [ ] T044 [Phase N] **VIF Calculation**: Implement VIF calculation using scikit-learn and log results to `data/artifacts/vif_report.json`.
- [ ] T045 [Phase N] **Simulated Data Integrity Check**: Verify that the simulated spectra are not deterministic functions of the fingerprint input alone, flagging any high collinearity. Log results to `data/artifacts/integrity_report.json`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on User Story 1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on User Story 2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

# Constitution (FR-030)

# Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms — Research Project Constitution

## Core Principles

### I. Reproducibility (NON-NEGOTIABLE)

Every result reported in this project MUST be reproducible by re-running the
project's `code/` against the project's `data/` on a fresh GitHub Actions
runner. Random seeds MUST be pinned in `code/`. External datasets MUST be
fetched from the same canonical source on every run.

### II. Verified Accuracy (inherits parent Principle II)

Every external citation in `idea/`, `technical-design/`,
`implementation-plan/`, or `paper/` MUST be verified by the
Reference-Validator Agent against the primary source before contributing
review points. Title-token-overlap with the cited source MUST be ≥
`CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7).

### III. Data Hygiene

Datasets MUST be checksummed and the checksum recorded under `data/`. No
data may be modified in place; every transformation MUST produce a new file
with a documented derivation. Personally identifying information MUST NOT
appear in committed data.

### IV. Single Source of Truth (inherits parent Principle I)

Every figure, statistic, or interpretation in the paper MUST trace back to
exactly one row in this project's `data/` and one block in this project's
`code/`. Derived numbers MUST NOT be hand-typed into the paper.

### V. Versioning Discipline

Every artifact under this project carries a content hash. The
Advancement-Evaluator Agent invalidates stale review records when the
hashed artifact changes. Every research-stage artifact change updates this
project's `state/projects/PROJ-165-predicting-chemical-reaction-yields-from.yaml` `updated_at` timestamp.

### VI. Spectral Preprocessing and Grid Alignment

All spectroscopic inputs (IR, Raman, ¹H‑NMR) MUST be resampled to a fixed
wavenumber or chemical shift grid (e.g., 400–4000 cm⁻¹ for IR/Raman, 0–10 ppm
for NMR) and normalized to unit variance before being fed into the model.
This requirement is grounded in the **Methodology sketch** which specifies
resampling to a common grid to enable concatenation into a multi-channel
tensor, ensuring that the attention mechanism operates on a consistent
spectral axis across all samples.

### VII. Structural Baseline and Attention Interpretability

Every model evaluation MUST include a baseline trained on structural
fingerprints (ECFP4) alone to isolate the predictive signal contributed
specifically by spectroscopic data. Additionally, the project MUST generate
and validate attention weight heatmaps against known functional group
frequencies (e.g., carbonyl stretches). This requirement is grounded in the
**Research question** which asks which spectral regions reveal environmental
effects, and the **Expected results** which state that attention heatmaps
must reveal distinct wavenumber regions to confirm the model learns
chemically interpretable features rather than noise.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-165-predicting-chemical-reaction-yields-from/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-165-predicting-chemical-reaction-yields-from.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.

## Verified Accuracy Gate

The Reference-Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement-Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted`
   transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any
citation in `unreachable` or `mismatch` status.

## Versioning

This constitution carries its own semver. Initial version:
**1.0.0** — ratified 2026-07-14.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-165-predicting-chemical-reaction-yields-from | **Field**: chemistry | **Ratified**: 2026-07-14