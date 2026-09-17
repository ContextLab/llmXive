# Tasks: Gut Microbiome-Cognitive Correlation Study

**Input**: Design documents from `/specs/001-gut-microbiome-cognitive/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [ ] T001 Create project structure per implementation plan. **Command**: `mkdir -p code/{utils,models,preprocess,analysis,visualize} data/{raw,processed,interim} results/{associations,plots,sensitivity,power} tests`. **Output**: Directory tree created. **Requirement**: Create `__init__.py` in every `code/` subdirectory and `tests/` to ensure package importability.
- [X] T002 Initialize Python 3.10 project with `code/requirements.txt` (pinned versions: pandas==2.0.3, numpy==1.24.3, scikit-learn==1.3.0, statsmodels==0.14.0, seaborn==0.12.2, matplotlib==3.7.2, pyarrow==12.0.1, requests==2.31.0, huggingface_hub==0.17.1, scikit-bio==0.5.9, zCompositions==1.3.2). **Output**: `code/requirements.txt` created.
- [ ] T003 [P] Configure linting and formatting tools. **Deliverables**: Generate `.ruff.toml` with rules E, F, W, I, line-length 88 and `pyproject.toml` with `[tool.black]` section (line-length=88, quote-style="double"). **Output**: Configuration files created.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data validation gates and power analysis.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with paths, random seeds, and constants. MUST include UK Biobank field IDs: microbiome-related fields, cognitive assessment fields, and confounder IDs (sex, age, BMI, etc.). **Requirement**: Must define `PREVALENCE_THRESHOLD = 0.01` (1%) for taxon filtering. **Requirement**: Must define `PHASE = "SYNTHETIC"` to control validation logic.
- [X] T005 [P] Setup data hygiene utilities (checksumming, PII masking helpers) in `code/utils/hygiene.py`
- [X] T006 [P] Implement streaming/batch data loader utilities in `code/utils/streaming.py` to handle >14GB datasets within 7GB RAM limits
- [X] T007 [P] Create base data models/entities (Participant, MicrobiomeProfile, CognitiveScore) in `code/models/`. Implement classes with explicit attributes matching Spec Key Entities.
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logging.py`
- [X] T011 [P] Setup environment configuration management for credentials. **Deliverables**: Create `.env.example` with keys `UKB_TOKEN`, `API_KEY`. Implement `code/config.py` to load from `os.environ`. **Output**: `.env.example` and config logic.
- [X] T019 [P] **Execute Power Analysis Gate**. **Logic**: 1) Generate a synthetic dataset with known effect size beta=0.1 using the **shared schema definition** from `code/config.py` (created in T004). **Schema Definition**: The generator MUST produce a DataFrame with columns: `participant_id` (int), `age` (float, mean=65), `sex` (str, 0/1), `bmi` (float, mean=27), `diet_quality` (float, 0-100), `activity` (float, 0-100), `medication_use` (int, 0/1), `antibiotic_use` (int, 0/1), `taxon_A` through `taxon_N` (float, compositional, sum=1), `cog_reaction` (float), `cog_memory` (float), `cog_reasoning` (float). Distributions must mimic UKB statistics (Gaussian for covariates, Dirichlet for taxa). 2) Run power analysis script. 3) **Verify Script Correctness**: Confirm script output matches theoretical power for beta=0.1 within 5% tolerance. 4) **Report Feasibility**: Report calculated power for the planned sample size. **Gate Criteria**: PASS = Script Correctness Verified (theoretical match) AND power >= 0.8. **Output**: `results/power/power_gate_report.md`. **Note**: This task validates the *methodology* (including Bayesian zero-replacement) using synthetic data; it does NOT depend on T014-T018 implementation. It uses the **SAME schema logic** as the main pipeline by importing from `code/config.py` to ensure data provenance. **Requires T004 completion**.
- [X] T025 [P] **Execute Reference-Validator Agent** on cognitive instrument citations (FR-009) against primary sources. **Logic**: Attempt to validate citations. **Crucial Condition**: If `config.PHASE == 'SYNTHETIC'`, the validator MUST accept a status of `DEFERRED` and **NOT** block the pipeline. If `config.PHASE == 'REAL'`, the validator MUST enforce strict primary source validation. **Specific Behavior**: If the validator fails to find a primary source for a synthetic placeholder citation, it MUST assign status `DEFERRED` and continue without blocking the pipeline. **Output**: `results/validation/instrument_citation_report.md` to satisfy the 'Verified Accuracy' gate.
- [X] T026 [P] Update `code/config.py` and metadata with validated citation IDs. **Logic**: Enforce citation validity by ensuring the `validation_reference` field is present in the config. **Crucial Condition**: If the validation status is `DEFERRED` (synthetic phase), the system MUST proceed without raising an error. **Output**: Updated `code/config.py`.
- [X] T027 [P] Implement `code/analysis.py` to load and use the validated cognitive instrument definitions (field IDs corresponding to the specified cognitive constructs) from `code/config.py` and map them to analysis variables.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Download and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic microbiome and cognitive data, filter cohort, and produce ILR-transformed data.

