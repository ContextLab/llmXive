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
- [X] T003a-fix Configure linting (ruff) and formatting (black) tools. **Exact Files**: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Verification**: Run `ruff check.` and `black --check.` and assert they pass. **[FR-001]**
- [X] T003b-install-deps [P] Install all required system and R packages via conda in a single step. **Exact Commands**:
  1. `conda install -c bioconda -c conda-forge -y fastp hisat2 subread r-sva r-normqpcr r-phylolm r-ape`
  2. **Verification**: Run `fastp --version`, `hisat2 --version`, `featureCounts -V`, `Rscript -e "library(sva)"`, `Rscript -e "library(NormqPCR)"`, `Rscript -e "library(phylolm)"`, `Rscript -e "library(ape)"` and assert exit code == 0 for all.
  3. **Prerequisites**: None (self-contained installation). **[FR-002][FR-003][FR-017]**
- [X] T003c-fix Create environment validation script to verify all system tools (fastp, hisat, featureCounts, R packages) are installed and executable. **Exact Output**: Generate `data/manifests/env_validation.json` with the following schema: `{ "tools": { "fastp": { "version": "<string>", "installed": <bool> }, "hisat2": { "version": "<string>", "installed": <bool> }, "featureCounts": { "version": "<string>", "installed": <bool> }, "r_sva": { "installed": <bool> }, "r_normqpcr": { "installed": <bool> }, "r_phylolm": { "installed": <bool> }, "r_ape": { "installed": <bool> } }, "timestamp": "<ISO8601>" }`. **Verification**: Assert that the JSON file exists and contains valid version strings and `installed: true` for all tools. **[FR-002]**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004-fix Implement configuration management (`src/utils/config.py`) for paths, seeds, thresholds, and the **fixed list of housekeeping genes** defined in FR-003. **Hardcode the following 50 genes** into `src/utils/config.py`: ACT2, ACT7, GAPDH, UBQ10, EF1a, TUB6, TUB1, PP2A, SAND, CYP79D16, CYP79D15, CYP79D17, CYP83A1, CYP83B1, CYP96A1, CYP96A2, CYP96A3, CYP71A1, CYP71A2, CYP71A3, CYP71A4, CYP71A5, CYP71A6, CYP71A7, CYP71A8, CYP71A9, CYP71A10, CYP71A11, CYP71A12, CYP71A13, CYP71A14, CYP71A15, CYP71A16, CYP71A17, CYP71A18, CYP71A19, CYP71A20, CYP71A21, CYP71A22, CYP71A23, CYP71A24, CYP71A25, CYP71A26, CYP71A27, CYP71A28, CYP71A29, CYP71A30, CYP71A31, CYP71A32. **Note**: While CYP79D16, CYP79D15, etc., are used here for normalization (FR-003), they MUST be excluded from the predictor set in T021 to prevent bias (FR-005).
- [X] T005-fix Implement logging and provenance tracking (`src/utils/logger.py`, `src/utils/provenance.py`) (see plan.md)
- [X] T006-fix Create base data schemas (`src/utils/schemas.py`) **defined inline**. **Implementation Detail**: Define Pydantic models inline with these exact fields:
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
- [X] T007-fix Create and execute `src/utils/setup_dirs.py` to initialize the directory structure (`data/raw`, `data/processed`, `data/traits`, `data/manifests`, `data/synthetic`). **Verification**: Assert that all required directories exist and are writable after execution. **Output**: `data/.dir_setup_complete` flag file. **[FR-001][FR-002]**

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
 1. **Mode Real (`--mode real`)**: Call T011‑real. **Fail Loud**: If real data fetch fails (no verified accession IDs, HTTP 404, timeout), **raise `RuntimeError` immediately**. Do NOT fallback to synthetic data within this specific fetch call. **However**, the *orchestrator* (this task) MUST catch this error and **switch to `--mode synthetic`** if the plan indicates real data is missing (i.e., if `data/manifests/verified_datasets.json` is empty or missing). In this case, call T015.
 2. **Mode Synthetic (`--mode synthetic`)**: Call T015 to generate synthetic data. **Constraint**: Synthetic mode is for structural validation only.
 3. **Dependency**: Requires T007-fix (directory setup). **[FR-001][VI]**
