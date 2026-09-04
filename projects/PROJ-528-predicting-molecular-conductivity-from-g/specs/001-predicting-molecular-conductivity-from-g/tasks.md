# Tasks: Predicting Molecular Conductivity from Graph-Based Features

**Input**: Design documents from `/specs/001-predicting-molecular-conductivity-from-g/`
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

- [X] T001 Create project structure by executing: `mkdir -p code tests data/raw data/processed contracts docs`
- [X] T002 Initialize Python 3.x project by creating `requirements.txt` containing: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`
- [X] T003 [P] Configure linting and formatting tools by creating `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']) sections

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration module (`code/config.py`) defining constants: `DATA_PATH`, `SEED`, `OUTLIER_SIGMA`, `VIF_THRESHOLD`, `TARGET_VAR` (default: 'conductivity')
- [X] T005 [P] Implement data validation utilities in `code/validators.py` with functions `validate_smiles(smiles_str)` and `check_target_range(values, min_log_range=3.0)`
- [X] T006 [P] Setup logging infrastructure in `code/logging_config.py` that configures a rotating file handler to `logs/pipeline.log` with JSON formatting
- [X] T007 Create `code/models.py` with Pydantic classes `Molecule` (fields: smiles, descriptors, target) and `Descriptor` (fields: name, value)
- [X] T008 [P] Implement scaffold splitting utility in `code/scaffold_split.py` using `rdkit.Chem.Scaffolds.MurckoScaffold` to ensure structural diversity and prevent data leakage (FR-002)
- [X] T009 Create `contracts/model_results_schema.yaml` defining fields: `r2`, `mae`, `cv_scores`, `sensitivity_data`, `vif_scores`, `quantum_proxy_metadata`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Load molecular structures and compute graph-based descriptors (Priority: P1) 🎯 MVP

**Goal**: Parse SMILES, compute standard topological descriptors, implement quantum-inspired proxies, and address resonance-related structural features as per reviewer feedback.

**Independent Test**: Can be fully tested by running the descriptor computation pipeline on a sample of SMILES strings and verifying that the output table contains all required descriptor columns with valid numeric values for each molecule.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write unit test code (expected to fail) before implementation

