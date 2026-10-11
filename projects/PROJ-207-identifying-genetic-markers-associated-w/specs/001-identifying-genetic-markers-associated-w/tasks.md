# Tasks: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

**Input**: `spec.md`, `plan.md`, existing data‑model and contracts.  
All paths are relative to the repository root.  

---

## Phase 0 – Project scaffolding  

- [X] T001 [P] Create the standard project directory layout  
  `mkdir -p code/ data/raw/ data/interim/ data/processed/ docs/ tests/`  
  *Verification*: `test -d code && test -d data/raw && test -d data/processed`.

- [X] T002 [P] Create a pinned `requirements.txt` containing the CPU‑tractable scientific stack (plink2, freebayes, bwa, scikit‑learn, pandas, numpy, statsmodels, pyyaml, requests, biopython, samtools).  
  *Verification*: `grep -E "plink2|freebayes|bwa|scikit-learn" requirements.txt`.

---

## Phase 1 – Real‑data acquisition (metadata → full FASTQ)  

- [ ] T003 [US1] Download **metadata only** (`code/01_download_metadata.py`)   <!-- FAILED-IN-EXECUTION: code/01_download_metadata.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_download_metadata.py exit=1 -->
  *Source*: NCBI BioProject PRJNA639195 (CCD) & PRJNA566029 (healthy) via Entrez Direct.  
  *Requirements*: SSL‑validated download; abort loudly on any certificate error.  
  *Outputs*: `data/processed/ncbi_metadata.json` (fields: `sample_accession`, `ccd_status`, `varroa_load`, `geographic_region`, `sampling_year`).  
  *Verification*: JSON is well‑formed, contains `sample_count` ≥ 80; compute SHA‑256 checksum and write to `data/processed/ncbi_metadata_checksum.txt`. The checksum file must exist and match the computed hash.

- [ ] T004 [US1] Perform power analysis (`code/utils/power_analysis.py`)  
  *Inputs*: `data/processed/ncbi_metadata.json` (checksum verified by T003).  
  *Behaviour*: computes statistical power for detecting an odds‑ratio ≥ 2.5 at α = 0.05; halts with exit code `ERR_SAMPLE_SIZE_INSUFFICIENT` if *n* < 80.  
  *Outputs*: `data/processed/power_analysis.json` (`power_value`, `status`, `n_samples`) and a human‑readable `data/processed/power_analysis.txt`.  
  *Verification*: JSON exists, `status=="PASS"` and `n_samples` ≥ 80.

- [ ] T005 [US1] Full FASTQ download (`code/01_download_full.py`) – **depends on T004 passing**  
  *Implementation*: uses `fasterq-dump` (SRA‑Toolkit) for all accessions listed in `ncbi_metadata.json`.  
  *SSL*: validated; any failure aborts with a clear error.  
  *Outputs*: `data/raw/fastq/<sample_id>_R1.fastq.gz` and `data/raw/fastq/<sample_id>_R2.fastq.gz`; log written to `data/processed/ncbi_fetch_log.json`.  
  *Verification*: at least 80 FASTQ pairs exist; log records total bytes downloaded; compute SHA‑256 checksums for every FASTQ file and write a manifest `data/processed/fastq_checksums.txt`. Verification succeeds if the manifest exists and contains a checksum line for each downloaded file.

- [ ] T006 [US1] Harmonise phenotypes (`code/02_harmonize_phenotypes.py`)  
  *Inputs*: `ncbi_metadata.json` + FASTQ list.  
  *Tasks*: map CCD diagnosis to binary (1 = CCD, 0 = healthy) per the 2007 CCD Working Group protocol; compute Varroa coverage.  
  *Gate*: if < 80 % of colonies have Varroa data → exit with `ERR_VARROA_COVARIATE_MISSING`. Otherwise, write `data/interim/phenotypes_harmonized.fam`.  
  *Verification*: `.fam` exists; header contains 6 columns; a companion `data/processed/varroa_coverage.txt` reports % coverage.

