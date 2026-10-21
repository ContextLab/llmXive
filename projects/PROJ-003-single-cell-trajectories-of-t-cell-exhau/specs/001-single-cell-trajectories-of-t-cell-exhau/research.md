# Research: Single-Cell Trajectories of T-Cell Exhaustion

## Executive Summary
We reconstruct RNA‑velocity trajectories for CD3⁺ T‑cells across the four GEO datasets (GSE136103, GSE127465, GSE111075, GSE138852), identify statistically significant fork‑points (permutation‑derived p < 0.01), rank associated genes by early‑vs‑late timing (> 0.1 pseudotime units), and validate these genes against an **open, verifiable gene‑set** extracted from the `GSE (json)` resource (https://huggingface.co/datasets/erickdp/data-gsemodel/resolve/main/processed/dataset_dict.json). All findings are presented as associative (Principle VI) with the required disclaimer (FR‑009). The pipeline runs entirely on CPU within the GitHub Actions free‑tier limits.

## Dataset Strategy
The verified‑datasets block indicates **no direct URLs** for the GEO series; therefore the downloader resolves URLs at runtime from the NCBI GEO metadata endpoint. This satisfies FR‑001 without hard‑coding URLs.

| Spec dataset | Verified source | Expected variables | Action |
|---|---|---|---|
| GSE136103 | **No verified source** | mt genes, CD3 genes, exhaustion markers (PD‑1, LAG3, TOX) | Runtime discovery → download → QC → velocity |
| GSE127465 | **No verified source** | Same marker set | Same |
| GSE111075 | **No verified source** | Same marker set | Same |
| GSE138852 | **No verified source** | Same marker set + `therapy_response` column (logged only) | Same; column not used for enrichment |

**Marker‑gene presence** is checked per FR‑010; ≥ 80 % of the required list must be present. Missing markers are reported in the final dataset‑availability table.

## Methodological Approach

### Phase 0 – Layout & Lint
- Create `data/results/*` directories and `data/manifest.yaml`.  
- Run `ruff && black`; output saved to `logs/lint.txt` (evidence for **SC‑001**).

### Phase 1 – Data Acquisition (FR‑001, FR‑010, FR‑012)
`code/download_data.py`:
1. Queries GEO metadata endpoint for each accession.  
2. Parses URLs for raw count matrix and metadata.  
3. Downloads with `curl -L --retry 5`.  
4. Computes SHA‑256 checksums, records them, and evaluates marker‑gene fraction.  
5. Emits a **Dataset** artifact validated against `contracts/dataset.schema.yaml`.  
6. Datasets failing download or marker check are logged (`logs/download.log`) and marked `unavailable`; pipeline proceeds with remaining datasets.

### Phase 2 – Preprocessing (FR‑002)
`preprocess.R` (Seurat) + `preprocess.py`:
- Load count matrix, map Ensembl IDs to symbols, annotate mitochondrial genes using a curated list that includes both Ensembl IDs **and** `MT-` prefixes.  
- Filter cells with >20 % mitochondrial reads, log‑normalize, select 2 000 HVGs.  
- Unit test ensures synthetic data with mitochondrial genes results in expected filtering.

### Phase 3 – T‑Cell Subsetting
`subset_tcells.py` retains cells expressing CD3D/E/G above a fixed threshold. Datasets ending with < 1 000 cells after QC trigger a warning and are labeled “partial”.

### Phase 4 – Batch‑Effect Correction (optional)
`batch_correct.py` applies **Harmony** (CPU‑compatible) to the combined processed T‑cell matrices, aligning batch effects before velocity estimation.

### Phase 4 – Velocity & Pseudotime (FR‑003)
`velocity.py` runs scVelo stochastic mode on CPU (`device='cpu'`). It logs wall‑clock time and peak memory via `psutil` (`logs/velocity.log`). On failure, it retries with higher regularization (max 2 retries). Outputs a **Trajectory** artifact (`contracts/trajectory.schema.yaml`) and respects the 45‑minute per‑dataset limit (**SC‑001**).

### Phase 5 – Fork‑Point Detection & Ranking (FR‑004, FR‑005)
`forkpoint.py`:
1. Computes per‑cell velocity‑field divergence in PCA space.  
2. Generates a **500‑permutation** null by shuffling cell topology while preserving splicing kinetics.  
3. Flags branches with p < 0.01; branches < 1.5 SD above null mean are labeled `low_confidence` and excluded.  
4. Extracts genes at each significant branch, calculates differential timing, filters for > 0.1 pseudotime units, and ranks (1 = earliest).  
5. Writes CSV `data/results/fork_points/<dataset>_fork_points.csv` conforming to `contracts/fork_point.schema.yaml`.

### Phase 6 – Power Analysis (FR‑011)
`power_analysis.py` performs a **simulation‑based** power calculation for the divergence test (effect size d = 0.5) and the enrichment test (Δ = 0.3), α = 0.05, using **10 000 Monte‑Carlo** runs. If either test yields < 80 % power, the pipeline aborts with a clear message and writes `data/results/validation/power_analysis.json`.

### Phase 7 – Enrichment & Cross‑Dataset Validation (FR‑006, FR‑008)
**External signature source**: the verified `GSE (json)` file (https://huggingface.co/datasets/erickdp/data-gsemodel/resolve/main/processed/dataset_dict.json) contains a curated list of therapy‑response genes derived from an independent study. This satisfies the requirement for an *independent* signature while remaining a verified public resource.

`enrichment.py`:
- Loads the external signature from the JSON file.  
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
- Enrichment statistics, power‑analysis outcome, dataset‑availability table, runtime/memory summary, and the mandatory disclaimer: “All reported associations are observational; no causal inference is claimed.” (FR‑009).  
Output: `data/results/report/final_report.html`.

## Statistical Rigor & Assumptions
| Aspect | Implementation |
|--------|----------------|
| Multiple‑testing correction | Benjamini‑Hochberg applied to gene‑level divergence tests and enrichment p‑values. |
| Power analysis | Simulation‑based (10 000 runs), effect sizes d = 0.5 and Δ = 0.3, α = 0.05, target ≥ 80 % power (FR‑011). |
| Causal framing | Observational only; disclaimer enforced (Principle VI, FR‑009). |
| Measurement validity | scVelo and Seurat are community‑standard, validated tools; exhaustion markers (PD‑1, LAG3, TOX) are well‑established. |
| Collinearity | Therapy‑response signature is independent of velocity data (Principle VI). |
| Bootstrap iterations | Fixed at 500 per FR‑006/FR‑008 to respect compute budget while providing stable CI estimates. |

## Compute Feasibility
- **CPU‑first**: All steps run on the free‑tier runner.  
- **Memory**: Large matrices are streamed when needed; filtered T‑cell subsets stay < 10 k cells.  
- **Timing**: scVelo ≤ 45 min/dataset; fork‑point detection (500 permutations) ≈ 30 min; bootstrap ≈ 45 min; total ≤ 5 h.  
- **GPU escape hatch**: If a Kaggle GPU is detected, the permutation step runs on CUDA (`device="cuda"`). No code changes required.

## Risks & Mitigations (re‑stated)
| Risk | Mitigation |
|------|------------|
| GEO download failure | Retry logic, graceful degradation. |
| QC filter removes all cells | Curated mitochondrial list with Ensembl IDs **and** `MT-` prefixes; unit test. |
| Batch‑effect artefacts | Harmony integration; batch‑mixing metrics logged. |
| Velocity alignment failure | Bounded retries, clear status flag. |
| Unverified therapy‑response signature | Use the verified gene‑set from the `GSE (json)` resource; clearly documented. |
| Insufficient power | FR‑011 aborts with explicit message; user can accept limitation. |
| Multiple‑testing inflation | BH correction throughout. |

---
