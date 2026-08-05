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
 3. **Prerequisites**: None (self-contained installation). **[FR-002][FR-003]**
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
- [X] T011-real [US1] Implement `src/data/fetch_real_data.py` to fetch FASTQ files from NCBI GEO/SRA **into `data/raw/`** and record checksums in a manifest under `data/manifests/`. **Primary Requirement**: Fetch real data using `prefetch` (SRA Toolkit) or `wget`/`curl` for FASTQ URLs. **Streaming**: If the dataset is large, use `datasets.load_dataset(..., streaming=True)` or `huggingface_hub.hf_hub_download` for shards to stay within RAM limits. **Fail Loud**: If fetch fails, raise `RuntimeError` immediately. **Do NOT** fallback to synthetic data here. Let the orchestrator (T011) handle the mode switch. **Output**: `data/raw/{accession_id}.fastq.gz` and `data/manifests/real_data_manifest.json` with schema `{ "accession_id": <string>, "checksum": <SHA256>, "source_url": <string>, "downloaded_at": <ISO8601> }`. **Constraint**: Must write to `data/raw/`. **[FR-001][VI]**
- [X] T011a [US1] Implement `src/data/verify_metadata.py` to verify downloaded FASTQ files match FR-001 requirements (tissue, herbivore type, replicates) **BEFORE** preprocessing. **Input**: Files from T011-real (or synthetic data when in synthetic mode). **Dependency**: T007, T011 (or T015). **Verification Logic**:
 1. **Real Mode**: Use `Entrez.esearch` with `db='sra'` (for SRA accessions) or `db='gds'` (for GEO accessions). **API Parameters**: `term="accession_id[Accession] AND Plant[Organism]"`. **Rate Limiting**: `time.sleep(0.34)` between requests.
 2. **Extract Metadata**: Parse the XML response from `Entrez.efetch`.
    - **Species**: Extract from `Sample.attributes.Sample_attribute[Key="organism"].Value`.
    - **Tissue**: Extract from `Sample.attributes.Sample_attribute[Key="tissue"].Value`.
    - **Treatment**: Extract from `Sample.attributes.Sample_attribute[Key="treatment"].Value`.
    - **Replicate Count**: Extract from `Run.attributes.Sample_attribute[Key="biological_replicate"].Value` OR count the number of `Run` elements associated with the same `Sample` if not explicitly tagged. If the count is < 2, flag for exclusion.
 3. **Synthetic Mode**: Generate a report with `mode: "synthetic"`, `real_data_available: false`, and populate fields with synthetic values.
 4. **Exclusion Logic**: If tissue metadata is missing or replicates < 2, add to exclusion list with reason. Do NOT raise `SystemExit`. Log exclusions.
 5. **Output**: Write `data/processed/metadata_verification_report.json` with schema `{ "accession_id": <string>, "species": <string>, "tissue": <string>, "treatment": <string>, "replicates": <int>, "exclusion_reason": <string> | null, "mode": "real" | "synthetic" }`. **[FR-001]**
- [X] T012a [US1] Implement `src/data/preprocess_fastp.py` wrapper for `fastp`. **Dependency**: Requires `fastp` installed via T003b-install-deps and verified by T003c-fix. **Execution**: `fastp -i input_R1.fastq.gz -I input_R2.fastq.gz -o output_R1_trimmed.fastq.gz -O output_R2_trimmed.fastq.gz --thread 4 --json fastp_report.json`. **Output**: `data/processed/trimmed/{accession_id}_R1_trimmed.fastq.gz`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [X] T012b [US1] Implement `src/data/preprocess_hisat2.py` wrapper for `HISAT2`. **Dependency**: Requires `HISAT2` installed via T003b-install-deps and verified by T003c-fix. **Execution**: `hisat2 -p 4 -x genome_index -1 input_R1_trimmed.fastq.gz -2 input_R2_trimmed.fastq.gz -S output.bam`. **Output**: `data/processed/aligned/{accession_id}.bam`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [X] T012c [US1] Implement `src/data/preprocess_featurecounts.py` wrapper for `featureCounts`. **Dependency**: Requires `featureCounts` installed via T003b-install-deps and verified by T003c-fix. **Execution**: `featureCounts -T 4 -p -a annotation.gtf -o output.counts input.bam`. **Output**: `data/processed/count_matrices/{accession_id}_tpm.csv`. **[FR-002]** **Note**: Skipped in synthetic mode.
- [ ] T014 [US1] Implement QC logic to exclude studies with <2 biological replicates or missing tissue metadata, logging exclusion reasons and outputting a **post‑QC species list** to `data/processed/post_qc_species_list.json`. **Exact Threshold**: < 2 replicates. **Input**: `data/processed/metadata_verification_report.json` (from T011a). **Dependency**: T011a. **Logic**:
 1. Read the verification report.
 2. For each study, if `exclusion_reason` is not null, add to exclusion list.
 3. Write the list of included species to `data/processed/post_qc_species_list.json`. **Output**: `data/processed/post_qc_species_list.json` with schema `{ "included_species": [<string>], "exclusions": [{"species": "<string>", "reason": "<string>"}] }`. **[FR-001]**
