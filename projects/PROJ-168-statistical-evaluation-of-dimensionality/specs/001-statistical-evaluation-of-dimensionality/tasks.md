# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Inputs**: `spec.md`, `plan.md`, data-model, contracts, and prior verification feedback.
All tasks are unchecked to enable independent verification. This re-plan consolidates the prior 19-task list into substantive, individually verifiable research tasks, removes platform-owned work (CI workflows, Snakemake scaffolding — the platform supplies CI), and repairs the rejected items: resource monitoring is implemented as an in-process `psutil` wrapper producing `results/monitoring.csv` (T004), no Snakemake rules are tasked, and the plan-consistency update is folded into the reporting task (T012). All scientific requirements (FR-001–FR-008, SC-001–SC-005) are preserved.

## Task format and paths

Use `- [ ] T### [P?] [USx?] description with exact artifact paths`. Paths are relative to the project directory. The platform provides common scientific packages and `llmxive_toolkit` (`paths`, `get_logger`); installing numpy/pandas/scipy/matplotlib/pytest is never a task.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] Establish the project layout, configuration, and documented runnable command.
  - Use `llmxive_toolkit.paths` to create `data/raw/`, `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `data/results/`, `figures/`, `paper/` on demand; do not write to `state/` or `.github/`.
  - Implement `code/config.py` with: `SEED = 42`; path constants for the directories above; `ACCESSIONS = ["GSE131907", "GSE111322", "GSE150728"]`; hyperparameters `PCA_N_COMPONENTS = 30`, `TSNE_PERPLEXITY = 30`, `TSNE_N_ITER = 1000`, `UMAP_N_NEIGHBORS = 15`, `UMAP_MIN_DIST = 0.1`, `LEIDEN_RESOLUTIONS = [0.1..1.0 step 0.1]`, `SILHOUETTE_THRESHOLDS = [0.4, 0.5, 0.6]`, `K_NEIGHBORS_GEOMETRIC = 15`, `SAMPLE_CELLS_THRESHOLD = 10000`, `SAMPLE_SIZE = 5000`, `MEMORY_LIMIT_BYTES = 7_000_000_000`, `RUNTIME_LIMIT_SECONDS = 21600`.
  - Write `quickstart.md` at the project root documenting the command `python code/main.py --config code/config.py` and what it does (resolve data sources, download, preprocess, embed, cluster, evaluate fidelity, fit statistics, aggregate).
  - Output: `code/config.py`, `quickstart.md`, directory tree.
  - Verification: `python -c "from code.config import SEED, ACCESSIONS, SILHOUETTE_THRESHOLDS"` succeeds; `cat quickstart.md` contains the runnable command; `ls data/raw data/processed data/results code figures paper` shows all directories exist.

- [ ] T002 [US1] Implement `code/utils.py` with resource monitoring that actually executes, records, and enforces limits.
  - Implement `get_logger(name)` (or use `llmxive_toolkit.get_logger`) writing to `results/run_log.txt` and stdout.
  - Implement `ResourceMonitor` with a `run(step_name, fn, *args, **kwargs)` context/method that: calls the callable, measures wall-clock time with `time.perf_counter()`, samples peak RSS via `psutil.Process().memory_info().rss` (polling in a background thread or reading `resource.getrusage(RUSAGE_SELF).ru_maxrss` after the step), appends a row `step,wall_time_s,peak_ram_bytes` to `results/monitoring.csv` (create with header on first use), and raises `MemoryLimitExceeded` (exit code 1) if peak RSS > 7,000,000,000 bytes (SC-003).
  - Implement `assert_budgets(monitoring_csv)` that sums `wall_time_s`, takes max `peak_ram_bytes`, and exits 1 if total > 21,600 s (SC-004) or peak > 7 GB.
  - Implement `parse_time_output(time_log_str)` extracting `Elapsed (wall clock) time` (seconds) and `Maximum resident set size` (KB) from `/usr/bin/time -v` output, for optional subprocess-based monitoring.
  - Include a `if __name__ == "__main__":` self-test that runs a trivial callable and writes one monitoring row.
  - Output: complete (non-truncated) `code/utils.py`, `results/monitoring.csv` with header `step,wall_time_s,peak_ram_bytes` and ≥1 data row.
  - Verification: `python code/utils.py` exits 0; `results/monitoring.csv` exists, has the header and at least one row with numeric values; `python -c "from code.utils import ResourceMonitor, parse_time_output, assert_budgets"` succeeds.

- [ ] T003 [US1] Implement `code/data_gap_resolver.py` and `code/download.py` that resolve and fetch REAL raw count matrices, failing loudly — never falling back to synthetic data.
  - For each accession in `config.ACCESSIONS`, query GEO with `GEOparse.get_GEO(accession, destdir="data/raw/")` and/or direct HTTPS to GEO supplementary-file URLs; resolve a concrete URL to a raw count matrix (MTX/CSV/H5) plus cell-type metadata. Do NOT use guessed or invented mirrors; record every attempted URL.
  - If no real count matrix can be resolved for an accession, mark it `status: "Unavailable"` with the reason in `error_message` — NEVER generate substitute data.
  - If NO accession resolves to a real raw count matrix, write `results/data_gap_summary.txt` listing every accession, the attempted sources, and the reason, and exit with code 1 (plan Phase 0.4 abort condition). No downstream fabrication.
  - For resolved datasets: download to `data/raw/{dataset_id}_raw.{ext}`, compute SHA-256, and write `data/manifest.json` conforming to `specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml` (fields `dataset_id`, `source_url`, `status`, `error_message`, `checksum`, `raw_file_path`, `processed_file_path`, plus `generated_at`). A failed download MUST raise, not substitute.
  - Also extract ground-truth cell-type labels from the GEO metadata to `data/processed/{dataset_id}_labels.csv` (columns `cell_id`, `cell_type`); if labels are missing for a dataset, record `status: "Unavailable"` with reason "missing ground-truth labels" (spec edge case).
  - Output: `data/manifest.json`, raw files in `data/raw/`, `data/processed/{dataset_id}_labels.csv`, `results/data_gap_summary.txt` (only if gaps).
  - Verification: `data/manifest.json` parses and validates against `dataset.schema.yaml`; every `Available` entry has a 64-hex `checksum` and an existing `raw_file_path`; no synthetic/mock data files exist anywhere in `data/`; if all unavailable, `results/data_gap_summary.txt` exists and the script exits 1.

- [ ] T004 [US1] Implement `code/preprocess.py` (log-CPM, HVG selection, sampling) and compute geometric diagnostics on the high-dimensional space.
  - Read each raw count matrix from `data/raw/`; validate counts are non-negative integers with ≥1 cell and ≥1 gene.
  - Apply log-CPM: `log2((counts / row_total) * 1e6 + 1)`.
  - Select highly variable genes with a variance-stabilizing method (e.g., Seurat-style dispersion or normalized-variance percentile); retain genes up to the elbow of the variance curve (second-derivative detection) or top 2000 if the elbow is ill-defined; record `hvg_count`.
  - If `n_cells > 10000`, sample exactly 5000 cells with a deterministic seed derived from `config.SEED` and the dataset ID; otherwise use all cells. The SAME sampled subset feeds all downstream steps (embeddings, diagnostics, clustering).
  - Save the processed matrix to `data/processed/{dataset_id}_matrix.parquet` (cells × HVG genes).
  - Compute global linearity as `sklearn.manifold.trustworthiness(X_highdim_sampled, X_pca30, n_neighbors=15)` and local continuity as the reverse-direction trustworthiness `trustworthiness(X_pca30, X_highdim_sampled, n_neighbors=15)` (LCA proxy, k=15), both on the sampled high-dimensional space (FR-002, FR-003).
  - If `n_cells < 500`, log a warning and skip geometric diagnostics for that dataset (spec edge case), writing `null` values.
  - Write `data/processed/{dataset_id}_geometric.json` with `trustworthiness`, `local_continuity` (floats in [0,1] or null), `n_cells_sampled`, `n_genes_hvg`.
  - Run under `ResourceMonitor` so preprocessing time/memory land in `results/monitoring.csv`.
  - Output: `data/processed/{dataset_id}_matrix.parquet`, `data/processed/{dataset_id}_geometric.json`, monitoring rows.
  - Verification: `pandas.read_parquet` succeeds on each matrix with non-null numeric values and shape `(n_cells_sampled, n_genes_hvg)`; each geometric JSON parses with `trustworthiness`/`local_continuity` ∈ [0,1] or null; `results/monitoring.csv` gained a `preprocess` row.

- [ ] T005 [US1] Implement `code/embeddings.py` generating PCA, t-SNE, and UMAP embeddings with fixed reproducible hyperparameters (FR-004).
  - Read `data/processed/{dataset_id}_matrix.parquet`; generate: PCA (`n_components=30`) → `data/embeddings/{dataset_id}_PCA.csv`; t-SNE (`perplexity=30`, `n_iter=1000`, fixed seed) → `data/embeddings/{dataset_id}_tSNE.csv`; UMAP (`n_neighbors=15`, `min_dist=0.1`, fixed seed) → `data/embeddings/{dataset_id}_UMAP.csv`.
  - Each CSV has a `cell_id` column plus 30 (PCA) or 2 (t-SNE, UMAP) numeric columns; row order matches the sampled matrix.
  - Wrap each fit in `ResourceMonitor.run(...)` with step names `embed_PCA`, `embed_tSNE`, `embed_UMAP` so per-method runtime and peak RAM are recorded (feeds the `runtime_seconds`/`peak_ram_gb` fields of `metrics_schema.schema.yaml`).
  - Output: three CSVs per dataset, monitoring rows.
  - Verification: each CSV has exactly `n_cells_sampled` rows and the correct column count; no nulls; `results/monitoring.csv` contains rows for all three embedding steps per dataset.

- [ ] T006 [US2] Implement `code/clustering.py` (Leiden with Silhouette-optimized resolution) and `code/metrics.py` (ARI/NMI fidelity) — the first end-to-end fidelity result (FR-005).
  - For each embedding CSV: build a kNN graph (`n_neighbors=15`) and run Leiden (`leidenalg`, fixed seed) for each resolution in `config.LEIDEN_RESOLUTIONS` (0.1–1.0, step 0.1); compute the Silhouette Score of each clustering; select the resolution with maximal Silhouette.
  - On Leiden failure, retry once with a fixed alternate seed; on second failure mark the result `"Unavailable"` in the output and continue (spec edge case).
  - Save `data/clustering/{dataset_id}_{method}_clusters.csv` with columns `cell_id`, `cluster_label`, `silhouette_score`, `optimal_resolution`.
  - In `code/metrics.py`: join cluster labels with ground truth from `data/processed/{dataset_id}_labels.csv`; compute ARI and NMI (`sklearn.metrics`); if labels are missing/incomplete for a dataset, skip fidelity for that dataset and record the error in the summary (spec edge case).
  - Write `data/metrics/fidelity_results.csv` with columns `embedding_id`, `method`, `dataset_id`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`, `runtime_seconds`, `peak_ram_gb` (one row per dataset×method; `"Unavailable"` where clustering failed).
  - Output: `data/clustering/*.csv`, `data/metrics/fidelity_results.csv`.
  - Verification: each clusters CSV has `n_cells_sampled` rows, integer `cluster_label`, `silhouette_score` ∈ [-1,1], `optimal_resolution` ∈ [0.1, 1.0]; `fidelity_results.csv` has one row per dataset×method with `ari`/`nmi` ∈ [0,1] or the literal `"Unavailable"`; no nulls in completed rows.

