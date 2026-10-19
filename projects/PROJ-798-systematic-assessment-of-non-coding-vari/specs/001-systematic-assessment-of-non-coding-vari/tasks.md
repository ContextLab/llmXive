# Tasks: Systematic Assessment of Non‑Coding Variant Effects on Transcription Factor Binding Affinities

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, contract schemas, and reviewer feedback.  
All tasks follow the canonical checklist format `- [ ] T### [P?] [USx?] description …`. Checked boxes (`[x]`) indicate work that has already passed verification; unchecked boxes indicate work that still needs to be completed or re‑run.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, fully‑real pipeline on a small, real input set and verify that every downstream step can be executed. |
|------|------------------------------------------------------------|

- [ ] T001 [P] [US1] **Create the project directory layout** and record a manifest.  
  *Path*: `code/`, `code/data_ingestion/`, `code/scoring/`, `code/analysis/`, `code/utils/`, `data/raw/`, `data/derived/`, `data/results/`, `tests/unit/`, `tests/integration/`, `tests/contract/`.  
  *Verification*:  
  ```text
  find code data tests -type d | sort > data/results/structure_manifest.txt
  ```  
  The manifest must list every required directory; the CI verifier checks that the file exists and contains at least 11 unique directory paths.

- [ ] T002 [P] [US1] **Create `.gitignore` at the repository root** with the exact exclusion patterns required by the spec.  
  *Path*: `.gitignore` (project root).  
  *Content*:  
  ```text
  data/raw/*
  !data/raw/checksums.json
  !data/raw/source_log.txt
  data/derived/*
  __pycache__/
  .env
  ```  
  *Verification*:  
  ```bash
  git check-ignore data/raw/snps_raw.vcf.gz   # must exit 0
  git check-ignore data/raw/source_log.txt   # must exit 1
  ```

- [ ] T003 [S] [US1] **Define LD‑block identifiers for each SNP and create test package scaffolding**.  
  *Path*: `code/data_ingestion/annotate_ld_blocks.py` and `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/contract/__init__.py`.  
  *Method*: Compute LD blocks (e.g., using a pre‑computed map) and add a `ld_block_id` column to `data/derived/filtered_snps.parquet`. Also create empty `__init__.py` files so pytest can discover packages.  
  *Verification*:  
  1. Load `filtered_snps.parquet` and assert every record has a non‑null `ld_block_id`.  
  2. `python -c "import pkgutil; assert pkgutil.find_loader('tests.unit')"` succeeds.

- [ ] T004 [S] [US1] **Implement dbSNP common‑SNP fetch** (MAF > 1 %) for GRCh38 build 155 with robust error handling.  
  *Path*: `code/data_ingestion/fetch_dbsnp.py`.  
  *Behavior*: Stream each chromosome VCF (`chr*.vcf.gz`) from `ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/`, filter by `MAF >= 0.01`, write to `data/raw/snps_raw.parquet`. Log every downloaded URL, build version, timestamp, and SHA‑256 checksum in `data/raw/source_log.txt`. Fail loudly (raise) if any download fails.  
  *Verification*:  
  ```bash
  python -m code.data_ingestion.fetch_dbsnp   # must exit 0
  parquet-tools schema data/raw/snps_raw.parquet | grep maf
  grep -E "ftp://.*dbSNP" data/raw/source_log.txt
  ```

- [ ] T005 [S] [US1] **Download regulatory region annotations** (ENCODE v4 promoters/enhancers, Roadmap Epigenomics) and the GRCh38 reference genome.  
  *Path*: `code/data_ingestion/fetch_annotations.py`.  
  *Artifacts*: `data/raw/regulatory_regions.bed` (merged, sorted, BED‑3), `data/raw/hg38.fa` and `data/raw/hg38.fa.fai`. All URLs and SHA‑256 checksums appended to `data/raw/source_log.txt`.  
  *Verification*:  
  ```bash
  bedtools intersect -a data/raw/regulatory_regions.bed -b data/raw/regulatory_regions.bed -u | wc -l
  samtools faidx data/raw/hg38.fa
  grep -E "ENCODE|Roadmap|hg38" data/raw/source_log.txt
  ```

