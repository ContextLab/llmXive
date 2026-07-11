# Data Model: Predicting Antibiotic Resistance Evolution from Genomic Sequences

## Overview

This document defines the data structures, schemas, and transformations used throughout the pipeline. It ensures data hygiene (Constitution Principle III) and traceability (Principle VI).

## Entities

### 1. Isolate
Represents a single *E. coli* sample.
*   **Attributes**:
    *   `isolate_id`: Unique identifier (e.g., from NCBI).
    *   `source`: "NCBI Pathogen Detection" or specific BioProject ID.
    *   `fasta_path`: Path to the raw FASTA file.
    *   `metadata`: Dictionary of susceptibility data (e.g., `{"ciprofloxacin": "R"}`).

### 2. GenomicFeature
Represents a biological marker.
*   **Types**:
    *   `SNP`: Single Nucleotide Polymorphism (Chromosomal position, Ref, Alt).
    *   `Gene`: Presence/Absence of a resistance gene.
    *   `CNV`: Copy Number Variation (if available, otherwise null).
*   **Traceability**: Each feature records the tool used (Snippy/ARIBA) and the reference genome version.

### 3. ResistancePhenotype
The target variable.
*   **Attributes**:
    *   `antibiotic_class`: e.g., "Fluoroquinolones".
    *   `label`: Binary (0 = Susceptible, 1 = Resistant).
    *   `threshold`: MIC value used to determine the label (stored for reference).

## Data Flow & Transformations

1.  **Raw Ingestion**:
    *   Input: NCBI API responses (JSON/XML), FASTA files.
    *   Output: `data/raw/isolates_manifest.csv` (list of IDs, paths, checksums).
2.  **Feature Extraction**:
    *   Input: FASTA files, Reference Genome.
    *   Process: Snippy (SNPs), ARIBA (Genes).
    *   Output: `data/processed/feature_matrix.csv` (Isolate ID vs. Features).
3.  **Preprocessing**:
    *   Input: Feature matrix.
    *   Process: **VIF Filtering** (remove features with VIF > 5).
    *   Output: `data/processed/feature_matrix_filtered.csv`.
4.  **Model Input**:
    *   Input: Filtered feature matrix + Phenotype labels.
    *   Process: Mechanism-blind filtering (remove target gene).
    *   Output: `data/processed/train_data.csv`, `test_data.csv`.
5.  **Model Output**:
    *   Input: Trained models.
    *   Output: `data/models/weights.pkl`, `data/models/metrics.json`.

## Schemas (Contract Definitions)

The following schemas are defined in `contracts/` and validated by the `tests/contract/` suite.

### Feature Matrix Schema
Defines the structure of the processed data used for modeling.
*   **Columns**: `isolate_id`, `feature_1`, `feature_2`, ..., `phenotype_<antibiotic>`.
*   **Types**: `isolate_id` (string), Features (binary/numeric), Phenotype (binary).
*   **Constraints**: No missing values in phenotype. No duplicate isolate IDs.

### Model Output Schema
Defines the structure of the saved model artifacts.
*   **Fields**: `model_type`, `antibiotic_class`, `auc_roc`, `p_value`, `feature_importance`, `timestamp`.

## Data Hygiene Rules

1.  **Checksums**: Every file in `data/raw/` must have a corresponding SHA256 hash recorded in `state/`.
2.  **Immutability**: Raw files are never modified. All transformations create new files in `data/processed/`.
3.  **PII**: No patient names or private identifiers are included. Only public isolate IDs.
4.  **Versioning**: The `hash_artifacts.py` script computes SHA256 hashes for all `data/` and `code/` artifacts and updates `state/` JSON files after each major stage.