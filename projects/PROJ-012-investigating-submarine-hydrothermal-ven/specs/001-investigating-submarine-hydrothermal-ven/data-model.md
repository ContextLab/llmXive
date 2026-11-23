# Data Model Specification: Submarine Hydrothermal Vent Microbial Communities

## Overview
This document defines the core data entities, their attributes, and relationships for the automated science pipeline investigating submarine hydrothermal vent microbial communities as indicators of ocean acidification.

## Key Entities

### 1. Sample
Represents a single environmental sampling event, linking physical location, temporal data, and biological material.

**Attributes:**
- `sample_id` (string, unique): Primary identifier (e.g., "VENT-001-S1")
- `timestamp` (datetime): Exact time of sample collection
- `deployment_event` (string): Identifier for the specific deployment campaign
- `sensor_id` (string): ID of the pH/Temp sensor used
- `coordinates` (string): Geo-spatial coordinates (lat, long, depth)
- `pH` (float): Measured pH value
- `temperature` (float): Measured temperature in Celsius
- `pH_sd` (float): Standard deviation of pH within the ±15 min window (heterogeneity metric)
- `pH_heterogeneous` (boolean): Flag indicating if pH_sd > 0.2
- `outlier_status` (string): "valid", "review_low", "review_high", "excluded"
- `fastq_path` (string): Relative path to raw sequencing data
- `quality_flag` (string): Derived quality status based on sensor and pH constraints

**Constraints:**
- pH must be within 1.0–10.0 for inclusion; values outside trigger exclusion or review.
- pH heterogeneity (SD > 0.2) triggers exclusion per FR-001.1.

### 2. OTU/ASV (Operational Taxonomic Unit / Amplicon Sequence Variant)
Represents a distinct microbial taxonomic unit derived from 16S rRNA sequencing.

**Attributes:**
- `otu_id` (string): Unique identifier for the OTU/ASV
- `taxonomy` (string): Taxonomic classification (Kingdom;Phylum;Class;Order;Family;Genus;Species)
- `counts` (dict): Mapping of `sample_id` -> count (integer)
- `sequence` (string): Representative nucleotide sequence (optional, for reference)

**Constraints:**
- Counts must be non-negative integers.
- Taxonomy must follow standard nomenclature or be marked "unclassified".

### 3. DiversityMetric
Represents calculated alpha or beta diversity metrics for a sample.

**Attributes:**
- `sample_id` (string): Reference to the Sample entity
- `metric_type` (string): "shannon", "simpson", "observed_otus", "bray_curtis", etc.
- `value` (float): Calculated metric value
- `rarefaction_depth` (int): The sequencing depth used for rarefaction (if applicable)
- `transformed_value` (float): Value after CLR or log transformation (if applicable)
- `model_estimate` (float): Coefficient from LME/Regression (if applicable)
- `model_p_value` (float): P-value from statistical test
- `model_type` (string): "lme", "linear", "spearman"

**Constraints:**
- Metrics must be derived from valid, non-excluded samples.
- Transformation logic must be documented (e.g., "CLR with pseudocount 1").

## Relationships
- **Sample** has **many** **DiversityMetric** entries.
- **Sample** is linked to **OTU** counts (many-to-many via count matrix).
- **Analysis Results** aggregate **DiversityMetric** and **Sample** data.

## Schema Validation Rules
- All numeric fields must be valid floats/ints (no NaN unless explicitly allowed).
- `sample_id` must be unique across the dataset.
- `timestamp` must be ISO 8601 compliant.
- `outlier_status` must be one of the defined enum values.

## Output Artifacts
- `data/processed/unified_sample_table.csv`: Aggregated sample metadata.
- `data/processed/otu_table.tsv`: OTU count matrix.
- `data/processed/alpha_diversity_results.csv`: Alpha diversity metrics.
- `data/processed/beta_diversity_results.csv`: Beta diversity metrics and PERMANOVA results.
- `data/processed/lme_results.csv`: Linear Mixed-Effects model results.
- `results/figures/`: Ordination plots and diagnostic charts.