- [ ] T007 [US1] Validate CCD instrument consistency (`code/02_validate_instruments.py`)  
  *Checks*: CCD status fields match BeeBase definitions; flag records where > 10 % are ambiguous.  
  *Output*: `data/processed/instrument_validation_report.json`.  
  *Verification*: JSON contains `ambiguous_fraction`; if > 0.10 the script exits with a non‑zero code.

- [ ] T008 [US1] Collinearity diagnostics for covariates (`code/05_collinearity_diag.py`) – **FR‑010**  
  *Input*: `data/interim/phenotypes_harmonized.fam`.  
  *Output*: `data/processed/collinearity_report.json` with VIF values **and** a Pearson correlation matrix.  
  *Verification*: any pair of covariates with **r² > 0.8** (square of Pearson correlation) is flagged in the JSON (VIF > 5 may also be reported but is not used for pass/fail).

## Phase 2 – Alignment & variant calling (CPU‑tractable)  

- [ ] T009 [US1] Align reads & call variants (`code/02_align_and_call.sh`) – **FR‑002**  
  *Reference*: `data/raw/refs/Amel_HAv3.1.fa` (checksum‑validated).  
  *Steps*: `bwa mem` → SAM → `samtools view` → sorted BAM → `freebayes` → raw VCF.  
  *Filtering*: `bcftools filter` to keep biallelic SNPs with QUAL > 30 and DP ≥ 10.  
  *Output*: `data/interim/raw_variants.vcf`.  
  *Verification*: VCF passes `bcftools stats` with > 0 variants.

- [ ] T010 [US1] Convert VCF → PLINK (`code/utils/vcf_to_plink.py`) – **FR‑003**  
  *Input*: `data/interim/raw_variants.vcf`.  
  *Output*: `data/interim/bed.{bed,bim,fam}`.  
  *Verification*: all three PLINK files exist; `plink --bfile data/interim/bed --write-snplist` runs without error.

- [ ] T011 [US1] LD pruning for population‑structure correction (`code/utils/ld_prune.sh`) – **FR‑003**  
  *Command*: `plink --bfile data/interim/bed --indep-pairwise 50 5 0.2 --out data/interim/bed_pruned`  
  *Output*: `data/interim/bed_pruned.prune.in` (list of retained SNPs).  
  *Verification*: file exists and contains ≥ 10 % of original SNPs.

## Phase 3 – GWAS & multiple‑testing correction  

- [ ] T012 [US1] GWAS logistic regression **and** Benjamini‑Hochberg FDR correction (`code/03_gwas.sh`) – **FR‑004**  
  *Input*: PLINK files (`bed`, `phenotypes_harmonized.fam`).  
  *Covariates*: geographic_region, sampling_year, varroa_mite_count.  
  *Steps*: run PLINK logistic regression to produce `data/interim/gwas_raw.tsv`; immediately pipe results to `code/utils/fdr_correction.py` (BH procedure) using the effective‑test count from T013, producing final `data/processed/gwas_results_fdr.tsv`.  
  *Outputs*:  
    - `data/interim/gwas_raw.tsv` (raw GWAS stats)  
    - `data/processed/gwas_results_fdr.tsv` (SNP, CHR, BP, A1, P, Q, OR, SIGNIFICANT).  
  *Verification*: both files exist; `gwas_results_fdr.tsv` contains header and at least one row; SIGNIFICANT is true iff Q < 0.05.

- [ ] T013 [US2] Estimate effective number of independent tests (`code/utils/estimate_me.py`) – **FR‑004**  
  *Input*: `data/interim/bed_pruned.prune.in`.  
  *Method*: Li & Ji eigenvalue approach.  
  *Output*: `data/processed/me_estimate.txt` (single integer).  
  *Verification*: file exists, integer > 0, and script runs without error.