- [X] T011-real [US1] Implement `src/data/fetch_real_data.py` to fetch FASTQ files from NCBI GEO/SRA **into `data/raw/`** and record checksums in a manifest under `data/manifests/`. **Primary Requirement**: Fetch real data using `prefetch` (SRA Toolkit) or `wget`/`curl` for FASTQ URLs. **Logic**:
 - **Streaming**: If the dataset is large, use `datasets.load_dataset(..., streaming=True)` or `huggingface_hub.hf_hub_download` for shards to stay within RAM limits.
 - **Fail Loud**: If fetch fails, raise `RuntimeError` immediately. **Do NOT** fallback to synthetic data here. Let the orchestrator (T011) handle the mode switch.
 - **Output**: `data/raw/{accession_id}.fastq.gz` and `data/manifests/real_data_manifest.json` with schema `{ "accession_id": <string>, "checksum": <SHA256>, "source_url": <string>, "downloaded_at": <ISO8601> }`. **Constraint**: Must write to `data/raw/`. **[FR-001][VI]**
- [X] T011a [US1] Implement `src/data/verify_metadata.py` to verify downloaded FASTQ files match FR-001 requirements (tissue, herbivore type, replicates) **BEFORE** preprocessing. **Input**: Files from T011-real (or synthetic data when in synthetic mode). **Dependency**: T011 (or T015). **Output**: Always write `data/processed/metadata_verification_report.json`. **Metadata Source**: Fetch metadata from NCBI E‑utilities using the accession ID or parse metadata from the SRA manifest. **Verification Logic**:
 1. **Real Mode**: Use `Entrez.esearch` and `Entrez.efetch` to retrieve metadata. **API Parameters**: `db='gene'`, `term="Organism[ORGN] AND {accession_id}"`. **Rate Limiting**: `time.sleep(0.34)` between requests. **Mapping**:
    - `Organism` -> `species`: Extract the species name from the `Organism` field.
    - `Bioproject` -> `treatment`: If `Bioproject` is present, extract keywords. **Herbivory Keywords**: ['chewing', 'piercing', 'herbivore', 'insect', 'sucking', 'biting']. **Classification**: If 'chewing' or 'biting' in description -> 'chewing'; if 'piercing' or 'sucking' -> 'piercing-sucking'; else -> 'unknown'.
    - `Sample` attributes -> `tissue`: Extract `tissue_type` or `organ` from `Sample` attributes.
    - **Fallback**: If `Bioproject` is missing, use `Sample` attributes for treatment classification. If `Organism` is missing, use the file name or accession ID to infer species.
 2. **Synthetic Mode**: Generate a report with `mode: "synthetic"`, `real_data_available: false`, and populate dummy metadata consistent with the synthetic data structure.
 3. **Validation**: Check for presence of tissue metadata. If missing, flag for exclusion. Check for biological replicate count. If < 2, flag for exclusion. Check for correct herbivore treatment labels.
 4. **Output**: Write the report file FIRST, THEN raise `SystemExit` if real data is invalid or missing (unless in synthetic mode). If in synthetic mode, the report MUST explicitly state `"mode": "synthetic"` and `"real_data_available": false`. **[FR-001]**
- [X] T012a [US1] Implement `src/data/preprocess_fastp.py` wrapper for `fastp`. **Dependency**: Requires `fastp` installed via T003b-install-deps and verified by T003c-fix. **Execution**: `fastp -i input_R1.fastq.gz -I input_R2.fastq.gz -o output_R1_trimmed.fastq.gz -O output_R2_trimmed.fastq.gz --thread 4 --json fastp_report.json`. **Output**: `data/processed/trimmed/{accession_id}_R1_trimmed.fastq.gz`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [X] T012b [US1] Implement `src/data/preprocess_hisat2.py` wrapper for `HISAT2`. **Dependency**: Requires `HISAT2` installed via T003b-install-deps and verified by T003c-fix. **Execution**: `hisat2 -p 4 -x genome_index -1 input_R1_trimmed.fastq.gz -2 input_R2_trimmed.fastq.gz -S output.bam`. **Output**: `data/processed/aligned/{accession_id}.bam`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [X] T012c [US1] Implement `src/data/preprocess_featurecounts.py` wrapper for `featureCounts`. **Dependency**: Requires `featureCounts` installed via T003b-install-deps and verified by T003c-fix. **Execution**: `featureCounts -T 4 -p -a annotation.gtf -o output.counts input.bam`. **Output**: `data/processed/count_matrices/{accession_id}_tpm.csv`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [X] T014 [US1] Implement QC logic to exclude studies with <2 biological replicates or missing tissue metadata, logging exclusion reasons and outputting a **post‑QC species list** to `data/processed/post_qc_species_list.json`. **Exact Threshold**: < 2 replicates. **Input**: `data/processed/metadata_verification_report.json` (Output of T011a). **Logic**:
 1. Read the verification report.
 2. For each study, if `replicates < 2` or `tissue_metadata` is missing, add to exclusion list with reason.
 3. Write the list of included species to `post_qc_species_list.json`.
 4. **Output**: `data/processed/post_qc_species_list.json` with schema `{ "species": <string>, "exclusion_reason": <string> }`. **[FR-001]**
