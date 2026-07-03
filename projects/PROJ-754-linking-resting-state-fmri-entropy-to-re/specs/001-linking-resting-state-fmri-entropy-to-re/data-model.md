# Data Model: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Overview
The project manipulates three primary data tiers:

| Tier | Description | Primary File(s) | Format |
|------|-------------|-----------------|--------|
| **Raw** | Original downloads (HCP time series, DSRT scores) | `data/raw/hcp_timeseries.parquet`, `data/raw/dsrt_scores.parquet` | Parquet |
| **Derived** | Quality‑controlled time series, entropy matrix, covariate table | `data/derived/clean_subjects.parquet`, `data/derived/entropy_matrix.parquet`, `data/derived/covariates.parquet` | Parquet |
| **Results** | Statistical outputs, neuroimaging maps, report | `results/model_coefficients.csv`, `results/significant_parcels.nii.gz`, `reports/link_entropy_risk.pdf` | CSV / NIfTI / PDF |

## Entity Definitions

| Entity | Attributes | Data Type | Notes |
|--------|------------|-----------|-------|
| **Subject** | `subject_id` (str), `age` (int), `sex` (categorical: "M"/"F"), `mean_fd` (float), `dsrt_score` (float) | Primary key `subject_id` | All covariates required for modeling; rows with missing `dsrt_score` are excluded. |
| **Parcel** | `parcel_id` (int), `parcel_name` (str) | Fixed 400‑parcel Schaefer atlas | Used for indexing entropy and statistical maps. |
| **EntropyMetric** | `subject_id` (FK), `parcel_id` (FK), `entropy` (float) | One row per subject‑parcel pair | Computed as mean of multiscale sample entropy across scales 1‑5. |
| **StatResult** | `parcel_id` (FK), `beta_entropy` (float), `se_entropy` (float), `t_entropy` (float), `p_raw` (float), `p_fwe` (float), `significant` (bool) | One row per parcel | Generated after permutation testing. |
| **SensitivityRecord** | `r` (float), `m` (int), `significant_parcels` (int) | Aggregated counts per parameter combo | Supports FR‑008. |
| **PowerAnalysis** | `effect_size_d` (float), `n_subjects` (int), `alpha` (float), `power` (float) | Single summary row | Used for SC‑006. |

## Relationships
- **Subject ↔ EntropyMetric**: One‑to‑many (subject has 400 entropy values).  
- **Parcel ↔ EntropyMetric**: One‑to‑many (parcel has entropy for each subject).  
- **Parcel ↔ StatResult**: One‑to‑one (each parcel yields a statistical summary).  

All tables include a SHA‑256 checksum column (`checksum`) stored in `data/checksums.txt` for reproducibility (Constitution III).

---
