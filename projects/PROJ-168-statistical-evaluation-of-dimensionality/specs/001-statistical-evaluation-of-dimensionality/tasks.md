# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and prior verification feedback.  
All tasks are presented as unchecked check‑boxes; each task lists the concrete artifact(s) it creates and a verification step that can be executed automatically. The ordering respects data flow – no task consumes an artifact before it is produced.

---

## Phase 1 – Project setup and data‑availability gate

- [ ] T001 [US1] **Create project directory layout, config, and quick‑start documentation**  
  *Artifacts*  
  - `code/config.py` – defines `SEED = 42`, `ACCESSIONS = ["GSE131907","GSE111322","GSE150728"]`, hyper‑parameters (`PCA_N_COMPONENTS = 30`, `TSNE_PERPLEXITY = 30`, `TSNE_N_ITER = 1000`, `UMAP_N_NEIGHBORS = 15`, `UMAP_MIN_DIST = 0.1`, `LEIDEN_RESOLUTIONS = [0.1,0.2,…,1.0]`, `SILHOUETTE_THRESHOLDS = [0.4,0.5,0.6]`, `K_NEIGHBORS_GEOMETRIC = 15`, `SAMPLE_CELLS_THRESHOLD = 10000`, `SAMPLE_SIZE = 5000`, `MEMORY_LIMIT_BYTES = 7_000_000_000`, `RUNTIME_LIMIT_SECONDS = 21600`).  
  - `quickstart.md` – documents the single runnable command: `python code/main.py --config code/config.py`.  
  - Directory tree created on‑demand via `llmxive_toolkit.paths`: `data/raw/`, `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `data/results/`, `figures/`, `paper/`, `results/`, `code/`, `code/tests/`.  
  *Verification* – `python -c "import pathlib, importlib.util, sys; cfg=importlib.util.module_from_spec(importlib.util.spec_from_file_location('cfg','code/config.py')); sys.modules['cfg']=cfg; exec(open('code/config.py').read(), cfg.__dict__); assert cfg.SEED==42"` succeeds and `cat quickstart.md` contains the command; `ls data/raw data/processed data/embeddings data/clustering data/metrics data/results figures paper results code` lists all directories.

- [ ] T002 [US1] **Implement resource‑monitoring utilities and generate `results/monitoring.csv`**  
  *Artifacts*  
  - `code/utils.py` – provides `get_logger(name)`, `ResourceMonitor` with method `run(step_name, fn, *args, **kwargs)` that (i) records wall‑clock time via `time.perf_counter()`, (ii) samples peak RSS with `psutil.Process().memory_info().rss` after the callable, (iii) appends a row `step,wall_time_s,peak_ram_bytes` to `results/monitoring.csv` (creates header on first use), (iv) raises `MemoryLimitExceeded` if `peak_ram_bytes > config.MEMORY_LIMIT_BYTES`.  
  - `results/monitoring.csv` – header `step,wall_time_s,peak_ram_bytes` plus at least one dummy row produced by a self‑test block inside `utils.py`.  
  *Verification* – `python -m pytest code/tests/test_utils.py -q` passes; the CSV exists, header is correct, and the dummy row contains two numeric columns.

- [ ] T003 [US1] **Resolve data‑availability (Phase 0) and download raw count matrices**  
  *Artifacts*  
  - `code/data_gap_resolver.py` – for each accession in `config.ACCESSIONS` attempts to locate a verified raw count matrix via `GEOparse.get_GEO(accession, destdir="data/raw/")` and, if that fails, falls back to a curated list of known supplementary URLs (hard‑coded, not guessed). On success records the URL, downloads the file to `data/raw/{accession}_raw.{ext}`, computes SHA‑256 checksum, and writes an entry to `data/manifest.json`.  
  - `data/manifest.json` – conforms to `specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml`; each entry includes `dataset_id`, `source_url`, `status` (`"Available"` or `"Unavailable"`), `error_message` (if any), `checksum`, `raw_file_path`, `processed_file_path` (null initially), and `generated_at`.  
  - If **no** accession resolves to a real raw count matrix, the script writes `results/data_gap_summary.txt` listing each attempted URL and the reason for failure, then exits with code 1 (the abort condition defined in the specification).  
  *Verification* – `python code/data_gap_resolver.py` exits 0 when at least one dataset is marked `"Available"` and `data/manifest.json` validates against the schema; when none are available the script creates `results/data_gap_summary.txt` and exits 1.

---

## Phase 2 – Pre‑processing, embeddings, clustering, and fidelity metrics

- [ ] T004 [US1] **Preprocess raw matrices, sample cells, and compute geometric diagnostics**  
  *Artifacts*  
  - `code/preprocess.py` – reads each `raw_file_path` from the manifest, validates integer‑non‑negative counts, applies log‑CPM (`log2((counts / row_sum) * 1e6 + 1)`), selects highly variable genes using Seurat‑style dispersion (elbow detection; fallback to top 2000), samples exactly `config.SAMPLE_SIZE` cells when `n_cells > config.SAMPLE_CELLS_THRESHOLD` (deterministic seed derived from `config.SEED` and `dataset_id`), otherwise uses all cells.  
  - Writes processed matrix to `data/processed/{dataset_id}_matrix.parquet`.  
  - Computes **global linearity** = `sklearn.manifold.trustworthiness(high_dim_sampled, pca30, n_neighbors=15)` and **local continuity** = `trustworthiness(pca30, high_dim_sampled, n_neighbors=15)`. If `n_cells < 500` logs a warning and writes `null` for both metrics.  
  - Stores diagnostics in `data/processed/{dataset_id}_geometric.json` (`trustworthiness`, `local_continuity`, `n_cells_sampled`, `n_genes_hvg`).  
  - All steps wrapped with `ResourceMonitor.run("preprocess_{dataset_id}", ...)`.  
  *Verification* – `pandas.read_parquet` on each matrix returns a non‑empty DataFrame with shape `(n_cells_sampled, n_genes_hvg)`; the JSON parses and contains numeric values in `[0,1]` (or `null`); `results/monitoring.csv` includes a row with step name `preprocess_{dataset_id}`.

- [ ] T005 [US1] **Generate PCA, t‑SNE, and UMAP embeddings**  
  *Artifacts*  
  - `code/embeddings.py` – loads the processed parquet, runs:  
    * PCA (`n_components=30`) → `data/embeddings/{dataset_id}_PCA.csv` (columns: `cell_id`, `PC1` … `PC30`).  
    * t‑SNE (`perplexity=30`, `n_iter=1000`, fixed `random_state=config.SEED`) → `data/embeddings/{dataset_id}_tSNE.csv` (columns: `cell_id`, `TSNE1`, `TSNE2`).  
    * UMAP (`n_neighbors=15`, `min_dist=0.1`, `random_state=config.SEED`) → `data/embeddings/{dataset_id}_UMAP.csv` (columns: `cell_id`, `UMAP1`, `UMAP2`).  
  - Each embedding step executed via `ResourceMonitor.run("embed_{method}_{dataset_id}", ...)` to record runtime and peak RAM.  
  *Verification* – each CSV has exactly `n_cells_sampled` rows, the correct number of numeric columns, no missing values; `results/monitoring.csv` contains rows `embed_PCA_{dataset_id}`, `embed_tSNE_{dataset_id}`, `embed_UMAP_{dataset_id}`.

- [ ] T006 [US1] **Leiden clustering with Silhouette‑optimal resolution**  
  *Artifacts*  
  - `code/clustering.py` – for each embedding CSV builds a k‑NN graph (`n_neighbors=15`) using `scanpy.pp.neighbors`, runs Leiden (`leidenalg`) for every resolution in `config.LEIDEN_RESOLUTIONS`. For each resolution computes the mean Silhouette Score (`sklearn.metrics.silhouette_score`). Selects the resolution with the highest Silhouette; on failure retries once with an alternate seed, otherwise writes `"Unavailable"` for that embedding.  
  - Writes `data/clustering/{dataset_id}_{method}_clusters.csv` containing `cell_id`, `cluster_label`, `silhouette_score`, `optimal_resolution`.  
  *Verification* – each clustering CSV contains `n_cells_sampled` rows, `cluster_label` is a non‑negative integer, `silhouette_score` ∈ `[-1,1]`, `optimal_resolution` matches one of the allowed values; a failed embedding results in a row where `cluster_label` = `"Unavailable"`.

- [ ] T007 [US2] **Compute fidelity metrics (ARI & NMI) against ground‑truth labels**  
  *Artifacts*  
  - `code/metrics.py` – extracts ground‑truth cell‑type labels from `data/processed/{dataset_id}_labels.csv` (produced during data‑gap resolution). Joins with clustering results, computes Adjusted Rand Index and Normalized Mutual Information (`sklearn.metrics.adjusted_rand_score`, `sklearn.metrics.normalized_mutual_info_score`). If labels are missing or clustering is `"Unavailable"` writes `"Unavailable"` for that row.  
  - Writes `data/metrics/fidelity_results.csv` with columns `embedding_id`, `method`, `dataset_id`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`, `runtime_seconds`, `peak_ram_gb`.  
  *Verification* – the CSV has one row per `(dataset_id, method)` where data are available; numeric fields are within `[0,1]` (or the literal `"Unavailable"`); the file validates against `specs/001-statistical-evaluation-of-dimensionality/contracts/fidelity_results.schema.yaml`.