- [X] T013 [US1] Implement `src/data/batch_correction.py` with ComBat‑seq logic. **Dependency**: **T004-fix** (configuration of housekeeping genes), **T011a** (metadata verification), **T014** (QC filtered species list). **Implementation**: Use `rpy2` to call `sva::ComBat_seq(counts, batch=batch, group=group)`. **Housekeeping Gene Selection**:
 1. Load the fixed list of 50 genes from `src/utils/config.py`.
 2. Filter the expression matrix to include only genes that are present in BOTH the fixed list AND the expression matrix (Candidate Pool).
 3. Call `NormqPCR::geNorm()` via `rpy2` on this Candidate Pool to obtain M-values.
 4. **Select the top 50 most stable genes** from the Candidate Pool by sorting by ascending M-value. (If <50 genes are available in the Candidate Pool, use all available).
 5. **Calculate Coefficient of Variation (CV) for this selected subset (top 50 or all available) BEFORE and AFTER correction. DO NOT use the full fixed list for the CV metric.**
 6. **Mandatory Output**: Write both `pre_correction_cv` and `post_correction_cv` to `data/manifests/batch_correction_report.json` with schema `{ "pre_correction_cv": <float>, "post_correction_cv": <float>, "reduction_percent": <float>, "target_reduction": 0.20, "selected_genes": [<list of selected gene IDs>] }`. **[FR-003]**
- [X] T015 [US1] Implement `src/data/synthetic_generator.py` to generate structurally valid synthetic **TPM count matrices** **stored in `data/synthetic/`** (NOT `data/raw/`). **Logic**:
 1. **Seed**: Use `seed=42` for reproducibility.
 2. **Distribution**: Generate TPM values using `scipy.stats.lognorm(s=1.5, scale=10)` to mimic real expression data.
 3. **Dimensions**: Create a matrix of multiple species × a large set of genes.
 4. **Metadata**: Generate synthetic metadata (accession_id, species, tissue, treatment) consistent with FR-001.
 5. **Manifest**: Write `data/manifests/synthetic_manifest.json` with schema:
 `{ "file_name": <string>, "checksum": <SHA256 of the JSON object>, "source_type": "synthetic", "provenance": { "generated_at": <ISO8601>, "tool_versions": { "python": "3.11", "numpy": "...", "scipy": "..." }, "accession_id": "SYNTH_001", "organism": "Arabidopsis thaliana", The research planning document outlines a study investigating the impact of log-normal distributed parameters on system stability. The proposed method involves simulating parameter sets with a fixed seed and shape parameter, while varying the scale parameter across a range of magnitudes to observe emergent behaviors, as detailed in prior work (DOI: 10.1038/s41586-020-2649-2). } }`.
 6. **Verification Report**: **CRITICAL**: Generate `data/processed/metadata_verification_report.json` with synthetic data populated (mode="synthetic", real_data_available=false) to satisfy T011a input requirements. **This report MUST be written BEFORE the task completes.**
 **Constraint**: This task is for prototype validation only; it must **not** write to `data/raw/`. The synthetic manifest satisfies Constitution Principle VI for synthetic cases. **[FR-003][VI]**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (with real or synthetic data)

---

## Phase 4: User Story 2 - Differential Expression and Feature Derivation (Priority: P2)

**Goal**: Compute differential expression, derive herbivore‑response vectors, perform pathway aggregation, and validate trait data availability.

**Independent Test**: Verify DESeq2 identifies DE genes correctly, response vectors are consistent across folds, pathway aggregation reduces features to ≤50, and trait data gate halts if >30% missing.