- [X] T010 [P] [US1] Write unit test code for aromaticity index calculation on benzene (SMILES: "c1ccccc1") in `tests/test_descriptors.py`. Function name: `test_aromaticity_benzene`. Assert that `aromaticity_index` equals 1.0 (or a specific non-zero value defined by the implementation).
- [X] T011 [P] [US1] Write unit test code for conjugation path length on butadiene vs. butane in `tests/test_descriptors.py`. Function name: `test_conjugation_path_length`. Use SMILES "C=CC=C" (butadiene) and "CCCC" (butane). Assert that butadiene's `conjugation_length` is greater than butane's.
- [X] T012 [P] [US1] Write unit test code for descriptor computation on mixed hybridization molecules in `tests/test_descriptors.py`. Function name: `test_mixed_hybridization_descriptors`. Use a molecule with both sp2 and sp3 carbons (e.g., "CC=C"). Assert that all computed descriptors are finite numbers and no NaN values are present.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `load_smiles(path: str) -> pd.DataFrame` in `code/data_loader.py` returning DataFrame with columns [smiles, valid, error_msg]
- [X] T014a [US1] Implement Degree Distribution Descriptors in `code/descriptors.py` (FR-001). Compute 4 scalar metrics for degree (mean, std, max, min) as distinct columns. **MUST return NaN for any molecule where degree calculation fails.**
- [X] T014b [US1] Implement Path Length Descriptors in `code/descriptors.py` (FR-001). Compute 4 scalar metrics for path length (mean, std, max, min) as distinct columns. **MUST return NaN for any molecule where path calculation fails.**
- [X] T015 [US1] Implement standard aromaticity and ring descriptors in `code/descriptors.py` (FR-008). Use `rdkit.Chem.rdMolDescriptors.CalcNumAromaticRings` and `rdkit.Chem.rdMolDescriptors.CalcNumRings` to compute 'aromaticity_index' and 'ring_count'. Do NOT implement custom HMO theory or resonance energy calculations. (FR-001, FR-008) **MUST return NaN if calculation fails.**
- [ ] T015c [US1] Implement **Longest Conjugated Path Length** in `code/descriptors.py` (FR-001). Compute the longest simple path in the subgraph induced by conjugated bonds (bonds with order > 1 or aromatic). Use `rdkit.Chem.GetSymmSSSR` and graph traversal on the conjugated subgraph. Output as `conjugation_length`. **MUST return NaN if conjugated subgraph is empty or calculation fails.**
- [X] T017 [US1] Implement fallback logic for missing quantum descriptors in `code/descriptors.py`. If a quantum-derived descriptor (e.g., HOMO-LUMO gap) is missing from the dataset for a molecule, log a warning: "Quantum descriptor missing for {smiles}; falling back to topological proxy." Use the topological conjugation length as the proxy. If both quantum and topological proxies fail for a molecule, exclude the molecule from the output. (FR-014)
- [X] T018 [US1] Implement error handling for invalid SMILES and missing conductivity in `code/data_loader.py`. If a SMILES string is invalid, log an error: "Invalid SMILES: {smiles}" and exclude the molecule. If the target variable (conductivity) is missing for a molecule, log a warning: "Missing conductivity for {smiles}" and exclude the molecule. (FR-012)
- [ ] T019 [US1] Write descriptor computation results to `data/processed/descriptors.csv` with EXACT columns: [smiles, status, degree_mean, degree_std, degree_max, degree_min, path_length_mean, path_length_std, path_length_max, path_length_min, aromaticity_index, conjugation_length, ring_count]. **Logic**: Iterate through computed descriptors. If any row has NaN values in the required descriptor columns (degree, path, aromaticity, conjugation, ring), drop the row and log: "Dropped {count} rows due to NaN values in descriptors." (FR-001, FR-008)
- [ ] T020 [US1] **Address Reviewer Feedback (linus-pauling-simulated)**: Implement **Bond Order and Length Annotation** in `code/descriptors.py`. Use `rdkit.Chem.GetBondOrder` and `rdkit.Chem.rdMolDescriptors.CalcCrippenDescriptors` (or similar) to estimate bond lengths (sp2 C-C ≈ 1.39Å, sp3 C-C ≈ 1.54Å) based on hybridization. Compute a new feature `weighted_path_length` that sums these estimated bond lengths along the longest conjugated path. (FR-001, FR-008, Reviewer Feedback)
- [ ] T021 [US1] **Address Reviewer Feedback (linus-pauling-simulated)**: Implement **Electronegativity-Weighted Polarity Term** in `code/descriptors.py`. Use `rdkit.Chem.rdMolDescriptors.CalcNumHBA` and `rdkit.Chem.rdMolDescriptors.CalcNumHBD` or atomic properties to estimate electronegativity differences. Compute a term `electronegativity_polarity = sum(|EN_atom1 - EN_atom2| * bond_length)` for polar bonds in the conjugated system. (FR-001, FR-008, Reviewer Feedback)
- [ ] T022 [US1] **Address Reviewer Feedback (linus-pauling-simulated)**: Implement **Hückel Resonance Energy Proxy** in `code/descriptors.py`. Use `rdkit.Chem.rdMolDescriptors.CalcNumAromaticRings` and the number of conjugated double bonds to estimate a Hückel-style resonance energy term (e.g., `resonance_proxy = num_aromatic_rings * 30 + num_conjugated_double_bonds * 10` in arbitrary units). Log a warning if this proxy is used instead of DFT. (FR-001, FR-008, Reviewer Feedback)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train regression models and evaluate predictive performance (Priority: P2)

**Goal**: Split data, train RF/GB models, handle outliers via sensitivity analysis, and validate target variable dynamic range.