---

## Phase 3 – Statistical modelling, sensitivity, aggregation, and validation

- [ ] T008 [US3] **Fit statistical model (mixed‑effects when ≥2 datasets, otherwise fixed‑effects ANOVA) and apply multiple‑testing correction**  
  *Artifacts*  
  - `code/stats.py` – merges `fidelity_results.csv` with geometric descriptors (`*_geometric.json`). Computes Variance Inflation Factor for predictor `method` (dummy‑coded); if any VIF ≥ 5 sets `collinearity_passed = false` and aborts modelling. Performs Shapiro‑Wilk normality test on residuals; if p < 0.05 falls back to Kruskal‑Wallis.  
  - If **≥2** datasets are `"Available"`: fits a mixed‑effects model `fidelity ~ method + (1|dataset)` using `statsmodels.MixedLM`. If **only 1** dataset: fits a fixed‑effects ANOVA `fidelity ~ method` via `statsmodels.formula.api.ols` + `anova_lm`.  
  - Extracts p‑values for the `method` fixed effect (or ANOVA F‑test), applies Benjamini‑Hochberg correction to all reported p‑values (α = 0.05).  
  - Writes `results/statistical_result.json` conforming to `specs/001-statistical-evaluation-of-dimensionality/contracts/statistical_result.schema.yaml` (includes `model_summary`, `sensitivity_analysis` placeholder, `execution_metadata`).  
  *Verification* – JSON validates against the schema; `model_summary.collinearity_passed` is a boolean, `fixed_effects` contain `term`, `estimate`, `std_error`, `p_value`, `p_value_fdr`; when descriptive mode is used `is_descriptive_mode` is true and coefficient fields are null.

