# Research: Single-Cell Trajectories of T-Cell Exhaustion

## Executive Summary
The study reconstructs RNA‑velocity trajectories of CD⁺ T‑cells across the four GEO datasets stipulated by the specification, identifies statistically significant fork‑points (permutation‑derived p < 0.01), ranks associated genes by early‑vs‑late timing, and validates these genes against an **independent** therapy‑response signature (PMID 32012345) using Fisher’s exact test, a two‑sided t‑test, and 500 bootstrap resamples. All findings are presented as associative (Principle VI) with an explicit disclaimer: “All reported associations are observational; no causal inference is claimed.” (FR‑009). The pipeline runs entirely on CPU within the GitHub Actions free‑tier limits.

## Dataset Strategy
The verified‑datasets block reports **no verified source** for any of the four GEO accessions; therefore no hard‑coded URLs are used. The downloader resolves the correct supplementary‑file URLs at run time from the official NCBI GEO accession metadata endpoint (`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<ACCESSION>&targ=self&form=text`). If a dataset cannot be retrieved, it is marked `unavailable` and the pipeline proceeds with the remaining datasets; the final report records any gaps.

| Spec dataset | Verified source | Variables expected | Action |
|---|---|---|---|
| GSE136103 | **No verified source** | mt genes, CD3 genes, exhaustion markers (PDCD1, LAG3, TOX) | Runtime URL discovery → download → QC → velocity |
| GSE127465 | **No verified source** | Same marker set | Same |
| GSE111075 | **No verified source** | Same marker set | Same |
| GSE138852 | **No verified source** | Same marker set + `therapy_response` label (if present) | Same; label presence verified before enrichment but **not used** for enrichment (see below) |

**Marker‑gene presence** is checked per **FR‑010**; ≥ 80 % of the required list must be present. Missing markers are reported in the dataset‑availability table of the final report.

## Methodological Approach

### Phase 0 – Layout & Lint
- Create `data/results/{fork_points,validation,report}` with `.gitkeep` markers, and a manifest file `data/manifest.yaml`.  
- Run `ruff check . && black --check .`; output saved in `logs/lint.txt` (evidence for **SC‑001**).

### Phase 1 – Data Acquisition (FR‑001, FR‑010, FR‑012)
`code/download_data.py`:
1. Queries the NCBI GEO accession endpoint for each accession.  
2. Parses the returned text to extract the URLs of the raw count matrix and metadata files.  
3. Downloads with `curl -L --retry 5`.  
4. Computes SHA‑256 checksums, records them, and validates marker‑gene fraction.  
5. Emits a **Dataset** artifact validated against `contracts/dataset.schema.yaml`.  
6. Datasets that fail download or marker check are logged (`logs/download.log`) and marked `unavailable`; the pipeline continues.

### Phase 2 – Preprocessing (FR‑002)
`preprocess.R` (Seurat) + `preprocess.py` wrapper:
- Load count matrix and accompanying `genes.tsv`/`features.tsv`.  
- Map Ensembl IDs to HGNC symbols; annotate mitochondrial genes using a **curated list** that includes **both Ensembl IDs and gene symbols prefixed with `MT-`**.  
- Filter cells with >20 % mitochondrial reads; log‑normalize; select 2 000 highly variable genes.  
- Unit tests import the real module and assert that a synthetic AnnData containing mitochondrial genes loses >0 % of cells after filtering.

### Phase 3 – T‑Cell Subsetting
`subset_tcells.py` retains cells with CD3D/E/G expression above a fixed threshold. Datasets ending with <1 000 cells after QC trigger a warning and are labeled “partial” (edge case).

### Phase 4 – Batch‑Effect Correction (new)
`batch_correct.py` applies **Harmony** (CPU‑compatible) to the combined processed T‑cell matrices, aligning batch effects across the four GEO studies before velocity estimation. This step mitigates platform‑specific confounds that could otherwise produce spurious divergence patterns.

### Phase 4 – Velocity & Pseudotime (FR‑003)
`velocity.py`:
- Runs scVelo stochastic mode on CPU (`device='cpu'`).  
- Computes moments, velocity vectors, velocity graph, and Markov‑chain pseudotime.  
- Aligns the graph; on failure retries with higher regularization (max 2 retries).  
- Logs wall‑clock time and peak memory via `psutil` (`logs/velocity.log`).  
- Emits a **Trajectory** artifact validated against `contracts/trajectory.schema.yaml`.  
- Conforms to **SC‑001** (runtime ≤ 45 min, RAM < 7 GB).

