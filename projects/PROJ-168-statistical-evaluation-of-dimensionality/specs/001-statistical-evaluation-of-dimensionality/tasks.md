# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Input**: `spec.md`, `plan.md`, data-model, contracts, and prior verification feedback.  
All tasks are unchecked (`- [ ]`) to enable independent verification. Preserve scientific requirements; repair format and artifact-generation failures from prior rounds.

---

## Phase 1: Setup, Configuration, and Early End-to-End Analysis

- [ ] T001 [US1] Create the canonical project directory tree and document the runnable command in `quickstart.md`.
  - Create directories: `mkdir -p data/raw data/processed data/embeddings data/clustering data/metrics results code tests figures`
  - Create `code/quickstart.md` with the command: `python code/main.py --config code/config.py`
  - Output: directory tree on disk, `code/quickstart.md` with documented entry point.
  - Verification: `ls -R data/ code/ results/` shows all subdirectories exist; `cat code/quickstart.md` contains the runnable command and explains that it downloads, preprocesses, embeds, clusters, and reports fidelity metrics.

- [ ] T002 [US1] Establish dependencies and pinned versions in `code/requirements.txt` and `environment.yml`.
  - Create `code/requirements.txt` with pinned versions: `numpy>=1.21`, `pandas>=1.3`, `scikit-learn>=1.0`, `scipy>=1.7`, `matplotlib>=3.4`, `seaborn>=0.11`, `umap-learn>=0.5`, `leidenalg>=0.8`, `GEOparse>=2.0`, `requests>=2.26`, `psutil>=5.8`, `statsmodels>=0.13`.
  - Create `environment.yml` with the same pinned versions and `python=3.9`.
  - Output: `code/requirements.txt`, `environment.yml`.
  - Verification: `pip install -r code/requirements.txt` succeeds; `conda env create -f environment.yml` succeeds; `python -c "import numpy, pandas, sklearn, scipy, matplotlib, umap, leidenalg, GEOparse; print('All imports OK')"` prints success.

- [ ] T003 [US1] Implement `code/config.py` defining all project paths, global random seed, and dataset accession IDs.
  - Define constants: `SEED = 42`, `DATA_RAW = "data/raw"`, `DATA_PROCESSED = "data/processed"`, `DATA_EMBEDDINGS = "data/embeddings"`, `DATA_CLUSTERING = "data/clustering"`, `DATA_METRICS = "data/metrics"`, `RESULTS_DIR = "results"`, `FIGURES_DIR = "figures"`, `ACCESSIONS = ["GSE131907", "GSE111322", "GSE150728"]`.
  - Define hyperparameters: `PCA_N_COMPONENTS = 30`, `TSNE_PERPLEXITY = 30`, `TSNE_N_ITER = 1000`, `UMAP_N_NEIGHBORS = 15`, `UMAP_MIN_DIST = 0.1`, `LEIDEN_RESOLUTION_MIN = 0.1`, `LEIDEN_RESOLUTION_MAX = 1.0`, `LEIDEN_RESOLUTION_STEP = 0.1`, `K_NEIGHBORS_GEOMETRIC = 15`, `SAMPLE_CELLS_THRESHOLD = 10000`, `SAMPLE_SIZE = 5000`, `MEMORY_LIMIT_BYTES = 7_000_000_000`, `RUNTIME_LIMIT_SECONDS = 21600`.
  - Output: `code/config.py`.
  - Verification: `python -c "from code.config import SEED, DATA_RAW, ACCESSIONS; print(f'SEED={SEED}, RAW={DATA_RAW}, ACCESSIONS={ACCESSIONS}')"` prints the correct values.

