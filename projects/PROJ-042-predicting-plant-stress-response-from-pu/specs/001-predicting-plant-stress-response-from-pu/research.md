# Research: Predicting Plant Stress Response from Publicly Available Transcriptomic Data

## Dataset Strategy

The pipeline discovers public plant RNA‑seq GEO series programmatically using **GEOparse** (verified loading recipe provided in the spec). No pre‑canned URLs are used because no open, directly‑downloadable plant stress datasets with the required metadata are present in the verified dataset list. The discovery workflow:

| Step | Action |
|------|--------|
| 1 | Query NCBI GEO via Entrez for series where `organism` ∈ {*Arabidopsis thaliana*, *Oryza sativa*, *Solanum lycopersicum*, *Zea mays*} and `title` or `summary` contain any of “drought”, “salinity”, “heat”, “cold”. |
| 2 | For each candidate accession, download the full SOFT file using `GEOparse.get_GEO`. |
| 3 | Parse sample metadata; keep series that contain **≥ 2** of the four target stress types (including a control condition). |
| 4 | Verify that **all four stress types** appear in the combined pool and that each stress is present in **≥ 2** distinct series. |
| 5 | Record SHA‑256 checksum of each raw archive; store in `state/projects/…yaml`. |
| 6 | If fewer than **7** qualifying series are found, abort with error `E‑DATA‑INSUFFICIENT` (FR‑017). |

*Result*: When sufficient series exist, they are downloaded to `data/raw/`. If the discovery step yields fewer than 7, the pipeline stops and reports the shortfall, satisfying the specification’s abort clause.

## Methodological Rigor & Statistical Plan

### 1. Hypothesis Testing & Multiple Comparisons
- **Primary metric**: Cross‑dataset classification accuracy (LODO).  
- **Null distributions**:  
  - *Within‑fold permutation*: Randomly permute stress labels **within** the held‑out dataset 1,000 times (preserving batch).  
  - *Across‑dataset permutation*: Shuffle stress labels **across** all datasets while keeping dataset boundaries intact, also 1,000 iterations.  
- **Significance**: Two‑sided p‑value = proportion of permuted accuracies ≥ observed accuracy.  
- **Correction**: Benjamini‑Hochberg FDR (α = 0.05) applied to the set of p‑values from the K‑sweep (K = 50, 100, 150) (FR‑012).

### 2. Power Analysis & MDES
- When observed accuracy ≤ random‑chance baseline (1 / N), a **post‑hoc power analysis** is performed.  
- **MDES** computed via normal approximation for difference in proportions with α = 0.05, using the effective sample size of the held‑out dataset.  
- **Power** estimated for detecting an effect size of 0.15 (Cohen’s h) given observed class balance. Results stored in `results/model_metrics.json` (SC‑005).

### 3. Measurement Validity
- Stress labels are taken directly from GEO sample metadata fields (`characteristics_ch1`). Samples lacking a clear stress annotation are written to `invalid_samples.csv` (FR‑013) and excluded.  
- Gene identifiers are mapped to Ensembl IDs via **mygene**; mapping success rate > 90 % is required; otherwise abort (FR‑004).

### 4. Collinearity & Stability
- Logistic regression coefficients are extracted for each bootstrap replicate (100 resamples).  
- **Variance** of each coefficient across bootstraps is computed; genes with variance ≤ 0.30 and selection frequency ≥ 0.70 are flagged as robust biomarkers (FR‑010, SC‑003).  
- No explicit VIF check is needed because the stability metric already accounts for correlated predictors.

### 5. Dataset‑Variable Fit & Label Space Harmonization
- After intersection, the final **FeatureSpace** contains ≥ 1,500 genes (Edge Case).  
- The stress label space used for classification is the **intersection** of stress types present across all *included* datasets; if a stress is missing from any dataset, it is omitted and the chance baseline is recomputed accordingly (addressing edge case of single‑stress dataset).

### 6. Batch‑Effect Confounding Check
- Prior to any correction, a chi‑square test of independence between `dataset_id` and `stress_type` is performed.  
- If **p < 0.01**, indicating perfect confounding, the pipeline aborts with `E‑BATCH‑CONFOUNDING` (new safety gate). This prevents removal of true biological signal by batch correction.

### 7. Unsupervised Validation
- UMAP (2‑D, n_neighbors = 15, min_dist = 0.1) is run on the **batch‑corrected** held‑out test matrix (no additional correction).  
- Silhouette scores computed for (a) stress‑type labels and (b) dataset‑ID labels.  
- Success criteria: stress‑type Silhouette ≥ 0.40 for at least three classes **and** Δ ≥ 0.10 (stress – dataset) (SC‑004).

## Expected Outputs
- `results/model_metrics.json` – all performance metrics, permutation p‑values, FDR‑adjusted q‑values, power, MDES, confusion matrix.  
- `results/robust_biomarkers.csv` – gene IDs, coefficient variance, selection frequency.  
- `results/umap_plot.png` & `results/embedding_coords.csv` – visual and numeric UMAP outputs.  
- `invalid_samples.csv` – samples excluded due to missing/contradictory metadata.  
- Updated `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` with hashes and `research_complete: true`.  
- PDF/HTML report containing sections required by US‑5, all framed associationally.

All artefacts are version‑hashed and referenced in the state file, satisfying Constitution Principle V.

## Decision Log (excerpt)

| Decision | Rationale |
|----------|-----------|
| Programmatic GEO discovery (GEOparse) | Uses verified primary source; no fabricated URLs (Principle II). |
| Abort if < 7 qualifying series | Directly mandated by FR‑017; prevents downstream speculation. |
| Strict gene‑intersection (≥ 1,500) | Enforces Principle VII; avoids batch‑specific features. |
| LODO CV without batch correction (primary) | Guarantees genuine cross‑dataset validation per Principle VI. |
| Bootstrap stability of coefficients | Provides quantitative robust biomarker criterion (US‑2). |
| Two‑level permutation testing + FDR | Controls family‑wise error (FR‑012). |
| Post‑hoc MDES & power | Enables interpretation of null results (SC‑005). |
| Fixed random seed (`seed=42`) | Ensures reproducibility (Principle I). |
| Resource guardrails (RAM ≤ 7 GB, runtime ≤ 6 h) | Satisfies FR‑016; prevents CI timeouts. |