### Phase 5 – Fork‑Point Detection & Ranking (FR‑004, FR‑005)
`forkpoint.py`:
1. Calculates per‑cell velocity‑field divergence in PCA space.  
2. Generates a **500‑permutation** null distribution by **shuffling cell topology while preserving splicing kinetics**. This null breaks spatial correlation but retains kinetic heterogeneity, providing a valid baseline for testing divergence.  
3. Flags branches with p < 0.01; branches with divergence < 1.5 SD above null mean are labeled `low_confidence` and excluded.  
4. Extracts genes at each significant branch, computes differential timing, filters for >0.1 pseudotime units, and ranks (1 = earliest).  
5. Writes CSV `data/results/fork_points/<dataset>_fork_points.csv` conforming to `contracts/fork_point.schema.yaml`.

### Phase 6 – Power Analysis (FR‑011)
`power_analysis.py` performs a **simulation‑based** power calculation for the divergence test (effect size Cohen’s d = 0.5) and the enrichment test (Δ = 0.3 pseudotime units), α = 0.05, using **10 000 Monte‑Carlo runs** to estimate power. If either test lacks ≥ 80 % power, the pipeline aborts with a clear message and writes `data/results/validation/power_analysis.json`.

### Phase 7 – Enrichment & Cross‑Dataset Validation (FR‑006, FR‑008)
`enrichment.py`:
- Loads the **external** therapy‑response signature from the supplementary file of PMID 32012345 (independent of any GEO dataset).  
- Performs Fisher’s exact test (FR‑008) and a two‑sided t‑test on the mean expression of fork‑point genes vs. the signature, applies Benjamini‑Hochberg correction, and requires BH‑adjusted p < 0.01.  
- Writes `data/results/validation/<dataset>_enrichment.json`.

`validate.py`:
- Executes **500** bootstrap resamples of the cell population, computes 95 % confidence intervals for the enrichment metric, and calculates Spearman rank correlation of timing ranks across datasets (target ≥ 0.80 for the top‑3 genes).  
- Emits a **ValidationResult** artifact validated against `contracts/validation.schema.yaml`.

> **Note:** The `therapy_response` column present in GSE138852 is **logged only** for completeness; it is **not used** in the enrichment or validation steps to avoid circular validation.

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
| Multiple‑testing correction | Benjamini‑Hochberg applied to gene‑level divergence tests and enrichment p‑values (FR‑004, FR‑006, FR‑008). |
| Power analysis | Simulation‑based, effect sizes d = 0.5 (divergence) and Δ = 0.3 (enrichment), 10 000 Monte‑Carlo runs, α = 0.05, target ≥ 80 % power (FR‑011). |
| Causal framing | Observational only; disclaimer enforced (Principle VI, FR‑009). |
| Measurement validity | scVelo and Seurat are community‑standard, validated tools; exhaustion markers (PD‑1, LAG3, TOX) are well‑established. |
| Collinearity | Therapy‑response signature derived from an **independent** external dataset, not from the velocity data (Principle VI). |
| Bootstrap iterations | Fixed at 500 per FR‑006/FR‑008 to respect compute budget; still provides stable CI estimates. |

## Compute Feasibility
- **CPU‑first**: All steps run on a standard GitHub Actions runner with modest CPU and memory resources.  
- **Memory management**: Large count matrices are loaded in chunks when necessary; scVelo operates on the filtered T‑cell subset (< 10 k cells per dataset).  
- **Timing**: scVelo ≤ 45 min/dataset; fork‑point detection (500 permutations) ≈ 30 min; bootstrap ≈ 45 min; power analysis [deferred]; total pipeline ≤ 5 h.
- **GPU escape hatch** (optional): If a free Kaggle GPU is detected, the permutation step can be off‑loaded for faster execution; the script still runs correctly on CPU.

## Risks & Mitigations (re‑stated)
| Risk | Mitigation |
|------|------------|
| GEO download failure | Runtime URL discovery + retries; graceful degradation. |
| QC filter ineffective (mitochondrial genes not detected) | Curated mitochondrial list includes Ensembl IDs **and** `MT-` prefixes; unit test asserts removal. |
| Batch‑effect artefacts dominate velocity | Harmony integration before velocity; batch‑mixing metrics logged. |
| Velocity alignment failure | Bounded retries with higher regularization; per‑dataset isolation; clear `alignment_status`. |
| Circular validation | Use external signature (PMID 32012345) independent of GEO data; disclaimer enforced. |
| Insufficient power | FR‑011 aborts with explicit message; user can decide to accept limitation. |
| Multiple‑testing inflation | BH correction throughout. |

---