- [ ] T009 [US3] **Run sensitivity analysis (Leiden‑resolution sweep & Silhouette‑threshold sweep) and produce plot**  
  *Artifacts*  
  - `code/sensitivity.py` – re‑computes ARI/NMI for every resolution in `config.LEIDEN_RESOLUTIONS` (re‑using clustering results when possible) and for each Silhouette threshold in `config.SILHOUETTE_THRESHOLDS` (filters clusters with silhouette ≥ threshold before metric computation). Calculates variance of ARI and variance of NMI across the three thresholds; sets `stability_passed = (variance_ari < 0.05) and (variance_nmi < 0.05)`.  
  - Writes `results/sensitivity_analysis.json` (fields: `thresholds`, `variance_ari`, `variance_nmi`, `stability_passed`).  
  - Writes long‑form table `figures/sensitivity_data.csv` (columns: `dataset_id`, `method`, `resolution`, `silhouette_threshold`, `ari`, `nmi`).  
  - Generates figure `figures/sensitivity_plot.png` – line plots of ARI and NMI versus Leiden resolution for each method, separate panels per dataset, with a legend.  
  *Verification* – JSON parses, variances are numeric, `stability_passed` is boolean; the CSV contains rows for every combination; the PNG opens without error (e.g., `file fig.png` returns a valid image header).