- [ ] T006 [S] [US1] **Fetch the JASPAR 2024 human PWM collection** and parse it into a structured JSON for fast lookup.  
  *Path*: `code/data_ingestion/fetch_pwms.py`.  
  *Artifact*: `data/raw/jaspar_pwms.json` (list of objects with `pwm_id`, `tf_name`, `matrix`, `length`). Log URL and checksum in `source_log.txt`.  
  *Verification*:  
  ```bash
  python -c "import json, pathlib; data=json.load(open('data/raw/jaspar_pwms.json')); assert all(p['length']>=6 for p in data)"
  grep -E "JASPAR.*2024" data/raw/source_log.txt
  ```

- [ ] T007 [P] [US1] **Filter SNPs to regulatory regions** and generate a GC‑matched non‑regulatory control set.  
  *Path*: `code/data_ingestion/filter_regions.py`.  
  *Outputs*:  
  - `data/derived/filtered_snps.parquet` (conforms to `snp_schema.schema.yaml`, `is_regulatory=True`).  
  - `data/derived/gc_matched_controls.parquet` (conforms to `control_set_schema.schema.yaml`).  
  - `data/results/sc001_proportion_regulatory.json` (ratio of regulatory SNPs to total raw SNPs).  
  *Verification*:  
  1. Load `filtered_snps.parquet` and confirm every record overlaps `regulatory_regions.bed` by ≥ 1 bp.  
  2. Assert the proportion in `sc001_proportion_regulatory.json` is > 0.0.  
  3. Validate both Parquet files against their JSON‑Schema contracts using `jsonschema`.

- [ ] T008 [P] [US1] **Assign stratification identifiers** to each filtered SNP.  
  *Path*: `code/data_ingestion/annotate_strata.py`.  
  *Method*: Create a composite `stratum_id` based on GC‑content bin (width 0.05) and distance‑to‑nearest‑TSS bin (10 kb). Write back to `data/derived/filtered_snps.parquet`.  
  *Verification*: The Parquet schema contains `stratum_id`; a sanity check confirms multiple distinct `stratum_id` values are present.

- [ ] T009 [P] [US2] **Implement PWM scoring and ΔScore calculation** (dynamic window).  
  *Path*: `code/scoring/pwm_scorer.py` (scoring) and `code/scoring/delta_calculator.py` (ΔScore + flag).  
  *Behavior*: For each SNP–TF pair, extract a sequence window of length equal to the PWM (centered on the variant) from `hg38.fa`, compute log‑odds scores for reference and alternate alleles, store `delta_score` and `is_large_magnitude` (|Δ| ≥ 2 bits).  
  *Verification*:  
  1. Unit tests in `tests/unit/test_pwm_scorer.py` compare scores for a hand‑crafted example against a manual calculation.  
  2. A test asserts that `window_size` equals the PWM’s `length`.  
  3. Validate the output of a test run against `contracts/score_schema.schema.yaml` using `jsonschema`.

- [ ] T010 [P] [US2] **Run a thin end‑to‑end scoring pass** on a small, real chromosome subset (e.g., chr22) to produce a real result file.  
  *Path*: `code/main.py --stage score --chroms 22`.  
  *Output*: `data/derived/sample_scores.parquet` (conforms to `score_schema.schema.yaml`).  
  *Verification*: The file contains ≥ 100 rows; a spot‑check script validates that the first row’s `window_size` matches the corresponding PWM length and that `delta_score` is a finite number.

---

## Phase 2 – Complete the study and validate evidence  

| Goal | Full‑genome analysis, statistical testing, and result generation. |
|------|-------------------------------------------------------------------|

