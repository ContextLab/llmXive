# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data  

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and reviewer feedback.  
All tasks are expressed as plain‑text checklist items; each unchecked box (`- [ ]`) represents work that must produce a real, verifiable artifact under a project‑owned path.

---  

## Phase 0 – Project Foundations & Specification Alignment  

- [X] **T001** [US1] Create the required project directory tree and provide a verifiable listing.  
  - Create the following directories (all under the repository root):  
    `data/raw/`, `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `data/results/`, `figures/`, `results/`, `code/`, `code/tests/`, `paper/`, `.github/workflows/`.  
  - Generate a plain‑text directory listing `results/dir_listing.txt` by running:  
    `find data code results figures paper .github -type d > results/dir_listing.txt`.  
  - **Verification**: `cat results/dir_listing.txt` contains each of the directories listed above; a Python assertion `assert pathlib.Path('results/dir_listing.txt').exists()` exits 0.

- [X] **T004** [US1] Create a lightweight CI script (`code/ci_limits.py`) that enforces SC‑003/SC‑004.  
  - The script reads `results/monitoring.csv`, checks the two thresholds, and exits with status 1 on violation, printing a clear message.  
  - It will be called from the GitHub Actions workflow (see T003).  
  - **Verification**: Running `python code/ci_limits.py` on a deliberately violating CSV returns exit code 1; `python -c "import subprocess, sys; sys.exit(subprocess.call(['python','code/ci_limits.py']))"` returns the expected code.

- [ ] **T003** [US1] Add a GitHub Actions workflow (`.github/workflows/research.yml`) that runs the full pipeline and enforces the runtime & RAM limits (SC‑003, SC‑004).  
  - The workflow must (a) set up the Python environment, (b) run `python code/main.py`, (c) capture the exit code, and (d) fail the job if the exit code ≠ 0.  
  - Include a step that parses `results/monitoring.csv` and aborts with `error` if any `peak_ram_bytes` > 7 000 000 000 or if the summed `wall_time_s` > 21 600.  
  - The workflow now references the script created in T004, guaranteeing the script exists before the workflow runs.  
  - **Verification**: `yq eval '.jobs.build.steps[] | select(.name == "Enforce limits")' .github/workflows/research.yml` returns a non‑null object; a dry‑run of the workflow (`act -j build --dry-run`) shows the limit‑enforcement step present.

- [X] **T005** [US1] Implement a full `code/utils.py` containing a robust `ResourceMonitor`.  
  - The module must provide:  
    * `get_logger(name)` – a logger configured with INFO level and a file handler `results/pipeline.log`.  
    * `MemoryLimitExceeded` exception.  
    * `ResourceMonitor` class with method `run(step_name, fn, *args, **kwargs)` that  
        - records start time,  
        - executes `fn(*args, **kwargs)` while periodically sampling RSS via `psutil` (every 0.5 s),  
        - aborts with `MemoryLimitExceeded` if peak RSS > `config.MEMORY_LIMIT_BYTES` (7 GB),  
        - writes a row `step_name,wall_time_s,peak_ram_bytes` to `results/monitoring.csv` (creating the header on first write).  
    * A `__main__` self‑test that runs a trivial computation and prints “ResourceMonitor self‑test OK”.  
  - Execute the self‑test to generate `results/monitoring.csv` with at least one row.  
  - **Verification**: `head -n 2 results/monitoring.csv` shows the header `step,wall_time_s,peak_ram_bytes` and a row beginning with `selftest`; `python -c "import pandas as pd; df=pd.read_csv('results/monitoring.csv'); assert not df.empty"` exits 0.

- [ ] **T006** [US1] Provide a Snakemake workflow (`Snakefile`) that includes a `verify_data_availability` rule.  
  - The rule must read `data/manifest.json` (produced by the data‑gap resolver) and abort the workflow with a clear error message if **all** datasets have `"status": "Unavailable"`.  
  - The rule must be a prerequisite for the `download` rule (i.e., `download: verify_data_availability`).  
  - Include a minimal `data_gap_resolver` rule that calls `code/data_gap_resolver.py`.  
  - **Verification**: Running `snakemake -n verify_data_availability` prints “All datasets unavailable – aborting.” when appropriate; the rule appears in the DAG (`snakemake -p -d . --dag | dot -Tpng -o dag.png` includes a node named `verify_data_availability`).

---  

## Phase 1 – Data‑Gap Resolution (Phase 0 blocker)  

- [ ] **T007** [FR‑001] Download raw count matrices, compute checksums, write a schema‑valid manifest, and enforce the three‑dataset requirement.   <!-- FAILED-IN-EXECUTION: code/data_gap_resolver.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_gap_resolver.py exit=1 -->
  - Implement `code/data_gap_resolver.py` that iterates over `config.GEO_ACCESSIONS`, uses `GEOparse` to locate supplementary count‑matrix files, downloads each into `data/raw/<accession>/`, and records: `dataset_id`, `source_url`, `status` (`Available`/`Unavailable`), `checksum`, `raw_file_path`, `processed_file_path` (null for now).  
  - Assemble `data/manifest.json` conforming to `specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/dataset.schema.yaml`.  
  - **Verification of citation accuracy**: for each `source_url` ensure the URL resolves and the dataset citation can be validated (placeholder step that would be caught by the Reference‑Validator).  
  - After manifest creation, count entries with `"status":"Available"`. If the count is **less than three**, write `results/data_gap_summary.txt` explaining the shortfall and exit 1 (pipeline abort).  
  - **Verification**: `python -m jsonschema -i data/manifest.json specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/dataset.schema.yaml` exits 0; when fewer than three datasets are available, `cat results/data_gap_summary.txt` exists and contains “abort”.

---  

## Phase 2 – Ingestion & Pre‑processing (FR‑002, FR‑003)  

- [ ] **T008** [FR‑001 FR‑002 FR‑003 US1] Load each available dataset, apply log‑CPM, select HVGs, optionally sample cells, and compute geometric diagnostics.   <!-- FAILED-IN-EXECUTION: code/preprocess_and_geometry.py exit=1 -->
  - For every entry in `data/manifest.json` with `"status":"Available"`:  
    1. Load the raw matrix (`scanpy.read_10x_mtx` or appropriate reader).  
    2. Extract ground‑truth cell‑type labels and write `data/processed/<dataset_id>_labels.csv`.  
    3. Perform log‑CPM: `log2((counts / counts.sum(axis=1)[:, None]) * 1e6 + 1)`.  
    4. Run `sc.pp.highly_variable_genes(..., flavor="seurat")`; retain the top‑N HVGs where **N** is the elbow point of the variance curve (recorded in `data/processed/<dataset_id>_hvg.txt`).  
    5. If `n_cells > config.SAMPLE_CELLS_THRESHOLD` (10 000), deterministically sample exactly `config.SAMPLE_SIZE` cells (`np.random.default_rng(config.SEED).choice`).  
    6. Compute **global linearity** (Trustworthiness, `k=15`) on the sampled high‑dimensional matrix against its PCA‑30 projection.  
    7. Compute **local continuity** (reverse Trustworthiness, same `k`).  
    8. Write the processed matrix to `data/processed/<dataset_id>_matrix.parquet` and diagnostics to `data/processed/<dataset_id>_geometric.json`.  
    9. Wrap the whole per‑dataset routine with `ResourceMonitor.run(f"preprocess_{dataset_id}", ...)`.  
  - **Verification**: Each parquet file loads with shape `(≤config.SAMPLE_SIZE, ≤2000)`; the corresponding JSON contains keys `trustworthiness` and `local_continuity` with float values in `[0,1]` (or `null` if `<500` cells). `results/monitoring.csv` contains a row `preprocess_<dataset_id>`.

---  

## Phase 3 – Embedding Generation (FR‑004)  

- [ ] **T009** [FR‑004 US1] Produce PCA, t‑SNE, and UMAP embeddings for every processed dataset.  
  - Load `data/processed/<dataset_id>_matrix.parquet`.  
  - **PCA**: `sklearn.decomposition.PCA(n_components=30, random_state=config.SEED)` → write `data/embeddings/<dataset_id>_PCA.csv` (columns: `cell_id,PC1,…,PC30`).  
  - **t‑SNE**: `sklearn.manifold.TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=config.SEED)` → write `data/embeddings/<dataset_id>_tSNE.csv`.  
  - **UMAP**: `umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=config.SEED)` → write `data/embeddings/<dataset_id>_UMAP.csv`.  
  - Each embedding step is wrapped with `ResourceMonitor.run(f"embed_{method}_{dataset_id}", ...)`.  
  - **Verification**: Each CSV loads with exactly the sampled number of rows; PCA CSV has 31 columns (cell_id + 30 PCs), t‑SNE/UMAP have 3 columns (cell_id + 2 dims). No `NaN` values; `results/monitoring.csv` includes rows `embed_PCA_<dataset_id>`, `embed_tSNE_<dataset_id>`, `embed_UMAP_<dataset_id>`.

---  

## Phase 4 – Clustering & Fidelity Evaluation (FR‑005)  

- [ ] **T010** [FR‑005 US2] Run Leiden clustering with silhouette‑optimised resolution and compute ARI/NMI.  
  - For each embedding CSV (`data/embeddings/<dataset_id>_<method>.csv`):  
    1. Build a k‑NN graph (`n_neighbors=15`).  
    2. Iterate over `config.LEIDEN_RESOLUTIONS` (0.1 → 1.0 step 0.1); for each resolution compute `sklearn.metrics.silhouette_score`.  
    3. Select the resolution with maximal silhouette; record the score and the chosen resolution.  
    4. On failure, retry once with a different fixed seed; if still failing, write `"Unavailable"` for that embedding in the downstream files.  
    5. Write `data/clustering/<dataset_id>_<method>_clusters.csv` (`cell_id,cluster_label,silhouette_score,optimal_resolution`).  
  - Join clustering labels with ground‑truth labels (`data/processed/<dataset_id>_labels.csv`) and compute `adjusted_rand_score` and `normalized_mutual_info_score`.  
  - Write `data/metrics/fidelity_results.csv` with columns: `embedding_id,method,dataset_id,ari,nmi,silhouette_score,optimal_resolution`. The `silhouette_score` column stores the optimal silhouette; the required `silhouette_threshold` field (for the sensitivity sweep) will be populated later.  
  - **Verification**: `pandas.read_csv('data/metrics/fidelity_results.csv')` yields one row per (dataset, method) with `ari` and `nmi` in `[0,1]` or the literal `"Unavailable"`; schema validation via `python -m jsonschema -i data/metrics/fidelity_results.csv specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/fidelity_results.schema.yaml` passes.

---  

## Phase 5 – Statistical Modeling & Multiple‑Testing (FR‑006 FR‑008 SC‑002 SC‑005)  

- [ ] **T011** [FR‑006 FR‑008 SC‑002 SC‑005 US3] Fit a **mixed‑effects** model; abort if insufficient datasets.  
  - Load `data/metrics/fidelity_results.csv` (filter out rows with `"Unavailable"`).  
  - Merge with geometric diagnostics (`data/processed/*_geometric.json`) on `dataset_id`.  
  - Verify that **at least two** datasets have valid rows; if not, write `results/model_abort.txt` explaining the shortfall and exit 1 (pipeline abort).  
  - Fit a linear mixed‑effects model `fidelity ~ method + (1|dataset)` using `statsmodels.MixedLM`.  
  - Compute VIF for the method dummy variables; abort the step (set `collinearity_passed = false`) if any VIF ≥ 5.  
  - Perform Shapiro‑Wilk on residuals; log a warning if normality fails (does not abort).  
  - Apply Benjamini‑Hochberg (`statsmodels.stats.multitest.multipletests`) to all p‑values, storing both raw and FDR‑adjusted values.  
  - Write `results/statistical_result.json` conforming to `specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/statistical_result.schema.yaml`.  
  - **Verification**: `python -m jsonschema -i results/statistical_result.json specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/statistical_result.schema.yaml` exits 0; the JSON contains the boolean `collinearity_passed`, the list `fixed_effects`, and `"is_descriptive_mode": false`.

---  

## Phase 6 – Sensitivity Sweep & Plotting (FR‑007 SC‑001)  

- [ ] **T012** [FR‑007 SC‑001 US3] Sweep **silhouette‑threshold** values {0.4, 0.5, 0.6} and compute variance of ARI/NMI.  
  - For every embedding, re‑run Leiden clustering at each resolution in `config.LEIDEN_RESOLUTIONS` **and** for each silhouette‑threshold value in the set {0.4, 0.5, 0.6}.  
  - For a given threshold, only accept clustering resolutions whose silhouette score meets or exceeds the threshold; compute ARI and NMI for those accepted resolutions.  
  - Store rows in `figures/sensitivity_data.csv` (`dataset_id,method,resolution,silhouette_threshold,ari,nmi`).  
  - Calculate `variance_ari` and `variance_nmi` across all **threshold** values (aggregated over resolutions) for each method; set `stability_passed = (variance_ari < 0.05) and (variance_nmi < 0.05)`.  
  - Write `results/sensitivity_analysis.json` containing `thresholds`, `variance_ari`, `variance_nmi`, `stability_passed`.  
  - Produce a line plot `figures/sensitivity_plot.png` (silhouette threshold on x‑axis, ARI & NMI on y‑axis, separate lines per method, faceted by dataset).  
  - **Verification**: `jq . results/sensitivity_analysis.json` shows the required keys; a Python script can load `figures/sensitivity_data.csv` and confirms the row count equals `datasets × methods × len(config.LEIDEN_RESOLUTIONS) × 3`; `file figures/sensitivity_plot.png` reports an image file.

---  

## Phase 7 – Aggregation, Execution Metadata & Validation Report (SC‑003 SC‑004 SC‑005)  

- [ ] **T013** [SC‑003 SC‑004 SC‑005 US1] Merge all metrics, compute execution metadata, and emit a comprehensive validation report.  
  - Join `data/metrics/fidelity_results.csv` with each dataset’s geometric JSON to create `data/results/combined_metrics.parquet` containing: `dataset_id,method,ari,nmi,silhouette_score,optimal_resolution,trustworthiness,local_continuity,runtime_seconds,peak_ram_gb`.  
  - Read `results/monitoring.csv` to derive `peak_memory_bytes` (max of `peak_ram_bytes`) and `total_runtime_seconds` (sum of `wall_time_s`).  
  - Count processed vs skipped datasets from `data/manifest.json`.  
  - Write `results/validation_report.txt` with one line per success criterion (SC‑001 … SC‑005), inserting the computed numeric values and a PASS/FAIL flag.  
  - Update `results/statistical_result.json` to embed the `execution_metadata` block (peak memory, total runtime, dataset counts, exit code).  
  - **Verification**: `cat results/validation_report.txt` contains lines starting with `SC-001:` … `SC-005:`; a Python script confirms that the values in the report match those stored in `results/statistical_result.json`; `grep -E "peak_memory_bytes|total_runtime_seconds" results/statistical_result.json` returns non‑empty results.

---  

## Phase 8 – Methods & Results Summary, Reproducibility Guide (Paper Hand‑off)  

- [ ] **T014** [US1] Write `paper/summary.md` and `paper/REPRODUCIBILITY.md` linking all numeric results to artifacts.  
  - `paper/summary.md` must include:  
    * **Methods** – concise description of data sources, preprocessing, sampling, embedding hyper‑parameters, clustering strategy, statistical modeling, and sensitivity analysis.  
    * **Results** – tables/figures whose numbers are programmatically inserted from `data/results/combined_metrics.parquet`, `results/statistical_result.json`, and `data/manifest.json` (e.g., mean ARI/NMI per method, VIF values, p‑values, variance statistics, stability verdict).  
    * **Limitations** – explicit note of how many GEO datasets were actually obtained and that the analysis proceeds only when ≥ 2 datasets enable a mixed‑effects model.  
  - `paper/REPRODUCIBILITY.md` must list: seed, all GEO URLs (from the manifest), pinned package versions (`code/requirements.txt`), the exact command `python code/main.py`, and the observed SC‑003/SC‑004 metrics.  
  - **Verification**: Running `pandoc paper/summary.md -o paper/summary.html` succeeds; grepping numeric literals in `paper/summary.md` finds matching entries in the parquet/JSON files (`grep -F "$(python -c "import pandas as pd; df=pd.read_parquet('data/results/combined_metrics.parquet'); print(df['ari'].iloc[0])")" paper/summary.md` returns at least one match).

---  

## Phase 9 – Clean Re‑run & Handoff Artifact (Paper Stage)  

- [ ] **T015** [US1] Re‑execute the full pipeline from a clean state and produce a handoff hash.  
  - Delete all intermediate folders except `data/raw/` (keep the downloaded raw files):  
    `rm -rf data/processed data/embeddings data/clustering data/metrics data/results figures results/*.csv results/*.json`.  
  - Run `python code/main.py` anew; ensure it completes with exit code 0 (or 1 only if the three‑dataset requirement was not met).  
  - Verify that all tests (`python -m pytest code/tests/ -q`) pass and that `results/validation_report.txt` reproduces the same SC lines as before.  
  - Compute SHA‑256 of the final statistical result:  
    `hash=$(sha256sum results/statistical_result.json | cut -d' ' -f1)`.  
  - Write `paper/HANDOFF_READY.txt` containing two lines: the hash and an ISO‑8601 timestamp (`datetime.datetime.utcnow().isoformat()`).  
  - Append a short “Handoff” section to `paper/summary.md` listing the downstream artifacts (`data/results/combined_metrics.parquet`, `results/statistical_result.json`, `figures/sensitivity_plot.png`, `results/validation_report.txt`).  
  - **Verification**: `sha256sum -c <(echo "$hash  results/statistical_result.json")` succeeds; the timestamp parses via `datetime.fromisoformat`; a second clean run yields an identical hash (within floating‑point tolerances) and the handoff file exists.

---  

### Dependency Mapping (summary)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 | T007, T008 |
| FR‑002 | T008 |
| FR‑003 | T008 |
| FR‑004 | T009 |
| FR‑005 | T010 |
| FR‑006 | T011 |
| FR‑007 | T012 |
| FR‑008 | T011 |
| SC‑001 | T012 |
| SC‑002 | T011 |
| SC‑003 | T003, T004, T005 |
| SC‑004 | T003, T004, T005 |
| SC‑005 | T011 |
| US‑1 | T001‑T015 (all) |
| US‑2 | T010 |
| US‑3 | T011, T012 |

All tasks are ordered to respect data flow; each produces a concrete artifact that can be independently validated by the verifier.  