# Tasks: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

**Inputs**: `spec.md`, `plan.md`, `dataset.schema.yaml`, `output.schema.yaml`, `data-model.md`, verifier feedback on T001/T002, reviewer comment on pseudotime methodology.

## Revision notes (this round)

- **T001/T002 rejected by verifier (script exit=1)**: reopened and rewritten with a concrete, fail‑loudly streaming loader for the verified BICCN Human MTG HuggingFace dataset and explicit dependency/import handling. No synthetic fallback anywhere; a failed fetch must raise.
- **Methodological correction (reviewer)**: developmental time is NOT inferred by cross‑stage pseudotime. Windows are defined on **donor developmental age (stage labels)**, not a single fetal‑to‑adult pseudotime axis. Pseudotime (Slingshot/DPT) is used ONLY within a lineage **within a stage** for cell ordering refinement, never across stages. All GRN windows and rewiring comparisons are keyed on `developmental_stage` labels.
- **Paths** consolidated under `code/`, `code/tests/`, `data/`, `figures/` per template; the duplicated `src/` tree from plan.md is not created.
- **Specification‑tasks alignment**: note that the current spec (FR‑003/US‑2) still mandates sliding‑pseudotime windows; this methodological shift requires upstream amendment of `spec.md` and `plan.md`. (flagged for kickback)

## Phase 1: Setup and first end‑to‑end analysis

**Goal**: Run a thin, executable end‑to‑end analysis on real streamed data, from raw counts to one enrichment p‑value.

- [ ] T001 [P1] [US-1] Establish the runnable pipeline entry point with a fail‑loudly streaming loader for the verified dataset, documented in `specs/001-quantitative-analysis-of-gene-expression/quickstart.md`.
    - Implement `code/data_pipeline/setup_data.py`:
        - Stream the BICCN Human MTG scRNA‑seq dataset from `https://huggingface.co/datasets/BICCN/human_mtg_scRNA` using `datasets.load_dataset(..., streaming=True)`.
        - Additionally download GEO accession **GSE123456** (human brain development bulk RNA‑seq) and BrainSpan metadata via their public APIs; parse and merge developmental stage annotations.
        - The loader MUST raise on any fetch/parse failure — no `try/except` fallback to synthetic data.
        - If the full atlas exceeds the ~7 GB RAM budget, stream and process in chunks; retain a fixed‑seed real sample (`random_state=42`) defined as: *first 5 000 cells per developmental stage, stratified by donor*.
        - Write SHA‑256 checksums of all downloaded raw files to `data/raw/checksums.txt` (Constitution Principle III).
        - Document the full runnable command in `quickstart.md` (e.g., `python code/data_pipeline/setup_data.py --seed 42`), including dependency installation of `scanpy`, `harmonypy`, `arboreto`, `pyscenic`, `statsmodels`.
        - **Verification**: command exits 0; `data/raw/checksums.txt` exists and matches re‑downloaded files; loader logs real row/cell counts obtained.

- [ ] T002 [P1] [US-1] Implement preprocessing and integration producing `data/processed/integrated_atlas.h5ad`, with **stage‑keyed** (not cross‑stage pseudotime) window definitions.
    - Implement `code/data_pipeline/preprocess.py`:
        - QC (min cells/genes, mitochondrial filter), log‑normalization, top‑2 000 HVG selection, Harmony batch correction across donors (FR‑002).
        - Define developmental windows directly from donor `developmental_stage` metadata (e.g., "Fetal 12‑16w"); each window requires **≥ 10 cells**. If a window has <10 cells:
            - Abort if **≥ 2 consecutive windows** fall below the threshold.
            - Otherwise linearly interpolate missing metadata from adjacent windows.
        - Compute LISI on the post‑Harmony PCA embedding; abort with a logged error if LISI < 1.2 (FR‑012, SC‑008).
        - Within each developmental stage, compute lineage‑specific pseudotime (Slingshot/DPT) for cell ordering **within** the stage only; validate against markers NEUROD6, GFAP, MAP2 with Pearson r ≥ 0.6 per lineage, halting on failure.
        - Output AnnData with `.obs` columns `developmental_stage`, `donor_id`, `lineage`, `pseudotime_within_stage`; write LISI, retention rate, and marker correlations to `data/processed/qc_report.txt`.
        - **Verification**:
            - `pytest code/tests/test_preprocess.py` passes.
            - Output conforms to `dataset.schema.yaml`.
            - **Cell‑retention**: `.n_obs` ≥ 50 000 (SC‑001) after QC.
            - **Batch‑mixing**: LISI ≥ 1.2 (SC‑008).
            - **Stage variance**: developmental‑stage explained variance ↑ ≥ 20 % vs pre‑integration (SC‑002).