## Phase 2: Complete the study and validate its evidence

- [ ] T007 [US3] Implement `code/stats.py`: statistical model with collinearity check, normality check, and Benjamini-Hochberg correction (FR-006, FR-008, SC-002, SC-005).
  - Read `data/metrics/fidelity_results.csv` and merge with `data/processed/{dataset_id}_geometric.json` on `dataset_id`.
  - Compute VIF for predictors; if any VIF ≥ 5, set `collinearity_passed = false`, abort the model, and record the flag (SC-005).
  - If >1 dataset with fidelity results: fit the mixed-effects model `fidelity ~ method + (1|dataset)` (`statsmodels.MixedLM`) and report the likelihood-ratio p-value for the `method` fixed effect. If exactly 1 dataset: fit fixed-effects ANOVA `fidelity ~ method` (descriptive case-study mode per plan); if <3 observations per method, set `is_descriptive_mode = true` with null coefficients (per `model_output_schema.schema.yaml`). If residuals fail Shapiro-Wilk (p < 0.05), fall back to Kruskal-Wallis and note it.
  - Apply Benjamini-Hochberg FDR correction (α = 0.05) to all p-values.
  - Write `results/statistical_result.json` conforming to `specs/001-statistical-evaluation-of-dimensionality/contracts/statistical_result.schema.yaml` (model_summary with fixed_effects incl. `p_value_fdr`, vif_values, collinearity_passed; sensitivity_analysis placeholder; execution_metadata placeholder).
  - Output: `results/statistical_result.json`.
  - Verification: JSON parses and validates against the schema; `collinearity_passed` is boolean; `fixed_effects` entries have `term`, `estimate`, `std_error`, `p_value`, `p_value_fdr`; descriptive mode flagged when applicable.

