# Data Model: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

## Overview

This document describes the data model for the plant defense compound prediction pipeline, including entity definitions, relationships, and validation schemas.

## Data Population Strategy

**CRITICAL**: All data matrices below are populated ONLY after Phase 0 Data Discovery confirms verified plant omics datasets. If no verified sources exist, the pipeline halts with error code E-DATASET.

### Population Protocol

1. **Phase 0 Verification**: Confirm GEO series and Metabolomics Workbench experiment IDs exist in verified datasets block
2. **Pairing Check**: Verify ≥95% sample-level pairing between expression and metabolite datasets
3. **Power Check**: Verify n≥28 samples for adequate statistical power
4. **Download**: Fetch data from verified sources only (GEO, Metabolomics Workbench)
5. **Validation**: Verify checksums (SHA-256) match expected values
6. **Populate**: Create ExpressionMatrix and MetaboliteMatrix only after steps 1-5 pass
7. **Log**: Record all population steps in data/sources.yaml with accession IDs, download dates, and preprocessing script versions

**⚠️ ABORT CONDITIONS**:
- If verified datasets block does not contain plant omics data → E-DATASET
- If pairing rate <95% → E-PAIRING
- If sample size <28 → E-POWER

## Core Entities

### ExpressionMatrix

**Description**: Gene expression values normalized to TPM/FPKM  
**Rows**: Gene identifiers (e.g., AT1G01010 for Arabidopsis, Solyc genes for Solanum)  
**Columns**: Sample IDs  
**Values**: TPM/FPKM values (float64)  
**Population Source**: GEO series after Phase 0 verification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| gene_id | string | Yes | Gene identifier (species-specific format) |
| sample_id | string | Yes | Sample identifier matching metabolite matrix |
| expression_value | float | Yes | TPM or FPKM value |

**Population Steps**:
1. Download raw expression matrix from GEO (data/raw/expression_GEO-*.csv)
2. Normalize to TPM/FPKM if not already normalized
3. Filter zero-variance genes (variance < 1e-10)
4. Log removed genes to logs/feature_filtering.csv
5. Write normalized matrix to data/processed/expression_normalized.csv

### MetaboliteMatrix

**Description**: Defense metabolite concentrations (log-transformed)  
**Rows**: Metabolite identifiers  
**Columns**: Sample IDs  
**Values**: Log-transformed concentrations (float64)  
**Population Source**: Metabolomics Workbench after Phase 0 verification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| metabolite_id | string | Yes | Metabolite identifier (e.g., compound name or HMDB ID) |
| sample_id | string | Yes | Sample identifier matching expression matrix |
| concentration | float | Yes | Log-transformed concentration value |

**Population Steps**:
1. Download raw metabolite data from Metabolomics Workbench (data/raw/metabolite_MW-*.csv)
2. Log-transform concentration values
3. Filter metabolites with <5 samples having quantified values
4. Write normalized matrix to data/processed/metabolite_normalized.csv

### FeatureSet

**Description**: Subset of genes belonging to defense biosynthetic pathways PLUS regulatory genes, transporters, and compartmentalization factors  
**Rows**: Gene identifiers  
**Columns**: Pathway membership flags

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| gene_id | string | Yes | Gene identifier |
| pathway_id | string | Yes | KEGG pathway ID (e.g., terpenoid, alkaloid, phenylpropanoid) |
| species | string | Yes | Species identifier (Arabidopsis or Solanum) |
| ortholog_mapped | boolean | No | True if gene was ortholog-mapped from reference species |
| feature_type | string | Yes | One of: "biosynthetic", "regulatory", "transporter", "compartmentalization" |

**Population Steps**:
1. Query KEGG API for defense pathway gene lists (terpenoid, alkaloid, phenylpropanoid)
2. Map gene IDs to expression matrix gene IDs
3. For unannotated genes, fallback to ortholog mapping (≥60% sequence identity)
4. Add regulatory genes, transporters, compartmentalization factors (FR-004 Extended)
5. Write FeatureSet to data/processed/features.csv
6. Log substitutions to docs/edge_cases.md

### ModelArtifact

**Description**: Serialized Ridge Regression model and evaluation metrics (species-specific)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| metabolite_id | string | Yes | Target metabolite identifier |
| species | string | Yes | Species (Arabidopsis or Solanum) |
| coefficients | array[float] | Yes | Ridge regression coefficients (one per gene feature) |
| alpha | float | Yes | Regularization parameter |
| rmse_mean | float | Yes | Mean RMSE across CV folds |
| rmse_std | float | Yes | Standard deviation of RMSE across CV folds |
| pearson_r | float | Yes | Pearson correlation coefficient |
| p_value | float | Yes | Permutation test p-value |
| bonferroni_corrected_p | float | Yes | Bonferroni-corrected p-value |

**Population Steps**:
1. Train species-specific Ridge Regression models (separate for Arabidopsis and Solanum)
2. Perform 5-fold cross-validation
3. Run permutation test (1,000 iterations)
4. Apply Bonferroni correction across metabolites
5. Write ModelArtifact to outputs/models/metabolite_*.pkl
6. Write evaluation summary to outputs/evaluation_summary.json

## Data Flow

```
Phase 0: Data Discovery → Verify dataset availability (abort if none)
    ↓
GEO Download → ExpressionMatrix (raw)
Metabolomics Workbench Download → MetaboliteMatrix (raw)
    ↓
Pairing Validation (FR-009)
    ↓
Normalization (FR-003) + Batch Correction (FR-010)
    ↓
Feature Selection (FR-004, FR-004 Extended) → FeatureSet
    ↓
Species-Specific Model Training (FR-005) → ModelArtifact
    ↓
Evaluation (FR-006, FR-007) → Final Results
```

## Storage Locations

| Entity | Storage Path | Format |
|--------|--------------|--------|
| Raw Expression | data/raw/expression_*.csv | CSV |
| Raw Metabolite | data/raw/metabolite_*.csv | CSV |
| Paired Data | data/paired/paired_*.csv | CSV |
| Feature Set | data/processed/features.csv | CSV |
| Model Artifacts | outputs/models/*.pkl | Pickle |
| Pairing Logs | logs/data_pairing.json | JSON |
| Feature Filtering Logs | logs/feature_filtering.csv | CSV |
| Power Analysis | outputs/power_analysis.json | JSON |
| Sources Documentation | data/sources.yaml | YAML |

## Data Integrity Requirements

**All data transformations must**:
1. Preserve raw data unchanged (data/raw/ is read-only after download)
2. Create new files for derived data (data/processed/, data/paired/)
3. Record SHA-256 checksums in state/artifact_hashes
4. Document derivation in data/sources.yaml with script version and parameters
5. Log all edge cases and exclusions to appropriate log files

**⚠️ SPEC VS PLAN INCONSISTENCY NOTE**: The spec.md FR-010 still references cross-species model as primary, but this data model correctly defines species-specific models as PRIMARY. This requires spec.md revision (flagged for kickback).