- [ ] T011 [S] [US3] **Ingest GWAS Catalog lead SNPs** and annotate the filtered SNP dataset.  
  *Path*: `code/analysis/fetch_gwas.py`.  
  *Artifact*: `data/raw/gwas_lead_snps.bed`; the script updates `data/derived/filtered_snps.parquet` with a boolean `is_gwas_lead`. All download URLs, version tags, and checksums are appended to `source_log.txt`.  
  *Verification*: After run, a query on the Parquet file shows at least one SNP with `is_gwas_lead=True`; the script exits with non‑zero status if the download fails.

- [ ] T012 [S] [US3] **Perform the permutation‑based KS test** for each TF using the GC‑matched control set.  
  *Path*: `code/analysis/ks_enrichment.py`.  
  *Method*:  
  1. For each TF, split ΔScore values into GWAS‑inside vs GC‑matched control set (full unfiltered distribution).  
  2. Compute the observed KS statistic and p‑value.  
  3. Generate **500** permutations by shuffling the `is_gwas_lead` labels **stratified by `stratum_id`** (preserving GC/TSS context) **jointly across all TFs** to satisfy West‑Stephens max‑T requirements.  
  4. The `is_large_magnitude` flag is **not** used to filter SNPs for this test.  
  *Outputs*: `data/derived/ks_null.npy` (null matrix) and `data/derived/ks_observed.parquet`.  
  *Verification*: Unit test `tests/unit/test_ks_permutation.py` confirms that each permutation preserves the exact number of GWAS‑positive labels per stratum and that a synthetic dataset with a known shift yields a KS p‑value < 0.01.

- [ ] T013 [S] [US3] **Aggregate results, apply West‑Stephens max‑T FDR correction, and run the Tail‑Enrichment test**.  
  *Path*: `code/analysis/aggregate_and_fdr.py`.  
  *Steps*:  
  1. Load `ks_observed.parquet` and the KS null matrix; compute the max‑T null distribution across TFs for each permutation.  
  2. Derive West‑Stephens corrected p‑values (`p_value_ks_corrected`).  
  3. Independently compute the Tail‑Enrichment statistic (proportion of |Δ| ≥ 2 bits inside vs outside GWAS) and its permutation‑based p‑value.  
  4. `is_large_magnitude` is used **only** as the target variable for the proportion test; it does **not** filter the input population.  
  5. Calculate final SC‑001 proportion (scored/raw) and save to `data/results/sc001_final.json`.  
  6. Merge per‑TF results into `data/derived/enrichment_results.parquet`.  
  *Verification*: Validate `enrichment_results.parquet` against both `contracts/enrichment_result_schema.schema.yaml` and `contracts/enrichment_schema.schema.yaml` using `jsonschema`.

- [ ] T014 [P] [US3] **Generate result tables and figures** directly from validated outputs.  
  *Path*: `code/visualization/generate_reports.py`.  
  *Artifacts*:  
  - `data/results/results_summary.csv` (per‑TF table with KS statistic, corrected p‑value, tail proportion, significance flags).  
  - `data/results/figures/tf_heatmap.png` (heatmap of mean |Δ| per TF).  
  - `data/results/figures/delta_distribution.png` (overlaid KDEs for GWAS‑inside vs outside).  
  *Verification*:  
  ```bash
  python -c "import pandas as pd; df=pd.read_csv('data/results/results_summary.csv'); assert not df.empty"
  file data/results/figures/tf_heatmap.png | grep PNG
  file data/results/figures/delta_distribution.png | grep PNG
  grep -E \"p_value_ks_corrected\" data/results/results_summary.csv
  ```

- [ ] T015 [P] [US3] **Sensitivity analysis & performance logging**.  
  *Path*: `code/analysis/sensitivity.py`.  
  *Actions*:  
  1. Sweep the large‑magnitude cutoff from 0.5 to 4.0 bits in 0.5‑bit increments, re‑run the full enrichment pipeline for each cutoff, and record the number of significant TFs in `data/results/sensitivity_cutoff_sweep.json`.  
  2. Record wall‑clock time and peak RAM per pipeline stage in `data/results/performance_log.json`.  
  *Verification*: The JSON files are well‑formed; `performance_log.json` reports total runtime < 6 h and peak memory < 7 GB on the CI runner.

