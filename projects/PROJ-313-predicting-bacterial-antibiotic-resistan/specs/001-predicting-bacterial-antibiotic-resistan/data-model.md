# Data Model: Predicting Bacterial Antibiotic Resistance (Real‑Data Pipeline)

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **Isolate** | `isolate_id` (str, PK) <br> `species` (enum: `E_coli`, `S_aureus`) <br> `assembly_path` (str) <br> `phenotype_label` (enum: `resistant`, `sensitive`) <br> `antibiotic` (str) <br> `geography` (str) <br> `collection_year` (int) <br> `sequencing_platform` (enum: `Illumina`, `Nanopore`, `PacBio`) | One bacterial sample with its real genome assembly, phenotype, and confounders. |
| **ARGPresence** | `isolate_id` (FK) <br> `arg_name` (str) <br> `present` (bool) | Binary indicator for each CARD resistance gene. |
| **SNPCount** | `isolate_id` (FK) <br> `gene_or_region` (str) <br> `snp_count` (int) | SNP count per gene/region **excluding any SNP that overlaps an ARG locus** (real extraction). |
| **MGEDistance** | `isolate_id` (FK) <br> `mge_type` (enum: `plasmid`, `transposon`) <br> `distance_bp` (float) | Genomic distance (bp) from the nearest simulated MGE to each ARG; later binned (`<1kb`, `1‑5kb`, `>5kb`). |
| **Confounder** | `isolate_id` (FK) <br> `geography` (str) <br> `collection_year` (int) <br> `sequencing_platform` (enum) | Metadata that may correlate with both genotype and phenotype. |
| **FeatureVector** | `isolate_id` (FK) <br> `features` (dict) – keys: `arg_*`, `snp_*`, `mge_*`, `conf_*` <br> `scaled_features` (np.ndarray[float]) | Consolidated, standardized feature set used for model training (≤ 500 features after optional PCA). |
| **ModelArtifact** | `model_id` (str, UUID) <br> `species` (enum) <br> `antibiotic` (str) <br> `model_type` (enum: `xgboost_baseline`, `xgboost_integrated`, `rf_baseline`, `rf_integrated`) <br> `training_date` (date) <br> `cv_metrics` (list of dict) | Stores trained classifier and per‑fold metrics. |
| **StatTestResult** | `test_id` (str) <br> `feature_name` (str) <br> `test_type` (enum: `mannwhitney`, `permutation`, `wilcoxon`) <br> `raw_p` (float) <br> `adj_p` (float) <br> `significant` (bool) | Result of statistical validation for each feature or model comparison. |

## File‑Based Representations

| File | Format | Content |
|------|--------|---------|
| `raw/assemblies/*.fasta` | FASTA | Real genome assemblies downloaded from NCBI. |
| `raw/phenotypes.parquet` | Parquet | Isolate metadata, phenotype labels, confounder fields extracted from NCBI. |
| `processed/arg_matrix.csv` | CSV | Rows = isolates; columns = binary ARG presence. |
| `processed/snp_counts.csv` | CSV | Rows = isolates; columns = SNP counts per gene/region. |
| `processed/mge_distances.csv` | CSV | Rows = isolates; columns = binned MGE distance features. |
| `processed/confounders.csv` | CSV | Rows = isolates; columns = geography, collection_year, sequencing_platform. |
| `processed/selected_features.npy` | NumPy binary | Scaled, optionally PCA‑reduced feature matrix (≤ 500 features). |
| `reports/metrics.json` | JSON | Conforms to `contracts/metrics.schema.yaml`. |
| `reports/summary.txt` | Text | Checksum logs, sample‑size table, power analysis, edge‑case warnings. |

All files are **immutable after creation**; each transformation writes a new file with a provenance header (script name, timestamp, input checksum) to satisfy **Data Hygiene** (Constitution III).

### Confounder Encoding Details (new)
- **Geography**: one‑hot encoded across a fixed set (e.g., `geo_US`, `geo_EU`, `geo_AS`).  
- **Sequencing Platform**: one‑hot encoded (`platform_Illumina`, `platform_Nanopore`, `platform_PacBio`).  
- **Collection Year**: integer (e.g., 2020, 2021) treated as a continuous covariate.  

These columns are merged into the `FeatureVector` under the `conf_*` namespace and supplied as covariates to the `pyseer` mixed‑effects model and permutation‑importance routine, satisfying FR‑017.

---

