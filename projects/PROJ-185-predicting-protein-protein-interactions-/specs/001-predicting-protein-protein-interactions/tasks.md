# Tasks: Predict Protein‑Protein Interactions from Co‑expression Networks  

**Inputs**: `spec.md`, `plan.md`, `contracts/`, `data-model.md`  

The checklist below follows the research phases defined in the specification and plan.  
Each task is written in the canonical form `- [ ] T### [USx?] description …` and includes the concrete output file(s) and a verification step.  
Tasks are ordered to respect data flow; parallel‑izable tasks are marked with **[P]**.  

---  

## Phase 1 – Project Skeleton & Core Configuration  

- [ ] T001 [US1] Create the required top‑level directories `src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`.  
  - **Output**: empty directories at the listed paths.  
  - **Verification**: `tests/unit/test_skeleton.py` asserts each directory exists; CI runs `pytest -q tests/unit/test_skeleton.py`.  

- [X] T002 [US1] Add a complete `pyproject.toml` with a `[project]` table (name, version, authors, description) and a `[build‑system]` table. All runtime dependencies must be **pinned** to exact versions (e.g., `numpy==1.26.4`).  
  - **Output**: `pyproject.toml` at project root.  
  - **Verification**: `tests/unit/test_pyproject_pins.py` parses the file and fails if any dependency lacks an `==` specifier.  

- [X] T003 [US1] Create a matching `requirements.txt` that lists the exact same pinned versions as `pyproject.toml`.  
  - **Output**: `requirements.txt`.  
  - **Verification**: `tests/unit/test_requirements_match.py` reads both files and asserts line‑by‑line equality of package names and versions.  

- [ ] T004 [US1] Add configuration files under `src/config/`:  
  - `species.yaml` – maps each target species to a list of GEO accession IDs, includes a `held_out_series` entry and a `min_samples: 50` field.  
  - `parameters.yaml` – contains `threshold: 0.80`, `norm_method: vst`, `seed: 42`.  
  - **Verification**: `tests/unit/test_config_contents.py` checks that required keys exist, that `threshold >= 0.75`, and that a numeric `seed` is present.  

- [ ] T005 [US1] Implement a global CLI parser (`src/utils/cli.py`) that registers a `--seed <int>` flag. All stochastic functions must read this seed via a shared module (`src/utils/random.py`). Extend the existing JSON‑Line logger (`src/logs/pipeline.log`) to record the seed, full command‑line invocation, and software versions (FR‑010, FR‑035).   <!-- FAILED-IN-EXECUTION: tests/unit/test_seed_flag.py exit=1 -->
  - **Output**: Updated `cli.py`, `random.py`, and an initialized `src/logs/pipeline.log`.  
  - **Verification**: `tests/unit/test_seed_flag.py` runs the CLI with `--seed 123`, checks that the same seed appears in `pipeline.log`, and that two consecutive runs produce identical `results/predicted_ppi_Arabidopsis.tsv` files.  

---  

## Phase 2 – Data Acquisition  

- [ ] T006 [US1] Implement `src/pipeline/download_geo.py` that reads `species.yaml`, downloads each GEO series with **GEOparse**, skips any series with `<30` samples (log a warning), writes the raw `.tar.gz` files to `data/raw/`, and records a SHA‑256 checksum for every downloaded file in `data/artifact_hashes.yaml`.  
  - **Output**: Raw GEO archives in `data/raw/`; updated `data/artifact_hashes.yaml`.  
  - **Verification**: `tests/unit/test_geo_downloader.py` confirms that each expected file exists, that its checksum matches the recorded value, and that series with insufficient samples are omitted.  

- [ ] T007 [US1] After all downloads, verify that the **total retained samples per species** meet the minimum (`min_samples` from `species.yaml`). If a species falls short, abort the pipeline with an `ERROR` entry in `pipeline.log`.   <!-- FAILED-IN-EXECUTION: code/src/pipeline/verify_samples.py exit=1 -->
  - **Output**: `pipeline.log` entry `ERROR` (if abort) or a `INFO` entry confirming sufficient samples.  
  - **Verification**: `tests/integration/test_sample_power.py` simulates a low‑sample scenario and expects the script to raise `SystemExit` with the appropriate log message.  

