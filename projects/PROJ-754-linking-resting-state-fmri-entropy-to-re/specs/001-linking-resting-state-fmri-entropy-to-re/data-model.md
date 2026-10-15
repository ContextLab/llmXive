# Data Model: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Overview
The project manipulates three data tiers (Raw → Derived → Results). All tables are stored as Parquet (or CSV for logs) and accompanied by SHA‑256 checksums recorded in `data/checksums.txt`.

| Tier | Primary Files | Format |
|------|---------------|--------|
| **Raw** | `data/raw/hcp_timeseries.parquet`, `data/raw/dsrt_scores.parquet` | Parquet |
| **Derived** | `data/derived/clean_subjects.parquet`, `data/derived/subject_qc.csv`, `data/derived/entropy_matrix.parquet`, `data/derived/invalid_parcels.csv` | Parquet / CSV |
| **Results** | `results/model_coefficients.csv`, `results/significant_parcels.nii.gz`, `results/power_analysis.csv`, `reports/link_entropy_risk.pdf` | CSV / NIfTI / PDF |

## Entity Definitions

| Entity | Attributes | Data Type | Notes |
|--------|------------|-----------|-------|
| **Subject** | `subject_id` (str), `age` (int), `sex` (str: "M"/"F"), `mean_fd` (float), `dsrt_score` (float) | Primary key `subject_id` | Rows failing QC are omitted from `clean_subjects.parquet`. |
| **Parcel** | `parcel_id` (int, 1‑400), `parcel_name` (str) | Fixed atlas (Schaefer‑400) | Used for indexing entropy and statistical maps. |
| **EntropyMetric** | `subject_id` (FK), `parcel_id` (FK), `entropy` (float) | One row per subject‑parcel pair | Averaged across scales 1‑5. |
| **StatResult** | `parcel_id` (FK), `beta_entropy` (float), `se_entropy` (float), `t_entropy` (float), `p_raw` (float), `p_fwe` (float), `significant` (bool), `vif` (float) | One row per parcel | Produced after permutation testing. |
| **SensitivityRecord** | `r` (float), `m` (int), `significant_parcels` (int) | Aggregated counts per parameter combo | Supports FR‑008. |
| **PowerAnalysis** | `effect_size_f2` (float), `n_subjects` (int), `alpha` (float), `power` (float) | Single summary row | Used for SC‑006. |

## Relationships
- **Subject ↔ EntropyMetric**: One‑to‑many (each subject has 400 entropy values).  
- **Parcel ↔ EntropyMetric**: One‑to‑many (each parcel has entropy for all subjects).  
- **Parcel ↔ StatResult**: One‑to‑one (each parcel yields a statistical summary).  

All derived tables include a `checksum` column (SHA‑256) for reproducibility (Constitution III).

---
