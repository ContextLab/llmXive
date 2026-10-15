# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Input**: `spec.md`, `plan.md`, data‑model, contracts, and reviewer feedback.  
All tasks are unchecked (`- [ ]`) so that the verifier can run them and produce the required artifacts.

## Phase 0 – Data‑Gap Resolution (Critical Blocker)

- [ ] T001 [US0] Create the canonical project directory tree.  
  ```
  mkdir -p data/raw data/processed data/embeddings data/clustering data/metrics results code tests
  ```  
  **Verification**: Run `tree -L 2 .` and confirm the directories exist; output saved to `results/dir_structure.txt`.

- [ ] T002 [P] Create `environment.yml` with pinned scientific dependencies and generate a flat `code/requirements.txt` via `pip‑compile`.  
  **Output**: `environment.yml`, `code/requirements.txt`.  
  **Verification**: `conda env export` matches `environment.yml`; `pip‑freeze` matches `requirements.txt`.

- [ ] T003 [P] Implement `code/config.py` that defines all project paths, a global random seed, and the list of GEO accession IDs (`GSE131907`, `GSE111322`, `GSE150728`).  
  **Output**: `code/config.py`.  
  **Verification**: Import the module in a REPL and print `config.DATA_RAW`, `config.SEED`.

- [ ] T029 [P] Implement a `ResourceMonitor` in `code/utils.py` that can wrap any shell command, abort if peak RSS > 7 GB, and write a row to `results/monitoring.csv` (columns: step, wall_time_s, peak_ram_gb).  
  **Output**: `code/utils.py`, `results/monitoring.csv` (initial header row).  
  **Verification**: Run `python -c "from code.utils import ResourceMonitor; ResourceMonitor.run(['echo','test'])"` and check the CSV entry.

- [ ] T021 [P] Add a parser in `code/utils.py` that reads the `/usr/bin/time -v` log produced by the `ResourceMonitor`, extracts `Elapsed (wall clock) time` and `Maximum resident set size`, and appends the values to `results/monitoring.csv`.  
  **Verification**: Simulate a log file, run the parser, and confirm the CSV row is added.

- [ ] T054 [P] Add a Snakemake rule `verify_data_availability` that executes `code/data_gap_resolver.py` before any `download` rule; the rule must halt the workflow with exit code 1 and a clear error message if **no** raw‑count source is found.  
  **Output**: `Snakefile` fragment for the rule.  
  **Verification**: Run `snakemake -n verify_data_availability` on an empty `data/raw/` and confirm the workflow stops with the expected error.

- [ ] T028 [P] Add a Snakemake rule `resource_monitor` that aggregates all `results/monitoring.csv` rows, checks that total wall‑clock time ≤ 21 600 s and peak RAM ≤ 7 GB, and writes a summary file `results/monitoring_summary.csv`. The rule must fail the workflow if either limit is exceeded.  
  **Output**: `Snakefile` fragment for `resource_monitor`.  
  **Verification**: Inject a row violating a limit and run the rule; it should exit with a non‑zero code.

- [ ] T030 [P] Create a GitHub Actions workflow `.github/workflows/research.yml` that (a) sets up the conda environment, (b) runs `snakemake --cores 2`, and (c) fails if the job exceeds 6 h or 7 GB RAM (the failure is enforced by the `resource_monitor` rule).  
  **Output**: `.github/workflows/research.yml`.  
  **Verification**: Validate the YAML with `act` locally or GitHub’s linting; ensure the job name is `Research Pipeline`.

- [ ] T032 [P] Within the same workflow, add a step that reads `results/monitoring_summary.csv` and explicitly asserts `total_runtime_seconds <= 21600` and `peak_ram_gb <= 7`. The step should `exit 1` on violation.  
  **Verification**: Run the workflow on a small dataset and confirm the step passes.

- [ ] T049 [P] Update `plan.md` to reflect the **Mixed‑Effects Model** (FR‑006) as the primary analysis and the **Silhouette‑threshold sweep** `{0.4,0.5,0.6}` (FR‑007) as the required sensitivity analysis. Add a short “Resolved inconsistency” note.  
  **Output**: Updated `plan.md`.  
  **Verification**: Diff the file before/after; the new sections must be present.

## Phase 1 – Data Ingestion & Pre‑processing

- [ ] T060 [US1] Implement `code/download.py` that (a) queries GEO (using `GEOparse`) for verified raw‑count URLs of the three accession IDs, (b) downloads each file, (c) computes a SHA‑256 checksum, and (d) writes a manifest `data/manifest.json` compliant with `dataset.schema.yaml`.  
  **Output**: `code/download.py`, `data/manifest.json`.  
  **Verification**: Run the script; the JSON must contain a `datasets` array with `status: "Available"` for each successfully downloaded file and correct checksums.

