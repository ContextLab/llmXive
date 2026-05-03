---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases  

**Field**: biology  

## Research question  

Can gene co‑expression patterns derived from publicly available plant transcriptomic datasets reliably predict physical protein‑protein interactions in *Arabidopsis thaliana* and related species?  

## Motivation  

Experimental mapping of plant PPIs is labor‑intensive and incomplete, limiting systems‑level understanding of plant biology and crop‑improvement efforts. Public RNA‑seq repositories (e.g., NCBI GEO) contain thousands of samples that capture diverse conditions; leveraging these data to infer PPIs could provide a low‑cost, scalable complement to experimental assays. Demonstrating predictive power would justify broader adoption of network‑based inference for plant interactomes.  

## Related work  

- [Ranking protein‑protein models with large language models and graph neural networks (2024)](http://arxiv.org/abs/2407.16375v1) — Shows how modern graph‑neural‑network and language‑model techniques can rank candidate PPI structures, illustrating the growing feasibility of computational PPI prediction.  

## Expected results  

We anticipate that a co‑expression network filtered at a high Pearson‑correlation threshold (e.g., r ≥ 0.8) will recover a statistically significant subset of known *Arabidopsis* PPIs from STRING (AUROC > 0.70). Enrichment analysis should reveal that predicted interactions are over‑represented in biologically coherent GO terms (Fisher’s exact test p < 0.05 after FDR correction). Failure to exceed these benchmarks would falsify the hypothesis that simple co‑expression alone is sufficient for reliable PPI prediction.  

## Methodology sketch  

- **Data acquisition**  
  - Download bulk RNA‑seq count matrices for *Arabidopsis thaliana* from NCBI GEO (e.g., series GSEXXXXX) using `wget`/`curl`.  
  - Obtain the latest *Arabidopsis* protein‑protein interaction reference from STRING (download `protein.links.v11.5.txt.gz`).  
- **Pre‑processing**  
  - Normalize counts with TPM or DESeq2’s variance‑stabilizing transformation.  
  - Filter genes with low expression (e.g., CPM < 1 in > 80 % of samples).  
- **Network construction**  
  - Compute pairwise Pearson correlation across all retained genes using NumPy/Pandas.  
  - Apply a correlation threshold (e.g., r ≥ 0.8) to generate an undirected co‑expression graph (NetworkX).  
- **Prediction extraction**  
  - Treat each edge in the co‑expression graph as a predicted PPI.  
  - Map gene identifiers to STRING protein IDs (using Bioconductor `org.At.tair.db` or Ensembl BioMart).  
- **Evaluation**  
  - Compare predicted edges to STRING’s high‑confidence interactions (combined score ≥ 700).  
  - Compute ROC and PR curves; report AUROC and AUPRC.  
  - Perform random‑graph baseline (degree‑preserving rewiring) to assess significance of performance metrics.  
- **Functional validation**  
  - Run GO enrichment on the set of genes participating in predicted PPIs using GOATOOLS.  
  - Test enrichment significance with Fisher’s exact test and correct for multiple testing (Benjamini–Hochberg).  
- **Reproducibility**  
  - All scripts will be written in Python (≥ 3.10) and R (≥ 4.2) and orchestrated with a Makefile to keep the total runtime < 6 h on a GitHub Actions runner (2 CPU, 7 GB RAM).  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: none.  
- Verdict: NOT a duplicate
