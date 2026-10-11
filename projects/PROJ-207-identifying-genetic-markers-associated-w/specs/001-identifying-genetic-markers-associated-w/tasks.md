# Tasks: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

**Input**: `spec.md`, `plan.md`, existing data‑model and contracts.  
All paths are relative to the repository root.  

---

## Phase 0 – Project scaffolding  

- [ ] **T001** [P] Create the standard project directory layout  
  `mkdir -p code/ data/raw/ data/interim/ data/processed/ docs/ tests/`  
  *Verification*: `test -d code && test -d data/raw && test -d data/processed`.

- [ ] **T002** [P] Create a pinned `requirements.txt` containing the CPU‑tractable scientific stack (plink2, freebayes, bwa, scikit‑learn, pandas, numpy, statsmodels, pyyaml, requests, biopython, samtools).  
  *Verification*: `grep -E "plink2|freebayes|bwa|scikit-learn" requirements.txt`.

---  

## Phase 1 – Real‑data acquisition (metadata → full FASTQ)  

- [ ] **T004** [US1] Download **metadata only** (`code/01_download_metadata.py`)  
  *Source*: NCBI BioProject PRJNA639195 (CCD) & PRJNA566029 (healthy) via Entrez Direct.  
  *Requirements*: SSL‑validated download; abort loudly on any certificate error.  
  *Outputs*: `data/processed/ncbi_metadata.json` containing per‑sample fields (`sample_accession`, `ccd_status`, `varroa_load`, `geographic_region`, `sampling_year`).  
  *Verification*: JSON is well‑formed, contains `sample_count` ≥ 80; compute SHA‑256 checksum of the JSON and write it to `data/processed/ncbi_metadata_checksum.txt`. Verification succeeds if the checksum file exists and matches the computed hash.

- [ ] **T003** [US1] Implement **power analysis** (`code/utils/power_analysis.py`)  
  *Inputs*: `data/processed/ncbi_metadata.json` (checksum verified by T004).  
  *Behaviour*: computes power for OR ≥ 2.5 at α = 0.05; halts with exit code `ERR_SAMPLE_SIZE_INSUFFICIENT` if *n* < 80.  
  *Outputs*: `data/processed/power_analysis.json` (keys `power_value`, `status`, `n_samples`) and a human‑readable `data/processed/power_analysis.txt`.  
  *Verification*: JSON exists, `status=="PASS"` and `n_samples` ≥ 80.

- [ ] **T005** [US1] Full FASTQ download (`code/01_download_full.py`) – **depends on T003 passing**  
  *Implementation*: uses `fasterq-dump` (SRA‑Toolkit) for all accessions listed in `ncbi_metadata.json`.  
  *SSL*: validated; any failure aborts with a clear error.  
  *Outputs*: `data/raw/fastq/<sample_id>_R1.fastq.gz` and `..._R2.fastq.gz`; log written to `data/processed/ncbi_fetch_log.json`.  
  *Verification*: at least 80 FASTQ pairs exist; log records total bytes downloaded; compute SHA‑256 checksums for every FASTQ file and write a manifest `data/processed/fastq_checksums.txt`. Verification succeeds if the manifest exists and contains a checksum line for each downloaded file.

- [ ] **T006** [US1] Harmonise phenotypes (`code/02_harmonize_phenotypes.py`)  
  *Inputs*: `ncbi_metadata.json` + FASTQ list.  
  *Tasks*: map CCD diagnosis to binary (1 = CCD, 0 = healthy) per the 2007 CCD Working Group protocol; compute Varroa coverage.  
  *Gate*: if < 80 % of colonies have Varroa data → exit with `ERR_VARROA_COVARIATE_MISSING`. Otherwise, write `data/interim/phenotypes_harmonized.fam`.  
  *Verification*: `.fam` exists; header contains 6 columns; a companion `data/processed/varroa_coverage.txt` reports % coverage.

- [ ] **T007** [US1] Validate CCD instrument consistency (`code/02_validate_instruments.py`)  
  *Checks*: CCD status fields match BeeBase definitions; flag records where > 10 % are ambiguous.  
  *Output*: `data/processed/instrument_validation_report.json`.  
  *Verification*: JSON contains `ambiguous_fraction`; if > 0.10 the script exits with a non‑zero code.

