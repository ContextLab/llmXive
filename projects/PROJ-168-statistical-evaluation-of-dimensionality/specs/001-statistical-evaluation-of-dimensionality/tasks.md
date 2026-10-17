# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Inputs**: `spec.md`, `plan.md`, data-model, contracts, and prior reviewer feedback.
This is a re-plan: the prior task list was rejected for format (task tables/fences) and for unverifiable deliverables (Snakemake rules, CI workflow files, truncated `code/utils.py`, missing `results/monitoring.csv`). The new plan uses a single plain-Python pipeline (`code/main.py`) with no Snakemake and no CI-authoring tasks (the platform supplies CI). Every task produces a real, deterministically checkable artifact under project-owned paths. Scientific requirements FR-001–FR-008 and SC-001–SC-005 are fully preserved.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US1] **Establish code layout, configuration constants, and quickstart command; document the directory tree**
  - Create `code/config.py` defining: `SEED=42`, `GEO_ACCESSIONS=["GSE131907", "GSE111322", "GSE150728"]`, `SAMPLE_CELLS_THRESHOLD=10000`, `SAMPLE_SIZE=5000`, `LEIDEN_RESOLUTIONS=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]`, `SILHOUETTE_THRESHOLDS=[0.4,0.5,0.6]`, `MEMORY_LIMIT_BYTES=7000000000`, `RUNTIME_LIMIT_SECONDS=21600`, `K_GEOMETRY=15`.
  - Create `quickstart.md` documenting the single runnable command: `python code/main.py`.
  - Create `code/requirements.txt` pinning: `scanpy`, `anndata`, `leidenalg`, `umap-learn`, `scikit-learn`, `statsmodels`, `pandas`, `pyarrow`, `numpy`, `scipy`, `matplotlib`, `psutil`, `GEOparse`, `jsonschema`.
  - After `code/main.py --setup` (or `llmxive_toolkit.paths`) has created `data/raw/`, `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `data/results/`, `figures/`, `paper/`, `code/tests/`, write `results/dir_listing.txt` by executing `python -c "import subprocess; open('results/dir_listing.txt','w').write(subprocess.run(['find','data','figures','code','results','-type','d'],capture_output=True,text=True).stdout)"`. The listing file is the reviewer-required proof that the directories exist on disk.
  - *Verification*: `python -c "from code.config import SEED, GEO_ACCESSIONS; assert SEED==42 and len(GEO_ACCESSIONS)==3"` exits 0. `results/dir_listing.txt` exists and contains the strings `data/raw`, `data/processed`, `data/embeddings`, `data/clustering`, `data/metrics`, `figures`, `code/tests`. `quickstart.md` contains the exact command `python code/main.py`.

- [ ] T002 [P] [US1] **Implement the complete resource-monitoring utility and generate `results/monitoring.csv`**
  - Create `code/utils.py` (complete, non-truncated file) containing:
    * `get_logger(name)` returning a configured logger.
    * `MemoryLimitExceeded` exception class.
    * `ResourceMonitor` class whose `run(step_name, fn, *args, **kwargs)` method: (a) records wall-clock via `time.perf_counter()` around `fn(*args, **kwargs)`; (b) samples RSS via `psutil.Process().memory_info().rss` in a background daemon thread every 0.5 s; (c) on completion appends a row `step_name,wall_time_s,peak_ram_bytes` to `results/monitoring.csv` (creating the header `step,wall_time_s,peak_ram_bytes` on first write); (d) raises `MemoryLimitExceeded` and exits non-zero if peak RSS > `config.MEMORY_LIMIT_BYTES` (SC-003); (e) returns `fn`'s result.
    * A `__main__` self-test block that runs `ResourceMonitor().run("selftest", lambda: sum(range(10**6)))` and prints "OK".
  - Execute `python code/utils.py`; this MUST leave `results/monitoring.csv` on disk with the header and a `selftest` row — the previously missing artifact.
  - *Verification*: `python code/utils.py` exits 0. `results/monitoring.csv` exists, its first line is exactly `step,wall_time_s,peak_ram_bytes`, and it contains a row starting with `selftest` whose third field is a positive integer. `python -c "from code.utils import ResourceMonitor, MemoryLimitExceeded, get_logger"` exits 0.

- [ ] T003 [P] [US1] **Resolve data availability: download raw count matrices via GEOparse and produce a schema-valid manifest**
  - Create `code/data_gap_resolver.py` that:
    * Iterates `config.GEO_ACCESSIONS`; for each, attempts `GEOparse.get_GEO(accession, destdir="data/raw/", silent=True)` and, if the GEO record exposes supplementary count-matrix files, downloads them. This is a REAL fetch: on failure it MUST raise/log the failure and record `status="Unavailable"` with the error message — it MUST NOT fall back to synthetic, simulated, or randomly generated count data (fabrication gate).
    * On success, writes the raw file to `data/raw/{accession}/`, computes its SHA-256 checksum, and appends a manifest entry with fields `dataset_id`, `source_url`, `status` ("Available"/"Unavailable"), `error_message`, `checksum`, `raw_file_path`, `processed_file_path` (null), per `specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml`.
    * Writes `data/manifest.json` (with `generated_at` ISO-8601 timestamp). If NO accession is Available, writes `results/data_gap_summary.txt` listing every attempted source and failure reason and exits 1 (plan Phase 0.4 abort condition). If at least one is Available, exits 0.
  - *Verification*: `python code/data_gap_resolver.py` exits 0 (≥1 Available) or 1 with `results/data_gap_summary.txt` present. `python -m jsonschema -i data/manifest.json specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml` exits 0. At least one entry has `"status": "Available"` OR the abort summary exists.

- [ ] T004 [P] [US1] **Preprocess available datasets (log-CPM, HVG selection, cell sampling) and compute geometric diagnostics**
  - Create `code/preprocess.py` that, for each `"Available"` dataset in `data/manifest.json`:
    * Loads the raw count matrix (CSV/MTX/HDF5 via scanpy), validates non-negative integer counts, and extracts ground-truth cell-type labels from GEO metadata (writing them to `data/processed/{dataset_id}_labels.csv` with columns `cell_id,label`); if labels are missing, records the dataset as fidelity-aborted (spec edge case) but still produces embeddings/diagnostics.
    * Applies log-CPM: `log2((counts / row_sum) * 1e6 + 1)`.
    * Selects highly variable genes via scanpy's Seurat-style variance-stabilizing dispersion (`sc.pp.highly_variable_genes`, `flavor="seurat"`); retains the top 2000 HVGs (elbow-based dynamic N permitted, recorded in output).
    * If `n_cells > config.SAMPLE_CELLS_THRESHOLD`, deterministically samples exactly `config.SAMPLE_SIZE` cells (seed derived from `config.SEED` and `dataset_id`); the SAME sampled subset feeds all downstream steps.
    * Computes **global linearity** = `sklearn.manifold.trustworthiness(high_dim_sampled, pca30_of_sampled, n_neighbors=config.K_GEOMETRY)` and **local continuity** = `sklearn.manifold.trustworthiness(pca30_of_sampled, high_dim_sampled, n_neighbors=config.K_GEOMETRY)` (FR-002/FR-003, k=15). If `n_cells < 500`, logs a warning and stores `null` (spec edge case).
    * Writes `data/processed/{dataset_id}_matrix.parquet` (cells × HVGs) and `data/processed/{dataset_id}_geometric.json` with keys `trustworthiness`, `local_continuity`, `n_cells_sampled`, `n_genes_hvg`, `n_genes_original`.
    * Wraps each dataset in `ResourceMonitor.run(f"preprocess_{dataset_id}", ...)`.
  - *Verification*: For each Available dataset, `pandas.read_parquet` on the matrix succeeds with shape `(n_cells_sampled, n_genes_hvg)`, `n_cells_sampled <= config.SAMPLE_SIZE`; the geometric JSON parses with values in `[0,1]` or `null`; `results/monitoring.csv` contains a `preprocess_{dataset_id}` row.

- [ ] T005 [P] [US1] **Generate PCA, t-SNE, and UMAP embeddings from the sampled matrices**
  - Create `code/embeddings.py` that, per dataset, loads `data/processed/{dataset_id}_matrix.parquet` and produces (FR-004):
    * **PCA**: `sklearn.decomposition.PCA(n_components=30, random_state=config.SEED)` → `data/embeddings/{dataset_id}_PCA.csv` with columns `cell_id,PC1..PC30`.
    * **t-SNE**: `sklearn.manifold.TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=config.SEED)` → `data/embeddings/{dataset_id}_tSNE.csv` with columns `cell_id,TSNE1,TSNE2`.
    * **UMAP**: `umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=config.SEED)` → `data/embeddings/{dataset_id}_UMAP.csv` with columns `cell_id,UMAP1,UMAP2`.
    * Each step wrapped in `ResourceMonitor.run(f"embed_{method}_{dataset_id}", ...)`.
  - *Verification*: Each CSV loads with exactly `n_cells_sampled` rows, the correct column count (32 for PCA incl. cell_id, 3 for t-SNE/UMAP), and no missing values; `results/monitoring.csv` has `embed_PCA_*`, `embed_tSNE_*`, `embed_UMAP_*` rows.

- [ ] T006 [P] [US2] **Run Leiden clustering with Silhouette-optimized resolution and compute ARI/NMI fidelity**
  - Create `code/clustering.py` that, for each embedding CSV:
    * Builds a k-NN graph (`n_neighbors=15`) and runs Leiden (`leidenalg.find_partition`) at every resolution in `config.LEIDEN_RESOLUTIONS`; computes `sklearn.metrics.silhouette_score(embedding, labels)` for each; selects the resolution maximizing Silhouette (FR-005).
    * On Leiden failure, retries once with a fixed alternate seed; on second failure writes `"Unavailable"` for that embedding (spec edge case) without crashing.
    * Writes `data/clustering/{dataset_id}_{method}_clusters.csv` with columns `cell_id,cluster_label,silhouette_score,optimal_resolution`.
  - Create `code/metrics.py` that joins cluster labels with ground-truth labels from `data/processed/{dataset_id}_labels.csv` and computes `adjusted_rand_score` and `normalized_mutual_info_score` per (dataset, method); if labels are missing or clustering is `"Unavailable"`, writes `"Unavailable"` for that row. Writes `data/metrics/fidelity_results.csv` with columns `embedding_id,method,dataset_id,ari,nmi,silhouette_score,optimal_resolution` conforming to `specs/001-statistical-evaluation-of-dimensionality/contracts/fidelity_results.schema.yaml` (the `silhouette_threshold` column carries the primary threshold 0.5).
  - *Verification*: Each clusters CSV has `n_cells_sampled` rows; `cluster_label` is a non-negative int or the literal `"Unavailable"`; `fidelity_results.csv` has one row per (dataset, method) with numeric ARI/NMI in [0,1] or `"Unavailable"`, and passes `python -m jsonschema` validation when read as JSON rows against the fidelity contract.

**Checkpoint**: `python code/main.py` (added in T009) executes end-to-end on real downloaded data and produces real result rows under `data/metrics/` and `data/results/`. No report writing from invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] T007 [P] [US3] **Fit the statistical model with BH correction and collinearity check**
  - Create `code/stats.py` that loads `data/metrics/fidelity_results.csv` merged with `data/processed/*_geometric.json`:
    * If ≥2 datasets with valid fidelity: fits `statsmodels` mixed-effects `fidelity ~ method + (1|dataset)` (FR-006); if exactly 1 dataset: fits fixed-effects ANOVA `fidelity ~ method` and sets `is_descriptive_mode=true`.
    * Computes VIF for method dummies; flags `collinearity_passed=false` if any VIF ≥ 5 (SC-005). Runs Shapiro-Wilk on residuals and logs violations.
    * Applies Benjamini-Hochberg FDR correction (`statsmodels.stats.multitest.multipletests(method="fdr_bh")`) to all p-values (FR-008, SC-002).
    * Writes `results/statistical_result.json` conforming to `specs/001-statistical-evaluation-of-dimensionality/contracts/statistical_result.schema.yaml`, with `model_summary` (formula, fixed_effects with `p_value_fdr`, `random_effects_variance`, `vif_values`, `collinearity_passed`), `sensitivity_analysis` (filled by T008), and `execution_metadata` (filled by T010).
  - *Verification*: `python -m jsonschema -i results/statistical_result.json specs/001-statistical-evaluation-of-dimensionality/contracts/statistical_result.schema.yaml` exits 0; all `p_value_fdr` values lie in [0,1]; `collinearity_passed` is boolean.

- [ ] T008 [P] [US3] **Run the sensitivity sweep and produce the sensitivity plot**
  - Create `code/sensitivity.py` that:
    * Re-runs Leiden at every resolution in `config.LEIDEN_RESOLUTIONS` on each embedding and recomputes ARI/NMI against ground truth (FR-007); also evaluates the Silhouette-threshold variants {0.4, 0.5, 0.6} from `config.SILHOUETTE_THRESHOLDS`.
    * Computes `variance_ari` and `variance_nmi` across the sweep; sets `stability_passed = (variance_ari < 0.05) and (variance_nmi < 0.05)` (SC-001).
    * Writes `results/sensitivity_analysis.json` (`thresholds`, `variance_ari`, `variance_nmi`, `stability_passed`) and merges it into `results/statistical_result.json`.
    * Writes `figures/sensitivity_data.csv` (`dataset_id,method,resolution,ari,nmi`) and renders `figures/sensitivity_plot.png` with matplotlib (x = resolution; one line per method, faceted by dataset; horizontal dashed reference at the primary ARI/NMI).
  - *Verification*: JSON contains numeric `variance_ari`, `variance_nmi`, boolean `stability_passed`; CSV covers every (dataset, method, resolution) combination; `file figures/sensitivity_plot.png` reports an image MIME type.

- [ ] T009 [P] [US1] **Orchestrate the full pipeline end-to-end with focused tests and the validation report**
  - Create `code/main.py` that runs, in order: `data_gap_resolver` → `preprocess` → `embeddings` → `clustering` → `metrics` → `stats` → `sensitivity` → `aggregate`, catching exceptions, logging them, and setting the exit code (0 when ≥1 dataset processed; 1 only on the no-data abort). It enforces the SC-004 runtime limit: if total wall-clock exceeds `config.RUNTIME_LIMIT_SECONDS`, exit 1.
  - Create focused tests in `code/tests/` (run on small REAL fixtures derived from the downloaded data, never synthetic stand-ins for measurements): `test_preprocess.py` (log-CPM non-negativity; `0 < n_genes_hvg < n_genes_original`; sampling yields exactly `SAMPLE_SIZE` when applicable), `test_embeddings.py` (embedding shapes, no NaN), `test_clustering.py` (ARI of identical label vectors = 1.0; silhouette in [-1,1]), `test_metrics.py` (ARI/NMI ranges on known cases), `test_utils.py` (`ResourceMonitor.run` appends a monitoring row; a mocked inflated RSS raises `MemoryLimitExceeded`).
  - Run `python code/main.py` end-to-end on the real data.
  - *Verification*: `python -m pytest code/tests/ -q` exits 0. `python code/main.py` exits 0 (or 1 only on no-data abort). `results/monitoring.csv` contains rows for every executed stage.

- [ ] T010 [P] [US1] **Aggregate metrics, enrich execution metadata, and emit the validation report**
  - Create `code/aggregate.py` that:
    * Merges `data/metrics/fidelity_results.csv` with geometric JSONs on (dataset_id, method) and writes `data/results/combined_metrics.parquet` with columns `dataset_id,method,ari,nmi,silhouette_score,optimal_resolution,trustworthiness,local_continuity,runtime_seconds,peak_ram_gb`.
    * Computes `execution_metadata`: `peak_memory_bytes` = max of `results/monitoring.csv` peak column; `total_runtime_seconds` = sum of wall times; `datasets_processed` / `datasets_skipped` from `data/manifest.json`; `exit_code`. Fails (exit 1) if `peak_memory_bytes > config.MEMORY_LIMIT_BYTES` (SC-003).
    * Writes `results/validation_report.txt` with one line per success criterion: `SC-001: variance_ari=…, variance_nmi=…, stability_passed=…`; `SC-002: method_effect_p_value=…, fdr_corrected=…`; `SC-003: peak_ram_bytes=…, limit_7gb=…`; `SC-004: total_runtime_seconds=…, limit_21600s=…`; `SC-005: max_vif=…, collinearity_passed=…`; plus a list of Unavailable datasets and the modeling mode (mixed-effects vs descriptive ANOVA).
  - *Verification*: `pandas.read_parquet("data/results/combined_metrics.parquet")` succeeds with all listed columns; `results/statistical_result.json` contains a complete `execution_metadata` object; `results/validation_report.txt` contains all five SC lines whose values match the JSON and monitoring CSV.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 [P] [US1] **Write the methods/results summary and reproducibility guide**
  - Create `paper/summary.md` with **Methods** (data sources, log-CPM, HVG selection, sampling strategy, embedding hyperparameters, Leiden/Silhouette optimization, ARI/NMI, statistical model), **Results** (all numbers inserted programmatically from `data/results/combined_metrics.parquet`, `results/statistical_result.json`, `data/manifest.json` — mean ARI/NMI per method, VIF values, raw and FDR-adjusted p-values, sensitivity variances, stability verdict), and **Limitations** (how many of the three GEO datasets were actually obtained; descriptive-mode caveat when <2 datasets; any Unavailable datasets).
  - Create `paper/REPRODUCIBILITY.md` with the seed, all source URLs from `data/manifest.json`, pinned versions from `code/requirements.txt`, the re-run command `python code/main.py`, and the SC-003/SC-004 thresholds alongside actual measured values.
  - *Verification*: `pandoc paper/summary.md -o paper/summary.html` exits 0; every numeric literal in the Results section traces to `combined_metrics.parquet` or the JSON artifacts (spot-check by grep); `paper/REPRODUCIBILITY.md` contains the seed value, at least one URL, and the command `python code/main.py`.

- [ ] T012 [P] [US1] **Re-run the documented workflow from its declared inputs and record the paper-stage handoff**
  - Re-execute `python code/main.py` from a clean `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `results/` state (raw `data/raw/` retained) and confirm the tests and all artifact checks from T009–T010 still pass.
  - Create `paper/HANDOFF_READY.txt` containing the SHA-256 hash of `results/statistical_result.json` (computed via `hashlib.sha256`) and an ISO-8601 completion timestamp.
  - Document the paper-stage handoff in `paper/summary.md` (a short "Handoff" section listing the result/figure artifacts the paper pipeline should consume: `data/results/combined_metrics.parquet`, `results/statistical_result.json`, `figures/sensitivity_plot.png`, `results/validation_report.txt`). Paper layout, PDF compilation and publication remain with the subsequent paper pipeline.
  - *Verification*: `sha256sum results/statistical_result.json` matches the hash in `paper/HANDOFF_READY.txt`; the timestamp parses via `datetime.fromisoformat`; the re-run exits 0 and `results/validation_report.txt` is regenerated with all five SC lines.

---

## Dependencies and requirement coverage

- **FR-001** (download/preprocess datasets) — T003, T004 → `data/manifest.json`, `data/processed/*_matrix.parquet`
- **FR-002** (global linearity, Trustworthiness k=15) — T004 → `data/processed/*_geometric.json`
- **FR-003** (local continuity, LCA k=15) — T004 → `data/processed/*_geometric.json`
- **FR-004** (PCA/t-SNE/UMAP embeddings) — T005 → `data/embeddings/*.csv`
- **FR-005** (ARI/NMI vs ground truth) — T006 → `data/metrics/fidelity_results.csv`
- **FR-006** (mixed-effects / ANOVA model) — T007 → `results/statistical_result.json`
- **FR-007** (sensitivity sweep) — T008 → `results/sensitivity_analysis.json`, `figures/sensitivity_plot.png`
- **FR-008** (Benjamini-Hochberg correction) — T007 → `results/statistical_result.json`
- **SC-001** (variance < 0.05) — T008 → `results/sensitivity_analysis.json`
- **SC-002** (FDR-corrected method effect) — T007 → `results/statistical_result.json`
- **SC-003** (peak RAM ≤ 7 GB) — T002, T010 → `results/monitoring.csv`, `results/validation_report.txt`
- **SC-004** (runtime ≤ 21,600 s) — T002, T009 → `results/monitoring.csv`, `results/validation_report.txt`
- **SC-005** (VIF < 5) — T007 → `results/statistical_result.json`
- **Spec edge cases** (low cell count, missing labels, Leiden failure) — T004, T006 → warnings/nulls/"Unavailable" handling
- **US-1 / US-2 / US-3** — T001–T012 → full pipeline artifacts

**Execution order**: T001 → T002 → T003 → T004 → T005 → T006 → T007 ↔ T008 → T009 → T010 → T011 → T012.

## Revision notes (addressing rejected prior tasks)

- Prior T001 (directory proof): now produces `results/dir_listing.txt` as an executable verification artifact.
- Prior T021/T029 (truncated `code/utils.py`, missing `results/monitoring.csv`): T002 requires the complete file plus an executed self-test that writes the CSV.
- Prior T028/T054 (Snakemake rules): dropped — the pipeline is plain Python orchestrated by `code/main.py`; no Snakemake artifacts are promised.
- Prior T030/T032 (GitHub Actions workflow): dropped — the platform supplies CI; SC-003/SC-004 are enforced inside the pipeline itself (T002, T009, T010) via `ResourceMonitor` and the runtime check in `main.py`.
- Prior T049 (plan.md update): superseded — the active plan.md already documents the fixed-effects/mixed-effects fallback and the resolution sweep; tasks T007/T008 implement it directly.