- [X] T013 [US1] Implement `src/data/batch_correction.py` with ComBat‑seq logic. **Dependency**: **T004-fix** (configuration of housekeeping genes), **T011a** (metadata verification), **T014** (QC filtered species list). **Implementation**: Use `rpy2` to call `sva::ComBat_seq(counts, batch=batch, group=group)`. **Housekeeping Gene Selection**:
 1. Load the fixed list of 50 genes from `src/utils/config.py`.
 2. Filter the expression matrix to include only genes that are present in BOTH the fixed list AND the expression matrix (Candidate Pool).
 3. Call `NormqPCR::geNorm()` via `rpy2` on this Candidate Pool to obtain M-values.
 4. **Select the top 50 most stable genes** from the Candidate Pool by sorting by ascending M-value. (If <50 genes are available in the Candidate Pool, use all available).
 5. **Calculate Coefficient of Variation (CV) for this selected subset (top 50 or all available) BEFORE and AFTER correction. DO NOT use the full fixed list for the CV metric.**
 6. **Mandatory Output**: Write both `pre_correction_cv` and `post_correction_cv` to `data/manifests/batch_correction_report.json` with schema `{ "pre_correction_cv": <float>, "post_correction_cv": <float>, "reduction_percent": <float>, "target_reduction": 0.20, "selected_genes": [<list of selected gene IDs>] }`. **[FR-003]**
- [X] T015 [US1] Implement `src/data/synthetic_generator.py` to generate structurally valid synthetic **TPM count matrices** **stored in `data/raw/`** (to comply with Constitution Principle VI). **Logic**:
 1. **Seed**: Use `seed=42` for reproducibility.
 2. **Distribution**: Generate TPM values using `scipy.stats.lognorm(s=1.5, scale=10)` to mimic real expression data.
 3. **Dimensions**: Create a matrix of multiple species × a large set of genes.
 4. **Metadata**: Generate synthetic metadata (accession_id, species, tissue, treatment) consistent with FR-001.
 5. **Manifest**: Write `data/manifests/synthetic_manifest.json` with schema `{ "file_name": <string>, "checksum": <SHA256>, "source_type": "synthetic", "provenance": { "generated_at": <ISO8601>, "tool_versions": { "python": "3.11", "numpy": "...", "scipy": "..." }, "accession_id": "SYNTH_001", "organism": "Arabidopsis thaliana" } }`.
 6. **Verification Report**: **CRITICAL**: Generate `data/processed/metadata_verification_report.json` with synthetic data populated (mode="synthetic", real_data_available=false) to satisfy T011a input requirements. **This report MUST be written BEFORE the task completes.** **[FR-003][VI]**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (with real or synthetic data)

---

## Phase 4: User Story 2 - Differential Expression and Feature Derivation (Priority: P2)

**Goal**: Compute differential expression, derive herbivore‑response vectors, perform pathway aggregation, and validate trait data availability.

**Independent Test**: Verify DESeq2 identifies DE genes correctly, response vectors are consistent across folds, pathway aggregation reduces features to ≤50, and trait data gate halts if >30% missing.

