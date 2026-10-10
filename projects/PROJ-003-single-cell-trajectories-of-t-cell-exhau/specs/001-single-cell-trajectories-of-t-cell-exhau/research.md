# Research: Single-Cell Trajectories of T-Cell Exhaustion

## Executive Summary

The study reconstructs RNA-velocity trajectories of T-cell exhaustion on the four GEO datasets stipulated by FR-012, identifies statistically significant fork-points via a permutation null that preserves splicing kinetics, ranks fork-point genes by differential timing, and validates them against a therapy-response signature with bootstrap resampling and BH-corrected significance testing. All findings are framed as associational (Constitution Principle VI). This revision repairs the four rejected tasks: the missing `data/results/` layout (T001), the failing downloader (T002), the non-functional mitochondrial QC filter caused by unloaded gene symbols (T003), and the failing velocity script (T004).

## Dataset Strategy

**Verified-source status (per the verified-datasets block): NO verified source was found for GSE136103, GSE127465, GSE111075, or GSE138852.** No URL is cited for any of them, and none is invented. The datasets are referenced by GEO accession only; the downloader resolves supplementary-file URLs at run time from the official NCBI GEO accession metadata endpoint (`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<ACCESSION>&targ=self&form=text`), which is the canonical NCBI service rather than a guessed FTP path. If resolution or download fails for an accession, the dataset is marked `unavailable`, the pipeline proceeds with the remainder, and the final report records the gap. No synthetic or toy stand-in is ever substituted.

| Spec dataset | Verified source | Variables expected | Action |
|---|---|---|---|
| GSE136103 | **No verified source found** (accession referenced by ID only) | mt genes, CD3D/E/G, exhaustion markers (PDCD1, LAG3, TOX) | Run-time URL discovery from NCBI accession metadata; QC; T-cell subset; velocity |
| GSE127465 | **No verified source found** (accession referenced by ID only) | exhaustion signatures, CD3 genes | Same; MT-gene annotation fixed (T003) |
| GSE111075 | **No verified source found** (accession referenced by ID only) | exhaustion signatures | Same |
| GSE138852 | **No verified source found** (accession referenced by ID only) | exhaustion markers + expected `therapy_response` labels | Same + enrichment/validation; label presence verified at run time, not assumed |

Marker presence is checked per FR-010 (≥80% of the marker list must be present, including PD-1, metabolic markers, exhaustion signatures; therapy-response labels where applicable); missing markers are reported.

## Methodological Approach

### Phase 0–1: Layout, lint, download (T001, T002)
- Commit `data/results/{fork_points,validation,report}/.gitkeep`; record `ruff check . && black --check .` output in `logs/lint.txt`.
- `code/download_data.py --datasets GSE136103 GSE127465 GSE111075 GSE138852 --output data/raw/`: fetches accession metadata from the NCBI endpoint above, parses supplementary file URLs, downloads with `curl -L --retry 5`, computes SHA-256 checksums (Constitution III), runs the FR-010 marker check, and writes Dataset artifacts validated against `contracts/dataset.schema.yaml`. Exit code 0 requires at least one successful dataset; per-dataset failures are logged and marked `unavailable` (never silently retried into a fabricated mirror).

### Phase 2: Preprocessing (T003 fix)
- Root cause of the prior failure: the `.mtx` loader left generic var names, so the `MT-` pattern never matched and zero cells were filtered.
- Fix: `preprocess.py` explicitly loads the features/`genes.tsv` file and assigns gene symbols to `adata.var`; if only Ensembl IDs are present, a bundled Ensembl→HGNC symbol map annotates mitochondrial genes (`MT-` prefix, plus `MTND1`-style aliases as fallback). The QC step then filters cells with >20% mitochondrial reads, log-normalizes, and selects 2,000 HVGs via Seurat v4 parameters (`preprocess.R`).
- Unit tests import and **call** the real `preprocess` module functions on fixture AnnData objects containing MT genes, asserting cells are actually removed; integration test asserts the filter changes cell count on a real-shaped fixture.

### Phase 3: T-cell subsetting
- `subset_tcells.py` keeps cells with CD3D/E/G expression ≥ threshold; datasets with <1,000 cells post-filter are skipped with a warning and "partial" status (spec edge case).

