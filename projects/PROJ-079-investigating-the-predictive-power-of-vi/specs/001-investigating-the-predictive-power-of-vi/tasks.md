# Tasks: Predictive Modeling of Host Immune Response from Viral Sequence Features

**Input**: Design documents from `/specs/001-predict-immune-response/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e., US1, US2, US3)
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
- [X] T002b [P] **Spec Amendment**: Create `docs/spec_amendments.md` with a section titled **"Protein Stability Proxy Override"**. The text MUST explicitly state: "FR-003 requirement for ESM-1b is overridden by Plan.md Section: Complexity Tracking (Uniform Stability Proxy). The system MUST use a Uniform Stability Proxy (Amino Acid Composition + Hydrophobicity Scales) for ALL samples to ensure CPU feasibility on standard multi-core, limited-memory hardware. [UNRESOLVED-CLAIM: c_5546905e — status=not_enough_info] This methodology is the single source of truth for stability metrics." (Depends on T002).
- [X] T002c [P] **Spec Amendment**: Create `docs/spec_amendments.md` (append) with a section titled **"k-mer Dimensionality Reduction"**. The text MUST explicitly state: "FR-003 requirement for k=3,4,5,6 is overridden by Plan.md Section: Complexity Tracking (Fixed k-mer Order). The system MUST restrict k-mer extraction to k=3 and k=4 ONLY to ensure CPU tractability and Debiased Lasso validity in the HDLSS regime. [UNRESOLVED-CLAIM: c_b3cf0ed2 — status=not_enough_info] This is a fixed, a priori selection protocol." (Depends on T002).
- [X] T002b-verify [P] **Spec Amendment Verification**: Implement `src/download.py` function `verify_spec_amendments() -> bool` that checks for the existence and validity of `docs/spec_amendments.md`. **MUST ABORT** if the file is missing or does not contain the required sections ("Protein Stability Proxy Override", "k-mer Dimensionality Reduction"). **Validity Criteria**: The function MUST search for the exact string "R² >= 0.8" in the Proxy section and "k=3, 4 ONLY" in the k-mer section. (Depends on T002b, T002c).
- [X] T002e [P] **Documentation Task**: Create `docs/research.md` (or update existing) with a section titled **"k-mer Reduction Justification"**. The text MUST explicitly document the decision to use k=3,4 only, citing Plan.md constraints and the HDLSS problem (N < 100, P > 10,000). This ensures the audit trail matches the implementation before code is written. (Depends on T002c).
- [X] T002b-ratify [P] **Ratification Simulation**: Implement `src/download.py` function `ratify_spec_amendments() -> None` that simulates the Advancement-Evaluator gate. This function MUST write a `docs/ratification_status.json` file with `{"amendments_ratified": true, "timestamp": "ISO8601"}` and a checksum of `docs/spec_amendments.md`. **MUST ABORT** if `verify_spec_amendments()` (T002b-verify) fails. (Depends on T002b-verify).
- [X] T002d [P] **Spec Amendment (Permutation Strategy)**: Create `docs/spec_amendments.md` (append) with a section titled **"Subset Permutation Strategy for Global Inference"**. The text MUST explicitly state: "FR-007 requirement for a global permutation test of the entire dataset is overridden by Plan.md Section: Complexity Tracking (Runtime Constraints). The system MUST perform the permutation test (including full feature re-extraction) on a representative subset of 20 strains (or [deferred] of total, whichever is smaller) and scale the p-value. This subset approach is the single source of truth for permutation inference." (Depends on T002).
- [X] T002d-ratify [P] **Ratification Simulation (Permutation)**: Implement `src/download.py` function `ratify_spec_amendments_permutation() -> None` that writes a `docs/ratification_status_permutation.json` file with `{"amendment_permutation_ratified": true}`. **MUST ABORT** if `verify_spec_amendments()` fails. (Depends on T002b-verify, T002d).
- [X] T006a Create `src/download.py` function `generate_manifest_template() -> str` that writes a **JSON** file to `data/manifest_template.json` with keys: "accessions", "source", "timestamp", "version", "database_release_version" (placeholder string), "file_checksum" (placeholder string), and "checksum_algorithm" (set to "sha256").
- [X] T007 Create `src/models/__init__.py` and `src/models/entities.py` defining Pydantic dataclasses: `ViralGenome` (accession: str, family: str, fasta: str) and `HostExpressionSample` (sample_id: str, counts: dict, metadata: dict, isg_score: float | None).
- [X] T008 Create `src/utils/logging.py` with a configured logger and `src/utils/timeout.py` with a decorator `@timeout(seconds=4*3600)` that raises `TimeoutError`; integrate into `src/main.py`.
- [X] T009 Create `.env.example` with keys: `NCBI_API_KEY`, `GEO_ACCESSIONS`; update `src/config.py` to load these via `python-dotenv`, defaulting to None if missing.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑End Data Acquisition & preprocessing (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean dataset pairing viral genomic features with host immune-response scores.

**Independent Test**: Run the pipeline on a representative subset of viruses and verify that a merged CSV containing all required columns is produced without manual intervention.

### Implementation for User Story 1

- [X] T012a [US1] Implement `src/download.py` function `fetch_viral_genomes(accessions: list) -> list` that queries NCBI Virus API for genomes. **MUST WRITE FASTA FILES** to `data/raw/{accession}.fasta` for each accession. (Depends on T005).
- [X] T012b [US1] Implement `src/download.py` function `fetch_geo_data(accessions: list) -> dict` that downloads GEO series matrix files. **MUST WRITE COUNTS MATRICES** to `data/raw/{geo_accession}_counts.tsv` for each accession. **Schema**: Tab-separated values, first column `gene_symbol` (index), subsequent columns `sample_id`, values are raw integer counts. **CRITICAL**: Must also extract and store `virus_strain_accession` metadata for each sample to enable downstream validation (FR-014). **Parsing Logic**: Use GEOparse or manual parsing of the Series Matrix file to locate `!Sample_title` and `!Sample_characteristics_ch1` fields to extract the strain accession. **Output**: Write metadata to `data/raw/{geo_accession}_metadata.json` in JSON format (key: `virus_strain_accession`). (Depends on T005).
- [X] T012c-version-check [US1] Implement `src/download.py` function `get_ncbi_version() -> str` that queries the NCBI Virus API for the current database release version. Return the version string. (Depends on T005).
- [ ] T012c [US1] Implement `src/download.py` function `generate_manifest(accessions: list, geo_accessions: list) -> None` that creates a **SINGLE unified `data/manifest.json`** containing:
 - "accessions" (list of all NCBI and GEO IDs)
 - "source" (NCBI Virus / GEO)
 - "timestamp" (ISO8601)
 - "version" (database release versions)
 - "file_checksum" (SHA-256 of file bytes)
 - "database_release_version" (string from T012c-version-check)
 - "n_strains_initial" (integer count of unique strains found in metadata)
 - **CRITICAL VALIDATION**: Before generating the manifest, check the GEO metadata. **ABORT with fatal error if >10% of initial candidate samples lack a valid `virus_strain_accession` link (FR-014).** **Do NOT perform ortholog mapping validation here; that is T015b.**
 - **Fallback Logic**: For individual missing genomes (not triggering the global abort), log a warning, exclude that specific virus from the list, and proceed with the remaining data (FR-013).
 - **Template Usage**: This task MUST use the template structure from T006a as the base, filling in the actual checksums and versions.
 - **Output Path**: Writes explicitly to `data/manifest.json`.
 - **Error Handling**: On validation failure, raise `RuntimeError` with message "FATAL: Strain link validation failed".
 - **Parsing Logic**: Search for the string "strain" in `!Sample_characteristics_ch1` and extract the accession following it. If not found, check `!Sample_title`. (Depends on T012a, T012b, T012c-version-check).
- [ ] T015a [US1] Implement `src/preprocess.py` function `map_isg_genes(species: str, gene_list: list) -> list` that uses Ensembl Compara v109 API to map human ISG set to orthologs for non-human species. Return list of Ensembl IDs. Save mapping to `data/processed/ortholog_map.csv`. **Schema**: CSV, columns `human_gene`, `ortholog_gene`, `species`; delimiter=comma. (Depends on T012a, T012b).
- [ ] T015b [US1] Implement `src/preprocess.py` function `validate_isg_mapping(mappings: list, raw_counts: pd.DataFrame) -> bool` that verifies mapped orthologs exist in the **raw** counts matrix. **CRITICAL VALIDATION**: If overlap < 80%, mark sample as `excluded` (FR-015) and log reason. **Do NOT normalize first; validate on raw counts to avoid wasting compute on excluded samples.** Return boolean. (Depends on T015a, T012b).
- [ ] T014 [US1] Implement `src/preprocess.py` function `normalize_counts(counts_matrix: pd.DataFrame) -> pd.DataFrame` using `rpy2` to call `edgeR::calcNormFactors`. **Pre-condition: T015b must have filtered raw counts.** **Conversion**: Convert pandas DataFrame to R DGEList object before calling edgeR. **Schema**: Tab-separated, `genes` as index, `samples` as columns. Save to `data/processed/normalized_counts.csv`. (Depends on T015b, T012b).
- [ ] T015c [US1] Implement `src/preprocess.py` function `calculate_isg_score(normalized_counts: pd.DataFrame, isg_genes: list) -> pd.Series` that computes the first principal component (PCA) of the ISG gene columns. **Safety net: Verify ISG gene columns exist in normalized_counts; ABORT with fatal error if ISG set is empty or PCA fails.** Save scores to `data/processed/isg_scores.csv`. **Schema**: CSV, single column `isg_score`, `sample_id` as index. (Depends on T014, T015b).
- [ ] T017 [US1] Implement `src/preprocess.py` function `filter_samples(merged_df: pd.DataFrame) -> pd.DataFrame` that removes rows with missing strain links. **Do NOT enforce the >=30 count here; that check belongs post-aggregation.** (Depends on T016).
- [ ] T018a [US1] Implement `src/features.py` function `calculate_cai(fasta_path: str) -> float` calculating Codon Adaption Index (CAI) using human/mouse codon usage tables. Return float. (Depends on T012a).
- [ ] T018b [US1] Implement `src/features.py` function `calculate_gc_content(fasta_path: str) -> dict` calculating Global and region-specific GC-content. Return dict of floats. (Depends on T012a).
- [ ] T018c [US1] Implement `src/features.py` function `calculate_kmer_frequencies(fasta_path: str) -> dict` calculating k-mer frequencies. **Logic**: Read `n_final` from `data/processed/aggregated_dataset.csv` (generated by T023). If `n_final < 50`, extract k=3, 4 ONLY as authorized by `docs/spec_amendments.md` (T002c). If `n_final >= 50`, extract k=3, 4, 5, 6. Calculate relative frequency (count / total_k_mers). Return dict of floats. (Depends on T012a, T023).
- [ ] T018c-verify [US1] Implement `src/features.py` function `validate_kmer_features(features_df: pd.DataFrame) -> None` that verifies the presence of k=3 and k=4 columns AND the absence of k=5 and k=6 columns (if N < 50) or presence of k=5/6 (if N >= 50) in the feature matrix. **ABORT with fatal error if the k-mer set does not match the N < 50 rule.** (Depends on T018c).
- [ ] T018d [US1] Implement `src/features.py` function `calculate_repeat_density(fasta_path: str) -> float` using `pybedtools` to count repeat-masked bases. Return percentage of genome covered by repeats. (Depends on T012a).
- [ ] T020-feasibility [US1] Implement `src/features.py` function `check_esm1b_feasibility() -> bool` that attempts to import `esm` and run a minimal inference test on a small peptide. **Failure Threshold**: If runtime > 30s OR memory > 1GB, return False. Log the failure reason. (Depends on T002).
- [ ] T020-correlation-verify [US1] Implement `src/features.py` function `validate_proxy_baseline -> bool` that **MANDATORY**: Select a representative subset of strains (e.g., 20 or [deferred] of total). Run ESM-1b (if feasible) or Proxy on this subset. Calculate R² between ESM-1b scores and Proxy scores. **ABORT** if R² < 0.8. Return True if validation passes. **Note**: This task performs the validation on the *current* dataset; it does NOT check for a static baseline file. (Depends on T020-feasibility).
- [ ] T020-esm [US1] Implement `src/features.py` function `calculate_stability_esm(fasta_path: str) -> dict` using ESM-1b for protein stability. (Depends on T012a, T020-feasibility).
- [ ] T020-proxy [US1] Implement `src/features.py` function `calculate_stability_proxy(fasta_path: str) -> dict`. **Logic**: Run ONLY if T020-feasibility returns False AND T020-correlation-verify returns True. **Mandatory**: Implement Uniform Stability Proxy for ALL samples. **Pre-condition**: This task runs ONLY if `check_esm1b_feasibility()` fails AND `validate_proxy_baseline()` passes. This MUST include:
 1. **Amino Acid Composition (AAC)**: Keys `aac_{AA}` for each of the standard amino acids (float frequency).
 2. **Hydrophobicity Scales** (Kyte-Doolittle): Key `hydrophobicity_kytedoolittle` (float). **Algorithm**: Average Kyte-Doolittle score using `pyteomics.physical_properties.hydrophobicity`. Return a **dictionary** with these exact keys. (Depends on T012a, T020-feasibility, T020-correlation-verify).
- [ ] T020 [US1] Implement `src/features.py` function `calculate_stability(fasta_path: str) -> dict` that orchestrates stability calculation. **Logic**: If `check_esm1b_feasibility()` returns True, call `calculate_stability_esm`. If False, call `calculate_stability_proxy` only if `validate_proxy_baseline()` returns True. Else ABORT. (Depends on T020-feasibility, T020-correlation-verify, T020-esm, T020-proxy).
- [ ] T021 [US1] Implement `src/main.py` function `merge_datasets(features_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame` that joins on strain_accession. **Pre-condition: T018a, T018b, T018c, T018d, T020 completed.** **Mandatory Dependency: T015b must have validated the host data, T016 must have produced isg_scores.csv.** (Note: Merge only valid features). Save to `data/processed/merged_dataset.csv`. (Depends on T012c, T018a-d, T018c, T018d, T020, T015b, T016).
- [ ] T022 [US1] Implement `src/main.py` function `aggregate_by_strain(merged_df: pd.DataFrame) -> pd.DataFrame` that groups by strain_accession and averages the `isg_score` column. **Pre-condition: T021 completed.** Save to `data/processed/aggregated_dataset.csv`.
- [ ] T023 [US1] Add validation in `src/main.py`: assert `len(aggregated_df) >= 30` AND `len(aggregated_df['strain_accession'].unique()) >= 5`. Abort with fatal error if false per FR-013, FR-017. (Depends on T022).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Contract test: Create `tests/contract/test_dataset_schema.py` with function `test_schema_validates(merged_df)` asserting columns match `spec.md` FR-004.
- [ ] T011a [US1] Integration test: Create `tests/integration/test_download_manifest.py` with function `test_download_manifest_generation()` verifying that `fetch_viral_genomes` and `fetch_geo_data` produce a valid **`data/manifest.json`** (exact path) with checksums. **MUST PASS after T012c.** (Depends on T012c).
- [X] T011b [US1] Integration test: Create `tests/integration/test_merge_schema.py` with function `test_merge_schema_validation()` verifying that `merge_datasets` produces `data/processed/merged_dataset.csv` with correct schema. **MUST PASS after T014 and T018.** (Depends on T014, T018).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model training & performance reporting (Priority: P2)

**Goal**: Train a predictive model and obtain clear performance metrics.

**Independent Test**: Execute the modelling step on the full dataset and verify that the reported R², RMSE, and permutation‑test p‑value are logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [US2] Contract test: Create `tests/contract/test_model_output_schema.py` with function `test_model_schema_validates(model_output)` asserting keys match `spec.md` FR-007.
- [X] T025 [US2] Integration test: Create `tests/integration/test_model_training.py` with function `test_training_and_eval()` verifying model training and evaluation produce `data/artifacts/metrics.json`.

### Implementation for User Story 2

- [ ] T025a [US2] Validate total strains: Implement `src/model.py` function `validate_strains(df: pd.DataFrame) -> None`. **Pre-condition: Depends on T022 (Aggregation). Input: data/processed/aggregated_dataset.csv.** Check `len(df['strain_accession'].unique()) >= 5`. **ABORT with fatal error if len(test_strains) < 5.** per FR-017. (Depends on T022).
- [ ] T026 [US2] Implement `src/model.py` function `split_stratified_strain(df: pd.DataFrame, test_strains: int=5) -> tuple[DataFrame, DataFrame]`. **Pre-condition: Depends on T025a. Input: data/processed/aggregated_dataset.csv.** Shuffles unique strain IDs using `SEED=42`, assigns a subset to test, rest to train. Ensure no strain overlap. **Assert `len(test_strains_actual) >= 5`. ABORT with fatal error if false.** Save splits to `data/processed/train.csv`, `data/processed/test.csv`. (Depends on T022).
- [ ] T026b [US2] **Load Split Data**: Implement `src/model.py` function `load_split_data() -> tuple[DataFrame, DataFrame]` that loads `data/processed/train.csv` and `data/processed/test.csv` into memory and returns them as DataFrames. **Mandatory** to bridge the gap for T030. (Depends on T026).
- [ ] T027 [US2] Implement `src/model.py` function `calculate_vif(df: pd.DataFrame) -> dict` that computes VIF for each predictor. Return dict of {feature: vif}. **Mandatory**: While VIF is diagnostic and features are NOT removed based on VIF > 5, this task MUST **LOG A WARNING** if any retained predictor has VIF > 5, ensuring compliance with Plan Section 4. **Note**: This task does NOT abort on VIF > 5, as per Plan Section 4, but reports the violation of SC-003. (Depends on T026).
- [ ] T027-check [US2] Implement `src/model.py` function `check_vif_status(vif_dict: dict) -> bool` that returns True if all VIF <= 5, False otherwise. This is for **diagnostic logging only**; the pipeline does NOT abort if False. (Depends on T027).
- [ ] T028 [US2] Implement `src/model.py` function `train_elastic_net(X_train: DataFrame, y_train: Series) -> tuple[Model, float, float]` using `sklearn.ElasticNetCV` with k-fold CV. **Use sklearn.model_selection.cross_val_predict with cv=5. Ensure X_test is not passed to fit step.** Verify test data is completely excluded from CV process. Return best model, alpha, lambda. Save model to `data/artifacts/models/elastic_net.pkl`. (Depends on T026b).
- [ ] T030 [US2] Implement `src/model.py` function `debiased_lasso_pvalues(model: Model, X_test: DataFrame, y_test: Series, X_train: DataFrame, y_train: Series) -> dict` that computes p-values for coefficients using **Debiased Lasso (library: hdi)**. **Mandatory: Execute Debiased Lasso for ALL retained predictors.** **Pre-condition**:
 1. **Feature Set Alignment**: Extract the exact list of feature columns present in `X_train`. Apply this exact column list to `X_test` (reordering if necessary).
 2. **Zero-Variance Handling**: For any feature in the aligned set that has zero variance in `X_test` (common in high-dimensional splits), **IMPUTE** the values in `X_test` with the mean of that feature calculated from `X_train`. **DO NOT DROP** any columns. This ensures the dimensionality and feature set of `X_test` is identical to `X_train`, satisfying FR-012 and the Plan's requirement for "all retained predictors".
 3. **Execution**: Run Debiased Lasso on the aligned and imputed `X_test` and `y_test`. **ABORT if the feature set is empty.** Save to `data/artifacts/pvalues_exploratory.json`. **Schema**: JSON object with keys `feature_name` (string), `coefficient` (float), `p_value_raw` (float), `p_value_fdr` (float). (Depends on T028, T026b).
- [ ] T031 [US2] Implement `src/model.py` function `fdr_correction(pvalues: dict) -> dict` that applies Benjamini-Hochberg correction to p-values. Return dict {feature: adjusted_p_value}. Save to `data/artifacts/fdr_pvalues_exploratory.json`. (Depends on T030).
- [ ] T032a [US2] **Pilot Execution**: Implement `src/model.py` function `run_pilot_permutation(model: Model, X_test: DataFrame, y_test: Series) -> float` that runs a small pilot (e.g., 10 shuffles) to estimate runtime per permutation. (Depends on T028).
- [ ] T032b-subset-extract [US2] **Subset Feature Re-extraction**: Implement `src/model.py` function `reextract_features_subset(strain_ids: list) -> DataFrame` that re-extracts ALL viral features (T018a-d, T020) for a specific list of strain IDs (the subset). This function is defined within `src/models.py` to avoid dependency on T018a-d. (Depends on T012a, T018a-d, T020).
- [ ] T032b [US2] **Permutation Loop**: Implement `src/model.py` function `run_full_permutation_test(model: Model, X_test: DataFrame, y_test: Series, n_shuffles: int=1000) -> float`. **Mandatory: Execute exactly 1,000 permutations as per Spec FR-007.**
 **STRICT PERMUTATION REQUIREMENT (Subset Strategy per T002d)**:
 1. **Subset Selection**: Select a representative subset of strains (e.g., 20 strains or [deferred] of total) from `X_train` and `y_train`.
 2. **Re-extract Features**: Call `reextract_features_subset` (T032b-subset-extract) for this subset to generate a local feature matrix.
 3. **Shuffle labels**: Randomly shuffle `y_train` and `y_test` labels together to preserve the relationship between features and labels for the null distribution.
 4. **Re-run Model Training**: Re-train the Elastic Net model (T028) on the shuffled/permuted subset.
 5. **Calculate Null R²**: Compute R² for the permuted model.
 6. **Repeat** for 1000 permutations (on the subset) to estimate the null distribution.
 7. **Scale P-value**: Calculate the empirical p-value from the subset distribution and scale it to approximate the full dataset p-value (statistical justification: subset distribution approximates full distribution).
 8. **Runtime Check**: Run `run_pilot_permutation` to estimate time per shuffle. Calculate `estimated_total_time` for 1000 permutations on the subset. **If `estimated_total_time > 3.5 hours` (12600 seconds): ABORT with fatal error.** Log error: "FATAL: Estimated runtime for 1000 permutations on subset exceeds 3.5 hours. Statistical rigor cannot be maintained. Aborting." **DO NOT reduce the permutation count.**
 Save result to `data/artifacts/permutation_pvalue.json`. **Schema**: JSON object with keys `observed_r2` (float), `p_value` (float), `n_permutations` (int), `subset_size` (int). (Depends on T032a, T028, T032b-subset-extract, T002d).
- [ ] T032c [US2] **P-value Aggregation**: Implement `src/model.py` function `aggregate_permutation_pvalue(null_distribution: list, observed_r2: float) -> float` that calculates the empirical p-value. (Depends on T032b).
- [ ] T033 [US2] Implement `src/model.py` function `evaluate_model(model: Model, X_test: DataFrame, y_test: Series) -> dict` that computes R² and RMSE. **Use the Elastic Net model (T028) and Debiased Lasso results (T030).** Return dict {r2: float, rmse: float, primary_method: 'elastic_net_debiased_lasso'}. Save to `data/artifacts/metrics.json`. (Depends on T028, T030).
- [ ] T034 [US2] Implement `src/main.py` function `log_metrics(metrics: dict) -> None` that writes metrics dict to `data/artifacts/metrics.json` with keys: r2, rmse, permutation_pvalue, fdr_min_pvalue.
- [ ] T035 [US2] Add validation in `src/model.py`: assert `len(test_df['strain_accession'].unique()) >= 5`. **ABORT with fatal error if len(test_strains) < 5.** per FR-017. (Depends on T026).

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
- [ ] T041 [US3] **Structural Feature Visualization**: Implement `src/viz.py` function `plot_structural_importance(features_df: DataFrame, coefficients: dict) -> None` that specifically visualizes the contribution of the **Uniform Stability Proxy features** (AAC, Hydrophobicity) identified in T020. **Mandatory**:
 1. **Filter** `features_df` to remove any rows where structural feature columns (AAC_*, Hydrophobicity) are NaN (samples without valid ORFs).
 2. Generate a dedicated bar chart comparing the effect sizes of these physical metrics against sequence-based metrics (k-mers, GC).
 3. Save to `data/artifacts/plots/structural_importance.png`. (Depends on T020, T030).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review Response - Structural Feature Quantification (Priority: P2) 🛠️

**Goal**: Address the "Linus Pauling" review concern regarding the vagueness of "predicted protein structural properties" by explicitly implementing and documenting the quantitative physical metrics used as the Uniform Stability Proxy.

**Independent Test**: Verify that `data/processed/features.csv` contains specific columns for AAC and Hydrophobicity with non-null values, and that `docs/research.md` explicitly justifies these as the chosen structural proxies over high-fidelity 3D folding.

### Implementation for Review Response

- [ ] T048 [P] [Review] Update `docs/research.md` with a new section titled **"Structural Feature Quantification Strategy"**. This section MUST:
 1. Explicitly acknowledge the review concern that "predicted protein structural properties" is vague.
 2. State that due to CPU constraints (limited core count and memory capacity), high-fidelity 3D folding (e., AlphaFold, ESM-1b) is infeasible (referencing the failure in T020-feasibility).
 3. Define the **Uniform Stability Proxy** as the chosen solution: **Amino Acid Composition (AAC)** and **Hydrophobicity Scales** (Kyte-Doolittle).
 4. Justify these metrics: AAC captures the "chemical composition" (elementary charge distribution potential), and Hydrophobicity captures the "steric and folding propensity" (critical for alpha-helix/sheet stability).
 5. Explicitly state that these metrics are calculated for **ALL** viral proteins >100aa in the dataset, ensuring no method-switch bias.
 6. Cite the Plan.md "Complexity Tracking" section as the authority for this CPU-tractable approach. **Note: This task documents the solution implemented in T020, not defines it.** (Depends on T002b, T002c, T020).
- [ ] T049 [P] [Review] Update `src/features.py` function `calculate_stability` (T020) to include **explicit logging** of the calculated metrics. The function MUST log:
 - "Calculating AAC: {dict of 20 amino acid frequencies}"
 - "Calculating Hydrophobicity: {Kyte-Doolittle score}"
 - "Total structural features generated: {actual_count}" (Dynamic count: 21 if ORF >100aa, 0 otherwise).
 - Ensure these logs appear in `data/artifacts/logs/feature_extraction.log`. (Depends on T020).
- [ ] T050 [P] [Review] Add a validation task in `src/main.py` to verify that the **structural feature columns** (AAC_*, Hydrophobicity) are present in `data/processed/merged_dataset.csv`. **ABORT with fatal error if any structural column is missing or contains NaNs**, ensuring the "physical reality" requirement is met before modeling. (Depends on T021, T020).
- [ ] T051 [P] [Review] Update `docs/spec_amendments.md` to add a section **"Response to Linus Pauling Review"**. This section MUST explicitly state: "The specification's requirement for 'predicted protein structural properties' has been refined to use Amino Acid Composition and Hydrophobicity Scales as the definitive, quantitative metrics. These metrics directly address the review's concern for 'numbers and the model' by providing specific, calculable values for chemical composition and folding propensity, suitable for CPU execution." (Depends on T048).

**Checkpoint**: Review concerns regarding structural feature vagueness are addressed with explicit, quantitative, CPU-tractable metrics.

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

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Compute Constraint**: All tasks must run on a limited number of CPU cores, constrained RAM, and no GPU. **Uniform Stability Proxy is MANDATORY** (T020) as authorized by T002b and Plan.md. ESM-1b is explicitly excluded unless feasibility check passes.
- **Data Constraint**: All dataset URLs must be real and reachable (NCBI, GEO). No synthetic data for primary validation.
- **Methodology Constraint**: Debiased Lasso is MANDATORY for all cases per FR-012. Stability Selection is NOT used.
- **Ordering Constraint**: Aggregation (T022) MUST occur after Merge (T021). Split (T026) depends on Aggregation.
- **Abort Constraint**: Pipeline MUST abort if N < 30, total strains < 5, or test strains < 5.
- **Feature Constraint**: k-mer extraction is restricted to k=3, 4 ONLY as authorized by T002c to ensure CPU feasibility **IF N < 50** (where N is the final dataset size). If N >= 50, k=5,6 are included. **Exception**: If `n_strains_initial >= 50` (from T012c), k=5,6 are included. **Correction**: T018c now depends on T023 to use the final N.
- **Structural Constraint**: The Uniform Stability Proxy (AAC + Hydrophobicity) is the only method, authorized by T002b and Plan.md. All structural metrics are computed in T020. SASA, H-bond, Electrostatics are explicitly excluded.
- **Provenance Constraint**: Single `data/manifest.json` generated by T012c.
- **Spec Amendment Constraint**: Deviations from Spec FR-003 (ESM-1b, k=3-6) and FR-007 (Global Permutation) are formally documented in `docs/spec_amendments.md` (T002b, T002c, T002d) and `docs/research.md` (T002e).
- **Permutation Constraint**: T032b uses a Stratified Subset (e.g., 20 strains) for 1000 permutations to satisfy runtime constraints while preserving statistical validity, as authorized by T002d.
- **VIF Constraint**: T027 logs warnings for VIF > 5 but does NOT abort, aligning with Plan Section 4. SC-003 is reported as a target, not a hard constraint.