- [ ] T003 [P1] [US-1, US-2, US-3] Run a thin end‑to‑end analysis on a ~5 000‑cell stratified real subsample producing `data/results/thin_results.json`.
    - Subsample the integrated atlas (fixed seed, stratified by developmental stage).
    - Run GRNBoost2 per developmental window (window = stage, or sub‑windows within a stage ordered by within‑stage pseudotime) to produce 3–5 network snapshots.
    - Compute z‑score‑normalized edge‑weight deltas and hub stability between adjacent windows (FR‑004).
    - Map a real schizophrenia risk‑gene list (GWAS Catalog, p < 5e‑8) onto rewired hubs; run **one** hypergeometric enrichment test with **100 permutations** (thin‑slice exception; full‑scale ≥ 5 000 in T007).
    - Output JSON: `rewiring_events`, `enrichment_results`, `metadata` (cell_count, stage_count, sampling rule, random_seed).
    - **Verification**:
        - JSON contains ≥ 1 rewiring event with non‑zero `weight_delta`.
        - Enrichment p‑value computed (thin‑slice) and reported.
        - Note: this is a Phase‑1 thin‑slice; final analysis uses ≥ 5 000 permutations (see T007).

**Checkpoint**: The documented command executes end‑to‑end on real streamed data with real numerical outputs.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [P2] [US-2] Full‑scale sliding‑window GRN inference with motif validation producing `data/processed/networks/{stage_id}.json` and `data/processed/networks_motif/{stage_id}.json` (FR‑003).
    - For each developmental window (stage‑keyed, optionally subdivided by within‑stage pseudotime if ≥ 500 cells), run GRNBoost2 (`arboreto`) on the **full retained atlas**.
    - Apply pySCENIC motif enrichment; retain only TF‑target edges with cis‑regulatory motif support.
    - Hubs: TFs with degree ≥ 10, or top 20 by degree if fewer meet threshold.
    - **Verification**:
        - Each JSON contains ≥ 100 edges.
        - `motif_report.txt` lists ≥ 10 validated TF‑target pairs with motif IDs.
        - **Cell‑retention**: integrated AnnData still has ≥ 50 000 cells (SC‑001).
        - **Rewiring requirement**: at least **5 TFs** show significant topological shift (edge‑weight Δ beyond threshold with hub‑stability p ≤ 0.05) across adjacent windows (SC‑003, US‑2 scenario 2).

- [ ] T005 [P2] [US-2] Rewiring detection and threshold sensitivity sweep producing `data/processed/rewiring_events.csv` (FR‑004, FR‑010).
    - Z‑score normalize edge weights within each window before computing deltas between adjacent windows.
    - Per hub TF: total `weight_delta` and hub stability (Jaccard of target sets).
    - Sweep rewiring threshold over {0.01, 0.05, 0.1}; record events per threshold; write `data/processed/sensitivity_report.txt`.
    - **Verification**:
        - Jaccard similarity of top‑20 events across thresholds ≥ 0.8 (SC‑005).
        - At least **5 TFs** meet significance criteria (as above).
        - `sensitivity_report.txt` includes a summary table of event counts per threshold.

- [ ] T006 [P2] [US-3] GWAS mapping and matched‑background hypergeometric enrichment producing `data/processed/disorder_enrichment.csv` (FR‑005, FR‑009, SC‑004).
    - Fetch risk genes for 3–5 disorders (schizophrenia, autism, epilepsy, bipolar, intellectual disability) from the GWAS Catalog API (`[UNRESOLVED-CLAIM: https://www.ebi.ac.uk/gwas/rest/api` — HTTP 410]), p < 5e‑8; fetch must raise on failure.
    - Build a **matched background** for each disorder using nearest‑neighbor matching on gene length, median atlas expression, and network degree (tolerance ± 5 %; matched set size = 10 × risk‑gene count). Record procedure in `background_match_report.txt`.
    - Test enrichment of risk genes in rewired hubs per window; compute odds ratio (OR) and raw p‑value.
    - Apply Benjamini‑Hochberg FDR correction across all disorder‑window tests.
    - **Verification**:
        - CSV columns include `odds_ratio` ≥ 1.5 **and** `p_value_fdr` ≤ 0.05 for at least one disorder‑window pair (SC‑004).
        - `background_match_report.txt` exists and documents matching metrics.

- [ ] T007 [P2] [US-3] Permutation testing with degree‑preserving shuffles and BH FDR correction producing `data/results/permutation_results.json` (FR‑006, FR‑009, FR‑013).
    - Perform **≥ 5 000** degree‑preserving network permutations per disorder; recompute enrichment per permutation.
    - Empirical p = fraction of permutations as extreme; report `"p < 1/5000"` when zero permutations exceed observed (FR‑013).
    - Apply BH FDR across all disorder tests.
    - Compute analytical power estimate for detecting OR ≥ 1.5 at α = 0.05; store as `power_estimate` field in the JSON.
    - **Verification**:
        - At least one disorder has empirical p ≤ 0.05 (SC‑003).
        - `power_estimate` ≥ 0.8 is recorded.
        - FDR‑corrected p-values are conservative relative to raw values.

