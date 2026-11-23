# Data Model Specification

This document defines the core data structures and schemas used throughout the
Submarine Hydrothermal Vent Microbial Communities analysis pipeline.

## Overview

The pipeline processes three primary data types:
1. **Sample Metadata**: Environmental and temporal data (pH, temperature, location)
2. **OTU/ASV Tables**: Microbial abundance data from 16S rRNA sequencing
3. **Analysis Results**: Statistical outputs from diversity and regression models

## Core Entities

### Sample

Represents a single environmental sampling event.

**Fields:**
- `sample_id` (str): Unique identifier
- `timestamp` (datetime): Sampling time
- `pH` (float): Measured pH value
- `temp` (float): Measured temperature (°C)
- `pH_sd` (float): Standard deviation of pH within ±15 min window
- `location` (str): Deployment location name
- `fastq_path` (str): Path to raw FASTQ file
- `deployment_event` (str): Event identifier
- `sensor_id` (str): Sensor identifier
- `coordinates` (str): GPS coordinates (lat,lon)
- `pH_heterogeneous` (bool): True if pH_sd > 0.2 (flagged for review)

**Validation Rules:**
- pH must be in range [1.0, 10.0]; edge ranges [1.0-2.0] and [8.5-10.0] flagged
- pH_sd calculated from all readings within ±15 min of timestamp
- Required fields: sample_id, timestamp, pH, temp, location, deployment_event, sensor_id, coordinates

### OTU/ASV

Represents a taxonomic unit (Operational Taxonomic Unit or Amplicon Sequence Variant).

**Fields:**
- `otu_id` (str): Unique identifier (e.g., OTU_001, ASV_1234)
- `taxonomy` (str): Taxonomic classification (Kingdom;Phylum;Class;Order;Family;Genus;Species)
- `abundance` (int): Count in sample (per-sample table)
- `presence_absence` (bool): Whether present in sample
- `sample_id` (str): Foreign key to Sample

**Validation Rules:**
- Abundance must be non-negative integer
- Taxonomy follows semicolon-delimited format
- OTU IDs must be unique within dataset

### DiversityMetric

Represents calculated diversity indices for a sample.

**Fields:**
- `sample_id` (str): Foreign key to Sample
- `shannon` (float): Shannon diversity index
- `simpson` (float): Simpson diversity index
- `observed_otus` (int): Number of observed OTUs/ASVs
- `chao1` (float): Chao1 richness estimator
- `rarefaction_depth` (int): Depth used for rarefaction
- `transformed` (bool): Whether CLR/log transformation applied

**Validation Rules:**
- Shannon, Simpson, Chao1 must be non-negative floats
- Observed OTUs must be positive integer
- Rarefaction depth must match pipeline parameter

## Schema Files

The following YAML schemas are defined in `contracts/`:

1. `contracts/sample_schema.schema.yaml`: Sample metadata validation
2. `contracts/otu_table_schema.schema.yaml`: OTU/ASV table validation
3. `contracts/analysis_results_schema.schema.yaml`: Analysis output validation

These schemas are used by:
- Ingestion pipeline (T010-T014) to validate input data
- Preprocessing pipeline (T018-T021) to validate OTU tables
- Analysis pipeline (T022a-T026) to validate regression results
- Contract tests (T008, T016, T027) to ensure schema compliance

## Integration with Code

The Python classes in `code/data_models.py` (`Sample`, `OTU`, `DiversityMetric`)
implement these schemas with runtime validation via the `validate_*_schema` functions.