- [ ] **T008** [US1] Collinearity diagnostics for covariates (`code/05_collinearity_diag.py`) – FR‑010  
  *Input*: `phenotypes_harmonized.fam`.  
  *Output*: `data/processed/collinearity_report.json` with VIF values and a correlation matrix.  
  *Verification*: any VIF > 5 or |r| > 0.8 is flagged in the JSON.

---  

## Phase 2 – Alignment & variant calling (CPU‑tractable)  

- [ ] **T009** [US1] Align reads & call variants (`code/02_align_and_call.sh`) – FR‑002  
  *Reference*: `data/raw/refs/Amel_HAv3.1.fa` (checksum‑validated).  
  *Steps*: `bwa mem` → SAM → `samtools view` → sorted BAM → `freebayes` → raw VCF.  
  *Filtering*: `bcftools filter` to keep biallelic SNPs with QUAL > 30 and DP ≥ 10.  
  *Output*: `data/interim/raw_variants.vcf`.  
  *Verification*: VCF passes `bcftools stats` with > 0 variants.

- [ ] **T010** [US1] Convert VCF → PLINK (`code/utils/vcf_to_plink.py`) – FR‑003  
  *Input*: `raw_variants.vcf`.  
  *Output*: `data/interim/bed.{bed,bim,fam}`.  
  *Verification*: all three PLINK files exist; `plink --bfile data/interim/bed --write-snplist` runs without error.

- [ ] **T011** [US1] LD pruning for population‑structure correction (`code/utils/ld_prune.sh`) – FR‑003  
  *Command*: `plink --bfile data/interim/bed --indep-pairwise 50 5 0.2 --out data/interim/bed_pruned`  
  *Output*: `data/interim/bed_pruned.prune.in` (list of retained SNPs).  
  *Verification*: file exists and contains ≥ 10 % of original SNPs.

---  

## Phase 3 – GWAS & multiple‑testing correction  

- [ ] **T012** [US1] GWAS logistic regression (`code/03_gwas.sh`) – FR‑004  
  *Input*: PLINK files (`bed`, `phenotypes_harmonized.fam`).  
  *Covariates*: geographic_region, sampling_year, varroa_mite_count.  
  *Output*: `data/interim/gwas_raw.tsv` (columns: SNP, CHR, BP, A1, OR, SE, P).  
  *Verification*: file exists, contains header, and at least one SNP row.

- [ ] **T013** [US2] Estimate effective number of independent tests (`code/utils/estimate_me.py`) – FR‑004 (implemented)  
  *Input*: `data/interim/bed_pruned.prune.in`.  
  *Method*: Li & Ji eigenvalue approach.  
  *Output*: `data/processed/me_estimate.txt` (single integer).  
  *Verification*: file exists, integer > 0, and script runs without error.

- [ ] **T014** [US2] Benjamini‑Hochberg FDR correction (`code/utils/fdr_correction.py`) – FR‑004  
  *Input*: `gwas_raw.tsv` + `me_estimate.txt`.  
  *Output*: `data/processed/gwas_results_fdr.tsv` (columns: SNP, CHR, BP, A1, P, Q, OR, SIGNIFICANT).  
  *Verification*: JSON schema `gwas_results.schema.yaml` validated; `SIGNIFICANT` is true iff Q < 0.05.

- [ ] **T015** [US2] Threshold‑sensitivity sweep (`code/utils/threshold_sensitivity.py`) – FR‑005  
  *Input*: `gwas_results_fdr.tsv`.  
  *Thresholds*: 1e‑7, 5e‑8, 1e‑8.  
  *Output*: `data/processed/threshold_sensitivity.json` (list of `{threshold, count, q_values}` objects).  
  *Verification*: JSON contains three objects; each `count` matches number of SNPs with P ≤ threshold.

- [ ] **T024** [US2] Count genome‑wide significant SNPs (`code/utils/count_significant.py`) – SC‑001  
  *Input*: `data/processed/gwas_results_fdr.tsv`.  
  *Output*: `data/processed/significant_snp_count.json` (`significant_count`: integer).  
  *Verification*: JSON exists and the integer equals the number of rows where `SIGNIFICANT` is true.

---  

## Phase 4 – Machine‑learning validation & polygenic risk  