- [ ] T008 [US3] Implement `code/sensitivity.py`: Leiden-resolution sweep and Silhouette-threshold sweep with stability verdict (FR-007, SC-001).
  - For each (dataset, method) pair, recompute ARI/NMI at every Leiden resolution 0.1–1.0 (reusing the sweep from T006 or recomputing deterministically).
  - Silhouette-threshold sweep: for thresholds {0.4, 0.5, 0.6}, retain only clusters whose Silhouette Score ≥ threshold, recompute ARI/NMI, and record the variance across the three thresholds (spec FR-007).
  - Compute `variance_ari` and `variance_nmi` (across resolutions and thresholds as specified) and `stability_passed = (variance_ari < 0.05) AND (variance_nmi < 0.05)` (SC-001).
  - Write `results/sensitivity_analysis.json` with `leiden_resolutions`, `silhouette_thresholds`, `variance_ari`, `variance_nmi`, `stability_passed`.
  - Plot `figures/sensitivity_plot.png`: ARI/NMI vs Leiden resolution per method, subplots per dataset.
  - Output: `results/sensitivity_analysis.json`, `figures/sensitivity_analysis_data.csv` (long-form sweep table), `figures/sensitivity_plot.png`.
  - Verification: JSON parses with numeric variances and boolean `stability_passed`; the CSV has one row per (dataset, method, resolution) with ARI/NMI values; the PNG is a readable image with axis labels and a legend.