- [ ] T004 [US1] Implement `code/utils.py` with utility functions for logging, resource monitoring, and data I/O.
  - Implement `get_logger(name)` that returns a logger writing to `results/run_log.txt` and stdout.
  - Implement `ResourceMonitor` class with a `run(cmd_list, step_name)` method that executes a shell command, captures wall-clock time and peak RSS via `/usr/bin/time -v`, and writes a CSV row to `results/monitoring.csv` with columns `step, wall_time_s, peak_ram_gb`. Abort if peak RSS > 7 GB.
  - Implement `parse_time_output(time_log_str)` that extracts `Elapsed (wall clock) time` (seconds) and `Maximum resident set size` (KB) from `/usr/bin/time -v` output.
  - Implement `ensure_dir(path)` that creates a directory if it does not exist.
  - Output: `code/utils.py`, `results/monitoring.csv` (header row only on first run).
  - Verification: `python code/utils.py --test` runs a test command (e.g., `echo "test"`), writes to `results/monitoring.csv`, and prints the parsed metrics; the CSV file contains columns `step, wall_time_s, peak_ram_gb` and at least one data row.

- [ ] T005 [US1] Implement `code/data_gap_resolver.py` that verifies the availability of raw-count matrices for the three required GEO accessions.
  - Query GEO for each accession ID using `GEOparse.get_GEO(accession)` or a direct HTTP request to known raw-count URLs (e.g., NCBI SRA, GEO FTP).
  - For each accession, attempt to resolve a verified URL to a raw count file (matrix or expression table).
  - Write a JSON manifest `data/manifest.json` conforming to `dataset.schema.yaml`, with fields: `dataset_id`, `source_url`, `status` ("Available" or "Unavailable"), `error_message` (if Unavailable), `checksum` (empty string if Unavailable), `raw_file_path`, `processed_file_path` (null initially).
  - If NO accessions resolve to available raw counts, write a summary to `results/data_gap_summary.txt` stating which accessions are unavailable and exit with code 1.
  - If at least one accession has a verified source, continue and update `spec.md` to note any unavailable datasets (see T049).
  - Output: `data/manifest.json`, `results/data_gap_summary.txt` (if errors occur).
  - Verification: Run `python code/data_gap_resolver.py`; it produces `data/manifest.json` with valid JSON; if all datasets are unavailable, `results/data_gap_summary.txt` contains a clear error message and the script exits with code 1.

- [ ] T006 [US1] Implement `code/download.py` that downloads raw count matrices for available datasets and validates checksums.
  - Read `data/manifest.json` to identify available datasets.
  - For each available dataset, download the raw file from its `source_url` to `data/raw/{dataset_id}_raw.{ext}`.
  - Compute a SHA-256 checksum of the downloaded file and compare to any pre-computed reference (if available); record the checksum in `data/manifest.json`.
  - If a download fails or checksum mismatches, mark the dataset as "Error" in the manifest and log the failure to `results/run_log.txt`.
  - Output: raw data files in `data/raw/`, updated `data/manifest.json` with checksums and file paths.
  - Verification: Run `python code/download.py`; `data/raw/` contains at least one raw data file; `data/manifest.json` contains a `checksum` field with a 64-character hex string for each downloaded file.

