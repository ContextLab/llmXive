# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and prior reviewer feedback.  
All tasks are expressed as plain‑text checklist items; each unchecked box (`- [ ]`) represents work that must produce a real, verifiable artifact under a project‑owned path.

---

## Phase 0 – Specification & Planning Adjustments

- [ ] T001 [P] [US1] **Update `plan.md` to reflect the mixed‑effects fallback and Silhouette‑threshold sweep**  
  - Edit `plan.md` so that FR‑006 is described as “fit a mixed‑effects model when ≥ 2 datasets are available; otherwise fit a fixed‑effects ANOVA (descriptive mode)”.  
  - Add a paragraph describing the sensitivity sweep over the Silhouette thresholds `{0.4, 0.5, 0.6}` (FR‑007).  
  - **Verification**: `git diff plan.md` shows the added sections; running `python -c "import pathlib, re; assert re.search(r'mixed‑effects', pathlib.Path('plan.md').read_text())"` exits 0.

---

## Phase 1 – Project Layout & Quick‑Start Command

- [ ] T002 [P] [US1] **Create project directory skeleton, configuration, and quick‑start documentation**  
  - Create `code/config.py` with constants (seed, GEO accessions, sampling sizes, resolution lists, RAM/CPU limits, `K_GEOMETRY=15`).  
  - Create `quickstart.md` that states the single runnable command: `python code/main.py`.  
  - Create empty directories `data/raw/`, `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `data/results/`, `figures/`, `paper/`, `code/tests/`.  
  - Generate a directory listing file `results/dir_listing.txt` by executing `find data code results figures paper -type d > results/dir_listing.txt`.  
  - **Verification**: `cat results/dir_listing.txt` contains all listed directories; a Python assertion `assert pathlib.Path('results/dir_listing.txt').exists()` exits 0.

---

## Phase 2 – Resource Monitoring Utility

- [ ] T003 [P] [US1] **Implement full `code/utils.py` with `ResourceMonitor` and produce `results/monitoring.csv`**  
  - `code/utils.py` must define:  
    * `get_logger(name)` – configured `logging.Logger`.  
    * `MemoryLimitExceeded` exception.  
    * `ResourceMonitor` class with method `run(step_name, fn, *args, **kwargs)` that records wall‑clock time, samples RSS every 0.5 s via `psutil`, aborts with `MemoryLimitExceeded` if peak > `config.MEMORY_LIMIT_BYTES`, and appends a row `step_name,wall_time_s,peak_ram_bytes` to `results/monitoring.csv` (creating the header on first write).  
    * A `__main__` self‑test that runs a modest computation and prints “OK”.  
  - Execute `python code/utils.py` to generate `results/monitoring.csv`.  
  - **Verification**: `head -n 2 results/monitoring.csv` shows header `step,wall_time_s,peak_ram_bytes` and a row beginning with `selftest`; `python -c "import pandas as pd; df=pd.read_csv('results/monitoring.csv'); assert not df.empty"` exits 0.

---

## Phase 3 – Data‑Gap Resolution (Phase 0 blocker)

- [ ] T004 [P] [US1] **Download raw count matrices, verify availability, and write a schema‑valid manifest**  
  - Implement `code/data_gap_resolver.py` that iterates `config.GEO_ACCESSIONS`, uses `GEOparse.get_GEO` to fetch each record, locates supplementary count‑matrix files, and downloads them into `data/raw/<accession>/`.  
  - For each accession, compute SHA‑256 checksum of the downloaded file.  
  - Assemble `data/manifest.json` conforming to `specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/dataset.schema.yaml`.  
  - If no accession is marked `"Available"`, write `results/data_gap_summary.txt` with failure reasons and exit 1 (abort condition).  
  - **Verification**: `python -m jsonschema -i data/manifest.json specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/dataset.schema.yaml` exits 0; `cat results/data_gap_summary.txt` exists only when exit 1.

---

## Phase 4 – Ingestion & Pre‑processing (FR‑001, FR‑002, FR‑003)

- [ ] T005 [P] [US1] **Load each available dataset, apply log‑CPM, select highly variable genes, sample cells, and compute geometric diagnostics**  
  - For every entry in `data/manifest.json` with `"status":"Available"`:  
    * Load the raw count matrix with `scanpy.read_10x_mtx` or appropriate reader.  
    * Extract ground‑truth cell‑type labels from GEO metadata and write `data/processed/<dataset_id>_labels.csv`.  
    * Perform log‑CPM transformation: `log2((counts / counts.sum(axis=1)[:, None]) * 1e6 + 1)`.  
    * Run `sc.pp.highly_variable_genes(..., flavor="seurat")` and retain the top‑N HVGs (elbow‑determined, recorded in the output).  
    * If `n_cells > config.SAMPLE_CELLS_THRESHOLD`, deterministically sample exactly `config.SAMPLE_SIZE` cells using `np.random.default_rng(seed).choice`.  
    * Compute **global linearity** as Trustworthiness (`sklearn.manifold.trustworthiness`) with `n_neighbors=config.K_GEOMETRY` comparing the high‑dim sampled matrix to its PCA‑30 projection.  
    * Compute **local continuity** as the reverse Trustworthiness (embedding → high‑dim).  
    * Write the processed matrix to `data/processed/<dataset_id>_matrix.parquet` and the diagnostics to `data/processed/<dataset_id>_geometric.json`.  
    * Wrap the whole per‑dataset routine in `ResourceMonitor.run(f"preprocess_{dataset_id}", ...)`.  
  - **Verification**: Each parquet file loads with shape `(≤config.SAMPLE_SIZE, ≤2000)`; the JSON contains keys `trustworthiness` and `local_continuity` with values in `[0,1]` (or `null` for < 500 cells); `results/monitoring.csv` contains a row `preprocess_<dataset_id>`.

---

## Phase 5 – Embedding Generation (FR‑004)

- [ ] T006 [P] [US1] **Produce PCA, t‑SNE, and UMAP embeddings for every processed dataset**  
  - Load `data/processed/<dataset_id>_matrix.parquet`.  
  - **PCA**: `sklearn.decomposition.PCA(n_components=30, random_state=config.SEED)` → write CSV `data/embeddings/<dataset_id>_PCA.csv` (`cell_id,PC1,…,PC30`).  
  - **t‑SNE**: `sklearn.manifold.TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=config.SEED)` → write `data/embeddings/<dataset_id>_tSNE.csv`.  
  - **UMAP**: `umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=config.SEED)` → write `data/embeddings/<dataset_id>_UMAP.csv`.  
  - Each embedding step is wrapped with `ResourceMonitor.run(f"embed_{method}_{dataset_id}", ...)`.  
  - **Verification**: Each CSV loads with exactly the sampled number of rows and the correct column count (32 for PCA, 3 for t‑SNE/UMAP); no `NaN` values; `results/monitoring.csv` contains rows `embed_PCA_<dataset_id>`, `embed_tSNE_<dataset_id>`, `embed_UMAP_<dataset_id>`.

---

## Phase 6 – Clustering & Fidelity Metrics (FR‑005)

- [ ] T007 [P] [US2] **Run Leiden clustering with Silhouette‑optimised resolution and compute ARI / NMI**  
  - For each embedding CSV:  
    * Build a k‑NN graph (`n_neighbors=15`).  
    * Iterate over `config.LEIDEN_RESOLUTIONS`; for each resolution run `leidenalg.find_partition` and compute `sklearn.metrics.silhouette_score`.  
    * Select the resolution with maximal silhouette score; record the score and resolution.  
    * On failure, retry once with a different fixed seed; if still failing, write `"Unavailable"` for that embedding.  
    * Write `data/clustering/<dataset_id>_<method>_clusters.csv` (`cell_id,cluster_label,silhouette_score,optimal_resolution`).  
  - Join clustering labels with ground‑truth labels from `data/processed/<dataset_id>_labels.csv` and compute `adjusted_rand_score` and `normalized_mutual_info_score`.  
  - Write `data/metrics/fidelity_results.csv` with columns `embedding_id,method,dataset_id,ari,nmi,silhouette_score,optimal_resolution` (the `silhouette_score` column stores the optimal silhouette, the `silhouette_threshold` field required by the schema is populated with the primary threshold `0.5`).  
  - **Verification**: `pandas.read_csv('data/metrics/fidelity_results.csv')` yields one row per (dataset, method) with `ari` and `nmi` in `[0,1]` or the literal `"Unavailable"`; schema validation via `python -m jsonschema -i data/metrics/fidelity_results.csv specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/fidelity_results.schema.yaml` passes.

---

## Phase 7 – Statistical Modeling & Multiple‑Testing Correction (FR‑006, FR‑008, SC‑002, SC‑005)

- [ ] T008 [P] [US3] **Fit mixed‑effects model (or fixed‑effects ANOVA when only one dataset) and apply Benjamini‑Hochberg correction**  
  - Load `data/metrics/fidelity_results.csv` (filter out `"Unavailable"` rows) and merge with `data/processed/*_geometric.json` on `dataset_id`.  
  - If ≥ 2 datasets have valid rows, fit a linear mixed‑effects model `fidelity ~ method + (1|dataset)` using `statsmodels.MixedLM`.  
  - If only one dataset, fit a fixed‑effects ANOVA `fidelity ~ method` via `statsmodels.formula.api.ols` and set `"is_descriptive_mode": true`.  
  - Compute VIF for the method dummy variables; abort (`collinearity_passed = false`) if any VIF ≥ 5.  
  - Perform Shapiro‑Wilk test on residuals; log warnings if normality fails.  
  - Apply Benjamini‑Hochberg (`statsmodels.stats.multitest.multipletests`) to all p‑values, storing both raw and FDR‑adjusted values.  
  - Write `results/statistical_result.json` conforming to `specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/statistical_result.schema.yaml` (populate `model_summary`, `is_descriptive_mode`, VIF values, collinearity flag, and fixed‑effects table).  
  - **Verification**: `python -m jsonschema -i results/statistical_result.json specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/statistical_result.schema.yaml` exits 0; the JSON contains a boolean `collinearity_passed` and, when mixed‑effects is used, a non‑null `fixed_effects` list.

---

## Phase 8 – Sensitivity Sweep & Plotting (FR‑007, SC‑001)

- [ ] T009 [P] [US3] **Sweep Leiden resolution and Silhouette thresholds, compute variance of ARI/NMI, and generate a sensitivity plot**  
  - For every embedding, re‑run Leiden clustering at each resolution in `config.LEIDEN_RESOLUTIONS` (0.1 → 1.0 step 0.1) and for each of the three silhouette thresholds `{0.4,0.5,0.6}`.  
  - Compute ARI and NMI for every (resolution, threshold) pair; store rows in `figures/sensitivity_data.csv` (`dataset_id,method,resolution,silhouette_threshold,ari,nmi`).  
  - Calculate `variance_ari` and `variance_nmi` across all resolutions for each method; set `stability_passed = (variance_ari < 0.05) and (variance_nmi < 0.05)`.  
  - Write `results/sensitivity_analysis.json` containing `thresholds`, `variance_ari`, `variance_nmi`, `stability_passed`.  
  - Produce a line plot `figures/sensitivity_plot.png` (resolution on x‑axis, ARI and NMI on y‑axis, separate lines per method, faceted by dataset).  
  - **Verification**: `jq . results/sensitivity_analysis.json` shows the required keys; `python - <<PY ...` can load the CSV and confirm the number of rows equals `datasets × methods × resolutions × thresholds`; `file figures/sensitivity_plot.png` reports an image type.

---

## Phase 9 – Aggregation & Validation Report (SC‑003, SC‑004, SC‑005)

- [ ] T010 [P] [US1] **Merge all metrics, compute execution metadata, and emit a comprehensive validation report**  
  - Merge `data/metrics/fidelity_results.csv` with each dataset’s geometric JSON to create `data/results/combined_metrics.parquet` containing columns: `dataset_id,method,ari,nmi,silhouette_score,optimal_resolution,trustworthiness,local_continuity,runtime_seconds,peak_ram_gb`.  
  - Read `results/monitoring.csv` to derive `peak_memory_bytes` (max of `peak_ram_bytes`) and `total_runtime_seconds` (sum of `wall_time_s`).  
  - Count processed vs skipped datasets from `data/manifest.json`.  
  - Write `results/validation_report.txt` with one line per success criterion (SC‑001 … SC‑005), inserting the computed numeric values and pass/fail status.  
  - Update `results/statistical_result.json` to embed the `execution_metadata` block (peak memory, total runtime, dataset counts, exit code).  
  - **Verification**: `cat results/validation_report.txt` contains lines beginning with `SC-001:` … `SC-005:`; the values match those in `results/statistical_result.json`; a Python check confirms `peak_memory_bytes <= config.MEMORY_LIMIT_BYTES` and `total_runtime_seconds <= config.RUNTIME_LIMIT_SECONDS`.

---

## Phase 10 – Methods/Results Summary & Reproducibility Guide (Paper Hand‑off)

- [ ] T011 [P] [US1] **Write `paper/summary.md` and `paper/REPRODUCIBILITY.md` linking all numeric results to artifacts**  
  - `paper/summary.md` includes:  
    * **Methods** – concise description of data sources, preprocessing, sampling, embedding hyper‑parameters, clustering strategy, statistical modeling, and sensitivity analysis.  
    * **Results** – tables/figures whose numbers are programmatically inserted from `data/results/combined_metrics.parquet`, `results/statistical_result.json`, and `data/manifest.json` (e.g., mean ARI/NMI per method, VIF values, p‑values, variance statistics, stability verdict).  
    * **Limitations** – explicit note of how many GEO datasets were actually obtained and whether the analysis ran in descriptive mode.  
  - `paper/REPRODUCIBILITY.md` lists: seed, all GEO URLs from the manifest, pinned package versions from `code/requirements.txt`, the exact command `python code/main.py`, and the observed SC‑003/SC‑004 metrics.  
  - **Verification**: Running `pandoc paper/summary.md -o paper/summary.html` succeeds; grepping numeric literals in `paper/summary.md` finds them also present in the parquet or JSON files (`grep -Ff <(python -c "import pandas as pd, json, sys; df=pd.read_parquet('data/results/combined_metrics.parquet'); print('\\n'.join(df['ari'].astype(str)))") paper/summary.md` returns matches).  

---

## Phase 11 – Clean Re‑run & Handoff Artifact (Paper Stage)

- [ ] T012 [P] [US1] **Re‑execute the full pipeline from a clean state and produce a handoff hash**  
  - Delete all intermediate folders except `data/raw/` (keep the downloaded raw files): `rm -rf data/processed data/embeddings data/clustering data/metrics data/results figures results/*.csv results/*.json`.  
  - Run `python code/main.py` anew; ensure it completes with exit code 0 (or 1 only if no dataset was available).  
  - Verify that all tests (`python -m pytest code/tests/ -q`) pass and that `results/validation_report.txt` reproduces the same SC lines as before.  
  - Compute SHA‑256 of the final statistical result: `hash=$(sha256sum results/statistical_result.json | cut -d' ' -f1)`.  
  - Write `paper/HANDOFF_READY.txt` containing two lines: the hash and an ISO‑8601 timestamp (`datetime.datetime.utcnow().isoformat()`).  
  - Add a short “Handoff” section to `paper/summary.md` listing the artifacts the downstream paper pipeline should consume (`data/results/combined_metrics.parquet`, `results/statistical_result.json`, `figures/sensitivity_plot.png`, `results/validation_report.txt`).  
  - **Verification**: `sha256sum -c <(echo "$hash  results/statistical_result.json")` succeeds; the timestamp parses via `datetime.fromisoformat`; re‑run of the pipeline yields identical hash (within floating‑point tolerances) and the handoff file exists.  

--- 

### Dependency Mapping (summary)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 | T004, T005 |
| FR‑002 | T005 |
| FR‑003 | T005 |
| FR‑004 | T006 |
| FR‑005 | T007 |
| FR‑006 | T008 |
| FR‑007 | T009 |
| FR‑008 | T008 |
| SC‑001 | T009 |
| SC‑002 | T008 |
| SC‑003 | T003, T010 |
| SC‑004 | T003, T010 |
| SC‑005 | T008 |
| US‑1 | T002, T003, T004, T005, T006, T007, T008, T009, T010, T011, T012 |
| US‑2 | T007 |
| US‑3 | T008, T009 |

All tasks are ordered to respect data flow; each produces a concrete artifact that can be independently validated by the verifier.
