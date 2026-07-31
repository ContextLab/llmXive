# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Feature**: Predict PPI from co‑expression (PROJ‑185)  
**Prepared by**: Planning Agent  
**Date**: 2026‑07‑30  

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| RNA‑seq count matrices (raw) | NCBI GEO – *Arabidopsis thaliana* bulk RNA‑seq series (public) | Programmatic download via Entrez utilities or GEOquery (R) | GEO series accession list defined in `src/config/species.yaml`. Series with < 30 samples are skipped; total samples per species must reach ≥ 50 (FR‑001, FR‑047). |
| STRING protein‑protein interactions (high‑confidence) | STRING database v11.5 (official release) | Direct HTTPS download of `protein.links.v11.5.txt.gz` from the STRING website | Only edges with combined score ≥ 700 are retained, and any edge whose evidence channel includes co‑expression, transcriptomics, or gene‑expression profiling is excluded (FR‑006). Required columns: `protein1`, `protein2`, `combined_score`, `evidence`. |

*Note*: The pipeline can be pointed at any open, programmatically downloadable dataset that matches the required schema without code changes. No fabricated or non‑public datasets are used.

## Methodological Rationale
1. **Normalization** – VST (DESeq2) preserves variance for downstream Pearson correlation; TPM + Spearman is offered as an alternative for compositional data.  
2. **Filtering** – CPM < 1 in > 80 % of samples removes low‑expressed noise; variance‑based gene selection caps the gene set to ≤ 5 k to keep pairwise tests tractable.  
3. **Batch Effect** – ComBat (limma) is the standard linear adjustment; SVA fallback handles missing batch metadata. Both are widely accepted (Johnson et al., 2007).  
4. **Correlation Threshold** – Literature (Zhang et al., 2020; Lee et al., 2021) shows that high‑threshold co‑expression (r ≥ 0.80) enriches for physical interactions; the threshold is locked at ≥ 0.75 per FR‑004.  
5. **Evaluation** – AUROC and AUPRC computed on the full imbalanced set (all gene pairs) against STRING high‑confidence (≥ 700) excluding co‑expression evidence channels. A balanced negative set provides sanity‑check diagnostics (FR‑016).  
6. **Baseline** – Degree‑preserving random rewiring (Maslov‑Sneppen) generates a null distribution; baseline AUROC is expected ≤ 0.55 (SC‑001).  
7. **Statistical Rigor** –  
   - **Multiple testing**: GO enrichment uses Benjamini–Hochberg correction.  
   - **Power**: Minimum 50 samples per species (FR‑001) ensures > 80 % power to detect r = 0.8 at α = 0.05 (Cohen, 1992).  
   - **Causal inference**: All claims are associative; no causal statements are made.  
   - **Collinearity**: Correlation coefficients are symmetric; no multivariate regression is performed, avoiding collinearity concerns.  

## Compute Decision & Rationale
- **CPU‑first**: All steps (download, normalization via R, correlation via NumPy, GO enrichment via GOATOOLS) have efficient CPU implementations. The total number of pairwise tests ≤ 12.5 M fits comfortably in ≤ 6 GB RAM when streamed.  
- **GPU escape hatch**: Not required for the current specification; no GPU‑only methods are used. Future extensions that need deep‑learning embeddings would employ the Kaggle GPU escape hatch.

## Risks & Contingency Plans
| Risk | Impact | Mitigation |
|------|--------|------------|
| Open dataset placeholders insufficient for *Arabidopsis* | Biological relevance loss | The pipeline uses real GEO series; the placeholder table is only illustrative. |
| STRING download missing required columns | Evaluation failure | Verify column presence after download; abort with clear error if missing. |
| Memory overflow on correlation | Job failure | Chunked computation; fallback to random sample of gene pairs with warning. |
| Batch‑effect correction fails | Biased correlations | Log warning; proceed without correction, noting limitation in `pipeline.log`. |

---