### Phase 4: Velocity & pseudotime (T004 fix)
- `velocity.py` runs scVelo stochastic mode on CPU: `scv.pp.moments` → `scv.tl.velocity` → `scv.tl.velocity_graph` → `scv.tl.velocity_pseudotime` (Markov-chain random-walk pseudotime). Prior failure is addressed by explicit spliced/unspliced layer detection with informative errors when layers are absent (a real gap reported, not worked around), bounded retries, and full tracebacks logged to `logs/velocity.log`. Alignment convergence failures retry with higher regularization (up to 2 retries), then emit `alignment_status: "failed"` and halt cross-dataset validation for that dataset. Wall-clock time and peak memory (`psutil`) are logged per dataset (SC-001).

### Phase 5: Fork-point detection
- Per-cell divergence of the velocity vector field in PCA space; null distribution from 1,000 permutations that shuffle cell topology while preserving splicing kinetics; branch points significant at p<0.01; divergence <1.5 SD above null mean flagged `low_confidence` and excluded from the ranked list. Significant cells clustered into discrete `branch_id`s; genes extracted and ranked by differential timing (>0.1 pseudotime units between early/late branches). Output CSV: `gene_symbol, branch_id, timing_rank` per FR-005, validated against `contracts/fork_point.schema.yaml`.

### Phase 6: Power analysis (FR-011)
- Simulation-based power analysis for the divergence test and the enrichment test (80% power, α=0.05) given the realized per-dataset cell counts; the pipeline aborts with an explicit report if power is insufficient.

### Phase 7: Enrichment & validation
- `enrichment.py`: therapy-response signature derived from GSE138852 responder vs. non-responder labels **if actually present in the downloaded metadata** (verified at run time); Fisher's exact test (FR-008) and two-sided t-test over 1,000 bootstrap resamples of cell populations (FR-006), BH-corrected, significance p<0.01. If response labels are absent, the step reports the gap explicitly rather than fabricating labels.
- `validate.py`: 1,000 bootstrap iterations for 95% CIs on the enrichment metric; Spearman rank correlation of fork-point-gene timing ranks across datasets (spec target ≥0.80 for top-3 genes, reported as measured); ValidationResult artifacts per `contracts/validation.schema.yaml`.

### Phase 8: Reporting
- `report.py` emits `data/results/report/final_report.html` with: velocity UMAP, divergence heatmap with fork-point locations, ranked gene table, cross-dataset heatmap of top fork-point genes with bootstrap CIs (FR-007), enrichment statistics, runtime/memory table (SC-001), power-analysis result, dataset-availability table, and the FR-009 disclaimer that all associations are observational, not causal.

## Statistical Rigor & Assumptions

| Aspect | Specification |
|---|---|
| Multiple comparisons | BH correction at gene-level divergence tests and enrichment tests (FR-004/006/008). |
| Power | Simulation-based analysis, 80% power, α=0.05; abort if insufficient (FR-011). |
| Causal framing | Observational; associational disclaimer mandatory (FR-009, Principle VI). |
| Measurement validity | scVelo and Seurat are community-standard, widely validated tools; exhaustion markers (PDCD1/PD-1, LAG3, TOX) are established. |
| Collinearity | The therapy-response signature is derived from response labels, not from the velocity signal, preserving predictor/predicted distinction (Principle VI). |
| Bootstrap | 1,000 iterations per FR-006 (the prior plan's 500 was an un-spec'd deviation — corrected to 1,000). |

## Compute Feasibility

- **CPU-first**: all methods (scanpy, scVelo stochastic, classical statistics) run faithfully on the 2-CPU/~7 GB runner; no GPU escape hatch required. `device` is CPU with default precision per FR-003.
- Largest dataset processed chunk-wise; peak RAM <7 GB; scVelo ≤45 min/dataset; total ≤6 h including 1,000 bootstraps.
- Wall-clock (`time`) and peak memory (`psutil`) logged per phase (SC-001).

## Risks & Mitigations

| Risk | Cause | Mitigation |
|---|---|---|
| Downloader exit 1 (T002) | Guessed FTP URLs, no metadata parsing | Run-time URL discovery from NCBI accession endpoint; retries; per-dataset graceful degradation; full logging. |
| QC filter no-ops (T003) | Gene symbols not loaded | Features-file loading + Ensembl→symbol MT map; tests assert real filtering. |
| Velocity exit 1 (T004) | Missing spliced/unspliced layers or convergence | Layer detection with explicit errors; stochastic model; bounded retries; per-dataset isolation. |
| No verified dataset source | Verified-datasets block confirms none | Honest reporting; no fabricated URLs or mirrors; scope revision path if all four fail. |
| Missing response labels | Metadata lacks therapy_response | Report gap; restrict validation; never synthesize labels. |

---