**⚠️ DEPENDENCY NOTICE**: All tasks in this phase depend on the completion of Phase 3 (US1), specifically **T014** (Post-QC Species List) and **T015** (Synthetic Data Generation) or **T011-real**.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for DE gene selection logic (FDR < 0.05, |log2FC| > 1) in `tests/unit/test_de_analysis.py`. **Logic**: Implement `deseq2_results[ (deseq2_results['padj'] < 0.05) & (abs(deseq2_results['log2FoldChange']) > 1) ]`. **[FR-004]**
- [X] T017 [P] [US2] Unit test for pathway aggregation mapping in `tests/unit/test_feature_engineering.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `src/analysis/de_analysis.py` to run DESeq2 (via `rpy2`) for each species‑tissue pair. **[FR-004]**
- [ ] T025a [US2] Implement `src/data/traits_try.py` to fetch defense trait data from TRY database (Primary Source). **Input**: Read target species list dynamically from `data/processed/post_qc_species_list.json` (Output of **T014**). **Dependency**: T014, T025b. **Sequential Execution**: This task MUST wait for T014 to complete and generate the post-QC species list before starting. **Output**: Write/initialize `data/processed/trait_fallback_summary.json` with schema `{ "target_species": [...], "primary_source_results": { "species": { "traits": [...] } }, "missing_from_try": ["species_name",...], "missing_from_all_sources": [] }`. **API**: Use `requests` to `https://db.traits.plantbiology.org/api/v1/traits` with `species_name` as query parameter. **[FR-011]**
- [ ] T025b [US2] Implement `src/data/traits_fallback.py` to fetch defense trait data from Phenoscape and GBIF if missing in TRY. **Input**: Read target species list from `data/processed/post_qc_species_list.json` and the `missing_from_try` list from T025a. **Output**: Append results into `data/processed/trait_fallback_summary.json` under a `fallback_results` key, updating the `missing_from_try` list if data is found. **API**: Use `requests` to `https://phenoscape.org/api/v1/traits` and `https://api.gbif.org/v1/occurrence/search`. **[FR-011]**
- [X] T036 [US2] Implement `src/data/kegg_mapper.py` to fetch KEGG/GO pathway mappings. **Implementation**: Use `bioservices.KEGG` or direct REST API. **Output**: `data/processed/pathway_mappings.json` with schema `{ "gene_id": "string", "pathways": ["koXXXXX"] }`. **[FR-012]**
- [ ] T038a [US2] Implement 'Merge Traits Task' to combine the results from T025a and T025b into `data/processed/final_aggregated_traits.json`. **Input**: `data/processed/trait_fallback_summary.json`. **Logic**: Aggregate chemical and physical traits per species, calculate mean values. **Output**: `data/processed/final_aggregated_traits.json` with schema `{ "species": <string>, "chemical_traits": [<float>], "physical_traits": [<float>], "sources": [<string>] }`. **[FR-011]**
- [ ] T038b [US2] Implement 'Trait Data Gate' to check if >30% of target species lack data from all sources. **Input**: `data/processed/final_aggregated_traits.json` (from T038a). **Logic**: Count species with missing traits. If >30% missing, raise `human_input_needed` and halt. **Output**: `data/manifests/trait_gate_status.json` with schema `{ "total_species": <int>, "missing_count": <int>, "missing_percent": <float>, "status": "pass" | "fail" }`. **[FR-011]**
- [X] T021 [US2] Implement `src/analysis/feature_engineering.py` to derive herbivore‑response vectors and perform pathway aggregation. **Logic**:
 1. Import `HOUSEKEEPING_GENES` from `src/utils/config.py`.
 2. Exclude trait‑synthesis genes (CYP79D16, etc.) from the DE list.
 3. **Within each LOSO training fold**, rank DE genes by aggregate significance, defined as `mean(-log10(p_value))` across all samples in the training fold.
 4. Select the common subset of top DE genes for that fold based on this ranking.
 5. Aggregate DE genes to pathways using `data/processed/pathway_mappings.json`.
 6. Reduce features to ≤50 pathway‑level scores using standard KEGG/GO aggregation (mean/median of member genes).
 7. **Output**: Aggregated feature matrix saved to `data/processed/aggregated_features.csv`. **[FR-012][FR-005]**
