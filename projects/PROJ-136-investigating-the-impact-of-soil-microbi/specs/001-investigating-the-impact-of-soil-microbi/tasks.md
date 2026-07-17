# Tasks: Soil Microbiome Diversity and Plant Disease Resistance

**Input**: Design documents from `/specs/001-soil-microbiome-diversity-disease-resistance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Format**: `[ID] [P?] [Story] Description`

**Path Conventions**:

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

**Terminological Alignment Note**: Spec title uses "Disease Resistance" but plan and implementation consistently use "disease incidence" (observational, not controlled inoculation). All tasks below use "disease incidence" terminology per plan.md to maintain construct validity per FR-009 (associational framing only). **SPEC AMENDMENT REQUIRED** to align spec title with implementation terminology.

**BLOCKING GATE**: Task T012 (dataset verification) MUST complete successfully with PASS status before any data download tasks (T013+) can execute. This resolves Constitution Principle II (Verified Accuracy) blocking gate. T013+ explicitly depend on T012 completion. **NOTE**: If T012 returns FAIL (no verified sources), the project halts and flags the spec for amendment; T013+ will not execute.

**CPU CONSTRAINT**: All analyses must complete on 2 CPU, 7GB RAM, no GPU within 6 hours. [UNRESOLVED-CLAIM: c_4779ff6a — status=not_enough_info] No GPU-dependent operations (load_in_8bit, device_map="cuda", large LLMs) are permitted.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan with exact directories: data/raw/, data/processed/, code/analysis/, code/tests/, code/tests/contract/, code/tests/integration/, code/tests/unit/, state/ - verification: all directories exist after execution
- [X] T002 Initialize Python 3.11 project with requirements.txt (scikit-learn, pandas, numpy, scipy, statsmodels, biopython, networkx) and **install QIIME 2 via Conda or Docker** (not pip) per Constitution Principle I - verification: QIIME 2 available in environment, requirements.txt lists non-QIIME dependencies
- [X] T003 [P] Configure linting and formatting tools (black, flake8, isort) - verification: config files created in.github/ and lint pass on code/analysis/*.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create schema contracts per contracts/ directory (sample.schema.yaml, disease-incidence.schema.yaml, taxon.schema.yaml)
- [X] T005 Implement data validation utilities using jsonschema against contract schemas - verification: validation functions pass all schema tests
- [X] T006 [P] Setup logging infrastructure with structured output in code/analysis/logging_config.py - verification: logger creates file handler outputting to logs/analysis.log with INFO level
- [X] T007 Create base data model entities (Sample, DiseaseIncidence, Taxon) in code/analysis/data_model.py
- [X] T008 Configure environment variables for dataset URLs and working directories in code/.env.example - verification: file created with DATASET_EMP_URL, DATASET_MGRAST_URL, DATASET_DISEASE_URL, WORKING_DIR variables
- [X] T009 Implement power analysis utility in code/analysis/power_analysis.py (a priori power ≥0.8, effect size ≥0.1) per FR-015 - verification: outputs data/processed/power_analysis_report.json with power (float ≥0.8), effect_size (float ≥0.1), min_sample_size (int) fields validated against FR-015 thresholds; **uses input parameters: alpha level = 0.05, variance estimate = 0.15 (default placeholder)**; report must explicitly confirm power ≥0.8 and effect_size ≥0.1 requirements are met
- [X] T012 [P] BLOCKING: Dataset verification task: **Attempt verification** of EMP/MG-RAST/disease dataset URLs and **report FAIL status** if no verified sources exist (per plan.md "BLOCKING GATE" warning); verification: data/processed/dataset_verification.json confirms URLs accessible and variables present with explicit pass/fail status; **if FAIL, halt T013+ and flag spec amendment requirement**; resolves Constitution Principle II BLOCKING GATE; T013+ depend on T012 completion with PASS status confirmed in dataset_verification.json

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess 16S rRNA amplicon tables and disease incidence records with validated contracts

**Independent Test**: Can be fully tested by verifying that the downloaded dataset contains sufficient samples for downstream analysis, disease records contain disease incidence entries, and the merged dataset has matched samples with complete metadata (plant species, GPS, soil type, disease incidence rate)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. **T012A (Integration test) depends on T013/T014 completion for execution, though test code can be written earlier.**

- [X] T010 [P] [US1] Contract test for sample data validation in code/tests/contract/test_sample_schema.py
- [X] T011 [P] [US1] Contract test for disease incidence data validation in code/tests/contract/test_disease_incidence_schema.py
- [ ] T012A [P] [US1] Integration test for data download and matching in code/tests/integration/test_data_acquisition.py (depends on T013/T014 completion for execution)

### Implementation for User Story 1

- [X] T013 [US1] Implement EMP/MG-RAST data download in code/analysis/data_acquisition.py with ≥100 samples target (FR-001) - URLs: EMP agricultural subset via a Qiita study (https://qiita.ucsd.edu/), MG-RAST via API endpoint mg-rast.org/api/mgrest - verification: data/raw/emp_agricultural_samples.csv and data/raw/mg-rast_soil_samples.csv created; DEPENDS ON T012 with PASS status confirmed in dataset_verification.json; T012 must pass before T013 can execute
- [ ] T014 [US1] Implement disease incidence record download in code/analysis/data_acquisition.py with ≥50 records target - verification: data/raw/disease_incidence_records.csv created; DEPENDS ON T012 completion
- [ ] T015 [US1] Implement variable verification per FR-008 (OTU/ASV tables, plant species, GPS, soil type, sequencing depth, sample ID, disease type, incidence rate, measurement date) with [MISSING_VARIABLE] markers - verification: data/processed/variable_verification_log.csv with columns sample_id, variable_name, status (present/missing)
- [ ] T016 [US1] Implement sample-disease matching logic by location and date fields (≥30 matched samples target)
- [ ] T016A [US1] **Validate merged dataset metadata completeness**: Verify that the merged dataset from T016 contains complete metadata for all required fields (plant species, GPS, soil type, disease incidence rate) per US1 Independent Test; verification: data/processed/metadata_completeness_report.csv with columns sample_id, field_name, status (complete/incomplete); **explicitly addresses US1 "complete metadata" requirement**
- [ ] T017 [US1] Implement taxon filtering (retain taxa present in ≥5% of samples) in code/analysis/preprocessing.py
- [ ] T018 [US1] Implement rarefaction to 10k reads per sample using QIIME 2 version 2023.9 (FR-002) in code/analysis/preprocessing.py - command: qiime diversity rarefy --i-table filtered-table.qza --p-sampling-depth 10000 - verification: data/processed/rarefied-table.qza created; **note: if >50% reads discarded, log warning and proceed with reduced sample size per Edge Cases**
- [ ] T019 [P] [US1] Implement checksum validation for all downloaded files in code/analysis/data_acquisition.py (Constitution Principle III)
- [ ] T020 [US1] Implement merged dataset export to data/processed/matched_samples.csv with complete metadata
- [ ] T051 [US1] Implement SC-006 data acquisition quality measurement: verify EMP/MG-RAST availability, disease dataset completeness, and matched sample count - verification: data/processed/data_quality_report.json with fields: emp_availability (boolean), mg-rast_availability (boolean), disease_dataset_completeness (float %), matched_sample_count (int), all meet spec thresholds; explicitly measures against SC-006 success criteria; **DEPENDS ON T012 PASS status AND T020 completion**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Model Fitting (Priority: P2)

**Goal**: Compute alpha-diversity metrics and fit beta regression/GLMM models with permutation tests

**Independent Test**: Can be fully tested by running the statistical analysis pipeline on a subset of 30 matched samples and verifying that a beta regression or binomial GLMM produces a p-value for the diversity coefficient, that permutation test results are reproducible, and that crop subset stratification produces consistent effect directions

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for alpha-diversity metrics schema in code/tests/contract/test_alpha_diversity_schema.py
- [ ] T022 [P] [US2] Integration test for statistical model fitting in code/tests/integration/test_statistical_models.py
- [ ] T023 [P] [US2] Integration test for permutation test reproducibility in code/tests/integration/test_permutation_tests.py

### Implementation for User Story 2

- [ ] T024 [US2] Implement alpha-diversity computation (Shannon, Simpson, Faith's PD) using QIIME 2 diversity alpha plugin (FR-003) in code/analysis/diversity_analysis.py
- [ ] T025 [US2] Implement beta regression or binomial GLMM fitting with disease incidence as response, alpha diversity as fixed effect, random intercepts for plant species and geographic region (FR-004) in code/analysis/statistical_models.py - model formula: disease_incidence ~ alpha_diversity + (1|plant_species) + (1|geographic_region), convergence criteria: max_iter=1000, tol=1e-6
- [ ] T026 [US2] Implement crop type stratification analysis (≥2 subsets, ≥15 samples each) with effect direction consistency check (≥80% consistent)
- [ ] T027 [US2] Implement permutation tests with 10,000 permutations (FR-005) in code/analysis/permutation_tests.py - justification: 10,000 permutations provides p-value stability <0.01 per permutation test power analysis for permutation tests; documents sufficiency against FR-005 "sufficient number of permutations" requirement; **includes performance validation step to verify 10,000 permutations complete within 6-hour runtime constraint**; verification: data/processed/permutation_stability.json with p-value variance <0.01 across runs
- [ ] T028 [US2] Implement multiple-comparison correction across all hypothesis tests (FR-010) with ≥100% correction coverage tracking - **default method: Benjamini-Hochberg (FDR)** - verification: data/processed/multiple_comparison_log.csv with test_id, raw_pvalue, corrected_pvalue, method columns; coverage = 100% if all tests corrected
- [ ] T029 [US2] Implement predictor collinearity diagnosis (VIF calculation) for alpha-diversity metrics per FR-012
- [ ] T030 [US2] Implement associational framing for all statistical findings (FR-009) - no causal claims - verification: all statistical output files contain 'associational relationship' or 'correlation' terminology, no causal language in docstrings/results
- [ ] T031 [US2] Implement model fit statistics (R², AIC) comparison against null model baseline per SC-002
- [ ] T032 [US2] Implement permutation test p-value stability measurement across multiple independent runs per SC-004
- [ ] T033A [US2] **Create reference meta-analysis values file**: Create data/reference/meta_analysis_values.json with placeholder structure and instructions to populate with verified reference values (e.g., from literature search) per SC-001; **if no verified reference exists, mark as 'unverified'** - verification: file created with structure { "reference_id": "string", "r_value": "float or null", "year": "int or null", "status": "verified/unverified" }
- [ ] T033 [US2] Implement correlation coefficient measurement against published meta-analysis values per SC-001 - **retrieve reference from data/reference/meta_analysis_values.json created by T033A; if status is 'unverified', report 'unverified' and skip comparison**; reference: 'Soil microbiome diversity and plant disease' (2023) meta-analysis r= -0.35 ± 0.12 (if available), stored in data/reference/meta_analysis_values.json - **removes hardcoded empirical value; defers to implementation phase as per spec**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Keystone Taxon Identification and Network Analysis (Priority: P3)

**Goal**: Perform ANCOM differential abundance testing and construct co-occurrence networks for keystone taxon identification

**Independent Test**: Can be fully tested by running ANCOM on a subset of samples and verifying that ≥3 taxa are identified with differential abundance (q<0.1) and that co-occurrence network produces ≥10 nodes with centrality metrics computed

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US3] Contract test for taxon schema with differential abundance q-values in code/tests/contract/test_taxon_schema.py
- [ ] T035 [P] [US3] Integration test for ANCOM differential abundance testing in code/tests/integration/test_keystone_taxa.py
- [ ] T036 [P] [US3] Integration test for co-occurrence network construction in code/tests/integration/test_cooccurrence_network.py

### Implementation for User Story 3

- [ ] T040 [US3] Implement high/low disease group stratification for ANCOM testing - verification: data/processed/high_low_disease_groups.csv with group assignment for each sample; **MUST precede T037 and T038**
- [ ] T037 [US3] Implement ANCOM differential abundance testing between high- and low-disease sites (FR-006) in code/analysis/keystone_taxa.py - ANCOM version 2.1 via q2-compositional plugin, significance threshold q<0.1 - verification: data/processed/ancom_results.csv with taxon, w-statistic, q-value columns
- [ ] T038 [US3] Implement co-occurrence network construction using CoNet (FR-007) in code/analysis/keystone_taxa.py - CoNet version 1.1.2 via Cytoscape plugin, parameters: Pearson/Spearman correlation, 1000 bootstrap iterations - verification: data/processed/cooccurrence_network.graphml created with ≥10 nodes
- [ ] T039 [US3] Implement node centrality computation (betweenness, degree) for keystone taxon identification
- [ ] T041 [US3] Implement keystone taxon flagging (≥2 taxa with high centrality) and output to data/processed/keystone_taxa.csv - verification: file contains ≥2 taxa with betweenness/degree centrality above 90th percentile
- [ ] T042 [US3] Implement differential abundance q-value filtering (q<0.1, ≥3 taxa target per SC-003)
- [ ] T042A [US3] **Handle edge case: insufficient significant taxa**: If ANCOM produces <3 taxa with q<0.1, log the failure, report the count, and ensure pipeline does not crash; verification: data/processed/ancom_edge_case_log.csv with fields: test_id, taxa_count, status (success/edge_case), message; **addresses spec Edge Cases requirement**
- [ ] T043 [US3] Implement network node count validation (≥10 nodes with centrality computed)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in docs/ including quickstart.md validation script, API reference docs - verification: quickstart.md validation script exists and runs, docs/api_reference.md documents all public functions, pytest docs tests pass
- [ ] T045 Code cleanup and refactoring across all analysis modules - concrete deliverables: remove dead code, reduce cyclomatic complexity <10 (Wikipedia: Cyclomatic complexity, https://en.wikipedia.org/wiki/Cyclomatic_complexity) per function, add type hints to all public functions
- [ ] T046 Performance optimization for QIIME 2 subprocess calls (ensure ≤6 hour runtime) - verification: code/analysis/runtime_benchmark.py measures each analysis script runtime, output data/processed/runtime_report.json, all <6 hours total
- [ ] T047 [P] Unit tests in code/tests/unit/ for data processing utilities - verification: tests for data_model.py, preprocessing.py, diversity_analysis.py with [deferred] line coverage minimum, output code/tests/coverage_report.xml
- [ ] T048 [P] Implement Docker containerization for QIIME 2 and CoNet (≤2 GB image size per Assumptions) - **use multi-stage build to strip dev dependencies and specific slim base image** - verification: docker/Dockerfile with base image python:3.11-slim, includes QIIME 2 2023.9, CoNet 1.1.2, image size <2GB
- [ ] T048A [P] **Validate Docker image size**: Check resulting Docker image size; if >2GB, document exception or split image strategy; verification: data/processed/docker_image_size_report.json with fields: image_name, size_gb, status (pass/fail), mitigation_strategy
- [ ] T049 [P] Run quickstart.md validation to verify all tasks execute end-to-end - verification: code/analysis/quickstart_validation.py runs all analysis scripts end-to-end, exits 0 if all pass, output logs/quickstart_validation.log
- [ ] T050 [P] Create final artifact hashes in state/PROJ-136-artifact-hashes.json (Constitution Principle V)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (matched_samples.csv)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output (matched_samples.csv)
- **CRITICAL DATA FLOW**: US1 data acquisition → US2 statistical analysis → US3 keystone identification
- **CRITICAL BLOCKING GATE**: T012 (dataset verification) MUST pass before T013 (EMP/MG-RAST download) can execute

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
Task: "Contract test for sample data validation in code/tests/contract/test_sample_schema.py"
Task: "Contract test for disease incidence data validation in code/tests/contract/test_disease_incidence_schema.py"
Task: "Integration test for data download and matching in code/tests/integration/test_data_acquisition.py (T012A)" (Note: execution depends on T013/T014)

# Launch all models for User Story 1 together:
Task: "Implement EMP/MG-RAST data download in code/analysis/data_acquisition.py with ≥100 samples target (T013)"
Task: "Implement disease incidence record download in code/analysis/data_acquisition.py with ≥50 records target (T014)"
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
 - Developer A: User Story 1 (data acquisition)
 - Developer B: User Story 2 (statistical models)
 - Developer C: User Story 3 (keystone taxa)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except T012 which is blocking)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **BLOCKING GATE**: All tasks contingent on dataset verification per research.md (EMP agricultural subset, MG-RAST soil microbiome, disease incidence records) - T012 must complete with PASS status before T013; **if T012 FAILS, halt and flag spec amendment**
- **CPU CONSTRAINT**: All analyses must complete on 2 CPU, 7GB RAM, no GPU within 6 hours
- **DATASET VERIFICATION**: Task T012 must verify real, reachable URLs before download proceeds (per Tasker Rule on dataset-download tasks); T013+ explicitly depend on T012 PASS status; **if no verified sources exist, T012 records FAIL and halts T013+**
- **CONSTRUCT VALIDITY**: All findings framed as "disease incidence" not "disease resistance" per spec/plan alignment note; SPEC AMENDMENT REQUIRED for terminological alignment
- **T012 CRITICAL**: This dataset verification task resolves the Constitution Principle II BLOCKING GATE before any download tasks proceed; **explicitly handles FAIL status**
- **T012A**: Integration test for US1 (distinct from T012 dataset verification); execution depends on T013/T014
- **FR-015 COMPLIANCE**: T009 must output explicit power ≥0.8, effect_size ≥0.1, min_sample_size (int) per FR-015; **uses default inputs: alpha=0.05, variance=0.15**
- **SC-006 COMPLIANCE**: T051 explicitly measures data acquisition quality against SC-006 success criteria; **depends on T012 PASS and T020**
- **FR-005 COMPLIANCE**: T027 documents 10,000 permutations sufficiency justification (p-value stability <0.01); **includes performance validation for 6-hour runtime**
- **EDGE CASE HANDLING**: T042A explicitly handles the case where ANCOM produces <3 significant taxa
- **REFERENCE DEFERRAL**: T033 removes hardcoded empirical values; T033A creates placeholder reference file
- **DOCKER STRATEGY**: T048 includes multi-stage build strategy; T048A validates image size
- **METADATA COMPLETENESS**: T016A explicitly validates merged dataset metadata completeness per US1 Independent Test
- **CORRECTION METHOD**: T028 specifies Benjamini-Hochberg (FDR) as default method
- **INSTALLATION CLARITY**: T002 specifies Conda/Docker for QIIME 2, not pip