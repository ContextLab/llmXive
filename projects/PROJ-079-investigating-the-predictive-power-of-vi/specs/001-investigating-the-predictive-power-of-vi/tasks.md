# Tasks: Predictive Modeling of Host Immune Response from Viral Sequence Features

**Input**: Design documents from `/specs/001-predict-immune-response/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: Directories `data/raw`, `data/processed`, `data/interim`, `data/artifacts`, `src`, `tests`, `artifacts/models`, `artifacts/plots`; Files `requirements.txt`, `README.md`.
- [X] T002 Generate `requirements.txt` with pinned versions of `biopython`, `pandas`, `scikit-learn`, `rpy2`, `statsmodels`, `seaborn`, `matplotlib`, `requests`, `numpy`, `scipy`, `pyyaml`, `tqdm`, `pybedtools`, `python-dotenv`, `pydantic`, `pytest`, `black`, `flake8`.
 - **Optional Dependencies**: `hdi` (for Debiased Lasso, CPU compatible check required), `prody` (for SASA if authorized, currently NOT authorized). Mark as optional in comments.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `src/` (setup.cfg or pyproject.toml).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `src/config.py` defining: `DATA_RAW_PATH='data/raw'`, `DATA_PROCESSED_PATH='data/processed'`, `ARTIFACTS_PATH='data/artifacts'`, `SEED=42`, `MAX_RUNTIME_HOURS=4`, `NCBI_BASE_URL=''`, `GEO_BASE_URL='https://www.ncbi.nlm.nih.gov/geo/download'`.
- [X] T005 Create `src/download.py` with stub functions: `fetch_viral_genomes(accessions: list) -> list`, `fetch_geo_data(accessions: list) -> dict` (raising `NotImplementedError`), and a `main()` entry point logging "Download skeleton initialized".
- [X] T002b [P] **Spec Amendment**: Create `docs/spec_amendments.md` with a section titled **"Protein Stability Proxy Override"**. The text MUST explicitly state: "FR-003 requirement for ESM-1b is overridden by Plan.md Section: Complexity Tracking (Uniform Stability Proxy). The system MUST use a Uniform Stability Proxy (Amino Acid Composition + Hydrophobicity Scales) for ALL samples to ensure CPU feasibility (2-core, 7GB RAM). This methodology is the single source of truth for stability metrics." (Depends on T002).
- [X] T002c [P] **Spec Amendment**: Create `docs/spec_amendments.md` (append) with a section titled **"k-mer Dimensionality Reduction"**. The text MUST explicitly state: "FR-003 requirement for k=3,4,5,6 is overridden by Plan.md Section: Complexity Tracking (Fixed k-mer Order). The system MUST restrict k-mer extraction to k=3 and k=4 ONLY to ensure CPU tractability and Debiased Lasso validity in the HDLSS regime. This is a fixed, a priori selection protocol." (Depends on T002).
- [X] T002e [P] **Documentation Task**: Create `docs/research.md` (or update existing) with a section titled **"k-mer Reduction Justification"**. The text MUST explicitly document the decision to use k=3,4 only, citing Plan.md constraints and the HDLSS problem (N < 100, P > 10,000). This ensures the audit trail matches the implementation before code is written. (Depends on T002c).
- [X] T006a Create `src/download.py` function `generate_manifest_template() -> str` that writes a **JSON** file to `data/manifest_template.json` with keys: "accessions", "source", "timestamp", "version", "checksum_algorithm" (set to "sha256").
- [X] T007 Create `src/models/__init__.py` and `src/models/entities.py` defining Pydantic dataclasses: `ViralGenome` (accession: str, family: str, fasta: str) and `HostExpressionSample` (sample_id: str, counts: dict, metadata: dict, isg_score: float | None).
- [X] T008 Create `src/utils/logging.py` with a configured logger and `src/utils/timeout.py` with a decorator `@timeout(seconds=4*3600)` that raises `TimeoutError`; integrate into `src/main.py`.
- [X] T009 Create `.env.example` with keys: `NCBI_API_KEY`, `GEO_ACCESSIONS`; update `src/config.py` to load these via `python-dotenv`, defaulting to None if missing.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑End Data Acquisition & preprocessing (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean dataset pairing viral genomic features with host immune-response scores.

**Independent Test**: Run the pipeline on a representative subset of viruses and verify that a merged CSV containing all required columns is produced without manual intervention.

### Implementation for User Story 1

- [ ] T012a [US1] Implement `src/download.py` function `fetch_viral_genomes(accessions: list) -> list` that queries NCBI Virus API for genomes. **MUST WRITE FASTA FILES** to `data/raw/` for each accession. (Depends on T005).
- [ ] T012b [US1] Implement `src/download.py` function `fetch_geo_data(accessions: list) -> dict` that downloads GEO series matrix files. **MUST WRITE COUNTS MATRICES** to `data/raw/`. (Depends on T005).
- [ ] T012c [US1] Implement `src/download.py` function `generate_manifest(accessions: list, geo_accessions: list) -> None` that creates a **SINGLE unified `data/manifest.json`** containing:
 - "accessions" (list of all NCBI and GEO IDs)
 - "source" (NCBI Virus / GEO)
 - "timestamp" (ISO8601)
 - "version" (database release versions)
 - "checksums" (SHA-256 of file bytes)
 - **CRITICAL VALIDATION**: Before generating the manifest, check the GEO metadata. **ABORT with fatal error if >10% of initial candidate samples lack a valid `virus_strain_accession` link (FR-014).** **ABORT with fatal error if ortholog mapping fails for >10% of non-human/mouse samples (FR-015).** If these checks pass, generate the manifest. (Depends on T012a, T012b).
- [ ] T015a [US1] Implement `src/preprocess.py` function `map_isg_genes(species: str, gene_list: list) -> list` that uses Ensembl Compara v109 API to map human ISG set to orthologs for non-human species. Return list of Ensembl IDs. Save mapping to `data/processed/ortholog_map.csv`. (Depends on T012a, T012b).
- [ ] T015b [US1] Implement `src/preprocess.py` function `validate_isg_mapping(mappings: list, counts_matrix: pd.DataFrame) -> bool` that verifies mapped orthologs exist in the normalized counts matrix. **CRITICAL VALIDATION**: If overlap < 80%, mark sample as `excluded` (FR-015) and log reason. Return boolean. (Depends on T015a).
- [ ] T014 [US1] Implement `src/preprocess.py` function `normalize_counts(counts_matrix: pd.DataFrame) -> pd.DataFrame` using `rpy2` to call `edgeR::calcNormFactors`, returning a normalized matrix. **Pre-condition: T015b must have validated the gene set.** Save to `data/processed/normalized_counts.csv`. (Depends on T015b).
- [ ] T016 [US1] Implement `src/preprocess.py` function `calculate_isg_score(normalized_counts: pd.DataFrame, isg_genes: list) -> pd.Series` that computes the first principal component (PCA) of the ISG gene columns. **Safety net: Verify ISG gene columns exist in normalized_counts; ABORT with fatal error if ISG set is empty or PCA fails.** Save scores to `data/processed/isg_scores.csv`. (Depends on T014).
- [ ] T017 [US1] Implement `src/preprocess.py` function `filter_samples(merged_df: pd.DataFrame) -> pd.DataFrame` that removes rows with missing strain links and ensures >=30 samples remain. Abort if <30 per FR-013. (Depends on T016).
- [ ] T018a [US1] Implement `src/features.py` function `calculate_cai(fasta_path: str) -> float` calculating Codon Adaptation Index (CAI) using human/mouse codon usage tables. Return float. (Depends on T012a).
- [ ] T018b [US1] Implement `src/features.py` function `calculate_gc_content(fasta_path: str) -> dict` calculating Global and region-specific GC-content. Return dict of floats. (Depends on T012a).
- [ ] T018c [US1] Implement `src/features.py` function `calculate_kmer_frequencies(fasta_path: str) -> dict` calculating k-mer frequencies for **k=3, 4 ONLY** as authorized by `docs/spec_amendments.md` (T002c) and Plan.md. **Mandatory: Restrict k-mer extraction to k=3 and k=4 ONLY as per Plan.md Methodological Adjustments to ensure CPU feasibility and Debiased Lasso validity.** Return dict of floats. (Depends on T012a).
- [ ] T018d [US1] Implement `src/features.py` function `calculate_repeat_density(fasta_path: str) -> float` using `pybedtools` to count repeat-masked bases. Return percentage of genome covered by repeats. (Depends on T012a).
- [ ] T020 [US1] Implement `src/features.py` function `calculate_stability(fasta_path: str) -> dict`. **Mandatory: Implement Uniform Stability Proxy for ALL samples as per `docs/spec_amendments.md` (T002b) and Plan.md.** This MUST include:
 1. **Amino Acid Composition (AAC)**
 2. **Hydrophobicity Scales** (Kyte-Doolittle)
 **Explicitly DO NOT implement SASA, H-bond, Electrostatics, or AlphaFold.** These are excluded to comply with CPU constraints and Plan.md. Return a **dictionary** of these quantitative metrics (floats). (Depends on T012a).
- [ ] T021 [US1] Implement `src/main.py` function `merge_datasets(features_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame` that joins on strain_accession. **Pre-condition: T018a, T018b, T018c, T018d, T020 completed.** (Note: Merge only valid features). Save to `data/processed/merged_dataset.csv`. (Depends on T012c, T018a-d, T020).
- [ ] T022 [US1] Implement `src/main.py` function `aggregate_by_strain(merged_df: pd.DataFrame) -> pd.DataFrame` that groups by strain_accession and averages the `isg_score` column. **Pre-condition: T021 completed. Input: data/processed/merged_dataset.csv.** Save to `data/processed/aggregated_dataset.csv`.
- [ ] T023 [US1] Add validation in `src/main.py`: assert `len(aggregated_df) >= 30` AND `len(aggregated_df['strain_accession'].unique()) >= 5`. Abort with fatal error if false per FR-013, FR-017.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Contract test: Create `tests/contract/test_dataset_schema.py` with function `test_schema_validates(merged_df)` asserting columns match `spec.md` FR-004.
- [ ] T011a [US1] Integration test: Create `tests/integration/test_download_manifest.py` with function `test_download_manifest_generation()` verifying that `fetch_viral_genomes` and `fetch_geo_data` produce a valid **`data/manifest.json`** (exact path) with checksums. **MUST PASS after T012c.** (Depends on T012c).
- [X] T011b [US1] Integration test: Create `tests/integration/test_merge_schema.py` with function `test_merge_schema_validation()` verifying that `merge_datasets` produces `data/processed/merged_dataset.csv` with correct schema. **MUST PASS after T014 and T018.** (Depends on T014, T018).
- [ ] T011c [US1] Unit test: Create `tests/unit/test_stability_proxy.py` with function `test_uniform_stability_proxy_accuracy()` verifying that the AAC and Hydrophobicity calculations match known standards for a test peptide. (Depends on T020).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model training & performance reporting (Priority: P2)

**Goal**: Train a predictive model and obtain clear performance metrics.

**Independent Test**: Execute the modelling step on the full dataset and verify that the reported R², RMSE, and permutation‑test p‑value are logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [US2] Contract test: Create `tests/contract/test_model_output_schema.py` with function `test_model_schema_validates(model_output)` asserting keys match `spec.md` FR-007.
- [X] T025 [US2] Integration test: Create `tests/integration/test_model_training.py` with function `test_training_and_eval()` verifying model training and evaluation produce `data/artifacts/metrics.json`.

### Implementation for User Story 2

- [ ] T025a [US2] Validate total strains: Implement `src/model.py` function `validate_strains(df: pd.DataFrame) -> None`. **Pre-condition: Depends on T022 (Aggregation). Input: data/processed/aggregated_dataset.csv.** Check `len(df['strain_accession'].unique()) >= 5`. **ABORT with fatal error if false** per FR-017. (Depends on T022).
- [ ] T026 [US2] Implement `src/model.py` function `split_stratified_strain(df: pd.DataFrame, test_strains: int=5) -> tuple[DataFrame, DataFrame]`. **Pre-condition: Depends on T025a. Input: data/processed/aggregated_dataset.csv.** Shuffles unique strain IDs using `SEED=42`, assigns a subset to test, rest to train. Ensure no strain overlap. **Assert `len(test_strains_actual) >= 5`. ABORT with fatal error if false.** Save splits to `data/processed/train.csv`, `data/processed/test.csv`. (Depends on T022).
- [ ] T027 [US2] Implement `src/model.py` function `calculate_vif(df: pd.DataFrame) -> dict` that computes VIF for each predictor. Return dict of {feature: vif}. Flag features with VIF > 5. Log warnings. (Depends on T026).
- [ ] T028 [US2] Implement `src/model.py` function `train_elastic_net(X_train: DataFrame, y_train: Series) -> tuple[Model, float, float]` using `sklearn.ElasticNetCV` with k-fold CV. **Use sklearn.model_selection.cross_val_predict with cv=5. Ensure X_test is not passed to fit step.** Verify test data is completely excluded from CV process. Return best model, alpha, lambda. Save model to `data/artifacts/models/elastic_net.pkl`. (Depends on T026).
- [ ] T030 [US2] Implement `src/model.py` function `debiased_lasso_pvalues(model: Model, X_test: DataFrame, y_test: Series) -> dict` that computes p-values for coefficients using **Debiased Lasso (library: hdi)**. **Mandatory: Execute Debiased Lasso for ALL retained predictors.** **Pre-condition: Filter X_test to remove any columns with zero variance BEFORE passing to Debiased Lasso.** If a feature has zero variance, it is NOT "retained" for the purpose of p-value calculation. **ABORT if all predictors are zero-variance.** Save to `data/artifacts/pvalues_exploratory.json`. (Depends on T028, T026).
- [ ] T031 [US2] Implement `src/model.py` function `fdr_correction(pvalues: dict) -> dict` that applies Benjamini-Hochberg correction to p-values. Return dict {feature: adjusted_p_value}. Save to `data/artifacts/fdr_pvalues_exploratory.json`. (Depends on T030).
- [ ] T032a [US2] **Pilot Execution**: Implement `src/model.py` function `run_pilot_permutation(model: Model, X_test: DataFrame, y_test: Series) -> float` that runs a small pilot (e.g., 10 shuffles) to estimate runtime per permutation. (Depends on T028).
- [ ] T032b [US2] **Permutation Loop**: Implement `src/model.py` function `run_full_permutation_test(model: Model, X_test: DataFrame, y_test: Series, n_shuffles: int=1000) -> float`. **Mandatory: Execute exactly 1,000 permutations as per Spec FR-007. For each permutation, re-run PCA on the permuted feature matrix (or permuted labels) to generate the null distribution of R².**
 **Time Estimation Logic**:
 1. Run `run_pilot_permutation` (10 shuffles).
 2. Calculate `estimated_total_time` as a multiple of `pilot_duration`.
 3. **If `estimated_total_time > 3.5 hours` (12600 seconds), ABORT with fatal error. Do NOT reduce the number of permutations.** This ensures statistical rigor is not compromised.
 4. If within limit, proceed with 1,000 permutations.
 Save result to `data/artifacts/permutation_pvalue.json`. (Depends on T032a, T028).
- [ ] T032c [US2] **P-value Aggregation**: Implement `src/model.py` function `aggregate_permutation_pvalue(null_distribution: list, observed_r2: float) -> float` that calculates the empirical p-value. (Depends on T032b).
- [ ] T033 [US2] Implement `src/model.py` function `evaluate_model(model: Model, X_test: DataFrame, y_test: Series) -> dict` that computes R² and RMSE. **Use the Elastic Net model (T028) and Debiased Lasso results (T030).** Return dict {r2: float, rmse: float, primary_method: 'elastic_net_debiased_lasso'}. Save to `data/artifacts/metrics.json`. (Depends on T028, T030).
- [ ] T034 [US2] Implement `src/main.py` function `log_metrics(metrics: dict) -> None` that writes metrics dict to `data/artifacts/metrics.json` with keys: r2, rmse, permutation_pvalue, fdr_min_pvalue.
- [ ] T035 [US2] Add validation in `src/model.py`: assert `len(test_df['strain_accession'].unique()) >= 5`. **ABORT with fatal error if len(test_strains) < 5.** per FR-017.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretation & visualization of predictive features (Priority: P3)

**Goal**: Understand which viral features drive predictions and inspect effect sizes.

**Independent Test**: After model training, request the feature‑importance plot and verify that the top predictors are displayed with partial dependence curves.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T036 [US3] Contract test: Create `tests/contract/test_viz_schema.py` with function `test_viz_schema_validates(plot_files)` asserting files exist and have correct dimensions.
- [ ] T037 [US3] Integration test: Create `tests/integration/test_viz_generation.py` with function `test_viz_generation()` verifying plot generation produces `data/artifacts/plots/coefficients.png` and `data/artifacts/plots/pdp_top5.png`. **Verify files exist and are non-empty.**

### Implementation for User Story 3

- [ ] T038 [US3] Implement `src/viz.py` function `plot_coefficients(model: Model, features: list) -> None` that generates a bar plot of standardized coefficients using `matplotlib`/`seaborn`. **Verify coefficients are standardized (divided by feature std dev) before plotting.** Save to `data/artifacts/plots/coefficients.png`.
- [ ] T039 [US3] Implement `src/viz.py` function `plot_partial_dependence(model: Model, X: DataFrame, features: list, n_points: int=50) -> None` that generates partial dependence plots for top-ranked features. **Define "influential" as top 5 ranked by absolute coefficient magnitude from the Debiased Lasso results.** Save to `data/artifacts/plots/pdp_top5.png`.
- [ ] T040a [US3] Update plot functions `plot_coefficients` and `plot_partial_dependence` in `src/viz.py` to explicitly set `xlabel`, `ylabel`, `title`, and `legend` for every plot generated.
- [ ] T040b [US3] Create `tests/unit/test_viz_labels.py` with function `test_plot_labels()` verifying Axes objects returned by `plot_coefficients` and `plot_partial_dependence` have `xlabel`, `ylabel`, `title`, and `legend` attributes set correctly.
- [ ] T041 [US3] **Structural Feature Visualization**: Implement `src/viz.py` function `plot_structural_importance(features_df: DataFrame, coefficients: dict) -> None` that specifically visualizes the contribution of the **Uniform Stability Proxy features** (AAC, Hydrophobicity) identified in T020. **Mandatory**: Generate a dedicated bar chart comparing the effect sizes of these physical metrics against sequence-based metrics (k-mers, GC). Save to `data/artifacts/plots/structural_importance.png`. (Depends on T020, T030).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Update `README.md` with installation instructions, usage examples, and data requirements. Update `quickstart.md` with a 5-minute run guide. Commit changes.
- [ ] T043a [P] Run `pytest --cov` on `src/` and `tests/`.
- [ ] T043b [P] Verify coverage report exists and indicates >80% line coverage for src/ modules.
- [ ] T044 [P] Profile `src/main.py`. Optimize loops and I/O. Add caching for expensive operations. **Verify total runtime < 4 hours on the 2-core GitHub Actions runner (Plan Target), noting Spec FR-011 assumes 8-core.** This is an **Authorized Environmental Adaptation** per Plan.md. Log timing in `data/artifacts/timing.log`. (Note: Spec FR-011 assumes 8-core, but implementation targets 2-core; this task verifies on the actual target). (Note: Spec FR-011 assumes 8-core, but implementation targets 2-core; this task verifies on the actual target).
- [X] T045 [P] Create `tests/unit/test_edge_cases.py` with tests for: missing genomes, low sample counts, invalid strain links, and stability proxy failure. Ensure all tests pass.
- [ ] T046a1 [P] **Input Validation (Download)**: Add input validation to `src/download.py` function `fetch_all_data`. Check that `accessions` is a non-empty list of strings. Raise `ValueError` if invalid. Add unit test `tests/unit/test_download_validation.py::test_fetch_invalid_inputs`. (Depends on T012a).
- [ ] T046a2 [P] **Input Validation (Download)**: Add input validation to `src/download.py` to check for network errors and non-200 HTTP responses. Raise `ConnectionError` with specific message. Add unit test `tests/unit/test_download_validation.py::test_fetch_network_errors`.
- [ ] T046b1 [P] **Input Validation (Preprocess)**: Add input validation to `src/preprocess.py` function `normalize_counts`. Check that `counts_matrix` is a DataFrame with numeric values. Raise `ValueError` if non-numeric or NaN present. Add unit test `tests/unit/test_preprocess_validation.py::test_normalize_invalid_inputs`.
- [ ] T046b2 [P] **Input Validation (Preprocess)**: Add input validation to `src/preprocess.py` function `map_isg_genes`. Check that `species` is a valid string and `gene_list` is non-empty. Raise `ValueError` if invalid. Add unit test `tests/unit/test_preprocess_validation.py::test_map_invalid_inputs`.
- [ ] T046c1 [P] **Input Validation (Model)**: Add input validation to `src/model.py` function `train_elastic_net`. Check that `X_train` is not empty and `y_train` has non-zero variance. Raise `ValueError` if invalid. Add unit test `tests/unit/test_model_validation.py::test_train_invalid_inputs`.
- [ ] T046c2 [P] **Input Validation (Model)**: Add input validation to `src/model.py` function `debiased_lasso_pvalues`. Check that `X_test` has no zero-variance columns (pre-filtered). Raise `ValueError` if any found. Add unit test `tests/unit/test_model_validation.py::test_debiased_invalid_inputs`.
- [ ] T047 Execute the steps in `quickstart.md` in a fresh virtualenv. Verify that the pipeline runs end-to-end and produces all expected artifacts. Document any failures.

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
- **Compute Constraint**: All tasks must run on a limited number of CPU cores, constrained RAM, and no GPU. **Uniform Stability Proxy is MANDATORY** (T020) as authorized by T002b and Plan.md. ESM-1b is explicitly excluded.
- **Data Constraint**: All dataset URLs must be real and reachable (NCBI, GEO). No synthetic data for primary validation.
- **Methodology Constraint**: Debiased Lasso is MANDATORY for all cases per FR-012. Stability Selection is NOT used.
- **Ordering Constraint**: Aggregation (T022) MUST occur after Merge (T021). Split (T026) depends on Aggregation.
- **Abort Constraint**: Pipeline MUST abort if N < 30, total strains < 5, or test strains < 5.
- **Feature Constraint**: k-mer extraction is restricted to k=3, 4 ONLY as authorized by T002c to ensure CPU feasibility. k=5,6 are removed.
- **Structural Constraint**: T020b removed; Uniform Stability Proxy (AAC + Hydrophobicity) is the only method, authorized by T002b and Plan.md. All structural metrics are computed in T020. SASA, H-bond, Electrostatics are explicitly excluded.
- **Provenance Constraint**: Single `data/manifest.json` generated by T012c.
- **Spec Amendment Constraint**: Deviations from Spec FR-003 (ESM-1b, k=3-6) are formally documented in `docs/spec_amendments.md` (T002b, T002c) and `docs/research.md` (T002e).
- **Statistical Rigor Constraint**: Permutation test (T032b) MUST run exactly 1,000 permutations. If time limit is exceeded, the task ABORTS with a fatal error rather than reducing count, preserving rigor.
- **Validation Constraint**: T012c enforces FR-014 and FR-015 abort conditions during fetch. T030 filters zero-variance features before Debiased Lasso.
- **Review Response Constraint**: T002b, T002c, T020, and T041 explicitly address the requirement for quantitative structural features (AAC + Hydrophobicity) to replace vague "predicted protein structural properties" descriptions, authorized by Plan.md constraints.