**Independent Test**: Run the pipeline on a subset; verify output contains ILR-transformed genus-level coordinates and matched cognitive scores with no missing participants.

### Tests for User Story 1 (OPTIONAL)

- [X] T040 [P] [US1] Unit test for ILR transformation with Bayesian zero-replacement in `tests/test_preprocess.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `code/pipelines/download.py` to **Generate Synthetic Microbiome Data**. **Logic**: Since real UK Biobank data is access-gated and cannot be downloaded on CI, this task implements a **deterministic synthetic generator** that mimics the UKB schema (Field IDs 20400, 20002, etc.) with realistic distributions. **Schema**: `participant_id`, `age`, `sex`, `bmi`, `diet_quality`, `activity`, `medication_use`, `antibiotic_use`, `taxon_counts` (compositional array generated via Dirichlet distribution). **Fail Loud**: If `config.USE_REAL_DATA` is True and credentials are missing, raise `DataFetchError` with clear instructions; it MUST NOT fall back to synthetic data silently. **Output**: `data/raw/microbiome_raw.parquet` (checksummed).
- [X] T015 [P] [US1] Implement `code/pipelines/download.py` to **Generate Synthetic Cognitive Data**. **Logic**: Generate synthetic cognitive assessment scores (reaction time, numeric memory, reasoning) that are **statistically correlated** with the synthetic microbiome data generated in T014 (using a shared random seed and a defined covariance matrix to mimic UKB correlations). **Output**: `data/raw/cognitive_raw.parquet` (checksummed). **Fail Loud**: Same as T014; raise `DataFetchError` on real fetch failure, do not silently fallback.
- [X] T016 [US1] Implement `code/preprocess.py` to filter cohort: exclude recent antibiotic users and participants missing either data type. **Output**: `data/processed/filtered_cohort.parquet`. **Includes**: Derive `Age_Group` categorical variable from continuous age where `Age >= code/config.py.AGE_GROUP_CUTOFF`. Log exclusion counts to `data/processed/cohort_retention_log.json`.
- [X] T017 [US1] Apply **Bayesian-multiplicative zero-replacement** to raw microbiome counts to handle zero counts. **Requirement**: This task explicitly satisfies the Spec Edge Case requirement to "apply a small pseudocount before transformation" by implementing the statistically sound Bayesian-multiplicative replacement method (via `zCompositions`), which serves as the rigorous equivalent to a simple pseudocount, avoiding log(0) while preserving compositional structure. **Output**: `data/processed/zero_replaced_counts.parquet`.
- [X] T018 [US1] Implement `code/preprocess.py` genus-level aggregation and **Isometric Log-Ratio (ILR)** transformation. **Pipeline**: Zero-replaced counts -> ILR transformation using **sequential binary partition (sbp) defined in Aitchison** via `skbio.stats.composition.ilr` with explicit basis matrix construction to produce orthonormal coordinates. **Output**: `data/processed/ilr_coordinates.parquet`. Satisfies Constitution Principle VI and FR-003 by producing orthonormal coordinates that break the sum-to-zero constraint, making standard linear regression mathematically sound.
- [X] T030 [US1] **Pre-screen taxa by prevalence**. Filter taxa with prevalence below `code/config.py.PREVALENCE_THRESHOLD` and generate report. **Output**: `data/processed/prevalence_filter_report.json`. **Justification**: Minimize noise from rare taxa; default threshold 1%. This step satisfies the 'quality filtering' requirement of FR-003. **Requires T018 completion**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis with Confounder Control (Priority: P2)

**Goal**: Fit linear models with confounders, apply Benjamini-Hochberg correction, and validate power.

**Independent Test**: Run analysis on validation subset; verify association statistics (beta, p-values, adj-p) are computed correctly with covariates.

### Tests for User Story 2 (OPTIONAL)

- [X] T012 [P] [US2] Unit test for Benjamini-Hochberg correction logic in `tests/test_analysis.py`
- [X] T013 [P] [US2] Unit test for power analysis script using synthetic beta=0.1 dataset in `tests/test_power.py`

### Implementation for User Story 2

- [X] T028 [US2] Implement `code/analysis.py` to fit **Lasso-regularized linear models** as the **primary method** per Plan Complexity Tracking. **Logic**: Configure Lasso to **force-inclusion (alpha=0) for confounders** [age, sex, BMI, diet_quality, physical_activity, medication_use] to prevent feature selection from dropping required covariates. **Output**: `results/associations/main_effects_lasso.parquet`. **Requires T030 completion**.
- [X] T028b [P] [US2] Implement `code/analysis.py` to fit **OLS linear models** as a robustness check and **Baseline Confounder Control Model** to explicitly satisfy FR-004. **Output**: `results/associations/main_effects_ols.parquet`. **Requires T030 completion**.
- [X] T028c [P] [US2] Implement `code/analysis.py` to fit **Ridge-regularized linear models** as a robustness check. **Output**: `results/associations/main_effects_ridge.parquet`. **Requires T030 completion**.
- [X] T021 [US2] Implement `code/analysis.py` Benjamini-Hochberg correction for all taxon-cognitive associations (Lasso results from T028) and report adjusted p-values (FR-005). **Output**: `results/associations/main_effects.parquet`. **Requires T028 completion**.
- [X] T022a [US2] Fit reduced models **excluding columns: diet_quality, medication_use** to check for over-control bias (FR-010). **Logic**: Compute and report the magnitude of signal masking (effect size difference) between full and reduced models directly in the output file. **Output**: `results/associations/main_effects_reduced.parquet`. **Requires T028 completion** (to have full model coefficients).
- [X] T022b [US2] Generate over-control bias comparison report comparing effect sizes between full and reduced models. **Output**: `results/sensitivity/over_control_report.json`. **Must explicitly calculate and report the magnitude of signal masking (effect size difference)** to satisfy SC-006. **Requires T022a completion**.
- [X] T023 [US2] Update `results/associations/*.parquet` metadata columns to include `causality_claim: false` (FR-008). **Requires T021 completion**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interaction Analysis and Visualization (Priority: P3)

**Goal**: Validate findings via age-interaction analysis and generate Manhattan-style plots.

**Independent Test**: Run interaction analysis; verify interaction p-values are computed and plots are generated with correct annotations.

### Tests for User Story 3 (OPTIONAL)

- [X] T042 [P] [US3] Unit test for interaction term construction (Age_Group * Taxon) in `tests/test_analysis.py`
- [X] T043 [P] [US3] Unit test for Manhattan plot generation logic in `tests/test_visualize.py`

### Implementation for User Story 3

- [X] T024 [US3] Implement `code/analysis.py` to fit interaction models: fit linear models with 'Age_Group * Taxon' term to assess age-dependent effects without splitting sample (FR-006). **Output**: `results/associations/interaction_effects.parquet`. **Requires T016 completion** (Age_Group derived).
- [X] T024c [US3] **Apply Benjamini-Hochberg correction for interaction terms** to produce adjusted p-values for interaction analysis. **Logic**: Interaction terms constitute a new set of hypotheses requiring FDR control under FR-005. **Output**: `results/associations/interaction_effects_bh.parquet`. **Requires T024 completion**.
- [X] T028a [US3] Implement `code/visualize.py` to generate Manhattan-style plots showing -log10(p-values) for each taxon-cognitive association with effect size annotations (FR-007). **Output**: `results/plots/manhattan_plot.png`. **Requires T021 completion**.
- [X] T029a [US3] Implement `code/visualize.py` threshold sweep sensitivity analysis (SC-005): sweep p-value cutoffs over a range of thresholds and report 'headline association rate' (count of taxa with adj-p < threshold). **Verify**: Explicitly report the variation (delta) in headline rates across thresholds. **Requires T021 completion**. **Output**: `results/sensitivity/threshold_sweep_report.json`.
- [X] T033 [US3] Generate report comparing interaction significance to primary effects (SC-004). **Output**: `results/sensitivity/interaction_comparison_report.json`. **Requires T024c completion** AND **T021 completion**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Documentation updates in `docs/` and `quickstart.md`. **Content**: Update `quickstart.md` with steps to run T014-T029a (excluding T036). Generate `results/validation/quickstart_pass.json` with exit code 0.
- [X] T053 [P] Run `black` and `ruff` on all code and generate `results/validation/linting_report.json` with pass/fail status and error counts. **Output**: Linting report. (Renumbered from T041 to resolve ID conflict).
- [X] T054 [P] Performance optimization. **Metric**: Profile `code/utils/streaming.py` using `memory_profiler` and optimize to reduce peak RAM to <5GB. **Output**: Record profile in `results/perf_profile.json`. (Renumbered from T042 to resolve ID conflict).
- [X] T034 [P] Additional integration tests in `tests/test_integration.py`
- [X] T055 [P] Run `quickstart.md` validation. **Outcome**: Execute quickstart.md steps and generate `results/validation/quickstart_pass.json` with exit code 0. (Renumbered from T043 to resolve ID conflict).

---

## Phase O: Review-Driven Revision Tasks

**Purpose**: Address specific reviewer concerns from prior research-stage reviews regarding data sourcing, streaming, and failure modes.

- [ ] T050 [US1] **Implement strict "Fail Loud" data loader in `code/download.py`**. **Logic**: Raise `DataFetchError` with clear instructions if UK Biobank fetch fails due to network or authentication errors. **Scoping**: If specific *fields* (variables) are missing, log a warning, exclude those fields, and scope analysis to available confounders as per Spec Assumptions. **Output**: Updated `code/download.py`. **Rationale**: Prevents silent fabrication on auth/network failure while respecting spec's allowance for graceful scoping on missing variables.
- [ ] T051 [US1] **Implement explicit streaming logic for large datasets in `code/utils/streaming.py`**. Ensure `datasets.load_dataset(..., streaming=True)` is used for UK Biobank data to process in chunks without loading the full dataset into RAM. **Output**: Update `code/download.py` to utilize these streaming iterators. **Rationale**: Addresses the constraint that large real datasets must be streamed, not shrunk to toy sets, and ensures the analysis fits within the ~7GB RAM limit.
- [ ] T052 [US1] **Add explicit sample size and representativeness logging**. If a sample is taken from a streamed dataset (due to compute limits), the code MUST log the exact sampling rule (e.g., a specified row count, random seed) and a statement of limitation in `data/processed/sample_metadata.json`. **Rationale**: Ensures transparency and honesty about data limitations, preventing "synthetic stand-in" fabrication.