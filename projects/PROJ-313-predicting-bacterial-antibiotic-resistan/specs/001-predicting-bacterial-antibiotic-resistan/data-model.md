# Data Model: Predicting Bacterial Antibiotic Resistance

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **Isolate** | `isolate_id` (str, primary key) <br> `species` (enum: `E_coli`, `S_aureus`) <br> `assembly_path` (str) <br> `phenotype_label` (enum: `resistant`, `sensitive`) <br> `antibiotic` (str) <br> `ast_value` (float) | Represents a single bacterial genome with a phenotypic AST measurement. |
| **ARGPresence** | `isolate_id` (FK) <br> `arg_name` (str) <br> `present` (bool) | Binary indicator for each CARD resistance gene. |
| **SNPCount** | `isolate_id` (FK) <br> `gene_or_region` (str) <br> `snp_count` (int) | Number of SNPs observed in the given gene or intergenic region after alignment to the core reference. **SNPs that overlap any ARG locus are excluded** to avoid collinearity (see methodology‑e442d9de). |
| **MGEDistance** | `isolate_id` (FK) <br> `mge_type` (enum: `plasmid`, `transposon`) <br> `distance_bp` (float) | Genomic distance (base pairs) from the nearest MGE to each ARG; binned into categorical bins (`<1kb`, `1-5kb`, `>5kb`). |
| **FeatureVector** | `isolate_id` (FK) <br> `features` (dict) – keys: `arg_*`, `snp_*`, `mge_*` <br> `scaled_features` (array[float]) | Consolidated, standardized feature set used for model training. After feature selection, only the top‑500 non‑redundant features are retained; an optional PCA step may further reduce dimensionality to ≤ 100 components. |
| **ModelArtifact** | `model_id` (str, UUID) <br> `species` (enum) <br> `antibiotic` (str) <br> `model_type` (`xgboost`) <br> `training_date` (date) <br> `cv_metrics` (list of dict) | Stores trained XGBoost model and per‑fold cross‑validation metrics. |
| **StatTestResult** | `test_id` (str) <br> `feature_name` (str) <br> `test_type` (enum: `mannwhitney`, `permutation`) <br> `raw_p` (float) <br> `adj_p` (float) <br> `significant` (bool) | Results of statistical validation for each feature. |

## File‑Based Representations

| File | Format | Content |
|------|--------|---------|
| `raw/ncbi_parquet/*.parquet` | Parquet | Raw isolate metadata, assembly URLs, AST columns (verified source). |
| `processed/arg_matrix.csv` | CSV | Rows = isolates; columns = binary ARG presence. |
| `processed/snp_counts.csv` | CSV | Rows = isolates; columns = SNP count per gene/region (ARG‑overlap excluded). |
| `processed/mge_distances.csv` | CSV | Rows = isolates; columns = binned distance features. |
| `processed/selected_features.npy` | NumPy binary | Scaled, dimension‑reduced feature matrix (≤ 500 features, optional PCA to ≤ 100 PCs) for XGBoost. |
| `reports/metrics.json` | JSON | Conforms to `contracts/metrics.schema.yaml`. |
| `reports/summary.txt` | Text | Checksum logs, sample‑size notes, edge‑case warnings. |

All files are **immutable** after creation; each transformation writes a new file with a provenance header (script name, timestamp, input checksum).

---


