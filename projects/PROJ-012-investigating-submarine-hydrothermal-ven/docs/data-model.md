# Data Model: Submarine Hydrothermal Vent Microbial Communities

This document defines the core data entities, their attributes, and the relationships between them for the automated science pipeline investigating ocean acidification effects on vent microbial communities.

## 1. Overview

The data model is designed to handle three primary types of data:
1. **Environmental Metadata**: Physical and chemical measurements (pH, Temperature) linked to spatial and temporal coordinates.
2. **Microbial Counts**: OTU/ASV tables derived from 16S rRNA sequencing.
3. **Derived Metrics**: Diversity indices and statistical analysis results.

## 2. Core Entities

### 2.1. Sample (Environmental Context)
Represents a specific sampling event at a hydrothermal vent.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `sample_id` | String | Unique identifier for the sample | PK, Non-null |
| `timestamp` | DateTime | Time of sample collection | ISO 8601 |
| `pH` | Float | Measured pH value | 0.0 <= pH <= 14.0 |
| `temperature` | Float | Measured temperature (°C) | > 0.0 |
| `location` | String | Site name or identifier | Non-null |
| `deployment_event` | String | Identifier for the sensor deployment | Non-null |
| `sensor_id` | String | Unique ID of the sensor used | Non-null |
| `coordinates` | String | Latitude/Longitude string | Format: "lat,lon" |
| `fastq_path` | String | Path to raw sequencing file | Optional |
| `pH_sd` | Float | Standard deviation of pH in ±15min window | >= 0.0 |
| `pH_heterogeneous` | Boolean | Flag if pH_SD > 0.2 | Derived |

### 2.2. OTU/ASV (Microbial Abundance)
Represents the count of a specific taxonomic unit within a sample.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `sample_id` | String | Foreign key to Sample | FK |
| `otu_id` | String | Unique identifier for the OTU/ASV | PK, Non-null |
| `count` | Integer | Read count for this OTU | >= 0 |
| `taxonomy` | List[String] | Taxonomic classification path | Optional |

### 2.3. DiversityMetric (Analysis Result)
Represents calculated diversity indices or statistical model outputs.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `sample_id` | String | Foreign key to Sample | FK |
| `metric_name` | String | Name of the metric (e.g., 'shannon') | Non-null |
| `value` | Float | Calculated value | >= 0.0 |
| `rarefaction_depth` | Integer | Depth used for rarefaction | Optional |
| `model_type` | String | Type of statistical model (e.g., 'LME') | Optional |
| `estimate` | Float | Regression coefficient (if applicable) | Optional |
| `se` | Float | Standard error (if applicable) | Optional |
| `p_value` | Float | P-value (if applicable) | 0.0 <= p <= 1.0 |

## 3. Relationships

- **One-to-Many (Sample -> OTU)**: A single sample contains multiple OTU records.
- **One-to-Many (Sample -> DiversityMetric)**: A single sample can have multiple diversity metrics calculated (e.g., Shannon, Simpson, different rarefaction depths).

## 4. Data Flow

1. **Ingestion**: Raw sensor data (CSV) and FASTQ files are mapped to the `Sample` entity.
2. **Processing**: FASTQ files are processed to generate `OTU` tables.
3. **Analysis**: `Sample` and `OTU` data are combined to generate `DiversityMetric` records.
4. **Output**: All entities are serialized to `data/processed/` in CSV format adhering to the schema definitions in `contracts/`.
