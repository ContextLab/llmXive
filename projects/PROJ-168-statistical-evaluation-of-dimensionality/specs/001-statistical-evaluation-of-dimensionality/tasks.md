# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data  

**Inputs**: `spec.md`, `plan.md`, `data‑model`, `contracts`, `reviewer feedback`.  
All tasks are expressed as plain‑text checklist items; each unchecked box (`- [ ]`) represents work that must produce a real, verifiable artifact under a project‑owned path (`data/`, `figures/`, `code/`, `paper/`).  

---  

## Phase 0 – Project Foundations & Specification Alignment  

- [~] T001 **[US1]** Initialise project directory layout and produce a verifiable listing.  
  - Create directories: `data/raw/`, `data/processed/`, `data/embeddings/`, `data/clustering/`, `data/metrics/`, `data/results/`, `figures/`, `code/`, `code/tests/`, `paper/`.  
  - Generate `results/dir_listing.txt` via `find data code results figures paper -type d > results/dir_listing.txt`.  
  - **Verification**: `assert pathlib.Path('results/dir_listing.txt').exists()` and the file contains each of the directories listed above.  

- [~] T003 **[US1]** Provide utility documentation (`code/ci_workflow_doc.md`).  
  - Write a markdown file describing the CI limits checker (`code/ci_limits.py`) and reference it from `README.md`.  
  - **Verification**: `grep -i "ci_limits.py" code/ci_workflow_doc.md` returns a match, `grep -i "ci_workflow_doc.md" README.md` returns a match, and both files appear in `results/dir_listing.txt`.  
  - *Note*: No files are written outside project‑owned directories (the previous .github path has been removed).  

- [~] T004 **[US1]** Implement CI limits checker (`code/ci_limits.py`).  
  - Reads `results/monitoring.csv`, exits 1 if `peak_ram_bytes` > 7 000 000 000 or total `wall_time_s` > 21 600, otherwise exits 0 with a success message.  
  - **Verification**: Running the script on a deliberately violating CSV returns exit code 1; on a compliant CSV returns 0.  

- [~] T006 **[US1]** Create a full Snakemake workflow (`code/Snakefile`).  
  - Implements rules: `verify_data_availability`, `download`, `preprocess`, `geometry`, `embed`, `cluster_fidelity`, `mixed_effects`, `sensitivity`, `aggregate_report`, `final_handoff`.  
  - `verify_data_availability` aborts with “All datasets unavailable – aborting.” if every entry in `data/manifest.json` is `"Unavailable"`.  
  - **Verification**: `snakemake -n -s code/Snakefile verify_data_availability` prints abort message when appropriate; `snakemake -p -s code/Snakefile --dag | dot -Tpng -o dag.png` shows the full DAG.  

- [~] T007 **[FR‑001]** Resolve dataset availability (`code/data_gap_resolver.py`).  
  - Iterate over GEO accessions GSE131907, GSE111322, GSE150728 (or documented open substitutes per amendment).  
  - Download via `datasets.load_dataset("geo", name=accession, split="train", streaming=False)`.  
  - Compute SHA‑256, write raw file to `data/raw/<accession>.h5ad`, and record fields `dataset_id`, `source_url`, `status`, `checksum`, `raw_file_path`, `processed_file_path` (null) in `data/manifest.json`.  
  - If fewer than three datasets are `"Available"`, write `results/data_gap_summary.txt` and exit 1.  
  - **Verification**: `python -m jsonschema -i data/manifest.json specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/dataset.schema.yaml` exits 0; when < 3 available, `cat results/data_gap_summary.txt` contains “abort”.  