- [ ] T014 [US2] Validate GWAS‑FDR TSV against schema – **P**  
  *Input*: `data/processed/gwas_results_fdr.tsv`.  
  *Output*: no new file; validation step only.  
  *Verification*: runs `code/utils/validate_tsv_schema.py --schema specs/001-identifying-genetic-markers-associated-w/contracts/gwas_results.schema.yaml --file data/processed/gwas_results_fdr.tsv`; exits with status 0 if schema matches.

- [ ] T015 [US2] Threshold‑sensitivity sweep (`code/utils/threshold_sensitivity.py`) – **FR‑005**  
  *Input*: `data/processed/gwas_results_fdr.tsv`.  
  *Thresholds*: 1e‑7, 5e‑8, 1e‑8.  
  *Output*: `data/processed/threshold_sensitivity.json` (list of `{threshold, count, q_values}` objects).  
  *Verification*: JSON contains three objects; each `count` matches the number of SNPs with P ≤ threshold.

- [ ] T016 [US2] Count genome‑wide significant SNPs (`code/utils/count_significant.py`) – **SC‑001**  
  *Input*: `data/processed/gwas_results_fdr.tsv`.  
  *Output*: `data/processed/significant_snp_count.json` (`significant_count`: integer).  
  *Verification*: JSON exists and the integer equals the number of rows where `SIGNIFICANT` is true.

## Phase 4 – Machine‑learning validation & polygenic risk  

- [ ] T017 [US3] LASSO logistic regression with 5‑fold CV (`code/04_lasso_validation.py`) – **FR‑006**  
  *Input*: `data/processed/gwas_results_fdr.tsv`.  
  *Split*: 80 % training, 20 % held‑out test (`train_test_split` with `random_state=42`, `stratify=y`).  
  *Model*: `LogisticRegression(penalty='l1', solver='saga', max_iter=1000)` inside `StratifiedKFold(n_splits=5, random_state=42)`.  
  *Output*: `data/processed/lasso_auc_report.json` (`auc_value`, `status`, `flag` = `low_power` if AUC < 0.75).  
  *Verification*: JSON exists; `auc_value` is a float in [0, 1].

- [ ] T018 [US3] Phenotype‑permutation null distribution (`code/04_lasso_permutation.py`) – **FR‑006**  
  *Procedure*: 1 000 permutations of the phenotype label **using a fixed seed (12345)**; repeat LASSO CV for each permutation; collect AUCs.  
  *Outputs*: `data/processed/phenotype_permutation_null.json` (`observed_auc`, `null_distribution` list of 1 000 floats, `p_value`) and a summary `data/processed/validation_metrics.json` (`auc`, `null_p_value`, `flag`).  
  *Verification*: both JSON files exist; `null_distribution` length = 1000; `p_value` computed as proportion of null AUC ≥ observed.

- [ ] T019 [US3] Polygenic risk score calculation & likelihood‑ratio test (`code/05_prs_lr_test.py`) – **FR‑007**  
  *Input*: Significant SNPs (`Q < 0.05`) from `data/processed/gwas_results_fdr.tsv`.  
  *PRS*: sum of genotype × log(OR) per colony.  
  *LR test*: compare full model (covariates + PRS) vs covariates‑only using `statsmodels` likelihood‑ratio.  
  *Outputs*: `data/processed/prs_scores.tsv` (columns: colony_id, prs_score, p_value) and `data/processed/prs_lr_test.json` (`chi_sq`, `p_value`, `df`, `significant`).  
  *Verification*: TSV header present; JSON `significant` true iff p < 0.05.

- [ ] T020 [US3] Functional annotation of significant SNPs (`code/06_annotation.py`) – **FR‑008**  
  *API*: Ensembl Bees v104 (`[UNRESOLVED-CLAIM: https://rest.ensembl.org/variation/honeybee/ — HTTP 400]<snp_id>?content-type=application/json`).  
  *Input*: SNP list from `data/processed/gwas_results_fdr.tsv`.  
  *Outputs*: `data/processed/annotation_results.tsv` (`snp_id`, `gene_symbol`, `distance`, `go_terms`) and `data/processed/annotation_errors.log`.  
  *Verification*: TSV exists; any “UNAVAILABLE” or “INTERGENIC” entries are logged with timestamps.