- [X] T039 [US2] Implement `src/analysis/defense_index.py` to calculate the **Defense Allocation Index (DAI)** = (mean standardized chemical traits) / (mean standardized physical traits) using the compiled data from T025a/T025b. **Logic**: Standardize traits (z‑score) per trait type, compute means, then calculate the ratio. **Output**: Write DAI values to `data/processed/defense_allocation_index.csv`. **[FR-006][FR-011]**
- [ ] T040 [US2] Implement `src/analysis/reproducibility.py` to calculate Jaccard similarity with a published herbivory response gene list. **Logic**:
 1. **Real Mode**: If `data/manifests/real_data_manifest.json` exists, fetch the specific published gene list from GEO supplementary files (e.g., `https://ftp.ncbi.nlm.nih.gov/geo/series/{GSE_ID}/supp/`). If no real data is present, **skip this check** and log "Real data not available, skipping reproducibility check".
 2. **Synthetic Mode**: Use a synthetic reference list generated with known ground truth for structural validation.
 3. **Mapping**: Map GSE accession ID to supplementary files by constructing the URL `https://ftp.ncbi.nlm.nih.gov/geo/series/{GSE_ID}/supp/` and parsing the directory listing for files matching `*gene_list*` or `*DE_genes*`.
 4. **Output**: `data/manifests/reproducibility_report.json` with schema `{ "jaccard_similarity": <float>, "reference_source": <string> | "synthetic", "status": "pass" | "fail" | "skipped" }`. **[FR-002][SC-002]**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Statistical Evaluation (Priority: P3)

**Goal**: Train models, validate with LOSO/PGLS, and perform significance testing.

**Independent Test**: Verify LOSO CV execution, power analysis halts if N insufficient, permutation tests run, and metrics are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for Power Analysis gate in `tests/unit/test_validation.py`
- [X] T024 [P] [US3] Unit test for Phylogenetic Null Model generation in `tests/unit/test_validation.py`

### Implementation for User Story 3

- [X] T026 [US3] Implement `src/analysis/modeling.py` for Elastic Net and Random Forest with LOSO CV. **Dependency**: T021 (feature engineering), T022 (feature‑selection logic), T026 (power analysis gate).
- [ ] T028a [US3] Implement `src/data/phylogeny_fetcher.py` to fetch and parse the Open Tree of Life tree for the specific target species identified in `data/processed/post_qc_species_list.json`. **API**: POST `https://api.opentreeoflife.org/v3/tree_of_life/get_ottol_tree`. **Payload**: `{"ott_ids": [list_of_ott_ids], "branch_length_type": "ot:branchLength"}`. **Fallback**: If fetch fails, generate a star phylogeny. **Output**: `data/processed/phylogenetic_tree.tre`. **[FR-017]**
- [X] T028 [US3] Implement Phylogenetic Generalized Least Squares (PGLS) and Phylogenetic Null Model using `phylolm`. **Dependency**: T028a, T003b-install-deps (r-phylolm, r-ape), T003c-fix.
- [X] T029 [US3] Implement permutation test (N=10 000 or until convergence) for Spearman correlation and apply Holm‑Bonferroni correction across all tissue‑specific model tests and gene‑set hypotheses.
- [X] T053 [US3] Implement `src/analysis/tissue_specificity.py` to calculate the **tissue-specificity effect size (ΔR²)** and aggregate results.
- [X] T030 [US3] Create CLI entry point `src/cli/run_pipeline.py` to orchestrate the full pipeline (`--mode synthetic|real`).

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T050 [P] [US3] Implement sensitivity analysis task `src/analysis/sensitivity_analysis.py` to vary the number of DE genes in the response vector (e.g., top N or a range of magnitudes) and report R² variation.
- [X] T051 [P] [US3] Implement final results aggregation and reporting in `src/cli/report_generator.py`.
- [X] T052 [P] [US3] Create a `README.md` section specifically for "Running with Real Data" detailing the exact steps to configure `TRY_API_KEY`, verify access to NCBI, and run `--mode real`.

---

## Dependencies & Execution Order

(Unchanged from previous version)