- [ ] T007 [US1] Implement `code/preprocess.py` that applies log-CPM transformation, selects highly-variable genes, samples cells if needed, and computes geometric descriptors on the high-dimensional space.
  - Read each raw count matrix from `data/raw/`.
  - Apply log-CPM transformation: `log2(CPM + 1)` where CPM = (counts / total_counts) * 1e6.
  - Select highly-variable genes using a variance-stabilizing method (e.g., Seurat's method or a simple variance percentile); retain genes up to an elbow point (automatic detection via second derivative or fixed percentile, e.g., top 2000 genes). Record the HVG count in metadata.
  - If `n_cells > 10000`, randomly sample 5000 cells using a deterministic seed derived from `config.SEED` and the dataset ID; otherwise use all cells.
  - Save the processed matrix (cells × HVG genes) as `data/processed/{dataset_id}_matrix.parquet`.
  - Compute **global linearity (Trustworthiness metric, k=15)** on the **sampled high-dimensional space** (the HVG-selected, log-CPM-transformed matrix), comparing neighborhood preservation between the high-dimensional space and a 30-dimensional PCA embedding of the same sampled space. Store as a float in [0, 1].
  - Compute **local continuity (Local Continuity Metric, k=15)** on the **sampled high-dimensional space**, comparing neighborhood preservation in the reverse direction (from embedding to high-D). Store as a float in [0, 1].
  - Write geometric descriptors to `data/processed/{dataset_id}_geometric.json` with fields: `trustworthiness` (float), `local_continuity` (float), `n_cells_sampled` (int), `n_genes_hvg` (int).
  - Output: `data/processed/{dataset_id}_matrix.parquet`, `data/processed/{dataset_id}_geometric.json`.
  - Verification: For each dataset, the Parquet file can be read with `pandas.read_parquet()` and contains non-null numeric values with shape `(n_cells, n_hvg_genes)`. The JSON file parses and contains `trustworthiness` and `local_continuity` as floats in [0, 1].

- [ ] T008 [US1] Implement `code/embeddings.py` that generates three embeddings (PCA, t-SNE, UMAP) from the preprocessed matrix.
  - Read the processed matrix from `data/processed/{dataset_id}_matrix.parquet`.
  - Generate PCA embedding: fit PCA with `n_components=30`, save 30-D coordinates to `data/embeddings/{dataset_id}_PCA.csv`.
  - Generate t-SNE embedding: fit t-SNE with `perplexity=30`, `n_iter=1000`, fixed random seed, save 2-D coordinates to `data/embeddings/{dataset_id}_tSNE.csv`.
  - Generate UMAP embedding: fit UMAP with `n_neighbors=15`, `min_dist=0.1`, fixed random seed, save 2-D coordinates to `data/embeddings/{dataset_id}_UMAP.csv`.
  - Each CSV has columns: `cell_id` (or row index), and numeric columns for each dimension.
  - Write a summary preview (first 5 rows of each embedding) to `results/embeddings_preview.txt`.
  - Output: `data/embeddings/{dataset_id}_PCA.csv`, `data/embeddings/{dataset_id}_tSNE.csv`, `data/embeddings/{dataset_id}_UMAP.csv`, `results/embeddings_preview.txt`.
  - Verification: Each CSV file exists and has `n_cells` rows and the correct number of columns (30 for PCA, 2 for t-SNE and UMAP); `results/embeddings_preview.txt` contains a human-readable preview.

- [ ] T009 [US2] Implement `code/clustering.py` that performs Leiden clustering on each embedding with resolution optimization via Silhouette Score.
  - Read each embedding from `data/embeddings/{dataset_id}_{method}.csv`.
  - For each embedding, sweep Leiden clustering resolution from 0.1 to 1.0 in steps of 0.1 (i.e., resolutions: 0.1, 0.2, 0.3, ..., 1.0).
  - For each resolution, compute the Silhouette Score of the resulting clusters.
  - Select the resolution with the **maximum Silhouette Score** as the optimal resolution.
  - Save cluster assignments to `data/clustering/{dataset_id}_{method}_clusters.csv` with columns: `cell_id`, `cluster_label`, `silhouette_score` (at optimal resolution), `optimal_resolution`.
  - If Leiden fails to converge, retry once with a different random seed; if it fails again, mark the result as "Unavailable" and log the error.
  - Output: `data/clustering/{dataset_id}_{method}_clusters.csv` for each dataset and method.
  - Verification: Each CSV file contains `n_cells` rows; `cluster_label` values are non-negative integers; `silhouette_score` is a float in [-1, 1]; `optimal_resolution` is a float in [0.1, 1.0].

- [ ] T010 [US2] Implement `code/metrics.py` that computes fidelity metrics (ARI, NMI) between Leiden clusters and ground-truth cell-type labels.
  - Read ground-truth cell-type labels from the original dataset metadata (or a dedicated metadata file in `data/processed/{dataset_id}_labels.csv`).
  - Read cluster assignments from `data/clustering/{dataset_id}_{method}_clusters.csv`.
  - Compute Adjusted Rand Index (ARI) between cluster labels and ground-truth labels; ARI ∈ [0, 1] (or [-1, 1] in some definitions).
  - Compute Normalized Mutual Information (NMI) between cluster labels and ground-truth labels; NMI ∈ [0, 1].
  - If ground-truth labels are missing or incomplete, log an error and skip that dataset.
  - Consolidate results into a CSV table `data/metrics/fidelity_results.csv` with columns: `dataset_id`, `method`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`.
  - Output: `data/metrics/fidelity_results.csv`.
  - Verification: The CSV file contains one row per (dataset, method) pair; all numeric columns are within the expected ranges (ARI/NMI ∈ [0, 1], silhouette ∈ [-1, 1], resolution ∈ [0.1, 1.0]); no null values.

---

## Phase 2: Statistical Analysis and Sensitivity Evaluation

- [ ] T011 [US3] Implement `code/stats.py` that fits a statistical model (mixed-effects or fixed-effects ANOVA) to test the effect of dimensionality reduction method on fidelity.
  - Read `data/metrics/fidelity_results.csv` and `data/processed/{dataset_id}_geometric.json` for all datasets.
  - Merge fidelity metrics with geometric descriptors (trustworthiness, local_continuity) on `dataset_id`.
  - Check collinearity: compute Variance Inflation Factor (VIF) for all predictors. If any VIF ≥ 5, log a warning and abort the model with `collinearity_passed = false`.
  - **If `datasets_processed > 1`**: Fit a **mixed-effects model** with formula `fidelity ~ method + (1|dataset)` using `statsmodels` or `scipy.stats`. Compute likelihood-ratio test p-value for the `method` fixed effect.
  - **If `datasets_processed == 1`**: Fit a **fixed-effects ANOVA** with formula `fidelity ~ method`. Compute F-statistic and p-value for the `method` effect.
  - Check normality of residuals via Shapiro-Wilk test; if p < 0.05, note this in the output but proceed (do not abort).
  - Apply Benjamini-Hochberg (FDR) correction to all p-values; use FDR threshold α = 0.05.
  - Write results to `results/statistical_result.json` conforming to `statistical_result.schema.yaml`, with fields: `model_summary` (formula, fixed_effects, vif_values, collinearity_passed), `sensitivity_analysis` (placeholder, filled by T012), `execution_metadata` (placeholder, filled by T013).
  - Output: `results/statistical_result.json`.
  - Verification: JSON parses and validates against the schema; `collinearity_passed` is a boolean; `fixed_effects` is a non-empty array with `term`, `estimate`, `std_error`, `p_value`, `p_value_fdr` for each term; if descriptive mode, `is_descriptive_mode = true`.

- [ ] T012 [US3] Implement `code/sensitivity.py` that performs a sensitivity analysis by sweeping Leiden resolution and Silhouette thresholds.
  - **Leiden-resolution sweep**: For each (dataset, method) pair, re-run Leiden clustering for all resolutions 0.1 to 1.0 (same as T009) and compute ARI/NMI for each resolution (not just the optimal one).
  - Record the variance of ARI and NMI across all resolutions swept.
  - **Silhouette-threshold sweep**: For each (dataset, method) pair, filter clusters to retain only those with Silhouette Score ≥ threshold, for thresholds {0.4, 0.5, 0.6}. Recompute ARI/NMI for each threshold.
  - Record the variance of ARI and NMI across the three thresholds.
  - Compute overall stability metric: `stability_passed = (variance_ari < 0.05) AND (variance_nmi < 0.05)`.
  - Write results to `results/sensitivity_analysis.json` with fields: `leiden_resolutions` (list of swept resolutions), `silhouette_thresholds` (list [0.4, 0.5, 0.6]), `variance_ari`, `variance_nmi`, `stability_passed`.
  - Create a scatter plot `figures/sensitivity_plot.png` showing ARI/NMI (y-axis) vs. Leiden resolution (x-axis) for each method, with separate subplots per dataset.
  - Output: `results/sensitivity_analysis.json`, `figures/sensitivity_plot.png`.
  - Verification: JSON parses and contains `variance_ari`, `variance_nmi`, `stability_passed` (boolean); PNG file exists and is readable as an image with expected axes and legend.

- [ ] T013 [US3] Implement `code/aggregate.py` that consolidates all intermediate results and computes execution metadata.
  - Read all results: `data/metrics/fidelity_results.csv`, `data/processed/*_geometric.json`, `results/statistical_result.json`, `results/sensitivity_analysis.json`, `results/monitoring.csv`.
  - Parse `results/monitoring.csv` to compute total wall-clock time (sum of `wall_time_s`) and peak RAM (max of `peak_ram_gb`).
  - Count datasets processed (rows in `data/manifest.json` with `status = "Available"`) and datasets skipped (rows with `status ≠ "Available"`).
  - Update `results/statistical_result.json` with `execution_metadata`: `peak_memory_bytes` (peak_ram_gb × 1e9), `total_runtime_seconds`, `datasets_processed`, `datasets_skipped`, `exit_code` (0 if all checks pass, 1 otherwise).
  - Aggregate all metrics into a single Parquet dataset `data/results/combined_metrics.parquet` with columns: `dataset_id`, `method`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`, `trustworthiness`, `local_continuity`.
  - Output: updated `results/statistical_result.json`, `data/results/combined_metrics.parquet`.
  - Verification: `results/statistical_result.json` contains `execution_metadata` with all required fields; `data/results/combined_metrics.parquet` can be read with `pandas.read_parquet()` and contains all expected columns.

---

## Phase 3: Validation, Reporting, and Reproducibility

- [ ] T014 [US1] Implement `code/main.py` as the entry point that orchestrates the entire pipeline and handles errors gracefully.
  - Parse command-line arguments: `--config CONFIG_PATH`, `--phase PHASE_NAME` (optional, defaults to "all").
  - Load configuration from `code/config.py`.
  - Call functions in order: `data_gap_resolver()`, `download()`, `preprocess()`, `embeddings()`, `clustering()`, `metrics()`, `stats()`, `sensitivity()`, `aggregate()`.
  - Wrap each phase in a try-except block; log errors to `results/run_log.txt` and continue to the next phase (or abort if critical, e.g., no datasets available).
  - On successful completion, print a summary to stdout and `results/run_log.txt` with counts of datasets processed, methods evaluated, and key statistics (e.g., mean ARI, p-value for method effect).
  - Exit with code 0 on success, code 1 on critical failure.
  - Output: `code/main.py`, `results/run_log.txt` (appended with each run).
  - Verification: `python code/main.py --config code/config.py` executes without errors (or logs expected errors); `results/run_log.txt` contains a timestamped log of all phases; final exit code is 0.

- [ ] T015 [US1] Implement `code/tests/test_preprocessing.py` with unit tests for the preprocessing pipeline.
  - Test that log-CPM transformation produces non-negative values and sums to ~1e6 per cell (before log).
  - Test that HVG selection retains the expected number of genes (within ±10% of the elbow point estimate).
  - Test that cell sampling (if n_cells > 10000) produces exactly 5000 cells.
  - Test that geometric descriptors (Trustworthiness, Local Continuity) are floats in [0, 1].
  - Run tests on a small synthetic dataset (e.g., 100 cells, 500 genes) to ensure correctness.
  - Output: `code/tests/test_preprocessing.py`, `results/test_preprocessing_report.txt`.
  - Verification: `python -m pytest code/tests/test_preprocessing.py -v` runs all tests and reports pass/fail; all tests pass.

- [ ] T016 [US2] Implement `code/tests/test_clustering.py` with unit tests for clustering and fidelity metrics.
  - Test that Leiden clustering produces valid cluster labels (non-negative integers, no gaps).
  - Test that Silhouette Score is computed correctly and is in [-1, 1].
  - Test that ARI and NMI are computed correctly against ground-truth labels (validate against a small hand-crafted example).
  - Test that resolution sweep produces different clusterings for different resolutions.
  - Output: `code/tests/test_clustering.py`, `results/test_clustering_report.txt`.
  - Verification: `python -m pytest code/tests/test_clustering.py -v` runs all tests and reports pass/fail; all tests pass.

- [ ] T017 [US3] Run the complete pipeline on real data and validate all outputs against the specification.
  - Execute `python code/main.py --config code/config.py` on all available datasets (at least one, up to three).
  - Verify that all output files are created: `data/processed/*`, `data/embeddings/*`, `data/clustering/*`, `data/metrics/*`, `results/statistical_result.json`, `results/sensitivity_analysis.json`, `data/results/combined_metrics.parquet`.
  - Check that all numeric outputs are within expected ranges (ARI/NMI ∈ [0, 1], Silhouette ∈ [-1, 1], geometric descriptors ∈ [0, 1]).
  - Verify that total runtime ≤ 21600 seconds and peak memory ≤ 7 GB (from `execution_metadata` in `results/statistical_result.json`).
  - Verify that statistical model output includes p-values, FDR-corrected p-values, and VIF values; collinearity check passes (all VIF < 5) or is documented.
  - Output: all data artifacts, `results/statistical_result.json`, `results/sensitivity_analysis.json`, `data/results/combined_metrics.parquet`, `results/run_log.txt`.
  - Verification: `python -c "import pandas; df = pandas.read_parquet('data/results/combined_metrics.parquet'); print(df.shape, df.columns.tolist())"` prints shape and column names; all numeric columns are within expected ranges; `results/statistical_result.json` validates against schema.

- [ ] T018 [US1] Generate a concise methods-and-results markdown report and prepare the paper handoff.
  - Create `paper/summary.md` with sections: Methods, Results, Limitations.
  - **Methods**: Programmatically pull dataset descriptions, preprocessing steps, embedding hyperparameters, and clustering procedure from `code/config.py` and `data/manifest.json`. Describe the statistical model (mixed-effects or fixed-effects ANOVA) and sensitivity analysis.
  - **Results**: Programmatically pull summary statistics from `data/results/combined_metrics.parquet` and `results/statistical_result.json`: mean/std ARI and NMI by method, p-value for method effect, VIF values, sensitivity stability verdict.
  - **Limitations**: Note if only one dataset is available (descriptive case study only, not generalizable). Mention any datasets that were unavailable or skipped. Note any collinearity warnings or normality violations.
  - Include inline references to figures: `figures/sensitivity_plot.png`.
  - Output: `paper/summary.md`.
  - Verification: Render `paper/summary.md` to HTML with `pandoc paper/summary.md -o paper/summary.html` without errors; the HTML contains all expected tables, statistics, and image references.

- [ ] T019 [US1] Document the reproducibility checklist and verify that the pipeline can be re-run from the documented inputs.
  - Create `paper/REPRODUCIBILITY.md` with:
    - Declared random seed (from `code/config.py`).
    - Verified data sources (URLs from `data/manifest.json`).
    - Exact package versions (from `code/requirements.txt`).
    - Step-by-step instructions to re-run the pipeline: install dependencies, run `python code/main.py --config code/config.py`, expected outputs.
    - Assertion checks: verify that total runtime ≤ 6 h, peak memory ≤ 7 GB, and all output files are present.
  - Re-run the pipeline from scratch (clean environment, fresh clone) and verify that all outputs are reproduced identically (or with negligible numerical differences due to floating-point precision).
  - Output: `paper/REPRODUCIBILITY.md`, `results/reproducibility_check.txt` (summary of re-run).
  - Verification: `cat paper/REPRODUCIBILITY.md` contains all required sections; `results/reproducibility_check.txt` confirms that re-run succeeded and outputs match.

---

## Summary of Requirements Coverage

| Requirement | Task ID | Verification |
|---|---|---|
| **FR-001**: Download and preprocess scRNA-seq datasets | T006, T007 | Raw files in `data/raw/`, processed matrices in `data/processed/` |
| **FR-002**: Compute global linearity (Trustworthiness) | T007 | `data/processed/{dataset_id}_geometric.json` contains `trustworthiness` ∈ [0, 1] |
| **FR-003**: Compute local continuity (LCA) | T007 | `data/processed/{dataset_id}_geometric.json` contains `local_continuity` ∈ [0, 1] |
| **FR-004**: Generate PCA, t-SNE, UMAP embeddings | T008 | CSV files in `data/embeddings/` with correct dimensions |
| **FR-005**: Calculate ARI and NMI for Leiden clusters | T009, T010 | `data/metrics/fidelity_results.csv` with ARI/NMI ∈ [0, 1] |
| **FR-006**: Fit mixed-effects model (method effect) | T011 | `results/statistical_result.json` with p-value for method term |
| **FR-007**: Sensitivity sweep (Silhouette thresholds {0.4, 0.5, 0.6}) | T012 | `results/sensitivity_analysis.json` with variance_ari, variance_nmi |
| **FR-008**: Benjamini-Hochberg correction | T011 | `results/statistical_result.json` with `p_value_fdr` for all terms |
| **SC-001**: Stability variance < 0.05 | T012 | `sensitivity_analysis.json` with `stability_passed` boolean |
| **SC-002**: Method effect p-value < 0.05 (after FDR) | T011 | `statistical_result.json` with FDR-adjusted p-value |
| **SC-003**: Peak memory ≤ 7 GB | T013 | `execution_metadata.peak_memory_bytes` ≤ 7,000,000,000 |
| **SC-004**: Total runtime ≤ 6 h (21600 s) | T013 | `execution_metadata.total_runtime_seconds` ≤ 21600 |
| **SC-005**: Collinearity check (VIF < 5) | T011 | `model_summary.collinearity_passed = true` |
| **US-1**: End-to-end pipeline on single dataset | T017 | All outputs produced; runtime/memory within limits |
| **US-2**: Fidelity metrics for all methods | T010, T017 | `fidelity_results.csv` with one row per (dataset, method) pair |
| **US-3**: Statistical analysis and sensitivity | T011, T012, T017 | `statistical_result.json` and `sensitivity_analysis.json` valid |

---

## Execution Order and Dependencies

1. **T001–T004**: Setup (directories, config, utilities) — independent, can run in parallel.
2. **T005**: Data-gap resolution — must run before T006 (blocks on no data).
3. **T006**: Download — depends on T005; produces raw files for T007.
4. **T007**: Preprocess — depends on T006; produces matrices for T008.
5. **T008**: Embeddings — depends on T007; produces embeddings for T009.
6. **T009**: Clustering — depends on T008; produces cluster labels for T010.
7. **T010**: Metrics — depends on T009; produces fidelity table for T011.
8. **T011**: Stats — depends on T010; produces model output for T013.
9. **T012**: Sensitivity — depends on T010 (uses fidelity results); produces sensitivity output for T013.
10. **T013**: Aggregate — depends on T011, T012; consolidates all results.
11. **T014**: Main orchestrator — depends on all phases; runs them in order.
12. **T015–T016**: Unit tests — can run after their corresponding implementation tasks.
13. **T017**: Full pipeline validation — depends on T014; verifies end-to-end correctness.
14. **T018–T019**: Reporting and reproducibility — depend on T017; final handoff.

---

**Notes**

- All random operations use `config.SEED` (42) to guarantee reproducibility.
- Every script logs to `results/run_log.txt` for traceability.
- Resource monitoring via `code/utils.py` tracks runtime and memory for compliance with SC-003 and SC-004.
- If fewer than 3 datasets are available after T005, the pipeline continues in **descriptive case-study mode** (fixed-effects ANOVA, no mixed-effects model); see T011 for conditional logic.
- All JSON outputs validate against their respective schemas (in `specs/001-statistical-evaluation-of-dimensionality/contracts/`).

---

*End of tasks.md*
