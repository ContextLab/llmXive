# Tasks: Systematic Assessment of Non‑Coding Variant Effects on Transcription Factor Binding Affinities

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, contract schemas, and reviewer feedback.  
All tasks follow the canonical checklist format `- [ ] T### [P?] [USx?] description …` with explicit file paths and verification steps indented beneath each item.

---

## Phase 1 – Data acquisition & preparation  

| Goal | Obtain all real input resources, filter to the regulatory context, and create the foundational Parquet datasets required for downstream scoring. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [X] T001 [P] [US1] **Create the project directory layout**.  
  *Path*: `code/`, `code/data_ingestion/`, `code/scoring/`, `code/analysis/`, `code/visualization/`, `code/utils/`, `data/raw/`, `data/derived/`, `data/results/`, `tests/unit/`, `tests/integration/`, `tests/contract/`.  
  *Verification*:  
  ```bash
  find code data tests -type d | sort > data/results/structure_manifest.txt
  wc -l < data/results/structure_manifest.txt   # must be ≥ 11
  ```

- [ ] T002 [P] [US1] **Create `.gitignore` at the repository root** with the exact exclusion patterns required by the specification.   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
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
  git check-ignore data/raw/snps_raw.vcf.gz   # exit code 0
  git check-ignore data/raw/source_log.txt   # exit code 1
  ```

- [ ] T003 [P] [US1] **Download raw genomic resources** (dbSNP VCF, ENCODE/Roadmap regulatory BED, hg38 reference FASTA) with streaming, checksum logging, and robust error handling (retries, explicit failure on missing file).  
  *Path*: `code/data_ingestion/fetch_raw_resources.py`.  
  *Artifacts*:  
  - `data/raw/snps_raw.vcf.gz` (streamed from `ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/`).  
  - `data/raw/regulatory_regions.bed` (merged ENCODE v4 + Roadmap).  
  - `data/raw/hg38.fa` and `data/raw/hg38.fa.fai`.  
  - `data/raw/source_log.txt` (URL, version, SHA‑256 for each file).  
  *Verification*:  
  ```bash
  python -m code.data_ingestion.fetch_raw_resources   # must exit 0
  grep -E "ftp://.*dbSNP|ENCODE|Roadmap|hg38" data/raw/source_log.txt
  sha256sum data/raw/snps_raw.vcf.gz data/raw/hg38.fa
  ```

- [ ] T004 [P] [US1] **Fetch the full JASPAR 2024 human PWM collection** (no sub‑sampling) and store it in a structured JSON file for fast lookup.  
  *Path*: `code/data_ingestion/fetch_jaspar_pwms.py`.  
  *Artifact*: `data/raw/jaspar_pwms.json`.  
  *Verification*:  
  ```bash
  python -c "import json, sys; data=json.load(open('data/raw/jaspar_pwms.json')); assert len(data) > 2000"
  grep -E "JASPAR.*2024" data/raw/source_log.txt
  ```

- [ ] T005 [P] [US1] **Prepare the filtered SNP dataset**:  
  1. Stream‑filter `snps_raw.vcf.gz` to retain only common human SNPs (MAF ≥ 0.01) that overlap at least one regulatory interval (≥ 1 bp).  
  2. Generate a GC‑matched non‑regulatory control set (± 2 % GC tolerance).  
  3. Assign LD‑block identifiers (using a pre‑computed map) and composite stratification IDs (GC‑content bin + TSS‑distance bin).  
  *Outputs*:  
  - `data/derived/filtered_snps.parquet` (conforms to `snp_schema.schema.yaml`, `is_regulatory=True`).  
  - `data/derived/gc_matched_controls.parquet` (conforms to `control_set_schema.schema.yaml`).  
  *Verification*:  
  ```bash
  python -c "import pyarrow.parquet as pq; df=pq.read_table('data/derived/filtered_snps.parquet').to_pandas(); assert df['is_regulatory'].all()"
  python -c "import jsonschema, json; schema=json.load(open('specs/001-systematic-assessment-of-non-coding-vari/contracts/snp_schema.schema.yaml')); jsonschema.validate(instance=json.loads(df.head(1).to_json(orient='records')[0]), schema=schema)"
  ```

- [ ] T006 [P] [US2] **Implement PWM scoring and ΔScore calculation** (dynamic window equal to PWM length) and flag large‑magnitude changes.  
  *Path*: `code/scoring/pwm_scorer.py` (scoring) and `code/scoring/delta_calculator.py` (ΔScore + `is_large_magnitude`).  
  *Behavior*: For each SNP‑TF pair, extract a sequence window centered on the variant from `hg38.fa`, compute log‑odds scores for reference and alternate alleles, store `delta_score`, `is_large_magnitude` (|Δ| ≥ 2 bits), and `window_size`.  
  *Verification*:  
  ```bash
  pytest tests/unit/test_pwm_scorer.py   # must pass
  head -n 1 data/derived/sample_scores.parquet   # check columns include window_size and delta_score
  ```

- [ ] T007 [P] [US2] **Run a thin end‑to‑end scoring pass** on a small real chromosome (e.g., chr22) to produce a real sample result file.  
  *Command*: `python -m code.main --stage score --chroms 22`.  
  *Output*: `data/derived/sample_scores.parquet` (conforms to `score_schema.schema.yaml`).  
  *Verification*:  
  ```bash
  parquet-tools rowcount data/derived/sample_scores.parquet   # ≥ 100 rows
  python -c "import pyarrow.parquet as pq; tbl=pq.read_table('data/derived/sample_scores.parquet'); assert tbl.column('window_size').to_pylist()[0] == tbl.column('pwm_length').to_pylist()[0]"
  ```

- [ ] T020 [P] [US2] **Run full‑scale scoring across all chromosomes** to generate the complete SNP‑TF score matrix.  
  *Command*: `python -m code.main --stage score --chroms all`.  
  *Output*: `data/derived/scores.parquet` (conforms to `score_schema.schema.yaml`).  
  *Verification*:  
  ```bash
  parquet-tools rowcount data/derived/scores.parquet   # ≥ 1,000,000 rows (full dataset)
  python -c "import pyarrow.parquet as pq; tbl=pq.read_table('data/derived/scores.parquet'); assert 'delta_score' in tbl.column_names"
  ```
  *Note*: This task must complete before enrichment analysis (T009).

---

## Phase 2 – GWAS annotation & statistical enrichment  

| Goal | Add disease‑association information, perform permutation‑based enrichment testing, and produce corrected significance metrics. |
|------|------------------------------------------------------------------------------------------------------------------------------|

- [ ] T008 [US3] **Ingest GWAS Catalog lead SNPs and annotate the filtered SNP dataset** without in‑place mutation.  
  *Path*: `code/analysis/fetch_gwas.py`.  
  *Artifact*: `data/raw/gwas_lead_snps.bed`; the script reads `data/derived/filtered_snps.parquet` and writes a new file `data/derived/filtered_snps_with_gwas.parquet` that includes a boolean `is_gwas_lead` column.  
  *Verification*:  
  ```bash
  python -c "import pyarrow.parquet as pq; df=pq.read_table('data/derived/filtered_snps_with_gwas.parquet').to_pandas(); assert df['is_gwas_lead'].any()"
  grep -E "GWAS Catalog" data/raw/source_log.txt
  ```

- [ ] T009 [P] [US3] **Perform full statistical enrichment analysis**:  
  1. Compute per‑TF ΔScore distributions for SNPs inside GWAS loci vs. the GC‑matched control set (full, unfiltered).  
  2. Run **100** stratified permutations of the `is_gwas_lead` label (preserving `stratum_id` and LD‑block structure) to build a null KS distribution.  
  3. Apply the **West‑Stephens max‑T** procedure across all TFs to obtain FDR‑adjusted KS p‑values.  
  4. Compute the tail‑enrichment test (proportion of |ΔScore| ≥ 2 bits) with the same permutation scheme.  
  *Inputs*: `data/derived/scores.parquet`, `data/derived/filtered_snps_with_gwas.parquet`, `data/derived/gc_matched_controls.parquet`.  
  *Outputs*:  
  - `data/derived/ks_null.npy` (null matrix).  
  - `data/derived/ks_observed.parquet`.  
  - `data/derived/enrichment_results.parquet` (conforms to both `enrichment_result_schema.schema.yaml` and `enrichment_schema.schema.yaml`).  
  *Verification*:  
  ```bash
  pytest tests/unit/test_ks_permutation.py   # checks stratified label preservation and known‑shift detection
  python -c "import pyarrow.parquet as pq; pq.read_table('data/derived/enrichment_results.parquet').schema"   # schema validation passes
  ```

- [ ] T010 [P] [US3] **Generate result tables and figures** directly from validated outputs.  
  *Path*: `code/visualization/generate_reports.py`.  
  *Artifacts*:  
  - `data/results/results_summary.csv` (per‑TF table with KS statistic, corrected p‑value, tail proportion, significance flags).  
  - `data/results/figures/tf_heatmap.png` (heatmap of mean |ΔScore| per TF).  
  - `data/results/figures/delta_distribution.png` (overlaid KDEs for GWAS‑inside vs. control).  
  *Verification*:  
  ```bash
  head -n 5 data/results/results_summary.csv
  file data/results/figures/tf_heatmap.png | grep PNG
  file data/results/figures/delta_distribution.png | grep PNG
  grep -E "p_value_ks_corrected" data/results/results_summary.csv
  ```

- [ ] T011 [P] [US3] **Compute SC‑001: proportion of SNP‑TF pairs successfully scored** and store as JSON.  
  *Path*: `code/analysis/score_success_rate.py`.  
  *Output*: `data/results/sc001_scoring_success.json` containing `proportion_scored`.  
  *Verification*:  
  ```bash
  cat data/results/sc001_scoring_success.json | python -c "import json, sys; obj=json.load(sys.stdin); assert 0.0 <= obj['proportion_scored'] <= 1.0"
  ```

- [ ] T012 [P] [US3] **Conduct sensitivity analysis & performance profiling**.  
  *Path*: `code/analysis/sensitivity.py`.  
  *Actions*:  
  1. Sweep the large‑magnitude cutoff from 0.5 to 4.0 bits (0.5‑bit steps), re‑run the full enrichment pipeline for each cutoff, and record the number of TFs declared significant.  
  2. Log wall‑clock time and peak RAM per pipeline stage.  
  *Outputs*: `data/results/sensitivity_cutoff_sweep.json`, `data/results/performance_log.json`.  
  *Verification*: Both JSON files must be syntactically valid and `performance_log.json` report `total_runtime_seconds < 21600` and `peak_memory_gb < 7`.

- [ ] T018 [P] [US3] **Flag TFs with insufficient PWM matches** (fewer than 10 matches in regulatory regions).  
  *Path*: `code/analysis/flag_insufficient_tfs.py`.  
  *Output*: `data/results/insufficient_tf_flags.csv` listing `motif_id`, `tf_name`, `match_count`.  
  *Verification*:  
  ```bash
  csvcut -c match_count data/results/insufficient_tf_flags.csv | awk '{if(NR>1) exit $1>=10}'
  ```

- [ ] T019 [P] [US3] **Verify exclusion of non‑ACGT SNPs** before any scoring step.  
  *Path*: `code/analysis/validate_alleles.py`.  
  *Verification*:  
  ```bash
  python -c "import pyarrow.parquet as pq, re; df=pq.read_table('data/derived/filtered_snps.parquet').to_pandas(); assert df['reference_allele'].apply(lambda x: re.fullmatch('[ACGT]', x)).all(); assert df['alternate_allele'].apply(lambda x: re.fullmatch('[ACGT]', x)).all()"
  ```

---

## Phase 3 – Reproducibility, hand‑off, and documentation  

| Goal | Produce fully reproducible artefacts, provenance, and user‑facing documentation for the downstream paper pipeline. |
|------|------------------------------------------------------------------------------------------------------------------------|

- [ ] T016 [P] [US3] **Run the full pipeline from a clean checkout** to demonstrate end‑to‑end reproducibility for the verifier.  
  *Command*: `python -m code.main --full --seed 42`.  
  *Post‑run check*: Compute SHA‑256 hashes of all files in `data/derived/` and `data/results/` and compare to the hashes stored in `provenance.yaml`.  
  *Verification*: `tests/integration/test_full_reproducibility.py` performs the hash comparison; it must pass.

- [ ] T015 [P] [US3] **Archive all provenance artefacts** (download URLs, version tags, SHA‑256 checksums, git commit hash) into a single YAML file.  
  *Path*: `code/utils/archive_provenance.py` → `data/results/provenance.yaml`.  
  *Verification*:  
  ```bash
  python -c "import yaml, sys; yaml.safe_load(open('data/results/provenance.yaml'))"
  grep -E "git_commit|source_log|checksums" data/results/provenance.yaml
  ```

- [ ] T013 [P] [US3] **Write methods & results report and verify reproducibility** (now runs **after** full pipeline T016).  
  *Path*: `data/results/report.md` and `data/results/paper_handoff.md`.  
  *Steps*:  
  1. Cite exact URLs and checksums from `source_log.txt`.  
  2. Re‑run the full pipeline (`python -m code.main --full --seed 42`) and compute SHA‑256 hashes of every file under `data/derived/` and `data/results/`.  
  3. Assert that the hashes match those recorded after the first run.  
  *Verification*: `tests/integration/test_reproducibility.py` performs the re‑run and hash comparison; it must exit 0.

- [ ] T014 [P] [US3] **Create a quickstart guide** for users to reproduce the analysis on a fresh checkout.  
  *Path*: `specs/001-systematic-assessment-of-non-coding-vari/quickstart.md`.  
  *Content*: Environment setup (Python 3.11, required packages), commands to invoke each pipeline stage (`fetch_raw_resources`, `fetch_jaspar_pwms`, `filter_regions`, `score`, `analysis`, `visualization`), and expected artefact locations.  
  *Verification*: The file exists and each documented command runs without error on the CI runner.

- [ ] T017 [P] [US3] **Write the data‑availability statement** describing how each external dataset was obtained and where it resides in the repository.  
  *Path*: `specs/001-systematic-assessment-of-non-coding-vari/data_availability.md`.  
  *Verification*: The file exists, lists dbSNP FTP URL, ENCODE/Roadmap BED URLs, JASPAR JSON URL, and GWAS Catalog FTP URL, and the listed URLs exactly match entries in `data/raw/source_log.txt`.
