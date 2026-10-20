# Tasks: Predicting Bacterial Antibiotic Resistance from Public Genomic Databases

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001-predicting-bacterial-antibiotic-resistan/contracts/`.

---

## Phase 1 – Data acquisition & feature construction (early end‑to‑end run)

- [ ] **T001** [P] [FR‑001] Download *E. coli* and *S. aureus* isolates with AST phenotypes from the NCBI Pathogen Detection dataset, verify checksums, and write raw parquet/FASTA files to `data/raw/`. <!-- FAILED-IN-EXECUTION: src/pipeline/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/pipeline/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/pipeline/download.py exit=1 -->
  *Creates* `data/raw/ncbi_parquet/*.parquet` and `data/raw/assemblies/*.fasta`.  
  *Verification*: `src/pipeline/download.py` exits with status 0, logs sample‑size table `data/processed/sample_sizes.csv`, and records any download/API warnings (FR‑008).  

- [ ] **T002** [P] [FR‑002] Query the CARD API for each isolate, build a binary ARG‑presence matrix, and save as `data/processed/arg_matrix.csv`.   <!-- FAILED-IN-EXECUTION: src/pipeline/extract_baseline.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/pipeline/extract_baseline.py exit=1 -->
  *Creates* `data/processed/arg_matrix.csv`.  
  *Verification*: Row count matches isolates in `sample_sizes.csv`; a checksum column is added; schema validated by `tests/contract/test_arg_matrix_schema.py`.  

- [ ] **T003** [P] [FR‑003] Align each isolate to the species‑specific core reference using `snippy`, pipe the alignment to `snp-sites` to count SNPs per gene/intergenic region, **excluding any SNP that overlaps an ARG locus** (as defined in `arg_matrix.csv`). Output `data/processed/snp_counts.csv`.  
  *Creates* `data/processed/snp_counts.csv`.  
  *Verification*: All isolates with < 90 % core coverage are filtered out (FR‑009); a log `data/processed/alignment_log.txt` records filtered isolates; **`data/processed/snp_overlap_excluded.log` lists the number of SNPs excluded due to ARG overlap**, and the script asserts that this count > 0 when applicable.  

- [ ] **T004** [P] [FR‑003] Detect plasmids with MOB‑suite and transposons with the ISfinder utility, compute the genomic distance from each ARG to the nearest MGE, bin distances (`<1kb`, `1‑5kb`, `>5kb`), and write `data/processed/mge_distances.csv`.  
  *Creates* `data/processed/mge_distances.csv`.  
  *Verification*: Distance bins are integer‑coded; a provenance header lists the MOB‑suite and ISfinder versions used.  

- [ ] **T005** [P] [FR‑010] Perform variance‑threshold filtering, chi‑square ranking, retain the top‑500 non‑redundant features, then scale with `StandardScaler`. Save the scaled matrix as `data/processed/selected_features.npy` and metadata as `data/processed/feature_metadata.json`.  
  *Creates* `data/processed/selected_features.npy`, `data/processed/feature_metadata.json`.  
  *Verification*: Feature count reported in the metadata matches ≤ 500; a checksum file `data/processed/selected_features.sha256` is generated.  

---

## Phase 2 – Baseline and integrated modelling (complete study)

- [ ] **T006** [P] [FR‑004] Hyper‑parameter tune and train a baseline XGBoost classifier (ARG‑only features) using stratified 5‑fold CV (max_depth ∈ {3,5,7}, learning_rate ∈ {0.01,0.1}, n_estimators ∈ {100,200}, reg_lambda ∈ {1,5}, reg_alpha ∈ {0,1}). Save the best model to `data/models/baseline_<species>_<antibiotic>.pkl` and metrics JSON to `data/reports/metrics_baseline_<species>_<antibiotic>.json`.  
  *Creates* model PKL and metrics JSON files.  
  *Verification*: JSON conforms to `contracts/metrics.schema.yaml`; CV folds are stratified (FR‑010).  

- [ ] **T007** [P] [FR‑004] Hyper‑parameter tune and train an integrated XGBoost classifier on the full feature set (`selected_features.npy`) with the same CV scheme. Save model to `data/models/integrated_<species>_<antibiotic>.pkl` and metrics JSON to `data/reports/metrics_integrated_<species>_<antibiotic>.json`.  
  *Creates* model PKL and metrics JSON files.  
  *Verification*: Same schema validation as T006; ensures species‑ and antibiotic‑specific training (FR‑013).  

- [ ] **T008** [P] [FR‑012] Compute per‑fold metric deltas (integrated – baseline) and run a Wilcoxon signed‑rank test to assess significance of the improvement. Record results in `data/reports/paired_fold_test.txt`.  
  *Creates* `data/reports/paired_fold_test.txt`.  
  *Verification*: Test reports a p‑value; if p < 0.05 the improvement is deemed significant (SC‑001).  

---

## Phase 3 – Statistical validation & robustness checks

- [ ] **T009** [P] [FR‑005] For every retained SNP and MGE distance feature, run a Mann‑Whitney U test comparing resistant vs. sensitive isolates, apply Benjamini‑Hochberg FDR correction, and output `data/reports/mannwhitney_results.csv`.  
  *Creates* `data/reports/mannwhitney_results.csv`.  
  *Verification*: Columns include `feature_name`, `raw_p`, `adj_p`, `significant` (adj p < 0.05) (SC‑002).  

- [ ] **T010** [P] [FR‑011] Build a kinship matrix with `pyseer`, perform a phylogeny‑aware permutation test for each SNP/MGE feature, and store results in `data/reports/permutation_results.csv`.  
  *Creates* `data/reports/permutation_results.csv`.  
  *Verification*: Reports permutation‑based p‑values; significant features flagged (SC‑002).  

- [ ] **T011** [P] [FR‑007] Sweep classification probability thresholds {0.3, 0.5, 0.7}, compute false‑positive and false‑negative rates for each model, and write `data/reports/threshold_analysis.json`.  
  *Creates* `data/reports/threshold_analysis.json`.  
  *Verification*: JSON matches `thresholds` schema in `metrics.schema.yaml`; rates are within [0,1] (SC‑004).  

- [ ] **T012** [P] [FR‑006][FR‑014] Generate a comprehensive comparative report (`data/reports/comparative_report.pdf`) that includes:  
  • Delta AUC‑ROC, Precision, Recall, F1‑score between integrated and baseline models (SC‑001)  
  • Power‑analysis summary (required n, observed n, effect size, achieved power, sufficiency flag) (SC‑005)  
  • Edge‑case log excerpts for download/API failures and low‑coverage isolates (FR‑008, FR‑009) (SC‑003)  
  • All figures (ROC curves, feature‑importance heatmaps) under `figures/`.  
  *Creates* PDF and accompanying `data/reports/summary.txt`.  
  *Verification*: The PDF opens without error, contains sections “Performance Comparison”, “Power Analysis”, “Edge‑Case Log”, and “Figures”. `summary.txt` includes a SHA‑256 checksum line for the PDF; script exits with status 0.  

- [ ] **T013** [P] Validate every `metrics_*.json` file against `specs/001-predicting-bacterial-antibiotic-resistan/contracts/metrics.schema.yaml` using `tests/contract/test_metrics_schema.py`. All tests must pass.  
  *Verification*: `pytest -q tests/contract/test_metrics_schema.py` returns exit 0.  

- [ ] **T014** [P] Run an end‑to‑end integration test on a small, real subset (first 50 isolates per species) using the master script `src/pipeline/run_all.py`. The test must complete within 30 min, use ≤ 4 GB RAM, and produce the full set of artefacts listed above (except the large‑scale power‑analysis which runs on the full data).  
  *Creates* a temporary `data/tmp_test/` tree and a log `data/tmp_test/run_log.txt`.  
  *Verification*: Log contains “END‑TO‑END SUCCESS”, runtime < 1800 s, peak memory < 4 GB; CI test `tests/integration/test_end_to_end.py` passes.  

- [ ] **T015** [P] [SC‑003] Execute the full pipeline (`src/pipeline/run_all.py`) on the complete dataset and record total wall‑clock runtime and peak RAM usage (using `time` and `psutil`). Verify that runtime ≤ 6 h and peak memory ≤ 7 GB.  
  *Creates* `data/reports/full_runtime_report.txt`.  
  *Verification*: The report contains lines `Runtime: HH:MM:SS` and `PeakMemory: X.Y GB`; a validation script checks both values against the limits and exits with status 0.  

- [ ] **T016** [P] [FR‑030] Ensure all pipeline scripts pin a fixed random seed (e.g., 42) for `random`, `numpy`, `torch` (if used), and `scikit‑learn`. Add a utility `src/utils/set_seed.py` that sets the seeds and logs “Seed set to 42”. All scripts must import this utility at start.  
  *Creates* `src/utils/set_seed.py`.  
  *Verification*: Each script logs the seed line; a deterministic checksum of a reference output (e.g., first fold AUC) is compared against a stored hash to confirm reproducibility.  

---

## Phase 4 – Reproducibility, contracts, and final hand‑off

- [ ] **T017** [P] (Previously T013) Validate every `metrics_*.json` file against the schema (remains unchanged).  

- [ ] **T018** [P] (Previously T014) Run the small‑subset integration test (remains unchanged).  

---  

### Dependency mapping (summary)

| Requirement | Covered by Task(s) |
|-------------|--------------------|
| FR‑001 | T001 |
| FR‑002 | T002 |
| FR‑003 | T003, T004 |
| FR‑004 | T006, T007 |
| FR‑005 | T009 |
| FR‑006 | T012 |
| FR‑007 | T011 |
| FR‑008 | T001 (warning handling) |
| FR‑009 | T003, T004 |
| FR‑010 | T005, T006, T007 |
| FR‑011 | T010 |
| FR‑012 | T008 |
| FR‑013 | T006, T007 |
| FR‑014 | T001, T005, T012, T014 |
| FR‑030 (seed pinning) | T016 |
| SC‑001 | T006, T007, T008, T012 |
| SC‑002 | T009, T010 |
| SC‑003 | T015 (runtime/memory) |
| SC‑004 | T011 |
| SC‑005 | T012 |

All tasks remain unchecked; they will be executed in the order shown, respecting data flow and the platform’s CPU‑only constraints. The early tasks (T001‑T005) constitute a runnable minimal pipeline that produces a real result matrix, satisfying the “first end‑to‑end analysis” requirement. Subsequent tasks expand the study to meet the full specification.  