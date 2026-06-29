# Tasks: Bayesian Hierarchical Modeling of Misinformation Cascade Size

**Input**: Design documents from `/specs/001-bayesian-misinformation-cascade/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are **mandatory**.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure:
 - `code/`, `data/`, `results/`, `tests/`, `contracts/`, `docs/`
 - Add placeholder `README.md` and `.gitignore`
- [X] T004 Create `requirements.txt` with pinned versions:
 ```
 numpy==1.26.4
 pandas==2.2.1
 numpyro==0.13.2
 cmdstanpy==1.2.0
 networkx==3.2
 scikit-learn==1.4.0
 pyyaml==6.0.1
 jsonschema==4.20.0
 pytest==8.0.0
 ruff==0.3.0
 black==24.2.0
 ```
- [X] T002 Initialize Python project (create `pyproject.toml`/virtualenv) and install dependencies from `requirements.txt`.
- [X] T003 Configure linting (ruff) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `run_pipeline.sh` skeleton:
 - Set `OMP_NUM_THREADS=2`
 - Add memory‑monitoring hook (abort if RAM > 7 GB)
 - Include placeholder sections for each pipeline stage and logging to `pipeline.log`.
- [X] T006 Create `code/pipeline/utils.py` with:
 - Logging infrastructure (`setup_logger()`)
 - Random‑seed initialization function (`set_global_seed(seed)`)
 - Helper for SHA‑256 checksum calculation (`compute_checksum(path)`).
- [X] T007 Create `data-model.md` specifying schemas for `Cascade`, `FeatureSet`, `ModelOutput`.
- [X] T008 Create `contracts/` JSON schemas for:
 - `features.csv`
 - `model_trace.nc`
 - `posterior_summary.csv`
 - `cv_metrics.json`
 - `collinearity_report.txt`
- [X] T009 Create `quickstart.md` with pipeline execution instructions and a reference to `model_spec.yaml`.
- [X] T010 Add node‑limit validation task: cascades with > 2,000 nodes are logged to `skipped_cascades.log` and skipped.
- [X] T060 [P] Add explicit random‑seed pinning in all code modules (call `set_global_seed(12345)` at script start).
- [X] T061 [P] Compute SHA‑256 checksums for every file in `data/raw/`, write to `data/checksums.txt`.
- [X] T062 [P] Implement proxy susceptibility score with formula `(historical_degree >= 2 AND historical_shares >= 1) ? 1.0: 0.0` per FR‑003 Clarification; document formula in `susceptibility_method.md`.
- [X] T064 [P] Run citation verification using `python code/pipeline/verify_citations.py` which checks each markdown file for reachable URLs and title-token-overlap ≥ 0.7. Exit non-zero on any failure.
- [X] T065 Align `FeatureSet` definition in `data-model.md` with the JSON schema in `contracts/`; add validation step in the pipeline.
- [X] T066 [P] Add a reference to `model_spec.yaml` in `quickstart.md` and `README.md` (Constitution Principle VI).
- [X] T084 Create `data/raw/` directory with sample JSON cascade file for schema validation testing.

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 – End‑to‑end Modeling Pipeline (Priority: P1) 🎯 MVP

**Goal**: Reproducible end‑to‑end pipeline that ingests raw cascade data, generates features, fits a Bayesian hierarchical model, and outputs posterior summaries.

**Independent Test**: Execute `run_pipeline.sh --data data/raw/ --out results/` on the benchmark dataset and verify that `features.csv`, `model_trace.nc`, and `posterior_summary.csv` exist with no missing values and pass schema tests.

### Contract Tests (mandatory)

- [X] T011 [P] [US1] Contract test for JSON cascade schema validation in `tests/contract/test_cascade_schema.py`.
- [X] T012 [P] [US1] Contract test for `features.csv` schema in `tests/contract/test_features_schema.py`.
- [X] T013 [P] [US1] Contract test for `posterior_summary.csv` schema in `tests/contract/test_posterior_schema.py`.
- [X] T070 [P] [US1] Contract test verifying timestamps are normalized to UTC.
- [X] T071 [P] [US1] Contract test confirming that cascades exceeding the node limit are logged in `skipped_cascades.log`.
- [X] T072 [P] [US1] Contract test ensuring `posterior_summary.csv` contains required columns:
 `predictor, mean, sd, lower_95, upper_95, prob_nonzero, direction_consistent`.

### Implementation

- [X] T019 [P] [US1] Create `model_spec.yaml` specifying priors, hyper‑parameters, and platform‑random‑effect logic.
- [X] T018 [P] [US1] Create `hierarchical_model.py` defining a Bayesian hierarchical model with:
 - Negative‑Binomial likelihood for cascade size
 - Fixed effects for all network and user predictors
 - Random intercepts for `user_id`, `message_id`, and optional `platform_id` (if ≥ 2 platforms).
- [X] T080 [P] [US1] Extend `load_cascade()` in `code/pipeline/utils.py` to accept **JSON edge‑list** files only, validate required columns (`node_id`, `timestamp`, `cascade_id`), normalize timestamps to UTC, and log validation errors.
- [ ] T014 [P] [US1] Within `load_cascade`, enforce the [deferred]‑node limit; skip oversized cascades and log IDs to `skipped_cascades.log`.
- [ ] T015 [P] [US1] Implement `network_features.py` to compute:
 - Degree distribution moments
 - Clustering coefficient
 - Betweenness centrality (mean)
 - All computed from **pre-cascade historical network context** (NOT cascade graph to avoid circularity).
 Output intermediate CSV `intermediate_network_features.csv`.
- [ ] T016 [P] [US1] Implement `user_susceptibility.py` to compute the susceptibility score using historical sharing frequency with formula `(historical_degree >= 2 AND historical_shares >= 1) ? 1.0: 0.0`; fallback to proxy as documented in `susceptibility_method.md`.
- [ ] T017 [P] [US1] Create `generate_synthetic.py` to synthesize a small benchmark dataset for testing. Dataset MUST include: cascade_id, node_id, timestamp, cascade_label, historical_degree, historical_shares, user_id, message_id, platform_id. Define 'small' as ≤50 cascades with ≤2,000 nodes each. Use formula `(historical_degree >= 2 AND historical_shares >= 1) ? 1.0: 0.0` for susceptibility.
- [ ] T082 [P] [US1] Add docstrings to all feature‑engineering scripts (`network_features.py`, `user_susceptibility.py`) that record input sources, transformation steps, and output files.
- [ ] T083 [P] [US1] Generate `manifest.json` containing software versions, random seeds, and data hashes (including checksums from T061).
- [ ] T067 [P] [US1] Ensure each feature‑engineering script logs its input file paths, transformation parameters, and output file paths to `pipeline.log` (Constitution Principle VII).
- [ ] T020 [P] [US1] Implement HMC/NUTS sampling in `hierarchical_model.py`:
 - Monitor divergent transitions (> 5 %)
 - Auto‑reduce step size and retry up to 3 times
 - Abort with diagnostic report if convergence still fails.
- [ ] T021a [P] [US1] Implement data loading stage in `run_pipeline.sh`: call `load_cascade()` for all JSON files in `data/raw/`, validate schema, normalize timestamps, and write validated cascades to `data/processed/validated_cascades.json`.
- [ ] T021b [P] [US1] Implement feature extraction stage in `run_pipeline.sh`: call `network_features.py` and `user_susceptibility.py`, aggregate outputs into `results/features.csv`, and log to `pipeline.log`.
- [ ] T021c [P] [US1] Implement model fitting stage in `run_pipeline.sh`: call `hierarchical_model.py` with `features.csv` as input, run HMC/NUTS sampling, and write posterior trace to `results/model_trace.nc`.
- [ ] T021d [P] [US1] Implement output generation stage in `run_pipeline.sh`: compute posterior summaries from `model_trace.nc`, write `results/posterior_summary.csv`, and verify all output files exist with no missing values.
- [ ] T022 [P] [US1] Ensure `features.csv` contains **all** predictors with no missing values.
- [ ] T023 [P] [US1] Ensure `model_trace.nc` stores posterior samples in NetCDF format.
- [ ] T024 [P] [US1] Ensure `posterior_summary.csv` includes:
 - `predictor`
 - `mean`
 - `sd`
 - `lower_95`
 - `upper_95`
 - `prob_nonzero` (posterior probability of non‑zero effect)
 - `direction_consistent` (TRUE if effect sign matches across folds, per SC‑001).
- [ ] T026 [P] [US1] Log all major steps to `pipeline.log` (already provided by utils).

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 – Predictive Performance Evaluation (Priority: P2)

**Goal**: Assess model predictive performance with leave-one-user-out cross-validation and calibrated prediction intervals.

**Independent Test**: Run the CV script and verify `cv_metrics.json` reports WAIC, LOO‑CV, and coverage rates that match nominal interval levels.

### Contract Tests (mandatory)

- [ ] T028 [P] [US2] Contract test for `cv_metrics.json` schema in `tests/contract/test_cv_metrics_schema.py`.

### Implementation

- [ ] T081 [P] [US2] Implement **leave-one-user-out cross-validation (LOUOCV)** in `hierarchical_model.py`; compute WAIC and LOO‑CV for the hierarchical model. Each fold holds out one unique user's cascades for validation.
- [ ] T029 [P] [US2] Fit a baseline linear regression model on the same features; compute its WAIC for comparison (SC‑003).
- [ ] T030 [P] [US2] Compute posterior predictive interval coverage statistics for each fold and aggregate into `cv_metrics.json`.
- [ ] T031 [P] [US2] Verify that at least three predictors have `prob_nonzero > 0.95` **and** `direction_consistent == TRUE` across folds (SC‑001).
- [ ] T032 [P] [US2] Generate calibration plots (`diagnostics.py`) showing interval coverage vs nominal levels; include in `results/` directory.

**Checkpoint**: User Stories 1 & 2 should now both work independently.

---

## Phase 5: User Story 3 – Collinearity Diagnostics & Reporting (Priority: P3)

**Goal**: Automated report flagging high collinearity among predictors with VIFs and recommendations.

**Independent Test**: Run `diagnostics.sh` and verify `collinearity_report.txt` lists every predictor pair with |r| > 0.8 together with its VIF, and includes a recommendation.

### Contract Tests (mandatory)

- [ ] T074 [P] [US3] Contract test for `collinearity_report.txt` format in `tests/contract/test_collinearity_report.py`.

### Implementation

- [ ] T039 [P] [US3] Compute pairwise Pearson correlations for all predictors in `network_features.py`.
- [ ] T040 [P] [US3] Compute Variance Inflation Factors (VIF) for all predictors.
- [ ] T041 [P] [US3] Flag any predictor pair with |r| > 0.8 in `collinearity_report.txt` and include VIF values.
- [ ] T042 [P] [US3] Implement `diagnostics.sh` to generate `collinearity_report.txt` with recommendations (drop/combine).
- [ ] T043 [P] [US3] Verify that no predictor pair exceeds |r| > 0.8 without being flagged (SC‑005).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T054 [P] Documentation updates: refresh `quickstart.md`, `README.md`, and add a reference to `model_spec.yaml` (covers Constitution Principle VI).
- [ ] T055 Code cleanup and refactoring for all pipeline modules: Refactor all code to meet ruff linting rules (`ruff check code/ --exit-zero`) and black formatting (`black --check code/`). Fix all violations.
- [ ] T056 Performance optimization: Add memory profiling with tracemalloc to each pipeline stage. Log peak RSS to pipeline.log. Verify peak ≤ 7 GB using `psutil` in utils.py.
- [ ] T057 [P] Add pre‑commit hooks for linting (`ruff`), formatting (`black`), and schema validation.
- [ ] T058 [P] Run quickstart.md validation to verify end-to-end documentation accuracy: Execute quickstart.md instructions in a fresh virtualenv. Verify pipeline completes successfully and produces all expected outputs. Document any errors in quickstart_validation.log.
- [ ] T063 [P] Add docstrings to all feature‑engineering scripts (`network_features.py`, `user_susceptibility.py`, etc.) that record input sources, transformation steps, and output files.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 – BLOCKS all user stories.
- **User Stories (Phases 3‑5)**: All depend on Phase 2; can run in parallel once Phase 2 is complete.
- **Polish (Phase 6)**: Depends on completion of desired user stories.

### Within Each User Story

- Tests (mandatory) must be written **before** implementation and must initially fail.
- Model code precedes evaluation scripts.
- Reporting scripts run after model fitting.
- Each story must be fully functional before moving to the next priority, unless parallel resources are available.

### Parallel Opportunities

- All `[P]` tasks within a phase can be executed concurrently if they touch distinct files.
- Different user stories can be developed by separate team members once Phase 2 is complete.

---

## Parallel Example: User Story 1

```bash
# Launch all contract tests for User Story 1 together:
Task: "Contract test for JSON cascade schema validation in tests/contract/test_cascade_schema.py"
Task: "Contract test for features.csv schema in tests/contract/test_features_schema.py"
Task: "Contract test for posterior_summary.csv schema in tests/contract/test_posterior_schema.py"
Task: "Contract test for timestamp normalization in tests/contract/test_timestamp_normalization.py"
Task: "Contract test for node‑limit logging in tests/contract/test_node_limit.py"
Task: "Contract test for posterior_summary column completeness in tests/contract/test_posterior_columns.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Run all contract tests for US 1.
5. Deploy/demo if ready.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add User Story 1 → test → demo (MVP!).
3. Add User Story 2 → test → demo.
4. Add User Story 3 → test → demo.
5. Polish → final release.

