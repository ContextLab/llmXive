# Data Model: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## 1. Entities & Relationships

| Entity | Key Attributes | Relationships |
|--------|----------------|---------------|
| **Subject** | `subject_id` (string), `status` (`processed`/`skipped`/`error`) | Owns one **Structural Connectome**, one **Functional Connectome**, one **Motif Profile**, one **Structural Metadata** |
| **Structural Connectome** | `structural.npy` (binary 100 × 100 float32) | Belongs to a **Subject** |
| **Functional Connectome** | `rsfc.npy` (float32 100 × 100) | Belongs to a **Subject** |
| **Motif Profile** | JSON: `{motif_type: z_score}` for multiple motifs | Belongs to a **Subject** |
| **Structural Metadata** | JSON conforming to `structural_connectome.schema.yaml` (includes seed, status, file paths) | Belongs to a **Subject** |
| **Covariates** | CSV rows: `subject_id, age, sex, head_motion, scanner_site` | Linked to **Subject** (used in regression) |
| **Correlation Result** | JSON/CSV row per motif‑metric pair (partial Pearson & Spearman, VIF, method) | Aggregates across **Subjects** |
| **Manifest** | Cohort‑level summary (`cohort_target`, `cohort_actual`, `cohort_skipped`, `subjects[]`, `checksums`) | Global view of all **Subject** records |

## 2. File Formats & Schemas

- **Raw Data**  
  - `data/raw/<subject_id>/structural.nii.gz` (original HCP diffusion)  
  - `data/raw/<subject_id>/rsfmri.nii.gz` (original HCP rs‑fMRI)

- **Processed Data**  
  - `data/processed/<subject_id>/structural.npy` (binary adjacency)  
  - `data/processed/<subject_id>/rsfc.npy` (Pearson correlation matrix)  
  - `data/processed/<subject_id>/motif_profile.json` (z‑scores for a set of motifs)  
  - `data/processed/<subject_id>/metadata.json` (conforms to `structural_connectome.schema.yaml`)  
  - `data/processed/manifest.json` (overall cohort status)

- **Covariates**  
  - `data/processed/covariates.csv` (age, sex, head‑motion, scanner site for each subject)

- **Outputs**  
  - `results/results.pdf` (final report)  
  - `data/processed/correlation_results.json` (statistical summary)  
  - `data/logs/pipeline.log` (machine‑readable log)

Schema files are located in `contracts/` and define the exact JSON structures for the manifest, motif profile, analysis results, and structural metadata.

## 3. Data Flow Diagram

1. **Ingestion** (`data_loader.py`) → Raw HCP files → `data/raw/`.
2. **Parcellation** (`data_loader.py`) → `structural.npy` (binary undirected) stored under `data/processed/`.
3. **Functional Calculation** (`data_loader.py`) → `rsfc.npy` + thresholding → `efficiency.csv`.
4. **Motif Enumeration** (`motif_analysis.py`) → `motif_profile.json`.
5. **Metadata Generation** (`utils.py`) → `metadata.json` per subject (matches `structural_connectome.schema.yaml`).
6. **Covariate Loading** (`utils.py`) → `covariates.csv`.
7. **Statistical Modeling** (`correlation_analysis.py`) → `correlation_results.json`.
8. **Reporting** (`report_generator.py`) → `results.pdf`.
9. **Logging** (`utils.py`) → `pipeline.log` throughout all steps.

## 4. Validation & Logging (Task T017)

- **utils.py** validates constants at start‑up (`seed=42`, `bonferroni_alpha=0.0125`, `permutation_count=1000`, `vif_threshold=5`).  
- **pipeline.log** records every major step, warnings (e.g., missing modality), errors, and the final success summary.  
- **Manifest** captures `cohort_actual` vs. `cohort_target` to enforce **SC‑001** (≥ 95 % success).  

---