- [ ] **T016** [US3] LASSO logistic regression with 5‑fold CV (`code/04_lasso_validation.py`) – FR‑006  
  *Input*: `gwas_results_fdr.tsv`.  
  *Split*: 80 % training, 20 % held‑out test (`train_test_split` with `random_state=42`, `stratify=y`).  
  *Model*: `LogisticRegression(penalty='l1', solver='saga', max_iter=1000)` inside `StratifiedKFold(n_splits=5, random_state=42)`.  
  *Output*: `data/processed/lasso_auc_report.json` (`auc_value`, `status`, `flag` = `low_power` if AUC < 0.75).  
  *Verification*: JSON exists; `auc_value` is a float in [0,1].

- [ ] **T017** [US3] Phenotype‑permutation null distribution (`code/04_lasso_permutation.py`) – FR‑006  
  *Procedure*: 1 000 permutations of the phenotype label, repeat LASSO CV for each, collect AUCs.  
  *Outputs*: `data/processed/phenotype_permutation_null.json` (`observed_auc`, `null_distribution` list, `p_value`) and an aggregated `data/processed/validation_metrics.json` (`auc`, `null_p_value`, `flag`).  
  *Verification*: both JSON files exist; `null_distribution` length = 1000; `p_value` computed as proportion of null AUC ≥ observed.

- [ ] **T018** [US3] Polygenic risk score calculation & likelihood‑ratio test (`code/05_prs_lr_test.py`) – FR‑007  
  *Input*: Significant SNPs (`Q < 0.05`) from `gwas_results_fdr.tsv`.  
  *PRS*: sum of genotype × log(OR) per colony.  
  *LR test*: compare full model (covariates + PRS) vs covariates‑only using `statsmodels` likelihood‑ratio.  
  *Outputs*: `data/processed/prs_scores.tsv` (colony_id, prs_score, p_value) and `data/processed/prs_lr_test.json` (`chi_sq`, `p_value`, `df`, `significant`).  
  *Verification*: TSV header present; JSON `significant` true iff p < 0.05.

- [ ] **T019** [US3] Functional annotation of significant SNPs (`code/06_annotation.py`) – FR‑008  
  *API*: Ensembl Bees v104 (`[UNRESOLVED-CLAIM: https://rest.ensembl.org/variation/honeybee/ — HTTP 400]<snp_id>?content-type=application/json`).  
  *Input*: SNP list from `gwas_results_fdr.tsv`.  
  *Outputs*: `data/processed/annotation_results.tsv` (`snp_id`, `gene_symbol`, `distance`, `go_terms`) and `data/processed/annotation_errors.log`.  
  *Verification*: TSV exists; any “UNAVAILABLE” or “INTERGENIC” entries are logged with timestamps.

---  

## Phase 5 – Documentation, runtime monitoring & final hand‑off  

- [ ] **T020** [US1] Generate study‑design document with disclaimer (`code/07_document_study_design.py`) – FR‑009  
  *Content*: description of GWAS design, Me value citation, explicit “findings are associational, not causal” statement.  
  *Output*: `data/processed/study_design.md`.  
  *Verification*: markdown contains the required disclaimer text.

- [ ] **T021** [US1] Runtime & memory monitor (`code/08_runtime_monitor.py`) – SC‑004 & SC‑005  
  *Wraps*: the entire pipeline (calls all previous scripts).  
  *Outputs*: `data/processed/runtime_log.json` (`start_time`, `end_time`, `duration_seconds`, `peak_memory_mb`).  
  *Verification*: JSON exists; `duration_seconds` ≤ 21600 (6 h) and `peak_memory_mb` ≤ 7000.

- [ ] **T022** [US1] Update `quickstart.md` with a reproducible, ordered command list that invokes the scripts exactly in the dependency order shown above.  
  *Verification*: Running `bash quickstart.sh` (generated by the quickstart steps) creates a marker file `data/processed/quickstart_success.txt`; the verification script `code/verify_quickstart.py` checks for this file and asserts that the key pipeline outputs (`gwas_results_fdr.tsv`, `lasso_auc_report.json`, `annotation_results.tsv`) exist.

- [ ] **T023** [P] Create a minimal end‑to‑end integration test (`tests/integration/test_end_to_end.py`) that runs the pipeline on a **small real subset** (e.g., first 5 colonies) and asserts the presence of `gwas_results_fdr.tsv`, `lasso_auc_report.json`, and `annotation_results.tsv`.  
  *Verification*: pytest passes; test logs the runtime of the subset (< 30 min).