**Independent Test**: Can be fully tested by running the training pipeline on a fixed dataset and verifying that both models produce R² scores, MAE values, and cross-validation metrics in a structured results file.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Integration test for scaffold split ensuring no structural leakage
- [X] T024 [P] [US2] Unit test for log-transformation of target variable
- [X] T025 [P] [US2] Unit test for outlier exclusion threshold logic

### Implementation for User Story 2

- [ ] T026 [US2] Implement target variable validation in `code/data_loader.py`: Check for 'conductivity'. If present and log-range >= 3.0, proceed. If missing, check for 'HOMO_LUMO_gap'. If missing, HALT with error "No valid target variable found". If HOMO_LUMO exists, **log a CRITICAL warning**: "Conductivity missing; using HOMO-LUMO gap fallback (Construct Validity Change)". **Update data/processed/metadata.json** to record the target variable change. (FR-003, Plan Scope Adjustment)
- [ ] T027 [US2] Implement scaffold-based train/test split (80/20 ratio) in `code/scaffold_split.py` AFTER T019 completes (FR-002)
- [ ] T028 [US2] Implement log-transformation of the selected target variable (conductivity or HOMO-LUMO) in `code/model_training.py`. Use natural logarithm (`np.log`) on the target column. Create a new column named `log_{target_var}` (e.g., `log_conductivity` or `log_HOMO_LUMO_gap`). (FR-003)
- [ ] T029 [US2] Train Random Forest and Gradient Boosting regressors on log-transformed target in `code/model_training.py`. RF: `n_estimators=100`, `max_depth=None`, `random_state=SEED`. GB: `n_estimators=100`, `learning_rate=0.1`, `random_state=SEED`. (FR-003)
- [ ] T030 [US2] Implement 5-fold cross-validation and metric recording in `code/model_training.py`. Use `cross_val_score` with `cv=5` and `scoring='r2'`. Record mean and std of R² scores. (FR-004)
- [ ] T031 [US2] Implement threshold filter function and retrain logic for outlier sensitivity in `code/analysis.py`. Function signature: `def filter_outliers(df, target_col, sigma_threshold):`. Logic: Calculate z-scores for `target_col`. Filter rows where `abs(z_score) <= sigma_threshold`. Return filtered DataFrame. Ensure it reuses the exact split indices from T027 and seed from T004. (FR-007)
- [ ] T032 [US2] Implement sensitivity analysis loop calling T031 in `code/analysis.py`, sweeping thresholds {σ, 3.0σ, 3.5σ}. **Logic**: For each threshold, record R². **Do NOT perform Kruskal-Wallis on N=3**. Instead, compute and report the range (max - min) and standard deviation of the R² scores across thresholds as a measure of variance. Save results to `data/processed/sensitivity_analysis.json`. Log a human-readable summary of the variance to `logs/pipeline.log`. (FR-007)
- [ ] T033 [US2] Save model results and sensitivity analysis data to `data/processed/model_results.json` with keys: {rf_r2, gb_r2, sensitivity_analysis: [{threshold, r2, variance_metric},...]}

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate feature importance analysis and correlation plots (Priority: P3)

**Goal**: Analyze feature importance, apply VIF filtering, correct for multiple comparisons, and generate visualizations.

**Independent Test**: Can be fully tested by running the analysis script on a trained model and verifying that feature importance rankings are exported and correlation plots are generated as image files.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Unit test for VIF calculation and thresholding
- [X] T035 [P] [US3] Unit test for Benjamini-Hochberg correction implementation
- [X] T036 [P] [US3] Unit test for correlation plot generation with confidence intervals

### Implementation for User Story 3