---  

## Phase 3 – Normalization, Batch‑Effect Correction & Confound Regression  

- [ ] T008 [US1] Implement `src/pipeline/normalize.py` supporting two mutually exclusive modes selected via the CLI (`--norm-method vst` or `--norm-method tpm`):  
  1. **VST** – call DESeq2’s `varianceStabilizingTransformation` through `rpy2`.  
  2. **TPM** – compute TPM in pure Python.  
  The script writes the normalized matrix to `data/processed/<species>_norm.tsv`.  
  - **Verification**: `tests/unit/test_normalization_modes.py` loads both outputs, checks that all values are non‑negative, and that TPM values are scaled to per‑million.  

- [ ] T009 [US1] Implement `src/pipeline/batch_correct.py` that applies **ComBat** (via `rpy2`) when a species has >1 GEO series; if required batch metadata are missing, fall back to **SVA**. The corrected matrix is written to `data/processed/<species>_batch_corrected.tsv`.  
  - **Verification**: `tests/unit/test_batch_correction.py` asserts that the number of samples (columns) is unchanged and that the mean expression per gene across batches is approximately equal (difference < 0.01).  

- [ ] T010 [US1] Implement `src/pipeline/regress_confounders.py` to regress out two global confounders (library size and gene length) from the batch‑corrected matrix using a simple linear model per gene. Output the final matrix to `data/processed/<species>_final.tsv`.  
  - **Verification**: `tests/unit/test_confound_regression.py` computes the Pearson correlation between each confound vector and the residuals; all correlations must be ≤ 0.05.  

---  

## Phase 4 – Gene Filtering  

- [ ] T011 [US1] Implement `src/pipeline/filter_genes.py` that (a) removes genes with **CPM < 1** in **> 80 %** of samples, then (b) selects the **≤ 5 000** most variable genes (by variance). The filtered expression matrix is written to `data/processed/<species>_filtered.tsv`.  
  - **Verification**: `tests/unit/test_gene_filtering.py` asserts that the CPM filter was applied correctly and that the final gene count does not exceed 5 000.  

---  

## Phase 5 – Correlation Computation (raw scores)  

- [ ] T012 [US1] Implement `src/pipeline/compute_raw_correlations.py` that streams pairwise **Pearson** correlations (for VST) or **Spearman** correlations (for TPM) in blocks of 1 000 genes to keep RAM ≤ 7 GB. Write a gzipped TSV `results/raw_correlations_<species>.tsv.gz` with columns `gene_id_1`, `gene_id_2`, `correlation`, `p_value`.  
  - **Verification**: `tests/unit/test_raw_correlation_stream.py` reads the file line‑by‑line, confirms no `MemoryError`, and checks that the number of rows equals *n_genes·(n_genes‑1)/2*.  

- [ ] T013 [US1] Apply Benjamini–Hochberg correction to the `p_value` column of the raw correlation file and write the adjusted p‑values to `results/correlation_stats_<species>.tsv`. This file is for reporting only (FR‑045).  
  - **Verification**: `tests/unit/test_correlation_stats.py` ensures the `adjusted_p` column exists, all values are ≤ 1, and that the file is parsable as TSV.  

---  

## Phase 6 – Identifier Mapping  

- [ ] T014 [US1] Implement `src/pipeline/map_to_string.py` that loads the Bioconductor package `org.At.tair.db` via `rpy2`; if unavailable, falls back to Ensembl BioMart REST calls. It maps every filtered gene ID to a STRING protein identifier, writes the mapping table to `results/gene_to_protein_<species>.csv`, and logs any unmapped genes to `results/mapping_warnings_<species>.log`.  
  - **Verification**: `tests/unit/test_mapping.py` checks that at least **95 %** of Arabidopsis genes are successfully mapped and that the warning log is created only when unmapped genes exist.  

