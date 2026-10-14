# Tasks: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

**Inputs**: `spec.md`, `plan.md`, `dataset.schema.yaml`, `output.schema.yaml`, `data-model.md`.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the pipeline and run a thin, end-to-end analysis on real data to verify the data flow from raw counts to enrichment results.

- [ ] T001 [P1] [US-1] Establish project layout, document execution in `quickstart.md`, and validate raw data provenance.
    - Initialize directories: `code/`, `data/raw/`, `data/processed/`, `figures/`, `tests/`.
    - Document the runnable command in `specs/001-gene-regulation/quickstart.md` specifying the entry point (e.g., `python code/main.py --seed 42`).
    - Implement data hygiene: download the BICCN Human MTG dataset from https://huggingface.co/datasets/BICCN/human_mtg_scRNA using `datasets.load_dataset()` with streaming enabled to fit within 7 GB RAM.
    - Generate SHA-256 checksums for all raw input files upon first download and record them in a `data/raw/checksums.txt` file (Constitution Principle III).
    - Verification: `quickstart.md` is readable and contains a complete, reproducible command; checksums file exists and matches re-downloaded files.

- [ ] T002 [P1] [US-1] Implement data acquisition and preprocessing pipeline producing `data/processed/integrated_atlas.h5ad`.
    - Implement `code/data_pipeline.py` with functions for streaming data loading, quality control (cell and gene filtering), log-normalization, HVG selection (retain top 2,000 genes), and Harmony batch correction.
    - Implement gap detection: scan each developmental stage window for cell count; if any window has < 10 cells, log the gap location and either interpolate using adjacent windows or abort with a clear error message (FR-011, SC-007).
    - Implement LISI score calculation using the `lisi` package; abort the pipeline with a logged error if LISI < 1.2 (FR-012, SC-008).
    - Compute pseudotime ordering using Monocle3 or Slingshot and validate against known developmental markers (NEUROD6, GFAP, MAP2) with Pearson r ≥ 0.6; log correlation values and halt if validation fails.
    - Output: single AnnData object at `data/processed/integrated_atlas.h5ad` with `.obs` columns for `developmental_stage`, `donor_id`, `pseudotime`, and `.var` for gene names.
    - Verification: Run `pytest tests/test_preprocess.py` to confirm output passes `dataset.schema.yaml` validation; verify ≥ 80% cell retention (SC-001) and ≥ 20% increase in stage-explained variance vs. pre-integration baseline (SC-002); record LISI score and marker correlation in `data/processed/qc_report.txt`.

- [ ] T003 [P1] [US-1, US-2, US-3] Execute thin end-to-end analysis on 5,000-cell subset producing `data/results/thin_results.json`.
    - Subsample the integrated atlas to 5,000 cells, preserving the distribution of developmental stages.
    - Run pseudotime-based sliding window GRN inference (GRNBoost2, window size = 500 cells, step = 250 cells) to produce 3–5 network snapshots.
    - Calculate edge weight differences and hub stability between adjacent windows (z-score normalized edge weights within each window).
    - Map a small subset of GWAS risk genes (e.g., 50 genes for schizophrenia from GWAS Catalog) to rewired hubs and execute a hypergeometric enrichment test.
    - Run 100 permutations of network structure to compute an empirical p-value for the enrichment.
    - Output JSON containing: `rewiring_events` (list of TF, stage_a, stage_b, weight_delta), `enrichment_results` (disorder, odds_ratio, p_value), and `metadata` (cell_count, stage_count, random_seed).
    - Verification: `thin_results.json` contains at least one rewiring event with weight_delta ≠ 0 and one enrichment p-value derived from real data (not synthetic); validate JSON schema conformance.

**Checkpoint**: The documented command executes successfully and produces real numerical outputs without synthetic fallbacks.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [P2] [US-2] Implement full-scale pseudotime ordering and sliding-window GRN inference producing `data/processed/networks/{stage_id}.json` and `data/processed/networks_motif/{stage_id}.json`.
    - Load the integrated atlas from T002 and compute pseudotime ordering for the full dataset using Monocle3 or Slingshot.
    - Define sliding windows over pseudotime (window size ≈ 5,000 cells, step ≈ 2,500 cells) and assign a `stage_id` label to each window (e.g., `"window_001"`, `"window_002"`).
    - For each window, run GRNBoost2 (`arboreto` library) to infer TF-target edges with importance weights (FR-003).
    - For each GRNBoost2 network, apply pySCENIC motif enrichment filtering: retain only edges where the TF has a cis-regulatory motif match in the target promoter region (FR-006, construct validity).
    - Output two JSON files per window: `networks/{stage_id}.json` (raw GRNBoost2 edges) and `networks_motif/{stage_id}.json` (motif-validated edges), each formatted as an adjacency list: `{"tf_1": [{"target": "gene_1", "weight": 0.85}, ...], ...}`.
    - Verification: Each JSON file is valid and contains at least 100 edges; spot-check 3 motifs using the pySCENIC reference database to confirm TF-target pairs have biological support.