**⚠️ DEPENDENCY NOTICE**: All tasks in this phase depend on the completion of Phase 3 (US1), specifically **T014** (Post-QC Species List) and **T015** (Synthetic Data Generation) or **T011-real** (Real Data Fetch).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for DE gene selection logic (FDR < 0.05, |log2FC| > 1) in `tests/unit/test_de_analysis.py`. **Logic**: Implement `deseq2_results[ (deseq2_results['padj'] < 0.05) & (abs(deseq2_results['log2FoldChange']) > 1) ]`. **[FR-004]**
- [X] T017 [P] [US2] Unit test for pathway aggregation mapping in `tests/unit/test_feature_engineering.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `src/analysis/de_analysis.py` to run DESeq2 (via `rpy2`) for each species‑tissue pair. **[FR-004]**
- [X] T036 [US2] Implement `src/data/kegg_mapper.py` to fetch KEGG/GO pathway mappings. **Implementation**: Use `bioservices.KEGG` or direct REST API. **Fallback**: If API fails, use a local static mapping file `data/raw/kegg_mapping_local.json`. **Output**: `data/processed/pathway_mappings.json` with schema `{ "gene_id": "string", "pathways": ["koXXXXX"] }`. **[FR-012]**
- [X] T025a [US2] Implement `src/data/traits_try.py` to fetch defense trait data from TRY database (Primary Source). **Input**: Read target species list dynamically from `data/processed/post_qc_species_list.json` (Output of **T014**). **Dependency**: **T014** (MUST be complete). **Requires: T014**. **Sequential Execution: This task MUST wait for T014 to complete and generate data/processed/post_qc_species_list.json**. **Output**: Write/initialize `data/processed/trait_fallback_summary.json` with schema `{ "target_species": [...], "primary_source_results": { "species": { "traits": [...] } }, "missing_from_try": ["species_name",...], "missing_from_all_sources": [] }`. **API**: Use `requests` with `https://api.try.eu.org/traits`. **Authentication**: Check for `TRY_API_KEY` env var. **Header**: `Authorization: Bearer <KEY>`. **Mapping**: Map species names to trait IDs for Glucosinolates, Alkaloids, Phenolics, Trichome Density, and Leaf Tensile Strength.. **Response Schema**: `{'trait_id': <int>, 'value': <float>, 'unit': <string>}`. **If Missing**: Log `TRY_API_KEY_MISSING` error, set `"try_api_key_status": "missing"` in the summary, and proceed immediately to T025b. **Do not raise SystemExit here**. **[FR-006][FR-011]**
- [X] T025b [US2] Implement `src/data/traits_fallback.py` to fetch defense trait data from Phenoscape and GBIF if missing in TRY. **Input**: Read target species list from `data/processed/post_qc_species_list.json` and the `missing_from_try` list from T025a. **Output**: Append results into `data/processed/trait_fallback_summary.json` under a `fallback_results` key, updating the `missing_from_try` list if data is found. **API**: Use ` and `. **Fallback Logic**: If API fails or returns no data, log the error and continue. **Schema**: `fallback_results` should contain `{"phenoscape": {...}, "gbif": {...}}` with the same structure as `primary_source_results`. **[FR-006][FR-011]**
- [X] T025c [US2] Implement `src/data/traits_cache.py` to cache raw API responses from TRY, Phenoscape, and GBIF. **Input**: Raw responses from T025a and T025b. **Output**: Save raw JSON responses to `data/raw/traits/{source}_{species}.json` before any processing. **Constraint**: Satisfies Constitution Principles III and VII. **[FR-011][III][VII]**
- [X] T038 [US2] **Gate Task**: After T025a/T025b/T025c have produced `data/processed/trait_fallback_summary.json`. **Dependency**: T025a, T025b, T025c. **Synchronization**: **WAIT** for the existence of `data/processed/final_aggregated_traits.json` (produced by a combined script or internal step in T038 that merges T025a/b outputs). **Logic**:
 1. Compute `missing_fraction = (species missing from BOTH primary AND fallback) / total_target_species`.
 2. **Target Species Definition**: The unique list of species in `data/processed/post_qc_species_list.json`.
 3. **If** `missing_fraction > 0.30`: **Write** `data/manifests/human_input_needed.flag` **FIRST**, THEN raise `SystemExit` with message "Insufficient trait data (missing > 30%)". **[FR-011]**