- [ ] T009 [US1] Implement `code/aggregate.py` and `code/main.py`: full orchestration, execution metadata, and budget enforcement.
  - `code/aggregate.py`: read `data/metrics/fidelity_results.csv`, geometric JSONs, `results/statistical_result.json`, `results/sensitivity_analysis.json`, `results/monitoring.csv`; compute `peak_memory_bytes` (max), `total_runtime_seconds` (sum), `datasets_processed`, `datasets_skipped` (from `data/manifest.json`), `exit_code`; fill `execution_metadata` in `results/statistical_result.json`; write `data/results/combined_metrics.parquet` with columns `dataset_id`, `method`, `ari`, `nmi`, `silhouette_score`, `optimal_resolution`, `trustworthiness`, `local_continuity`, `runtime_seconds`, `peak_ram_gb` (conforming to `metrics_schema.schema.yaml` semantics).
  - `code/main.py`: CLI with `--config` and optional `--phase`; calls data-gap resolution → download → preprocess → embeddings → clustering/metrics → stats → sensitivity → aggregate in order; wraps phases in try/except logging to `results/run_log.txt`, aborting on the critical no-data condition; on completion calls `assert_budgets` (SC-003/SC-004) and prints a summary (datasets processed, mean ARI/NMI by method, method-effect p-value); exits 0 on success, 1 on critical failure.
  - Output: `code/main.py`, `code/aggregate.py`, updated `results/statistical_result.json`, `data/results/combined_metrics.parquet`, `results/run_log.txt`.
  - Verification: `python code/main.py --config code/config.py` completes with exit code 0 (or exits 1 with a clear no-data summary if no real sources resolve); `execution_metadata` contains all five required fields; `pandas.read_parquet('data/results/combined_metrics.parquet')` returns the expected columns with values in valid ranges.

