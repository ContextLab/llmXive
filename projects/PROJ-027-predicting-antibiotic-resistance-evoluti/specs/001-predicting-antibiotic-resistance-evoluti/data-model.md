# Data Model: Predicting Antibiotic Resistance Evolution from Genomic Sequences

## Overview
This document defines all data artifacts, their schemas, and the transformations applied throughout the pipeline. It ensures compliance with Constitution Principles III (Data Hygiene) and VI (Genomic Feature Traceability). **`data-model.md` is the designated Single Source of Truth (SSoT) for all downstream artifacts** as required by Constitution Principle IV.

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **Isolate** | `isolate_id` (str), `tax_id` (int, constant identifier), `fasta_path` (str), `metadata` (dict) | Represents a single *E. coli* sample; `metadata` includes ARIBA gene‑presence dict and phenotypic AST results. |
| **SNPFeature** | `gene_id` (str), `position` (int), `ref_allele` (str), `alt_allele` (str), `count` (int) | SNPs called by Snippy; `count` is the number of isolates carrying the SNP. |
| **GeneFeature** | `gene_id` (str), `presence` (binary), `tool` (enum: Snippy, ARIBA) | Binary flag from ARIBA indicating presence of a CARD resistance gene. |
| **TargetLabel** | `gene_id` (str), `label` (binary) | For each antibiotic class, the binary phenotypic outcome (1 = resistant, 0 = susceptible). |

## Data Flow & Transformations

1. **Raw Ingestion**  
   - **Input**: GenBank parquet (`data/raw/genbank.parquet`).  
   - **Output**: `data/raw/isolates_manifest.csv` (columns: `isolate_id`, `fasta_path`, `checksum`).  

2. **Phenotype Fetch**  
   - **Input**: `isolates_manifest.csv`.  
   - **Process**: Query NCBI Pathogen Detection API for AST results per isolate.  
   - **Output**: `data/raw/phenotype.csv` (columns: `isolate_id`, `antibiotic`, `phenotype`).  

3. **Feature Extraction**  
   - **SNP Calling** (`run_snippy.sh`) → per‑isolate VCF → aggregated SNP count matrix (`data/processed/snp_counts.csv`).  
   - **Gene Detection** (`run_ariba.sh`) → binary gene matrix (`data/processed/gene_presence.csv`).  

4. **Feature Matrix Assembly** (`build_feature_matrix.py`)  
   - **Input**: `snp_counts.csv`, `gene_presence.csv`, `phenotype.csv`.  
   - **Processing**: VIF filtering, **exclusion of SNPs with VIF > 5**; **mechanism‑blind filter removes the target resistance gene column *and* any SNPs whose coordinates lie within that gene’s locus**; no removal of target gene column (outcome is phenotypic).  
   - **Output**: `data/processed/feature_matrix_filtered.csv` (see **Feature Matrix Schema**).  

5. **Model Input Split** (`train_models.py`)  
   - **Stratified, phylogenetically‑blocked split** → `train_data.csv`, `test_data.csv`.  

6. **Model Output** (`train_models.py` & `evaluate.py`)  
   - **Artifacts**: `data/models/{gene}_logreg.pkl`, `data/models/{gene}_rf.pkl`, `data/models/metrics.json`.  

7. **Validation Artifacts** (`phylo_permutation.py`, `sensitivity_analysis.py`)  
   - **Outputs**: `data/results/{gene}_perm_test.json`, `data/results/{gene}_sensitivity.json`.  

8. **Verification Summary** (`04_validate/verify_results.py`)  
   - **Produces**: `data/processed/verification_summary.json` that aggregates AUC, p‑value, top‑10 feature ranking, and class‑to‑genes mapping.  
   - **Required Input Files** (now explicitly generated):  
     - `data/models/metrics.json` (model performance per gene).  
     - `data/processed/feature_ranking.csv` (global ranking of all features by importance).  
     - `data/processed/class_to_genes.json` (mapping of each antibiotic class / target gene to the set of genes used in its model).  

9. **Visualization** (`generate_plots.py`)  
   - **Outputs**: `data/figures/roc_{gene}.png`, `data/figures/feature_importance_{gene}.png`.  

## Schemas (Contract Definitions)

- **Feature Matrix Schema** – located at `contracts/feature_matrix.schema.yaml`.  
- **Model Output Schema** – located at `contracts/model_output.schema.yaml`.  

Both schemas are validated by the `tests/contract/` suite before downstream steps.

## Data Hygiene Rules

1. **Checksums** – Every file in `data/raw/` has a SHA‑256 hash stored in `state/artifact_hashes.yaml`.  
2. **Immutability** – Raw FASTA/FASTA‑derived files are never overwritten; each transformation writes a new file under `data/processed/`.  
3. **PII** – Only public isolate IDs are stored; no patient identifiers.  
4. **Versioning** – After each major stage, `hash_artifacts.py` recomputes hashes for *all* files in `data/` and updates `state/`.  

## Additional Output Files (required for verification)

| File | Description |
|------|-------------|
| `data/models/metrics.json` | JSON dictionary per antibiotic class containing AUC‑ROC, precision‑recall, and cross‑validation statistics. |
| `data/processed/feature_ranking.csv` | CSV listing all features (SNPs and genes) ranked by aggregated importance across all models. |
| `data/processed/class_to_genes.json` | Mapping from each antibiotic class (treated as target phenotype) to the list of gene‑presence features that were **included** in its model (mechanism‑blind not applicable). |

All three files are generated automatically during the **Model Training** and **Statistical Validation** phases and are consumed by the verification script (`verify_results.py`).  

---



