# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and prior reviewer feedback.  
All tasks are presented as unchecked checkboxes; each task lists the concrete artifact(s) it creates and a verification step that can be executed automatically. The ordering respects data flow – no task consumes an artifact before it is produced.

---

## Phase 0 – Project scaffolding & data‑availability gate

- [ ] T001 [P] [US1] **Create project directory layout, configuration, and quick‑start documentation**
  - Create `code/config.py` defining global constants: `SEED=42`, `GEO_ACCESSIONS=["GSE131907", "GSE111322", "GSE150728"]`, `SAMPLE_CELLS_THRESHOLD=10000`, `SAMPLE_SIZE=5000`, `LEIDEN_RESOLUTIONS=[0.1, 0.2, ..., 1.0]`, `SILHOUETTE_THRESHOLDS=[0.4, 0.5, 0.6]`, `MEMORY_LIMIT_BYTES=7000000000`, `RUNTIME_LIMIT_SECONDS=21600`.
  - Create `quickstart.md` documenting the single runnable command: `python code/main.py --config code/config.py`.
  - Create directory tree via `pathlib.Path.mkdir(parents=True, exist_ok=True)` for: `data/raw/`, `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `data/results/`, `figures/`, `paper/`, `code/tests/`.
  - Write `results/dir_listing.txt` with output of `find . -type d | sort` showing all created directories.
  - *Verification*: Execute `python -c "import sys; sys.path.insert(0, '.'); from code.config import SEED, GEO_ACCESSIONS; assert SEED == 42; assert len(GEO_ACCESSIONS) == 3"` (exit 0). Confirm `results/dir_listing.txt` contains each required directory name. Confirm `quickstart.md` exists and contains the exact command `python code/main.py --config code/config.py`.

- [ ] T002 [P] [US1] **Implement resource‑monitoring utility with peak‑RAM and wall‑clock recording**
  - Create `code/utils.py` with:
    * `get_logger(name)` function returning a configured Python logger.
    * `MemoryLimitExceeded` exception class.
    * `ResourceMonitor` class with method `run(step_name, fn, *args, **kwargs)` that:
      - Records wall‑clock time via `time.perf_counter()` before and after calling `fn(*args, **kwargs)`.
      - Samples peak RSS via `psutil.Process().memory_info().rss` during execution (e.g., via a background thread or periodic sampling).
      - Appends a row `step_name,wall_time_s,peak_ram_bytes` to `results/monitoring.csv`.
      - Raises `MemoryLimitExceeded` if peak RSS exceeds `config.MEMORY_LIMIT_BYTES`.
      - Returns the result of `fn(*args, **kwargs)`.
    * Initialize `results/monitoring.csv` with header `step,wall_time_s,peak_ram_bytes` on first write.
  - Run a self‑test: call `ResourceMonitor().run("dummy_test", lambda: None)` at module load, writing a dummy row to the CSV.
  - *Verification*: Execute `python code/utils.py` (exit 0). Confirm `results/monitoring.csv` exists, contains header `step,wall_time_s,peak_ram_bytes`, and has at least one row with `dummy_test`. Confirm that `MemoryLimitExceeded` is importable and `get_logger` returns a logger object.

- [ ] T003 [P] [US1] **Resolve data availability: attempt to download raw count matrices and produce a validated manifest**
  - Create `code/data_gap_resolver.py` that:
    * Iterates over `config.GEO_ACCESSIONS`.
    * For each accession, attempts to download raw count matrix via `GEOparse.get_GEO(accession, destdir="data/raw/", silent=True)`.
    * If GEOparse fails, tries a curated list of supplementary URLs (hard‑coded, no guessing; e.g., known FTP links for GSE131907, GSE111322, GSE150728 if available in public documentation).
    * On successful download, records the source URL, writes file to `data/raw/{accession}_raw.{ext}`, computes SHA‑256 checksum via `hashlib.sha256(open(..., 'rb').read()).hexdigest()`.
    * Appends entry to `data/manifest.json` with fields: `dataset_id`, `source_url`, `status` (`"Available"` or `"Unavailable"`), `error_message` (if any), `checksum`, `raw_file_path`, `processed_file_path` (null initially), `generated_at` (ISO 8601 timestamp).
    * If **no** accession resolves to `"Available"`, writes `results/data_gap_summary.txt` listing all attempted URLs and failure reasons, then exits with code 1.
    * If **at least one** accession is `"Available"`, exits with code 0.
  - *Verification*: Run `python code/data_gap_resolver.py` (exit 0 or 1). If exit 0, confirm `data/manifest.json` exists and validates against `specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml` via `python -m jsonschema -i data/manifest.json specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml` (exit 0). Confirm at least one entry has `"status": "Available"`. If exit 1, confirm `results/data_gap_summary.txt` exists and lists attempted URLs.

---

## Phase 1 – Pre‑processing, geometric diagnostics, and embeddings

- [ ] T004 [P] [US1] **Preprocess raw matrices, apply log‑CPM, select HVGs, sample cells, and compute geometric diagnostics**
  - Create `code/preprocess.py` that:
    * Reads `data/manifest.json` and processes each dataset with `status == "Available"`.
    * Loads raw count matrix from `raw_file_path` (handles CSV, MTX, or HDF5 formats).
    * Validates that counts are non‑negative integers.
    * Applies log‑CPM transformation: `log2((counts / row_sum) * 1e6 + 1)` where `row_sum` is the sum of counts per cell.
    * Selects highly variable genes (HVGs) using Seurat‑style variance‑stabilizing dispersion: compute mean and variance per gene, fit a local polynomial to the mean‑variance trend, compute dispersion as (variance / trend), select genes with dispersion > elbow point (determined automatically via knee detection or top 2000 HVGs as fallback).
    * If `n_cells > config.SAMPLE_CELLS_THRESHOLD` (10000), randomly sample exactly `config.SAMPLE_SIZE` (5000) cells using seed `hash(config.SEED + dataset_id) % 2^32` for deterministic reproducibility.
    * Computes **global linearity** = `sklearn.manifold.trustworthiness(high_dim_sampled, pca30_sampled, n_neighbors=15)` where `pca30_sampled` is PCA fit on the sampled high‑dimensional matrix. If `n_cells < 500` logs warning and stores `null`.
    * Computes **local continuity** = `sklearn.manifold.trustworthiness(pca30_sampled, high_dim_sampled, n_neighbors=15)` (inverse direction). If `n_cells < 500` stores `null`.
    * Writes processed matrix to `data/processed/{dataset_id}_matrix.parquet` (sparse Parquet format if >90% zeros).
    * Writes geometric descriptors to `data/processed/{dataset_id}_geometric.json` with keys: `trustworthiness` (float or null), `local_continuity` (float or null), `n_cells_sampled` (int), `n_genes_hvg` (int), `n_genes_original` (int).
    * Wraps each dataset processing with `ResourceMonitor.run(f"preprocess_{dataset_id}", ...)`.
  - *Verification*: For every `"Available"` dataset, `pandas.read_parquet("data/processed/{dataset_id}_matrix.parquet")` returns a non‑empty DataFrame with shape `(n_cells_sampled, n_genes_hvg)` where `n_cells_sampled ≤ config.SAMPLE_SIZE`. JSON file parses and contains numeric values in `[0,1]` (or `null`). `results/monitoring.csv` contains a row with `step` matching `preprocess_*`.

- [ ] T005 [P] [US1] **Generate PCA, t‑SNE, and UMAP embeddings from the sampled, preprocessed matrix**
  - Create `code/embeddings.py` that:
    * Loads each processed Parquet from `data/processed/{dataset_id}_matrix.parquet`.
    * **PCA** (`sklearn.decomposition.PCA(n_components=30, random_state=config.SEED)`): fit on sampled matrix, output 30 principal components. Write to `data/embeddings/{dataset_id}_PCA.csv` with columns `cell_id` (index) and `PC1`, `PC2`, ..., `PC30`.
    * **t‑SNE** (`sklearn.manifold.TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=config.SEED, n_jobs=-1)`): fit on sampled matrix. Write to `data/embeddings/{dataset_id}_tSNE.csv` with columns `cell_id`, `TSNE1`, `TSNE2`.
    * **UMAP** (`umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=config.SEED)`): fit on sampled matrix. Write to `data/embeddings/{dataset_id}_UMAP.csv` with columns `cell_id`, `UMAP1`, `UMAP2`.
    * Each embedding step wrapped with `ResourceMonitor.run(f"embed_{method}_{dataset_id}", ...)`.
  - *Verification*: For each embedding CSV, `pandas.read_csv` returns a DataFrame with exactly `n_cells_sampled` rows and the correct number of numeric columns (30 for PCA, 2 for t‑SNE/UMAP). No missing values. Corresponding rows in `results/monitoring.csv` exist with `step` matching `embed_PCA_*`, `embed_tSNE_*`, `embed_UMAP_*`.

- [ ] T006 [P] [US2] **Perform Leiden clustering with resolution optimized by Silhouette Score**
  - Create `code/clustering.py` that:
    * For each embedding CSV in `data/embeddings/`, loads the 2D or 30D coordinates.
    * Builds a k‑NN graph using `scanpy.pp.neighbors(n_neighbors=15)`.
    * Runs Leiden clustering (`leidenalg.find_partition`) for each resolution in `config.LEIDEN_RESOLUTIONS` (0.1, 0.2, ..., 1.0).
    * For each resolution, computes mean Silhouette Score (`sklearn.metrics.silhouette_score(embedding, labels)`).
    * Selects the resolution that maximizes Silhouette Score.
    * On failure (e.g., Leiden convergence timeout), retries once with a different random seed; if still fails, writes `"Unavailable"` for that embedding.
    * Writes `data/clustering/{dataset_id}_{method}_clusters.csv` with columns: `cell_id`, `cluster_label` (non‑negative int or literal string `"Unavailable"`), `silhouette_score` (float or `"Unavailable"`), `optimal_resolution` (float or `"Unavailable"`).
  - *Verification*: Each clustering CSV has exactly `n_cells_sampled` rows. `cluster_label` is either a non‑negative integer or the string `"Unavailable"`. `silhouette_score` is numeric in `[-1, 1]` or `"Unavailable"`. `optimal_resolution` is numeric in `[0.1, 1.0]` or `"Unavailable"`.

- [ ] T007 [P] [US2] **Compute fidelity metrics (ARI & NMI) against ground‑truth cell‑type labels**
  - Create `code/metrics.py` that:
    * Extracts ground‑truth cell‑type labels from `data/raw/` (either from GEO metadata file or a separate `{dataset_id}_labels.csv` produced during data gap resolution).
    * Joins ground‑truth labels with clustering results from `data/clustering/{dataset_id}_{method}_clusters.csv`.
    * For each (dataset, method) pair, computes:
      - **ARI** = `sklearn.metrics.adjusted_rand_score(ground_truth, cluster_labels)`.
      - **NMI** = `sklearn.metrics.normalized_mutual_info_score(ground_truth, cluster_labels)`.
    * If ground‑truth labels are missing or clustering is `"Unavailable"`, writes `"Unavailable"` for that row.
    * Writes `data/metrics/fidelity_results.csv` with columns: `embedding_id`, `method`, `dataset_id`, `ari` (float in [0,1] or `"Unavailable"`), `nmi` (float in [0,1] or `"Unavailable"`), `silhouette_score`, `optimal_resolution`, `runtime_seconds`, `peak_ram_gb`.
  - *Verification*: CSV has one row per (dataset_id, method) where data are available. Numeric fields are in `[0, 1]` or the literal string `"Unavailable"`. CSV validates against `specs/001-statistical-evaluation-of-dimensionality/contracts/fidelity_results.schema.yaml`.

---

## Phase 2 – Statistical modelling, sensitivity analysis, and aggregation

- [ ] T008 [P] [US3] **Fit statistical model (Fixed‑Effects ANOVA or Mixed‑Effects when data permit) and apply Benjamini‑Hochberg correction**
  - Create `code/stats.py` that:
    * Loads `data/metrics/fidelity_results.csv` and merges with geometric descriptors from `data/processed/*_geometric.json`.
    * Counts the number of datasets with `status == "Available"` in `data/manifest.json`.
    * **If ≥2 datasets**: Fits a mixed‑effects model `fidelity ~ method + (1|dataset)` using `statsmodels.formula.api.mixedlm(data, groups=data['dataset_id'])`. Extracts fixed‑effects coefficients, standard errors, t‑statistics, and p‑values.
    * **If exactly 1 dataset**: Fits a fixed‑effects ANOVA `fidelity ~ method` via `statsmodels.formula.api.ols(...).fit()` and computes an F‑test. Sets `is_descriptive_mode = true` in output.
    * **Collinearity check**: Computes Variance Inflation Factor (VIF) for dummy‑coded `method` predictor using `statsmodels.stats.outliers_influence.variance_inflation_factor`. If any VIF ≥ 5, sets `collinearity_passed = false` and logs warning (does not abort, but flags the result).
    * **Normality check**: Performs Shapiro‑Wilk test on residuals; if p < 0.05, logs that normality is violated (falls back to Kruskal‑Wallis if requested, but primary output is ANOVA).
    * Applies **Benjamini‑Hochberg correction** to all p‑values: compute FDR thresholds and adjust p‑values via `statsmodels.stats.multitest.multipletests(..., method='fdr_bh')`.
    * Writes `results/statistical_result.json` conforming to `specs/001-statistical-evaluation-of-dimensionality/contracts/statistical_result.schema.yaml`, including:
      - `model_summary.formula` (string).
      - `model_summary.fixed_effects` (list of dicts with `term`, `estimate`, `std_error`, `p_value`, `p_value_fdr`).
      - `model_summary.random_effects_variance` (null for Fixed‑Effects).
      - `model_summary.vif_values` (dict of predictor → VIF).
      - `model_summary.collinearity_passed` (boolean).
      - `is_descriptive_mode` (boolean, true if only 1 dataset).
  - *Verification*: JSON validates against schema. `model_summary.collinearity_passed` is a boolean. `fixed_effects` contains required fields. When descriptive mode is used, `is_descriptive_mode` is `true`. All p‑values in `p_value_fdr` are in `[0, 1]` and satisfy FDR threshold.

- [ ] T009 [P] [US3] **Run sensitivity analysis (Leiden‑resolution sweep) and produce summary statistics and plot**
  - Create `code/sensitivity.py` that:
    * Re‑computes ARI/NMI for every resolution in `config.LEIDEN_RESOLUTIONS` (0.1, 0.2, ..., 1.0) by re‑running Leiden clustering on each embedding with each resolution and re‑computing ARI/NMI against ground‑truth labels.
    * For each (dataset, method) pair, collects the ARI and NMI values across all resolutions.
    * Computes variance of ARI across resolutions: `var_ari = numpy.var([ari_r1, ari_r2, ..., ari_r10])`.
    * Computes variance of NMI across resolutions: `var_nmi = numpy.var([nmi_r1, nmi_r2, ..., nmi_r10])`.
    * Sets `stability_passed = (var_ari < 0.05) and (var_nmi < 0.05)` (SC‑001 criterion).
    * Writes `results/sensitivity_analysis.json` with structure:
      - `thresholds` (list of floats: 0.1, 0.2, ..., 1.0).
      - `variance_ari` (float).
      - `variance_nmi` (float).
      - `stability_passed` (boolean).
    * Writes `figures/sensitivity_data.csv` with columns: `dataset_id`, `method`, `resolution`, `ari`, `nmi`.
    * Generates `figures/sensitivity_plot.png` using matplotlib:
      - X‑axis: Leiden resolution (0.1 to 1.0).
      - Y‑axis (left): ARI; Y‑axis (right): NMI.
      - One line per method (PCA, t‑SNE, UMAP), faceted by dataset.
      - Include a horizontal dashed line at the primary result's ARI/NMI (from T008) for reference.
  - *Verification*: JSON parses and contains numeric `variance_ari`, `variance_nmi` and boolean `stability_passed`. CSV has rows for every (dataset, method, resolution) combination. PNG file opens without error (confirmed via `file figures/sensitivity_plot.png` reporting an image MIME type).

- [ ] T010 [P] [US1] **Aggregate all metrics into a unified Parquet file and enrich statistical result with execution metadata**
  - Create `code/aggregate.py` that:
    * Reads `data/metrics/fidelity_results.csv`, all geometric JSON files from `data/processed/`, `results/statistical_result.json`, `results/sensitivity_analysis.json`, and `results/monitoring.csv`.
    * Merges fidelity metrics with geometric descriptors on (dataset_id, method).
    * Computes:
      - `peak_memory_bytes` = max of `peak_ram_bytes` column in `results/monitoring.csv`.
      - `total_runtime_seconds` = sum of `wall_time_s` column.
      - `datasets_processed` = count of entries in `data/manifest.json` with `status == "Available"`.
      - `datasets_skipped` = count with status not `"Available"`.
      - `exit_code` = 0 if no abort condition (see Phase 0), else 1.
    * Updates `results/statistical_result.json` with these values in the `execution_metadata` section.
    * Writes `data/results/combined_metrics.parquet` containing columns: `dataset_id`, `method`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`, `trustworthiness`, `local_continuity`, `runtime_seconds`, `peak_ram_gb`.
  - *Verification*: `pandas.read_parquet("data/results/combined_metrics.parquet")` succeeds and returns a DataFrame with all listed columns. `results/statistical_result.json` now includes a complete `execution_metadata` object with numeric `peak_memory_bytes`, `total_runtime_seconds`, integer `datasets_processed` and `datasets_skipped`, and integer `exit_code`.

---

## Phase 3 – Testing, end‑to‑end execution, and documentation

- [ ] T011 [P] [US1] **Add focused unit‑tests for preprocessing, embeddings, clustering, and metrics**
  - Create `code/tests/test_preprocess.py`:
    * Load a small real fixture matrix (e.g., `data/fixtures/fixture_counts.parquet` with ~100 cells, ~5000 genes).
    * Test that log‑CPM transformation produces non‑negative values.
    * Test that HVG selection returns `n_genes_hvg > 0` and `n_genes_hvg < n_genes_original`.
    * Test that sampling yields exactly `config.SAMPLE_SIZE` rows when applicable.
  - Create `code/tests/test_embeddings.py`:
    * Run PCA, t‑SNE, UMAP on a tiny processed matrix (e.g., 50 cells, 100 genes).
    * Assert each embedding CSV has the expected number of columns and no NaN values.
  - Create `code/tests/test_clustering.py`:
    * Run Leiden on a synthetic 30‑cell 2D embedding.
    * Assert that ARI between identical label vectors equals 1.0.
    * Assert that Silhouette scores lie in `[-1, 1]`.
  - Create `code/tests/test_metrics.py`:
    * Verify that ARI/NMI return values in `[0, 1]` for known small cases.
  - Create `code/tests/test_utils.py`:
    * Confirm that `ResourceMonitor.run` appends a row to `results/monitoring.csv`.
    * Confirm that the CSV header is correct.
    * Mock a function that reports inflated RSS and verify that `MemoryLimitExceeded` is raised.
  - *Verification*: Run `python -m pytest code/tests/ -q` (exit 0, all tests passing).

- [ ] T012 [P] [US1] **Execute full pipeline end‑to‑end and produce a validation report**
  - Create `code/main.py` that:
    * Orchestrates the workflow by calling (in order):
      1. `data_gap_resolver.py` (Phase 0).
      2. `preprocess.py` (Phase 1).
      3. `embeddings.py` (Phase 1).
      4. `clustering.py` (Phase 1).
      5. `metrics.py` (Phase 2).
      6. `stats.py` (Phase 2).
      7. `sensitivity.py` (Phase 2).
      8. `aggregate.py` (Phase 2).
    * Catches exceptions and logs them; sets exit code appropriately.
    * Writes `results/validation_report.txt` with:
      - One line per success criterion (SC‑001 through SC‑005).
      - Format: `SC‑001: variance_ari={value}, variance_nmi={value}, stability_passed={pass/fail}`.
      - Format: `SC‑002: method_effect_p_value={value}, fdr_corrected={pass/fail}`.
      - Format: `SC‑003: peak_ram_bytes={value}, limit_7gb={pass/fail}`.
      - Format: `SC‑004: total_runtime_seconds={value}, limit_21600s={pass/fail}`.
      - Format: `SC‑005: max_vif={value}, collinearity_passed={pass/fail}`.
      - List any datasets marked `"Unavailable"` and their reasons.
      - State whether the analysis ran in mixed‑effects or descriptive ANOVA mode.
  - *Verification*: Run `python code/main.py --config code/config.py`. Exit code must be 0 when at least one dataset is available (or 1 only when no raw data were found). File `results/validation_report.txt` must exist, contain all five SC lines with statuses, and values must match those stored in `results/statistical_result.json` and `results/monitoring.csv`.

- [ ] T013 [P] [US1] **Write methods/results summary and reproducibility guide**
  - Create `paper/summary.md` with sections:
    * **Methods**: Describe data sources, preprocessing (log‑CPM, HVG selection, sampling strategy), embedding methods (PCA/t‑SNE/UMAP hyperparameters), clustering (Leiden with Silhouette optimization), fidelity metrics (ARI/NMI), and statistical model (Fixed‑Effects ANOVA or mixed‑effects).
    * **Results**: Insert all numeric results programmatically via Jinja2 template reading `data/results/combined_metrics.parquet`, `results/statistical_result.json`, `data/manifest.json`. Include: mean ARI/NMI per method, VIF values, model p‑values, FDR‑adjusted p‑values, sensitivity analysis variance, and stability verdict.
    * **Limitations**: Explicitly state how many of the three required GEO datasets were actually obtained, note that the statistical model is descriptive when fewer than two datasets are available, and acknowledge any datasets marked `"Unavailable"`.
  - Create `paper/REPRODUCIBILITY.md` with:
    * Random seed value (from `config.SEED`).
    * All source URLs from `data/manifest.json`.
    * Exact package versions from `code/requirements.txt`.
    * Step‑by‑step re‑run instructions: `python code/main.py --config code/config.py`.
    * RAM and runtime assertions (SC‑003/SC‑004 thresholds and actual values).
  - *Verification*: Render `paper/summary.md` to HTML via `pandoc paper/summary.md -o paper/summary.html` (exit 0). Grep for numeric literals in the rendered HTML that do **not** appear in `data/results/combined_metrics.parquet` or JSON files (should return no matches). Confirm `paper/REPRODUCIBILITY.md` contains the seed, at least one URL, and a valid `requirements.txt` block.

- [ ] T014 [P] [US1] **Mark project ready for paper‑stage handoff**
  - Create `paper/HANDOFF_READY.txt` containing:
    * SHA‑256 hash of `results/statistical_result.json` (computed via `hashlib.sha256(open(..., 'rb').read()).hexdigest()`).
    * ISO‑8601 timestamp of completion (generated by `code/main.py` after successful validation).
  - *Verification*: File exists. Run `sha256sum results/statistical_result.json` and confirm the output matches the hash in `HANDOFF_READY.txt`. Confirm the timestamp parses as valid ISO 8601 via `datetime.fromisoformat(...)`.

---

## Dependencies and requirement coverage

| Requirement | Satisfying Task(s) | Artifact(s) |
|-------------|-------------------|-------------|
| FR‑001 (download ≥1 dataset) | T003 | `data/manifest.json`, `results/data_gap_summary.txt` |
| FR‑002 (global linearity: Trustworthiness) | T004 | `data/processed/*_geometric.json` |
| FR‑003 (local continuity: LCA) | T004 | `data/processed/*_geometric.json` |
| FR‑004 (PCA/t‑SNE/UMAP) | T005 | `data/embeddings/*_PCA.csv`, `*_tSNE.csv`, `*_UMAP.csv` |
| FR‑005 (ARI/NMI) | T007 | `data/metrics/fidelity_results.csv` |
| FR‑006 (mixed‑effects or Fixed‑Effects ANOVA) | T008 | `results/statistical_result.json` |
| FR‑007 (Leiden‑resolution sensitivity sweep) | T009 | `results/sensitivity_analysis.json`, `figures/sensitivity_plot.png` |
| FR‑008 (Benjamini‑Hochberg correction) | T008 | `results/statistical_result.json` (p_value_fdr fields) |
| SC‑001 (variance < 0.05) | T009 | `results/sensitivity_analysis.json` |
| SC‑002 (FDR < 0.05 for method effect) | T008 | `results/statistical_result.json` |
| SC‑003 (peak RAM ≤ 7 GB) | T002, T012 | `results/monitoring.csv`, `results/validation_report.txt` |
| SC‑004 (runtime ≤ 21,600 s) | T002, T012 | `results/monitoring.csv`, `results/validation_report.txt` |
| SC‑005 (VIF < 5) | T008 | `results/statistical_result.json` |
| US‑1 (runnable end‑to‑end) | T001–T014 | `quickstart.md`, `code/main.py`, `results/validation_report.txt` |
| US‑2 (fidelity metrics) | T007 | `data/metrics/fidelity_results.csv` |
| US‑3 (statistical analysis & sensitivity) | T008, T009 | `results/statistical_result.json`, `results/sensitivity_analysis.json` |

**Execution order** (respecting data flow):  
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 ↔ T009 → T010 → T011 → T012 → T013 → T014.

All scientific requirements from the specification are covered. Each task produces a real, verifiable artifact with a deterministic verification step.