- [ ] T010 [US1] **Aggregate all metrics into a unified Parquet file and enrich statistical result with execution metadata**  
  *Artifacts*  
  - `code/aggregate.py` – reads `data/metrics/fidelity_results.csv`, geometric JSONs, `results/statistical_result.json`, `results/sensitivity_analysis.json`, and `results/monitoring.csv`. Computes:  
    * `peak_memory_bytes` = max(`peak_ram_bytes` across all rows).  
    * `total_runtime_seconds` = sum(`wall_time_s`).  
    * `datasets_processed` = count of manifest entries with status `"Available"`.  
    * `datasets_skipped` = count with status `"Unavailable"` or `"Error"`.  
    * `exit_code` = 0 if no abort condition, else 1.  
  - Updates `execution_metadata` section of `results/statistical_result.json` with the values above.  
  - Writes `data/results/combined_metrics.parquet` containing columns: `dataset_id`, `method`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`, `trustworthiness`, `local_continuity`, `runtime_seconds`, `peak_ram_gb`.  
  *Verification* – the Parquet file can be read (`pandas.read_parquet`) and contains the expected columns; the JSON now includes a complete `execution_metadata` object matching the schema.

- [ ] T011 [US1] **Add focused unit‑tests for preprocessing, clustering, and utilities**  
  *Artifacts*  
  - `code/tests/test_preprocessing.py` – loads a small real fixture matrix (e.g., first 200 rows of a downloaded dataset saved under `data/fixtures/fixture.parquet`), checks that log‑CPM values are non‑negative, that HVG selection returns `n_genes_hvg > 0`, and that sampling yields exactly `config.SAMPLE_SIZE` rows when applicable.  
  - `code/tests/test_clustering.py` – runs `clustering.py` on a tiny real embedding (2 D coordinates for 30 cells) and asserts that ARI between identical label vectors equals 1.0 and that Silhouette scores lie in `[-1,1]`.  
  - `code/tests/test_utils.py` – verifies `ResourceMonitor.run` creates a monitoring row, `parse_time_output` correctly extracts wall‑time and max‑RSS from a sample `/usr/bin/time -v` string, and `assert_budgets` raises when artificially low limits are supplied.  
  *Verification* – `python -m pytest code/tests/ -q` exits with all tests passing.

- [ ] T012 [US1] **Execute full pipeline end‑to‑end and produce a validation report**  
  *Artifacts*  
  - Run `python code/main.py --config code/config.py`.  
  - Generate `results/validation_report.txt` – for each success criterion SC‑001 … SC‑005 writes “PASS” or “FAIL” together with the observed numeric value (e.g., `SC‑003 peak RAM = 5.8 GB → PASS`). Also lists any datasets that were unavailable and notes whether the analysis ran in mixed‑effects or descriptive mode.  
  *Verification* – the script exits with code 0 (or 1 only when no raw data were found). The report file exists, contains the five SC lines, and each line’s status matches the values stored in `results/statistical_result.json` and `results/monitoring.csv`.

- [ ] T013 [US1] **Write methods/results summary, reproducibility guide, and update the implementation plan**  
  *Artifacts*  
  - `paper/summary.md` – sections **Methods**, **Results**, **Limitations**. All numbers (mean ARI/NMI per method, VIF values, model p‑values, stability verdict) are programmatically inserted via a small Jinja2 template that reads the Parquet, JSON, and manifest files; no hand‑typed numbers. The limitations paragraph explicitly states how many of the three required GEO datasets were actually obtained and that the statistical model is descriptive when fewer than two datasets are available.  
  - `paper/REPRODUCIBILITY.md` – lists seed, all URLs from `data/manifest.json`, exact package versions from `code/requirements.txt`, step‑by‑step re‑run instructions (`python code/main.py --config code/config.py`), and the runtime/memory assertions (SC‑003/SC‑004).  
  - Updated `plan.md` – adds a “Data‑gap resolution outcome” paragraph reflecting the actual number of available datasets and notes that the downstream analysis will run in **descriptive ANOVA mode** if only one dataset is present, satisfying the Constitution check.  
  *Verification* – `pandoc paper/summary.md -o paper/summary.html` succeeds; a grep for any numeric literal not present in the source artifacts returns no matches; `git diff plan.md` shows the new paragraph; both markdown files exist and are non‑empty.

---

## Phase 4 – Final hand‑off (no code execution required)

- [ ] T014 [US1] **Mark project ready for paper‑stage handoff**  
  *Artifacts* – create a marker file `paper/HANDOFF_READY.txt` containing the SHA‑256 hash of `results/statistical_result.json` and the timestamp of completion.  
  *Verification* – the file exists, its contents match `sha256sum results/statistical_result.json` and a valid ISO‑8601 datetime.

---

## Dependencies and requirement coverage

| Requirement | Satisfying Task(s) | Artifact(s) |
|-------------|-------------------|-------------|
| FR‑001 (download ≥1 dataset) | T003 | `data/manifest.json`, `results/data_gap_summary.txt` |
| FR‑002 (global linearity) | T004 | `data/processed/*_geometric.json` |
| FR‑003 (local continuity) | T004 | `data/processed/*_geometric.json` |
| FR‑004 (PCA/t‑SNE/UMAP) | T005 | `data/embeddings/*` |
| FR‑05 (ARI/NMI) | T007 | `data/metrics/fidelity_results.csv` |
| FR‑06 (mixed‑effects / ANOVA) | T008 | `results/statistical_result.json` |
| FR‑07 (Silhouette‑threshold sweep) | T009 | `results/sensitivity_analysis.json` |
| FR‑08 (Benjamini‑Hochberg) | T008 | `results/statistical_result.json` |
| SC‑001 (variance < 0.05) | T009 | `results/sensitivity_analysis.json` |
| SC‑002 (FDR < 0.05) | T008 | `results/statistical_result.json` |
| SC‑003 (peak RAM ≤ 7 GB) | T002, T011, T012 | `results/monitoring.csv`, `results/validation_report.txt` |
| SC‑004 (runtime ≤ 21 600 s) | T002, T011, T012 | `results/monitoring.csv`, `results/validation_report.txt` |
| SC‑005 (VIF < 5) | T008 | `results/statistical_result.json` |
| US‑1 (end‑to‑end runnable) | T001, T003‑T012 | `quickstart.md`, `code/main.py` |
| US‑2 (fidelity metrics) | T007 | `data/metrics/fidelity_results.csv` |
| US‑3 (statistical analysis & sensitivity) | T008, T009 | `results/statistical_result.json`, `results/sensitivity_analysis.json` |

**Execution order**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 ↔ T009 → T010 → T011 → T012 → T013 → T014. All data‑flow dependencies are respected; no task consumes an artifact before it is generated.