---  

## Phase 7 – Edge Extraction & Schema Validation  

- [ ] T015 [US1] Implement `src/pipeline/extract_edges.py` that (1) reads `results/raw_correlations_<species>.tsv.gz`, (2) joins protein IDs using the mapping table, (3) applies the **user‑specified correlation threshold** (default 0.80, enforced minimum 0.75), and (4) writes the retained edges to `results/predicted_ppi_<species>.tsv` with columns `protein_id_1`, `protein_id_2`, `correlation`.  
  - **Verification**: `tests/unit/test_edge_extraction.py` confirms that the header matches the schema, that every `correlation` ≥ the effective threshold, and that the file contains at least one edge for Arabidopsis.  

- [ ] T016 [US1] Validate the edge list against `contracts/predicted_edges.schema.yaml` using `jsonschema`. The script `src/pipeline/validate_edges.py` exits with non‑zero status on any violation.  
  - **Verification**: `tests/unit/test_edge_schema.py` runs the validator on a known‑good file (should pass) and on a deliberately malformed file (should fail).  

---  

## Phase 8 – Evaluation & Baseline  

- [ ] T017 [US1] (optional) Implement `src/pipeline/split_data.py` that partitions samples per species into training (80 %) and test (20 %) sets **solely for downstream exploratory analyses**. The split indices are saved to `data/processed/<species>_split.json`. This split is **not** used by the primary evaluation task to comply with FR‑006.  
  - **Verification**: `tests/unit/test_data_split.py` checks that no sample appears in both sets and that the proportion is within 1 % of the target split.  

- [ ] T018 [US1] Implement `src/pipeline/evaluate.py` that (a) loads the **full** raw correlation scores from `results/raw_correlations_<species>.tsv.gz` (i.e., all gene‑pair candidates, no test‑set restriction), (b) loads the STRING high‑confidence network (`protein.links.v11.5.txt.gz`) filtered to exclude any evidence channel containing “coexpression”, “transcriptomics”, or “text‑mining”, (c) computes **AUROC** and **AUPRC** on the full (imbalanced) set, (d) draws a **balanced negative set** (size = positive set) using the global seed, and (e) writes per‑species entries to `results/evaluation_metrics.json`.  
  - **Verification**: `tests/unit/test_evaluation_metrics.py` parses the JSON, asserts presence of all required fields, checks that AUROC/AUPRC are numbers in `[0,1]`, and confirms the evaluation was performed on the full correlation set.  

- [ ] T019 [US1] Implement `src/pipeline/baseline_random_graph.py` that (a) builds a degree‑preserving random graph from the predicted edge list via NetworkX `double_edge_swap` (10 × |E| swaps), (b) scores this baseline against the same STRING reference, (c) computes baseline AUROC/AUPRC, and (d) performs a permutation test to obtain a p‑value (`baseline_p`). The baseline fields are added to `results/evaluation_metrics.json`.  
  - **Verification**: `tests/unit/test_baseline.py` confirms that node degree distribution is unchanged, that baseline metrics are ≤ 0.55 for AUROC (per FR‑007), and that `baseline_p` lies in `[0,1]`.  

- [ ] T020 [US1] Add a CI test (`tests/integration/test_evaluation_thresholds.py`) that fails the workflow if **any species with ≥1 predicted edge** has `auroc < 0.70` **or** `auprc < 0.70` (SC‑001). The test is invoked by the GitHub Actions job `validate_evaluation.yml`.  
  - **Verification**: CI execution of the test suite; a failing case aborts the run.  

---  

## Phase 9 – Functional Enrichment  

- [ ] T021 [US1] Implement `src/pipeline/go_enrichment.py` that (a) extracts the set of genes appearing in `results/predicted_ppi_<species>.tsv`, (b) runs GOATOOLS Fisher’s exact test with Benjamini–Hochberg correction using the filtered‑gene universe as background, (c) writes `results/go_enrichment_<species>.tsv` with columns `go_id`, `description`, `raw_p`, `adjusted_p`, `gene_count`. If no term reaches `adjusted_p < 0.05`, write a single line `No significant enrichment`.  
  - **Verification**: `tests/unit/test_go_enrichment.py` validates the file against `contracts/go_enrichment.schema.yaml` and checks the graceful‑no‑term handling.  

