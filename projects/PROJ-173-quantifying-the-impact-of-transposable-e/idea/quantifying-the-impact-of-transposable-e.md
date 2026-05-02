---
field: biology
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

**Field**: biology

## Research question

Do polymorphic transposable element (TE) insertions in the Drosophila Genetic Reference Panel (DGRP) significantly influence the expression levels of nearby genes across natural genotypes?

## Motivation

Gene expression variation is a major substrate for phenotypic diversity and adaptation in *Drosophila*. While single‑nucleotide polymorphisms have been extensively linked to expression changes, the contribution of TE insertion polymorphisms remains unclear. Clarifying this link will reveal a hidden layer of regulatory variation and improve our understanding of how mobile DNA shapes quantitative traits.

## Related work

- [Pervasive adaptation of gene expression in Drosophila (2015)](http://arxiv.org/abs/1502.06406v2) — Demonstrates that expression levels are selectable traits in *Drosophila* populations, providing a baseline for association analyses.  
- [Revised Annotations, Sex-Biased Expression, and Lineage-Specific Genes in the Drosophila melanogaster group (2014)](http://arxiv.org/abs/1408.0247v2) — Supplies updated gene models and expression datasets that improve mapping of TE insertions to nearby genes.  
- [Transposable Elements Are Major Contributors to the Origin, Diversification, and Regulation of Vertebrate Long Noncoding RNAs (2013)](https://doi.org/10.1371/journal.pgen.1003470) — Shows that TEs can generate regulatory RNAs, supporting the hypothesis that they affect gene expression.  
- [The Impact of Genomic Variation on Function (IGVF) Consortium (2023)](http://arxiv.org/abs/2307.13708v1) — Highlights the broad influence of genomic variants on molecular phenotypes, underscoring the relevance of TE polymorphisms as functional variants.  

## Expected results

We anticipate identifying a subset of TE insertions whose presence/absence is significantly associated (FDR < 0.05) with altered expression of proximal genes. A positive result would be a reproducible list of TE‑gene pairs where the effect size exceeds a predefined threshold (e.g., ≥ 0.2 log₂‑fold change). Failure to detect such associations after correcting for population structure would suggest that TE polymorphisms contribute little to expression variation in the DGRP.

## Methodology sketch

- **Data acquisition**
  - Download the DGRP genotype VCF (including TE insertion calls) from the DGRP website (e.g., `ftp://ftp.flybase.net/genomes/Drosophila/DGRP/`).
  - Retrieve publicly available RNA‑seq fastq files for the same lines from NCBI SRA (accession SRPXXXXX) or pre‑processed TPM tables from modENCODE.
- **TE annotation**
  - Use the TE insertion VCF to extract coordinates of polymorphic TEs.
  - Define “proximal” TEs as those whose insertion site lies ≤5 kb upstream or downstream of a gene’s transcription start/end (using the revised gene models from the 2014 Drosophila annotation paper).
- **Expression quantification**
  - Align RNA‑seq reads with STAR (2‑pass) to the *D. melanogaster* reference genome (release 6).
  - Quantify gene expression with featureCounts and TE expression with TEtranscripts, generating a matrix of gene TPMs and TE‑derived read counts per line.
- **Association analysis**
  - For each gene–TE pair, fit a linear model: `gene_expression ~ TE_presence + PC1 + PC2 + PC3` where PCs are derived from genome‑wide SNP genotype to control for population structure.
  - Perform the analysis with the `MatrixEQTL` R package to handle thousands of tests efficiently.
  - Apply Benjamini–Hochberg correction across all tested pairs; retain pairs with adjusted p‑value < 0.05.
- **Validation & robustness**
  - Replicate significant associations using an independent DGRP expression dataset (e.g., from a different tissue or developmental stage) to assess consistency.
  - Conduct permutation testing (shuffle TE presence labels) to confirm that the observed signal exceeds random expectation.
- **Reporting**
  - Summarize significant TE‑gene associations in a table (effect size, confidence interval, FDR).
  - Visualize exemplar loci with IGV screenshots showing TE insertion and altered expression.
  - Deposit all scripts and intermediate files in a public GitHub repository for reproducibility.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A (no comparable fleshed‑out idea found).
- Verdict: **NOT a duplicate**
