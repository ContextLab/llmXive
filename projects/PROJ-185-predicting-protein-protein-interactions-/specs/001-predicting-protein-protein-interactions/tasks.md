# Tasks: Predict Protein‑Protein Interactions from Co‑expression Networks  

**Inputs**: `spec.md`, `plan.md`, `contracts/`, `data-model.md`  

The checklist below follows the research phases defined in the specification and plan.  
Each task is written in the canonical form `- [ ] T### [P?] [USx?] description …` and includes the concrete output file(s) and a verification step.  
Tasks are ordered to respect data flow; parallel‑izable tasks are marked with **[P]**.  

---  

## Phase 1 – Project Skeleton & Configuration  

- [ ] T000 [US1] Create a `Makefile` with required targets `all`, `evaluate`, `enrich`, `summary`, and `clean`.  
  - **Output**: `Makefile` at project root.  
  - **Verification**: `tests/unit/test_makefile.py` parses the file and asserts the presence of all five targets.  

- [ ] T001 [US1] Create the required top‑level directories (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`).  
  - **Output**: empty directories at the paths listed.  
  - **Verification**: `tests/integration/test_skeleton.py` asserts that each directory exists; CI runs `pytest -q tests/integration/test_skeleton.py`.  

- [ ] T002 [US1] Add a minimal `pyproject.toml` with a full `[project]` table (name, version, dependencies) and a `[build‑system]` table; pin all dependencies to exact versions (e.g., `numpy==1.26.4`).  
  - **Output**: `pyproject.toml`.  
  - **Verification**: `tests/unit/test_pyproject_pinning.py` parses the file and checks that every dependency has a `==` specifier.  

- [ ] T003 [US1] Add a `requirements.txt` that mirrors the pinned versions from `pyproject.toml`.  
  - **Output**: `requirements.txt`.  
  - **Verification**: `tests/unit/test_requirements_match.py` confirms the two files list identical packages with identical versions.  

- [ ] T004 [US1] Create configuration files under `src/config/`:  
  - `species.yaml` (default species *Arabidopsis thaliana* with GEO accession list, `held_out_series` entry, and minimum‑sample requirement).  
  - `parameters.yaml` (default `threshold: 0.80`, `norm_method: vst`, `seed: 42`).  
  - **Verification**: `tests/unit/test_config_contents.py` checks required keys exist and that `threshold >= 0.75`.  

- [ ] T036 [US1] Implement a global CLI flag `--seed <int>` that sets a random seed used by **all** stochastic processes (evaluation baseline, negative sampling, sensitivity analysis, etc.) and records the seed in `pipeline.log`.  
  - **Output**: Updated CLI parsers in `src/utils/cli.py` (or equivalent).  
  - **Verification**: `tests/unit/test_seed_flag.py` runs the CLI with `--seed 123` and checks that the same seed appears in `pipeline.log` and that repeated runs produce identical output files.  

- [ ] T031 [US1] Initialize the JSON‑Line `pipeline.log` (path `src/logs/pipeline.log`). The logger must record: timestamp, level, message, and `schema_version` (e.g., `v1.0.0`). It must also log the exact command‑line invocation, software versions, and the random seed (from T036).  
  - **Output**: `src/logs/pipeline.log`.  
  - **Verification**: `tests/unit/test_log_schema.py` validates the file against `contracts/pipeline_log.schema.yaml`.  

- [ ] T032 [US1] Create a post‑target verification script `src/pipeline/verify_outputs.py` that runs after each Make target, confirming presence and parsability of all required output files for each species. Integrate this script into the Makefile so each target calls it upon successful completion.  
  - **Output**: `src/pipeline/verify_outputs.py`.  
  - **Verification**: `tests/unit/test_verification_script.py` simulates a successful target run and checks that the script exits with status 0 only when all required files are present and valid.  

- [ ] T033 [US1] Compute SHA‑256 checksums for **all** files under `data/` (raw GEO downloads, processed matrices, mapping tables, summary files, etc.) and record them in `data/artifact_hashes.yaml`. The checksum step must run after each data‑generation task.  
  - **Output**: Updated `data/artifact_hashes.yaml`.  
  - **Verification**: `tests/unit/test_checksums.yaml` ensures every file listed under `data/` has a corresponding checksum entry and that the recorded hash matches the file’s actual SHA‑256.  

---  

## Phase 2 – Data Acquisition  

- [ ] T005 [US1] Implement `src/pipeline/download_geo.py` that reads `species.yaml`, downloads each GEO series via **GEOparse**, records a SHA‑256 checksum in `data/artifact_hashes.yaml`, and skips any series with `<30` samples (log a warning).  
  - **Output**: raw GEO tarballs under `data/raw/`, `data/artifact_hashes.yaml`.  
  - **Verification**: `tests/unit/test_geo_downloader.py` confirms successful download, checksum recording, and correct skipping behavior.  

- [ ] T006 [US1] After all series are downloaded, verify that the **total retained samples per species ≥ 50**; abort with a clear error logged to `pipeline.log` if not.  
  - **Output**: `pipeline.log` entry `ERROR` if abort condition met.  
  - **Verification**: `tests/integration/test_sample_power.py` simulates a low‑sample scenario and expects the pipeline to raise `SystemExit`.  

---  

## Phase 3 – Normalization & Batch‑Effect Correction  

- [ ] T007 [US1] Implement `src/pipeline/normalize.py` supporting two modes (selected via CLI `--norm-method`):  
  - **VST**: call DESeq2’s `varianceStabilizingTransformation` through `rpy2`.  
  - **TPM**: compute TPM in pure Python.  
  - Produce a normalized matrix `data/processed/<species>_norm.tsv`.  
  - **Verification**: `tests/unit/test_normalization_modes.py` loads both outputs and checks that values are non‑negative and that TPM values are unit‑scaled.  

- [ ] T008 [US1] Implement `src/pipeline/batch_correct.py` that applies **ComBat** (via `rpy2`) when more than one GEO series contributes; if required metadata are missing, fall back to **SVA**. Write the batch‑corrected matrix to `data/processed/<species>_batch_corrected.tsv`.  
  - **Verification**: `tests/unit/test_batch_correction.py` validates that the number of columns (samples) is unchanged and that the mean of each gene across batches is approximately equal.  

- [ ] T009 [US1] Implement `src/pipeline/regress_confounders.py` to regress out expression‑level and gene‑length confounds from the batch‑corrected matrix (linear model per gene). Output `data/processed/<species>_final.tsv`.  
  - **Verification**: `tests/unit/test_confound_regression.py` checks that residuals have reduced correlation with the confound vectors.  

---  

## Phase 4 – Gene Filtering  

- [ ] T010 [US1] Implement `src/pipeline/filter_genes.py` that:  
  1. Filters out genes with **CPM < 1** in **> 80 %** of samples.  
  2. Computes per‑gene variance on the remaining set and retains the **top 5 000** most variable genes (or fewer if less are available).  
  - **Output**: `data/processed/<species>_filtered.tsv` (gene‑by‑sample matrix).  
  - **Verification**: `tests/unit/test_gene_filtering.py` asserts the CPM filter and that the gene count ≤ 5 000.  

---  

## Phase 5 – Correlation Computation (raw scores)  

- [ ] T011 [US1] Implement `src/pipeline/compute_raw_correlations.py` that streams pairwise **Pearson** (for VST) or **Spearman** (for TPM) correlations block‑wise (block size = 1 000 genes) to stay ≤ 7 GB RAM. Write a gzipped TSV `results/raw_correlations_<species>.tsv.gz` with columns `gene_id_1`, `gene_id_2`, `correlation`, `p_value`, `adjusted_p_value`.  
  - **Verification**: `tests/unit/test_raw_correlation_stream.py` confirms that the file can be read line‑by‑line without loading the whole matrix and that the number of rows matches `n_genes * (n_genes‑1) / 2`.  

- [ ] T012 [US1] Perform Benjamini–Hochberg correction on the `p_value` column and write the adjusted p‑values to `results/correlation_stats_<species>.tsv` (FR‑045 – reporting only).  
  - **Verification**: `tests/unit/test_correlation_stats.py` checks that the `adjusted_p` column exists and that all values are ≤ 1.  

---  

## Phase 6 – Identifier Mapping  

- [ ] T013 [US1] Implement `src/pipeline/map_to_string.py` that:  
  1. Loads `org.At.tair.db` (Bioconductor) via `rpy2`; if unavailable, falls back to Ensembl BioMart (REST API).  
  2. Maps filtered gene IDs to STRING protein IDs.  
  3. Writes a mapping table `results/gene_to_protein_<species>.csv` and a warning log `results/mapping_warnings_<species>.log` for any unmapped genes.  
  - **Verification**: `tests/unit/test_mapping.py` validates that at least 95 % of genes are mapped for Arabidopsis and that the warning log is created when unmapped genes exist.  

---  

## Phase 7 – Edge Extraction & Schema Validation  

- [ ] T014 [US1] Implement `src/pipeline/extract_edges.py` that reads the raw correlation file, applies the **user‑specified correlation threshold** (default 0.80, never below 0.75, enforced by CLI validator), and writes the retained edges to `results/predicted_ppi_<species>.tsv` with columns `protein_id_1`, `protein_id_2`, `correlation`.  
  - **Verification**: `tests/unit/test_edge_extraction.py` checks that the header matches the schema and that every correlation ≥ threshold.  

- [ ] T015 [US1] Validate `results/predicted_ppi_<species>.tsv` against `contracts/predicted_edges.schema.yaml`.  
  - **Verification**: `tests/unit/test_edge_schema.py` runs `jsonschema.validate` on the parsed TSV (converted to JSON) and fails if any row violates the schema.  

---  

## Phase 8 – Evaluation & Baseline  

- [ ] T016 [US2] Implement `src/pipeline/split_data.py` that splits samples per species into **training** (80 % of samples) and **test** (20 %) sets, preserving batch structure. Store the split indices in `data/processed/<species>_split.json`.  
  - **Verification**: `tests/unit/test_data_split.py` ensures no sample appears in both sets and that the split respects the 80/20 ratio.  

- [ ] T017 [US2] Implement `src/pipeline/evaluate.py` that:  
  1. Loads the **test‑set** raw correlation scores (streamed from `raw_correlations_*.tsv.gz`).  
  2. Loads STRING high‑confidence interactions (`protein.links.v11.5.txt.gz`) filtered to exclude any evidence channel containing “coexpression”, “transcriptomics”, or “text‑mining”.  
  3. Computes **AUROC** and **AUPRC** on the full (imbalanced) set.  
  4. Generates a **balanced negative set** (size = positive set) sampled uniformly from the complement of STRING high‑confidence edges (global seed).  
  5. Writes per‑species entries to `results/evaluation_metrics.json`.  
  - **Verification**: `tests/unit/test_evaluation_metrics.py` checks that the JSON contains the required fields, that AUROC/AUPRC are numbers between 0 and 1, and that the balanced negative set size matches the positive set size.  

- [ ] T018 [US2] Implement `src/pipeline/baseline_random_graph.py` that:  
  1. Builds a degree‑preserving random graph from the predicted edge list using NetworkX `double_edge_swap` (10 × |E| swaps).  
  2. Scores the random graph against the same STRING reference and computes baseline AUROC/AUPRC.  
  3. Performs a permutation test to obtain `baseline_p`.  
  - **Verification**: `tests/unit/test_baseline.py` confirms that node degree distribution is unchanged and that `baseline_p` is a float in `[0,1]`.  

- [ ] T019 [US2] Add a CI step (`validate_evaluation.yml`) that parses `results/evaluation_metrics.json` against `contracts/evaluation.schema.yaml` and **conditionally** asserts **AUROC ≥ 0.70** **and** **AUPRC ≥ 0.70** **only for species that have at least one predicted edge** (per SC‑001).  
  - **Verification**: CI job fails if any metric falls below the threshold for a species with `predicted_ppi_<species>.tsv` containing ≥ 1 edge; otherwise it passes.  

- [ ] T035 [US2] (new) Add a CI test `test_evaluation_thresholds.py` that implements the conditional logic described above, used by `validate_evaluation.yml`.  
  - **Output**: `tests/integration/test_evaluation_thresholds.py`.  
  - **Verification**: Verified by CI execution of the test suite.  

---  

## Phase 9 – Functional Enrichment  

- [ ] T020 [US3] Implement `src/pipeline/go_enrichment.py` that:  
  1. Collects the set of genes appearing in `predicted_ppi_<species>.tsv`.  
  2. Runs GOATOOLS Fisher’s exact test with Benjamini–Hochberg correction using the filtered‑gene universe (all genes that passed CPM filtering and were successfully mapped).  
  3. Writes `results/go_enrichment_<species>.tsv` with columns `go_id`, `description`, `raw_p`, `adjusted_p`, `gene_count`.  
  4. If no term passes `adjusted_p < 0.05`, writes a single line “No significant enrichment”.  
  - **Verification**: `tests/unit/test_go_enrichment.py` checks that the file conforms to `contracts/go_enrichment.schema.yaml` and that the “No significant enrichment” line appears only when appropriate.  

- [ ] T034 [US3] Add a CI test `test_go_significance.py` that asserts each species’ GO enrichment file contains at least one term with `adjusted_p < 0.05`.  
  - **Output**: `tests/integration/test_go_significance.py`.  
  - **Verification**: CI fails if any enrichment file lacks a significant term, satisfying SC‑002.  

---  

## Phase 10 – Correlation‑Threshold Sensitivity  

- [ ] T021 [US1] Implement `src/pipeline/sensitivity_analysis.py` that loops over thresholds **0.60, 0.70, 0.80, 0.85, 0.90**, repeats edge extraction (T014) for each, computes edge count, AUROC, and AUPRC (using T017), and writes `results/threshold_sensitivity_<species>.tsv`.  
  - **Verification**: `tests/unit/test_sensitivity_output.py` ensures the TSV contains exactly five rows, each with the required columns, and that the AUROC/AUPRC values increase monotonically with higher thresholds (non‑strict monotonicity is acceptable).  

- [ ] T022 [US1] Validate `results/threshold_sensitivity_<species>.tsv` against `contracts/threshold_sensitivity.schema.yaml`.  
  - **Verification**: `tests/unit/test_threshold_schema.py` runs `jsonschema.validate` on the parsed TSV.  

---  

## Phase 11 – Pilot Benchmark & Construct‑Validity  

- [ ] T023 [US1] Implement `src/pipeline/pilot_benchmark.py` that:  
  1. Loads the **held‑out GEO series** specified in `species.yaml`.  
  2. Runs the full pipeline (normalization → correlation → edge extraction) on this series only, using the default threshold 0.80.  
  3. Evaluates against STRING high‑confidence interactions (same as T017) and records **precision** and **recall**.  
  4. Writes `results/pilot_validation_<species>.json` containing `precision`, `recall`, and a boolean `meets_criteria` (true if precision ≥ 0.60 and recall ≥ 0.40).  
  - **Verification**: `tests/unit/test_pilot_benchmark.py` asserts that the JSON contains all fields and that `meets_criteria` matches the numeric thresholds.  

- [ ] T024 [US1] Extend the per‑species summary generator (`src/pipeline/summary.py`) to include the pilot benchmark results and a construct‑validity paragraph citing *Zhang et al., Nat Commun. 2020* and *Lee et al., Plant Cell 2021* (FR‑026).  
  - **Output**: `results/summary_<species>.txt`.  
  - **Verification**: `tests/unit/test_summary_content.py` checks that the summary contains the pilot precision/recall numbers and the citation block.  

---  

## Phase 12 – Aggregated Reporting  

- [ ] T025 [US1] Implement `src/pipeline/aggregate_reports.py` that:  
  1. Collects all `summary_<species>.txt` files.  
  2. Builds `results/master_results.json` (single source of truth) containing per‑species fields: `species`, `edge_count`, `auroc`, `auprc`, `baseline_p`, `top_go_terms` (list of up‑to‑3 terms).  
  3. Generates the final human‑readable report `results/final_report.txt` aggregating overall statistics and restating the construct‑validity justification (FR‑028).  
  - **Verification**: `tests/unit/test_master_results_schema.py` validates the JSON against a locally defined schema; `tests/unit/test_final_report.py` checks that the report contains the phrase “construct‑validity justification”.  

---  

## Phase 13 – Continuous‑Integration & Reproducibility Checks  

- [ ] T026 [US1] Add a Makefile target `validate` that runs all validation scripts (`validate.py`, schema checks, test suites) and exits with non‑zero status on any failure.  
  - **Verification**: CI workflow executes `make validate` after each run; failure is captured in CI logs.  

- [ ] T027 [US1] Implement `src/pipeline/reproducibility_check.py` that re‑runs the entire pipeline with the same `--seed` and compares **all** result files (`predicted_ppi_*.tsv`, `evaluation_metrics.json`, `go_enrichment_*.tsv`, `summary_*.txt`, `master_results.json`) byte‑wise. Any mismatch causes exit 1.  
  - **Verification**: `tests/unit/test_repro_check.py` runs the script on a tiny mock dataset and expects exit 0.  

- [ ] T028 [US1] Add a CI job `runtime_check.yml` that records wall‑clock time of `make all` (via `time`), writes `results/benchmark_report.txt`, and fails (error level) if runtime > 6 h (SC‑003).  
  - **Verification**: CI job parses the file and asserts the duration constraint.  

---  

## Phase 14 – Documentation & Quick‑Start  

- [ ] T029 [US1] Write `docs/quickstart.md` that walks a new user through: (1) installing dependencies, (2) configuring `species.yaml`, (3) running `make all` on the default Arabidopsis dataset, and (4) locating the key output files.  
  - **Verification**: `tests/unit/test_quickstart.md` parses the markdown and confirms that each required command (`pip install -r requirements.txt`, `make all`, `cat results/final_report.txt`) appears.  

- [ ] T030 [US1] Update `README.md` with a reproducibility statement citing the global `--seed` flag, the content‑hashed `artifact_hashes.yaml`, and the location of `master_results.json`.  
  - **Verification**: `tests/unit/test_readme_statement.py` checks that the exact phrase “All results are reproducible given the same seed and input data” is present.  

---  

### Dependency Mapping  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, FR‑047 | T005, T006 |
| FR‑002 | T007 |
| FR‑003 | T010 |
| FR‑004, FR‑045 | T011, T012, T014 |
| FR‑005 | T013 |
| FR‑006, FR‑016, FR‑032 | T017 |
| FR‑007 | T018 |
| FR‑008, FR‑023 | T020 |
| FR‑009, FR‑010, FR‑035 | T000, T031, T036 |
| FR‑011, FR‑013 | T014, T015 |
| FR‑014 | T008, T009 |
| FR‑018, FR‑019 | T017, T022 |
| FR‑020 | T011 |
| FR‑021, FR‑028 | T024, T025 |
| FR‑025 | T021 |
| FR‑026 | T024 |
| FR‑030 | T022 |
| FR‑032 | T017 |
| FR‑034, FR‑034 | T006, T010 |
| SC‑001, SC‑002, SC‑003, SC‑004, SC‑005, SC‑006 | T019, T020, T028, T027, T026, T010, T015, etc. |

---  

**All tasks remain unchecked (‑ [ ])** and must be implemented, tested, and verified to move the project from `planned` → `tasked`. Completion of each task will be recorded automatically by the platform’s CI when the associated test passes.  