- [ ] T022 [US1] Add a CI test (`tests/integration/test_go_significance.py`) that asserts each species’ GO enrichment file contains at least one term with `adjusted_p < 0.05` **unless** the file contains the exact line “No significant enrichment”. Failure aborts the run, satisfying SC‑002.  

---  

## Phase 10 – Correlation‑Threshold Sensitivity  

- [ ] T023 [US1] Implement `src/pipeline/sensitivity_analysis.py` that iterates over thresholds **0.60, 0.70, 0.80, 0.85, 0.90**, repeats edge extraction for each threshold, computes edge count, AUROC, and AUPRC (re‑using `evaluate.py` on the full set), and writes `results/threshold_sensitivity_<species>.tsv`.  
  - **Verification**: `tests/unit/test_sensitivity_output.py` ensures the TSV has exactly five rows, each with the required columns (`species`, `threshold`, `num_edges`, `auroc`, `auprc`), that `num_edges` values are non‑negative integers, and that AUROC/AUPRC values are non‑decreasing with higher thresholds (monotonicity check).  

- [ ] T024 [US1] Validate the sensitivity table against `contracts/threshold_sensitivity.schema.yaml`.  
  - **Verification**: `tests/unit/test_threshold_schema.py` runs `jsonschema.validate` on the parsed TSV.  

---  

## Phase 11 – Pilot Benchmark & Construct‑Validity Summary  

- [ ] T025 [US1] Implement `src/pipeline/pilot_benchmark.py` that (a) loads the **held‑out** GEO series specified in `species.yaml`, (b) runs the full pipeline (normalization → correlation → edge extraction) on this series alone using the default threshold 0.80, (c) evaluates against STRING high‑confidence interactions, (d) records **precision** and **recall** and a boolean `meets_criteria` (precision ≥ 0.60 and recall ≥ 0.40) in `results/pilot_validation_<species>.json`.  
  - **Verification**: `tests/unit/test_pilot_benchmark.py` checks that the JSON contains all fields and that `meets_criteria` correctly reflects the numeric thresholds.  

- [ ] T026 [US1] Extend `src/pipeline/summary.py` to generate `results/summary_<species>.txt` containing (i) total predicted edges, (ii) evaluation metrics (AUROC, AUPRC, baseline p), (iii) top 3 enriched GO terms, (iv) pilot benchmark precision/recall, and (v) a construct‑validity paragraph citing *Zhang et al., Nat Commun. 2020* and *Lee et al., Plant Cell 2021* (FR‑026).  
  - **Verification**: `tests/unit/test_summary_content.py` parses the summary and asserts that each of the five sections appears and that the citation block is present.  

---  

## Phase 12 – Aggregated Reporting & Final Hand‑off  

- [ ] T027 [US1] Implement `src/pipeline/aggregate_reports.py` that (a) collects all `summary_<species>.txt` files, (b) builds `results/master_results.json` (single source of truth) with per‑species fields `species`, `edge_count`, `auroc`, `auprc`, `baseline_p`, `top_go_terms` (list of up‑to‑3 terms), and (c) writes a human‑readable `results/final_report.txt` aggregating overall statistics and restating the construct‑validity justification (FR‑028).  
  - **Verification**: `tests/unit/test_master_results_schema.py` validates the JSON against an inline schema; `tests/unit/test_final_report.py` checks that the phrase “construct‑validity justification” appears in the final report.  

---  

## Phase 13 – Reproducibility Checks & Continuous Integration  

- [ ] T028 [US1] Add a Makefile target `validate` that runs **all** verification scripts (`validate_edges.py`, `go_enrichment.py`, `sensitivity_analysis.py`, etc.) and executes the full pytest suite. The target exits with non‑zero status on any failure.  
  - **Verification**: CI workflow executes `make validate`; a successful run yields a green check.  