- [ ] T062 [US1] Implement `code/preprocess.py` that (a) reads the raw count matrix, (b) applies a log‑CPM transformation, (c) selects highly‑variable genes using a variance‑stabilizing elbow method, (d) if `n_cells > 10 000` randomly samples 10 000 cells (deterministic seed derived from `config.SEED` and the accession), and (e) writes the processed matrix to `data/processed/{dataset}_matrix.parquet`. The same script must also compute **global linearity (Trustworthiness, k=15)** and **local continuity (LCA, k=15)** on the **sampled high‑dimensional space** and write `data/processed/{dataset}_geometric.json`.  
  **Verification**: After running on a test dataset, confirm the Parquet file exists, contains non‑null values, and the JSON contains keys `trustworthiness` and `local_continuity` with floats in [0, 1].

## Phase 2 – Embedding & Clustering

- [ ] T064 [US2] Implement `code/embeddings.py` that (a) loads the processed matrix, (b) generates three embeddings (PCA – 30 PCs, t‑SNE – perplexity 30, n_iter 1000, UMAP – n_neighbors 15, min_dist 0.1) with fixed seeds, (c) saves each as `data/embeddings/{dataset}_{method}.csv`, and (d) calls `code/clustering.py` (see next task) to obtain Leiden clusters.  
  **Verification**: Each CSV must have `n_cells` rows and the correct number of columns (2 D or 3 D); a preview of the first five rows is written to `results/embeddings_preview.txt`.

- [ ] T065 [US3] Implement `code/clustering.py` that (a) runs Leiden clustering on each embedding, (b) sweeps resolution values from 0.1 to 1.0 in steps of 0.1, (c) computes the Silhouette Score for each resolution, (d) selects the resolution with the maximal Silhouette Score, (e) saves the final cluster labels and the optimal resolution to `data/clustering/{dataset}_{method}_clusters.csv`, and (f) records the chosen Silhouette Score in the same file.  
  **Verification**: The CSV contains columns `cell_id`, `cluster_label`, `silhouette_score`, `optimal_resolution`; the file size > 0 KB.

## Phase 3 – Fidelity Evaluation & Statistical Modeling

- [ ] T066 [US3] Implement `code/metrics.py` that (a) loads the ground‑truth cell‑type labels, (b) compares them to the Leiden clusters for each embedding, (c) computes Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI), (d) writes a consolidated table `data/metrics/fidelity_results.csv` with columns `dataset_id, method, ari, nmi, silhouette_score, optimal_resolution`.  
  **Verification**: All numeric columns are within the [0, 1] range; no nulls.

- [ ] T067 [US3] Implement `code/stats.py` that (a) merges the fidelity table with geometric descriptors, (b) checks VIF for all predictors (must be < 5), (c) fits a **mixed‑effects model** `fidelity ~ method + (1|dataset)` when `datasets_processed > 1` or a **fixed‑effects ANOVA** `fidelity ~ method` otherwise, (d) applies Benjamini‑Hochberg correction to all p‑values, (e) writes the full model output to `results/statistical_result.json` conforming to `statistical_result.schema.yaml`.  
  **Verification**: JSON validates against the schema; `collinearity_passed` is true; `is_descriptive_mode` is false when >1 dataset.

- [ ] T068 [US3] Implement `code/sensitivity.py` that (a) re‑runs the clustering step for the three **Silhouette thresholds** `{0.4, 0.5, 0.6}` (i.e., only keep clusterings whose Silhouette Score meets the threshold), (b) also performs a **Leiden‑resolution sweep** `0.1 … 1.0`, (c) records the variance of ARI and NMI across all sweeps, (d) writes `results/sensitivity_analysis.json` (schema‑validated), and (e) creates a scatter plot `figures/sensitivity_plot.png`.  
  **Verification**: JSON contains `variance_ari`, `variance_nmi`, `stability_passed`; the PNG file exists.

- [ ] T069 [P] Aggregate all intermediate results (`data/processed/*`, `data/embeddings/*`, `data/clustering/*`, `data/metrics/*`, `results/statistical_result.json`, `results/sensitivity_analysis.json`) into a single Parquet dataset `data/results/combined_metrics.parquet` for downstream reporting.  
  **Verification**: Parquet file can be read with `pandas.read_parquet` and contains all expected columns.

## Phase 4 – Reporting & Handoff

- [ ] T070 [P] Generate a concise methods‑and‑results markdown file `paper/summary.md` that programmatically pulls values from `data/results/combined_metrics.parquet` and the figures in `figures/`. Include a “Limitations” section that mentions the case‑study fallback if only one dataset is available.  
  **Verification**: Render the markdown to HTML locally (`pandoc`) without errors; the HTML contains the expected tables and the plot image.

---

**Notes**

- All random operations use the seed defined in `code/config.py` to guarantee reproducibility.  
- Every script writes a short log entry to `results/run_log.txt` for traceability.  
- Tasks marked `[P]` can be executed in parallel as they operate on independent files.  
- The pipeline aborts early if Phase 0 determines that no raw counts are available (as required by SC‑003/SC‑004).  

--- 

*End of `tasks.md`.*
