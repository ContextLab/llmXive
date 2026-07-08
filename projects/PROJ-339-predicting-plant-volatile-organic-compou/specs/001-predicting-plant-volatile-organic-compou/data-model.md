# Data Model: Predicting Plant VOC Emission Profiles

## Entities

### Sample
Represents a single experimental condition.
- **Attributes**:
  - `sample_id` (string): Unique identifier.
  - `treatment` (string): Experimental condition (e.g., "drought", "herbivory").
  - `time_point` (integer): Time in hours.
  - `tissue` (string): Plant part (e.g., "leaf", "root").
  - `temperature` (float): Ambient temperature (°C).
  - `light_intensity` (float): Light intensity (µmol m⁻² s⁻¹).
  - `co2_level` (float): CO2 concentration (ppm). **Required: Samples missing this value are excluded.**
  - `replicate_count` (integer): Number of biological replicates for this condition.

### GenomicFeature
Represents a gene expression level.
- **Attributes**:
  - `gene_id` (string): Gene identifier (e.g., "AT1G01010").
  - `gene_family` (string): Family name (e.g., "TPS", "JAZ").
  - `expression_tpm` (float): Normalized transcript count (TPM).

### VOCProfile
Represents the measured concentration of a specific VOC.
- **Attributes**:
  - `voc_id` (string): VOC identifier (e.g., "limonene", "terpinen-4-ol").
  - `concentration` (float): Concentration (ng g⁻¹ FW).
  - `detection_limit` (float): Lower limit of detection.

## Relationships

- **Sample** `1:1` **GenomicFeature** (via `sample_id` and `gene_id` in a long-format table or wide-format matrix).
- **Sample** `1:1` **VOCProfile** (via `sample_id` and `voc_id` in a long-format table or wide-format matrix).
- **Sample** `1:1` **EnvironmentalFeature** (embedded in Sample or separate table linked by `sample_id`).

## Data Flow

1.  **Raw Input**: Mock/Real files (CSV/JSON) containing RNA-seq counts, VOC concentrations, and metadata.
2.  **Normalization**: Transcript counts converted to TPM.
3.  **Imputation**: Missing values filled (median/KNN).
4.  **Merging**: Join on `sample_id`. Exclude unpaired samples.
5.  **Filtering**: Exclude conditions with <3 replicates; exclude samples with missing continuous environmental metadata (temperature, light intensity, **CO2**).
6.  **Dimensionality Reduction**: Aggregate gene expression into pathway-level features.
7.  **Final Dataset**: Wide-format matrix where rows are samples, columns are `gene_id` (TPM), `environmental_feature` (float), and target `voc_id` (float).

## Constraints

- **Sample Size**: Minimum 50 samples for modeling (warning if <50).
- **Replicates**: Minimum 3 biological replicates per condition.
- **Data Types**: All numeric columns must be float/int. Categorical columns must be encoded.
- **Missing Data**: Continuous environmental metadata (temperature, light, CO2) must not be missing; if missing, sample is excluded.