- [ ] T029 [US1] Implement `src/pipeline/repro_check.py` that (a) re‑runs the entire pipeline with the same `--seed` on a tiny mock dataset, (b) compares **all** result files (`predicted_ppi_*.tsv`, `evaluation_metrics.json`, `go_enrichment_*.tsv`, `summary_*.txt`, `master_results.json`) byte‑wise, and (c) exits with status 1 if any mismatch is detected.  
  - **Verification**: `tests/unit/test_repro_check.py` runs the script on the mock data and expects exit 0.  

- [ ] T030 [US1] Add a CI job `runtime_check.yml` that records wall‑clock time of `make all` (via the Unix `time` command), writes `results/benchmark_report.txt`, and fails if runtime > 6 h (SC‑003).  
  - **Verification**: `tests/unit/test_runtime_limit.py` parses the benchmark file and asserts the duration constraint.  

---  

## Phase 14 – Documentation & Quick‑Start  

- [ ] T031 [US1] Write `docs/quickstart.md` that walks a new user through (1) installing dependencies (`pip install -r requirements.txt`), (2) configuring `species.yaml`, (3) running the full pipeline (`make all`), and (4) locating the key output files (`results/final_report.txt`, `results/master_results.json`).  
  - **Verification**: `tests/unit/test_quickstart.md` parses the markdown and confirms that each of the four commands appears verbatim.  

- [ ] T032 [US1] Update `README.md` with a reproducibility statement: “All results are reproducible given the same seed and input data; the seed is recorded in `pipeline.log`, and every artifact is content‑hashed in `data/artifact_hashes.yaml`.”  
  - **Verification**: `tests/unit/test_readme_statement.py` checks that the exact phrase above is present.  

---  

## Phase 15 – Schema Validation Tasks (New)  

- [ ] T033 [US1] Validate `evaluation_metrics.json` against `contracts/evaluation.schema.yaml` using `jsonschema`. The script `src/pipeline/validate_evaluation.py` exits with non‑zero status on any schema violation.  
  - **Output**: Validation pass/fail logged to `pipeline.log`.  
  - **Verification**: `tests/unit/test_evaluation_schema.py` runs the validator on a correct file (should pass) and on a malformed file (should fail).  

- [ ] T034 [US1] Validate `pipeline.log` against `contracts/pipeline_log.schema.yaml` using `jsonschema`. The script `src/pipeline/validate_log_schema.py` exits with non‑zero status on any violation.  
  - **Output**: Validation pass/fail logged to `pipeline.log`.  
  - **Verification**: `tests/unit/test_log_schema.py` creates a well‑formed log entry (should pass) and an entry missing `schema_version` (should fail).  

---  

### Dependency Mapping  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, FR‑047   | T006, T007 |
| FR‑002           | T008 |
| FR‑003           | T011 |
| FR‑004, FR‑045   | T012, T013, T015 |
| FR‑005           | T014 |
| FR‑006, FR‑016, FR‑032 | T018 (full‑set evaluation), T019 |
| FR‑007           | T019 |
| FR‑008, FR‑023   | T021 |
| FR‑009, FR‑010, FR‑035 | T001–T005 |
| FR‑011, FR‑013   | T015, T016 |
| FR‑014           | T009 |
| FR‑018, FR‑019   | T018 |
| FR‑020           | T012 |
| FR‑021, FR‑028   | T026, T027 |
| FR‑025           | T023 |
| FR‑026           | T026 |
| FR‑030           | T024 |
| FR‑032           | T018 |
| FR‑034           | T034 |
| SC‑001, SC‑002, SC‑003, SC‑004, SC‑005, SC‑006 | T020, T022, T030, T029, T028, T010, T015, etc. |

---  

All tasks remain unchecked (`- [ ]`). They must be implemented, tested, and verified to move the project from **planned → tasked**. Completion of each task will be recorded automatically by the platform’s CI when the associated test passes.  
