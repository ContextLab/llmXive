# Data Model: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

## Overview

This document defines the data structures, schemas, and transformations used in the pipeline. All data flows through these schemas to ensure consistency and validation.

## Core Entities

### 1. RNA-Seq Study Metadata
Represents a single experiment.
- **Accession ID**: String (e.g., "GSE12345")
- **Species**: String (Scientific name)
- **Tissue**: Enum {leaf, stem, root}
- **Treatment**: Enum {chewing, piercing_sucking, control}
- **Replicates**: Integer (≥2)
- **Sequencing Platform**: String

### 2. Expression Matrix
- **Format**: Dense/Sparse Matrix (Species × Genes) or Long Format (Species, Gene, TPM)
- **Normalization**: TPM (Transcripts Per Million)
- **Batch ID**: String (for ComBat-seq)
- **Constraint**: Must exclude genes directly involved in defense trait synthesis (e.g., CYP79D16) to prevent data leakage.

### 3. Defense Trait Record
- **Species**: String
- **Chemical Traits**: Dict {Glucosinolates: float, Alkaloids: float, Phenolics: float} (Fixed list)
- **Physical Traits**: Dict {Trichome_Density: float, Leaf_Tensile_Strength: float} (Fixed list)
- **Source**: String (TRY, Literature, Phenoscape, GBIF)
- **Units**: String (standardized)

### 4. Herbivore-Response Vector
- **Species**: String
- **Treatment**: Enum {chewing, piercing_sucking}
- **Features**: Dict {Pathway_ID: float} (Aggregated from top DE genes)
- **Vector Length**: ≤50
- **Robustness**: Pathways must have ≥3 mapped genes in all target species.

### 5. Defense Allocation Index (DAI)
- **Species**: String
- **Chemical_Mean**: Float (Standardized)
- **Physical_Mean**: Float (Standardized)
- **DAI_Value**: Float (Ratio)

## Data Flow

1.  **Raw Ingestion**: FASTQ -> (fastp, HISAT2, featureCounts) -> **Expression Matrix (TPM)**
2.  **Batch Correction**: Expression Matrix -> (ComBat-seq with fixed 50-gene list) -> **Corrected Matrix**
3.  **Differential Expression**: Corrected Matrix -> (DESeq2) -> **DE Gene List**
4.  **Feature Engineering**: DE Gene List -> (Exclude trait genes, Pathway Agg) -> **Herbivore-Response Vector**
5.  **Trait Integration**: Raw Traits -> (Fallback Lookup, Normalization) -> **Defense Trait Record** -> **DAI**
6.  **Modeling**: Response Vector + DAI -> (LOSO CV, PGLS) -> **Model Artifacts**

## Constraints

- **Memory**: All matrices must fit in available system memory.. Sampling to 15 species is mandatory if >15.
- **Immutability**: Raw files in `data/raw` are never modified. Derived files in `data/processed` are new.
- **Validation**: Every step must validate against the schemas in `contracts/`.
- **Data Leakage**: Predictors must exclude genes involved in the synthesis of the measured traits.
- **Pathway Robustness**: Pathways with <3 mapped genes in any target species are excluded.