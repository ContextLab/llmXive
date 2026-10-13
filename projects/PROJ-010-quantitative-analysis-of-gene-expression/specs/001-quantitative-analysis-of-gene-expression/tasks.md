# Tasks: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

**Inputs**: `spec.md`, `plan.md`, `dataset.schema.yaml`, `output.schema.yaml`, `data-model.md`.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the pipeline and run a thin, end-to-end analysis on a real subset of the human fetal brain atlas to verify the data flow from raw counts to enrichment results.

- [ ] T001 Establish the project layout, document the execution command in `quickstart.md`, and implement data hygiene for raw inputs.
    - Ensure `code/`, `data/raw/`, `data/processed/`, and `figures/` directories are initialized.
    - Verify accessibility of the raw scRNA-seq atlas via `datasets` or `GEOparse`.
    - Generate SHA-256 checksums for all raw input files and record them in the project state YAML (Constitution Principle III).
- [ ] T002 Implement the data acquisition and preprocessing pipeline in `code/data_pipeline.py` producing `data/processed/integrated_atlas.h5ad`. [US-1] <!-- FAILED-IN-EXECUTION: code/data_pipeline.py exit=1 -->
    - Implement streaming loading of the atlas to fit within 7GB RAM.
    - Implement QC, normalization, and Harmony batch correction (FR-002).
    - Implement gap detection: halt if any developmental window contains $< 10$ cells (FR-011, SC-007).
    - Implement LISI score calculation: abort if LISI $< 1.2$ (FR-012, SC-008).
    - Verification: The output `.h5ad` file must pass `dataset.schema.yaml` validation; verify that $\ge 80\%$ of input cells are retained (SC-001) and that the proportion of variance explained by developmental stage increases by $\ge 20\%$ relative to pre-integration baseline (SC-002).
- [ ] T003 Execute a thin end-to-end analysis on a sampled subset of cells (e.g., 5,000 cells) to produce a proof-of-concept result in `data/results/thin_results.json`. [US-1, US-2, US-3]
    - Run a simplified version of pseudotime ordering $\rightarrow$ GRN inference $\rightarrow$ rewiring detection $\rightarrow$ hypergeometric test.
    - Verification: `thin_results.json` must contain at least one identified rewiring event and one enrichment p-value derived from real data.

**Checkpoint**: The documented command executes and produces real numerical outputs in `data/results/` without synthetic fallbacks.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 Implement the full-scale trajectory and windowed GRN reconstruction in `code/network_inference.py` producing `data/processed/networks/{stage_id}.json`. [US-2]
    - Compute pseudotime for the full dataset and partition into sliding windows (FR-003).
    - Run GRNBoost2 (`arboreto`) for each window to infer TF-target edges and weights (FR-003).
    - Verification: Each stage JSON must contain a valid adjacency list of TF-target pairs with weights.
- [ ] T005 Implement the rewiring analysis and sensitivity sweep in `code/rewiring_analysis.py` producing `data/processed/rewiring_events.csv`. [US-2]
    - Calculate edge weight differences and hub stability between adjacent windows (FR-004).
    - Perform sensitivity analysis by sweeping the rewiring threshold over $\{0.01, 0.05, 0.1\}$ (FR-010).
    - Verification: Calculate Jaccard similarity for the top 20 events across thresholds; target $\ge 0.8$ (SC-005).
- [ ] T006 Implement GWAS mapping and hypergeometric enrichment tests in `code/clinical_analysis.py` producing `data/processed/disorder_enrichment.csv`. [US-3]
    - Execute the Reference-Validator Agent to verify all external GWAS risk gene citations against primary sources (Constitution Principle II).
    - Map these verified risk genes from catalogs to identified rewired hubs (FR-005).
    - Execute hypergeometric tests to identify significant overlap between rewired hubs and disorder risk genes (FR-005).
    - Verification: Output must conform to `output.schema.yaml` and target an odds ratio $\ge 1.5$ for at least one disorder (SC-004).
- [ ] T007 Implement statistical validation via permutation tests in `code/statistical_validation.py` producing `data/results/permutation_results.json`. [US-3]
    - Run $\ge 1,000$ permutations of the network structure to calculate empirical p-values for enrichment (FR-006).
    - Apply Benjamini-Hochberg correction to all p-values (FR-009).
    - Implement the reporting rule: if zero extremes are found, report $p < 1/N$ (FR-013, SC-009).
    - Verification: Empirical p-value for top rewiring events must be $\le 0.05$ (SC-003).
- [ ] T008 Implement multi-level independent validation in `code/validation_independent.py` producing `data/results/validation_metrics.json`. [US-3]
    - Topological Validation: Replicate rewiring events in an independent scRNA-seq cohort (FR-014).
    - Expression Validation: Cross-check hub importance using bulk RNA-seq time courses from BrainSpan (FR-014).
    - Verification: Target a consistent direction of effect (Odds Ratio $\ge 1.1$) and nominal $p \le 0.1$ (SC-006).

**Checkpoint**: All scientific requirements from the specification are executed on the full dataset; results are statistically validated and replicated.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 Generate final visualization artifacts and summary tables in `code/visualize_results.py` producing `figures/network_topology.png` and `data/results/final_summary.csv`. [US-2, US-3]
    - Create network topology plots showing the transition between windows using Plotly or Cytoscape formats (FR-007).
    - Ensure all labels and accompanying text in the results table use associational language only (FR-008).
- [ ] T010 Write the concise methods/results account in `research.md` and perform a final end-to-end workflow run to confirm reproducibility.
    - Link all claims to specific cells in `final_summary.csv` and `validation_metrics.json`.
    - Document any data gaps encountered or limitations in the permutation power.
    - Final verification: Re-run the full pipeline from `data/raw/` to `figures/` without modification.

## Dependencies and requirement coverage

| Requirement | Task | Verification Command/Artifact | Order |
| :--- | :--- | :--- | :--- |
| FR-001, 011 | T002 | `data/processed/integrated_atlas.h5ad` | 1 |
| FR-002, 012 | T002 | LISI score check in logs | 1 |
| FR-003, 004 | T004 | `data/processed/networks/*.json` | 2 |
| FR-010 | T005 | Jaccard index in `rewiring_events.csv` | 2 |
| FR-005 | T006 | `data/processed/disorder_enrichment.csv` | 3 |
| FR-006, 009, 013 | T007 | `data/results/permutation_results.json` | 3 |
| FR-014 | T008 | `data/results/validation_metrics.json` | 3 |
| FR-007, 008 | T009 | `figures/network_topology.png` | 4 |