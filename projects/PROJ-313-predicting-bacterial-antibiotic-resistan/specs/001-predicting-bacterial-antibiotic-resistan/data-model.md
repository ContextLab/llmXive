# Data Model: Predicting Bacterial Antibiotic Resistance

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **Isolate** | `isolate_id` (str, PK) <br> `species` (enum: `E_coli`, `S_aureus`) <br> `assembly_path` (str) <br> `phenotype_label` (enum: `resistant`, `sensitive`) <br> `antibiotic` (str) <br> `geography` (str) <br> `collection_date` (date) <br> `sequencing_platform` (enum: `Illumina`, `Nanopore`, `PacBio`) | One bacterial sample with its genome assembly, phenotype, and potential confounders. |
| **ARGPresence** | `isolate_id` (FK) <br> `arg_name` (str) <br> `present` (bool) | Binary indicator for each CARD resistance gene. |
| **SNPCount** | `isolate_id` (FK) <br> `gene_or_region` (str) <br> `snp_count` (int) | SNP count per gene/region **excluding any SNP that overlaps an ARG locus** (to avoid collinearity). |
| **MGEDistance** | `isolate_id` (FK) <br> `mge_type` (enum: `plasmid`, `transposon`) <br> `distance_bp` (float) | Genomic distance (bp) from the nearest MGE to each ARG; later binned (`<1kb`, `1‑5kb`, `>5kb`). |
| **Confounder** | `isolate_id` (FK) <br> `geography` (str) <br> `collection_date` (date) <br> `sequencing_platform` (enum) | Metadata that may correlate with both genotype and phenotype. |
| **FeatureVector** | `isolate_id` (FK) <br> `features` (dict) – keys: `arg_*`, `snp_*`, `mge_*`, `conf_*` <br> `scaled_features` (np.ndarray[float]) | Consolidated, standardized feature set used for model training. After selection, ≤ 500 features (optional PCA ≤ 100 PCs). |
| **ModelArtifact** | `model_id` (str, UUID) <br> `species` (enum) <br> `antibiotic` (str) <br> `model_type` (enum: `xgboost_baseline`, `xgboost_integrated`) <br> `training_date` (date) <br> `cv_metrics` (list of dict) | Stores trained classifier and per‑fold metrics. |
| **StatTestResult** | `test_id` (str) <br> `feature_name` (str) <br> `test_type` (enum: `mannwhitney`, `permutation`) <br> `raw_p` (float) <br> `adj_p` (float) <br> `significant` (bool) | Result of statistical validation for each feature. |

## File‑Based Representations

| File | Format | Content |
|------|--------|---------|
| `raw/synthetic_assemblies/*.fasta` | FASTA | Synthetic genome assemblies (generated in Phase 0‑a). |
| `raw/synthetic_phenotypes.parquet` | Parquet | Isolate metadata, phenotype labels, and confounder fields. |
| `processed/arg_matrix.csv` | CSV | Rows = isolates; columns = binary ARG presence. |
| `processed/snp_counts.csv` | CSV | Rows = isolates; columns = SNP counts per gene/region (ARG‑overlap excluded). |
| `processed/mge_distances.csv` | CSV | Rows = isolates; columns = binned MGE distance features. |
| `processed/confounders.csv` | CSV | Rows = isolates; columns = geography, collection_date, sequencing_platform. |
| `processed/selected_features.npy` | NumPy binary | Scaled, dimension‑reduced feature matrix (≤ 500 features, optional PCA ≤ 100 PCs). |
| `reports/metrics.json` | JSON | Conforms to `contracts/metrics.schema.yaml`. |
| `reports/summary.txt` | Text | Checksum logs, sample‑size table, power analysis, edge‑case warnings. |

All files are immutable after creation; each transformation writes a new file with a provenance header (script name, timestamp, input checksum) to satisfy **Data Hygiene** (Constitution III).
