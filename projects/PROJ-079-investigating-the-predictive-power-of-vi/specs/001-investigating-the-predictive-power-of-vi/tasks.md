# Tasks: Predictive Modeling of Host Immune Response from Viral Sequence Features

**Input**: Design documents from `/specs/001-predict-immune-response/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [ ] T001 Create project structure: Directories `code/data/raw`, `code/data/processed`, `code/src`, `code/tests`, `artifacts/models`, `artifacts/plots`; Files `code/requirements.txt`, `code/README.md`.
- [ ] T002 Generate `code/requirements.txt` with pinned versions of `biopython`, `pandas`, `scikit-learn`, `rpy2`, `statsmodels`, `seaborn`, `matplotlib`, `requests`, `numpy`, `scipy`, `pyyaml`, `tqdm`, `pybedtools`, `python-dotenv`, `pydantic`, `pytest`, `black`, `flake8`.
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `code/` (setup.cfg or pyproject.toml).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/src/config.py` defining: `DATA_RAW_PATH='data/raw'`, `DATA_PROCESSED_PATH='data/processed'`, `ARTIFACTS_PATH='artifacts'`, `SEED=42`, `MAX_RUNTIME_HOURS=4`, `NCBI_BASE_URL='https://www.ncbi.nlm.nih.gov/nuccore'`, `GEO_BASE_URL=''`.
- [ ] T005 Create `code/src/download.py` with stub functions: `fetch_viral_genomes(accessions: list) -> list`, `fetch_geo_data(accessions: list) -> dict` (raising `NotImplementedError`), and a `main()` entry point logging "Download skeleton initialized".
- [ ] T006 Implement `code/src/download.py` function `generate_manifest(accessions: list, version: str) -> str` that writes a YAML file to `data/manifest.yaml` with keys: "accessions", "source", "timestamp" (ISO8601), "version".
- [ ] T007 Create `code/src/models/__init__.py` and `code/src/models/entities.py` defining Pydantic dataclasses: `ViralGenome` (accession: str, family: str, fasta: str) and `HostExpressionSample` (sample_id: str, counts: dict, metadata: dict, isg_score: float | None).
- [ ] T008 Create `code/src/utils/logging.py` with a configured logger and `code/src/utils/timeout.py` with a decorator `@timeout(seconds=4*3600)` that raises `TimeoutError`; integrate into `code/src/main.py`.
- [ ] T009 Create `code/.env.example` with keys: `NCBI_API_KEY`, `GEO_ACCESSIONS`; update `code/src/config.py` to load these via `python-dotenv`, defaulting to None if missing.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑End Data Acquisition & preprocessing (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean dataset pairing viral genomic features with host immune-response scores.

**Independent Test**: Run the pipeline on a representative subset of viruses and verify that a merged CSV containing all required columns is produced without manual intervention.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [US1] Contract test: Create `tests/contract/test_dataset_schema.py` with function `test_schema_validates(merged_df)` asserting columns match `spec.md` FR-004.
- [ ] T011 [US1] Integration test: Create `tests/integration/test_data_pipeline.py` with function `test_e2e_download_merge()` verifying end-to-end download and merge produces `data/processed/merged_dataset.csv`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/src/download.py` function `fetch_viral_genomes(accessions: list) -> list[dict]` that queries NCBI Virus API, parses FASTA, returns list of dicts with keys: "accession", "sequence", "family". Log warnings for missing accessions per FR-013.
- [ ] T013 [US1] Implement `code/src/download.py` function `fetch_geo_data(accessions: list) -> dict` that downloads GEO series matrix files, parses "virus_strain_accession" metadata column, returns dict mapping sample_id to strain_accession. Abort if >10% missing per FR-014.
- [ ] T014 [US1] Implement `code/src/preprocess.py` function `normalize_counts(counts_matrix: pd.DataFrame) -> pd.DataFrame` using `rpy2` to call `edgeR::calcNormFactors`, returning a normalized matrix. Save to `data/processed/normalized_counts.csv`.
- [ ] T015 [US1] Implement `code/src/preprocess.py` function `map_isg_genes(species: str, gene_list: list) -> list` that uses Ensembl Compara v109 API to map human ISG set to orthologs for non-human species. Return mapped gene list or raise error if mapping fails.
- [ ] T016 [US1] Implement `code/src/preprocess.py` function `calculate_isg_score(normalized_counts: pd.DataFrame, isg_genes: list) -> pd.Series` that computes the first principal component (PCA) of the ISG gene columns. Save scores to `data/processed/isg_scores.csv`.
- [ ] T017 [US1] Implement `code/src/preprocess.py` function `filter_samples(merged_df: pd.DataFrame) -> pd.DataFrame` that removes rows with missing strain links and ensures >=30 samples remain. Abort if <30 per FR-013.
- [ ] T018 [US1] Implement `code/src/features.py` function `extract_sequence_features(fasta_path: str) -> dict` calculating: CAI (using codon usage table), GC_content (global and 3-region), kmer_freqs (k=3,4,5,6). Return dict of floats.
- [ ] T019 [US1] Implement `code/src/features.py` function `calculate_repeat_density(fasta_path: str) -> float` using `pybedtools` to count repeat-masked bases. Return percentage of genome covered by repeats.
- [ ] T020 [US1] Implement `code/src/features.py` function `calculate_stability(fasta_path: str, proxy_mode: bool) -> float`. If `proxy_mode` is False, use ESM-1b v1.1; if True, use AAIndex. **Abort if ESM-1b fails and `proxy_mode` is not set.** Log warning if proxy is used.
- [ ] T021 [US1] Implement `code/src/main.py` function `merge_datasets(features_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame` that joins on strain_accession. Save to `data/processed/merged_dataset.csv`.
- [ ] T022 [US1] Implement `code/src/main.py` function `aggregate_by_strain(merged_df: pd.DataFrame) -> pd.DataFrame` that groups by strain_accession and averages the `isg_score` column. Save to `data/processed/aggregated_dataset.csv`.
- [ ] T023 [US1] Add validation in `code/src/main.py`: assert `len(aggregated_df) >= 30` AND `len(aggregated_df['strain_accession'].unique()) >= 5`. Abort with fatal error if false per FR-013, FR-017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model training & performance reporting (Priority: P2)

**Goal**: Train a predictive model and obtain clear performance metrics.

**Independent Test**: Execute the modelling step on the full dataset and verify that the reported R², RMSE, and permutation‑test p‑value are logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [US2] Contract test: Create `tests/contract/test_model_output_schema.py` with function `test_model_schema_validates(model_output)` asserting keys match `spec.md` FR-007.
- [ ] T025 [US2] Integration test: Create `tests/integration/test_model_training.py` with function `test_training_and_eval()` verifying model training and evaluation produce `artifacts/metrics.json`.

### Implementation for User Story 2

- [ ] T026 [US2] Implement `code/src/model.py` function `split_stratified_strain(df: pd.DataFrame, test_strains: int=5) -> tuple[DataFrame, DataFrame]` that shuffles unique strain IDs, assigns a subset to test, rest to train. Ensure no strain overlap. Save splits to `data/processed/train.csv`, `data/processed/test.csv`. (Depends on T021).
- [ ] T027 [US2] Implement `code/src/model.py` function `calculate_vif(df: pd.DataFrame) -> dict` that computes VIF for each predictor. Return dict of {feature: vif}. Flag features with VIF > 5. Log warnings. (Depends on T026).
- [ ] T028 [US2] Implement `code/src/model.py` function `train_elastic_net(X_train: DataFrame, y_train: Series) -> tuple[Model, float, float]` using `sklearn.ElasticNetCV` with 5-fold CV. Return best model, alpha, lambda. Save model to `artifacts/models/elastic_net.pkl`. (Depends on T026).
- [ ] T030 [US2] Implement `code/src/model.py` function `debiased_lasso_pvalues(model: Model, X_test: DataFrame) -> dict` that computes p-values for coefficients using Debiased Lasso (primary method per FR-012). Return dict {feature: p_value}. Save to `artifacts/pvalues.json`. (Depends on T028).
- [ ] T031 [US2] Implement `code/src/model.py` function `fdr_correction(pvalues: dict) -> dict` that applies Benjamini-Hochberg correction to p-values. Return dict {feature: adjusted_p_value}. Save to `artifacts/fdr_pvalues.json`. (Depends on T030).
- [ ] T032 [US2] Implement `code/src/model.py` function `permutation_test(model: Model, X_test: DataFrame, y_test: Series, n_shuffles: int=1000) -> float` that shuffles y_test repeatedly, retrains model, and calculates empirical p-value. Save result to `artifacts/permutation_pvalue.json`. (Depends on T028).
- [ ] T033 [US2] Implement `code/src/model.py` function `evaluate_model(model: Model, X_test: DataFrame, y_test: Series) -> dict` that computes R² and RMSE. Return dict {r2: float, rmse: float}. Save to `artifacts/metrics.json`. (Depends on T028).
- [ ] T034 [US2] Implement `code/src/main.py` function `log_metrics(metrics: dict) -> None` that writes metrics dict to `artifacts/metrics.json` with keys: r2, rmse, permutation_pvalue, fdr_min_pvalue.
- [ ] T035 [US2] Add validation in `code/src/model.py`: assert `len(test_df['strain_accession'].unique()) >= 5`. Abort with fatal error if false per FR-017.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretation & visualization of predictive features (Priority: P3)

**Goal**: Understand which viral features drive predictions and inspect effect sizes.

**Independent Test**: After model training, request the feature‑importance plot and verify that the top predictors are displayed with partial dependence curves.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T036 [US3] Contract test: Create `tests/contract/test_viz_schema.py` with function `test_viz_schema_validates(plot_files)` asserting files exist and have correct dimensions.
- [ ] T037 [US3] Integration test: Create `tests/integration/test_viz_generation.py` with function `test_viz_generation()` verifying plot generation produces `artifacts/plots/coefficients.png` and `artifacts/plots/pdp_top5.png`.

### Implementation for User Story 3

- [ ] T038 [US3] Implement `code/src/viz.py` function `plot_coefficients(model: Model, features: list) -> None` that generates a bar plot of standardized coefficients using `matplotlib`/`seaborn`. Save to `artifacts/plots/coefficients.png`.
- [ ] T039 [US3] Implement `code/src/viz.py` function `plot_partial_dependence(model: Model, X: DataFrame, features: list, n_points: int=50) -> None` that generates partial dependence plots for top-ranked features. Save to `artifacts/plots/pdp_top5.png`.
- [ ] T040 [US3] Add code to all viz functions in `code/src/viz.py` to set `xlabel`, `ylabel`, `title`, and `legend` for every plot generated. Verify via unit test that plot objects have these attributes.
- [ ] T041 [US3] Ensure all viz functions in `code/src/viz.py` save output files to `artifacts/plots/` with specific filenames: `coefficients.png`, `pdp_top5.png`. Verify file existence in unit tests.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Update `code/README.md` with installation instructions, usage examples, and data requirements. Update `code/quickstart.md` with a 5-minute run guide. Commit changes.
- [ ] T043 Run `black` and `flake8` on `code/src/` and `code/tests/`. Fix all formatting and linting errors. Ensure [deferred] line coverage for core logic in unit tests.
- [ ] T044 Profile `code/src/main.py`. Optimize loops and I/O. Add caching for expensive operations. Verify total runtime < 4 hours on a 2-core CPU environment. Log timing in `artifacts/timing.log`.
- [ ] T045 [P] Create `code/tests/unit/test_edge_cases.py` with tests for: missing genomes, low sample counts, invalid strain links, and ESM-1b failure. Ensure all tests pass.
- [ ] T046 Add input validation to all public functions in `code/src/` to check for nulls, invalid types, and out-of-range values. Raise `ValueError` for invalid inputs. Add unit tests for validation.
- [ ] T047 Execute the steps in `code/quickstart.md` in a fresh virtualenv. Verify that the pipeline runs end-to-end and produces all expected artifacts. Document any failures.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (merged data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US2 (trained model)

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for end-to-end download and merge in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/download.py to fetch viral genomes from NCBI Virus using real URLs"
Task: "Implement src/download.py to fetch GEO transcriptomic data and validate metadata"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Compute Constraint**: All tasks must run on 2 CPU cores, 7GB RAM, no GPU. Use CPU-only fallbacks for ESM-1b (AAIndex) ONLY if `--proxy_mode` is set.
- **Data Constraint**: All dataset URLs must be real and reachable (NCBI, GEO). No synthetic data for primary validation.
- **Methodology Constraint**: Debiased Lasso is the primary method for p-values (FR-012). Stability Selection is NOT included as it contradicts the Spec.