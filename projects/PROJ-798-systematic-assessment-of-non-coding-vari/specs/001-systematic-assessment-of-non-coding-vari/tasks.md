# Tasks: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

**Input**: Design documents from `/specs/001-gene-regulation/` (spec.md, plan.md, data-model.md, contracts/)

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] Create the project directory structure and prove it with a committed manifest. Create `code/`, `code/data_ingestion/`, `code/scoring/`, `code/analysis/`, `code/utils/`, `data/raw/`, `data/derived/`, `data/results/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, each containing an `__init__.py` (for Python packages) or a `.gitkeep` (for data dirs). **Verification**: run `find code data tests -type d | sort > data/results/structure_manifest.txt` and commit the manifest; the verifier checks that this file lists every required directory. Also document the runnable entry command (`python -m code.main --help`) in `quickstart.md`. (Reopened)

- [ ] T004 [P] Create `.gitignore` at repository root containing the exact exclusion patterns `data/raw/*`, `!data/raw/checksums.json`, `!data/raw/source_log.txt`, `data/derived/*`, `__pycache__/`, `.env`. **Verification**: the committed file is non‑empty and contains all five patterns; `git check-ignore data/raw/snps_raw.vcf` exits 0 and `git check-ignore data/raw/source_log.txt` exits 1. (Reopened)

- [ ] T010 [US1] Implement dbSNP SNP fetching in `code/data_ingestion/fetch_dbsnp.py`: download **all** common human SNPs (MAF > 1 %) from dbSNP build 155 GRCh38 via the canonical FTP mirror `ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/` (HTTPS fallback allowed). Stream each chromosome VCF (`chr*.common_snps.vcf.gz`) line‑by‑line with `gzip.open` to stay within CI memory limits. Write source URLs, build version, timestamp, and SHA‑256 checksums to `data/raw/source_log.txt`. **Verification**: `data/raw/source_log.txt` exists and lists all downloaded URLs; `data/derived/snps_raw.parquet` contains real rsIDs with GRCh38 coordinates.

- [ ] T011 [US1] Download ENCODE v4 and Roadmap Epigenomics promoter/enhancer BED files from their official repositories (e.g., ENCODE FTP `ftp://ftp.encodeproject.org/` and Roadmap `[UNRESOLVED-CLAIM: https://egg2.wustl.edu/roadmap/data/byFileType/peaks/` — HTTP 404]). Record URLs, version tags, and SHA‑256 checksums in `data/raw/source_log.txt`. Merge and index them into `data/raw/regulatory_regions.bed`. **Verification**: BED file exists, non‑empty, and checksum logged.

- [ ] T010b [US2] Download the GRCh38 reference genome FASTA (e.g., `ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/GRCh38.primary_assembly.genome.fa.gz`). Index with `samtools faidx`. Log URL, version, and checksum in `source_log.txt`. **Verification**: FASTA and `.fai` exist; checksum recorded.

- [ ] T012 [US1] Fetch the JASPAR 2024 human PWM collection (`ftp://ftp.ebi.ac.uk/pub/databases/jaspar/JASPAR2024/CORE/non_redundant/vertebrates/`) as a single TSV/FASTA file `data/raw/jaspar_pwm.txt`. Parse each matrix, store `pwm_id`, `tf_name`, `matrix`, and `length`. Log source URL, version, checksum. **Verification**: parsed PWM objects can be listed; checksum present.

- [ ] T014 [US1] Implement regulatory filtering in `code/data_ingestion/filter_regions.py`: apply MAF > 1 % and A/C/G/T allele filters (exclude N/indels), intersect SNPs with `data/raw/regulatory_regions.bed` using ≥1 bp overlap (boundary SNPs included), and save to `data/derived/filtered_snps.parquet` validated against `specs/001-systematic-assessment-of-non-coding-vari/contracts/snp_schema.schema.yaml`. Log the scored‑vs‑input SNP ratio (SC‑001) to `data/results/sc001_proportion.json`. **Dependency**: T010, T011. Also explicitly drop any non‑human species variants (none expected from dbSNP) to satisfy US‑1 scenario 3.

- [ ] T013b [US1] Implement the GC‑matched non‑regulatory control set in `code/data_ingestion/filter_regions.py`: sample random non‑regulatory genomic windows (excluding `regulatory_regions.bed`), compute GC% with `pyfaidx`, and match the filtered SNPs' GC distribution within ±2 % tolerance. Save to `data/derived/gc_matched_controls.parquet` validated against `specs/001-systematic-assessment-of-non-coding-vari/contracts/control_set_schema.schema.yaml`. **Dependency**: T014. *Note*: controls are for baseline reporting only, not the primary KS test.

- [ ] T015 [US1] Compute LD blocks and stratification IDs for each filtered SNP using a pre‑computed LD reference (e.g., 1000 Genomes Phase 3) via `pysam`/`plink` utilities. Add fields `ld_block_id` and `stratum_id` (GC‑content + TSS‑distance bin) to `data/derived/filtered_snps.parquet`. Validate against the same SNP schema (which now requires these fields). **Dependency**: T014.

- [ ] T018 [US2] Implement the affinity scorer in `code/scoring/pwm_scorer.py` and `code/scoring/delta_calculator.py`: load PWMs from `data/raw/jaspar_pwm.txt`, extract reference‑genome context windows via `pyfaidx` with window size equal to each PWM length (dynamic per TF), compute log‑odds scores for reference and alternate alleles, and output ΔScore = Score_alt − Score_ref plus the `is_large_magnitude` flag (|Δ| ≥ 2 bits). **Dependency**: T014, T010b. Include unit tests in `tests/unit/test_pwm_scorer.py` verifying log‑odds math on a hand‑computed example and asserting window size == PWM length.

- [ ] T021 [US2] Connect scoring into `code/main.py` and run a thin end‑to‑end pass: score all filtered SNPs (now full‑genome) against **all** high‑confidence human JASPAR motifs (≈ 600 PWMs). Write real result rows to `data/derived/scores.parquet` with columns `snp_id`, `tf_id`, `score_ref`, `score_alt`, `delta_score`, `window_size`, `is_large_magnitude` per `specs/001-systematic-assessment-of-non-coding-vari/contracts/score_schema.schema.yaml`. **Checkpoint**: the documented command in `quickstart.md` executes and its numerical outputs can be spot‑checked against expected values for three concrete fixtures (see `tests/integration/expected_spotcheck.json`). **Dependency**: T018, T015.

## Phase 2: Complete the study and validate its evidence

- [ ] T027 [US3] Implement GWAS Catalog ingestion in `code/analysis/enrichment_test.py`: download the latest GWAS associations file from `[UNRESOLVED-CLAIM: https://ftp.ebi.ac.uk/pub/databases/gwas/latest/` — HTTP 404] (determine the most recent file at runtime), extract lead SNPs to a BED, intersect with `data/derived/filtered_snps.parquet` to set `is_gwas_lead`, and log the exact file name, version, and checksum to `data/raw/source_log.txt`. Fail loudly on fetch errors. **Dependency**: T014.

- [ ] T024 [US3] Implement the permutation test in `code/analysis/enrichment_test.py`: n = 100 permutations randomly reassigning the *in‑GWAS/out‑of‑GWAS* status labels across the entire dataset simultaneously (preserving total GWAS/non‑GWAS counts), with a fixed random seed. Run the KS test on the **FULL** unfiltered ΔScore distributions (in‑GWAS vs out‑GWAS) per TF. Flag TFs with insufficient SNP counts rather than crashing. Include unit tests in `tests/unit/test_statistics.py` verifying label‑count preservation and KS correctness on a synthetic dataset with known enrichment, and a specific check that TF TCF7L2 obtains a corrected p‑value < 0.05. **Dependency**: T021, T027.

- [ ] T025 [US3] Implement West‑Stephens max‑T FDR correction and final result aggregation in `code/analysis/fdr_correction.py`: build the null distribution of the maximum KS statistic across all TFs per permutation, compute corrected p‑values per TF, apply α = 0.05, **merge** the KS results from T024 with Tail‑Enrichment results from T026, and save the combined per‑TF results to `data/derived/enrichment_results.parquet` conforming to `specs/001-systematic-assessment-of-non-coding-vari/contracts/enrichment_result_schema.schema.yaml`. Include fields `ks_statistic`, `p_value_ks_observed`, `p_value_ks_corrected`, `tail_proportion_observed`, `tail_p_value`, `is_significant_ks`, `is_significant_tail`, etc. **Verification**: schema validation passes (using jsonschema) and the parquet file contains non‑null values for all tail‑related columns for each TF. **Dependency**: T024, T026.

- [ ] T026 [US3] Implement the Tail‑Enrichment test in `code/analysis/tail_enrichment.py`: compute the proportion of SNP‑TF pairs with `|ΔScore| ≥ 2 bits` inside GWAS loci versus outside, perform a permutation‑based test (same label shuffling as T024), and output `tail_proportion_observed`, `tail_p_value`, and `is_significant_tail` per TF. Store results in `data/derived/tail_enrichment.parquet` validated against `specs/001-systematic-assessment-of-non-coding-vari/contracts/enrichment_result_schema.schema.yaml`. **Dependency**: T021, T027.

- [ ] T028 [US3] Validate enrichment result schema integration and tail‑test outputs: add a unit test `tests/unit/test_enrichment_schema.py` that loads a sample `enrichment_results.parquet`, validates it against `enrichment_result_schema.schema.yaml`, and asserts that the columns `tail_proportion_observed`, `tail_p_value`, and `is_significant_tail` are present and contain non‑null values for every TF. **Verification**: test passes and schema validation succeeds; any missing tail fields cause a test failure. **Dependency**: T025, T026.

- [ ] T005v [US3] Add validation and sensitivity checks: 
    * Sweep the large‑magnitude cutoff from 0.5 to 4.0 bits in 0.5‑bit steps, re‑run the enrichment pipeline, and record outcomes in `data/results/sensitivity_cutoff_sweep.json`.
    * Verify runtime and peak memory of the full pipeline stay within 6 h / 7 GB by logging per‑phase timings and RAM usage to `data/results/performance_log.json`. **Dependency**: T025, T026.

- [ ] T006v [US3] Generate result tables and figures directly from validated outputs:
    * `data/results/results_summary.csv` (per‑TF enrichment table from `enrichment_results.parquet`),
    * TF‑sensitivity heatmap (`data/results/figures/tf_heatmap.png`),
    * ΔScore distribution figure (in‑GWAS vs out‑GWAS) (`data/results/figures/delta_distribution.png`).
    All figures trace back to `data/derived/enrichment_results.parquet` and `data/derived/scores.parquet`. **Dependency**: T025, T026.

## Phase 3: Reproducible results and paper handoff

- [ ] T007 Write `data/results/report.md`: a concise methods/results account linking each claim to the actual output files and figure paths, stating the sampled chromosome scope (full‑genome dbSNP subset and its representativeness limitation), the permutation count, the 2‑bit cutoff sensitivity result, negative findings, and the associational (non‑causal) framing required by the spec assumptions. **Dependency**: T006v.

- [ ] T008 Write‑up re‑run verification (no `[P]` tag): Re‑run the documented workflow from its declared inputs (`python -m code.main`), confirm `pytest tests/` passes, verify that all derived result files (`*.parquet`, `*.csv`, `*.png`) are byte‑identical to the previous run (ignoring the raw GWAS source file which may change), and document the paper‑stage handoff (tables, figures, and report paths) in `data/results/paper_handoff.md`. **Verification**: a clean re‑run reproduces identical derived artifacts given the fixed seed. **Dependency**: T007.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (dbSNP fetch, regulatory filter, GC‑matched controls) | T010, T011, T014, T013b | `python -m code.main --stage ingest` |
| FR-002/FR-003 (dynamic‑window PWM scoring, ΔScore, 2‑bit flag) | T018, T021 | `pytest tests/unit/test_pwm_scorer.py` |
| FR-004/FR-005 (label permutation, KS test) | T024 | `pytest tests/unit/test_statistics.py` |
| FR-006/FR-007/FR-008 (West‑Stephens max‑T FDR, α = 0.05) | T025 | `python -m code.main --stage analysis` |
| SC-001/SC-002/SC-003 | T014, T025, T005v | `data/results/sc001_proportion.json`, `enrichment_results.parquet`, `sensitivity_cutoff_sweep.json` |
| NFR-001/NFR-002 (runtime, memory) | T005v | `data/results/performance_log.json` |

**Execution order**: T001/T004 (parallel) → T010 → T011 → T010b → T012 → T014 → T013b → T015 → T018 → T021 → T027 → T024 → T025 → T026 → T028 → T005v → T006v → T007 → T008.