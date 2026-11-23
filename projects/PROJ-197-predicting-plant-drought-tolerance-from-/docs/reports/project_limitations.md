# Project Limitations Report

## Overview
This document outlines the known limitations and constraints of the "Predicting Plant Drought Tolerance" research pipeline (PROJ-197). These limitations are critical for interpreting the results and understanding the scope of the current MVP.

## 1. Synthetic Genomic Data
**Status:** Active Limitation
**Description:** The genomic marker data used for training and validation is **entirely synthetic**.
**Details:**
- Real genomic data from sources like NCBI RefSeq or the TRY database (which primarily contains trait data) was not available in a format suitable for direct ingestion without extensive, non-trivial processing pipelines.
- The current implementation (`code/data/generate.py`) generates synthetic expression levels for 20 key stress-response genes (e.g., `NCED3`, `DREB2A`, `P5CS`) based on a random seed (`random_state=42`).
- Drought tolerance labels are derived deterministically from these synthetic markers (Label = 1 if sum of markers >= 12, else 0).
**Impact:**
- Model performance metrics (AUC, accuracy) reflect the ability to learn the *synthetic* generation logic, not necessarily real biological relationships.
- Feature importance rankings indicate which synthetic genes drive the synthetic label, which serves as a proof-of-concept for the pipeline but does not constitute biological discovery.
**Future Work:** Integration with real transcriptomic datasets (e.g., from NCBI GEO or SRA) is required to validate biological relevance.

## 2. Synthetic Phylogenetic Distance Matrix
**Status:** Active Limitation
**Description:** The phylogenetic distance matrix used for the KNN baseline model is synthetic.
**Details:**
- As noted in task T016, a real, high-quality phylogenetic tree for the specific species subset in the TRY database was not available.
- The matrix is generated with zero diagonal and off-diagonal values uniformly distributed between arbitrary bounds.
**Impact:**
- The KNN baseline does not represent a true phylogenetic neighbor prediction but serves as a statistical control for the pipeline.

## 3. Standard MICE vs. Phylogenetic MICE
**Status:** Active Limitation
**Description:** Imputation of missing trait data uses standard Iterative Imputer (MICE) rather than Phylogenetic MICE.
**Details:**
- The original design envisioned phylogenetic imputation to account for evolutionary relationships.
- Due to the lack of a verified real phylogenetic tree (see Limitation #2), the implementation falls back to `sklearn.impute.IterativeImputer`.
**Impact:**
- Imputed values do not account for phylogenetic signal, potentially introducing bias if close relatives share similar unobserved traits.

## 4. Species Coverage and Data Sparsity
**Status:** Known Constraint
**Description:** The TRY database is massive, but the current pipeline processes a limited subset of species.
**Details:**
- The pipeline explicitly logs species present in TRY but missing from the genomic dataset (which is synthetic and limited to the 20 gene list).
- Many species in the full TRY database may lack the necessary trait data to be included in the final merged dataset.
**Impact:**
- Results are representative only of the species successfully merged and imputed, not the global plant diversity.

## 5. Model Generalizability
**Status:** Theoretical Limitation
**Description:** Models are trained and tested on a single split of synthetic data.
**Details:**
- While stratified splitting and cross-validation are implemented, the underlying data distribution is artificial.
- No external validation on a completely independent real-world dataset has been performed.
**Impact:**
- High performance scores should not be interpreted as evidence of real-world predictive power.

## Conclusion
This project successfully demonstrates an end-to-end automated science pipeline for data ingestion, imputation, model training, and statistical validation. However, the reliance on synthetic genomic and phylogenetic data means the current results are a **technical validation of the pipeline architecture** rather than a biological discovery. Future iterations must replace synthetic data sources with real, verified biological datasets to achieve scientific utility.

---
*Generated automatically as part of Task T031.*