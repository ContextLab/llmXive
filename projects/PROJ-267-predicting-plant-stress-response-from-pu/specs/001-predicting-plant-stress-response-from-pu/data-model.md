# Data Model: Predicting Plant Stress Response from Publicly Available Proteomic Data

## 1. Entity Relationship Overview
The model captures the flow from raw proteomic / transcriptomic files to a unified training matrix and final model artefacts.

### Key Entities
- **ProteomicSample** – protein abundance vector for a single plant sample.  
- **TranscriptomicSample** – gene expression vector for the same sample.  
- **StressCondition** – categorical label (`Drought`, `Salinity`, `Heat`).  
- **UnifiedMatrix** – rows = samples; columns = normalized protein features; target = gene expression value.  

## 2. Data Flow
1. **Raw Ingestion** → `data/raw/` (downloaded files).  
2. **Preprocessing** (filter, impute, map IDs) → `data/processed/unified_matrix.csv`.  
3. **Modeling** (split, train, evaluate) → `results/models/` & `results/figures/`.  

## 3. Schema Definitions

### 3.1 Raw Proteomic Schema
| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | string | Unique identifier. |
| `protein_id` | string | UniProt accession. |
| `abundance` | number | Raw intensity. |
| `stress` | string | `Drought`, `Salinity`, or `Heat`. |
| `species` | string | `Arabidopsis`, `Rice`, or `Wheat`. |

### 3.2 Raw Transcriptomic Schema
| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | string | Must match proteomic `sample_id`. |
| `gene_id` | string | Ensembl gene accession. |
| `expression` | number | TPM/FPKM value. |
| `stress` | string | Same as proteomic. |
| `species` | string | Same as proteomic. |

### 3.3 Processed Unified Matrix Schema
| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | string | Unique ID. |
| `stress` | string | Stress label. |
| `species` | string | Plant species. |
| `protein_<ID>` | number | Normalized abundance for each protein (dynamic columns). |
| `target_gene_expression` | number | Mapped gene expression (regression target). |

*All processed files must validate against `contracts/dataset.schema.yaml`.*

## 4. Constraints & Rules
- **Uniqueness**: (`sample_id`, `protein_id`) unique in raw proteomics.  
- **Completeness**: Samples lacking a matching transcriptomic record are dropped (FR‑003).  
- **Imputation**: LCM applied to protein abundances; any column where > 90 % are missing is dropped and logged.  
- **Mapping**: Only rows with successful `biomaRt` mapping survive to the unified matrix.  
- **No In‑Place Modification**: Raw files remain untouched; every transformation writes a new file under `data/processed/`.  

---

