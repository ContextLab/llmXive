# Research: 001-gene-regulation

## Dataset Strategy

The project relies on NCBI Gene Expression Omnibus (GEO) datasets. Because no verified HuggingFace URLs exist for the required plant stress series, the pipeline fetches raw count matrices and metadata directly from the NCBI GEO FTP server (`ftp.ncbi.nlm.nih.gov/geo/series/...`).  

### Verification Workflow
1. **Download** each accession via `wget`/`curl`.  
2. **Checksum** the downloaded archive (SHA‑256) and record it in `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml`.  
3. **Parse metadata** to confirm:  
   - **Organism** is a plant (e.g., *Arabidopsis thaliana*, *Oryza sativa*, *Zea mays*).  
   - **Stress labels** include at least two of the four target stresses (drought, salinity, heat, cold) **and** a control condition.  
4. **Inclusion flag** (`included: true`) is set only when both criteria are met; otherwise the dataset is excluded and logged (`logs/exclusion.log`).  
   - **GSE40677**: Explicitly excluded as a human cancer dataset (non‑plant).

### Candidate GEO Accessions (post‑verification)
| Dataset ID | Stress Types Present | Verification Outcome |
|------------|----------------------|----------------------|
| GSE30047   | drought, heat, control | Included |
| GSE51148   | salinity, cold, control | Included |
| GSE59991   | drought, salinity, heat, cold, control | Included |
| GSE66904   | drought, salinity, heat, cold, control | Included |
| GSE40677   | **Excluded** – human cancer dataset (non‑plant) | N/A |

*If any accession fails verification (e.g., missing plant taxonomy), the pipeline aborts with a “Data Unavailable” error.*

## Methodological Rigor & Statistical Plan

### 1. Hypothesis Testing & Multiple Comparisons
- **Primary hypothesis**: Stress signatures are separable across datasets.  
- **Metric**: Classification accuracy (cross‑dataset).  
- **Global Permutation Baseline**: To address the high variance of LODO with small N (N=5), stress labels are permuted **across datasets** (shuffling labels among samples from different datasets while keeping the dataset ID fixed) 1000 times. This preserves the batch structure but breaks the biological signal, generating a null distribution for the cross-dataset accuracy metric.  
- **Permutation Test**: For each LODO fold, stress labels are **permuted within each training dataset** 1000 times (preserving batch‑condition structure) to assess within-fold significance.  
- **Multiple‑comparison correction**: Benjamini‑Hochberg FDR applied to the set of p‑values obtained for each stress‑pair accuracy test.

### 2. Power Analysis & Minimum Detectable Effect Size (MDES)
- Because sample sizes are fixed, a formal a priori power analysis is infeasible.  
- **Post‑hoc power**: Bootstrapped resampling of the training data estimates the probability of detecting a given accuracy lift over chance.  
- **MDES**: Computed as the smallest accuracy improvement over the random‑chance baseline that yields ≥80 % power given the observed sample size. Results are reported in `results/model_metrics.json`. If observed accuracy ≤ MDES, the result is flagged “Underpowered – Cannot Distinguish Weak Signal from Noise”.

### 3. Measurement Validity
- **Stress labels**: Validated against GEO metadata fields (`duration`, `severity`). Samples with missing or inconsistent severity are excluded per FR‑012.  
- **Gene identifiers**: Mapped via Biopython; failure to map >10 % of genes triggers a “Feature Space Insufficient” halt.

### 4. Collinearity & Feature Importance Stability
- **Stability Selection**: 1000 bootstrap replicates of the training data; Random Forest feature importances are computed for each replicate.  
- **Stability Score**: Frequency a gene appears in the top‑50 importance list across bootstraps (0  – 1). Only genes with **Stability > 0.8** are reported as robust biomarkers.  
- This metric replaces any optional VIF check and satisfies the need for a quantitative stability assessment in the presence of correlated gene modules.

### 5. Dataset‑Variable Fit & Label Space Harmonization
- After verification, the **stress label space** is the *intersection* of stress types present across all **included** datasets.  
- If a stress type is missing from any dataset, it is omitted from the multi‑class task, and the chance‑level baseline is recomputed accordingly (e.g., 3‑class vs. 4‑class).  
- Class imbalance is addressed via stratified sampling and class‑weighting in the Random Forest (`class_weight='balanced'`).

### 6. Batch‑Effect Correction & Confounding Check
- **Pre-ComBat Confounding Check**: Before any correction, a chi-square test checks whether “batch” (dataset) and “condition” (stress) are perfectly aligned. If p < 0.01 (high confounding), the pipeline halts with a specific error to prevent the removal of biological signal. This is a proactive gate.  
- **Within‑fold ComBat**: For each LODO iteration, batch parameters are estimated on the training set and applied to the held‑out test set only. This ensures the test set is never corrected using its own information, preventing circular validation.

### 7. Unsupervised Validation
- **UMAP** (or t‑SNE) is run on the **batch‑corrected test set** of each LODO fold.  
- **Silhouette Score** > 0.4 for at least 3 of the stress clusters is required (SC‑004).  
- Visualizations color samples by stress type and by dataset source to assess cross‑dataset overlap.

## Expected Outputs

- `results/model_metrics.json` – contains within‑ and cross‑dataset metrics, null distribution stats, stability scores, MDES, and post‑hoc power.  
- `results/confusion_matrix.png` – visual confusion matrix for each LODO fold.  
- `results/umap_plot.png` – UMAP embedding with dual coloring.  
- `data/processed/feature_space.csv` – list of intersecting genes and top‑1500 variable genes.  

All outputs are version‑hashed and referenced in the project state file to satisfy Constitution Principle V.

## Decision Log (excerpt)

| Decision | Rationale |
|----------|-----------|
| Direct NCBI GEO fetch | Primary source verification satisfies Constitution Principle II; no fabricated URLs. |
| [deferred] Gene Intersection | Required by Constitution Principle VII; eliminates batch‑specific artifacts. |
| LODO CV with intra‑fold batch correction | Guarantees genuine cross‑dataset generalization testing (Principle VI) and prevents circular validation. |
| Stability Selection & Stability Score | Provides robust biomarker identification despite collinearity. |
| Post‑hoc power & MDES | Enables interpretation of null results (distinguish “no signal” vs. “underpowered”). |
| Pre-ComBat Confounding Check | Proactive gate to prevent removal of true biological signal when batch and condition are aligned. |
| Exclusion of non‑plant or single‑stress datasets | Ensures relevance to the plant stress hypothesis. |