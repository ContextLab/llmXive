# Research: Can Publicly Available Microbiome Data Predict Host Plant Defense Responses?

## Objective
Determine whether the composition of the leaf‑associated microbiome (16S rRNA amplicon) can predict concentrations of defense metabolites in *Arabidopsis thaliana* and *Solanum lycopersicum* under herbivore stress.

## Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **Data Sources** | Only the SRA parquet URLs are verified. No verified MetaboLights URL exists, so metabolomics data cannot be automatically retrieved. We therefore place a **hard guard** (Phase 0) that aborts if metabolomics data are missing, preserving reproducibility and avoiding fabricated data. |
| **Open 16S Dataset** | A placeholder note indicates that an open, verified 16S ASV dataset must be supplied (pending URL). When available, it will replace the current guard and enable real microbiome features. |
| **Compute Platform** | All analysis steps are CPU‑only and fit comfortably within a multi‑core, several‑gigabyte RAM GitHub Actions runner. No GPU escape hatch is required. |
| **Statistical Approach** | Multi‑output Random Forest with leave‑one‑study‑out cross‑validation using multiple folds provides unbiased performance estimates for observational data. Permutation testing (with a sufficient number of iterations) supplies a proper null distribution for the R² metric. PCA is fit inside each CV training fold to avoid leakage (FR‑009). Species is included as a one‑hot covariate to control for confounding. |
| **Sensitivity** | Sweeping the PCA variance‑retention threshold (80 %, 90 %, 95 %) **and** key Random Forest hyper‑parameters (n_estimators, max_features) directly addresses SC‑002 and ensures robustness to modeling choices. |
| **Power & Sample‑Size** | A minimum of 30 usable samples is enforced (FR‑008). After modeling, we compute effect‑size‑based post‑hoc power and report it alongside R², acknowledging limited power when sample size is low. |
| **Reproducibility** | Random seeds are fixed (`np.random.seed(42)`, `random_state=42` in scikit‑learn). All intermediate files are version‑controlled with checksums. |

## Dataset Strategy
| Data Modality | Verified Source | Loader | Notes |
|---------------|----------------|--------|-------|
| 16S rRNA amplicon (raw reads) | **None** (current placeholder; open ASV dataset pending) | – | Phase 0 will abort with “Missing metabolomics data – cannot proceed.” once a verified 16S source is added, the guard will be lifted. |
| Metabolomics (defense compounds) | **None** (MetaboLights not verified) | – | Phase 0 will abort with “Missing metabolomics data – cannot proceed.” |

> **Important**: The lack of verified metabolomics (and currently 16S) sources is a **blocking limitation**. When open datasets become available with verified URLs, the guards can be removed and the pipeline will continue automatically.

## Methodology Overview
1. **Data Acquisition** – download SRA parquet (or open ASV dataset when available), checksum, store under `data/raw/`.  
2. **Pre‑processing** – optional DADA2 denoising of 16S reads (executed only if raw reads are present); otherwise load pre‑computed ASV table; median‑scale metabolite intensities (when available).  
3. **Metadata Normalization** – canonicalize “herbivore stress” labels (e.g., `herbivore_stress`, `herbivore`, `damage`).  
4. **Missing‑Data Assessment** – quantify missingness per modality, report bias, optionally impute (median for metabolites, zero for ASVs) before dropping irrecoverable rows; log excluded count.  
5. **Integration** – inner join on `sample_id`, `species`, `condition`; enforce one‑to‑one match; drop rows only after assessment.  
6. **Modeling** – leave‑one‑study‑out 5‑fold CV; within each training fold: PCA (retain [deferred] variance) → PC scores; concatenate one‑hot species encoding; train multi‑output Random Forest (`MultiOutputRegressor(RandomForestRegressor)`). Record per‑metabolite R², mean R², and species‑stratified performance.
7. **Permutation Test** – 200 label permutations per fold (within‑fold), refit PCA & RF, compute R²; build null distribution, compute one‑sided p‑value. Parallelise across cores.  
8. **Sensitivity Sweep** – repeat step 6 for variance thresholds 0.80, 0.90, 0.95 **and** RF `n_estimators` ∈ {200, 500}, `max_features` ∈ {'sqrt', 0.5}. Summarise R² per configuration.  
9. **Power Analysis** – after CV, compute effect‑size‑based power given observed R² and sample size; report alongside results.  
10. **Reporting** – per‑metabolite R², mean R², species‑stratified tables, feature‑importance (top 10 PCs), regression plots, sensitivity table, power summary, and a markdown summary.  

All steps are implemented as pure functions in `code/` and are orchestrated by a top‑level CLI (`python -m pipeline.run`).

## Expected Deliverables
- `data/merged/merged_dataset.csv` adhering to `contracts/merged-dataset.schema.yaml`.  
- `results/cv_metrics.json` (per‑metabolite R², mean R², species‑stratified R²).  
- `results/permutation_pvalue.txt`.  
- `results/sensitivity_table.csv`.  
- `results/power_summary.txt`.  
- Figures in `figures/` (regression scatter, feature importance, sensitivity line plot, species‑performance bar chart).  
- Unit‑test suite under `tests/` validating FR‑008 guard, contract compliance, and power‑analysis output.

---

