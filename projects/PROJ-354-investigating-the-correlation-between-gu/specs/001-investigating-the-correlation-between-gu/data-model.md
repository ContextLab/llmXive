# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data

## Overview

This document defines the data structures, transformations, and schemas used throughout the pipeline. All data is generated synthetically to mimic the UK Biobank schema, as no open-access UKB microbiome dataset exists for CI execution.

## Entity Definitions

### 1. Participant

Represents a single subject in the cohort.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | `str` | Unique identifier (UUID) | Primary Key |
| `age` | `float` | Age in years | [40, 85] |
| `sex` | `int` | 0=Female, 1=Male | {0, 1} |
| `bmi` | `float` | Body Mass Index | [15, 45] |
| `diet_quality` | `float` | Diet quality score | [0, 100] |
| `physical_activity` | `float` | MET-min/week | > 0 |
| `medication_use` | `int` | 0=No, 1=Yes | {0, 1} |
| `antibiotic_use` | `int` | 0=No, 1=Yes (Recent) | {0, 1} |

### 2. MicrobiomeProfile

ILR-transformed taxonomic coordinates for a participant.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | `str` | Foreign Key to Participant | PK, FK |
| `ilr_coords` | `dict[str, float]` | ILR-transformed values for each genus | Sum of coordinates = 0 (orthonormal) |
| `sequencing_depth` | `int` | Total reads | > 0 |
| `quality_score` | `float` | Sequencing quality metric | [0, 1] |

### 3. CognitiveScore

Standardized cognitive performance metrics.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | `str` | Foreign Key to Participant | PK, FK |
| `reaction_time` | `float` | Mean reaction time (ms) | > 0 |
| `numeric_memory` | `int` | Score 0-100 | [0, 100] |
| `reasoning` | `int` | Score 0-100 | [0, 100] |
| `test_date` | `str` | ISO 8601 date | YYYY-MM-DD |

### 4. AssociationResult

Statistical output from the analysis.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `taxon` | `str` | Genus name | |
| `cognitive_metric` | `str` | "reaction_time", "numeric_memory", "reasoning" | |
| `beta` | `float` | Effect size (coefficient) | |
| `p_value` | `float` | Unadjusted p-value | (0, 1] |
| `p_adj` | `float` | Benjamini-Hochberg adjusted p-value | (0, 1] |
| `interaction_p` | `float` | Interaction term p-value (optional) | (0, 1] |
| `causality_claim` | `bool` | Always `false` | `false` |

## Transformation Pipeline

### 1. Raw Data Generation
*   **Input**: Random seed.
*   **Output**: `data/raw/synthetic_ukb.parquet`.
*   **Logic**:
    *   Sample `age`, `sex`, `bmi` from distributions.
    *   Generate `microbiome_counts` using Dirichlet-Multinomial to simulate 16S sequencing.
    *   Generate `cognitive_scores` with correlation to `age` and `antibiotic_use`.

### 2. Preprocessing (ILR Transformation)
*   **Input**: `data/raw/synthetic_ukb.parquet`.
*   **Output**: `data/processed/ilr_transformed.parquet`.
*   **Logic**:
    *   Filter: Exclude participants with `antibiotic_use == 1` or missing data.
    *   Pseudocount: Add $1 \times 10^{-6}$ to all zero counts.
    *   Transformation: Apply ILR using a balance tree (e.g., phylogenetic or equal split).
    *   Result: Orthonormal coordinates.

### 3. Statistical Analysis
*   **Input**: `data/processed/ilr_transformed.parquet`.
*   **Output**: `results/associations/main_effects.parquet`.
*   **Logic**:
    *   Fit OLS: $Cognitive \sim ILR_{taxon} + Confounders$.
    *   Apply BH correction.
    *   Fit Interaction: $Cognitive \sim ILR_{taxon} \times Age\_Group + Confounders$.

## File Formats

*   **Parquet**: Used for all intermediate and final datasets (efficient, schema-preserving).
*   **YAML**: Used for configuration and schema definitions.
*   **JSON**: Used for metadata (e.g., `causality_claim`).
