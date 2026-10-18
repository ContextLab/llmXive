# Tasks: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

**Inputs**: `spec.md`, `plan.md`, `contracts/`, `data-model.md`, reviewer feedback, existing code artifacts.

The tasks are organized into research phases. Each task follows the canonical checklist format  
`- [ ] T### [P?] [USx?] description … with file path`.  
Verification steps are listed as indented continuation lines. All paths are relative to the project root and reside under `code/`, `data/`, `figures/`, or `specs/`.

---

## Phase 0 – Data acquisition, preprocessing, and methodological alignment

- [ ] T001 [P1] [US-1] Implement a fail‑loudly streaming data loader for the verified BICCN Human MTG dataset and auxiliary GEO/BrainSpan metadata.  
  - **File**: `code/data_pipeline/setup_data.py`  
  - **Steps**:  
    • Stream `https://huggingface.co/datasets/BICCN/human_mtg_scRNA` via `datasets.load_dataset(..., streaming=True)`.  
    • Download GEO accession **GSE123456** (human brain development bulk RNA‑seq) and BrainSpan developmental‑stage metadata via their public REST APIs.  
    • Raise on any fetch or parsing error; **no synthetic fallback**.  
    • If the full atlas exceeds ~7 GB RAM, process it in chunks and retain a deterministic stratified sample of the first 5 000 cells per developmental stage (seed = 42).  
    • Write SHA‑256 checksums of all raw files to `data/raw/checksums.txt`.  
    • Document the runnable command in `specs/001-quantitative-analysis-of-gene-expression/quickstart.md` (e.g., `python code/data_pipeline/setup_data.py --seed 42`).  
  - **Verification**:  
    • Running the command exits with status 0.  
    • `data/raw/checksums.txt` exists and matches re‑downloaded files.  
    • Log reports the total number of cells streamed and the stratified sample size per stage.

- [ ] T002 [P1] [US-1] Implement preprocessing, integration, and stage‑keyed window definition.  
  - **File**: `code/data_pipeline/preprocess.py`  
  - **Steps**:  
    • QC: filter cells with <200 genes, genes expressed in <3 cells, and >5 % mitochondrial reads.  
    • Log‑normalize counts, select top 2 000 highly variable genes, and apply Harmony batch correction across donors.  
    • Define developmental windows directly from the `developmental_stage` annotation (e.g., “Fetal 12‑16w”). Require ≥ 10 cells per window; abort if two consecutive windows fall below this threshold, otherwise linearly interpolate missing metadata.  
    • Compute LISI on the Harmony‑corrected PCA embedding; abort with clear error if LISI < 1.2 (FR‑012).  
    • Within each developmental window, compute lineage‑specific pseudotime (Slingshot/DPT) **only** for ordering cells *inside* that window. Validate pseudotime against marker genes (NEUROD6, GFAP, MAP2) with Pearson r ≥ 0.6 per lineage; halt on failure.  
    • Write the integrated AnnData object to `data/processed/integrated_atlas.h5ad`.  
    • Generate `data/processed/qc_report.txt` containing: cell‑retention rate, LISI score, per‑stage variance explained, and marker‑correlation values.  
  - **Verification**:  
    • `pytest code/tests/test_preprocess.py` passes.  
    • Output AnnData conforms to `contracts/dataset.schema.yaml`.  
    • Retained cells ≥ 50 000 (SC‑001).  
    • LISI ≥ 1.2 (SC‑008).  
    • Developmental‑stage variance explained ↑ ≥ 20 % vs. pre‑integration (SC‑002).

- [ ] T003 [P1] [US‑0] Update internal documentation to reflect compliance with FR‑003 without altering the specification text.  
  - **Files**: `specs/001-quantitative-analysis-of-gene-expression/research.md`, `plan.md`  
  - **Steps**:  
    • Add a “Methodology compliance” section noting that GRN inference will be performed using a true sliding‑window pseudotime approach as required by FR‑003 and Constitution Principle VI.  
    • Ensure no changes are made to `spec.md` wording.  
  - **Verification**:  
    • Diff shows added documentation only; `spec.md` unchanged.  
    • No remaining mentions of “stage‑only windows” as the sole GRN inference method.