- [X] T022 [US2] Pre‑compute the logic for LOSO‑aware feature selection (e.g., variance threshold calculation) to be used as a sub‑routine in T027. **Requires output from T036** (for pathway definitions). This task defines the **logic module**; the execution happens inside T027. **[FR-012]**
- [X] T021 [US2] Implement `src/analysis/feature_engineering.py` to derive herbivore‑response vectors and perform pathway aggregation. **Logic**:
 1. Import `HOUSEKEEPING_GENES` from `src/utils/config.py`.
 2. Exclude trait‑synthesis genes (CYP79D16, etc.) from the DE list.
 3. **Within each LOSO training fold**, rank DE genes by aggregate significance, defined as `mean(-log10(p_value))` across all samples in the training fold.
 4. Select the common subset of top DE genes for that fold based on this ranking.
 5. Aggregate DE genes to pathways using `data/processed/pathway_mappings.json` (output of T036).
 6. Reduce features to ≤50 pathway‑level scores using standard KEGG/GO aggregation (mean/median of member genes).
 7. **Output**: Aggregated feature matrix saved to `data/processed/aggregated_features.csv`. **[FR-012][FR-005]**
- [X] T039 [US2] Implement `src/analysis/defense_index.py` to calculate the **Defense Allocation Index (DAI)** = (mean standardized chemical traits) / (mean standardized physical traits) using the compiled data from T025a/T025b. **Logic**: Standardize traits (z‑score) per trait type, compute means, then calculate the ratio. **Output**: Write DAI values to `data/processed/defense_allocation_index.csv`. **[FR-006][FR-011]**
- [X] T040 [US2] Implement `src/analysis/reproducibility.py` to calculate **Jaccard similarity** between raw DE results and a published herbivory response gene list. **Primary Source**: Fetch from a verified public repository (e.g., GEO GSE accession provided in `data/manifests/real_data_manifest.json` if available). **Configuration**: Check `config.py` for a list of verified accession IDs. **Constraint**: **STRICT**: If `--mode real` is used and no verified accession is found in config:
 1. Use a hardcoded consensus list of a defined set of genes (e.g., [ACT2, GAPDH, etc.]) as a **proxy**.
 2. **Output**: Save the Jaccard similarity score to `data/manifests/reproducibility_report.json` with schema `{ "jaccard_similarity": <float>, "source_url": "<URL or N/A>", "used_fallback": <bool>, "proxy_used": <bool>, "validation_rigor": "reduced" }`.
 3. **Note**: If `proxy_used` is true, the Jaccard score is not a valid scientific validation for SC-002, but the pipeline continues. **[SC-002]**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Statistical Evaluation (Priority: P3)

**Goal**: Train models, validate with LOSO/PGLS, and perform significance testing.

**Independent Test**: Verify LOSO CV execution, power analysis halts if N insufficient, permutation tests run, and metrics are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for Power Analysis gate in `tests/unit/test_validation.py`
- [X] T024 [P] [US3] Unit test for Phylogenetic Null Model generation in `tests/unit/test_validation.py`

### Implementation for User Story 3

