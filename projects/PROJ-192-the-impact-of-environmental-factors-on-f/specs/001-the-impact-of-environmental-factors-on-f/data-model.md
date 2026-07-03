# Data Model: Impact of Environmental Factors on Fungal Community Structure in Soil

## Overview
The project manipulates several artefact types: raw sequencing files, processed ASV tables, environmental metadata, distance matrices, and result tables/figures. The following schemas formalize the expected structure of each artefact. All schemas are version‑controlled under `contracts/`.

### 1. Raw Sequencing (`data/raw-seq/`)
| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | string | Unique identifier for the sequencing sample. |
| `fastq_path` | string (path) | Relative path to the gzipped FASTQ file. |
| `study_id` | string | Identifier of the source study (e.g., SRA accession). |
| `checksum_md5` | string | MD5 hash of the FASTQ file (for data hygiene). |

*No schema file needed – raw files are immutable.*

### 2. Harmonized Metadata (`data/metadata/harmonized.csv`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Environmental Metadata Schema"
type: "object"
properties:
  sample_id:
    type: "string"
    description: "Matches a sample_id in raw‑seq."
  study_id:
    type: "string"
    description: "Identifier of the source study (e.g., SRA accession)."
  pH:
    type: "number"
    description: "Soil pH (dimensionless)."
  nitrogen:
    type: "number"
    description: "Total nitrogen concentration (mg kg⁻¹)."
  phosphorus:
    type: "number"
    description: "Total phosphorus concentration (mg kg⁻¹)."
  potassium:
    type: "number"
    description: "Total potassium concentration (mg kg⁻¹)."
  temperature:
    type: "number"
    description: "Soil temperature at sampling (°C)."
  moisture:
    type: "number"
    description: "Volumetric water content (%)."
  biome:
    type: "string"
    description: "Biome or soil‑type classification (e.g., forest, grassland)."
required: ["sample_id", "study_id", "pH", "nitrogen", "phosphorus", "potassium", "temperature", "moisture", "biome"]
additionalProperties: false
```

### 3. ASV Table (`data/asv/{study_id}_asv.biom`)
- BIOM format containing integer counts per `sample_id` (rows) × `ASV_id` (columns).  
- No schema file required; validated via `biom-format` library.

### 4. Distance Matrices (`data/processed/`)
| File | Type | Description |
|------|------|-------------|
| `bray_curtis.parquet` | Parquet (square matrix) | Bray‑Curtis distances between samples (beta‑diversity). |
| `env_euclidean.parquet` | Parquet (square matrix) | Euclidean distances on the scaled environmental matrix. |
| `shannon.csv` | CSV | One‑column per sample, Shannon diversity values. |
| `observed_asv.csv` | CSV | Observed ASV richness per sample. |

### 5. Imputed Environmental Matrix (`data/processed/imputed_env.parquet`)
Same columns as metadata (except `sample_id`, `study_id`), after MICE imputation and VIF‑based variable selection.

### 6. Results Tables (`results/`)
| File | Description |
|------|-------------|
| `permanova_summary.csv` | Columns: `predictor`, `R2`, `p_value`, `p_adj` (Benjamini‑Hochberg FDR). |
| `varpart_summary.csv` | Columns: `predictor`, `unique_variance`, `shared_variance`, `p_value`. |
| `db_rda_biome_<NAME>.csv` | RDA variance explained per predictor for biome `<NAME>`. |
| `sensitivity_analysis.csv` | Columns: `p_thresh`, `r2_cutoff`, `top_driver`, `stable` (bool). |
| `robustness_summary.md` | Narrative summary with confidence flag. |

### 7. Figures (`results/figures/`)
- `db_rda_triplot.png` – sample points + environmental vectors.  
- `driver_ranking_by_biome.png` – bar plot of driver ranks per biome.  
- `sensitivity_heatmap.png` – heatmap of top driver stability across thresholds.

All artefacts are version‑hashed and recorded in the project state file for reproducibility.

---