---

## Phase 1 – Thin end‑to‑end sanity check

- [ ] T004 [P1] [US‑2] Execute a thin analysis on a stratified 5 000‑cell subsample to verify the full pipeline runs end‑to‑end.  
  - **File**: `code/run_thin_analysis.py` (or invoke `python -m code.thin_pipeline`).  
  - **Steps**:  
    • Load the subsample produced by T001/T002.  
    • For each of 3‑5 developmental windows, run GRNBoost2 (via `arboreto`) to infer a network.  
    • Compute z‑score‑normalized edge‑weight deltas between adjacent windows and hub‑stability scores.  
    • Map a real schizophrenia GWAS risk‑gene list (EBI GWAS Catalog) onto the rewired hubs and perform a single hypergeometric test with **100** permutations (thin‑slice exception).  
    • Output `data/results/thin_results.json` containing: network snapshots, rewiring events, enrichment statistic, and the sampling rule used.  
  - **Verification**:  
    • JSON contains ≥ 1 rewiring event with non‑zero `weight_delta`.  
    • Enrichment p‑value field is present and numeric.  
    • The script exits with status 0 and logs the exact number of cells processed.

---

## Phase 2 – Full‑scale analysis and validation

- [ ] T005 [P2] [US‑2] Perform full‑scale GRN inference using **overlapping sliding‑window pseudotime** across the entire trajectory.  
  - **File**: `code/network_inference/infer_grn.py`  
  - **Steps**:  
    • Order all cells in the integrated atlas (`integrated_atlas.h5ad`) by global pseudotime (computed in T002).  
    • Define overlapping windows of width = 10 % of the pseudotime range with step = 5 % (adjustable via `--window-size` and `--step`).  
    • For each window, run GRNBoost2 on the cells within that window.  
    • Apply pySCENIC motif enrichment; retain only TF‑target edges with cis‑regulatory motif support.  
    • Define hubs as TFs with degree ≥ 10, or the top‑20 TFs by degree if fewer meet the threshold.  
    • Write each window’s network to `data/processed/networks/{window_id}.json` and the motif‑filtered version to `data/processed/networks_motif/{window_id}.json`.  
    • Summarize motif validation in `data/processed/motif_report.txt`.  
  - **Verification**:  
    • Each JSON contains ≥ 100 edges.  
    • `motif_report.txt` lists ≥ 10 validated TF‑target pairs.  
    • Integrated cell count remains ≥ 50 000 (SC‑001).  

- [ ] T006 [P2] [US‑2] Detect rewiring events and conduct a sensitivity sweep over edge‑weight thresholds.  
  - **File**: `code/network_inference/rewiring.py`  
  - **Steps**:  
    • Z‑score normalize edge weights within each window.  
    • For every pair of adjacent windows, compute `weight_delta` for shared edges and hub‑stability (Jaccard of target sets).  
    • Sweep the rewiring significance threshold over {0.01, 0.05, 0.1}; record events per threshold.  
    • Write the consolidated list to `data/processed/rewiring_events.csv` (columns: `event_id, tf, window_a, window_b, weight_delta_z, stability_score, threshold`).  
    • Produce `data/processed/sensitivity_report.txt` summarizing event counts and the Jaccard similarity of the top‑20 events across thresholds.  
  - **Verification**:  
    • Jaccard similarity of the top‑20 events across thresholds ≥ 0.8 (SC‑005).  
    • At least 5 TFs meet the significance criterion (Δ > threshold & stability p ≤ 0.05).  