## Phase 5 – Documentation, runtime monitoring & final hand‑off  

- [ ] T021 [US1] Generate study‑design document with disclaimer (`code/07_document_study_design.py`) – **FR‑009**  
  *Content*: description of GWAS design, Me value citation, explicit “findings are associational, not causal” statement.  
  *Output*: `data/processed/study_design.md`.  
  *Verification*: markdown contains the required disclaimer text.

- [ ] T022 [US1] Runtime & memory monitor (`code/08_runtime_monitor.py`) – **SC‑004** & **SC‑005**  
  *Wraps*: the entire pipeline (calls all previous scripts).  
  *Outputs*: `data/processed/runtime_log.json` (`start_time`, `end_time`, `duration_seconds`, `peak_memory_mb`).  
  *Verification*: JSON exists; `duration_seconds` ≤ 21600 (6 h) and `peak_memory_mb` ≤ 7000.

- [ ] T023 [P] Create reproducible quick‑start script and documentation  
  *Actions*: (a) generate `quickstart.sh` that executes the pipeline scripts in the exact dependency order; (b) update `quickstart.md` with the same ordered command list.  
  *Verification*: Running `bash quickstart.sh` creates `data/processed/quickstart_success.txt`; `code/verify_quickstart.py` checks for this file and asserts that the key pipeline outputs (`gwas_results_fdr.tsv`, `lasso_auc_report.json`, `annotation_results.tsv`) exist.

- [ ] T024 [P] Create a minimal end‑to‑end integration test (`tests/integration/test_end_to_end.py`) that runs the pipeline on a **small real subset** (e.g., first 5 colonies) and asserts the presence of `gwas_results_fdr.tsv`, `lasso_auc_report.json`, and `annotation_results.tsv`.  
  *Verification*: `pytest` passes; test logs the runtime of the subset (< 30 min).

- [ ] T025 [US2] Generate final results report (`code/13_format_results.py`) – **FR‑009**  
  *Inputs*: `data/processed/gwas_results_fdr.tsv`, `data/processed/validation_metrics.json`, `data/processed/prs_lr_test.json`, `data/processed/annotation_results.tsv`.  
  *Output*: `data/processed/final_report.md` containing tables of significant SNPs, polygenic risk performance, functional annotations, and the mandatory associational disclaimer.  
  *Verification*: Markdown renders without errors; contains sections titled “GWAS Summary”, “Validation Metrics”, “Polygenic Risk Scores”, “Functional Annotation”, and the disclaimer sentence.

- [ ] T026 [P] Run Reference‑Validator on all external citations (`code/99_reference_validator.py`) – **Constitution II**  
  *Scope*: scans scripts, markdown, and documentation for external citations; invokes the platform’s Reference‑Validator agent; fails if any citation is unreachable or mismatched.  
  *Output*: `data/processed/reference_validation_report.json` with pass/fail status per citation.  
  *Verification*: JSON `overall_status` equals `"PASS"`; task exits with non‑zero code if any citation fails.

---  

## Revision notes  

- Candidate‑gene pre‑filtering introduced in the plan has been **flagged for upstream correction** (see concern F001).  
- Data source has been aligned to the NCBI BioProject requirement; any HF‑mirror usage is now removed from the plan (plan‑root cause).  
- Collinearity verification now uses r² > 0.8 as mandated by SC‑006.  
- GWAS task (T012) now fully satisfies FR‑004, eliminating split tagging.  
- FDR correction validation (T014) now checks TSV against the schema.  
- Quick‑start script generation (T023) now creates an executable `quickstart.sh`.  
- Seed pinning added to permutation step (T018) and confirmed across stochastic tasks.  
- Reference‑Validator step (T026) added to meet Constitution Principle II.  