- [~] T008 **[FR‑002 FR‑003 US1]** Pre‑process each available dataset and compute geometry (`code/preprocess_and_geometry.py`).
  - For each `"Available"` entry in `data/manifest.json`:  
    1. Load raw matrix with Scanpy (`sc.read_h5ad`).  
    2. Export ground‑truth labels to `data/processed/<dataset_id>_labels.csv`.  
    3. Perform log‑CPM transformation.  
    4. Select highly‑variable genes (Seurat‑flavor) and record N in `data/processed/<dataset_id>_hvg.txt`.  
    5. If cell count > 10 000, deterministically subsample 5 000 cells using `np.random.default_rng(42)`.  
    6. Compute **global intrinsic dimensionality** (Levina‑Bickel, k = 15, 10 000 unordered cell‑pair samples, seed = 42).  
    7. Compute **local density** (average 15‑NN distance, same sampling).  
    8. Write processed matrix to `data/processed/<dataset_id>_matrix.parquet` and descriptors to `data/processed/<dataset_id>_geometric.json`.  
    9. **Verification**:  
        - JSON contains keys `intrinsic_dimensionality` and `local_density`.  
        - Additionally checks that the sampling used `seed=42`, `pair_count=10000` (or all possible pairs if fewer) and that `k=15` was used.  
        - Fails loudly if any parameter deviates.  
    10. Wrap the routine with `ResourceMonitor.run(f"preprocess_{dataset_id}", ...)`.  

- [ ] T009 **[FR‑004 US1]** Generate PCA, t‑SNE, and UMAP embeddings (`code/generate_embeddings.py`).   <!-- FAILED-IN-EXECUTION: code/generate_embeddings.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/generate_embeddings.py exit=1 -->
  - Load `data/processed/<dataset_id>_matrix.parquet`.  
  - **PCA**: `sklearn.decomposition.PCA(n_components=30, random_state=42)` → save `data/embeddings/<dataset_id>_PCA.csv` (columns: `cell_id,PC1,…,PC30`).  
  - **t‑SNE**: `sklearn.manifold.TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=42)` → save `data/embeddings/<dataset_id>_tSNE.csv`.  
  - **UMAP**: `umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=42)` → save `data/embeddings/<dataset_id>_UMAP.csv`.  
  - **Verification**: CSV row count matches processed matrix rows; PCA CSV has 31 columns, t‑SNE/UMAP have 3; no NaNs; `results/monitoring.csv` contains `embed_PCA_<dataset_id>`, `embed_tSNE_<dataset_id>`, `embed_UMAP_<dataset_id>`.  

- [ ] T010 **[FR‑005 US2]** Perform Leiden clustering, generate embeddings (if needed), and compute native ARI/NMI (`code/cluster_and_fidelity_selfcontained.py`).  
  - For each dataset **and** method (PCA, t‑SNE, UMAP):  
    1. **Embedding Generation (self‑contained)** – if the embedding file does not already exist, run the same code as T009 to create it.  
    2. Build a k‑NN graph (`n_neighbors=15`).  
    3. Sweep resolutions 0.1–1.0 (step 0.1), compute `silhouette_score` for each, select the resolution with maximal silhouette.  
    4. If clustering fails twice, abort the pipeline (no “Unavailable” rows).  
    5. Save `data/clustering/<dataset_id>_<method>_clusters.csv` (`cell_id,cluster_label,silhouette_score,optimal_resolution`).  
    6. Join with ground‑truth labels and compute **Adjusted Rand Index** and **Normalized Mutual Information** (both in native 0‑1 range, **no transformation**).  
    7. Append rows to `data/metrics/fidelity_results.csv` with columns `embedding_id,method,dataset_id,ari,nmi,silhouette_score,optimal_resolution`.  
    8. **Verification**: After writing, script asserts that every row has non‑null `ari` and `nmi`; if any are missing, the script exits with a non‑zero code, causing the pipeline to fail (fulfills SC‑006). Schema validation against `fidelity_results.schema.yaml` passes.  

- [ ] T016 **[SC‑006]** Validate completeness of fidelity results.  
  - Load `data/metrics/fidelity_results.csv` and assert that no row has missing (`null`/empty) `ari` or `nmi`. Abort with clear error if any are missing.  
  - **Verification**: Script exits 0 only when all entries are present; otherwise non‑zero exit code.  

- [ ] T017 **[FR‑001 contract]** Validate raw dataset files against `dataset_schema.schema.yaml`.  
  - After each download in T007, run `python -m jsonschema -i data/raw/<dataset_id>.json specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/dataset_schema.schema.yaml`.  
  - **Verification**: Exit 0 on success; any schema violation aborts the pipeline.  