- [X] T026 [US3] Implement `src/analysis/validation.py` for Power Analysis. **Gate**: Execute *before* model training. **Dependency**: T014 (to count species). **Calculation**: Using `statsmodels.stats.power.FTestPower` (or R's `pwr.f2.test`) compute required N to detect R²=0.3 with α=0.05, β=0.2. **If** `available_species_count < required_N`: **Write** `data/manifests/human_input_needed.flag` **FIRST**, THEN raise `SystemExit` with message `"Insufficient statistical power for reliable prediction (required N={required_N}, available N={available_species_count})"`. **[FR-016]**
- [X] T027 [US3] Implement `src/analysis/modeling.py` for Elastic Net and Random Forest with LOSO CV. **Dependency**: T021 (feature engineering), T022 (feature‑selection logic), T026 (power analysis gate), T040 (reproducibility flag). **Calls** T021 and T022 **inside each training fold**. **Check**: Verify `REPRODUCIBILITY_SYNTHETIC_FALLBACK` flag from T040; if true, log a warning that the model is trained with potentially invalid features. Apply the exclusion list from `src/utils/config.py` during feature selection in each fold to prevent data leakage. **[FR-007]**
- [X] T028a [US3] Implement `src/data/phylogeny_fetcher.py` to fetch and parse the Open Tree of Life tree for the specific target species identified in `data/processed/post_qc_species_list.json`. **API**: POST `/v3/tree/ottol`. **Species name resolution**: Use OTT ID mapping via `/v3/taxonomy/search`. **Output**: `data/processed/phylogenetic_tree.tre`. If tree cannot be fetched for all species:
 1. Generate a star phylogeny: create a Newick string where all species are direct children of a single root node with uniform branch lengths. Format: `(SpeciesA:1.0, SpeciesB:1.0,..., SpeciesN:1.0);`.
 2. **Log a warning**: "Star phylogeny generated. Bootstrap support threshold ≥70% not met. Phylogenetic validation (FR-017) will be skipped or marked as 'not phylogenetically informed'."
 3. **Set Flag**: Write `data/manifests/phylogeny_status.json` with `{"tree_type": "star", "phylogenetic_informed": false}`. **[FR-017]**
- [X] T028 [US3] Implement Phylogenetic Generalized Least Squares (PGLS) and Phylogenetic Null Model using `phylolm`. **Dependency**: T028a, T003b-install-deps (r-phylolm, r-ape), T003c-fix. **Gate**: **Check** `data/manifests/phylogeny_status.json`. If `phylogenetic_informed` is false, **SKIP** the PGLS and Null Model steps, log "Phylogenetic validation skipped due to star phylogeny", and proceed to T029. **Implementation**: If tree is valid, via `rpy2`, call `phylolm::pgls()` for the observed data. **Null Model**: **CRITICAL**: Generate null distribution by **shuffling species labels across the phylogenetic tree**. Specifically, use `ape::permute` with `method='phylo'`. **Fallback**: If `phylo.permute` unavailable, use `method='residual'`. If both fail, raise error `PHYLONULL_METHOD_UNAVAILABLE`. Repeat for N=10 000 permutations (or until convergence). **[FR-017]**
- [X] T053 [US3] Implement `src/analysis/tissue_specificity.py` to calculate the **tissue-specificity effect size (ΔR²)** and aggregate results. **Input**: Model results from T027 (leaf-only models and multi-tissue models). **Logic**: Calculate R² for leaf-only models and multi-tissue models. Compute ΔR² = R²_multi_tissue - R²_leaf_only. **Output**: Write results to `data/manifests/tissue_specificity_report.json` with schema `{ "r2_leaf_only": <float>, "r2_multi_tissue": <float>, "delta_r2": <float>, "interpretation": <string> }`. **[FR-008][SC-006]**
- [X] T029 [US3] Implement permutation test (N=10 000 or until convergence) for Spearman correlation and apply **Holm‑Bonferroni correction** across all tissue‑specific model tests and gene‑set hypotheses. **Additional Requirement**: Calculate the **tissue-specificity effect size (ΔR²)** by consuming the output from T053 (`data/manifests/tissue_specificity_report.json`). **Logic**: ΔR² = R²_multi_tissue - R²_leaf_only. **[FR-008][FR-010][SC-006]**
- [X] T030 [US3] Create CLI entry point `src/cli/run_pipeline.py` to orchestrate the full pipeline (`--mode synthetic|real`). **[FR-010]**

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T050 [P] [US3] Implement sensitivity analysis task `src/analysis/sensitivity_analysis.py` to vary the number of DE genes in the response vector (e.g., top N or a range of magnitudes) and report R² variation. **Input**: Aggregated features from T021. **Output**: `data/manifests/sensitivity_analysis_report.json` with schema `{ "gene_count": <int>, "r2": <float>, "spearman": <float> }`. **[FR-009]**
- [X] T051 [P] [US3] Implement final results aggregation and reporting in `src/cli/report_generator.py`. **Logic**: Compile all manifests (batch correction, reproducibility, power analysis, modeling results, phylogenetic validation, tissue specificity) into a single summary report. **Output**: `data/manifests/final_analysis_summary.json` and `docs/analysis_report.md`. **[FR-008][FR-010]**
- [X] T052 [P] [US3] Create a `README.md` section specifically for "Running with Real Data" detailing the exact steps to configure `TRY_API_KEY`, verify access to NCBI, and run `--mode real`. **[VI][VII]**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Phase 3 (US1)**: Must complete T014 (Post-QC Species List) before Phase 4 tasks can begin.
 - **Phase 4 (US2)**: **MUST WAIT** for Phase 3 completion. Specifically, T025a, T025b, T026, and T027 explicitly depend on `data/processed/post_qc_species_list.json` (Output of T014).
 - **Phase 5 (US3)**: Must complete Phase 4 (US2) tasks.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST WAIT** for T014 (US1) to complete to access the species list.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **MUST WAIT** for T014 (US1) and T025a/T038 (US2) to complete.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start.
- **US2 and US3 cannot start until T014 (US1) is complete.**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once dependencies are met)

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
3. Complete Phase 3: User Story 1 (Specifically T014)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (T014) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (T025a+) → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Focus on T014 completion)
 - Developer B: (Wait for T014, then start US2)
 - Developer C: (Wait for T014/T025a, then start US3)
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