- [ ] T007 [P2] [US‑3] Map GWAS risk genes to rewired hubs and perform matched‑background hypergeometric enrichment.  
  - **File**: `code/clinical_analysis/enrichment.py`  
  - **Steps**:  
    • Retrieve risk‑gene sets for 3–5 neurological disorders (e.g., schizophrenia, autism, epilepsy) from the EBI GWAS Catalog API; abort on fetch failure.  
    • For each disorder, construct a matched background gene set (matched on gene length, median expression in the atlas, and network degree; tolerance ± 5 %; background size = 10 × risk‑gene count). Document the matching procedure in `data/processed/background_match_report.txt`.  
    • Perform hypergeometric enrichment of risk genes within the set of rewired hub TFs per developmental window.  
    • Apply Benjamini‑Hochberg FDR correction across all disorder‑window tests.  
    • Write results to `data/processed/disorder_enrichment.csv` (columns: `disorder, vulnerability_window, odds_ratio, p_value_raw, p_value_fdr, is_significant`).  
  - **Verification**:  
    • CSV contains at least one disorder‑window pair with `odds_ratio` ≥ 1.5 **and** `p_value_fdr` ≤ 0.05 (SC‑004).  
    • `background_match_report.txt` exists and records matching statistics.  

- [ ] T008 [P2] [US‑3] Conduct ≥ 5 000 degree‑preserving permutation tests to obtain empirical p‑values for the enrichments.  
  - **File**: `code/clinical_analysis/permutation_test.py`  
  - **Steps**:  
    • For each disorder, generate 5 000 network permutations that preserve node degree (using the `networkx.double_edge_swap` method).  
    • Re‑compute enrichment on each permuted network; record the number of permutations with a statistic ≥ the observed.  
    • Report empirical p = k/5 000; if k = 0, report `"p < 1/5000"` per FR‑013.  
    • Apply BH FDR correction to the empirical p‑values.  
    • Store results in `data/results/permutation_results.json` (include `empirical_p`, `fdr_corrected_p`, and a `power_estimate` field).  
  - **Verification**:  
    • At least one disorder shows empirical p ≤ 0.05 (SC‑003).  
    • `power_estimate` ≥ 0.8.  
    • All p‑values are correctly formatted (raw numeric or `"p < 1/5000"`).  

- [ ] T009 [P2] [US‑3] Independent validation using an external scRNA‑seq cohort and bulk RNA‑seq time‑course, including odds‑ratio consistency check.  
  - **File**: `code/clinical_analysis/validation.py`  
  - **Steps**:  
    • Download GEO accession **GSE158762** (human cortical development scRNA‑seq) via `datasets.load_dataset`; verify with SHA‑256 checksums stored in `data/raw/independent_checksums.txt`.  
    • Re‑run the full GRN inference (T005) and rewiring detection (T006) on this independent atlas.  
    • Compute Jaccard similarity of the top‑20 rewired TFs between primary and independent results; require ≥ 0.5.  
    • Perform the same GWAS enrichment pipeline (T007/T008) on the independent dataset to obtain odds ratios per disorder‑window.  
    • Compare odds ratios to those from the primary analysis; require that for any replicated disorder the independent odds ratio is ≥ 1.1 times the primary odds ratio (i.e., consistent direction and magnitude).  
    • Download BrainSpan bulk RNA‑seq developmental time‑course (verified URL). Compute Spearman correlation of expression trajectories of the primary‑study rewired‑hub TFs versus the bulk data; require ρ ≥ 0.6 and nominal p ≤ 0.1.  
    • Write `data/results/validation_metrics.json` containing `topological_validation_jaccard`, `expression_validation_spearman`, `odds_ratio_consistency_pass` (boolean), and associated p‑values.  
  - **Verification**:  
    • Both Jaccard and Spearman criteria are met.  
    • Odds‑ratio consistency flag is true (≥ 1.1 ratio) for at least one disorder.  
    • Checksums files exist and match the downloaded data.  

- [ ] T010 [P3] [US‑2, US‑3] Generate final visualizations and a summary table.  
  - **Files**: `code/visualization/plot_networks.py`, `code/visualization/plot_enrichment.py`  
  - **Steps**:  
    • Create interactive Plotly node‑link diagrams for 2–3 key developmental windows; color nodes by hub‑stability and edges by `weight_delta_z`. Save as `figures/network_topology.html`.  
    • Produce a heatmap of disorder enrichment odds ratios across windows, marking significance (FDR ≤ 0.05); save as `figures/enrichment_heatmap.html`.  
    • Assemble `data/results/final_summary.csv` with columns `disorder, vulnerability_window, odds_ratio, p_value_fdr, empirical_p, is_validated, validation_cohort_id, interpretation`. Ensure all values respect associational language only (FR‑008).  
  - **Verification**:  
    • HTML files open and display interactive plots.  
    • CSV contains ≥ 3 disorders with complete fields and meets SC‑004 thresholds.  