- [ ] T018 **[FR‑005 contract]** Convert fidelity CSV to `metrics.schema.yaml` YAML and validate.  
  - Read `data/metrics/fidelity_results.csv`, produce `data/metrics/fidelity_metrics.yaml` adhering to `metrics.schema.yaml`.  
  - Run `python -m jsonschema -i data/metrics/fidelity_metrics.yaml specs/001‑statistical‑evaluation‑of‑dimensionality/contracts/metrics.schema.yaml`.  
  - **Verification**: Schema validation passes; file exists.  

- [ ] T019 **[FR‑004 contract]** Assemble embedding‑metrics YAML (`metrics_schema.schema.yaml`).  
  - For each dataset‑method pair, combine geometric descriptors (intrinsic dimensionality, local density), embedding runtime (`runtime_seconds`), and peak RAM (`peak_ram_gb`) into `data/metrics/<dataset_id>_<method>_embedding_metrics.yaml`.  
  - Validate each file against `metrics_schema.schema.yaml`.  
  - **Verification**: All YAML files pass schema validation.  

- [ ] T020 **[FR‑006 contract]** Write mixed‑effects model output to `model_output_schema.schema.yaml`.  
  - After model fitting in T011 (or descriptive fallback), produce `data/results/model_output.yaml` conforming to `model_output_schema.schema.yaml`.  
  - Validate with jsonschema.  
  - **Verification**: Schema validation succeeds.  

- [ ] T021 **[spec‑amendment]** Record formal amendment for dataset substitution.  
  - Append a markdown amendment to `specs/001‑statistical‑evaluation‑of‑dimensionality/spec.md` documenting the use of open substitute datasets and the justification.  
  - **Verification**: The amendment section exists and includes a timestamp.  

## Phase 1 – Snakemake Orchestration & Data‑Gap Resolution (covered by T006‑T007)  

---  

## Phase 2 – Ingestion, Pre‑processing & Geometric Diagnostics (covered by T008)  

---  

## Phase 3 – Embedding Generation (covered by T009)  

---  

## Phase 4 – Clustering & Fidelity Evaluation (covered by T010, T016)  

---  

## Phase 5 – Mixed‑Effects Modeling & Multiple‑Testing  

- [ ] T011 **[FR‑006 FR‑008 SC‑002 SC‑005 US3]** Fit mixed‑effects model (self‑contained).  
  - **Self‑contained preprocessing**: runs the same geometry computation as T008 for each dataset.  
  - **Self‑contained fidelity**: runs the full clustering & fidelity pipeline as in T010, guaranteeing required metrics are present.  
  - Load the combined metrics, require at least two datasets with valid rows; otherwise abort with `results/model_abort.txt`.  
  - Fit `logit_fidelity ~ method + intrinsic_dimensionality + local_density + (1|dataset)` using `statsmodels.MixedLM`.  
  - If the model fails to converge, switch to descriptive mode (`is_descriptive_mode:true`) and record only summary statistics.  
  - Compute VIF for fixed effects; abort if any VIF ≥ 5.  
  - Perform Shapiro‑Wilk on residuals; log warning if p < 0.05.  
  - Apply Benjamini‑Hochberg to all p‑values.  
  - Write `results/statistical_result.yaml` (conforms to `statistical_result.schema.yaml`) and also `data/results/model_output.yaml` (via T020).  
  - **Verification**: Schema validation passes; `collinearity_passed` true; `is_descriptive_mode` correctly set.  

---  

## Phase 6 – Sensitivity Sweep & Plotting  

- [ ] T012 **[FR‑007 SC‑001 US3]** Sweep silhouette thresholds and report stability.  
  - For each embedding, re‑run Leiden clustering at thresholds {0.4, 0.5, 0.6}. Accept only resolutions whose silhouette ≥ threshold.  
  - Record ARI/NMI for each accepted clustering in `figures/sensitivity_data.csv`.  
  - Compute variance of ARI and NMI across the three thresholds and a 95 % bootstrap CI (10 000 resamples).  
  - **Verification**:  
      - JSON `results/sensitivity_analysis.json` contains keys `thresholds`, `variance_ari`, `variance_nmi`, `stability_report`, **and** fields `bootstrap_resamples: 10000` and `confidence_interval` with lower/upper bounds.  
      - PNG file exists and is non‑empty, CSV row count equals `datasets × methods × 3`.  