### Parallel Team Strategy

- Team finishes Setup + Foundational together.
- Once ready:
 - Dev A: User Story 1
 - Dev B: User Story 2
 - Dev C: User Story 3
 - Dev D: Polish & cross‑cutting tasks

---

## Notes

- All tasks are designed to run on **CPU‑only** CI (2 cores, ≤ 7 GB RAM, ≤ 6 h).
- Node‑limit is **[deferred] nodes** per plan for CPU feasibility (reduced from spec's [deferred]).
- Feature engineering scripts record provenance and transformations.
- Random seeds are pinned in **code**, not only in the wrapper script.
- Data integrity is ensured via checksums and a reproducibility manifest.
- The pipeline aborts with clear error messages for missing columns, oversized cascades, or sampling divergence.
- No GPU‑only libraries or large‑scale models are used; the Bayesian inference relies on NumPyro's CPU‑compatible NUTS sampler.
- **CASCADE DEPTH REMOVED**: Per plan Phase 2, cascade depth is not computed to avoid circular validation with outcome variable. Pre-cascade network context is used instead.
- **LOUOCV REQUIRED**: Per plan Phase 3, leave-one-user-out CV is used instead of k-fold to prevent information leakage in hierarchical data.
- **JSON ONLY**: Per plan Phase 1, only JSON edge-list format is accepted for topology data.
- **Message content features removed**: Per Phase 7 scope decision, sentiment/readability features are out-of-scope.
- **Synthetic dataset definition**: T017 defines 'small' as ≤50 cascades with ≤2,000 nodes each, with explicit schema requirements.
- **Pipeline stages granularized**: T021 split into T021a-T021d for clear stage-by-stage orchestration.