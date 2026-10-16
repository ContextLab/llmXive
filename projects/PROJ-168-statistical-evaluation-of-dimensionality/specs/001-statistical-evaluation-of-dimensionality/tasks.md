# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and prior verification feedback.  
All tasks are presented as unchecked check‑boxes; each task lists the concrete artifact(s) it creates and a verification step that can be executed automatically. The ordering respects data flow – no task consumes an artifact before it is produced.

---

## Phase 0 – Project scaffolding & data‑availability gate  

- [ ] T001 [P] [US1] **Create project directory layout, configuration file, and quick‑start documentation**  
  *Artifacts*  
  - `code/config.py` – defines global constants (seed, GEO accessions, hyper‑parameters, resource limits).  
  - `quickstart.md` – describes the single runnable command: `python code/main.py --config code/config.py`.  
  - Directory tree (created on‑demand by `llmxive_toolkit.paths`): `data/raw/`, `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `data/results/`, `figures/`, `paper/`, `results/`, `code/`, `code/tests/`.  
  - `results/dir_listing.txt` – output of `find . -type d` captured after directories are created.  
  *Verification* – Run `python -c "import importlib.util, sys; spec=importlib.util.spec_from_file_location('cfg','code/config.py'); cfg=importlib.util.module_from_spec(spec); spec.loader.exec_module(cfg); assert cfg.SEED==42"` and check that `results/dir_listing.txt` contains each of the listed directories.

- [ ] T002 [P] [US1] **Implement robust resource‑monitoring utilities and generate an initial monitoring CSV**  
  *Artifacts*  
  - `code/utils.py` – provides `get_logger(name)`, `MemoryLimitExceeded` exception, and a fully‑implemented `ResourceMonitor` class with method `run(step_name, fn, *args, **kwargs)`. The method records wall‑clock time (`time.perf_counter()`), samples peak RSS via `psutil.Process().memory_info().rss`, writes a row `step,wall_time_s,peak_ram_bytes` to `results/monitoring.csv`, and raises `MemoryLimitExceeded` if the peak exceeds `config.MEMORY_LIMIT_BYTES`.  
  - `results/monitoring.csv` – header `step,wall_time_s,peak_ram_bytes` plus a dummy row produced by a self‑test call inside `utils.py` (e.g., `ResourceMonitor().run("dummy", lambda: None)`).  
  *Verification* – Execute `python -m pytest code/tests/test_utils.py -q` (tests are added in T011) and confirm that `results/monitoring.csv` exists, has the correct header, and contains at least the dummy row.

- [ ] T003 [P] [US1] **Resolve data‑availability (Phase 0) and download raw count matrices**  
  *Artifacts*  
  - `code/data_gap_resolver.py` – iterates over `config.ACCESSIONS`, attempts to download a verified raw count matrix via `GEOparse.get_GEO(accession, destdir="data/raw/")`. If that fails, it tries a curated list of known supplementary URLs (hard‑coded, no guessing). On success it records the URL, writes the file to `data/raw/{accession}_raw.{ext}`, computes a SHA‑256 checksum, and appends an entry to `data/manifest.json`.  
  - `data/manifest.json` – conforms to `specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml`. Each entry includes `dataset_id`, `source_url`, `status` (`"Available"` or `"Unavailable"`), `error_message` (if any), `checksum`, `raw_file_path`, `processed_file_path` (null initially), and `generated_at`.  
  - If **no** accession resolves, the script writes `results/data_gap_summary.txt` listing attempted URLs and reasons for failure, then exits with code 1.  
  *Verification* – Run `python code/data_gap_resolver.py`. The script must exit 0 when at least one entry in `data/manifest.json` has `"status": "Available"` and the JSON validates against the schema; otherwise it must produce `results/data_gap_summary.txt` and exit 1. Validation can be checked with `python -m jsonschema -i data/manifest.json specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml`.

---

## Phase 1 – Pre‑processing, geometric diagnostics, and embeddings  

- [ ] T004 [P] [US1] **Preprocess raw matrices, sample cells, and compute geometric diagnostics**  
  *Artifacts*  
  - `code/preprocess.py` – reads each `raw_file_path` from the manifest, validates that counts are non‑negative integers, applies log‑CPM (`log2((counts / row_sum) * 1e6 + 1)`), selects highly variable genes using a Seurat‑style dispersion‑elbow method (fallback to top 2000 HVGs), and samples exactly `config.SAMPLE_SIZE` cells when `n_cells > config.SAMPLE_CELLS_THRESHOLD` (deterministic seed derived from `config.SEED` and `dataset_id`).  
  - Writes processed matrix to `data/processed/{dataset_id}_matrix.parquet`.  
  - Computes **global linearity** = `sklearn.manifold.trustworthiness(high_dim_sampled, pca30, n_neighbors=15)` and **local continuity** = `trustworthiness(pca30, high_dim_sampled, n_neighbors=15)`. If `n_cells < 500` logs a warning and stores `null` for both metrics.  
  - Stores diagnostics in `data/processed/{dataset_id}_geometric.json` (keys: `trustworthiness`, `local_continuity`, `n_cells_sampled`, `n_genes_hvg`).  
  - Each step wrapped with `ResourceMonitor.run("preprocess_{dataset_id}", ...)`.  
  *Verification* – For every `"Available"` dataset, `pandas.read_parquet` on the matrix returns a non‑empty DataFrame with shape `(n_cells_sampled, n_genes_hvg)`. The JSON parses and contains numeric values in `[0,1]` (or `null`). `results/monitoring.csv` must contain a row named `preprocess_{dataset_id}`.

- [ ] T005 [P] [US1] **Generate PCA, t‑SNE, and UMAP embeddings from the sampled matrix**  
  *Artifacts*  
  - `code/embeddings.py` – loads the processed parquet, runs:  
    * **PCA** (`n_components=30`) → `data/embeddings/{dataset_id}_PCA.csv` (columns: `cell_id`, `PC1` … `PC30`).  
    * **t‑SNE** (`perplexity=30`, `n_iter=1000`, `random_state=config.SEED`) → `data/embeddings/{dataset_id}_tSNE.csv` (`cell_id`, `TSNE1`, `TSNE2`).  
    * **UMAP** (`n_neighbors=15`, `min_dist=0.1`, `random_state=config.SEED`) → `data/embeddings/{dataset_id}_UMAP.csv` (`cell_id`, `UMAP1`, `UMAP2`).  
  - Each embedding step executed via `ResourceMonitor.run("embed_{method}_{dataset_id}", ...)`.  
  *Verification* – Each CSV must contain exactly `n_cells_sampled` rows, the correct number of numeric columns, and no missing values. Corresponding rows must appear in `results/monitoring.csv` (`embed_PCA_…`, `embed_tSNE_…`, `embed_UMAP_…`).

- [ ] T006 [P] [US2] **Leiden clustering with resolution optimized by Silhouette Score**  
  *Artifacts*  
  - `code/clustering.py` – for each embedding CSV builds a k‑NN graph (`n_neighbors=15`) using `scanpy.pp.neighbors`, runs Leiden clustering (`leidenalg`) for every resolution in `config.LEIDEN_RESOLUTIONS` (0.1 → 1.0 step 0.1). For each resolution computes mean Silhouette Score (`sklearn.metrics.silhouette_score`). Selects the resolution with the highest Silhouette; on failure retries once with a different seed, otherwise writes `"Unavailable"` for that embedding.  
  - Writes `data/clustering/{dataset_id}_{method}_clusters.csv` containing `cell_id`, `cluster_label`, `silhouette_score`, `optimal_resolution`.  
  *Verification* – Each clustering CSV must have `n_cells_sampled` rows, `cluster_label` as a non‑negative integer (or the literal `"Unavailable"`), `silhouette_score` within `[-1,1]`, and `optimal_resolution` matching one of the allowed values. A failed embedding must contain `"Unavailable"` in the `cluster_label` column.

- [ ] T007 [P] [US2] **Compute fidelity metrics (ARI & NMI) against ground‑truth labels**  
  *Artifacts*  
  - `code/metrics.py` – extracts ground‑truth cell‑type labels from `data/raw/{dataset_id}_metadata.tsv` (produced during data‑gap resolution) or from a separate `data/processed/{dataset_id}_labels.csv` if the metadata file contains a `cell_type` column. Joins labels with clustering results, computes Adjusted Rand Index and Normalized Mutual Information (`sklearn.metrics.adjusted_rand_score`, `sklearn.metrics.normalized_mutual_info_score`). If labels are missing or clustering is `"Unavailable"` writes `"Unavailable"` for that row.  
  - Writes `data/metrics/fidelity_results.csv` with columns `embedding_id`, `method`, `dataset_id`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`, `runtime_seconds`, `peak_ram_gb`.  
  *Verification* – The CSV must have one row per `(dataset_id, method)` where data are available, numeric fields within `[0,1]` (or the literal `"Unavailable"`), and must validate against `specs/001-statistical-evaluation-of-dimensionality/contracts/fidelity_results.schema.yaml`.