- [ ] T005 [P2] [US-2] Implement rewiring detection and sensitivity analysis producing `data/processed/rewiring_events.csv`.
    - Load all motif-validated networks from T004 and compute pairwise edge weight differences between adjacent windows.
    - Normalize edge weights within each window using z-score transformation (subtract mean, divide by std) before computing deltas (FR-004, methodology-7516c898).
    - For each TF with degree ≥ 10 (or top 20 TFs if fewer than 10 meet threshold), calculate: (a) total weight_delta across its edges, (b) hub_stability_score (Jaccard similarity of target sets between adjacent windows).
    - Perform sensitivity analysis: sweep the rewiring threshold (edge weight delta cutoff) over {0.01, 0.05, 0.1}; for each threshold, identify rewiring events and record the TF, stage pair, and weight_delta.
    - Output CSV with columns: `event_id`, `tf`, `stage_a`, `stage_b`, `weight_delta`, `stability_score`, `threshold_tested`.
    - Verification: Calculate Jaccard similarity of the top 20 rewiring events (by weight_delta magnitude) across the three thresholds; target Jaccard ≥ 0.8 (SC-005). Log the sensitivity results in `data/processed/sensitivity_report.txt`.

- [ ] T006 [P2] [US-3] Implement GWAS mapping and hypergeometric enrichment tests producing `data/processed/disorder_enrichment.csv`.
    - Fetch verified GWAS risk gene lists for 3–5 neurological disorders (schizophrenia, autism, intellectual disability, bipolar disorder, epilepsy) from the GWAS Catalog (https://www.ebi.ac.uk/gwas/); use `requests` to download and parse the catalog, filtering for genes with p < 5e-8.
    - For each disorder, construct a matched-gene background control set (same size as risk genes) matched on: gene length, baseline expression level (median expression in the atlas), and network degree in the full GRN (FR-005, methodology-79849ee1).
    - For each disorder, test for hypergeometric enrichment of risk genes in the set of rewired hubs identified in T005 (hubs from windows showing the largest weight_delta for that disorder's associated developmental stage).
    - Calculate odds ratio (OR) and p-value for each disorder; target OR ≥ 1.5 (SC-004).
    - Output CSV with columns: `disorder`, `vulnerability_window`, `risk_gene_count`, `rewired_hub_count`, `overlap_count`, `odds_ratio`, `p_value_raw`, `p_value_fdr`.
    - Verification: Confirm that at least one disorder shows OR ≥ 1.5 and p_value_raw ≤ 0.05 before FDR correction; validate the matched background by plotting matched vs. risk gene distributions (length, expression, degree).

- [ ] T007 [P2] [US-3] Implement permutation testing and multiple-comparison correction producing `data/results/permutation_results.json`.
    - For each disorder identified in T006, run ≥ 5,000 permutations of the network structure: randomly shuffle edge assignments while preserving the degree distribution (FR-006, SC-003).
    - For each permutation, recalculate the hypergeometric enrichment p-value and record whether it is as extreme as (or more extreme than) the observed p-value.
    - Compute the empirical p-value as the fraction of permutations with p ≤ observed_p; if zero permutations are as extreme, report `"p < 1/5000"` (FR-013, SC-009).
    - Apply Benjamini-Hochberg FDR correction across all disorder tests (FR-009).
    - Output JSON containing: `permutation_summary` (disorder, observed_p, empirical_p, fdr_adjusted_p, permutation_count), `power_analysis` (simulated power to detect OR ≥ 1.5 at p ≤ 0.05 given 50k cells, 5k TFs, expected effect size).
    - Verification: Empirical p-value for at least one disorder must be ≤ 0.05 (SC-003); compare empirical p-values to raw p-values and confirm FDR correction is conservative.

- [ ] T008 [P2] [US-3] Implement independent validation against external cohorts producing `data/results/validation_metrics.json`.
    - Topological Validation: Obtain an independent scRNA-seq cohort (e.g., from the Human Cell Atlas or a separate GEO accession) covering at least 2 of the same developmental stages as the primary dataset.
    - Infer GRNs for the same stages in the independent cohort using the same pipeline (T004, T005); compare the rewiring events identified in the primary dataset to those in the independent cohort.
    - Calculate the Jaccard similarity of the top 20 rewired TFs between datasets; target ≥ 0.5 overlap (SC-006).
    - Expression Validation: Download bulk RNA-seq time-course data from BrainSpan (https://www.brainspan.org/); for each disorder's vulnerability window, extract expression trends for the rewired hub TFs and calculate Spearman correlation with the pseudotime trajectory in the primary dataset.
    - Output JSON with: `topological_validation` (independent_cohort_id, jaccard_similarity, overlapping_tfs), `expression_validation` (disorder, stage, bulk_correlation, direction_consistent).
    - Verification: Topological validation shows Jaccard ≥ 0.5; expression validation shows ≥ 70% of rewired hubs with consistent direction of effect (correlation sign) and nominal p ≤ 0.1 (SC-006).

**Checkpoint**: All scientific requirements from the specification are executed on the full dataset; results are statistically validated and replicated in independent data.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 [P3] [US-2, US-3] Generate final visualizations and summary tables producing `figures/network_topology.html`, `figures/enrichment_heatmap.html`, and `data/results/final_summary.csv`.
    - Create an interactive Plotly network visualization showing node-link diagrams for 2–3 key developmental windows, with TF nodes colored by hub stability and edges colored by weight_delta (FR-007).
    - Create a heatmap visualization (Plotly or matplotlib) showing disorder enrichment odds ratios across developmental windows, with significance markers (FR-007).
    - Generate a summary CSV with columns: `disorder`, `vulnerability_window`, `odds_ratio`, `p_value_fdr`, `empirical_p`, `is_validated`, `validation_cohort_id`, `interpretation` (using associational language only; e.g., "Network rewiring in window X is associated with disorder Y vulnerability" — no causal claims, FR-008).
    - Ensure all figure labels and annotations use associational language (e.g., "associated with," "correlated with") and avoid causal statements (FR-008).
    - Verification: All HTML figures are interactive and render correctly in a web browser; `final_summary.csv` contains ≥ 3 disorders with complete data and adheres to `output.schema.yaml`.

- [ ] T010 [P3] [US-1, US-2, US-3] Write methods/results account in `specs/001-gene-regulation/research.md` and perform final reproducibility verification.
    - Document the complete pipeline in `research.md`: data sources (BICCN Human MTG URL, GWAS Catalog URL, BrainSpan bulk data URL), preprocessing steps, GRN inference method (GRNBoost2 + pySCENIC), rewiring detection algorithm (z-score normalized edge deltas), enrichment test (hypergeometric with matched background), permutation procedure (5,000 iterations, degree-preserving shuffling), and validation approach (independent cohort + bulk expression).
    - Link all key claims to specific rows in `final_summary.csv` and `validation_metrics.json` (e.g., "Schizophrenia risk genes are enriched in hubs rewired during Fetal 20w (OR = 1.8, empirical p = 0.003, see row 5 of final_summary.csv)").
    - Document any data gaps (e.g., missing developmental stages, insufficient cell counts in specific windows) and explain how they were handled (interpolation, exclusion, or pipeline abort).
    - State the limitations: observational design precludes causal inference, permutation power depends on network density, bulk RNA-seq provides only indirect validation of TF activity.
    - Final verification: Execute the full pipeline from `data/raw/` to `figures/` using the command in `quickstart.md` without any modifications; confirm all output files are regenerated with identical content (deterministic given `random_state=42`); re-run `pytest tests/` and confirm all tests pass.
    - Verification: `research.md` is complete, cites all artifacts, and the full pipeline re-run produces bit-identical results; all tests in `tests/` pass.

## Dependencies and requirement coverage

| Requirement | Task | Verification Artifact | Execution Order |
| :--- | :--- | :--- | :--- |
| FR-001, FR-011 | T002 | `data/processed/integrated_atlas.h5ad`, gap detection log | 1 |
| FR-002, FR-012 | T002 | LISI score in `data/processed/qc_report.txt` | 1 |
| FR-003, FR-004 | T004, T005 | `data/processed/networks_motif/*.json`, `data/processed/rewiring_events.csv` | 2 (after T002) |
| FR-006 (motif validation) | T004 | pySCENIC motif-enriched edges in `networks_motif/*.json` | 2 |
| FR-010 | T005 | Sensitivity sweep results in `data/processed/sensitivity_report.txt` | 2 |
| FR-005 | T006 | `data/processed/disorder_enrichment.csv` with matched background | 3 (after T005) |
| FR-006, FR-009, FR-013 | T007 | `data/results/permutation_results.json` with empirical p-values | 3 (after T006) |
| FR-014 | T008 | `data/results/validation_metrics.json` with independent cohort results | 3 (after T007) |
| FR-007, FR-008 | T009 | `figures/network_topology.html`, `figures/enrichment_heatmap.html`, `data/results/final_summary.csv` | 4 (after T008) |
| All FR | T010 | `research.md` with linked claims, full pipeline re-run, test suite pass | 5 (final) |

**Note on Compute Feasibility**: All tasks are CPU-tractable. GRNBoost2 and pySCENIC run efficiently on CPU; streaming data loading ensures the 50k-cell atlas fits within 7 GB RAM; 5,000 permutations complete within ~2 hours on a 2-core CPU. No GPU is required.

**Note on Data Provenance**: All external data sources are verified, reachable, and documented in task descriptions (BICCN Human MTG from HuggingFace, GWAS Catalog from EBI, BrainSpan bulk data from brainspan.org). No synthetic or fabricated data is generated; all analyses use real, streamed data with explicit sample sizes and limitations documented in `research.md`.