- [ ] T016 [P] [US3] **Write the methods/results report and verify reproducibility**.  
  *Path*: `data/results/report.md` and `data/results/paper_handoff.md`.  
  *Steps*:  
  1. The report cites the exact versions/URLs logged in `source_log.txt`.  
  2. Run `python -m code.main --full --seed 42` a second time; compute SHA‑256 hashes of all derived files.  
  3. Assert that the hashes match those recorded after the first run.  
  *Verification*: Test script `tests/integration/test_reproducibility.py` performs the re‑run, compares hashes, and exits with status 0 only when they are identical.

- [ ] T017 [P] [US3] **Create the project quickstart guide**.  
  *Path*: `specs/001-systematic-assessment-of-non-coding-vari/quickstart.md`.  
  *Content*: Document the steps to set up the environment, run the data ingestion, scoring, and analysis stages, and verify results. Include exact shell commands that correspond to the entry points in `code/main.py`.  
  *Verification*: The file exists, contains valid commands, and executing the documented commands reproduces the pipeline without errors.

- [ ] T022 [P] [US3] **Compute SC‑001: proportion of SNP‑TF pairs successfully scored**.  
  *Path*: `code/analysis/score_success_rate.py`.  
  *Output*: `data/results/sc001_scoring_success.json` containing the ratio (`scored_pairs / total_possible_pairs`).  
  *Verification*: The JSON contains a numeric `proportion_scored` between 0 and 1; the value is cross‑checked against row counts in `data/derived/filtered_snps.parquet` and `data/raw/jaspar_pwms.json`.

- [ ] T018 [P] [US3] **Archive all provenance artifacts** (source logs, checksums, git commit hash) into a single `data/results/provenance.yaml`.  
  *Path*: `code/utils/archive_provenance.py`.  
  *Verification*: The YAML file contains fields `git_commit`, `source_log`, and `checksums` and validates against a minimal schema (`contracts/provenance_schema.schema.yaml`).

- [ ] T019 [P] [US3] **Run the full pipeline from a clean checkout** to demonstrate end‑to‑end reproducibility.  
  *Command*: `python -m code.main --full --seed 42`.  
  *Verification*: After completion, compute SHA‑256 hashes of every file under `data/derived/` and `data/results/`; compare to the hashes recorded in `provenance.yaml`. The CI test `tests/integration/test_full_reproducibility.py` must pass.

- [ ] T020 [P] [US3] **Create a minimal data‑availability statement** describing how external datasets were fetched (FTP URLs, version tags) and where they are stored in the repository.  
  *Path*: `specs/001-systematic-assessment-of-non-coding-vari/data_availability.md`.  
  *Verification*: The file exists, lists all external sources, and matches entries in `source_log.txt`.

---

## Phase 3 – Reproducible results and paper handoff  

| Goal | Provide a clean hand‑off to the paper‑writing stage, ensuring full reproducibility. |
|------|-----------------------------------------------------------------------------------|

- (All tasks in Phase 2 already produce the artefacts required for hand‑off; Phase 3 consists of the provenance archiving (T018), full‑pipeline reproducibility check (T019), and data‑availability statement (T020) listed above.)

---

### Dependency & requirement coverage  

| Requirement | Task(s) | Command to demonstrate |
|------------|---------|--------------------------|
| FR‑001 | T004, T005, T007 | `python -m code.main --stage ingest` |
| FR‑002 / FR‑003 | T009, T010 | `pytest tests/unit/test_pwm_scorer.py` |
| FR‑004 / FR‑005 | T012 | `pytest tests/unit/test_ks_permutation.py` |
| FR‑006 / FR‑007 / FR‑008 | T013 | `python -m code.main --stage analysis` |
| SC‑001 | T022 | `cat data/results/sc001_scoring_success.json` |
| SC‑002 / SC‑003 | T013, T014 | `head data/results/results_summary.csv` |
| NFR‑001 / NFR‑002 | T015 | `cat data/results/performance_log.json` |

**Execution order** (enforced by data flow):  

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T022 → T018 → T019 → T020.