---

## Phase 2 – Statistical modelling, sensitivity analysis, and aggregation  

- [ ] T008 [P] [US3] **Fit statistical model (mixed‑effects when ≥2 datasets, otherwise fixed‑effects ANOVA) and apply Benjamini‑Hochberg correction**  
  *Artifacts*  
  - `code/stats.py` – merges `fidelity_results.csv` with geometric descriptors (`*_geometric.json`). Computes Variance Inflation Factor for the dummy‑coded `method` predictor; if any VIF ≥ 5 sets `collinearity_passed = false` and aborts modelling (writes a warning). Performs Shapiro‑Wilk test on residuals; if p < 0.05 falls back to Kruskal‑Wallis.  
  - If **≥2** datasets are `"Available"`: fits a mixed‑effects model `fidelity ~ method + (1|dataset)` using `statsmodels.MixedLM`. If **only 1** dataset: fits a fixed‑effects ANOVA `fidelity ~ method` via `statsmodels.formula.api.ols` + `anova_lm`.  
  - Applies Benjamini‑Hochberg correction to all reported p‑values (α = 0.05).  
  - Writes `results/statistical_result.json` conforming to `specs/001-statistical-evaluation-of-dimensionality/contracts/statistical_result.schema.yaml` (includes `model_summary`, placeholder `sensitivity_analysis`, and empty `execution_metadata` for now).  
  *Verification* – JSON must validate against the schema; `model_summary.collinearity_passed` is a boolean; `fixed_effects` (or `mixed_effects` terms) contain required fields; when descriptive mode is used `is_descriptive_mode` is true and coefficient fields are null.