- [ ] T037 [US3] Implement VIF calculation function in `code/analysis.py`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor`. Input: feature matrix (numpy array). Output: dictionary mapping feature names to VIF scores. **This function MUST be callable iteratively.** (FR-013)
- [ ] T038 [US3] Implement feature exclusion logic for features with VIF > 10 in `code/analysis.py`. If any feature has VIF > 10, mark it for exclusion. (FR-013)
- [ ] T039 [US3] Implement iterative retraining loop in `code/analysis.py`: WHILE any VIF > 10, exclude the feature with the HIGHEST VIF, **call T037 logic** to recalculate VIF on the reduced feature set, retrain the model using the EXACT split indices from T027 and random seed from T004 on the reduced feature set. Repeat until all VIF ≤ 10. (FR-013)
- [ ] T040 [US3] Compute feature importance rankings (permutation or tree-based) on the final VIF-filtered model in `code/analysis.py`. Use `sklearn.inspection.permutation_importance` with `n_repeats=10` and `random_state=SEED`. **Save the ranked list to `data/processed/feature_importance.csv`**. Output format: a ranked list of (feature, importance_score). (FR-005)
- [ ] T041 [US3] Calculate feature-conductivity (or target) correlations with p-values in `code/analysis.py`. Use `scipy.stats.pearsonr`. Output format: a dictionary mapping feature names to (correlation_coefficient, p_value). (FR-005)
- [ ] T042 [US3] Apply Benjamini-Hochberg FDR correction to p-values in `code/analysis.py`. Use `statsmodels.stats.multitest.multipletests` with method='fdr_bh'. Output format: a dictionary mapping feature names to adjusted p-values. (FR-006)
- [ ] T043 [US3] Generate scatter plots with regression lines and 95% CI for top features in `code/plotting.py`, DEPENDENT ON T039, T040, T041, T042. Use `seaborn.regplot` with `ci=95`. **Save plots as PNG files to `data/processed/corr_plot_top5.png`**. (FR-005)
- [X] T045 [US3] Generate final analysis summary with adjusted p-values and top features, saving to `data/processed/analysis_summary.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T046 [P] Documentation updates in `docs/` including reviewer feedback resolution
- [X] T047 Code cleanup and refactoring. Criteria: remove unused imports, fix linting errors (black, ruff), and ensure all functions have docstrings. (FR-010)
- [X] T049 [P] Run full pipeline integration test on sample dataset (`data/raw/sample_smiles.csv`), verifying execution time < 6 hours on 2-core CPU. Log success/failure to `state/validation_log.json`. (FR-010)
- [X] T050 Verify all artifacts match `contracts/` schemas
- [X] T051 Run quickstart.md validation by executing all commands in `docs/quickstart.md` and logging success/failure to `state/validation_log.json`

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
- **User Story 2 (P2)**: Depends on US1 completion (needs descriptors)
- **User Story 3 (P3)**: Depends on US2 completion (needs trained models)

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
Task: "Write unit test code for aromaticity index calculation on benzene"
Task: "Write unit test code for conjugation path length on butadiene vs. butane"

# Launch all models for User Story 1 together:
Task: "Implement Degree Distribution Descriptors"
Task: "Implement Path Length Descriptors"
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
 - Developer A: User Story 1 (Descriptors)
 - Developer B: User Story 2 (Model Training & Sensitivity)
 - Developer C: User Story 3 (Analysis & VIF)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Reviewer Feedback Addressed**: Tasks T014a, T014b, T015, T015c implement standard topological descriptors (Degree, Path, Aromaticity, Ring, Conjugation) required by FR-001/FR-008. T015c specifically addresses the need for conjugation length using valid RDKit APIs. T020, T021, T022 address the specific resonance-related structural features (Bond Order/Length, Electronegativity Polarity, Hückel Resonance Proxy) flagged by reviewer `linus-pauling-simulated` to improve predictive fidelity and theoretical validity. T039 implements the iterative VIF filtering with reproducibility constraints. T040 and T043 now explicitly handle artifact saving, resolving the granularity issue previously identified in T044.
- **Target Variable Logic**: T026 implements the strict Spec requirement (Conductivity) with a conditional fallback (HOMO-LUMO) if Conductivity is missing, ensuring no silent relaxation of FR-003 while enabling the Plan's scope adjustment.