- [ ] T010 [US1] Add focused correctness tests for preprocessing, clustering, and fidelity computation.
  - `code/tests/test_preprocessing.py`: log-CPM yields non-negative values and per-cell CPM sums ≈ 1e6 pre-log; HVG selection retains a recorded, positive gene count; sampling yields exactly 5000 cells when input > 10,000; geometric descriptors are floats in [0,1] on a small REAL-derived fixture (e.g., a fixed row-subset of a downloaded matrix saved under `data/results/test_fixture.parquet` — never synthetic random data standing in for measurements).
  - `code/tests/test_clustering.py`: Leiden labels are non-negative integers; Silhouette ∈ [-1,1]; ARI/NMI match hand-computed values on a small labeled example (e.g., ARI of identical labelings = 1.0, of random vs fixed ≠ 1); different resolutions can yield different cluster counts.
  - `code/tests/test_utils.py`: `parse_time_output` correctly parses a sample `/usr/bin/time -v` string; `ResourceMonitor.run` writes a monitoring row; budget assertion fires on an artificially small limit.
  - Output: `code/tests/test_preprocessing.py`, `code/tests/test_clustering.py`, `code/tests/test_utils.py`.
  - Verification: `python -m pytest code/tests/ -v` runs and all tests pass; no test fabricates input data via `random.*` standing in for real measurements.

- [ ] T011 [US1] Run the complete pipeline on the real data and validate every output against the specification.
  - Execute `python code/main.py --config code/config.py` end-to-end on all available datasets (1–3 depending on Phase 0 resolution).
  - Confirm all artifacts exist and are non-empty: `data/processed/*`, `data/embeddings/*`, `data/clustering/*`, `data/metrics/fidelity_results.csv`, `results/statistical_result.json`, `results/sensitivity_analysis.json`, `data/results/combined_metrics.parquet`, `figures/sensitivity_plot.png`, `results/monitoring.csv`.
  - Confirm ranges: ARI/NMI ∈ [0,1] (or `"Unavailable"`), Silhouette ∈ [-1,1], geometric descriptors ∈ [0,1] or null; `execution_metadata.peak_memory_bytes` ≤ 7,000,000,000 (SC-003) and `total_runtime_seconds` ≤ 21,600 (SC-004); `model_summary.collinearity_passed` true or documented (SC-005); FDR-adjusted p-values present (SC-002); `stability_passed` verdict present (SC-001).
  - Output: all run artifacts plus `results/validation_report.txt` recording each check and its pass/fail outcome with actual measured values.
  - Verification: `python -c "import pandas; df=pandas.read_parquet('data/results/combined_metrics.parquet'); print(df.shape, df.columns.tolist())"` succeeds; `results/validation_report.txt` lists every SC-001–SC-005 check with actual values and pass/fail; no fabricated or placeholder metrics anywhere in `data/` or `results/`.

## Phase 3: Reproducible results and paper handoff