---  

## Phase 7 – Aggregation, Execution Metadata & Validation Report  

- [ ] T013 **[SC‑003 SC‑004 SC‑005 US1]** Consolidate metrics and produce a validation report (`code/aggregate_and_report.py`).  
  - Join `data/metrics/fidelity_results.csv` with each dataset’s geometric JSON to create `data/results/combined_metrics.parquet`.  
  - Derive `peak_memory_bytes` (max of `peak_ram_bytes`) and `total_runtime_seconds` (sum of `wall_time_s`).  
  - Count processed vs skipped datasets from `data/manifest.json`.  
  - Write `results/validation_report.txt` with PASS/FAIL flags for SC‑001 … SC‑005, inserting computed numeric values.  
  - Embed the `execution_metadata` block into `results/statistical_result.yaml`.  
  - **Verification**: Each `SC‑0xx:` line appears in the report and matches values in `results/statistical_result.yaml`.  

---  

## Phase 8 – Methods & Results Summary, Reproducibility Guide (Paper Hand‑off)  

- [ ] T014 **[US1]** Draft methods/results summary and reproducibility documentation (`paper/summary.md`, `paper/REPRODUCIBILITY.md`).  
  - `summary.md` programmatically pulls numbers from `data/results/combined_metrics.parquet` and `results/statistical_result.yaml` (mean ARI/NMI per method, VIF values, p‑values, variance statistics, stability verdict, limitations).  
  - `REPRODUCIBILITY.md` lists random seeds, GEO URLs (from manifest), pinned package versions (`code/requirements.txt`), full command `python code/main.py`, and observed SC‑003/SC‑004 metrics.  
  - **Verification**: `pandoc paper/summary.md -o paper/summary.html` succeeds; a grep for any numeric literal from the parquet file finds the same literal in `summary.md`.  

---  

## Phase 9 – Clean Re‑run & Handoff Artifact (Paper Stage)  

- [ ] T015 **[US1]** Perform a clean re‑run and generate handoff hash.  
  - Delete all intermediate artefacts except raw downloads:  
    `rm -rf data/processed data/embeddings data/clustering data/metrics data/results figures results/*.csv results/*.json`.  
  - Execute the full pipeline via `python code/main.py`; ensure exit code 0 (or 1 only if dataset requirement cannot be met).  
  - Run the full test suite `python -m pytest code/tests/ -q`; all tests must pass.  
  - Re‑compute SHA‑256 of `results/statistical_result.yaml` and store it in `paper/HANDOFF_READY.txt` together with an ISO‑8601 timestamp.  
  - Append a “Handoff” subsection to `paper/summary.md` listing downstream artefacts (`data/results/combined_metrics.parquet`, `results/statistical_result.yaml`, `figures/sensitivity_plot.png`, `results/validation_report.txt`).  
  - **Verification**: `sha256sum -c <(echo "<hash>  results/statistical_result.yaml")` succeeds; a second clean run yields the same hash (deterministic seeds guarantee identical output); `paper/HANDOFF_READY.txt` contains a valid hash and timestamp.  

---  

### Dependency Mapping (updated)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 | T007, T008, T017, T021 |
| FR‑002 | T008 |
| FR‑003 | T008 |
| FR‑004 | T009, T019 |
| FR‑005 | T010 |
| FR‑006 | T011, T020 |
| FR‑007 | T012 |
| FR‑008 | T011 |
| SC‑001 | T012 |
| SC‑002 | T011 |
| SC‑003 | T004, T005, T009, T010, T011, T012, T013 |
| SC‑004 | T004, T005, T009, T010, T011, T012, T013 |
| SC‑005 | T011 |
| SC‑006 | T010, T016 |
| US‑1 | T001‑T015 (all) |
| US‑2 | T010 (self‑contained) |
| US‑3 | T011 (self‑contained) |

All tasks respect data‑flow ordering, produce real, verifiable artifacts under project‑owned paths, and now fully cover every contract and success criterion.  


