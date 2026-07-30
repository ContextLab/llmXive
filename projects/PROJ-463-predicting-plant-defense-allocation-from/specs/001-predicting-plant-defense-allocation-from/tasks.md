# Tasks: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

**Input**: Design documents from `/specs/001-plant-defense-allocation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (see plan.md). **Exact Files**: Create `src/__init__.py`, `tests/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/traits/.gitkeep`, `data/manifests/.gitkeep`, `data/synthetic/.gitkeep`. **Verification**: Run `test -d src && test -d tests && test -d data` and assert all directories exist. **Output**: `data/.dir_setup_complete` flag file. **[FR-001][FR-002]**
- [X] T002 Initialize Python project with pinned `requirements.txt` (includes `rpy2`, `biopython`, `scikit-learn`, `seaborn`, `matplotlib`, `ete3`, `pydantic`, `requests`, `tqdm`, `pyyaml`)
- [ ] T003a-fix Configure linting (ruff) and formatting (black) tools. **Exact Files**: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Verification**: Run `ruff check.` and `black --check.` and assert they pass. **[FR-001]**
- [ ] T003b-fastp [P] Install `fastp` system package. **Exact Commands**: `sudo apt-get update && sudo apt-get install -y fastp`. **Verification**: Run `fastp --version` and assert non-zero exit code is NOT returned and version string is printed. **[FR-002]**
- [ ] T003b-hisat2 [P] Install `HISAT2` system package. **Exact Commands**: `sudo apt-get update && sudo apt-get install -y hisat2`. **Verification**: Run `hisat2 --version` and assert non-zero exit code is NOT returned and version string is printed. **[FR-002]**
- [ ] T003b-featurecounts [P] Install `featureCounts` (via Subread) system package. **Exact Commands**: `sudo apt-get update && sudo apt-get install -y subread`. **Verification**: Run `featureCounts -V` and assert non-zero exit code is NOT returned and version string is printed. **[FR-002]**
- [ ] T003c-fix Create environment validation script to verify all system tools (fastp, hisat, featureCounts) are installed and executable. **Exact Output**: Generate `data/manifests/env_validation.json` with the following schema: `{ "tools": { "fastp": { "version": "<string>", "installed": <bool> }, "hisat2": { "version": "<string>", "installed": <bool> }, "featureCounts": { "version": "<string>", "installed": <bool> } }, "timestamp": "<ISO8601>" }`. **Verification**: Assert that the JSON file exists and contains valid version strings and `installed: true` for all tools. **[FR-002]**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004-fix Implement configuration management (`src/utils/config.py`) for paths, seeds, thresholds, and the **fixed list of housekeeping genes** defined in FR-003. **Exact List**: ACT2, ACT7, GAPDH, UBQ10, EF1a, TUB6, TUB1, PP2A, SAND, CYP79D16, CYP79D15, CYP79D17, CYP83A1, CYP83B1, CYP96A1, CYP96A2, CYP96A3, CYP71A1, CYP71A2, CYP71A3, CYP71A4, CYP71A5, CYP71A6, CYP71A7, CYP71A8, CYP71A9, CYP71A10, CYP71A11, CYP71A12, CYP71A13, CYP71A14, CYP71A15, CYP71A16, CYP71A17, CYP71A18, CYP71A19, CYP71A20, CYP71A21, CYP71A22, CYP71A23, CYP71A24, CYP71A25, CYP71A26, CYP71A27, CYP71A28, CYP71A29, CYP71A30, CYP71A31, CYP71A32. **Note**: While CYP79D16, CYP79D15, etc., are used here for normalization (FR-003), they MUST be excluded from the predictor set in T021 to prevent bias (FR-005).
- [ ] T005-fix Implement logging and provenance tracking (`src/utils/logger.py`, `src/utils/provenance.py`) (see plan.md)
- [ ] T006-fix Create base data schemas (`src/utils/schemas.py`) **defined inline**. **Implementation Detail**: Define Pydantic models inline with these exact fields:
 ```python
 class RNASeqStudy(BaseModel):
     accession_id: str
     species: str
     tissue: str
     treatment: str
     replicates: int
 class HerbivoreResponseVector(BaseModel):
     gene_id: str
     log2fc: float
     pvalue: float
     herbivore_type: str
 class DefenseAllocationIndex(BaseModel):
     species: str
     chemical_mean: float
     physical_mean: float
     ratio: float
 class Species(BaseModel):
     name: str
     tissue_types: List[str]
     herbivore_types: List[str]
 ```
 **Source**: Derived directly from spec.md (FR-001, FR-006, FR-017). **[FR-001][FR-006][FR-017]**
- [ ] T007-fix Create and execute `src/utils/setup_dirs.py` to initialize the directory structure (`data/raw`, `data/processed`, `data/traits`, `data/manifests`, `data/synthetic`). **Verification**: Assert that all required directories exist and are writable after execution. **Output**: `data/.dir_setup_complete` flag file. **[FR-001][FR-002]**
- [ ] T015-fix Create `src/data/synthetic_generator.py` to generate structurally valid synthetic **TPM count matrices** **stored in `data/synthetic/`** (NOT `data/raw/`). **Logic**:
 1. **Seed**: Use a fixed random seed for reproducibility.
 2. **Distribution**: Generate TPM values using a log‑normal distribution (`scipy.stats.lognorm(s=1.5, scale=10)`) to mimic real expression data.
 3. **Dimensions**: Create a matrix of multiple species × a large set of genes.
 4. **Metadata**: Generate synthetic metadata (accession_id, species, tissue, treatment) consistent with FR-001.
 5. **Manifest**: Write `data/manifests/synthetic_manifest.json` with schema:
 `{ "file_name": <string>, "checksum": <SHA256 (Wikidata Q130595694, https://www.wikidata.org/wiki/Q130595694)>, "source_type": "synthetic", "provenance": { "generated_at": <ISO8601>, "tool_versions": { "python": "3.11", "numpy": "...", "scipy": "..." }, "accession_id": "SYNTH_001", "organism": "Arabidopsis thaliana", "parameters": { "seed": 42, "distribution": "log-normal" } } }`.
 **Constraint**: This task is for prototype validation only; it must **not** write to `data/raw/`. The synthetic manifest satisfies Constitution Principle VI for synthetic cases. **[FR-003][VI]**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Acquire public RNA‑seq data, preprocess into normalized TPM matrices, and apply batch correction.

**Independent Test**: Verify output files match FASTA/TPM specs, batch correction reduces CV ≥20% for housekeeping genes, and low‑coverage samples are flagged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] [US1] Unit test for FASTQ download validation in `tests/unit/test_download.py`
- [X] T009 [P] [US1] Unit test for batch correction metric calculation in `tests/unit/test_batch_correction.py`
- [X] T010 [P] [US1] Integration test for full preprocessing pipeline on a single synthetic study in `tests/integration/test_preprocess.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `src/data/download.py` to orchestrate data acquisition. **Logic**:
 1. If `--mode real`: Call T011‑real.
 2. If `--mode real` fails (e.g., no verified accession IDs, HTTP 404, timeout): **Trigger T015** to load synthetic data and log a warning.
 3. If `--mode synthetic`: Load pre‑generated synthetic data from `data/synthetic/`.
 4. **Dependency**: Requires T007-fix (directory setup). **[FR-001][VI]**
- [ ] T011-real [US1] Implement `src/data/fetch_real_data.py` to fetch FASTQ files from NCBI GEO/SRA **into `data/raw/`** and record checksums in a manifest under `data/manifests/`. **Primary Requirement**: Fetch real data using `prefetch` (SRA Toolkit) or `wget`/`curl` for FASTQ URLs. **Output**: `data/raw/{accession_id}.fastq.gz` and `data/manifests/real_data_manifest.json` with schema `{ "accession_id": <string>, "checksum": <SHA256>, "source_url": <string>, "downloaded_at": <ISO8601> }`. **Constraint**: Must write to `data/raw/`. **[FR-001][VI]**
- [ ] T011a [US1] Implement `src/data/verify_metadata.py` to verify downloaded FASTQ files match FR-001 requirements (tissue, herbivore type, replicates) **BEFORE** preprocessing. **Input**: Files from T011-real (or synthetic data when in synthetic mode). **Output**: `data/processed/metadata_verification_report.json`. **Metadata Source**: Fetch metadata from NCBI E‑utilities using the accession ID or parse metadata from the SRA manifest. If verification fails, log exclusion reason and halt processing for that study. **Synthetic Mode**: Verify synthetic metadata against schema. If real data is missing and synthetic mode is active, the report MUST explicitly state `"mode": "synthetic"` and `"real_data_available": false`. If the synthetic data also fails schema validation, the task MUST raise `SystemExit` and write `data/manifests/human_input_needed.flag`. **[FR-001]**
- [X] T012a [US1] Implement `src/data/preprocess_fastp.py` wrapper for `fastp`. **Dependency**: Requires `fastp` installed via T003b‑fastp and verified by T003c‑fix. **Execution**: `fastp -i input_R1.fastq.gz -I input_R2.fastq.gz -o output_R1_trimmed.fastq.gz -O output_R2_trimmed.fastq.gz --thread 4 --json fastp_report.json`. **Output**: `data/processed/trimmed/{accession_id}_R1_trimmed.fastq.gz`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [X] T012b [US1] Implement `src/data/preprocess_hisat2.py` wrapper for `HISAT2`. **Dependency**: Requires `HISAT2` installed via T003b‑hisat2 and verified by T003c‑fix. **Execution**: `hisat2 -p 4 -x genome_index -1 input_R1_trimmed.fastq.gz -2 input_R2_trimmed.fastq.gz -S output.bam`. **Output**: `data/processed/aligned/{accession_id}.bam`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [X] T012c [US1] Implement `src/data/preprocess_featurecounts.py` wrapper for `featureCounts`. **Dependency**: Requires `featureCounts` installed via T003b‑featurecounts and verified by T003c‑fix. **Execution**: `featureCounts -T 4 -p -a annotation.gtf -o output.counts input.bam`. **Output**: `data/processed/count_matrices/{accession_id}_tpm.csv`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [ ] T013 [US1] Implement `src/data/batch_correction.py` with ComBat‑seq logic. **Dependency**: **T004-fix** (configuration of housekeeping genes). **Implementation**: Use `rpy2` to call `sva::ComBat_seq(counts, batch=batch, group=group)`. **Housekeeping Gene Selection**: Read the fixed list of 50 genes from `src/utils/config.py` (output of T004). Use `rpy2` to call `genefilter::geNorm()` on this list to obtain the 50 lowest M‑value genes. **Concrete Logic**:
 1. Load the fixed list of 50 genes from `src/utils/config.py`.
 2. Filter the expression matrix to include only these 50 genes.
 3. Call `geNorm` via `rpy2` with the filtered matrix.
 4. Extract the M-values and sort genes by ascending M-value.
 5. Select a representative subset of top-ranked genes (or all if fewer than the threshold are available).
 6. Compute **Coefficient of Variation (CV)** for these genes before and after correction; report reduction percent.
 7. **Mandatory Output**: Write both `pre_correction_cv` and `post_correction_cv` to `data/manifests/batch_correction_report.json` with schema `{ "pre_correction_cv": <float>, "post_correction_cv": <float>, "reduction_percent": <float>, "target_reduction": 0.20, "selected_genes": [<list of gene IDs>] }`. **[FR-003]**
- [ ] T014 [US1] Implement QC logic to exclude studies with <2 biological replicates or missing tissue metadata, logging exclusion reasons and outputting a **post‑QC species list** to `data/processed/post_qc_species_list.json`. **Exact Threshold**: < 2 replicates. **Schema**: `{ "species": <string>, "exclusion_reason": <string> }`. **[FR-001]**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (with real or synthetic data)

---

## Phase 4: User Story 2 - Differential Expression and Feature Derivation (Priority: P2)

**Goal**: Compute differential expression, derive herbivore‑response vectors, perform pathway aggregation, and validate trait data availability.

**Independent Test**: Verify DESeq2 identifies DE genes correctly, response vectors are consistent across folds, pathway aggregation reduces features to ≤50, and trait data gate halts if >30% missing.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for DE gene selection logic (FDR < 0.05, |log2FC| > 1) in `tests/unit/test_de_analysis.py`. **Logic**: Implement `deseq2_results[ (deseq2_results['padj'] < 0.05) & (abs(deseq2_results['log2FoldChange']) > 1) ]`. **[FR-004]**
- [X] T017 [P] [US2] Unit test for pathway aggregation mapping in `tests/unit/test_feature_engineering.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `src/analysis/de_analysis.py` to run DESeq2 (via `rpy2`) for each species‑tissue pair. **[FR-004]**
- [ ] T036 [US2] Implement `src/data/kegg_mapper.py` to fetch KEGG/GO pathway mappings. **Implementation**: Use `bioservices.KEGG` or direct REST API. **Fallback**: If API fails, use a local static mapping file `data/raw/kegg_mapping_local.json`. **Output**: `data/processed/pathway_mappings.json` with schema `{ "gene_id": "string", "pathways": ["koXXXXX"] }`. **[FR-012]**
- [ ] T025a [US2] Implement `src/data/traits_try.py` to fetch defense trait data from TRY database (Primary Source). **Input**: Read target species list dynamically from `data/processed/post_qc_species_list.json`. **Output**: Write/initialize `data/processed/trait_fallback_summary.json` with schema `{ "target_species": [...], "primary_source_results": { "species": { "traits": [...] } }, "missing_from_try": ["species_name",...], "missing_from_all_sources": [] }`. **API**: Use `requests` with species name and trait IDs. **Authentication**: Check for `TRY_API_KEY` env var. **If Missing**: Raise `TRY_API_KEY_MISSING` error, log it, and proceed immediately to T025b. **Schema Update**: If `TRY_API_KEY` is missing, set `"try_api_key_status": "missing"` in the summary. **Halt Condition**: After both primary and fallback fetching (see T025b), if `len(missing_from_all_sources) / total_target_species > 0.30`, raise `SystemExit` and write `data/manifests/human_input_needed.flag`. **[FR-006][FR-011]**
- [ ] T025b [US2] Implement `src/data/traits_fallback.py` to fetch defense trait data from Phenoscape and GBIF if missing in TRY. **Input**: Read target species list from `data/processed/post_qc_species_list.json` and the `missing_from_try` list from T025a. **Output**: Append results into `data/processed/trait_fallback_summary.json` under a `fallback_results` key, updating the `missing_from_try` list if data is found. **Halt Condition**: Same as in T025a – if after fallback the missing fraction exceeds 30 %, raise `SystemExit` and create the flag file. **[FR-006][FR-011]**
- [ ] T025c [US2] Implement `src/data/traits_cache.py` to cache raw API responses from TRY, Phenoscape, and GBIF. **Input**: Raw responses from T025a and T025b. **Output**: Save raw JSON responses to `data/raw/traits/{source}_{species}.json` before any processing. **Constraint**: Satisfies Constitution Principles III and VII. **[FR-011][III][VII]**
- [ ] T038 [US2] **Gate Task**: After T025a/T025b/T025c have produced `data/processed/trait_fallback_summary.json`, compute `missing_fraction = (species missing from BOTH primary AND fallback) / total_target_species`. **If** `missing_fraction > 0.30`, raise `SystemExit` and write `data/manifests/human_input_needed.flag`. This task must run **before** any modeling or validation steps (Phase 5). **[FR-011]**
- [ ] T022 [US2] Pre‑compute the logic for LOSO‑aware feature selection (e.g., variance threshold calculation) to be used as a sub‑routine in T027. **Requires output from T036** (for pathway definitions). This task defines the **logic module**; the execution happens inside T027. **[FR-012]**
- [ ] T021 [US2] Implement `src/analysis/feature_engineering.py` to derive herbivore‑response vectors and perform pathway aggregation. **Logic**:
 1. Import `HOUSEKEEPING_GENES` from `src/utils/config.py`.
 2. Exclude trait‑synthesis genes (CYP79D16, etc.) from the DE list.
 3. **Within each LOSO training fold**, rank DE genes by aggregate significance, defined as `mean(-log10(p_value))` across all samples in the training fold.
 4. Select the common subset of top DE genes for that fold based on this ranking.
 5. Aggregate DE genes to pathways using `data/processed/pathway_mappings.json` (output of T036).
 6. Reduce features to ≤50 pathway‑level scores.
 7. **Output**: Aggregated feature matrix saved to `data/processed/aggregated_features.csv`. **[FR-012][FR-005]**
- [ ] T039 [US2] Implement `src/analysis/defense_index.py` to calculate the **Defense Allocation Index (DAI)** = (mean standardized chemical traits) / (mean standardized physical traits) using the compiled data from T025a/T025b. **Logic**: Standardize traits (z‑score) per trait type, compute means, then calculate the ratio. **Output**: Write DAI values to `data/processed/defense_allocation_index.csv`. **[FR-006][FR-011]**
- [ ] T040 [US2] Implement `src/analysis/reproducibility.py` to calculate **Jaccard similarity** between raw DE results and a published herbivory response gene list. **Primary Source**: Fetch from `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123456` (a simulated dataset for prototype). **Fallback**: If fetch fails, generate a synthetic list of random genes and set `"used_fallback": true`. **Output**: Save the Jaccard similarity score to `data/manifests/reproducibility_report.json` with schema `{ "jaccard_similarity": <float>, "source_url": "<URL>", "used_fallback": <bool> }`. **Gate**: If `used_fallback` is true, set a flag `REPRODUCIBILITY_SYNTHETIC_FALLBACK` in the manifest. **[SC-002]**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Statistical Evaluation (Priority: P3)

**Goal**: Train models, validate with LOSO/PGLS, and perform significance testing.

**Independent Test**: Verify LOSO CV execution, power analysis halts if N insufficient, permutation tests run, and metrics are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for Power Analysis gate in `tests/unit/test_validation.py`
- [ ] T024 [P] [US3] Unit test for Phylogenetic Null Model generation in `tests/unit/test_validation.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/analysis/validation.py` for Power Analysis. **Gate**: Execute *before* model training. **Calculation**: Using `statsmodels.stats.power.FTestPower` (or R's `pwr.f2.test`) compute required N to detect R²=0.3 with α=0.05, β=0.2. **If** `available_species_count < required_N`, raise `SystemExit` with message `"Insufficient statistical power for reliable prediction (required N={required_N}, available N={available_species_count})"` and create `human_input_needed` flag. **[FR-016]**
- [ ] T027 [US3] Implement `src/analysis/modeling.py` for Elastic Net and Random Forest with LOSO CV. **Calls** T021 (feature engineering) and T022 (feature‑selection logic) **inside each training fold**. **Check**: Verify `REPRODUCIBILITY_SYNTHETIC_FALLBACK` flag from T040; if true, log a warning that the model is trained with potentially invalid features. Apply the exclusion list from `src/utils/config.py` during feature selection in each fold to prevent data leakage. **[FR-007]**
- [ ] T028a [US3] Implement `src/data/phylogeny_fetcher.py` to fetch and parse the Open Tree of Life tree for the specific target species identified in `data/processed/post_qc_species_list.json`. **API**: POST `/v3/tree/ottol`. **Species name resolution**: Use OTT ID mapping. **Output**: `data/processed/phylogenetic_tree.tre`. If tree cannot be fetched for all species, generate a star phylogeny and log a warning that the null model is not phylogenetically informed. **[FR-017]**
- [ ] T028 [US3] Implement Phylogenetic Generalized Least Squares (PGLS) and Phylogenetic Null Model using `phylolm`. **Implementation**: Via `rpy2`, call `phylolm::pgls()` for the observed data. **Null Model**: Use `phylolm::phylo.permute` to shuffle the DAI vector while preserving the phylogenetic covariance structure, refit the model, and record R². Repeat for N=10 000 permutations (or until convergence). **Fallback**: If `phylo.permute` unavailable, fall back to `ape::permute`. **If neither available, raise a critical error.** **[FR-017]**
- [ ] T029 [US3] Implement permutation test (N=10 000 or until convergence) for Spearman correlation and apply **Holm‑Bonferroni correction** across all tissue‑specific model tests and gene‑set hypotheses. **[FR-008][FR-010]**
- [ ] T030 [US3] Create CLI entry point `src/cli/run_pipeline.py` to orchestrate the full pipeline (`--mode synthetic|real`). **[FR-010]**

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] [US3] Implement sensitivity analysis task `src/analysis/sensitivity_analysis.py` to vary the number of DE genes in the response vector (e.g., top N, 100, 200) and report R² variation. **Input**: Aggregated features from T021. **Output**: `data/manifests/sensitivity_analysis_report.json` with schema `{ "gene_count": <int>, "r2": <float>, "spearman": <float> }`. **[FR-009]**
- [ ] T051 [P] [US3] Implement final results aggregation and reporting in `src/cli/report_generator.py`. **Logic**: Compile all manifests (batch correction, reproducibility, power analysis, modeling results, phylogenetic validation) into a single summary report. **Output**: `data/manifests/final_analysis_summary.json` and `docs/analysis_report.md`. **[FR-008][FR-010]**
- [ ] T052 [P] [US3] Create a `README.md` section specifically for "Running with Real Data" detailing the exact steps to configure `TRY_API_KEY`, verify access to NCBI, and run `--mode real`. **[VI][VII]**

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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