- [ ] T009 [P] [US3] **Run sensitivity analysis (Leiden‑resolution sweep & Silhouette‑threshold sweep) and produce summary plot**  
  *Artifacts*  
  - `code/sensitivity.py` – re‑computes ARI/NMI for every resolution in `config.LEIDEN_RESOLUTIONS` (re‑using existing clustering results when possible) and for each Silhouette threshold in `config.SILHOUETTE_THRESHOLDS` (`0.4, 0.5, 0.6`). Calculates variance of ARI and variance of NMI across the three thresholds; sets `stability_passed = (variance_ari < 0.05) and (variance_nmi < 0.05)`.  
  - Writes `results/sensitivity_analysis.json` (`thresholds`, `variance_ari`, `variance_nmi`, `stability_passed`).  
  - Writes `figures/sensitivity_data.csv` (columns: `dataset_id`, `method`, `resolution`, `silhouette_threshold`, `ari`, `nmi`).  
  - Generates `figures/sensitivity_plot.png` – line plots of ARI and NMI versus Leiden resolution for each method, faceted by dataset.  
  *Verification* – JSON parses, variances are numeric, `stability_passed` is boolean. The CSV contains a row for every combination of dataset, method, resolution, and silhouette threshold. The PNG file opens without error (e.g., `file figures/sensitivity_plot.png` reports an image header).