- [ ] T011 [P3] [US‑1, US‑2, US‑3] Write the methods and results manuscript draft and perform a full reproducibility run.  
  - **File**: `specs/001-quantitative-analysis-of-gene-expression/research.md`  
  - **Steps**:  
    • Document every data source (BICCN, GEO GSE123456, BrainSpan, GWAS Catalog, independent cohort) with URLs, version tags, and checksum verification.  
    • Explicitly describe the sliding‑window pseudotime design, GRNBoost2 + pySCENIC pipeline, z‑score normalization, rewiring detection, matched‑background enrichment, permutation testing, and independent validation including odds‑ratio consistency.  
    • Cite all verification artifacts (e.g., `integrated_atlas.h5ad`, `rewiring_events.csv`, `disorder_enrichment.csv`, `validation_metrics.json`).  
    • Re‑run the entire pipeline from the command in `quickstart.md` on a fresh environment, confirming deterministic outputs with `--seed 42`.  
    • Run the full pytest suite (`pytest code/tests/`) and ensure all tests pass.  
    • Include a “Limitations” subsection that mentions observational nature, window‑coverage gaps, and the fact that causality is not claimed.  
  - **Verification**:  
    • All sections are present and cross‑referenced to concrete artifact rows.  
    • A clean run reproduces identical file hashes (checked via the platform’s state hashing).  
    • `pytest` exits with 0 and reports all tests passing.  

- [ ] T012 [P2] [US‑2] Compute empirical p‑values for rewiring events via permutation testing.  
  - **File**: `code/network_inference/rewiring_permutation.py`  
  - **Steps**:  
    • For each pair of adjacent windows, generate 5 000 degree‑preserving permutations of the edge set (using `networkx.double_edge_swap`).  
    • For each permutation, recompute `weight_delta_z` for shared edges and record the maximum absolute delta.  
    • Compare the observed `weight_delta_z` to the null distribution to obtain an empirical p‑value (k/5 000). If k = 0, report `"p < 1/5000"` per FR‑013.  
    • Append a column `empirical_p` to `data/processed/rewiring_events.csv`.  
    • Apply Benjamini‑Hochberg FDR correction across all rewiring event tests and add `p_value_fdr`.  
  - **Verification**:  
    • At least one rewiring event achieves empirical p ≤ 0.05 (satisfying SC‑003).  
    • All p‑values correctly formatted; FDR column present.  

---

### Dependency & requirement coverage table

| Requirement | Task(s) | Artifact(s) | Order |
|-------------|---------|--------------|-------|
| FR‑001, FR‑011 | T001, T002 | `data/raw/*`, `integrated_atlas.h5ad` | 0 |
| FR‑002, FR‑012 | T002 | `qc_report.txt` (LISI) | 0 |
| FR‑003 (sliding‑window) | T005, T012 | `networks/*.json`, `rewiring_events.csv` | 1 |
| FR‑004, FR‑010 | T006 | `rewiring_events.csv`, `sensitivity_report.txt` | 1 |
| FR‑005, FR‑009, FR‑013 | T007, T008 | `disorder_enrichment.csv`, `permutation_results.json` | 2 |
| FR‑014, SC‑006 | T009 | `validation_metrics.json` | 2 |
| FR‑007, FR‑008 | T010 | figures, `final_summary.csv` | 3 |
| All FR | T011 | `research.md`, full rerun, test suite | 4 |

**Compute feasibility**: All tasks are CPU‑tractable; streaming keeps memory ≤ 7 GB, and the 5 000 permutation steps fit within the 6‑hour free‑runner limit on 2 cores. No GPU resources are required.

--- 

*End of `tasks.md`.*  