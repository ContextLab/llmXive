---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Gene Expression from Chromatin Accessibility in Human Cells

**Field**: biology

## Research question

To what extent can bulk chromatin accessibility profiles (DNase-seq/ATAC-seq) predict steady-state gene expression levels (RNA-seq) across diverse human cell types using interpretable regression models?

## Motivation

Understanding the regulatory code linking open chromatin to transcription is fundamental for interpreting non-coding variants associated with disease. While complex deep learning models exist, simpler, resource-efficient models are needed for scalable analysis on limited compute infrastructure, ensuring reproducibility on standard cloud runners.

## Related work

- [BABEL enables cross-modality translation between multiomic profiles at single-cell resolution (2021)](https://doi.org/10.1073/pnas.2023070118) — Demonstrates feasibility of translating between multiomic modalities, providing a benchmark for cross-modality prediction accuracy.
- [Integrative analysis of 111 reference human epigenomes (2015)](https://doi.org/10.1038/nature14248) — Provides the reference human epigenome data (ENCODE) that serves as the primary data source for accessibility and expression profiles.
- [Integration of Unpaired Single-cell Chromatin Accessibility and Gene Expression Data via Adversarial Learning (2021)](http://arxiv.org/abs/2104.12320v1) — Uses adversarial learning for unpaired data, contrasting with the proposed regression approach for paired bulk data.
- [Identifying and Mapping Cell-type Specific Chromatin Programming of Gene Expression (2012)](http://arxiv.org/abs/1210.3313v1) — Early systematic mapping of chromatin structure to gene expression regulation across cell types, establishing baseline biological correlations.
- [The basal level of gene expression associated with chromatin loosening shapes Waddington landscapes and controls cell differentiation (2020)](http://arxiv.org/abs/2012.12962v1) — Highlights the biological importance of baseline transcription linked to chromatin state, supporting the hypothesis of correlation.

## Expected results

A regression model achieving moderate-to-high correlation (R² > 0.5) between predicted and observed expression for housekeeping genes, with lower performance for cell-type specific genes due to complex distal regulation. Feature importance analysis will highlight specific accessible regions near the transcription start site (TSS) as primary predictors.

## Methodology sketch

- **Data Acquisition**: Download paired RNA-seq and DNase-seq/ATAC-seq counts for 5 common human cell lines (e.g., GM12878, K562) from the ENCODE portal (https://www.encodeproject.org/).
- **Preprocessing**: Use `bedtools` (CPU) to aggregate accessibility signal within ±50kb windows of each gene's TSS; filter genes with zero expression in all samples.
- **Feature Selection**: Select the top 10,000 most variable chromatin peaks across all samples to reduce dimensionality for the 7GB RAM limit.
- **Model Training**: Train Elastic Net regression models (scikit-learn) for each cell line, using accessibility features to predict log-transformed expression values.
- **Validation**: Perform 5-fold cross-validation per cell line to assess generalization without overfitting.
- **Statistical Testing**: Calculate Pearson correlation coefficients and p-values between predicted and actual expression; apply Bonferroni correction for multiple testing across genes.
- **Runtime**: Estimated execution time < 2 hours on 2 CPU cores using sparse matrix representations.

## Duplicate-check

- Reviewed existing ideas: None provided in corpus.
- Closest match: N/A.
- Verdict: NOT a duplicate.