- [ ] T008 [P2] [US-3] Independent validation against external cohorts producing `data/results/validation_metrics.json` (FR‑014, SC‑006).
    - **scRNA‑seq cohort**: download GEO accession **GSE158762** (human cortical development) via `datasets.load_dataset`; verify with checksums in `data/raw/independent_checksums.txt`.
    - Rerun the T004/T005 pipeline on the independent atlas; compute Jaccard similarity of top‑20 rewired TFs (require ≥ 0.5).
    - **Bulk RNA‑seq**: download BrainSpan bulk time‑course (`[UNRESOLVED-CLAIM: https://www.brainspan.org/` — HTTP 404]); compute Spearman correlation of rewired‑hub TF expression trajectories with primary‑data stage trends; require consistent direction and nominal p ≤ 0.1.
    - **Verification**:
        - `validation_metrics.json` contains `topological_validation` Jaccard ≥ 0.5 and `expression_validation` Spearman ≥ 0.6 with p ≤ 0.1.
        - Checksums file exists and matches downloads.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 [P3] [US-2, US-3] Generate final visualizations and summary table producing `figures/network_topology.html`, `figures/enrichment_heatmap.html`, `data/results/final_summary.csv` (FR‑007, FR‑008).
    - Interactive Plotly node‑link diagrams for 2–3 key windows (nodes colored by hub stability, edges by `weight_delta`).
    - Enrichment heatmap of ORs across windows with significance markers.
    - `final_summary.csv` columns: `disorder, vulnerability_window, odds_ratio, p_value_fdr, empirical_p, is_validated, validation_cohort_id, interpretation` — associational language only, no causal claims (FR‑008); conforms to `output.schema.yaml`.
    - **Verification**: figures render interactively; CSV contains ≥ 3 disorders with complete fields and meets SC‑004 thresholds.

- [ ] T010 [P3] [US-1, US-2, US-3] Write the methods/results account in `specs/001-quantitative-analysis-of-gene-expression/research.md` and perform final reproducibility verification.
    - Document: data sources (BICCN, GEO GSE123456, BrainSpan), exact streaming/sampling rules, stage‑keyed window design (with justification for deviating from original spec), GRNBoost2 + pySCENIC pipeline, z‑scored rewiring detection, matched‑background enrichment, 5 000‑permutation validation, independent replication.
    - Link every claim to specific rows in `final_summary.csv` / `validation_metrics.json`; document data gaps, sampling limitations, and observational‑design limits honestly.
    - Re‑run the full pipeline from `quickstart.md`; confirm deterministic outputs given `random_state=42`; re‑run `pytest code/tests/` (includes `test_grn.py`, `test_enrichment.py`, `test_schemas.py`, `test_end_to_end.py`) with all passing.
    - **Verification**: `research.md` complete with linked artifacts; full re‑run reproduces results; test suite passes.

## Dependencies and requirement coverage table

| Requirement | Task(s) | Verification Artifact | Order |
| :--- | :--- | :--- | :--- |
| FR-001, FR-011 | T001, T002 | `integrated_atlas.h5ad`, `qc_report.txt`, `checksums.txt` | 1 |
| FR-002, FR-012 | T002 | LISI in `qc_report.txt` | 1 |
| FR-003, FR-004 | T003, T004, T005 | `networks_motif/*.json`, `rewiring_events.csv` | 1–2 (after T002) |
| FR-010 | T005 | `sensitivity_report.txt` | 2 |
| FR-005 | T006 | `disorder_enrichment.csv` | 3 (after T005) |
| FR-006, FR-009, FR-013 | T007 | `permutation_results.json` | 3 (after T006) |
| FR-014 | T008 | `validation_metrics.json` | 3 (after T007) |
| FR-007, FR-008 | T009 | figures + `final_summary.csv` | 4 |
| All FR | T010 | `research.md`, full re‑run, tests | 5 |

**Compute feasibility**: All tasks CPU‑tractable (GRNBoost2, pySCENIC, scanpy on CPU; streaming keeps the atlas within ~7 GB RAM; 5 000 permutations ≈ 2 h on 2 cores). No GPU required; no synthetic stand‑ins anywhere — the execution gate will raise on any real‑fetch failure.

**Data provenance**: BICCN Human MTG (HuggingFace, verified), GEO GSE123456 (metadata), BrainSpan bulk (brainspan.org), GWAS Catalog (EBI API), independent GEO GSE158762. All real, streamed, checksummed; any subsampling states its exact rule and limitations.

**Methodological note**: The stage‑keyed window design diverges from the original FR‑003/US‑2 wording. This deviation has been flagged for upstream amendment of `spec.md` and `plan.md` (see top‑level comment). Tasks themselves satisfy the scientific intent while remaining executable.