- [ ] T012 [US1] Write the methods/results account and reproducibility documentation, including the honest data-availability and scope statement.
  - Create `paper/summary.md` with Methods, Results, and Limitations sections, all numbers pulled programmatically from `data/results/combined_metrics.parquet`, `results/statistical_result.json`, `results/sensitivity_analysis.json`, and `data/manifest.json` (mean/std ARI and NMI by method, method-effect p-value with FDR, VIF values, stability verdict, per-dataset availability). Reference `figures/sensitivity_plot.png` inline.
  - Limitations must state honestly: how many of the three required datasets resolved to real raw counts; that with ≤3 datasets the mixed-effects model is descriptive/not generalizable (plan Constitution note); any skipped datasets, collinearity warnings, or normality violations; the sampling rule (5000 cells when >10,000) and its representativeness limitation.
  - Create `paper/REPRODUCIBILITY.md`: declared seed (42), verified source URLs from `data/manifest.json`, exact package versions from `code/requirements.txt`, step-by-step re-run instructions, and the runtime/memory assertion checks.
  - Update `plan.md`'s Tasks Overview only if execution revealed an inconsistency between the documented statistical mode (mixed-effects vs fixed-effects descriptive) and what the available data supported — resolving the prior T049 rejection by recording which mode actually ran and why.
  - Document the paper-stage handoff: required figures (sensitivity plot, embedding scatter plots), tables (fidelity by method, model coefficients), and the limitations statement — PDF compilation and publication belong to the paper pipeline.
  - Output: `paper/summary.md`, `paper/REPRODUCIBILITY.md`, updated `plan.md` (if needed).
  - Verification: `pandoc paper/summary.md -o paper/summary.html` succeeds and the HTML contains the statistics tables and image reference; every numeric claim in `summary.md` traces to an artifact in `data/` or `results/` (no hand-typed results); `paper/REPRODUCIBILITY.md` contains seed, URLs, versions, and re-run steps.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command / artifact |
|---|---|---|
| FR-001 (download & preprocess ≥1 real dataset) | T003, T004 | `data/manifest.json` + `data/processed/*_matrix.parquet` |
| FR-002 (Trustworthiness, k=15) | T004 | `data/processed/*_geometric.json` `trustworthiness` |
| FR-003 (Local continuity, k=15) | T004 | `data/processed/*_geometric.json` `local_continuity` |
| FR-004 (PCA/t-SNE/UMAP, fixed hyperparameters) | T005 | `data/embeddings/*.csv` |
| FR-005 (ARI/NMI vs ground truth) | T006 | `data/metrics/fidelity_results.csv` |
| FR-006 (mixed-effects / conditional ANOVA) | T007 | `results/statistical_result.json` |
| FR-007 (Silhouette-threshold sweep {0.4,0.5,0.6}) | T008 | `results/sensitivity_analysis.json` |
| FR-008 (Benjamini-Hochberg) | T007 | `p_value_fdr` fields |
| SC-001 (variance < 0.05) | T008 | `stability_passed` |
| SC-002 (FDR p < 0.05) | T007 | FDR-adjusted p-value |
| SC-003 (peak RSS ≤ 7 GB) | T002, T009, T011 | `execution_metadata.peak_memory_bytes` |
| SC-004 (runtime ≤ 21,600 s) | T002, T009, T011 | `execution_metadata.total_runtime_seconds` |
| SC-005 (VIF < 5) | T007 | `collinearity_passed` |

Execution order: T001–T002 (setup) → T003 (data gap, blocking) → T004 → T005 → T006 (first end-to-end fidelity result) → T007, T008 (parallel after T006) → T009 → T010 → T011 → T012. Data-flow rule: no task consumes `data/results/` or `results/` artifacts before the task that produces them.

## Revision behavior

Prior rejected items are addressed as follows: T001 (directory proof) — directories are created via `llmxive_toolkit.paths` in T001 with an explicit `ls` verification; T029/T021 (truncated `utils.py`, missing `monitoring.csv`) — consolidated into T002 with a runnable self-test that produces the CSV; T054/T028 (missing Snakemake rules) — Snakemake is dropped in favor of the plain-Python orchestrator `code/main.py` (T009), which implements the same pre-download availability gate and resource aggregation; T030/T032 (CI workflow) — platform-owned CI is not tasked; budget enforcement (SC-003/SC-004) is implemented in-project via `assert_budgets` (T002) and validated in T011; T049 (plan consistency) — folded into T012 with an explicit conditional update. No synthetic data fallback exists anywhere: a failed real fetch raises (T003).

*End of tasks.md*