- [ ] T010 [P] [US1] **Aggregate all metrics into a unified Parquet file and enrich statistical result with execution metadata**  
  *Artifacts*  
  - `code/aggregate.py` – reads `data/metrics/fidelity_results.csv`, all geometric JSON files, `results/statistical_result.json`, `results/sensitivity_analysis.json`, and `results/monitoring.csv`. Computes:  
    * `peak_memory_bytes` = max(`peak_ram_bytes` across all monitoring rows).  
    * `total_runtime_seconds` = sum(`wall_time_s`).  
    * `datasets_processed` = count of manifest entries with `"status": "Available"`.  
    * `datasets_skipped` = count with `"status"` not `"Available"`.  
    * `exit_code` = 0 if no abort condition, else 1.  
  - Updates the `execution_metadata` section of `results/statistical_result.json` with these values.  
  - Writes `data/results/combined_metrics.parquet` containing columns: `dataset_id`, `method`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`, `trustworthiness`, `local_continuity`, `runtime_seconds`, `peak_ram_gb`.  
  *Verification* – `pandas.read_parquet data/results/combined_metrics.parquet` succeeds and the DataFrame contains all listed columns. The JSON now includes a complete `execution_metadata` object that validates against its schema.

---

## Phase 3 – Testing, end‑to‑end execution, and documentation  

- [ ] T011 [P] [US1] **Add focused unit‑tests for preprocessing, clustering, metrics, and utilities**  
  *Artifacts*  
  - `code/tests/test_preprocess.py` – loads a small real fixture matrix (`data/fixtures/fixture.parquet`), checks that log‑CPM values are non‑negative, that HVG selection returns `n_genes_hvg > 0`, and that sampling yields exactly `config.SAMPLE_SIZE` rows when applicable.  
  - `code/tests/test_clustering.py` – runs `clustering.py` on a tiny synthetic embedding (30 cells, 2 D) and asserts that ARI between identical label vectors equals 1.0 and that silhouette scores lie in `[-1,1]`.  
  - `code/tests/test_metrics.py` – verifies that `metrics.py` returns ARI/NMI within `[0,1]` for a known small case.  
  - `code/tests/test_utils.py` – confirms that `ResourceMonitor.run` creates a monitoring row, that the RAM‑limit check raises `MemoryLimitExceeded` when a mock function reports an inflated RSS, and that the CSV header is correct.  
  *Verification* – Running `python -m pytest code/tests/ -q` must exit with all tests passing (return code 0).  

- [ ] T012 [P] [US1] **Execute full pipeline end‑to‑end and produce a validation report**  
  *Artifacts*  
  - `code/main.py` – orchestrates the workflow: calls `data_gap_resolver.py`, `preprocess.py`, `embeddings.py`, `clustering.py`, `metrics.py`, `stats.py`, `sensitivity.py`, `aggregate.py`, and finally writes a human‑readable report.  
  - `results/validation_report.txt` – for each success criterion SC‑001 … SC‑005 writes “PASS” or “FAIL” together with the observed numeric value (e.g., `SC‑003 peak RAM = 5.8 GB → PASS`). Also lists any datasets marked `"Unavailable"` and states whether the analysis ran in mixed‑effects or descriptive ANOVA mode.  
  *Verification* – `python code/main.py --config code/config.py` must exit with code 0 when at least one dataset is available (or with code 1 only when no raw data were found). The file `results/validation_report.txt` must exist and contain the five SC lines with statuses that match the values stored in `results/statistical_result.json` and `results/monitoring.csv`.

- [ ] T013 [P] [US1] **Write methods/results summary, reproducibility guide, and update the implementation plan**  
  *Artifacts*  
  - `paper/summary.md` – sections **Methods**, **Results**, **Limitations**. All numbers (mean ARI/NMI per method, VIF values, model p‑values, sensitivity verdict) are inserted programmatically via a small Jinja2 template that reads `data/results/combined_metrics.parquet`, `results/statistical_result.json`, and `data/manifest.json`. No hand‑typed literals appear. The limitations paragraph explicitly states how many of the three GEO datasets were actually obtained and that the statistical model is descriptive when fewer than two datasets are available.  
  - `paper/REPRODUCIBILITY.md` – lists the random seed, all URLs from `data/manifest.json`, exact package versions from `code/requirements.txt`, step‑by‑step re‑run instructions (`python code/main.py --config code/config.py`), and the RAM/runtime assertions (SC‑003/SC‑004).  
  - Updated `plan.md` – adds a “Data‑gap resolution outcome” paragraph reflecting the actual number of available datasets and notes that downstream analysis will run in **descriptive ANOVA mode** if only one dataset is present, satisfying the constitutional check.  
  *Verification* – Rendering `paper/summary.md` to HTML (`pandoc paper/summary.md -o paper/summary.html`) succeeds, and a grep for any numeric literal that does **not** appear in the JSON/Parquet files returns no matches. `paper/REPRODUCIBILITY.md` contains the seed, at least one URL, and a valid requirements block. `git diff plan.md` shows the added paragraph.

- [ ] T014 [P] [US1] **Mark project ready for paper‑stage handoff**  
  *Artifacts*  
  - `paper/HANDOFF_READY.txt` – contains the SHA‑256 hash of `results/statistical_result.json` and the ISO‑8601 timestamp of completion (generated by `code/main.py` after successful validation).  
  *Verification* – The file exists, `sha256sum results/statistical_result.json` matches the hash recorded in `HANDOFF_READY.txt`, and the timestamp parses as a valid datetime.

---

## Dependencies and requirement coverage

| Requirement | Satisfying Task(s) | Artifact(s) |
|-------------|-------------------|-------------|
| FR‑001 (download ≥1 dataset) | T003 | `data/manifest.json`, `results/data_gap_summary.txt` |
| FR‑002 (global linearity) | T004 | `data/processed/*_geometric.json` |
| FR‑003 (local continuity) | T004 | `data/processed/*_geometric.json` |
| FR‑004 (PCA/t‑SNE/UMAP) | T005 | `data/embeddings/*` |
| FR‑005 (ARI/NMI) | T007 | `data/metrics/fidelity_results.csv` |
| FR‑006 (mixed‑effects / ANOVA) | T008 | `results/statistical_result.json` |
| FR‑007 (silhouette‑threshold sweep) | T009 | `results/sensitivity_analysis.json` |
| FR‑008 (Benjamini‑Hochberg) | T008 | `results/statistical_result.json` |
| SC‑001 (variance < 0.05) | T009 | `results/sensitivity_analysis.json` |
| SC‑002 (FDR < 0.05) | T008 | `results/statistical_result.json` |
| SC‑003 (peak RAM ≤ 7 GB) | T002, T011, T012 | `results/monitoring.csv`, `results/validation_report.txt` |
| SC‑004 (runtime ≤ 21 600 s) | T002, T011, T012 | `results/monitoring.csv`, `results/validation_report.txt` |
| SC‑005 (VIF < 5) | T008 | `results/statistical_result.json` |
| US‑1 (runnable end‑to‑end) | T001, T003‑T012 | `quickstart.md`, `code/main.py` |
| US‑2 (fidelity metrics) | T007 | `data/metrics/fidelity_results.csv` |
| US‑3 (statistical analysis & sensitivity) | T008, T009 | `results/statistical_result.json`, `results/sensitivity_analysis.json` |

**Execution order** (respecting data flow):  
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 ↔ T009 → T010 → T011 → T012 → T013 → T014.  

All scientific requirements from the specification are covered, and each task produces a real, verifiable artifact.
