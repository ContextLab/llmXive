# Data Model: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Overview
Defines the entities, transformations, and JSON schemas that govern every artifact produced by the pipeline. All files are validated against the schemas in `contracts/` using Pydantic models; failures abort the run, guaranteeing Constitution Principle III (Data Hygiene).

## Core Entities

| Entity | Fields | Description |
|--------|--------|-------------|
| **Species** | `species_name` (str), `phylogenetic_clade` (str), `genome_status` (str), `metabolome_status` (str), `genome_size_mb` (float) | Metadata for each plant; used for filtering and stratification. |
| **BGCFeature** | `species_name` (str), `bgc_type` (str), `count` (int), `presence` (bool), `mapping_source` (str) | One row per BGC type per species; counts derived from antiSMASH JSON. |
| **MetaboliteTarget** | `species_name` (str), `inchikey` (str), `abundance_raw` (float), `abundance_log` (float), `compound_class` (str) | Harmonized metabolite data; log‑transformed for modeling. |
| **Covariate** | `species_name` (str), `ecological_niche` (str, optional), `tissue_type` (str, optional), `growth_habit` (str, optional) | Additional non‑phylogenetic covariates retrieved from the TRY Plant Trait Database. |
| **AlignedRecord** | `species_id` (str), `clade` (str), `bgc_features` (dict\<bgc_type → int\>), `metabolite_targets` (dict\<InChIKey → float\>), `covariates` (dict\<cov_name → value\>) | Single row of the final feature‑target matrix (output of alignment). |
| **ModelOutput** | `model_type` (str), `r_squared` (float), `pearson_r` (float), `p_value` (float), `feature_importance` (dict\<feature → score\>), `cross_val_scores` (list\<float\>), `cv_method` (str) | Results from each regression model, ready for SSoT. |

## Data Flow Diagram
1. **Raw Input** – FASTA/GFF (genomes) + CSV/TSV (metabolites) + TSV (covariates).  
2. **Intermediate** – `bgc_predictions.json`, `metabolite_harmonized.csv`, `covariates.tsv`, `tree_pruned.nwk`.  
3. **Processed** – `aligned_matrix.csv` (conforms to `aligned_dataset.schema.yaml`).  
4. **Final** – `model_metrics.json` (conforms to `model_output.schema.yaml`).  

## Validation & Hygiene
- **Schema Validation** – After each major step (`download`, `antismash`, `align`, `train`, `evaluate`) the produced file is validated against its corresponding schema in `contracts/`.  
- **Checksums** – SHA‑256 checksums are computed for all raw and derived files; stored in project state (`state/projects/...yaml`).  
- **Zero‑BGC Handling** – Species with zero predicted BGCs are retained (`count = 0`, `presence = false`).  
- **Missing Modality** – Species lacking genome **or** metabolite data are excluded; a warning is logged.  
- **Numeric Ranges** – R² ∈ [‑1, 1]; counts ≥ 0; log‑abundances bounded by realistic limits (‑1000 → 1000).  

## Contracts Referenced
- `contracts/aligned_dataset.schema.yaml` – validates the final aligned matrix.  
- `contracts/model_output.schema.yaml` – validates each model’s result object.  

---

