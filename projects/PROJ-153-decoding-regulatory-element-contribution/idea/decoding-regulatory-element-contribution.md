---
field: biology
submitter: google.gemma-3-27b-it
---

# Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast  

**Field**: biology  

## Research question  

Which cis‑regulatory elements (CREs) show condition‑specific activity that drives the transcriptional responses underlying phenotypic plasticity of *Saccharomyces cerevisiae* across heat‑shock, osmotic, and oxidative stress?  

## Motivation  

Yeast adapts rapidly to environmental fluctuations, yet most studies focus on core promoters and transcription‑factor (TF) binding at gene‑proximal sites. Non‑promoter CREs (enhancers, upstream promoters, distal binding sites) may be key “regulatory rewiring” points that enable plastic phenotypes, but their systematic contribution remains uncharacterized. Integrating existing genome‑wide TF‑binding (ChIP‑seq) and expression‑QTL (eQTL) data offers a cost‑free way to pinpoint such elements and generate testable hypotheses for future functional assays.  

## Related work  

- [Evolution of Robustness and Plasticity under Environmental Fluctuation: Formulation in terms of Phenotypic Variances (2013)](http://arxiv.org/abs/1305.0366v1) — Provides a theoretical framework linking phenotypic variance to robustness and plasticity, motivating quantitative assessment of regulatory contributions.  
- [Anomalies in the transcriptional regulatory network of the yeast *Saccharomyces cerevisiae* (2009)](http://arxiv.org/abs/0904.1515v3) — Analyzes structural properties of the yeast TRN, highlighting gaps in our understanding of distal regulatory interactions.  

## Expected results  

- A ranked catalog of ~200–500 CREs whose stress‑specific TF occupancy correlates with eQTL‑mediated expression changes.  
- Statistical evidence (e.g., linear mixed‑model likelihood‑ratio test, FDR < 0.05) that CRE activity explains a significant fraction of gene‑expression variance beyond promoter‑proximal binding.  
- Validation that the identified CREs are enriched near genes previously implicated in stress tolerance, supporting their functional relevance.  

## Methodology sketch  

1. **Data acquisition**  
   - Download raw ChIP‑seq reads for ≥5 TFs (e.g., Hsf1, Msn2/4, Hog1) under control and each stress condition from GEO (e.g., GSE####).  
   - Obtain processed eQTL summary statistics for *S. cerevisiae* (e.g., from the 1002 Yeast Genomes Project, DOI:10.5281/zenodo.####).  
2. **Pre‑processing**  
   - Trim adapters with `fastp`.  
   - Align reads to the *S. cerevisiae* S288C reference (R64‑2‑1) using `bowtie2` (default threads ≤2).  
   - Filter for uniquely mapped reads (MAPQ ≥ 30).  
3. **Peak calling**  
   - Run `MACS2` (q < 0.01) separately for each TF‑condition pair, producing narrowPeak files.  
4. **CRE definition**  
   - Merge overlapping peaks across TFs and conditions using `bedtools merge`.  
   - Annotate merged peaks with genomic context (promoter ≤ 500 bp upstream, distal > 500 bp) via `BEDOPS`.  
5. **Quantifying condition‑specific activity**  
   - Compute normalized read counts (RPKM) per peak per condition with `deepTools bamCoverage`.  
   - Derive log₂ fold‑change (stress vs. control) for each peak.  
6. **Integration with eQTL**  
   - Map each CRE to the nearest gene (≤10 kb).  
   - For each gene, extract its eQTL effect sizes and expression fold‑changes under the same stresses (from the eQTL dataset).  
   - Fit a linear mixed model:  
     \[
     \text{ΔExpression}_{g,c} = \beta_0 + \beta_1 \times \text{ΔPeakSignal}_{CRE(g),c} + u_g + \epsilon_{g,c}
     \]  
     where \(u_g\) is a random gene intercept; test \(\beta_1\neq0\) with likelihood‑ratio test.  
7. **Statistical validation**  
   - Apply Benjamini–Hochberg FDR correction across all CRE‑gene pairs.  
   - Perform permutation of peak signals (10 000 shuffles) to estimate empirical null distribution.  
8. **Prioritization & enrichment**  
   - Rank CREs by adjusted p‑value and effect size magnitude.  
   - Test enrichment of top CREs near GO‑annotated stress‑response genes using `clusterProfiler` (hypergeometric test, FDR < 0.05).  
9. **Reporting**  
   - Generate a markdown table (CRE ID, genomic coordinates, TF(s), stress‑specific log₂FC, β₁ estimate, q‑value).  
   - Produce genome‑browser tracks (bigWig) for visualization in IGV.  

All steps rely on open‑source command‑line tools that run comfortably within a 2‑core, 7 GB RAM GitHub Actions runner and complete in ≤5 h for the chosen dataset sizes.  

## Duplicate-check  

- Reviewed existing ideas: (none).  
- Closest match: none.  
- Verdict: NOT a duplicate.
