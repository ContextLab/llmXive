---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Disease Resistance from Publicly Available Genomic and Metabolomic Data

**Field**: biology

## Research question

Can plant disease resistance be predicted using publicly available genomic (SNPs) and metabolomic data from plant-pathogen interaction studies? Specifically, can we identify genetic markers and metabolic signatures that correlate with resistance levels to common plant pathogens?

## Motivation

Plant disease resistance is critical for sustainable agriculture, but traditional breeding programs are time-consuming and costly. Integrating genomic and metabolomic data could reveal predictive biomarkers for resistance, enabling faster selection of resistant cultivars. However, multi-omics integration for plant disease prediction remains underexplored in publicly available datasets.

## Related work

- TODO — lit-search returned no relevant results for plant disease resistance, plant genomics, or plant metabolomics. The provided literature block contains papers on Alzheimer's disease, cognitive decline, and PFAS toxicity, which are not applicable to this research question.

## Expected results

We expect to identify a subset of SNPs and metabolites that show significant correlation with resistance phenotypes across multiple plant-pathogen systems. Statistical validation (p<0.05 after multiple testing correction) and cross-validation accuracy ≥75% would confirm predictive utility. A reproducible pipeline demonstrating multi-omics feature selection would provide evidence for feasibility.

## Methodology sketch

- **Data acquisition**: Download plant genomic data from NCBI SRA (e.g., search terms: "plant GWAS disease resistance", "Arabidopsis pathogen response") and metabolomics data from MetaboLights or Metabolomics Workbench (public plant-pathogen datasets).
- **Data preprocessing**: Process raw sequencing reads with `fastp` (QC) and `bcftools` (variant calling) for SNPs; normalize metabolomics data using `MetaboAnalyst`-compatible pipelines; filter to samples with both data types available.
- **Feature selection**: Apply LASSO regression or random forest feature importance to identify top 50 SNPs and 50 metabolites associated with resistance phenotypes from public phenotype annotations.
- **Model training**: Train elastic net regression or gradient boosting classifier (scikit-learn) to predict resistance levels (continuous or categorical) from selected features; 5-fold cross-validation on public dataset.
- **Statistical validation**: Perform permutation testing (n=1000) to assess model significance; calculate AUC-ROC, precision-recall, and R² metrics; apply Benjamini-Hochberg correction for multiple hypothesis testing.
- **Reproducibility**: Package pipeline as GitHub repository with Docker container; document all commands for `wget`/`curl` data retrieval; ensure total runtime ≤6 hours on 2 CPU cores, ≤7GB RAM.

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: N/A (no existing ideas to compare).
- Verdict: NOT a duplicate.
